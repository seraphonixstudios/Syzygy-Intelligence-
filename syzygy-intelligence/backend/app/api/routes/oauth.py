"""OAuth routes — Google and GitHub social login via Authorization Code flow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.api.auth import create_access_token, create_refresh_token
from app.config import settings
from app.db.models import User, SubscriptionTier
from app.db.session import _get_session_factory

router = APIRouter(prefix="/oauth")

PROVIDER_CONFIGS: dict[str, dict] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "scope": "openid email profile",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "scope": "read:user user:email",
    },
}


@router.get("/{provider}")
async def oauth_redirect(provider: str, request: Request):
    cfg = PROVIDER_CONFIGS.get(provider)
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown provider: {provider}")

    if not cfg["client_id"]:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"OAuth for {provider} is not configured")

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": f"{settings.oauth_redirect_url}/{provider}/callback",
        "response_type": "code",
        "scope": cfg["scope"],
        "state": str(uuid.uuid4()),
    }
    redirect_url = f"{cfg['authorize_url']}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str, request: Request):
    cfg = PROVIDER_CONFIGS.get(provider)
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown provider: {provider}")

    # Exchange code for access token
    token_data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": f"{settings.oauth_redirect_url}/{provider}/callback",
        "grant_type": "authorization_code",
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        token_res = await client.post(cfg["token_url"], data=token_data, headers=headers)
        if token_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange authorization code")

        token_body = token_res.json()
        access_token = token_body.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token in provider response")

        # Fetch user info
        userinfo_headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        userinfo_res = await client.get(cfg["userinfo_url"], headers=userinfo_headers)
        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user info from provider")

        userinfo = userinfo_res.json()

    # Extract email and display name
    if provider == "google":
        email = userinfo.get("email")
        display_name = userinfo.get("name") or userinfo.get("given_name", "")
    elif provider == "github":
        email = userinfo.get("email")
        display_name = userinfo.get("name") or userinfo.get("login", "")
        # GitHub sometimes doesn't return email in userinfo; fetch emails separately
        if not email:
            emails_res = await client.get("https://api.github.com/user/emails", headers=userinfo_headers)
            if emails_res.status_code == 200:
                emails = emails_res.json()
                for e in emails:
                    if e.get("primary") and e.get("verified"):
                        email = e.get("email")
                        break
                if not email and emails:
                    email = emails[0].get("email")
    else:
        email = userinfo.get("email")
        display_name = userinfo.get("name", "")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve email from provider")

    # Create or find user
    factory = _get_session_factory()
    async with factory() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=email,
                hashed_password="",  # OAuth users have no password
                display_name=display_name or email.split("@")[0],
                verified_at=datetime.now(timezone.utc),  # Auto-verify OAuth users
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=settings.free_tier_days),
                settings={},
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        elif not user.verified_at:
            user.verified_at = datetime.now(timezone.utc)
            db.add(user)
            await db.commit()

        our_access = create_access_token(str(user.id), user.email)
        our_refresh = create_refresh_token(str(user.id), user.email)

    # Redirect back to frontend with tokens in hash fragment
    frontend_url = (settings.cors_origins.split(",")[0].strip() if settings.cors_origins else "http://localhost:3000")
    redirect_to = f"{frontend_url}/auth/oauth-callback#access_token={our_access}&refresh_token={our_refresh}"
    return RedirectResponse(url=redirect_to)
