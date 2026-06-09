"""Stripe payment routes — checkout session, webhooks, customer portal."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_user
from app.config import settings
from app.db.models import User
from app.db.session import get_db
from app.logging_setup import logger
from app.services.payments import (
    create_checkout_session,
    create_customer_portal_url,
    get_stripe_config,
    handle_webhook,
)

router = APIRouter()


class CreateCheckoutRequest(BaseModel):
    price_id: str
    success_url: str = "http://localhost:3000/settings?checkout=success"
    cancel_url: str = "http://localhost:3000/settings?checkout=cancel"


class CheckoutResponse(BaseModel):
    url: str
    session_id: str | None = None


class PortalResponse(BaseModel):
    url: str


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout(
    req: CreateCheckoutRequest,
    user: User = Depends(require_user),
):
    if not get_stripe_config() and settings.env == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured. Contact support.",
        )

    result = await create_checkout_session(
        user_id=str(user.id),
        user_email=user.email,
        price_id=req.price_id,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        trial_days=0,
    )
    return CheckoutResponse(url=result["url"], session_id=result.get("session_id"))


@router.post("/customer-portal", response_model=PortalResponse)
async def customer_portal(
    user: User = Depends(require_user),
):
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )
    url = await create_customer_portal_url(
        customer_id=user.stripe_customer_id,
        return_url="http://localhost:3000/settings",
    )
    return PortalResponse(url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = await handle_webhook(payload, sig_header)
        return result
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), source="payments")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
