"""Auth utilities — JWT, password hashing, current user dependency, API keys."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.models import ApiKey, SubscriptionTier, User
from app.db.session import get_db
from app.services.email import EmailMessage, create_email_sender

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_password_reset_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=15)
    payload = {
        "sub": user_id,
        "type": "password_reset",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_verification_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=24)
    payload = {
        "sub": user_id,
        "type": "email_verification",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Safely decode JWT token, returning None if invalid or expired."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])  # type: ignore
    except jwt.PyJWTError:
        return None


def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, hashed_key)."""
    raw = f"syzygy_{secrets.token_urlsafe(settings.api_key_length)}"
    hashed = hash_password(raw)
    return raw, hashed


async def authenticate_api_key(token: str, db: AsyncSession) -> User | None:
    """Look up an API key by its hash. Updates last_used_at."""
    result = await db.execute(
        select(ApiKey)
        .options(selectinload(ApiKey.user))
        .where(ApiKey.is_active)
    )
    for api_key in result.scalars().all():
        if verify_password(token, api_key.hashed_key):  # type: ignore
            api_key.last_used_at = datetime.now(UTC)  # type: ignore
            db.add(api_key)
            await db.commit()
            return api_key.user  # type: ignore[no-any-return]
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    token = credentials.credentials

    # Try JWT first
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        user_id = payload.get("sub")
        if user_id:
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            return result.scalar_one_or_none()

    # Fall back to API key auth
    return await authenticate_api_key(token, db)


async def require_user(
    user: User | None = Depends(get_current_user),
) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def check_usage_limit(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Check if user has exceeded their monthly message limit. Always normalize to UTC."""
    now = datetime.now(UTC)

    # Reset usage if new month started — normalize naive datetimes to UTC
    usage_reset = user.usage_reset_at
    if usage_reset and usage_reset.tzinfo is None:
        usage_reset = usage_reset.replace(tzinfo=UTC)
    if usage_reset and (usage_reset.year, usage_reset.month) < (now.year, now.month):
        user.message_count = 0  # type: ignore
        user.usage_reset_at = now  # type: ignore
        db.add(user)
        await db.commit()

    # Premium and enterprise users have unlimited messages
    if user.subscription_tier == SubscriptionTier.PREMIUM or user.subscription_tier == SubscriptionTier.ENTERPRISE:
        return user

    # Trial users can use premium limit — normalize naive datetimes to UTC
    trial_ends = user.trial_ends_at
    if trial_ends and trial_ends.tzinfo is None:
        trial_ends = trial_ends.replace(tzinfo=UTC)
    if trial_ends and trial_ends > now:
        return user

    # Free tier users are limited
    if user.message_count >= settings.free_tier_monthly_messages:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "USAGE_LIMIT_EXCEEDED",
                "message": (
                    f"Free tier limit of {settings.free_tier_monthly_messages} "
                    "messages per month exceeded. Upgrade to continue."
                ),
            },
        )
    return user


async def require_admin(
    user: User = Depends(require_user),
) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def send_email(message: EmailMessage) -> None:
    sender = create_email_sender(
        provider=settings.email_provider,
        sendgrid_api_key=settings.sendgrid_api_key,
        ses_region=settings.ses_region,
        ses_access_key_id=settings.ses_access_key_id,
        ses_secret_access_key=settings.ses_secret_access_key,
        from_address=settings.email_from_address,
        from_name=settings.email_from_name,
    )
    await sender.send(message)
