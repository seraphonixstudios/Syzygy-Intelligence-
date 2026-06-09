"""Auth routes — register, login, refresh, me, settings, password reset, API keys."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import (
    authenticate_api_key,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    create_verification_token,
    decode_token,
    generate_api_key,
    get_current_user,
    hash_password,
    require_user,
    send_email,
    verify_password,
)
from app.config import settings
from app.db.models import ApiKey, SubscriptionTier, User
from app.db.session import get_db
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
    settings: dict
    created_at: str


class UpdateSettingsRequest(BaseModel):
    settings: dict


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
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    token = create_password_reset_token(str(user.id))
    frontend_url = settings.cors_origins.split(",")[0].strip() or "http://localhost:3000"
    reset_link = f"{frontend_url}/auth/reset-password?token={token}"

    await send_email(EmailMessage(
        to=user.email,
        subject="Reset your Syzygy password",
        text_body=f"Reset your password here: {reset_link}\n\nThis link expires in 15 minutes.",
        html_body=(
            f"<p>Click <a href='{reset_link}'>here</a> to reset your password.</p>"
            f"<p>This link expires in 15 minutes.</p>"
        ),
    ))

    resp: dict = {"message": "If that email exists, a reset link has been sent."}
    if settings.email_provider == "console":
        resp["reset_token"] = token
    return resp


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.token)
    if payload is None or payload.get("type") != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.hashed_password = hash_password(req.new_password)
    db.add(user)
    await db.commit()
    return {"message": "Password has been reset successfully."}


@router.post("/send-verification")
async def send_verification(req: SendVerificationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or user.verified_at:
        return {"message": "If that email exists, a verification link has been sent."}

    token = create_verification_token(str(user.id))
    frontend_url = settings.cors_origins.split(",")[0].strip() or "http://localhost:3000"
    verify_link = f"{frontend_url}/auth/verify-email?token={token}"

    await send_email(EmailMessage(
        to=user.email,
        subject="Verify your Syzygy email",
        text_body=f"Verify your email here: {verify_link}\n\nThis link expires in 24 hours.",
        html_body=(
            f"<p>Click <a href='{verify_link}'>here</a> to verify your email.</p>"
            f"<p>This link expires in 24 hours.</p>"
        ),
    ))

    resp: dict = {"message": "If that email exists, a verification link has been sent."}
    if settings.email_provider == "console":
        resp["verification_token"] = token
    return resp


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.token)
    if payload is None or payload.get("type") != "email_verification":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.verified_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    return {"message": "Email verified successfully."}


def _user_to_response(user: User) -> UserResponse:
    now = datetime.now(timezone.utc)
    trial_ends = user.trial_ends_at
    if trial_ends and trial_ends.tzinfo is None:
        trial_ends = trial_ends.replace(tzinfo=timezone.utc)

    if user.subscription_tier == SubscriptionTier.PREMIUM or user.subscription_tier == SubscriptionTier.ENTERPRISE:
        limit = settings.premium_monthly_messages
    elif trial_ends and trial_ends > now:
        limit = settings.premium_monthly_messages
    else:
        limit = settings.free_tier_monthly_messages

    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        verified_at=user.verified_at.isoformat() if user.verified_at else None,
        trial_ends_at=trial_ends.isoformat() if trial_ends else None,
        subscription_tier=user.subscription_tier.value,
        message_count=user.message_count,
        monthly_message_limit=limit,
        settings=user.settings or {},
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


async def _reset_usage_if_needed(user: User, db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    usage_reset = user.usage_reset_at
    if usage_reset and usage_reset.tzinfo is None:
        usage_reset = usage_reset.replace(tzinfo=timezone.utc)

    if usage_reset and usage_reset.replace(day=1) < now.replace(day=1):
        user.message_count = 0
        user.usage_reset_at = now
        db.add(user)
        await db.commit()


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        display_name=req.display_name or req.email.split("@")[0],
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=settings.free_tier_days),
        settings={},
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id), user.email),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id), user.email),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    return TokenResponse(
        access_token=create_access_token(payload["sub"], payload["email"]),
        refresh_token=create_refresh_token(payload["sub"], payload["email"]),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    await _reset_usage_if_needed(user, db)
    return _user_to_response(user)


@router.put("/me/settings")
async def update_settings(
    req: UpdateSettingsRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    user.settings = req.settings
    db.add(user)
    await db.commit()
    return {"status": "ok"}


# ─── API Key Management ─────────────────────────────────────

@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    req: CreateApiKeyRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
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

    return ApiKeyCreatedResponse(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        raw_key=raw_key,
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        is_active=api_key.is_active,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return ApiKeyListResponse(keys=[
        ApiKeyResponse(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ])


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == uuid.UUID(key_id), ApiKey.user_id == user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    db.add(api_key)
    await db.commit()
    return {"status": "revoked"}
