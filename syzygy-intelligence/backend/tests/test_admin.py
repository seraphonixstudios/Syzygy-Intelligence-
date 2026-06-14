"""Tests for admin API routes — user management and system stats."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models import SubscriptionTier


def _make_user(**overrides):
    defaults = dict(
        id=str(uuid.uuid4()),
        email="test@example.com",
        display_name="Test User",
        is_active=True,
        is_superuser=False,
        subscription_tier=SubscriptionTier.FREE,
        message_count=0,
        verified_at=datetime(2026, 1, 1, tzinfo=UTC),
        trial_ends_at=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=None,
    )
    defaults.update(overrides)
    u = MagicMock()
    for k, v in defaults.items():
        setattr(u, k, v)
    return u


@pytest.fixture
def admin_user():
    return _make_user(is_superuser=True)


def _mock_db_for_scalar_one_or_none(user):
    """db.execute returns an awaitable; result.scalar_one_or_none is sync."""
    fut = AsyncMock()
    fut.scalar_one_or_none = MagicMock(return_value=user)
    db = MagicMock()
    db.execute = AsyncMock(return_value=fut)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _mock_db_for_scalars_all(users):
    """db.execute returns an awaitable; result.scalars().all() is sync."""
    fut = AsyncMock()
    fut.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=users)))
    db = MagicMock()
    db.execute = AsyncMock(return_value=fut)
    return db


class TestListUsers:
    @pytest.mark.asyncio
    async def test_returns_users_with_free_tier(self, admin_user):
        user = _make_user(subscription_tier=SubscriptionTier.FREE, trial_ends_at=datetime(2025, 1, 1, tzinfo=UTC))
        db = _mock_db_for_scalars_all([user])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        assert len(result) == 1
        assert result[0].email == "test@example.com"
        assert result[0].monthly_message_limit == 100

    @pytest.mark.asyncio
    async def test_premium_tier_10k_limit(self, admin_user):
        user = _make_user(subscription_tier=SubscriptionTier.PREMIUM)
        db = _mock_db_for_scalars_all([user])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        assert result[0].monthly_message_limit == 10000

    @pytest.mark.asyncio
    async def test_enterprise_tier_10k_limit(self, admin_user):
        user = _make_user(subscription_tier=SubscriptionTier.ENTERPRISE)
        db = _mock_db_for_scalars_all([user])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        assert result[0].monthly_message_limit == 10000

    @pytest.mark.asyncio
    async def test_active_trial_10k_limit(self, admin_user):
        user = _make_user(subscription_tier=SubscriptionTier.FREE, trial_ends_at=datetime(2099, 1, 1, tzinfo=UTC))
        db = _mock_db_for_scalars_all([user])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        assert result[0].monthly_message_limit == 10000

    @pytest.mark.asyncio
    async def test_empty_list(self, admin_user):
        db = _mock_db_for_scalars_all([])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        assert result == []

    @pytest.mark.asyncio
    async def test_pagination(self, admin_user):
        db = _mock_db_for_scalars_all([])
        execute_call = AsyncMock(return_value=db.execute.return_value)
        db.execute = execute_call

        from app.api.routes.admin import list_users
        await list_users(page=3, per_page=20, db=db, admin=admin_user)
        stmt = execute_call.call_args[0][0]
        assert stmt._limit == 20

    @pytest.mark.asyncio
    async def test_full_field_mapping(self, admin_user):
        verified = datetime(2026, 5, 1, tzinfo=UTC)
        updated = datetime(2026, 6, 1, tzinfo=UTC)
        user = _make_user(
            display_name="Alice",
            is_superuser=True,
            verified_at=verified,
            subscription_tier=SubscriptionTier.PREMIUM,
            message_count=42,
            updated_at=updated,
        )
        db = _mock_db_for_scalars_all([user])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        item = result[0]
        assert item.display_name == "Alice"
        assert item.is_superuser is True
        assert item.verified_at == "2026-05-01T00:00:00+00:00"
        assert item.subscription_tier == "premium"
        assert item.message_count == 42
        assert item.last_active_at == "2026-06-01T00:00:00+00:00"

    @pytest.mark.asyncio
    async def test_unverified_user(self, admin_user):
        user = _make_user(verified_at=None)
        db = _mock_db_for_scalars_all([user])

        from app.api.routes.admin import list_users
        result = await list_users(db=db, admin=admin_user)
        assert result[0].verified_at is None


class TestGetUser:
    @pytest.mark.asyncio
    async def test_returns_user(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import get_user
        result = await get_user(user_id=user.id, db=db, admin=admin_user)
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, admin_user):
        db = _mock_db_for_scalar_one_or_none(None)

        from app.api.routes.admin import get_user
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await get_user(user_id="nonexistent", db=db, admin=admin_user)
        assert exc.value.status_code == 404


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_updates_is_active(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import update_user, UpdateUserRequest
        result = await update_user(user_id=user.id, req=UpdateUserRequest(is_active=False), db=db, admin=admin_user)
        assert result["status"] == "ok"
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_updates_is_superuser(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import update_user, UpdateUserRequest
        await update_user(user_id=user.id, req=UpdateUserRequest(is_superuser=True), db=db, admin=admin_user)
        assert user.is_superuser is True

    @pytest.mark.asyncio
    async def test_updates_subscription_tier(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import update_user, UpdateUserRequest
        await update_user(user_id=user.id, req=UpdateUserRequest(subscription_tier="premium"), db=db, admin=admin_user)
        assert user.subscription_tier == SubscriptionTier.PREMIUM

    @pytest.mark.asyncio
    async def test_updates_display_name(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import update_user, UpdateUserRequest
        await update_user(user_id=user.id, req=UpdateUserRequest(display_name="New Name"), db=db, admin=admin_user)
        assert user.display_name == "New Name"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, admin_user):
        db = _mock_db_for_scalar_one_or_none(None)

        from app.api.routes.admin import update_user, UpdateUserRequest
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await update_user(user_id="nonexistent", req=UpdateUserRequest(is_active=False), db=db, admin=admin_user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_tier_returns_400(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import update_user, UpdateUserRequest
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await update_user(
                user_id=user.id, req=UpdateUserRequest(subscription_tier="invalid_tier"), db=db, admin=admin_user
            )
        assert exc.value.status_code == 400
        assert "Invalid tier" in str(exc.value.detail)


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_disables_user(self, admin_user):
        user = _make_user()
        db = _mock_db_for_scalar_one_or_none(user)

        from app.api.routes.admin import delete_user
        result = await delete_user(user_id=user.id, db=db, admin=admin_user)
        assert result["detail"] == "User disabled"
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, admin_user):
        db = _mock_db_for_scalar_one_or_none(None)

        from app.api.routes.admin import delete_user
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await delete_user(user_id="nonexistent", db=db, admin=admin_user)
        assert exc.value.status_code == 404


class TestSystemStats:
    @pytest.mark.asyncio
    async def test_returns_all_stats(self, admin_user):
        db = MagicMock()

        scalar_values = iter([50, 30, 5, 20, 10, 3, 1000, 7, 12])

        async def execute_side(*args, **kwargs):
            fut = AsyncMock()
            val = next(scalar_values)
            fut.scalar = MagicMock(return_value=val)
            return fut

        db.execute = execute_side

        from app.api.routes.admin import system_stats
        result = await system_stats(db=db, admin=admin_user)
        assert result.total_users == 50
        assert result.active_users == 30
        assert result.superusers == 5
        assert result.free_users == 20
        assert result.premium_users == 10
        assert result.enterprise_users == 3
        assert result.total_messages == 1000
        assert result.users_on_trial == 7
        assert result.users_over_limit == 12

    @pytest.mark.asyncio
    async def test_returns_zeros_when_none(self, admin_user):
        db = MagicMock()

        async def execute_side(*args, **kwargs):
            fut = AsyncMock()
            fut.scalar = MagicMock(return_value=None)
            return fut

        db.execute = execute_side

        from app.api.routes.admin import system_stats
        result = await system_stats(db=db, admin=admin_user)
        assert result.total_users == 0
        assert result.active_users == 0
        assert result.superusers == 0
        assert result.free_users == 0
        assert result.premium_users == 0
        assert result.enterprise_users == 0
        assert result.total_messages == 0
        assert result.users_on_trial == 0
        assert result.users_over_limit == 0
