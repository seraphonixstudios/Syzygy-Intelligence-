"""Tests for memory API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException


class TestStoreMemory:
    @pytest.mark.asyncio
    async def test_stores_memory(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.store = AsyncMock(return_value="mem-123")
            from app.api.routes.memory import store_memory

            result = await store_memory({
                "content": "Important info",
                "type": "long_term",
                "agent_id": "agent-1",
                "importance": 0.9,
            })
            assert result["memory_id"] == "mem-123"
            m_mem.store.assert_awaited_with(
                content="Important info",
                memory_type="long_term",
                agent_id="agent-1",
                session_id="",
                polarity="",
                archetype="",
                importance=0.9,
                tags=[],
            )

    @pytest.mark.asyncio
    async def test_uses_defaults(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.store = AsyncMock(return_value="mem-default")
            from app.api.routes.memory import store_memory

            result = await store_memory({})
            m_mem.store.assert_awaited_with(
                content="",
                memory_type="short_term",
                agent_id="",
                session_id="",
                polarity="",
                archetype="",
                importance=0.5,
                tags=[],
            )

    @pytest.mark.asyncio
    async def test_handles_error(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.store = AsyncMock(side_effect=RuntimeError("store failed"))
            from app.api.routes.memory import store_memory

            with pytest.raises(HTTPException) as exc:
                await store_memory({"content": "test"})
            assert exc.value.status_code == 500


class TestRecallMemory:
    @pytest.mark.asyncio
    async def test_recalls_by_query(self):
        mock_results = [{"id": "m1", "content": "Result 1", "importance": 0.8}]
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.recall = AsyncMock(return_value=mock_results)
            from app.api.routes.memory import recall_memory

            result = await recall_memory(query="test query", agent_id="", polarity="", limit=10)
            assert len(result["memories"]) == 1
            m_mem.recall.assert_awaited_with(
                query="test query", agent_id="", polarity="", limit=10
            )

    @pytest.mark.asyncio
    async def test_filters_by_agent_and_polarity(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.recall = AsyncMock(return_value=[])
            from app.api.routes.memory import recall_memory

            await recall_memory(query="", agent_id="agent-1", polarity="masculine", limit=5)
            m_mem.recall.assert_awaited_with(
                query="", agent_id="agent-1", polarity="masculine", limit=5
            )

    @pytest.mark.asyncio
    async def test_handles_error(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.recall = AsyncMock(side_effect=RuntimeError("recall failed"))
            from app.api.routes.memory import recall_memory

            with pytest.raises(HTTPException) as exc:
                await recall_memory(query="test", agent_id="", polarity="", limit=10)
            assert exc.value.status_code == 500


class TestRecentMemories:
    @pytest.mark.asyncio
    async def test_returns_recent(self):
        mock_results = [{"id": "m1", "content": "Recent", "importance": 0.5}]
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.remember_recent = AsyncMock(return_value=mock_results)
            from app.api.routes.memory import recent_memories

            result = await recent_memories(session_id="session-1", limit=5)
            assert len(result["memories"]) == 1
            m_mem.remember_recent.assert_awaited_with(session_id="session-1", limit=5)

    @pytest.mark.asyncio
    async def test_returns_empty(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.remember_recent = AsyncMock(return_value=[])
            from app.api.routes.memory import recent_memories

            result = await recent_memories(session_id="", limit=5)
            assert result["memories"] == []

    @pytest.mark.asyncio
    async def test_handles_error(self):
        with patch("app.api.routes.memory.memory_system") as m_mem:
            m_mem.remember_recent = AsyncMock(side_effect=RuntimeError("recent failed"))
            from app.api.routes.memory import recent_memories

            with pytest.raises(HTTPException) as exc:
                await recent_memories(session_id="test", limit=5)
            assert exc.value.status_code == 500
