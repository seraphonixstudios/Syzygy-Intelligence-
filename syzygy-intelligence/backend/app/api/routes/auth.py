"""Auth routes — register, login, refresh, me, settings, password reset, API keys."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import (
    check_usage_limit,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_verification_token,
    decode_token,
    generate_api_key,
    hash_password,
    require_user,
    send_email,
    verify_password,
)
from app.config import settings
from app.db.models import ApiKey, SubscriptionTier, User
from app.db.session import get_db
from app.observability import (
    log_auth_event,
    log_usage_event,
    metrics_registry,
)
from app.services.email import EmailMessage

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None
    is_active: bool
    is_superuser: bool
    verified_at: str | None
    trial_ends_at: str | None
    subscription_tier: str
    message_count: int
    monthly_message_limit: int
    settings: dict[str, Any]
    created_at: str


class UpdateSettingsRequest(BaseModel):
    settings: dict[str, Any]


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SendVerificationRequest(BaseModel):
    email: str


class VerifyEmailRequest(BaseModel):
    token: str


class CreateApiKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    last_used_at: str | None
    is_active: bool
    created_at: str


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyResponse]


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        log_auth_event("password_reset_requested", user_email=req.email, result="user_not_found")
        return {"message": "If that email exists, a reset link has been sent."}

    token = create_password_reset_token(str(user.id))
    reset_link = f"{settings.frontend_url}/auth/reset-password?token={token}"

    await send_email(EmailMessage(
        to=user.email,  # type: ignore
        subject="Reset your Syzygy password",
        text_body=f"Reset your password here: {reset_link}\n\nThis link expires in 15 minutes.",
        html_body=(
            f"<p>Click <a href='{reset_link}'>here</a> to reset your password.</p>"
            f"<p>This link expires in 15 minutes.</p>"
        ),
    ))

    log_auth_event("password_reset_requested", user_email=req.email, user_id=str(user.id), result="success")
    metrics_registry.auth_password_resets.labels(result="sent").inc()

    resp: dict[str, Any] = {"message": "If that email exists, a reset link has been sent."}
    if settings.email_provider == "console":
        resp["reset_token"] = token
    return resp


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    payload = decode_token(req.token)
    if payload is None or payload.get("type") != "password_reset":
        log_auth_event("password_reset", result="invalid_token")
        metrics_registry.auth_password_resets.labels(result="invalid_token").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user_id = payload.get("sub")
    if user_id is None:
        log_auth_event("password_reset", result="invalid_token")
        metrics_registry.auth_password_resets.labels(result="invalid_token").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        log_auth_event("password_reset", user_id=user_id, result="user_not_found")
        metrics_registry.auth_password_resets.labels(result="user_not_found").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.hashed_password = hash_password(req.new_password)  # type: ignore
    db.add(user)
    await db.commit()

    log_auth_event("password_reset", user_id=str(user.id), user_email=user.email, result="success")
    metrics_registry.auth_password_resets.labels(result="success").inc()
    return {"message": "Password has been reset successfully."}


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

    await send_email(EmailMessage(
        to=user.email,  # type: ignore
        subject="Verify your Syzygy email",
        text_body=f"Verify your email here: {verify_link}\n\nThis link expires in 24 hours.",
        html_body=(
            f"<p>Click <a href='{verify_link}'>here</a> to verify your email.</p>"
            f"<p>This link expires in 24 hours.</p>"
        ),
    ))

    log_auth_event("email_verification_requested", user_email=req.email, user_id=str(user.id), result="success")

    resp: dict[str, Any] = {"message": "If that email exists, a verification link has been sent."}
    if settings.email_provider == "console":
        resp["verification_token"] = token
    return resp


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    payload = decode_token(req.token)
    if payload is None or payload.get("type") != "email_verification":
        log_auth_event("email_verified", result="invalid_token")
        metrics_registry.auth_email_verifications.labels(result="invalid_token").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user_id = payload.get("sub")
    if user_id is None:
        log_auth_event("email_verified", result="invalid_token")
        metrics_registry.auth_email_verifications.labels(result="invalid_token").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        log_auth_event("email_verified", user_id=user_id, result="user_not_found")
        metrics_registry.auth_email_verifications.labels(result="user_not_found").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.verified_at = datetime.now(UTC)  # type: ignore
    db.add(user)
    await db.commit()

    log_auth_event("email_verified", user_id=str(user.id), user_email=user.email, result="success")
    metrics_registry.auth_email_verifications.labels(result="success").inc()
    return {"message": "Email verified successfully."}


def _user_to_response(user: User) -> UserResponse:
    now = datetime.now(UTC)
    trial_ends = user.trial_ends_at
    if trial_ends and trial_ends.tzinfo is None:
        trial_ends = trial_ends.replace(tzinfo=UTC)

    if user.subscription_tier == SubscriptionTier.PREMIUM or user.subscription_tier == SubscriptionTier.ENTERPRISE:
        limit = settings.premium_monthly_messages
    elif trial_ends and trial_ends > now:
        limit = settings.premium_monthly_messages
    else:
        limit = settings.free_tier_monthly_messages

    return UserResponse(
        id=str(user.id),
        email=user.email,  # type: ignore
        display_name=user.display_name,  # type: ignore
        is_active=user.is_active,  # type: ignore
        is_superuser=user.is_superuser,  # type: ignore
        verified_at=user.verified_at.isoformat() if user.verified_at else None,
        trial_ends_at=trial_ends.isoformat() if trial_ends else None,
        subscription_tier=user.subscription_tier.value,
        message_count=user.message_count,  # type: ignore
        monthly_message_limit=limit,
        settings=user.settings or {},  # type: ignore
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


async def _reset_usage_if_needed(user: User, db: AsyncSession) -> None:
    now = datetime.now(UTC)
    usage_reset = user.usage_reset_at
    if usage_reset and usage_reset.tzinfo is None:
        usage_reset = usage_reset.replace(tzinfo=UTC)

    if usage_reset and (usage_reset.year, usage_reset.month) < (now.year, now.month):
        user.message_count = 0  # type: ignore
        user.usage_reset_at = now  # type: ignore
        db.add(user)
        await db.commit()
        log_usage_event("usage_reset", str(user.id), user.subscription_tier.value, 0)


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        log_auth_event("register", user_email=req.email, result="already_exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        display_name=req.display_name or req.email.split("@")[0],
        trial_ends_at=datetime.now(UTC) + timedelta(days=settings.free_tier_days),
        settings={},
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    log_auth_event("register", user_email=req.email, user_id=str(user.id), result="success", subscription_tier="free")
    metrics_registry.auth_login_attempts.labels(status="success").inc()
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),  # type: ignore
        refresh_token=create_refresh_token(str(user.id), user.email),  # type: ignore
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):  # type: ignore
        log_auth_event("login", user_email=req.email, result="invalid_credentials")
        metrics_registry.auth_login_attempts.labels(status="failed").inc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        log_auth_event("login", user_email=req.email, user_id=str(user.id), result="account_disabled")
        metrics_registry.auth_login_attempts.labels(status="failed").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    log_auth_event("login", user_email=req.email, user_id=str(user.id), result="success")
    metrics_registry.auth_login_attempts.labels(status="success").inc()
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),  # type: ignore
        refresh_token=create_refresh_token(str(user.id), user.email),  # type: ignore
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest) -> TokenResponse:
    payload = decode_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        log_auth_event("token_refresh", result="invalid_token")
        metrics_registry.auth_token_refreshes.labels(token_type="refresh").inc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    sub = payload.get("sub")
    email = payload.get("email")
    if not sub or not email:
        log_auth_event("token_refresh", result="invalid_token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    log_auth_event("token_refresh", user_id=sub, user_email=email, result="success")
    metrics_registry.auth_token_refreshes.labels(token_type="access").inc()
    return TokenResponse(
        access_token=create_access_token(sub, email),
        refresh_token=create_refresh_token(sub, email),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    await _reset_usage_if_needed(user, db)
    return _user_to_response(user)


@router.put("/me/settings")
async def update_settings(
    req: UpdateSettingsRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user.settings = req.settings  # type: ignore
    db.add(user)
    await db.commit()
    log_auth_event("settings_updated", user_id=str(user.id), user_email=user.email, result="success")
    return {"status": "ok"}


# ─── API Key Management ─────────────────────────────────────

@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    req: CreateApiKeyRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedResponse:
    raw_key, hashed_key = generate_api_key()
    prefix = raw_key[:12]

    api_key = ApiKey(
        user_id=user.id,
        name=req.name,
        key_prefix=prefix,
        hashed_key=hashed_key,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    log_auth_event(
        "api_key_created",
        user_id=str(user.id),
        user_email=user.email,
        result="success",
        api_key_id=str(api_key.id),
    )
    metrics_registry.auth_api_keys_created.inc()

    return ApiKeyCreatedResponse(
        id=str(api_key.id),
        name=api_key.name,  # type: ignore
        key_prefix=api_key.key_prefix,  # type: ignore
        raw_key=raw_key,
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        is_active=api_key.is_active,  # type: ignore
        created_at=api_key.created_at.isoformat(),
    )


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyListResponse:
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return ApiKeyListResponse(keys=[
        ApiKeyResponse(
            id=str(k.id),
            name=k.name,  # type: ignore
            key_prefix=k.key_prefix,  # type: ignore
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            is_active=k.is_active,  # type: ignore
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ])


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == uuid.UUID(key_id), ApiKey.user_id == user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        log_auth_event("api_key_revoked", user_id=str(user.id), result="not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False  # type: ignore
    db.add(api_key)
    await db.commit()

    log_auth_event("api_key_revoked", user_id=str(user.id), api_key_id=key_id, result="success")
    metrics_registry.auth_api_keys_revoked.inc()
    return {"status": "revoked"}


@router.post("/expire-trial")
async def expire_trial(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            trial_ends_at=None,
            message_count=settings.free_tier_monthly_messages,
            usage_reset_at=datetime.now(UTC),
        )
    )
    await db.commit()

    log_auth_event("trial_expired", user_id=str(user.id), user_email=user.email, result="success")
    metrics_registry.trial_expirations.inc()
    return {"trial_ends_at": None, "message_count": settings.free_tier_monthly_messages}


@router.post("/charge-message")
async def charge_message(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await check_usage_limit(user, db)
    # Atomically increment message count using RETURNING to prevent race conditions
    # This ensures the operation is atomic: both increment and value fetch happen in a single transaction
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(message_count=User.message_count + 1)
        .returning(User.message_count)
    )
    result = await db.execute(stmt)
    new_count = result.scalar_one()
    await db.commit()

    log_usage_event(
        "message_charged",
        user_id=str(user.id),
        subscription_tier=user.subscription_tier.value,
        message_count=new_count,
    )
    metrics_registry.message_count_charged.labels(subscription_tier=user.subscription_tier.value).inc()
    return {"message_count": new_count}
