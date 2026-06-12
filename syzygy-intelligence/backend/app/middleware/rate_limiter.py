from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_setup import logger

TOKEN_BUCKET_SCRIPT = """
local data = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens, ts
if data[1] then
    tokens = tonumber(data[1])
    ts = tonumber(data[2])
else
    tokens = tonumber(ARGV[2])
    ts = tonumber(ARGV[3])
end
local elapsed = tonumber(ARGV[3]) - ts
tokens = math.min(tonumber(ARGV[2]), tokens + elapsed * tonumber(ARGV[1]))
if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', ARGV[3])
    redis.call('EXPIRE', KEYS[1], math.ceil(tonumber(ARGV[2]) / tonumber(ARGV[1])) + 1)
    return 1
end
redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', ARGV[3])
redis.call('EXPIRE', KEYS[1], math.ceil(tonumber(ARGV[2]) / tonumber(ARGV[1])) + 1)
return 0
"""


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


class RedisRateLimiter:
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self._redis: Any = None
        self._sha: str | None = None
        self._failed = False

    async def _ensure_redis(self) -> Any:
        if self._redis is not None:
            return self._redis
        if self._failed:
            return None
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(
                settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            await r.ping()
            self._sha = await r.script_load(TOKEN_BUCKET_SCRIPT)
            self._redis = r
            return r
        except Exception as exc:
            self._failed = True
            logger.warning("Redis rate limiter unavailable, falling back to in-memory", error=str(exc))
            return None

    async def consume(self, key: str) -> bool:
        r = await self._ensure_redis()
        if r is None:
            return False
        try:
            result = await r.evalsha(
                self._sha, 1, f"rl:{key}",
                self.rate, self.burst, time.time(),
            )
            return bool(result)
        except Exception as exc:
            self._failed = True
            await self._redis.aclose()
            self._redis = None
            logger.warning("Redis rate limiter error, falling back to in-memory", error=str(exc))
            return False


class RateLimiterMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app
        self.ip_limiter = RedisRateLimiter(
            settings.rate_limit_per_second, settings.rate_limit_burst
        )
        self.user_limiter = RedisRateLimiter(
            settings.rate_limit_authenticated_per_second,
            settings.rate_limit_authenticated_burst,
        )
        self.ip_fallback: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(settings.rate_limit_per_second, settings.rate_limit_burst)
        )
        self.user_fallback: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(settings.rate_limit_authenticated_per_second, settings.rate_limit_authenticated_burst)
        )

    async def _check(self, scope: str, identifier: str) -> bool:
        limiter = self.ip_limiter if scope == "ip" else self.user_limiter
        allowed = await limiter.consume(f"{scope}:{identifier}")
        if allowed:
            return True
        if limiter._failed:
            fallback = self.ip_fallback if scope == "ip" else self.user_fallback
            return fallback[identifier].consume()
        return False

    async def __call__(
        self, scope: dict[str, Any], receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if path.startswith("/api/") and not self._is_exempt(path) and settings.rate_limit_enabled:
            if not await self._check("ip", ip):
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
