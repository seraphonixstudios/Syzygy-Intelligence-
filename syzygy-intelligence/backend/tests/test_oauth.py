"""Tests for OAuth routes — Google and GitHub social login."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routes.oauth import oauth_callback, oauth_redirect
from app.db.models import SubscriptionTier

# Provider config templates — patched directly since PROVIDER_CONFIGS
# is evaluated at module import time (settings values are baked in).
GOOGLE_CFG = {
    "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
    "client_id": "google-id-123",
    "client_secret": "google-secret",
    "scope": "openid email profile",
}

GITHUB_CFG = {
    "authorize_url": "https://github.com/login/oauth/authorize",
    "token_url": "https://github.com/login/oauth/access_token",
    "userinfo_url": "https://api.github.com/user",
    "client_id": "github-id-456",
    "client_secret": "github-secret",
    "scope": "read:user user:email",
}

GOOGLE_UNCONFIGURED = {**GOOGLE_CFG, "client_id": ""}

MOCK_TOKEN = {"access_token": "provider-access-token-abc", "token_type": "bearer"}
MOCK_GOOGLE_USERINFO = {"email": "alice@gmail.com", "name": "Alice Smith", "given_name": "Alice"}
MOCK_GITHUB_USERINFO = {"email": "bob@github.com", "name": "Bob Developer", "login": "bob-dev"}


def _mock_httpx(mock_client_cls, post_return, get_return=None, get_side_effect=None):
    mock_client = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client
    mock_client.post.return_value = post_return
    if get_side_effect:
        mock_client.get.side_effect = get_side_effect
    else:
        mock_client.get.return_value = get_return
    return mock_client


def _mock_session_factory(existing_user=None):
    async def fake_execute(stmt):
        fut = AsyncMock()
        fut.scalar_one_or_none = MagicMock(return_value=existing_user)
        return fut

    session = AsyncMock()
    session.execute = fake_execute
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    factory = MagicMock()
    factory.return_value.__aenter__.return_value = session
    return factory, session


def _patch_auth_tokens():
    return patch.multiple(
        "app.api.routes.oauth",
        create_access_token=MagicMock(return_value="our-access-token"),
        create_refresh_token=MagicMock(return_value="our-refresh-token"),
    )


class TestOAuthRedirect:
    def test_unknown_provider_returns_404(self):
        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                import inspect
                oauth_redirect(provider="unknown", request=MagicMock())
                # Actually it's async so we need to handle differently

    @pytest.mark.asyncio
    async def test_unknown_provider_returns_404(self):
        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_redirect(provider="unknown", request=MagicMock())
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_unconfigured_provider_returns_501(self):
        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_UNCONFIGURED}):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_redirect(provider="google", request=MagicMock())
            assert exc.value.status_code == 501

    @pytest.mark.asyncio
    async def test_google_redirect(self):
        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("app.api.routes.oauth.settings.oauth_redirect_url", "http://localhost:8001/api/auth"):
            result = await oauth_redirect(provider="google", request=MagicMock())
            assert result.status_code == 307
            loc = result.headers["location"]
            assert "accounts.google.com" in loc
            assert "google-id-123" in loc

    @pytest.mark.asyncio
    async def test_github_redirect(self):
        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"github": GITHUB_CFG}), \
             patch("app.api.routes.oauth.settings.oauth_redirect_url", "http://localhost:8001/api/auth"):
            result = await oauth_redirect(provider="github", request=MagicMock())
            assert result.status_code == 307
            loc = result.headers["location"]
            assert "github.com/login/oauth/authorize" in loc
            assert "github-id-456" in loc


class TestOAuthCallback:
    @pytest.mark.asyncio
    async def test_unknown_provider_returns_404(self):
        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_callback(provider="unknown", code="abc", request=MagicMock())
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_token_exchange_failure_returns_400(self):
        token_resp = MagicMock(status_code=401, text="unauthorized")

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp)
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_callback(provider="google", code="abc", request=MagicMock())
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_access_token_returns_400(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = {"token_type": "bearer"}

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp)
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_callback(provider="google", code="abc", request=MagicMock())
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_userinfo_fetch_failure_returns_400(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=403, text="forbidden")

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo_resp)
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_callback(provider="google", code="abc", request=MagicMock())
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_email_returns_400(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo = MagicMock(status_code=200)
        userinfo.json.return_value = {"name": "No Email"}

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo)
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await oauth_callback(provider="google", code="abc", request=MagicMock())
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_new_google_user_created(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = MOCK_GOOGLE_USERINFO

        factory, session = _mock_session_factory(existing_user=None)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo_resp)

            result = await oauth_callback(provider="google", code="abc", request=MagicMock())
            assert result.status_code == 307
            assert "our-access-token" in result.headers["location"]
            assert "our-refresh-token" in result.headers["location"]
            session.add.assert_called_once()
            added_user = session.add.call_args[0][0]
            assert added_user.email == "alice@gmail.com"
            assert added_user.display_name == "Alice Smith"
            assert added_user.hashed_password == ""
            assert added_user.verified_at is not None

    @pytest.mark.asyncio
    async def test_new_github_user_created(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = MOCK_GITHUB_USERINFO

        factory, session = _mock_session_factory(existing_user=None)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"github": GITHUB_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo_resp)

            result = await oauth_callback(provider="github", code="abc", request=MagicMock())
            assert result.status_code == 307
            added_user = session.add.call_args[0][0]
            assert added_user.email == "bob@github.com"
            assert added_user.display_name == "Bob Developer"

    @pytest.mark.asyncio
    async def test_existing_user_found(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = MOCK_GOOGLE_USERINFO

        existing_user = MagicMock()
        existing_user.verified_at = datetime(2026, 1, 1, tzinfo=UTC)

        factory, session = _mock_session_factory(existing_user=existing_user)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo_resp)

            result = await oauth_callback(provider="google", code="abc", request=MagicMock())
            assert result.status_code == 307
            session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_existing_unverified_user_gets_verified(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = MOCK_GOOGLE_USERINFO

        existing_user = MagicMock()
        existing_user.verified_at = None

        factory, session = _mock_session_factory(existing_user=existing_user)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo_resp)

            await oauth_callback(provider="google", code="abc", request=MagicMock())
            session.add.assert_called_once()
            assert existing_user.verified_at is not None

    @pytest.mark.asyncio
    async def test_github_user_without_email_in_userinfo(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = {"login": "bob-dev", "name": "Bob"}
        emails_resp = MagicMock(status_code=200)
        emails_resp.json.return_value = [
            {"email": "bob@primary.com", "primary": True, "verified": True},
        ]

        factory, session = _mock_session_factory(existing_user=None)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"github": GITHUB_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, get_side_effect=[userinfo_resp, emails_resp])

            result = await oauth_callback(provider="github", code="abc", request=MagicMock())
            assert result.status_code == 307
            added_user = session.add.call_args[0][0]
            assert added_user.email == "bob@primary.com"

    @pytest.mark.asyncio
    async def test_github_user_email_fallback_to_first(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = {"login": "bob-dev"}
        emails_resp = MagicMock(status_code=200)
        emails_resp.json.return_value = [
            {"email": "bob@first.com", "primary": False, "verified": False},
        ]

        factory, session = _mock_session_factory(existing_user=None)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"github": GITHUB_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, get_side_effect=[userinfo_resp, emails_resp])

            result = await oauth_callback(provider="github", code="abc", request=MagicMock())
            assert result.status_code == 307
            added_user = session.add.call_args[0][0]
            assert added_user.email == "bob@first.com"

    @pytest.mark.asyncio
    async def test_google_display_name_fallback_to_given_name(self):
        token_resp = MagicMock(status_code=200)
        token_resp.json.return_value = MOCK_TOKEN
        userinfo_resp = MagicMock(status_code=200)
        userinfo_resp.json.return_value = {"email": "alice@gmail.com", "given_name": "Alice"}

        factory, session = _mock_session_factory(existing_user=None)

        with patch("app.api.routes.oauth.PROVIDER_CONFIGS", new={"google": GOOGLE_CFG}), \
             patch("app.api.routes.oauth.settings", frontend_url="http://localhost:3000", free_tier_days=30), \
             patch("app.api.routes.oauth._get_session_factory", return_value=factory), \
             _patch_auth_tokens(), \
             patch("httpx.AsyncClient") as mock_cls:
            _mock_httpx(mock_cls, token_resp, userinfo_resp)

            await oauth_callback(provider="google", code="abc", request=MagicMock())
            added_user = session.add.call_args[0][0]
            assert added_user.display_name == "Alice"
