"""Auth routes — register, login, refresh, me, settings."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    get_current_user,
    require_user,
)
from app.config import settings
from app.db.models import User, SubscriptionTier
from app.db.session import get_db

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


def _user_to_response(user: User) -> UserResponse:
    now = datetime.now(timezone.utc)
    if user.subscription_tier == SubscriptionTier.PREMIUM or user.subscription_tier == SubscriptionTier.ENTERPRISE:
        limit = settings.premium_monthly_messages
    elif user.trial_ends_at and user.trial_ends_at > now:
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
        trial_ends_at=user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        subscription_tier=user.subscription_tier.value,
        message_count=user.message_count,
        monthly_message_limit=limit,
        settings=user.settings or {},
        created_at=user.created_at.isoformat(),
    )


async def _reset_usage_if_needed(user: User, db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    if user.usage_reset_at and user.usage_reset_at.replace(day=1) < now.replace(day=1):
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
