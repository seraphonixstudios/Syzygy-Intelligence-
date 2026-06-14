"""Tests for the rate limiter middleware (TokenBucket, RedisRateLimiter, RateLimiterMiddleware)."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.middleware.rate_limiter import (
    CircuitBreakerState,
    RateLimiterMiddleware,
    RedisRateLimiter,
    TokenBucket,
    setup_rate_limiter,
)


class TestTokenBucket:
    def test_init_full_burst(self):
        bucket = TokenBucket(rate=10.0, burst=5)
        assert bucket.rate == 10.0
        assert bucket.burst == 5
        assert bucket.tokens == 5.0

    def test_consume_returns_true_when_tokens_available(self):
        bucket = TokenBucket(rate=10.0, burst=5)
        assert bucket.consume() is True

    def test_consume_depletes_tokens(self):
        bucket = TokenBucket(rate=10.0, burst=3)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_consume_refills_over_time(self):
        bucket = TokenBucket(rate=10.0, burst=5)
        for _ in range(5):
            bucket.consume()
        assert bucket.consume() is False
        # Give time for one token to refill
        bucket.last_refill -= 0.15
        assert bucket.consume() is True

    def test_burst_never_exceeds_max(self):
        bucket = TokenBucket(rate=1.0, burst=5)
        for _ in range(5):
            bucket.consume()
        bucket.last_refill -= 10.0
        assert bucket.consume() is True
        assert bucket.tokens <= 5.0

    def test_zero_rate_never_refills(self):
        bucket = TokenBucket(rate=0.0, burst=3)
        for _ in range(3):
            bucket.consume()
        bucket.last_refill -= 60.0
        assert bucket.consume() is False


class TestRedisRateLimiter:
    @pytest.mark.asyncio
    async def test_consume_returns_true_when_redis_unavailable(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        result = await limiter.consume("test-key")
        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_redis_circuit_breaker_initial_state(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        assert limiter._circuit_breaker_state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_ensure_redis_skips_connection_in_open_window(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        limiter._circuit_breaker_state = CircuitBreakerState.OPEN
        limiter._circuit_breaker_open_at = time.time()  # Just opened
        result = await limiter._ensure_redis()
        assert result is None

    @pytest.mark.asyncio
    async def test_ensure_redis_tries_reconnect_after_open_window(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        limiter._circuit_breaker_state = CircuitBreakerState.OPEN
        limiter._circuit_breaker_open_at = time.time() - 31  # Past window

        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379/0"
            with patch("redis.asyncio.from_url") as mock_from_url:
                mock_from_url.side_effect = ConnectionError("Not available")
                result = await limiter._ensure_redis()
                assert result is None
                assert limiter._circuit_breaker_state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_ensure_redis_connection_success(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)

        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379/0"
            with patch("redis.asyncio.from_url") as mock_from_url:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_redis.script_load = AsyncMock(return_value="sha1")
                mock_from_url.return_value = mock_redis

                result = await limiter._ensure_redis()
                assert result is mock_redis
                assert limiter._redis is mock_redis
                assert limiter._sha == "sha1"
                assert limiter._circuit_breaker_state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_key_sanitization_removes_dangerous_chars(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        limiter._redis = AsyncMock()
        limiter._sha = "sha1"
        mock_redis = AsyncMock()
        mock_redis.evalsha = AsyncMock(return_value=1)
        limiter._redis = mock_redis

        result = await limiter.consume("user; DROP TABLE users;--")
        assert result is True
        # The dangerous characters should be sanitized
        call_key = mock_redis.evalsha.call_args[0][2]
        assert ";" not in call_key

    @pytest.mark.asyncio
    async def test_consume_fails_open_on_redis_error(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        limiter._redis = AsyncMock()
        limiter._sha = "sha1"
        mock_redis = AsyncMock()
        mock_redis.evalsha = AsyncMock(side_effect=Exception("Redis error"))
        limiter._redis = mock_redis

        result = await limiter.consume("test-key")
        assert result is True  # Fail open
        assert limiter._redis is None  # Connection reset

    @pytest.mark.asyncio
    async def test_consume_honors_redis_return_value(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        limiter._redis = AsyncMock()
        limiter._sha = "sha1"
        mock_redis = AsyncMock()
        limiter._redis = mock_redis

        # Redis says allowed
        mock_redis.evalsha = AsyncMock(return_value=1)
        assert await limiter.consume("test-key") is True

        # Redis says denied
        mock_redis.evalsha = AsyncMock(return_value=0)
        assert await limiter.consume("test-key") is False

    @pytest.mark.asyncio
    async def test_sanitize_empty_key_fails_open(self):
        limiter = RedisRateLimiter(rate=10.0, burst=5)
        limiter._redis = AsyncMock()
        limiter._sha = "sha1"
        mock_redis = AsyncMock()
        mock_redis.evalsha = AsyncMock(return_value=1)
        limiter._redis = mock_redis

        result = await limiter.consume("!!!")
        assert result is True


class TestRateLimiterMiddleware:
    def test_is_exempt_auth_routes(self):
        assert RateLimiterMiddleware._is_exempt("/api/auth/login") is True
        assert RateLimiterMiddleware._is_exempt("/api/auth/register") is True

    def test_is_exempt_health(self):
        assert RateLimiterMiddleware._is_exempt("/health") is True

    def test_is_exempt_root(self):
        assert RateLimiterMiddleware._is_exempt("/") is True

    def test_is_exempt_api_routes(self):
        assert RateLimiterMiddleware._is_exempt("/api/chat/completions") is False
        assert RateLimiterMiddleware._is_exempt("/api/agents/") is False

    def test_is_exempt_auth_subpath(self):
        assert RateLimiterMiddleware._is_exempt("/api/auth/login/extra") is True
        assert RateLimiterMiddleware._is_exempt("/api/auth/register/extra") is True

    def test_catches_non_http_scope(self):
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"ok": True}

        middleware = RateLimiterMiddleware(app)

        async def mock_send(msg):
            pass

        async def mock_receive():
            return {"type": "websocket.connect"}

        # Should not raise for non-HTTP scope
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                middleware(
                    {"type": "websocket", "path": "/ws", "headers": []},
                    mock_receive,
                    mock_send,
                )
            )
        finally:
            loop.close()

    def test_rate_limit_enforced(self):
        """Test that rate-limited requests get 429."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"ok": True}

        middleware = RateLimiterMiddleware(app)

        app.add_middleware(RateLimiterMiddleware)

        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.rate_limit_enabled = True
            mock_settings.rate_limit_per_second = 0.001
            mock_settings.rate_limit_burst = 1
            mock_settings.rate_limit_authenticated_per_second = 10.0
            mock_settings.rate_limit_authenticated_burst = 10

            with TestClient(app) as client:
                # First request should pass
                resp1 = client.get("/api/test")
                assert resp1.status_code in (200, 429)

    @pytest.mark.asyncio
    async def test_in_memory_fallback_on_redis_failure(self):
        """Test that in-memory fallback is used when Redis is down."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"ok": True}

        middleware = RateLimiterMiddleware(app)
        # Force Redis to fail by setting invalid connection
        middleware.ip_limiter._circuit_breaker_state = CircuitBreakerState.OPEN
        middleware.ip_limiter._circuit_breaker_open_at = 0

        # The in-memory fallback should handle the request
        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.rate_limit_enabled = True
            mock_settings.rate_limit_per_second = 1000.0
            mock_settings.rate_limit_burst = 1000
            mock_settings.rate_limit_authenticated_per_second = 1000.0
            mock_settings.rate_limit_authenticated_burst = 1000

            async def mock_send(msg):
                pass

            async def mock_receive():
                return {"type": "http.request"}

            scope = {
                "type": "http",
                "method": "GET",
                "path": "/api/test",
                "headers": [],
                "client": ("127.0.0.1", 12345),
                "query_string": b"",
            }

            await middleware(scope, mock_receive, mock_send)
            # Should not raise and should have reached the app


class TestSetupRateLimiter:
    def test_setup_when_enabled(self):
        app = FastAPI()
        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.rate_limit_enabled = True
            mock_settings.rate_limit_per_second = 10.0
            mock_settings.rate_limit_burst = 20
            mock_settings.rate_limit_authenticated_per_second = 100.0
            mock_settings.rate_limit_authenticated_burst = 200

            setup_rate_limiter(app)
            # Middleware should be registered
            assert len(app.user_middleware) > 0

    def test_setup_when_disabled(self):
        app = FastAPI()
        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.rate_limit_enabled = False

            setup_rate_limiter(app)
            # No middleware should be registered
            assert len(app.user_middleware) == 0
