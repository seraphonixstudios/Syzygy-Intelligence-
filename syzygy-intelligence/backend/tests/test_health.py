"""Tests for the health check endpoint."""

from unittest.mock import AsyncMock, patch

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
