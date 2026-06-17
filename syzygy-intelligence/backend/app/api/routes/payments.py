"""Stripe payment routes — checkout session, webhooks, customer portal."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.api.auth import require_user
from app.config import settings
from app.db.models import User
from app.logging_setup import logger
from app.services.payments import (
    activate_subscription,
    create_checkout_session,
    create_customer_portal_url,
    create_setup_intent,
    get_stripe_config,
    handle_webhook,
)

router = APIRouter()


class CreateCheckoutRequest(BaseModel):
    price_id: str
    success_url: str = ""
    cancel_url: str = ""


class CheckoutResponse(BaseModel):
    url: str
    session_id: str | None = None


class SetupIntentResponse(BaseModel):
    client_secret: str | None = None
    customer_id: str | None = None
    error: str | None = None


class ActivateSubscriptionRequest(BaseModel):
    customer_id: str
    payment_method_id: str
    price_id: str


class ActivateSubscriptionResponse(BaseModel):
    subscription_id: str | None = None
    error: str | None = None


class PortalResponse(BaseModel):
    url: str


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout(
    req: CreateCheckoutRequest,
    user: User = Depends(require_user),
) -> CheckoutResponse:
    if not get_stripe_config() and settings.env == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured. Contact support.",
        )

    result = await create_checkout_session(
        user_id=str(user.id),
        user_email=user.email,  # type: ignore
        price_id=req.price_id,
        success_url=req.success_url or f"{settings.frontend_url}/settings?checkout=success",
        cancel_url=req.cancel_url or f"{settings.frontend_url}/settings?checkout=cancel",
        trial_days=0,
    )
    return CheckoutResponse(url=result["url"], session_id=result.get("session_id"))


@router.post("/create-setup-intent", response_model=SetupIntentResponse)
async def create_setup(
    req: CreateCheckoutRequest,
    user: User = Depends(require_user),
) -> SetupIntentResponse:
    if not get_stripe_config():
        return SetupIntentResponse(error="Stripe not configured")
    result = await create_setup_intent(
        user_id=str(user.id),
        user_email=user.email,
        price_id=req.price_id,
    )
    return SetupIntentResponse(
        client_secret=result.get("client_secret"),
        customer_id=result.get("customer_id"),
        error=result.get("error"),
    )


@router.post("/activate-subscription", response_model=ActivateSubscriptionResponse)
async def activate_sub(
    req: ActivateSubscriptionRequest,
    user: User = Depends(require_user),
) -> ActivateSubscriptionResponse:
    result = await activate_subscription(
        user_id=str(user.id),
        customer_id=req.customer_id,
        payment_method_id=req.payment_method_id,
        price_id=req.price_id,
    )
    return ActivateSubscriptionResponse(
        subscription_id=result.get("subscription_id"),
        error=result.get("error"),
    )


@router.post("/customer-portal", response_model=PortalResponse)
async def customer_portal(
    user: User = Depends(require_user),
) -> PortalResponse:
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )
    url = await create_customer_portal_url(
        customer_id=user.stripe_customer_id,  # type: ignore
        return_url=f"{settings.frontend_url}/settings",
    )
    return PortalResponse(url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict[str, Any]:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = await handle_webhook(payload, sig_header)
        return result
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), source="payments")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
