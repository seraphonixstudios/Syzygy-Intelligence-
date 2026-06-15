"""Tests for tools API routes."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from app.api.routes.tools import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return app


class TestListTools:
    @pytest.mark.asyncio
    async def test_returns_tools(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data
        assert len(data["tools"]) == 5
        tool_ids = [t["id"] for t in data["tools"]]
        assert "browser" in tool_ids
        assert "search" in tool_ids


class TestExecuteTool:
    @pytest.mark.asyncio
    async def test_executes_tool(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/execute", json={"tool_id": "browser", "params": {"url": "http://example.com"}})
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool_id"] == "browser"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_executes_with_empty_params(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/execute", json={"tool_id": "git"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool_id"] == "git"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_executes_without_data(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/execute", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool_id"] == ""
        assert data["status"] == "completed"
