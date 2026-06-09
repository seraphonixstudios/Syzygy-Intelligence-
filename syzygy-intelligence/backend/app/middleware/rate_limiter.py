from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_setup import logger


class TokenBucket:
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.burst), self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimiterMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app
        self.ip_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(settings.rate_limit_per_second, settings.rate_limit_burst)
        )
        self.user_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(settings.rate_limit_authenticated_per_second, settings.rate_limit_authenticated_burst)
        )

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if path.startswith("/api/") and not self._is_exempt(path):
            ip_bucket = self.ip_buckets[ip]
            if not ip_bucket.consume():
                logger.warning("Rate limit exceeded", ip=ip, path=path, limiter="ip")
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please slow down.",
                            "details": {"retry_after_seconds": 1.0 / settings.rate_limit_per_second},
                        }
                    },
                    headers={"Retry-After": str(int(1.0 / settings.rate_limit_per_second))},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    def _is_exempt(self, path: str) -> bool:
        exempt = ["/api/auth/login", "/api/auth/register", "/health", "/"]
        return any(path == e or path.startswith(e + "/") for e in exempt)


def setup_rate_limiter(app: FastAPI) -> None:
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimiterMiddleware)
        logger.info("Rate limiter enabled", per_second=settings.rate_limit_per_second, burst=settings.rate_limit_burst)
