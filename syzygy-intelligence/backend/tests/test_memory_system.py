"""Tests for the unified MemorySystem (app.memory.__init__)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_subsystems():
    with (
        patch("app.memory.ShortTermMemory") as mock_st,
        patch("app.memory.LongTermMemory") as mock_lt,
        patch("app.memory.VectorMemory") as mock_vec,
        patch("app.memory.GraphMemory") as mock_gr,
        patch("app.memory.TeamMemory") as mock_tm,
    ):
        mock_st_instance = AsyncMock()
        mock_st_instance.store = AsyncMock(return_value="st-id")
        mock_st_instance.recall = AsyncMock(return_value=[{"id": "st-1", "content": "short term", "importance": 0.2}])
        mock_st_instance.get_recent = AsyncMock(return_value=[{"id": "st-1"}])
        mock_st.return_value = mock_st_instance

        mock_lt_instance = AsyncMock()
        mock_lt_instance.store = AsyncMock(return_value="lt-id")
        mock_lt_instance.recall = AsyncMock(return_value=[{"id": "lt-1", "content": "long term", "importance": 0.9}])
        mock_lt.return_value = mock_lt_instance

        mock_vec_instance = AsyncMock()
        mock_vec_instance.store = AsyncMock(return_value="vec-id")
        mock_vec_instance.search = AsyncMock(return_value=[{"id": "vec-1", "content": "vector", "importance": 0.8}])
        mock_vec.return_value = mock_vec_instance

        mock_gr_instance = AsyncMock()
        mock_gr_instance.store = AsyncMock()
        mock_gr.return_value = mock_gr_instance

        mock_tm_instance = AsyncMock()
        mock_tm_instance.store = AsyncMock()
        mock_tm_instance.search = AsyncMock(return_value=[{"content": "team memory"}])
        mock_tm.return_value = mock_tm_instance

        yield {
            "st": mock_st_instance,
            "lt": mock_lt_instance,
            "vec": mock_vec_instance,
            "gr": mock_gr_instance,
            "tm": mock_tm_instance,
        }


class TestMemorySystemStore:
    @pytest.mark.asyncio
    async def test_stores_short_term_when_importance_low(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        mid = await ms.store("low importance", memory_type="short_term", agent_id="a1", importance=0.2)
        _mock_subsystems["st"].store.assert_called_once()
        _mock_subsystems["lt"].store.assert_not_called()
        assert mid == "st-id"

    @pytest.mark.asyncio
    async def test_stores_long_term_when_importance_high(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        mid = await ms.store("important", memory_type="long_term", importance=0.9)
        _mock_subsystems["lt"].store.assert_called_once()
        assert mid == "lt-id"

    @pytest.mark.asyncio
    async def test_stores_vector_when_type_is_vector(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        mid = await ms.store("vector data", memory_type="vector", importance=0.5)
        _mock_subsystems["vec"].store.assert_called_once()
        assert mid == "vec-id"

    @pytest.mark.asyncio
    async def test_medium_importance_goes_to_short_term(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        # importance 0.5 with explicit short_term type
        await ms.store("mid", memory_type="short_term", importance=0.5)
        _mock_subsystems["st"].store.assert_called_once()
        _mock_subsystems["lt"].store.assert_not_called()

    @pytest.mark.asyncio
    async def test_low_importance_routes_to_short_term(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        # importance 0.1 (< 0.3) forces short_term even with explicit long_term type
        await ms.store("low", memory_type="long_term", importance=0.1)
        _mock_subsystems["st"].store.assert_called_once()
        _mock_subsystems["lt"].store.assert_not_called()

    @pytest.mark.asyncio
    async def test_stores_in_graph_when_tags_present(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        await ms.store("tagged", tags=["important", "research"], agent_id="a1", importance=0.5)
        _mock_subsystems["gr"].store.assert_called_once()


class TestMemorySystemRecall:
    @pytest.mark.asyncio
    async def test_recalls_from_multiple_layers(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        results = await ms.recall("query", memory_types=["short_term", "long_term"])
        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_memories(self, _mock_subsystems):
        _mock_subsystems["st"].recall.return_value = []
        _mock_subsystems["lt"].recall.return_value = []
        from app.memory import MemorySystem
        ms = MemorySystem()
        results = await ms.recall("query", memory_types=["short_term", "long_term"])
        assert results == []

    @pytest.mark.asyncio
    async def test_sorts_by_importance(self, _mock_subsystems):
        _mock_subsystems["st"].recall.return_value = [
            {"id": "a", "content": "low", "importance": 0.1},
            {"id": "b", "content": "high", "importance": 0.9},
        ]
        from app.memory import MemorySystem
        ms = MemorySystem()
        results = await ms.recall("query", memory_types=["short_term"])
        assert results[0]["id"] == "b"
        assert results[1]["id"] == "a"

    @pytest.mark.asyncio
    async def test_deduplicates_by_id(self, _mock_subsystems):
        _mock_subsystems["st"].recall.return_value = [
            {"id": "dup", "content": "first", "importance": 0.5},
        ]
        _mock_subsystems["lt"].recall.return_value = [
            {"id": "dup", "content": "second", "importance": 0.5},
            {"id": "uniq", "content": "unique", "importance": 0.6},
        ]
        from app.memory import MemorySystem
        ms = MemorySystem()
        results = await ms.recall("query", memory_types=["short_term", "long_term"])
        ids = [r["id"] for r in results]
        assert ids.count("dup") == 1


class TestMemorySystemConvenience:
    @pytest.mark.asyncio
    async def test_remember_recent_delegates(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        results = await ms.remember_recent("session-1")
        _mock_subsystems["st"].get_recent.assert_called_once()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_team_memory_delegates(self, _mock_subsystems):
        from app.memory import MemorySystem
        ms = MemorySystem()
        results = await ms.search_team_memory("query")
        _mock_subsystems["tm"].search.assert_called_once()
        assert results[0]["content"] == "team memory"
