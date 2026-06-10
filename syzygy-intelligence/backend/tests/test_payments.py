"""Unit tests for Stripe payment integration."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status


class TestStripeConfig:
    def test_get_config_returns_none_when_no_key(self):
        from app.services.payments import get_stripe_config
        with patch("app.services.payments.settings.stripe_secret_key", ""):
            assert get_stripe_config() is None

    def test_get_config_returns_config_when_key_set(self):
        from app.services.payments import get_stripe_config
        with patch("app.services.payments.settings.stripe_secret_key", "sk_test_xyz"):
            with patch("app.services.payments.settings.stripe_publishable_key", "pk_test_xyz"):
                with patch("app.services.payments.settings.stripe_webhook_secret", "whsec_xyz"):
                    cfg = get_stripe_config()
                    assert cfg is not None
                    assert cfg.secret_key == "sk_test_xyz"
                    assert cfg.publishable_key == "pk_test_xyz"

    def test_price_ids_from_config(self):
        from app.services.payments import get_stripe_config
        with patch("app.services.payments.settings.stripe_secret_key", "sk_test_xyz"):
            with patch("app.services.payments.settings.stripe_publishable_key", "pk_test_xyz"):
                with patch("app.services.payments.settings.stripe_webhook_secret", "whsec_xyz"):
                    cfg = get_stripe_config()
                    assert cfg.premium_price_id == "price_premium_monthly"
                    assert cfg.enterprise_price_id == "price_enterprise_monthly"


class TestCreateCheckoutSession:
    @pytest.mark.asyncio
    async def test_returns_mock_url_without_stripe(self):
        from app.services.payments import create_checkout_session
        result = await create_checkout_session(
            user_id=str(uuid.uuid4()),
            user_email="test@example.com",
            price_id="price_premium_monthly",
            success_url="http://localhost:3000/settings",
            cancel_url="http://localhost:3000/settings",
        )
        assert "mock_checkout=true" in result["url"]
        assert "tier=premium" in result["url"]

    @pytest.mark.asyncio
    async def test_returns_enterprise_mock_url(self):
        from app.services.payments import create_checkout_session
        result = await create_checkout_session(
            user_id=str(uuid.uuid4()),
            user_email="test@example.com",
            price_id="price_enterprise_monthly",
            success_url="http://localhost:3000/settings",
            cancel_url="http://localhost:3000/settings",
        )
        assert "tier=enterprise" in result["url"]

    @pytest.mark.asyncio
    async def test_calls_stripe_when_configured(self):
        from app.services.payments import create_checkout_session
        with patch("app.services.payments.get_stripe_config") as mock_cfg:
            mock_cfg.return_value = MagicMock(secret_key="sk_test_xyz")
            with patch.dict("sys.modules", {"stripe": MagicMock()}):
                import stripe
                stripe.checkout.Session.create.return_value = MagicMock(
                    url="https://checkout.stripe.com/test",
                    id="cs_test_123",
                )

                result = await create_checkout_session(
                    user_id=str(uuid.uuid4()),
                    user_email="test@example.com",
                    price_id="price_premium_monthly",
                    success_url="http://localhost:3000/settings",
                    cancel_url="http://localhost:3000/settings",
                    trial_days=7,
                )
        assert result["url"] == "https://checkout.stripe.com/test"
        assert result["session_id"] == "cs_test_123"


class TestWebhookHandlers:
    @pytest.mark.asyncio
    async def test_handle_webhook_returns_ignored_without_stripe(self):
        from app.services.payments import handle_webhook
        result = await handle_webhook(b"{}", "")
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_upgrades_to_premium(self):
        from app.services.payments import _handle_checkout_completed
        user = MagicMock()
        user.id = uuid.uuid4()
        user.subscription_tier = "free"

        with patch("app.db.session.get_db_context") as mock_db:
            db = AsyncMock()
            mock_db.return_value.__aenter__.return_value = db
            result = MagicMock()
            result.scalar_one_or_none.return_value = user
            db.execute.return_value = result

            session = {
                "metadata": {"user_id": str(user.id)},
                "customer": "cus_abc123",
                "subscription": "sub_xyz789",
                "mode": "subscription",
                "amount_total": 2900,
            }
            await _handle_checkout_completed(session)

            assert user.stripe_customer_id == "cus_abc123"
            assert user.stripe_subscription_id == "sub_xyz789"
            assert user.subscription_tier == "premium"
            db.add.assert_called_once_with(user)
            db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_upgrades_to_enterprise(self):
        from app.services.payments import _handle_checkout_completed
        user = MagicMock()
        user.id = uuid.uuid4()

        with patch("app.db.session.get_db_context") as mock_db:
            db = AsyncMock()
            mock_db.return_value.__aenter__.return_value = db
            result = MagicMock()
            result.scalar_one_or_none.return_value = user
            db.execute.return_value = result

            session = {
                "metadata": {"user_id": str(user.id)},
                "customer": "cus_abc123",
                "subscription": "sub_xyz789",
                "mode": "subscription",
                "amount_total": 9900,
            }
            await _handle_checkout_completed(session)
            assert user.subscription_tier == "enterprise"

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_downgrades_on_cancel(self):
        from app.services.payments import _handle_subscription_updated
        user = MagicMock()
        user.subscription_tier = "premium"

        with patch("app.db.session.get_db_context") as mock_db:
            db = AsyncMock()
            mock_db.return_value.__aenter__.return_value = db
            result = MagicMock()
            result.scalar_one_or_none.return_value = user
            db.execute.return_value = result

            sub = {
                "customer": "cus_abc123",
                "status": "canceled",
                "items": {"data": [{"price": {"id": "price_other"}}]},
            }
            await _handle_subscription_updated(sub)
            assert user.subscription_tier == "free"

    @pytest.mark.asyncio
    async def test_handle_subscription_deleted_resets_to_free(self):
        from app.services.payments import _handle_subscription_deleted
        user = MagicMock()
        user.subscription_tier = "enterprise"
        user.stripe_subscription_id = "sub_xyz789"

        with patch("app.db.session.get_db_context") as mock_db:
            db = AsyncMock()
            mock_db.return_value.__aenter__.return_value = db
            result = MagicMock()
            result.scalar_one_or_none.return_value = user
            db.execute.return_value = result

            await _handle_subscription_deleted({"customer": "cus_abc123"})
            assert user.subscription_tier == "free"
            assert user.stripe_subscription_id is None

    @pytest.mark.asyncio
    async def test_handle_invoice_paid_logs(self):
        from app.services.payments import _handle_invoice_paid
        with patch("app.services.payments.logger.info") as mock_log:
            await _handle_invoice_paid({"id": "in_abc123"})
            mock_log.assert_called_once()


class TestPaymentRoutes:
    def test_require_user_rejects_unauthenticated(self):
        from app.api.auth import require_user
        import asyncio
        with pytest.raises(HTTPException) as exc:
            asyncio.run(require_user(user=None))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_create_checkout_returns_url_for_logged_in_user(self):
        from app.api.routes.payments import create_checkout
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"

        req = MagicMock(price_id="price_premium_monthly", success_url="http://localhost:3000/settings", cancel_url="http://localhost:3000/settings")

        with patch("app.api.routes.payments.create_checkout_session") as mock_svc:
            mock_svc.return_value = {"url": "http://mock.checkout/url", "session_id": None}
            resp = await create_checkout(req, user=user)
            assert resp.url == "http://mock.checkout/url"

    @pytest.mark.asyncio
    async def test_customer_portal_requires_stripe_customer(self):
        from app.api.routes.payments import customer_portal
        user = MagicMock()
        user.stripe_customer_id = None
        with pytest.raises(HTTPException) as exc:
            await customer_portal(user=user)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_customer_portal_returns_url(self):
        from app.api.routes.payments import customer_portal
        user = MagicMock()
        user.stripe_customer_id = "cus_abc123"

        with patch("app.api.routes.payments.create_customer_portal_url") as mock_portal:
            mock_portal.return_value = "http://portal.stripe.com/test"
            resp = await customer_portal(user=user)
            assert resp.url == "http://portal.stripe.com/test"

    @pytest.mark.asyncio
    async def test_webhook_delegates_to_service(self):
        from app.api.routes.payments import stripe_webhook
        request = MagicMock()
        request.body = AsyncMock(return_value=b'{"type": "test"}')
        request.headers = {"stripe-signature": "sig_test"}
        with patch("app.api.routes.payments.handle_webhook") as mock_webhook:
            mock_webhook.return_value = {"status": "ok"}
            result = await stripe_webhook(request)
            assert result["status"] == "ok"
