"""Auth utilities — JWT, password hashing, current user dependency, API keys."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from base64 import b64encode
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
from app.logging_setup import logger
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
    """Safely decode JWT token, returning None if invalid or expired.
    
    Logs decode errors for security auditing. Distinguishes between:
    - Malformed tokens (security issue)
    - Expired tokens (normal/expected)
    - Invalid signatures (potential tampering)
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])  # type: ignore
    except jwt.ExpiredSignatureError:
        logger.debug("Token decode failed: token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(
            "Token decode failed: invalid token",
            error_type=type(e).__name__,
            error_msg=str(e)[:100],  # Truncate to prevent log injection
        )
        return None
    except Exception as e:
        logger.error(
            "Token decode failed: unexpected error",
            error_type=type(e).__name__,
            error_msg=str(e)[:100],
        )
        return None


def _compute_searchable_hash(token: str) -> str:
    """Compute a deterministic searchable hash (first 16 chars of base64-encoded SHA256).
    
    This allows looking up API keys by a searchable prefix without storing plaintext tokens.
    The full token is then verified with bcrypt for constant-time comparison.
    """
    token_hash = hashlib.sha256(token.encode()).digest()
    return b64encode(token_hash).decode('utf-8')[:16]


def generate_api_key() -> tuple[str, str, str]:
    """Returns (raw_key, hashed_key, searchable_hash).
    
    - raw_key: shown once to user (store securely)
    - hashed_key: bcrypt hash for verification (constant-time comparison)
    - searchable_hash: deterministic hash for fast lookup
    """
    raw = f"syzygy_{secrets.token_urlsafe(settings.api_key_length)}"
    hashed = hash_password(raw)
    searchable = _compute_searchable_hash(raw)
    return raw, hashed, searchable


async def authenticate_api_key(token: str, db: AsyncSession) -> User | None:
    """Look up and validate an API key with atomic last_used_at update.
    
    Security properties:
    - Uses deterministic searchable hash for O(1) lookup (prevent timing attacks on key count)
    - Uses bcrypt for constant-time verification against stored hash
    - Updates last_used_at atomically using SQL to prevent race conditions
    - Logs all authentication attempts for security auditing
    
    Design:
    - First query: fast deterministic lookup + bcrypt verify
    - Second query: atomic SQL update to last_used_at (fire-and-forget)
    - Returns immediately after verification; logging happens async
    """
    try:
        from sqlalchemy import update
        
        searchable = _compute_searchable_hash(token)
        
        # Fast deterministic lookup by searchable hash
        result = await db.execute(
            select(ApiKey)
            .options(selectinload(ApiKey.user))
            .where(ApiKey.is_active, ApiKey.searchable_key_hash == searchable)
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            logger.debug("API key authentication failed: key not found", searchable_prefix=searchable[:8])
            return None
        
        # Constant-time bcrypt verification
        if not verify_password(token, api_key.hashed_key):  # type: ignore
            logger.warning(
                "API key verification failed: hash mismatch",
                key_id=str(api_key.id),
                searchable_prefix=searchable[:8],
            )
            return None
        
        # Update last_used_at atomically using SQL
        # Fire-and-forget: don't wait for result, don't block response
        # Using separate query avoids race conditions from ORM object state
        try:
            await db.execute(
                update(ApiKey)
                .where(ApiKey.id == api_key.id)  # type: ignore
                .values(last_used_at=datetime.now(UTC))
            )
            # Commit atomically
            await db.commit()
        except Exception as update_err:
            # Log but don't fail authentication if update fails
            logger.warning(
                "Failed to update API key last_used_at",
                key_id=str(api_key.id),
                error=str(update_err),
            )
            await db.rollback()
        
        logger.info(
            "API key authenticated successfully",
            key_id=str(api_key.id),
            user_id=str(api_key.user.id) if api_key.user else None,  # type: ignore
        )
        return api_key.user  # type: ignore[no-any-return]
    except Exception as e:
        logger.error("API key authentication error", error=str(e), error_type=type(e).__name__)
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


def _to_utc(dt: datetime | None) -> datetime | None:
    """Convert a naive or aware datetime to UTC. Returns None if input is None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def check_usage_limit(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Check if user has exceeded their monthly message limit. Always normalize to UTC."""
    now = datetime.now(UTC)

    # Reset usage if new month started
    usage_reset = _to_utc(user.usage_reset_at)
    if usage_reset and (usage_reset.year, usage_reset.month) < (now.year, now.month):
        user.message_count = 0  # type: ignore
        user.usage_reset_at = now  # type: ignore
        db.add(user)
        await db.commit()

    # Premium and enterprise users have unlimited messages
    if user.subscription_tier in (SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE):
        return user

    # Trial users can use premium limit
    trial_ends = _to_utc(user.trial_ends_at)
    if trial_ends and trial_ends > now:
        return user

    # Free tier users are limited
    if user.message_count >= settings.free_tier_monthly_messages:
        from app.errors import SyzygyError
        raise SyzygyError(
            message=f"Free tier limit of {settings.free_tier_monthly_messages} messages per month exceeded. Upgrade to continue.",
            code="USAGE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"limit": settings.free_tier_monthly_messages, "usage": user.message_count},
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
