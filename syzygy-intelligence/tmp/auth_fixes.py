# This script shows the key fixes needed in auth.py

# FIX 1: Email send error handling in forgot_password
@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        log_auth_event("password_reset_requested", user_email=req.email, result="user_not_found")
        return {"message": "If that email exists, a reset link has been sent."}

    token = create_password_reset_token(str(user.id))
    reset_link = f"{settings.frontend_url}/auth/reset-password?token={token}"

    try:
        await send_email(EmailMessage(
            to=user.email,
            subject="Reset your Syzygy password",
            text_body=f"Reset your password here: {reset_link}\n\nThis link expires in 15 minutes.",
            html_body=(
                f"<p>Click <a href='{reset_link}'>here</a> to reset your password.</p>"
                f"<p>This link expires in 15 minutes.</p>"
            ),
        ))
    except Exception as exc:
        logger.error("Failed to send password reset email", error=str(exc), user_id=str(user.id))
        # In production, fail the request. In dev (console provider), continue.
        if settings.email_provider != "console":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is unavailable. Please try again later."
            )

    log_auth_event("password_reset_requested", user_email=req.email, user_id=str(user.id), result="success")
    metrics_registry.auth_password_resets.labels(result="sent").inc()

    resp: dict[str, Any] = {"message": "If that email exists, a reset link has been sent."}
    if settings.email_provider == "console":
        resp["reset_token"] = token
    return resp


# FIX 2: Similar error handling for send_verification
@router.post("/send-verification")
async def send_verification(req: SendVerificationRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or user.verified_at:
        if user and user.verified_at:
            log_auth_event(
                "email_verification_requested",
                user_email=req.email,
                user_id=str(user.id),
                result="already_verified",
            )
        return {"message": "If that email exists, a verification link has been sent."}

    token = create_verification_token(str(user.id))
    frontend_url = settings.cors_origins.split(",")[0].strip() or "http://localhost:3000"
    verify_link = f"{frontend_url}/auth/verify-email?token={token}"

    try:
        await send_email(EmailMessage(
            to=user.email,
            subject="Verify your Syzygy email",
            text_body=f"Verify your email here: {verify_link}\n\nThis link expires in 24 hours.",
            html_body=(
                f"<p>Click <a href='{verify_link}'>here</a> to verify your email.</p>"
                f"<p>This link expires in 24 hours.</p>"
            ),
        ))
    except Exception as exc:
        logger.error("Failed to send verification email", error=str(exc), user_id=str(user.id))
        if settings.email_provider != "console":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is unavailable. Please try again later."
            )

    log_auth_event("email_verification_requested", user_email=req.email, user_id=str(user.id), result="success")

    resp: dict[str, Any] = {"message": "If that email exists, a verification link has been sent."}
    if settings.email_provider == "console":
        resp["verification_token"] = token
    return resp


# FIX 3: Fixed usage reset logic (monthly reset on month boundary)
async def _reset_usage_if_needed(user: User, db: AsyncSession) -> None:
    now = datetime.now(UTC)
    usage_reset = _to_utc(user.usage_reset_at)

    # Reset if no previous reset or if month/year has changed
    if usage_reset is None or (usage_reset.year, usage_reset.month) < (now.year, now.month):
        user.message_count = 0  # type: ignore
        user.usage_reset_at = now  # type: ignore
        db.add(user)
        await db.commit()
        log_usage_event("usage_reset", str(user.id), user.subscription_tier.value, 0)
