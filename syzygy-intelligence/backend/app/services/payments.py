"""Stripe payment integration for subscription management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.logging_setup import logger


@dataclass
class StripeConfig:
    secret_key: str
    publishable_key: str
    webhook_secret: str
    premium_price_id: str
    enterprise_price_id: str


def get_stripe_config() -> StripeConfig | None:
    if not settings.stripe_secret_key:
        return None
    return StripeConfig(
        secret_key=settings.stripe_secret_key,
        publishable_key=settings.stripe_publishable_key,
        webhook_secret=settings.stripe_webhook_secret,
        premium_price_id=settings.stripe_premium_price_id,
        enterprise_price_id=settings.stripe_enterprise_price_id,
    )


async def create_checkout_session(
    user_id: str,
    user_email: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    trial_days: int = 0,
) -> dict[str, Any]:
    cfg = get_stripe_config()
    if not cfg:
        return {
            "url": (
                f"{success_url}?mock_checkout=true"
                f"&tier={'premium' if 'premium' in price_id else 'enterprise'}"
                f"&user_id={user_id}"
            ),
        }

    try:
        import stripe
        stripe.api_key = cfg.secret_key

        session = stripe.checkout.Session.create(
            customer_email=user_email,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={"trial_period_days": trial_days} if trial_days else {},
            metadata={"user_id": user_id},
        )
        return {"url": session.url, "session_id": session.id}
    except Exception as e:
        logger.error("Stripe checkout session creation failed", error=str(e), source="payments")
        raise


async def create_customer_portal_url(customer_id: str, return_url: str) -> str:
    try:
        import stripe
        cfg = get_stripe_config()
        assert cfg is not None
        stripe.api_key = cfg.secret_key
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except Exception as e:
        logger.error("Stripe portal session creation failed", error=str(e), source="payments")
        raise


async def handle_webhook(payload: bytes, sig_header: str) -> dict[str, Any]:
    cfg = get_stripe_config()
    if not cfg:
        return {"status": "ignored", "reason": "Stripe not configured"}

    try:
        import stripe
        stripe.api_key = cfg.secret_key
        event = stripe.Webhook.construct_event(payload, sig_header, cfg.webhook_secret)  # type: ignore[no-untyped-call]
    except Exception as e:
        logger.error("Stripe webhook verification failed", error=str(e), source="payments")
        raise

    handlers = {
        "checkout.session.completed": _handle_checkout_completed,
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
        "invoice.payment_succeeded": _handle_invoice_paid,
        "invoice.payment_failed": _handle_invoice_failed,
    }

    event_type = event.get("type", "")
    handler = handlers.get(event_type)
    if handler:
        logger.info(f"Stripe webhook: {event_type}", source="payments")
        await handler(event["data"]["object"])
    else:
        logger.debug(f"Unhandled webhook event type: {event_type}", source="payments")

    return {"status": "ok"}


async def _handle_checkout_completed(session: dict[str, Any]) -> None:
    from sqlalchemy import select

    from app.db.models import User
    from app.db.session import get_db_context

    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not user_id:
        logger.warning("Checkout session missing user_id metadata", source="payments")
        return

    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.stripe_customer_id = customer_id  # type: ignore
            user.stripe_subscription_id = subscription_id  # type: ignore
            session.get("mode", "")
            if session.get("amount_total", 0) >= 9900:
                user.subscription_tier = "enterprise"  # type: ignore
            elif session.get("amount_total", 0) >= 2900:
                user.subscription_tier = "premium"  # type: ignore
            db.add(user)
            await db.commit()
            logger.info(f"User {user_id} upgraded via checkout", tier=user.subscription_tier, source="payments")


async def _handle_subscription_updated(sub: dict[str, Any]) -> None:
    from sqlalchemy import select

    from app.db.models import User
    from app.db.session import get_db_context

    customer_id = sub.get("customer")
    status = sub.get("status", "")
    items = sub.get("items", {}).get("data", [])

    if not customer_id:
        return

    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user:
            if status in ("canceled", "incomplete_expired", "past_due"):
                user.subscription_tier = "free"  # type: ignore
            elif items:
                price_id = items[0].get("price", {}).get("id", "")
                if price_id == settings.stripe_enterprise_price_id:
                    user.subscription_tier = "enterprise"  # type: ignore
                elif price_id == settings.stripe_premium_price_id:
                    user.subscription_tier = "premium"  # type: ignore
            db.add(user)
            await db.commit()
            logger.info("User subscription updated", tier=user.subscription_tier, status=status, source="payments")


async def _handle_subscription_deleted(sub: dict[str, Any]) -> None:
    from sqlalchemy import select

    from app.db.models import User
    from app.db.session import get_db_context

    customer_id = sub.get("customer")
    if not customer_id:
        return

    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user:
            user.subscription_tier = "free"  # type: ignore
            user.stripe_subscription_id = None  # type: ignore
            db.add(user)
            await db.commit()
            logger.info("User subscription cancelled", user_id=user.id, source="payments")


async def _handle_invoice_paid(invoice: dict[str, Any]) -> None:
    logger.info("Invoice paid", invoice_id=invoice.get("id"), source="payments")


async def _handle_invoice_failed(invoice: dict[str, Any]) -> None:
    from sqlalchemy import select

    from app.db.models import User
    from app.db.session import get_db_context

    customer_id = invoice.get("customer")
    if not customer_id:
        return

    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user:
            logger.warning(
                "Invoice payment failed for user",
                user_id=user.id,
                invoice_id=invoice.get("id"),
                source="payments",
            )
