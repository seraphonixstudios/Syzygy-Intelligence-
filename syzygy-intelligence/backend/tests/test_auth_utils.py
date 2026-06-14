"""Tests for app/api/auth.py — JWT, password hashing, API keys, current user, usage limits."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.db.models import SubscriptionTier


class TestDecodeToken:
    def test_returns_none_on_unexpected_error(self):
        from app.api.auth import decode_token
        with patch("jwt.decode", side_effect=Exception("unexpected")):
            result = decode_token("some.token.here")
            assert result is None


class TestGenerateApiKey:
    def test_returns_three_values(self):
        from app.api.auth import generate_api_key
        raw, hashed, searchable = generate_api_key()
        assert raw.startswith("syzygy_")
        assert hashed != raw
        assert len(searchable) == 16


class TestComputeSearchableHash:
    def test_returns_deterministic_hash(self):
        from app.api.auth import _compute_searchable_hash
        h1 = _compute_searchable_hash("test-key")
        h2 = _compute_searchable_hash("test-key")
        assert h1 == h2
        assert len(h1) == 16


class TestToUtc:
    def test_handles_naive_datetime(self):
        from app.api.auth import _to_utc
        from datetime import datetime
        naive = datetime(2026, 1, 1, 12, 0, 0)
        result = _to_utc(naive)
        assert result.tzinfo is not None
        assert result.hour == 12  # Same hour since we just attach UTC

    def test_handles_none(self):
        from app.api.auth import _to_utc
        assert _to_utc(None) is None

    def test_handles_aware_datetime(self):
        from app.api.auth import _to_utc
        from datetime import timezone, timedelta
        aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        result = _to_utc(aware)
        assert result.hour == 7  # 12 - 5 = 7 UTC


class TestRequireUser:
    @pytest.mark.asyncio
    async def test_returns_user_when_authenticated(self):
        from app.api.auth import require_user
        user = MagicMock()
        result = await require_user(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_raises_when_not_authenticated(self):
        from app.api.auth import require_user
        with pytest.raises(HTTPException) as exc:
            await require_user(None)
        assert exc.value.status_code == 401


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_returns_user_when_superuser(self):
        from app.api.auth import require_admin
        user = MagicMock()
        user.is_superuser = True
        result = await require_admin(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_raises_when_not_superuser(self):
        from app.api.auth import require_admin
        user = MagicMock()
        user.is_superuser = False
        with pytest.raises(HTTPException) as exc:
            await require_admin(user)
        assert exc.value.status_code == 403


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_credentials(self):
        from app.api.auth import get_current_user
        result = await get_current_user(None, AsyncMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticates_via_jwt(self):
        from app.api.auth import get_current_user, create_access_token
        from fastapi.security import HTTPAuthorizationCredentials
        uid = str(uuid.uuid4())
        token = create_access_token(uid, "test@example.com")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = MagicMock()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        db.execute.return_value = result
        authenticated = await get_current_user(creds, db)
        assert authenticated is user

    @pytest.mark.asyncio
    async def test_falls_back_to_api_key(self):
        from app.api.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="api_key_xyz")
        db = AsyncMock()
        with patch("app.api.auth.authenticate_api_key", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = MagicMock()
            user = await get_current_user(creds, db)
            assert user is not None


class TestSendEmail:
    @pytest.mark.asyncio
    async def test_sends_email(self):
        from app.api.auth import send_email
        from app.services.email import EmailMessage
        msg = EmailMessage(to="test@test.com", subject="Test", text_body="body")
        mock_sender = AsyncMock()
        with (
            patch("app.api.auth.create_email_sender", return_value=mock_sender),
            patch("app.api.auth.settings") as ms,
        ):
            ms.email_provider = "console"
            ms.sendgrid_api_key = ""
            ms.ses_region = ""
            ms.ses_access_key_id = ""
            ms.ses_secret_access_key = ""
            ms.email_from_address = "noreply@syzygy.ai"
            ms.email_from_name = "Syzygy"
            await send_email(msg)
            mock_sender.send.assert_awaited_once_with(msg)


class TestAuthenticateApiKey:
    @pytest.mark.asyncio
    async def test_returns_none_when_key_not_found(self):
        from app.api.auth import authenticate_api_key, generate_api_key
        raw, _, _ = generate_api_key()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result
        user = await authenticate_api_key(raw, db)
        assert user is None

    @pytest.mark.asyncio
    async def test_returns_none_on_hash_mismatch(self):
        from app.api.auth import authenticate_api_key, generate_api_key
        raw, _, _ = generate_api_key()
        db = AsyncMock()
        api_key = MagicMock()
        api_key.hashed_key = "different_hash"
        api_key.id = uuid.uuid4()
        api_key.is_active = True
        result = MagicMock()
        result.scalar_one_or_none.return_value = api_key
        db.execute.return_value = result
        user = await authenticate_api_key(raw, db)
        assert user is None

    @pytest.mark.asyncio
    async def test_logs_update_failure(self):
        from app.api.auth import authenticate_api_key, generate_api_key
        raw, hashed, _ = generate_api_key()
        db = AsyncMock()
        api_key = MagicMock()
        api_key.hashed_key = hashed
        api_key.id = uuid.uuid4()
        api_key.is_active = True
        api_key.user = MagicMock()
        result_find = MagicMock()
        result_find.scalar_one_or_none.return_value = api_key
        db.execute = AsyncMock(side_effect=[result_find, Exception("update failed")])
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        user = await authenticate_api_key(raw, db)
        assert user is not None
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_on_generic_exception(self):
        from app.api.auth import authenticate_api_key
        db = AsyncMock()
        db.execute.side_effect = Exception("DB down")
        user = await authenticate_api_key("some_key", db)
        assert user is None


class TestCheckUsageLimit:
    @pytest.mark.asyncio
    async def test_returns_user_when_under_limit(self):
        from app.api.auth import check_usage_limit
        user = MagicMock()
        user.subscription_tier = SubscriptionTier.FREE
        user.trial_ends_at = None
        user.message_count = 50
        user.usage_reset_at = datetime.now(UTC)
        result = await check_usage_limit(user=user, db=AsyncMock())
        assert result is user

    @pytest.mark.asyncio
    async def test_raises_when_over_free_limit(self):
        from app.api.auth import check_usage_limit, settings
        from app.errors import SyzygyError
        user = MagicMock()
        user.subscription_tier = SubscriptionTier.FREE
        user.trial_ends_at = None
        user.message_count = settings.free_tier_monthly_messages + 1
        user.usage_reset_at = datetime.now(UTC)
        with pytest.raises(SyzygyError) as exc:
            await check_usage_limit(user=user, db=AsyncMock())
        assert exc.value.status_code == 429


class TestCreatePasswordResetToken:
    def test_creates_token(self):
        from app.api.auth import create_password_reset_token, decode_token
        uid = str(uuid.uuid4())
        token = create_password_reset_token(uid)
        payload = decode_token(token)
        assert payload["sub"] == uid
        assert payload["type"] == "password_reset"


class TestCreateVerificationToken:
    def test_creates_token(self):
        from app.api.auth import create_verification_token, decode_token
        uid = str(uuid.uuid4())
        token = create_verification_token(uid)
        payload = decode_token(token)
        assert payload["sub"] == uid
        assert payload["type"] == "email_verification"
