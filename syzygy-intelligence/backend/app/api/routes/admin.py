"""Admin routes — user management, usage stats, system overview."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_admin
from app.db.models import SubscriptionTier, User
from app.db.session import get_db

router = APIRouter()


class UserListItem(BaseModel):
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
    created_at: str
    last_active_at: str | None


class SystemStats(BaseModel):
    total_users: int
    active_users: int
    superusers: int
    free_users: int
    premium_users: int
    enterprise_users: int
    total_messages: int
    users_on_trial: int
    users_over_limit: int


@router.get("/users", response_model=list[UserListItem])
async def list_users(
    page: int = 1,
    per_page: int = 50,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    now = datetime.now(UTC)
    items = []
    for u in users:
        if u.subscription_tier in (SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE):
            limit = 10000
        elif u.trial_ends_at and u.trial_ends_at > now:
            limit = 10000
        else:
            limit = 100

        items.append(UserListItem(
            id=str(u.id),
            email=u.email,
            display_name=u.display_name,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            verified_at=u.verified_at.isoformat() if u.verified_at else None,
            trial_ends_at=u.trial_ends_at.isoformat() if u.trial_ends_at else None,
            subscription_tier=u.subscription_tier.value,
            message_count=u.message_count,
            monthly_message_limit=limit,
            created_at=u.created_at.isoformat(),
            last_active_at=u.updated_at.isoformat() if u.updated_at else None,
        ))
    return items


@router.get("/users/{user_id}", response_model=UserListItem)
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    now = datetime.now(UTC)
    if u.subscription_tier in (SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE):
        limit = 10000
    elif u.trial_ends_at and u.trial_ends_at > now:
        limit = 10000
    else:
        limit = 100

    return UserListItem(
        id=str(u.id),
        email=u.email,
        display_name=u.display_name,
        is_active=u.is_active,
        is_superuser=u.is_superuser,
        verified_at=u.verified_at.isoformat() if u.verified_at else None,
        trial_ends_at=u.trial_ends_at.isoformat() if u.trial_ends_at else None,
        subscription_tier=u.subscription_tier.value,
        message_count=u.message_count,
        monthly_message_limit=limit,
        created_at=u.created_at.isoformat(),
        last_active_at=u.updated_at.isoformat() if u.updated_at else None,
    )


class UpdateUserRequest(BaseModel):
    is_active: bool | None = None
    is_superuser: bool | None = None
    subscription_tier: str | None = None
    display_name: str | None = None


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    req: UpdateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.is_active is not None:
        u.is_active = req.is_active
    if req.is_superuser is not None:
        u.is_superuser = req.is_superuser
    if req.subscription_tier is not None:
        try:
            u.subscription_tier = SubscriptionTier(req.subscription_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {req.subscription_tier}")
    if req.display_name is not None:
        u.display_name = req.display_name

    db.add(u)
    await db.commit()
    return {"status": "ok"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    u.is_active = False
    db.add(u)
    await db.commit()
    return {"status": "ok", "detail": "User disabled"}


@router.get("/stats", response_model=SystemStats)
async def system_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)

    total = await db.execute(select(func.count(User.id)))
    total_users = total.scalar() or 0

    active = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = active.scalar() or 0

    superusers = await db.execute(select(func.count(User.id)).where(User.is_superuser == True))
    superuser_count = superusers.scalar() or 0

    free = await db.execute(
        select(func.count(User.id)).where(User.subscription_tier == SubscriptionTier.FREE)
    )
    free_users = free.scalar() or 0

    premium = await db.execute(
        select(func.count(User.id)).where(User.subscription_tier == SubscriptionTier.PREMIUM)
    )
    premium_users = premium.scalar() or 0

    enterprise = await db.execute(
        select(func.count(User.id)).where(User.subscription_tier == SubscriptionTier.ENTERPRISE)
    )
    enterprise_users = enterprise.scalar() or 0

    msgs = await db.execute(select(func.coalesce(func.sum(User.message_count), 0)))
    total_messages = msgs.scalar() or 0

    trial = await db.execute(
        select(func.count(User.id)).where(
            User.trial_ends_at > now,
            User.subscription_tier == SubscriptionTier.FREE,
        )
    )
    users_on_trial = trial.scalar() or 0

    over_limit = await db.execute(
        select(func.count(User.id)).where(
            User.subscription_tier == SubscriptionTier.FREE,
            User.message_count >= 100,
        )
    )
    users_over_limit = over_limit.scalar() or 0

    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        superusers=superuser_count,
        free_users=free_users,
        premium_users=premium_users,
        enterprise_users=enterprise_users,
        total_messages=total_messages,
        users_on_trial=users_on_trial,
        users_over_limit=users_over_limit,
    )
