"""Tests for auth route handlers — register, login, refresh, me, settings, password reset, API keys."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.auth import create_access_token, create_refresh_token


def _make_user(**overrides):
    now = datetime.now(UTC)
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.hashed_password = "$2b$12$fakehash"
    user.is_active = True
    user.is_superuser = False
    user.verified_at = None
    user.trial_ends_at = now + timedelta(days=7)
    user.subscription_tier = MagicMock()
    user.subscription_tier.value = "free"
    user.message_count = 5
    user.usage_reset_at = now
    user.settings = {"theme": "dark"}
    user.created_at = now
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


def _make_api_key(**overrides):
    k = MagicMock()
    k.id = uuid.uuid4()
    k.name = "My Key"
    k.key_prefix = "syzygy_abc"
    k.hashed_key = "fake_hashed"
    k.searchable_key_hash = "fake_searchable"
    k.is_active = True
    k.last_used_at = None
    k.created_at = datetime.now(UTC)
    for attr, val in overrides.items():
        setattr(k, attr, val)
    return k


class MockUserDepends:
    """Simulate FastAPI Depends(require_user) by returning this user."""
    def __init__(self, user=None):
        self.user = user or _make_user()


@pytest.fixture(autouse=True)
def _patch_deps():
    with (
        patch("app.api.routes.auth.require_user") as mock_req_user,
        patch("app.api.routes.auth.get_db") as mock_get_db,
        patch("app.api.routes.auth.send_email") as mock_send,
        patch("app.api.routes.auth.settings") as mock_settings,
    ):
        mock_settings.frontend_url = "http://localhost:3000"
        mock_settings.email_provider = "console"
        mock_settings.free_tier_days = 14
        mock_settings.free_tier_monthly_messages = 100
        mock_settings.premium_monthly_messages = 1000
        mock_settings.cors_origins = "http://localhost:3000"

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_get_db.return_value = mock_db

        yield {
            "require_user": mock_req_user,
            "get_db": mock_get_db,
            "send_email": mock_send,
            "settings": mock_settings,
            "db": mock_db,
        }


class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_sends_reset_email_when_user_found(self, _patch_deps):
        from app.api.routes.auth import forgot_password, ForgotPasswordRequest
        user = _make_user()
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        resp = await forgot_password(ForgotPasswordRequest(email="test@example.com"), _patch_deps["db"])
        assert resp["message"] == "If that email exists, a reset link has been sent."
        _patch_deps["send_email"].assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_same_message_when_user_not_found(self, _patch_deps):
        from app.api.routes.auth import forgot_password, ForgotPasswordRequest
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        _patch_deps["db"].execute.return_value = result

        resp = await forgot_password(ForgotPasswordRequest(email="missing@example.com"), _patch_deps["db"])
        assert resp["message"] == "If that email exists, a reset link has been sent."
        _patch_deps["send_email"].assert_not_called()


class TestResetPassword:
    @pytest.mark.asyncio
    async def test_resets_password_successfully(self, _patch_deps):
        from app.api.routes.auth import reset_password, ResetPasswordRequest
        from app.api.auth import create_password_reset_token
        user = _make_user()
        token = create_password_reset_token(str(user.id))

        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result_user

        resp = await reset_password(ResetPasswordRequest(token=token, new_password="new_pass"), _patch_deps["db"])
        assert resp["message"] == "Password has been reset successfully."

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self, _patch_deps):
        from app.api.routes.auth import reset_password, ResetPasswordRequest
        with pytest.raises(HTTPException) as exc:
            await reset_password(ResetPasswordRequest(token="bad_token", new_password="new_pass"), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestSendVerification:
    @pytest.mark.asyncio
    async def test_sends_verification_email(self, _patch_deps):
        from app.api.routes.auth import send_verification, SendVerificationRequest
        user = _make_user(verified_at=None)
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        resp = await send_verification(SendVerificationRequest(email="test@example.com"), _patch_deps["db"])
        assert "verification_token" in resp
        _patch_deps["send_email"].assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_already_verified(self, _patch_deps):
        from app.api.routes.auth import send_verification, SendVerificationRequest
        user = _make_user(verified_at=datetime.now(UTC))
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        resp = await send_verification(SendVerificationRequest(email="test@example.com"), _patch_deps["db"])
        assert "message" in resp


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_verifies_email_successfully(self, _patch_deps):
        from app.api.routes.auth import verify_email, VerifyEmailRequest
        from app.api.auth import create_verification_token
        user = _make_user(verified_at=None)
        token = create_verification_token(str(user.id))

        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        resp = await verify_email(VerifyEmailRequest(token=token), _patch_deps["db"])
        assert resp["message"] == "Email verified successfully."

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self, _patch_deps):
        from app.api.routes.auth import verify_email, VerifyEmailRequest
        with pytest.raises(HTTPException) as exc:
            await verify_email(VerifyEmailRequest(token="bad"), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestRegister:
    @pytest.mark.asyncio
    async def test_registers_new_user(self, _patch_deps):
        from app.api.routes.auth import register, RegisterRequest
        result = MagicMock()
        result.scalar_one_or_none.return_value = None  # No existing user
        _patch_deps["db"].execute.return_value = result

        resp = await register(RegisterRequest(email="new@example.com", password="secret"), _patch_deps["db"])
        assert resp.access_token
        assert resp.refresh_token

    @pytest.mark.asyncio
    async def test_rejects_duplicate_email(self, _patch_deps):
        from app.api.routes.auth import register, RegisterRequest
        result = MagicMock()
        result.scalar_one_or_none.return_value = _make_user()
        _patch_deps["db"].execute.return_value = result

        with pytest.raises(HTTPException) as exc:
            await register(RegisterRequest(email="existing@example.com", password="secret"), _patch_deps["db"])
        assert exc.value.status_code == 409


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, _patch_deps):
        from app.api.routes.auth import login, LoginRequest
        from app.api.auth import hash_password
        user = _make_user(hashed_password=hash_password("correct_pass"))
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        resp = await login(LoginRequest(email="test@example.com", password="correct_pass"), _patch_deps["db"])
        assert resp.access_token

    @pytest.mark.asyncio
    async def test_rejects_wrong_password(self, _patch_deps):
        from app.api.routes.auth import login, LoginRequest
        from app.api.auth import hash_password
        user = _make_user(hashed_password=hash_password("correct_pass"))
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        with pytest.raises(HTTPException) as exc:
            await login(LoginRequest(email="test@example.com", password="wrong"), _patch_deps["db"])
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_disabled_account(self, _patch_deps):
        from app.api.routes.auth import login, LoginRequest
        from app.api.auth import hash_password
        user = _make_user(is_active=False, hashed_password=hash_password("pass"))
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result

        with pytest.raises(HTTPException) as exc:
            await login(LoginRequest(email="test@example.com", password="pass"), _patch_deps["db"])
        assert exc.value.status_code == 403


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        uid = str(uuid.uuid4())
        token = create_refresh_token(uid, "test@example.com")
        resp = await refresh(RefreshRequest(refresh_token=token))
        assert resp.access_token
        assert resp.refresh_token

    @pytest.mark.asyncio
    async def test_rejects_invalid_refresh_token(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        with pytest.raises(HTTPException) as exc:
            await refresh(RefreshRequest(refresh_token="bad"))
        assert exc.value.status_code == 401


class TestGetMe:
    @pytest.mark.asyncio
    async def test_returns_user_response(self, _patch_deps):
        from app.api.routes.auth import get_me
        user = _make_user()
        resp = await get_me(user, _patch_deps["db"])
        assert resp.email == user.email
        assert resp.subscription_tier == "free"


class TestUpdateSettings:
    @pytest.mark.asyncio
    async def test_updates_settings(self, _patch_deps):
        from app.api.routes.auth import update_settings, UpdateSettingsRequest
        user = _make_user()
        resp = await update_settings(UpdateSettingsRequest(settings={"theme": "light"}), user, _patch_deps["db"])
        assert resp["status"] == "ok"


class TestCreateApiKey:
    @pytest.mark.asyncio
    async def test_creates_api_key(self, _patch_deps):
        from app.api.routes.auth import create_api_key, CreateApiKeyRequest
        from datetime import UTC, datetime
        from app.db.models import ApiKey
        user = _make_user()
        # The real ApiKey model's default=func.now() is not evaluated until DB flush
        # Patch refresh to set ORM defaults not applied without real flush
        _patch_deps["db"].commit = AsyncMock()
        now = datetime.now(UTC)

        async def _refresh(obj):
            obj.created_at = now
            obj.is_active = True

        _patch_deps["db"].refresh = AsyncMock(side_effect=_refresh)

        resp = await create_api_key(CreateApiKeyRequest(name="Test Key"), user, _patch_deps["db"])
        assert resp.name == "Test Key"
        assert resp.raw_key.startswith("syzygy_")
        assert resp.is_active


class TestListApiKeys:
    @pytest.mark.asyncio
    async def test_lists_api_keys(self, _patch_deps):
        from app.api.routes.auth import list_api_keys
        user = _make_user()
        api_keys = [_make_api_key(), _make_api_key(name="Key 2")]
        result = MagicMock()
        result.scalars.return_value.all.return_value = api_keys
        _patch_deps["db"].execute.return_value = result

        resp = await list_api_keys(user, _patch_deps["db"])
        assert len(resp.keys) == 2


class TestRevokeApiKey:
    @pytest.mark.asyncio
    async def test_revokes_api_key(self, _patch_deps):
        from app.api.routes.auth import revoke_api_key
        user = _make_user()
        api_key = _make_api_key()
        result = MagicMock()
        result.scalar_one_or_none.return_value = api_key
        _patch_deps["db"].execute.return_value = result

        resp = await revoke_api_key(str(api_key.id), user, _patch_deps["db"])
        assert resp["status"] == "revoked"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, _patch_deps):
        from app.api.routes.auth import revoke_api_key
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        _patch_deps["db"].execute.return_value = result

        with pytest.raises(HTTPException) as exc:
            await revoke_api_key(str(uuid.uuid4()), _make_user(), _patch_deps["db"])
        assert exc.value.status_code == 404


class TestExpireTrial:
    @pytest.mark.asyncio
    async def test_expires_trial(self, _patch_deps):
        from app.api.routes.auth import expire_trial
        user = _make_user()
        resp = await expire_trial(user, _patch_deps["db"])
        assert resp["trial_ends_at"] is None
        assert resp["message_count"] == 100


class TestChargeMessage:
    @pytest.mark.asyncio
    async def test_charges_message(self, _patch_deps):
        from app.api.routes.auth import charge_message
        user = _make_user()
        result = MagicMock()
        result.scalar_one.return_value = 6
        _patch_deps["db"].execute.return_value = result

        resp = await charge_message(user, _patch_deps["db"])
        assert resp["message_count"] == 6


class TestUserToResponse:
    def test_premium_user_gets_premium_limit(self):
        from app.api.routes.auth import _user_to_response
        user = _make_user()
        user.subscription_tier.value = "premium"
        resp = _user_to_response(user)
        assert resp.monthly_message_limit == 1000

    def test_free_user_gets_free_limit(self):
        from app.api.routes.auth import _user_to_response
        user = _make_user(trial_ends_at=datetime.now(UTC) - timedelta(days=1))
        resp = _user_to_response(user)
        assert resp.monthly_message_limit == 100

    def test_trial_user_gets_premium_limit(self):
        from app.api.routes.auth import _user_to_response
        user = _make_user(trial_ends_at=datetime.now(UTC) + timedelta(days=1))
        resp = _user_to_response(user)
        assert resp.monthly_message_limit == 1000


class TestResetUsageIfNeeded:
    @pytest.mark.asyncio
    async def test_resets_when_new_month(self, _patch_deps):
        from app.api.routes.auth import _reset_usage_if_needed
        user = _make_user(usage_reset_at=datetime.now(UTC) - timedelta(days=40))
        await _reset_usage_if_needed(user, _patch_deps["db"])
        assert user.message_count == 0

    @pytest.mark.asyncio
    async def test_does_not_reset_within_same_month(self, _patch_deps):
        from app.api.routes.auth import _reset_usage_if_needed
        user = _make_user(message_count=5)
        await _reset_usage_if_needed(user, _patch_deps["db"])
        assert user.message_count == 5


class TestForgotPasswordEdgeCases:
    @pytest.mark.asyncio
    async def test_email_failure_non_console_raises(self, _patch_deps):
        from app.api.routes.auth import forgot_password, ForgotPasswordRequest
        _patch_deps["settings"].email_provider = "smtp"
        user = _make_user()
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result
        _patch_deps["send_email"].side_effect = RuntimeError("SMTP down")

        with pytest.raises(HTTPException) as exc:
            await forgot_password(ForgotPasswordRequest(email="test@example.com"), _patch_deps["db"])
        assert exc.value.status_code == 503


class TestSendVerificationEdgeCases:
    @pytest.mark.asyncio
    async def test_email_failure_non_console_raises(self, _patch_deps):
        from app.api.routes.auth import send_verification, SendVerificationRequest
        _patch_deps["settings"].email_provider = "smtp"
        user = _make_user(verified_at=None)
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        _patch_deps["db"].execute.return_value = result
        _patch_deps["send_email"].side_effect = RuntimeError("SMTP down")

        with pytest.raises(HTTPException) as exc:
            await send_verification(SendVerificationRequest(email="test@example.com"), _patch_deps["db"])
        assert exc.value.status_code == 503


class TestResetPasswordEdgeCases:
    @pytest.mark.asyncio
    async def test_rejects_token_without_sub(self, _patch_deps):
        from app.api.routes.auth import reset_password, ResetPasswordRequest
        import jwt
        token = jwt.encode({"type": "password_reset", "sub": None}, "secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await reset_password(ResetPasswordRequest(token=token, new_password="new"), _patch_deps["db"])
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_user_not_found(self, _patch_deps):
        from app.api.routes.auth import reset_password, ResetPasswordRequest
        from app.api.auth import create_password_reset_token
        from unittest.mock import PropertyMock
        user_id = str(uuid.uuid4())
        token = create_password_reset_token(user_id)
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        _patch_deps["db"].execute.return_value = result

        with pytest.raises(HTTPException) as exc:
            await reset_password(ResetPasswordRequest(token=token, new_password="new"), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestVerifyEmailEdgeCases:
    @pytest.mark.asyncio
    async def test_rejects_token_without_sub(self, _patch_deps):
        from app.api.routes.auth import verify_email, VerifyEmailRequest
        import jwt
        token = jwt.encode({"type": "email_verification", "sub": None}, "secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await verify_email(VerifyEmailRequest(token=token), _patch_deps["db"])
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_user_not_found(self, _patch_deps):
        from app.api.routes.auth import verify_email, VerifyEmailRequest
        from app.api.auth import create_verification_token
        user_id = str(uuid.uuid4())
        token = create_verification_token(user_id)
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        _patch_deps["db"].execute.return_value = result

        with pytest.raises(HTTPException) as exc:
            await verify_email(VerifyEmailRequest(token=token), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestRefreshEdgeCases:
    @pytest.mark.asyncio
    async def test_rejects_token_without_sub_or_email(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        import jwt
        token = jwt.encode({"type": "refresh", "sub": None, "email": None}, "secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await refresh(RefreshRequest(refresh_token=token))
        assert exc.value.status_code == 401


class TestUserToResponseEdgeCases:
    def test_enterprise_user_gets_premium_limit(self):
        from app.db.models import SubscriptionTier
        from app.api.routes.auth import _user_to_response
        user = _make_user(subscription_tier=SubscriptionTier.ENTERPRISE)
        resp = _user_to_response(user)
        assert resp.monthly_message_limit == 1000

    def test_premium_user_gets_premium_limit(self):
        from app.db.models import SubscriptionTier
        from app.api.routes.auth import _user_to_response
        user = _make_user(subscription_tier=SubscriptionTier.PREMIUM)
        resp = _user_to_response(user)
        assert resp.monthly_message_limit == 1000


class TestVerifyEmailSubNone:
    @pytest.mark.asyncio
    async def test_rejects_token_without_sub(self, _patch_deps):
        from app.api.routes.auth import verify_email, VerifyEmailRequest
        import jwt
        token = jwt.encode({"type": "email_verification", "sub": None}, "secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await verify_email(VerifyEmailRequest(token=token), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestRefreshSubOrEmailNone:
    @pytest.mark.asyncio
    async def test_rejects_token_without_sub(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        import jwt
        token = jwt.encode({"type": "refresh", "sub": None, "email": "test@example.com"}, "secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await refresh(RefreshRequest(refresh_token=token))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_token_without_email(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        import jwt
        token = jwt.encode({"type": "refresh", "sub": "user-1", "email": None}, "secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await refresh(RefreshRequest(refresh_token=token))
        assert exc.value.status_code == 401


class TestResetPasswordSubNoneWithValidToken:
    @pytest.mark.asyncio
    async def test_reset_password_token_with_sub_none(self, _patch_deps):
        from app.api.routes.auth import reset_password, ResetPasswordRequest
        from app.config import settings
        import jwt
        token = jwt.encode(
            {"type": "password_reset", "sub": None},
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(HTTPException) as exc:
            await reset_password(ResetPasswordRequest(token=token, new_password="new"), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestVerifyEmailSubNoneWithValidToken:
    @pytest.mark.asyncio
    async def test_verify_email_token_with_sub_none(self, _patch_deps):
        from app.api.routes.auth import verify_email, VerifyEmailRequest
        from app.config import settings
        import jwt
        token = jwt.encode(
            {"type": "email_verification", "sub": None},
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(HTTPException) as exc:
            await verify_email(VerifyEmailRequest(token=token), _patch_deps["db"])
        assert exc.value.status_code == 400


class TestRefreshTokenSubEmailNoneWithValidToken:
    @pytest.mark.asyncio
    async def test_refresh_token_with_sub_none_valid_key(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        from app.config import settings
        import jwt
        token = jwt.encode(
            {"type": "refresh", "sub": None, "email": "test@example.com"},
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(HTTPException) as exc:
            await refresh(RefreshRequest(refresh_token=token))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_with_email_none_valid_key(self, _patch_deps):
        from app.api.routes.auth import refresh, RefreshRequest
        from app.config import settings
        import jwt
        token = jwt.encode(
            {"type": "refresh", "sub": "user-1", "email": None},
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(HTTPException) as exc:
            await refresh(RefreshRequest(refresh_token=token))
        assert exc.value.status_code == 401
