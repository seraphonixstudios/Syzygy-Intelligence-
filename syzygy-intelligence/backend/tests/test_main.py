"""Tests for main.py — app lifecycle, middleware, and root endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestLifespan:
    @pytest.mark.asyncio
    async def test_startup_shutdown_success(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, return_value=True) as mock_init,
            patch("app.main.close_db", new_callable=AsyncMock) as mock_close,
            patch("app.main.setup_tracing") as mock_tracing,
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
        ):
            from app.main import lifespan
            app = MagicMock()
            async with lifespan(app):
                mock_init.assert_awaited_once()
                mock_tracing.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_closes_db(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, return_value=True),
            patch("app.main.close_db", new_callable=AsyncMock) as mock_close,
            patch("app.main.setup_tracing"),
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
        ):
            from app.main import lifespan
            async with lifespan(MagicMock()):
                pass
            mock_close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_logs_startup_and_shutdown(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, return_value=True),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_tracing"),
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
            patch("app.main.logger") as mock_logger,
        ):
            from app.main import lifespan
            async with lifespan(MagicMock()):
                pass
            info_calls = [c for c in mock_logger.info.call_args_list if "Syzygy Intelligence" in str(c)]
            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_db_init_failure_dev_logs_warning(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, return_value=False),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_tracing"),
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
            patch("app.main.logger") as mock_logger,
            patch("app.main.settings.env", "development"),
        ):
            from app.main import lifespan
            async with lifespan(MagicMock()):
                pass
            warning_calls = [c for c in mock_logger.warning.call_args_list if "Database unavailable" in str(c)]
            assert len(warning_calls) == 1

    @pytest.mark.asyncio
    async def test_db_init_failure_prod_raises(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, return_value=False),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
            patch("app.main.settings.env", "production"),
        ):
            from app.main import lifespan
            with pytest.raises(RuntimeError, match="Database initialization failed"):
                async with lifespan(MagicMock()):
                    pass

    @pytest.mark.asyncio
    async def test_db_init_exception_dev_logs_warning(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, side_effect=Exception("conn refused")),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_tracing"),
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
            patch("app.main.logger") as mock_logger,
            patch("app.main.settings.env", "development"),
        ):
            from app.main import lifespan
            async with lifespan(MagicMock()):
                pass
            warning_calls = [c for c in mock_logger.warning.call_args_list if "Database initialization error" in str(c)]
            assert len(warning_calls) == 1

    @pytest.mark.asyncio
    async def test_db_init_exception_prod_raises(self):
        with (
            patch("app.main.init_db", new_callable=AsyncMock, side_effect=Exception("conn refused")),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_error_handlers"),
            patch("app.main.setup_rate_limiter"),
            patch("app.main.settings.env", "production"),
        ):
            from app.main import lifespan
            with pytest.raises(Exception, match="conn refused"):
                async with lifespan(MagicMock()):
                    pass


class TestAppEndpoints:
    def test_root_returns_structure(self):
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "Syzygy Intelligence"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"

    def test_metrics_returns_response(self):
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/metrics")
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/plain")


class TestAppConfiguration:
    def test_middleware_is_setup(self):
        from app.main import app
        middlewares = [str(m.cls) for m in app.user_middleware]
        assert any("CORSMiddleware" in m for m in middlewares)
        assert any("RequestTracingMiddleware" in m for m in middlewares)

    def test_routers_are_included(self):
        from app.main import app
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        route_paths = list(paths.keys())
        routes_str = ", ".join(route_paths)
        expected_prefixes = [
            "/api/chat", "/api/admin", "/api/auth", "/api/agents",
            "/api/sessions", "/api/consensus", "/api/memory", "/api/tools",
            "/api/workflows", "/api/audit", "/api/meta", "/api/uploads",
            "/api/rag", "/api/payments", "/health",
        ]
        for prefix in expected_prefixes:
            assert any(p.startswith(prefix) for p in route_paths), f"Missing route prefix: {prefix}"
        assert "/ws" in [r.path for r in app.routes if hasattr(r, "path")]

    def test_websocket_route_registered(self):
        from app.main import app
        ws_routes = [r for r in app.routes if hasattr(r, "path") and r.path == "/ws"]
        assert len(ws_routes) == 1
