"""Rate limiting middleware with Redis fallback and circuit breaker pattern.

Best practices:
- Circuit breaker: automatic fallback when Redis is unavailable
- Graceful degradation: in-memory fallback maintains functionality
- Observability: detailed logging for troubleshooting
- Type safety: proper exception handling
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from enum import Enum
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
    ts = tonumber(ARGV[4])
end
local elapsed = tonumber(ARGV[4]) - ts
tokens = math.min(tonumber(ARGV[2]), tokens + elapsed * tonumber(ARGV[1]))
if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', ARGV[4])
    redis.call('EXPIRE', KEYS[1], math.ceil(tonumber(ARGV[2]) / tonumber(ARGV[1])) + 1)
    return 1
end
redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', ARGV[4])
redis.call('EXPIRE', KEYS[1], math.ceil(tonumber(ARGV[2]) / tonumber(ARGV[1])) + 1)
return 0
"""


class CircuitBreakerState(Enum):
    """Circuit breaker states for Redis connection."""

    CLOSED = "closed"  # Operating normally
    OPEN = "open"  # Redis unavailable, use fallback
    HALF_OPEN = "half_open"  # Attempting to reconnect


class TokenBucket:
    """Local token bucket rate limiter (in-memory fallback)."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        """Attempt to consume one token."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.burst), self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RedisRateLimiter:
    """Redis-backed rate limiter with automatic fallback."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self._redis: Any = None
        self._sha: str | None = None
        self._circuit_breaker_state = CircuitBreakerState.CLOSED
        self._circuit_breaker_open_at = 0.0

    async def _ensure_redis(self) -> Any:
        """Get Redis connection with circuit breaker logic."""
        # Circuit breaker: if recently opened, don't retry immediately
        if self._circuit_breaker_state == CircuitBreakerState.OPEN:
            if time.time() - self._circuit_breaker_open_at < 30:
                # Still in open window, skip connection attempt
                return None
            else:
                # Try to recover (half-open state)
                self._circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker: attempting to reconnect to Redis")

        if self._redis is not None:
            return self._redis

        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(
                settings.redis_url,
                socket_connect_timeout=2,
                socket_keepalive=True,
                socket_keepalive_options={},
                decode_responses=False,
            )
            await r.ping()
            self._sha = await r.script_load(TOKEN_BUCKET_SCRIPT)
            self._redis = r
            self._circuit_breaker_state = CircuitBreakerState.CLOSED
            logger.info("Redis connection established", url=settings.redis_url)
            return r
        except (ConnectionError, TimeoutError, OSError) as exc:
            self._circuit_breaker_state = CircuitBreakerState.OPEN
            self._circuit_breaker_open_at = time.time()
            logger.warning(
                "Redis rate limiter unavailable, falling back to in-memory",
                error=type(exc).__name__,
                details=str(exc),
            )
            return None
        except Exception as exc:
            self._circuit_breaker_state = CircuitBreakerState.OPEN
            self._circuit_breaker_open_at = time.time()
            logger.error(
                "Redis connection failed unexpectedly",
                error=type(exc).__name__,
                details=str(exc),
            )
            return None

    async def consume(self, key: str) -> bool:
        """Consume one token. Returns True if allowed, False if rate-limited."""
        r = await self._ensure_redis()
        if r is None:
            # Redis unavailable, allow request (fail open)
            return True

        try:
            # Sanitize key to prevent injection attacks
            # Only allow alphanumeric, hyphens, underscores (NO colons to prevent Redis key structure injection)
            safe_key = "".join(c for c in key if c.isalnum() or c in ("-", "_"))
            if not safe_key:
                logger.warning(
                    "Rate limiter: invalid key format after sanitization",
                    original_key=key,
                )
                return True

            redis_key = f"rl:{safe_key}"
            result = await r.evalsha(
                self._sha,
                1,
                redis_key,
                self.rate,
                self.burst,
                self.burst,
                time.time(),
            )
            return bool(result)
        except Exception as exc:
            logger.warning(
                "Redis rate limiter error, allowing request",
                error=type(exc).__name__,
                details=str(exc),
            )
            # Clean up connection and retry next time
            try:
                if self._redis:
                    await self._redis.aclose()
            except Exception:
                pass
            finally:
                self._redis = None
                self._sha = None

            # Fail open: allow request when Redis is down
            return True


class RateLimiterMiddleware:
    """ASGI middleware for request rate limiting."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.ip_limiter = RedisRateLimiter(
            settings.rate_limit_per_second,
            settings.rate_limit_burst,
        )
        self.user_limiter = RedisRateLimiter(
            settings.rate_limit_authenticated_per_second,
            settings.rate_limit_authenticated_burst,
        )
        # In-memory fallback buckets
        self.ip_fallback: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(settings.rate_limit_per_second, settings.rate_limit_burst)
        )
        self.user_fallback: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                settings.rate_limit_authenticated_per_second,
                settings.rate_limit_authenticated_burst,
            )
        )

    async def _check(self, scope: str, identifier: str) -> bool:
        """Check rate limit for scope (ip or user)."""
        limiter = self.ip_limiter if scope == "ip" else self.user_limiter

        # Try Redis first
        if await limiter.consume(f"{scope}:{identifier}"):
            return True

        # Fallback to in-memory if Redis returned False (rate limited)
        fallback = self.ip_fallback if scope == "ip" else self.user_fallback
        return fallback[identifier].consume()

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """ASGI middleware entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Check rate limits for API endpoints
        if (
            path.startswith("/api/")
            and not self._is_exempt(path)
            and settings.rate_limit_enabled
        ):
            allowed = await self._check("ip", ip)
            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    ip=ip,
                    path=path,
                    limiter="ip",
                )
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please slow down.",
                            "details": {
                                "retry_after_seconds": int(1.0 / settings.rate_limit_per_second)
                            },
                        }
                    },
                    headers={"Retry-After": str(int(1.0 / settings.rate_limit_per_second))},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    @staticmethod
    def _is_exempt(path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        exempt_paths = [
            "/api/auth/login",
            "/api/auth/register",
            "/health",
            "/",
        ]
        return any(path == ep or path.startswith(ep + "/") for ep in exempt_paths)


def setup_rate_limiter(app: FastAPI) -> None:
    """Add rate limiter middleware to FastAPI app."""
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimiterMiddleware)
        logger.info(
            "Rate limiter enabled",
            per_second=settings.rate_limit_per_second,
            burst=settings.rate_limit_burst,
            authenticated_per_second=settings.rate_limit_authenticated_per_second,
            authenticated_burst=settings.rate_limit_authenticated_burst,
        )
    else:
        logger.info("Rate limiter disabled")
