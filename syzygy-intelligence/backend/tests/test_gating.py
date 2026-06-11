"""Unit tests for usage gating and authentication utilities."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models import SubscriptionTier


class TestPasswordHashing:
    def test_hash_and_verify_password(self):
        from app.api.auth import hash_password, verify_password
        pw = "secure_password_123"
        h = hash_password(pw)
        assert h != pw
        assert verify_password(pw, h)
        assert not verify_password("wrong", h)

    def test_hash_is_different_each_time(self):
        from app.api.auth import hash_password
        pw = "same_password"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2


class TestTokenCreation:
    def test_create_and_decode_access_token(self):
        from app.api.auth import create_access_token, decode_token
        uid = str(uuid.uuid4())
        email = "test@example.com"
        token = create_access_token(uid, email)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == uid
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        from app.api.auth import create_refresh_token, decode_token
        uid = str(uuid.uuid4())
        email = "test@example.com"
        token = create_refresh_token(uid, email)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_returns_none(self):
        from app.api.auth import decode_token
        assert decode_token("invalid.token.here") is None

    def test_decode_expired_token_returns_none(self):
        from app.api.auth import create_access_token, decode_token
        uid = str(uuid.uuid4())
        with patch("app.api.auth.settings.access_token_expire_minutes", -1):
            token = create_access_token(uid, "test@example.com")
        assert decode_token(token) is None


class TestApiKeyAuth:
    @pytest.mark.asyncio
    async def test_generate_api_key_returns_tuple(self):
        from app.api.auth import generate_api_key
        raw, hashed = generate_api_key()
        assert raw.startswith("syzygy_")
        assert len(raw) > 10
        assert hashed != raw

    @pytest.mark.asyncio
    async def test_authenticate_api_key_valid(self):
        from app.api.auth import authenticate_api_key, generate_api_key
        raw, hashed = generate_api_key()
        user = MagicMock()
        user.id = uuid.uuid4()

        api_key = MagicMock()
        api_key.hashed_key = hashed
        api_key.is_active = True
        api_key.user = user

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [api_key]
        db.execute.return_value = result

        result_user = await authenticate_api_key(raw, db)
        assert result_user is user
        db.add.assert_called_once_with(api_key)
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_authenticate_api_key_invalid(self):
        from app.api.auth import authenticate_api_key, generate_api_key, hash_password
        raw, _ = generate_api_key()
        different_hashed = hash_password("some_other_key_value_12345")
        other_key = MagicMock()
        other_key.hashed_key = different_hashed
        other_key.is_active = True
        other_key.user = MagicMock()

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [other_key]
        db.execute.return_value = result

        result_user = await authenticate_api_key(raw, db)
        assert result_user is None

    @pytest.mark.asyncio
    async def test_authenticate_api_key_empty_db(self):
        from app.api.auth import authenticate_api_key
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        assert await authenticate_api_key("some_key", db) is None


class TestCheckUsageLimit:
    def _make_user(self, **overrides):
        now = datetime.now(UTC)
        defaults = dict(
            subscription_tier=SubscriptionTier.FREE,
            trial_ends_at=now - timedelta(days=1),
            usage_reset_at=now,
            message_count=0,
        )
        defaults.update(overrides)
        user = MagicMock()
        for k, v in defaults.items():
            setattr(user, k, v)
        return user

    @pytest.mark.asyncio
    async def test_returns_user_on_active_trial(self):
        from app.api.auth import check_usage_limit
        user = self._make_user(
            trial_ends_at=datetime.now(UTC) + timedelta(days=7),
            message_count=9999,
        )
        result = await check_usage_limit(user=user, db=AsyncMock())
        assert result is user

    @pytest.mark.asyncio
    async def test_returns_user_on_premium_tier(self):
        from app.api.auth import check_usage_limit
        user = self._make_user(
            subscription_tier=SubscriptionTier.PREMIUM,
            trial_ends_at=None,
        )
        result = await check_usage_limit(user=user, db=AsyncMock())
        assert result is user

    @pytest.mark.asyncio
    async def test_returns_user_on_enterprise_tier(self):
        from app.api.auth import check_usage_limit
        user = self._make_user(
            subscription_tier=SubscriptionTier.ENTERPRISE,
            trial_ends_at=None,
        )
        result = await check_usage_limit(user=user, db=AsyncMock())
        assert result is user

    @pytest.mark.asyncio
    async def test_raises_429_when_exceeded(self):
        from fastapi import HTTPException

        from app.api.auth import check_usage_limit, settings

        limit = settings.free_tier_monthly_messages
        user = self._make_user(message_count=limit + 1)
        with pytest.raises(HTTPException) as exc:
            await check_usage_limit(user=user, db=AsyncMock())
        assert exc.value.status_code == 429
        assert exc.value.detail["code"] == "USAGE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_resets_counter_new_month(self):
        from app.api.auth import check_usage_limit

        user = self._make_user(
            usage_reset_at=datetime.now(UTC) - timedelta(days=40),
            message_count=50,
        )
        result = await check_usage_limit(user=user, db=AsyncMock())
        assert result is user

    @pytest.mark.asyncio
    async def test_trial_ends_at_none_still_limited(self):
        from fastapi import HTTPException

        from app.api.auth import check_usage_limit, settings

        limit = settings.free_tier_monthly_messages
        user = self._make_user(trial_ends_at=None, message_count=limit + 1)
        with pytest.raises(HTTPException) as exc:
            await check_usage_limit(user=user, db=AsyncMock())
        assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_expired_trial_still_limited(self):
        from fastapi import HTTPException

        from app.api.auth import check_usage_limit, settings

        limit = settings.free_tier_monthly_messages
        user = self._make_user(message_count=limit + 1)
        with pytest.raises(HTTPException):
            await check_usage_limit(user=user, db=AsyncMock())
