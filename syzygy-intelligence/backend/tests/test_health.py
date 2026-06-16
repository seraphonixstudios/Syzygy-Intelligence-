"""Tests for the health check endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.health import router as health_router

test_app = FastAPI()
test_app.include_router(health_router)


def test_health_returns_200():
    with TestClient(test_app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200


def test_health_response_structure():
    with TestClient(test_app) as client:
        resp = client.get("/health")
    body = resp.json()
    assert "status" in body
    assert body["status"] in ("healthy", "degraded", "unhealthy")
    assert body["version"] == "0.1.0"
    assert "env" in body
    assert "uptime_seconds" in body
    assert "checks" in body


def test_health_includes_all_checks():
    with TestClient(test_app) as client:
        resp = client.get("/health")
    body = resp.json()
    for service in ("database", "redis", "ollama", "neo4j"):
        assert service in body["checks"], f"Missing health check for {service}"
        assert "status" in body["checks"][service]


def test_health_latency_is_float():
    with TestClient(test_app) as client:
        resp = client.get("/health")
    body = resp.json()
    for name, check in body["checks"].items():
        if check["status"] == "ok":
            assert isinstance(check["latency_ms"], (int, float))


@pytest.mark.asyncio
async def test_check_database_success():
    from app.api.routes.health import _check_database

    class FakeConnection:
        async def execute(self, *args, **kwargs):
            return AsyncMock()
        async def commit(self):
            pass

    class FakeEngine:
        def connect(self):
            return _AsyncContextManager(FakeConnection())

    class _AsyncContextManager:
        def __init__(self, obj):
            self._obj = obj
        async def __aenter__(self):
            return self._obj
        async def __aexit__(self, *args):
            pass

    with patch("app.api.routes.health._get_engine", return_value=FakeEngine()):
        result = await _check_database()
        assert result["status"] == "ok"
        assert "latency_ms" in result


@pytest.mark.asyncio
async def test_check_database_failure():
    from app.api.routes.health import _check_database

    class _FailingEngine:
        def connect(self):
            raise Exception("connection refused")

    with patch("app.api.routes.health._get_engine", return_value=_FailingEngine()):

        result = await _check_database()
        assert result["status"] == "unavailable"
        assert "error" in result


@pytest.mark.asyncio
async def test_check_redis_success():
    from app.api.routes.health import _check_redis

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.redis_url = "redis://myhost:6379/0"
        mock_settings.env = "production"
        mock_ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = mock_ping
            mock_redis.aclose = AsyncMock()
            mock_from_url.return_value = mock_redis

            result = await _check_redis()
            assert result["status"] == "ok"
            assert "latency_ms" in result


@pytest.mark.asyncio
async def test_check_redis_default_dev_url():
    from app.api.routes.health import _check_redis

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.env = "development"

        result = await _check_redis()
        assert result["status"] == "ok"
        assert "note" in result


@pytest.mark.asyncio
async def test_check_ollama_success():
    from app.api.routes.health import _check_ollama

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.ollama_base_url = "http://ollama:11434"
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await _check_ollama()
            assert result["status"] == "ok"
            assert "latency_ms" in result


@pytest.mark.asyncio
async def test_check_ollama_unreachable():
    from app.api.routes.health import _check_ollama

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.ollama_base_url = "http://ollama:11434"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("connection refused")
            mock_client_cls.return_value = mock_client

            result = await _check_ollama()
            assert result["status"] == "unavailable"
            assert "error" in result


@pytest.mark.asyncio
async def test_check_neo4j_default_dev_uri():
    from app.api.routes.health import _check_neo4j

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.neo4j_uri = "bolt://localhost:7687"
        mock_settings.env = "development"

        result = await _check_neo4j()
        assert result["status"] == "ok"
        assert "note" in result


# ═══════════════════════════════════════════════════════════
# Edge case tests for health endpoint
# ═══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_health_unhealthy_all_fail():
    """When all checks fail, overall status is unhealthy."""
    with (
        patch("app.api.routes.health._check_database", return_value={"status": "unavailable", "error": "fail"}),
        patch("app.api.routes.health._check_redis", return_value={"status": "unavailable", "error": "fail"}),
        patch("app.api.routes.health._check_ollama", return_value={"status": "unavailable", "error": "fail"}),
        patch("app.api.routes.health._check_neo4j", return_value={"status": "unavailable", "error": "fail"}),
    ):
        resp = TestClient(test_app).get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_check_redis_ping_false():
    """Redis ping returning false logs as unavailable."""
    from app.api.routes.health import _check_redis

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.redis_url = "redis://myhost:6379/0"
        mock_settings.env = "production"
        mock_ping = AsyncMock(return_value=False)

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = mock_ping
            mock_redis.aclose = AsyncMock()
            mock_from_url.return_value = mock_redis

            result = await _check_redis()
            assert result["status"] == "unavailable"
            assert "ping returned false" in result["error"]


@pytest.mark.asyncio
async def test_check_ollama_no_url():
    """Ollama check returns unavailable when no URL configured."""
    from app.api.routes.health import _check_ollama

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.ollama_base_url = ""
        result = await _check_ollama()
        assert result["status"] == "unavailable"
        assert "no URL" in result["error"]


@pytest.mark.asyncio
async def test_check_ollama_non_200():
    """Ollama check returns unavailable on non-200 status."""
    from app.api.routes.health import _check_ollama

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.ollama_base_url = "http://ollama:11434"
        mock_resp = AsyncMock()
        mock_resp.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await _check_ollama()
            assert result["status"] == "unavailable"


@pytest.mark.asyncio
async def test_check_neo4j_unexpected_result():
    """Neo4j check returns unavailable when query returns unexpected result."""
    from app.api.routes.health import _check_neo4j

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.neo4j_uri = "bolt://myhost:7687"
        mock_settings.env = "production"
        mock_settings.neo4j_user = "neo4j"
        mock_settings.neo4j_password = "pass"

        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 2
        mock_result = AsyncMock()
        mock_result.single.return_value = mock_record
        mock_session = AsyncMock()
        mock_session.run.return_value = mock_result
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session

        with patch("neo4j.AsyncGraphDatabase.driver", return_value=mock_driver):
            result = await _check_neo4j()
            assert result["status"] == "unavailable"
            assert "unexpected" in result["error"]


@pytest.mark.asyncio
async def test_check_redis_connection_exception():
    """Redis check returns unavailable when connection raises."""
    from app.api.routes.health import _check_redis

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.redis_url = "redis://myhost:6379/0"
        mock_settings.env = "production"
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Connection refused")
            result = await _check_redis()
            assert result["status"] == "unavailable"
            assert "error" in result


@pytest.mark.asyncio
async def test_check_neo4j_connection_exception():
    """Neo4j check returns unavailable when driver creation raises."""
    from app.api.routes.health import _check_neo4j

    with patch("app.api.routes.health.settings") as mock_settings:
        mock_settings.neo4j_uri = "bolt://myhost:7687"
        mock_settings.env = "production"
        mock_settings.neo4j_user = "neo4j"
        mock_settings.neo4j_password = "pass"
        with patch("neo4j.AsyncGraphDatabase.driver") as mock_driver:
            mock_driver.side_effect = Exception("Connection refused")
            result = await _check_neo4j()
            assert result["status"] == "unavailable"
            assert "error" in result
