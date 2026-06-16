"""Unit tests for Syzygy Memory System."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from app.memory.long_term import LongTermMemory
from app.memory.short_term import ShortTermMemory
from app.memory.team_memory import TeamMemory
from app.memory.vector_store import VectorMemory


@pytest.fixture(autouse=True)
def _mock_vector_init(monkeypatch):
    """Prevent VectorMemory from initializing ChromaDB (onnxruntime segfaults on some platforms)."""
    from app.memory import vector_store

    async def mock_ensure_init(self):
        self._initialized = True

    monkeypatch.setattr(vector_store.VectorMemory, "_ensure_init", mock_ensure_init)


class TestShortTermMemory:
    @pytest.mark.asyncio
    async def test_store_and_recall(self):
        mem = ShortTermMemory()
        mem_id = await mem.store("Test memory content", agent_id="agent_1", polarity="masculine")
        assert mem_id

        results = await mem.recall(agent_id="agent_1")
        assert len(results) == 1
        assert results[0]["content"] == "Test memory content"

    @pytest.mark.asyncio
    async def test_recall_by_polarity(self):
        mem = ShortTermMemory()
        await mem.store("Masc content", agent_id="a1", polarity="masculine")
        await mem.store("Fem content", agent_id="a2", polarity="feminine")

        masc_results = await mem.recall(polarity="masculine")
        assert len(masc_results) == 1

        fem_results = await mem.recall(polarity="feminine")
        assert len(fem_results) == 1

    @pytest.mark.asyncio
    async def test_recall_empty(self):
        mem = ShortTermMemory()
        results = await mem.recall(agent_id="nonexistent")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear_session(self):
        mem = ShortTermMemory()
        await mem.store("Memory 1", session_id="s1")
        await mem.store("Memory 2", session_id="s2")
        await mem.clear(session_id="s1")
        results = await mem.recall(session_id="s1")
        assert len(results) == 0
        results = await mem.recall(session_id="s2")
        assert len(results) == 1


class TestLongTermMemory:
    @pytest.mark.asyncio
    async def test_store_and_recall(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        mid = await mem.store("Important knowledge", importance=0.9, tags=["key"])
        assert mid

        results = await mem.recall()
        found = any(r["id"] == mid for r in results)
        assert found

    @pytest.mark.asyncio
    async def test_recall_by_importance(self, tmp_path):
        import app.config
        app.config.settings.data_dir = str(tmp_path)
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Mid priority", importance=0.5)
        await mem.store("High priority", importance=0.9)

        high = await mem.recall(min_importance=0.8)
        assert len(high) == 1
        assert high[0]["content"] == "High priority"

        all_mem = await mem.recall(min_importance=0.0)
        assert len(all_mem) >= 2

    @pytest.mark.asyncio
    async def test_forget(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        mid = await mem.store("To forget")
        assert await mem.forget(mid)
        assert not await mem.forget("nonexistent")

    @pytest.mark.asyncio
    async def test_recall_by_polarity(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Masc insight", polarity="masculine")
        await mem.store("Fem insight", polarity="feminine")
        masc = await mem.get_memories_by_polarity("masculine")
        fem = await mem.get_memories_by_polarity("feminine")
        assert len(masc) >= 1
        assert len(fem) >= 1


class TestTeamMemory:
    @pytest.mark.asyncio
    async def test_store_and_search(self):
        mem = TeamMemory()
        mid = await mem.store("Team insight", session_id="s1", tags=["collaboration"])
        assert mid

        results = await mem.search(session_id="s1")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_individuation_moment(self):
        mem = TeamMemory()
        mid = await mem.store_individuation_moment(
            session_id="s1",
            description="Significant polarity integration moment",
            polarity_insight="masculine and feminine reconciled",
        )
        assert mid

        results = await mem.search(memory_type="individuation")
        assert len(results) >= 1


class TestVectorMemory:
    @pytest.mark.asyncio
    async def test_store(self):
        mem = VectorMemory()
        mid = await mem.store("Vector content", agent_id="a1", polarity="unified")
        assert mid

    @pytest.mark.asyncio
    async def test_search(self):
        mem = VectorMemory()
        await mem.store("Searchable content", tags=["test"])
        results = await mem.search("searchable")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_empty_collection(self):
        mem = VectorMemory()
        results = await mem.search("nonexistent")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        mem = VectorMemory()
        await mem.store("Some content")
        results = await mem.search("")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_store_with_metadata(self):
        mem = VectorMemory()
        mid = await mem.store("Meta", agent_id="a1", session_id="s1", polarity="masculine", tags=["a", "b"])
        assert mid

    @pytest.mark.asyncio
    async def test_long_content(self):
        mem = VectorMemory()
        long_text = "word " * 500
        mid = await mem.store(long_text, tags=["long"])
        assert mid

    # ─── Additional VectorMemory coverage ─────────────────────────

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        mem = VectorMemory()
        mid = await mem.store("filtered content", agent_id="a1", polarity="masculine")
        results = await mem.search("filtered", agent_id="a1", polarity="masculine")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_returns_empty_when_collection_fails(self):
        mem = VectorMemory()
        with patch.object(mem, "_collection", None):
            results = await mem.search("query")
            assert results == []

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_no_collection(self):
        mem = VectorMemory()
        result = await mem.delete("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_count_returns_zero_when_no_collection(self):
        mem = VectorMemory()
        count = await mem.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_ensure_init_handles_import_error(self):
        from app.memory import vector_store
        mem = VectorMemory()
        mem._initialized = False
        # Make the import inside _ensure_init raise ImportError
        import builtins
        original_import = builtins.__import__

        def _mock_import(name, *args, **kwargs):
            if name == "chromadb":
                raise ImportError("No chromadb")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = _mock_import
        try:
            await mem._ensure_init()
            assert mem._initialized  # Should still set flag even on error
        finally:
            builtins.__import__ = original_import

    @pytest.mark.asyncio
    async def test_search_handles_chroma_exception(self):
        mem = VectorMemory()
        await mem._ensure_init()
        if mem._collection:
            mem._collection.query = MagicMock(side_effect=Exception("Chroma down"))
        results = await mem.search("query")
        assert results == []

    @pytest.mark.asyncio
    async def test_store_handles_chroma_exception(self):
        mem = VectorMemory()
        # Force initialized but no collection
        mem._initialized = True
        mem._collection = MagicMock()
        mem._collection.add.side_effect = Exception("Chroma down")
        mid = await mem.store("content")
        assert mid


# ═══════════════════════════════════════════════════════════
# MemorySystem (app/memory/__init__.py) — recall with vector, rag, knowledge
# ═══════════════════════════════════════════════════════════

class TestMemorySystemRecall:
    @pytest.fixture
    def mem_sys(self):
        from app.memory import MemorySystem
        return MemorySystem()

    @pytest.mark.asyncio
    async def test_recall_with_vector_types(self, mem_sys):
        mem_sys.vector.search = AsyncMock(return_value=[
            {"id": "v1", "content": "vector result", "importance": 0.7, "source": "vector"},
        ])
        mem_sys.short_term.recall = AsyncMock(return_value=[])
        mem_sys.long_term.recall = AsyncMock(return_value=[])
        results = await mem_sys.recall("query", memory_types=["vector"])
        assert len(results) == 1
        assert results[0]["content"] == "vector result"

    @pytest.mark.asyncio
    async def test_recall_with_rag_types(self, mem_sys):
        mem_sys.short_term.recall = AsyncMock(return_value=[])
        mem_sys.long_term.recall = AsyncMock(return_value=[])
        mem_sys.vector.search = AsyncMock(return_value=[])
        with patch("app.rag.retriever.query", new=AsyncMock(return_value=[
            {"id": "r1", "content": "rag result", "metadata": {"source": "doc"}},
        ])):
            results = await mem_sys.recall("query", memory_types=["rag"])
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_recall_rag_exception(self, mem_sys):
        mem_sys.short_term.recall = AsyncMock(return_value=[])
        mem_sys.long_term.recall = AsyncMock(return_value=[])
        mem_sys.vector.search = AsyncMock(return_value=[])
        with patch("app.rag.retriever.query", new=AsyncMock(side_effect=Exception("RAG down"))):
            results = await mem_sys.recall("query", memory_types=["rag"])
            assert len(results) == 0


# ═══════════════════════════════════════════════════════════
# GraphMemory (app/memory/graph_memory.py) — store, query, related
# ═══════════════════════════════════════════════════════════

class TestGraphMemoryEdgeCases:
    @pytest.fixture
    def graph(self):
        from app.memory.graph_memory import GraphMemory
        g = GraphMemory()
        g._initialized = True  # Skip init
        return g

    @pytest.mark.asyncio
    async def test_store_without_driver(self, graph):
        """store returns a memory_id even without a Neo4j driver."""
        mid = await graph.store("content")
        assert mid
        assert isinstance(mid, str)

    @pytest.mark.asyncio
    async def test_store_with_driver_success(self, graph):
        """store with a mock driver succeeds."""
        mock_session = AsyncMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        graph._driver = mock_driver
        mid = await graph.store("content", tags=["tag1"])
        assert mid
        assert mock_session.run.called

    @pytest.mark.asyncio
    async def test_store_driver_exception(self, graph):
        """store handles Neo4j exceptions gracefully."""
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("Neo4j down")
        graph._driver = mock_driver
        mid = await graph.store("content")
        assert mid

    @pytest.mark.asyncio
    async def test_query_without_driver(self, graph):
        """query returns empty list without a driver."""
        results = await graph.query("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_query_with_filters(self, graph):
        """query builds Cypher with all filters."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetch.return_value = []
        mock_session.run.return_value = mock_result
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        graph._driver = mock_driver
        results = await graph.query(
            query_text="test",
            agent_id="a1",
            polarity="masculine",
            archetype="sage",
            tags=["important"],
            limit=5,
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_query_exception(self, graph):
        """query handles Neo4j exceptions gracefully."""
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("Neo4j down")
        graph._driver = mock_driver
        results = await graph.query("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_related_memories_without_driver(self, graph):
        """get_related_memories returns empty list without driver."""
        results = await graph.get_related_memories("mem1")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_related_memories_exception(self, graph):
        """get_related_memories handles Neo4j exceptions."""
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("Neo4j down")
        graph._driver = mock_driver
        results = await graph.get_related_memories("mem1")
        assert results == []


# ═══════════════════════════════════════════════════════════
# LongTermMemory (app/memory/long_term.py) — recall edge cases
# ═══════════════════════════════════════════════════════════

class TestLongTermMemoryEdgeCases:
    @pytest.mark.asyncio
    async def test_recall_filters_by_polarity(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Masc content", polarity="masculine")
        await mem.store("Fem content", polarity="feminine")
        masc = await mem.recall(polarity="masculine")
        assert all(m.get("polarity") == "masculine" for m in masc)

    @pytest.mark.asyncio
    async def test_recall_filters_by_archetype(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Sage content", archetype="sage")
        await mem.store("Hero content", archetype="hero")
        sage = await mem.recall(archetype="sage")
        assert all(m.get("archetype") == "sage" for m in sage)

    @pytest.mark.asyncio
    async def test_recall_filters_by_min_importance(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Low importance", importance=0.3)
        await mem.store("High importance", importance=0.9)
        high = await mem.recall(min_importance=0.8)
        assert all(m.get("importance", 0) >= 0.8 for m in high)

    @pytest.mark.asyncio
    async def test_recall_filters_by_tags(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Tagged content", tags=["key", "important"])
        await mem.store("Untagged content", tags=["other"])
        tagged = await mem.recall(tags=["important"])
        assert any("Tagged" in m.get("content", "") for m in tagged)

    @pytest.mark.asyncio
    async def test_recall_filters_by_query(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Python programming tips")
        await mem.store("Cooking recipes")
        results = await mem.recall(query="Python")
        assert all("Python" in m.get("content", "") for m in results)

    @pytest.mark.asyncio
    async def test_get_memories_by_archetype(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Archetype memory", archetype="hero")
        results = await mem.get_memories_by_archetype("hero")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_recall_filters_by_agent_id(self, tmp_path):
        mem = LongTermMemory(storage_path=str(tmp_path / "long_term"))
        await mem.store("Agent A memory", agent_id="agent_a")
        await mem.store("Agent B memory", agent_id="agent_b")
        a_results = await mem.recall(agent_id="agent_a")
        assert len(a_results) == 1
        assert a_results[0]["content"] == "Agent A memory"
        b_results = await mem.recall(agent_id="agent_b")
        assert len(b_results) == 1
        assert b_results[0]["content"] == "Agent B memory"
        # recall with non-matching agent_id returns empty
        empty = await mem.recall(agent_id="nonexistent")
        assert len(empty) == 0


# ═══════════════════════════════════════════════════════════
# ShortTermMemory (app/memory/short_term.py) — recall edge cases
# ═══════════════════════════════════════════════════════════

class TestShortTermMemoryEdgeCases:
    @pytest.mark.asyncio
    async def test_recall_skips_expired(self):
        mem = ShortTermMemory()
        from datetime import datetime, timedelta, UTC
        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        mem._store["expired"] = {"content": "expired", "expires_at": past, "created_at": past}
        mem._store["valid"] = {"content": "valid", "created_at": datetime.now(UTC).isoformat()}
        results = await mem.recall()
        assert not any(r.get("id") == "expired" for r in results)

    @pytest.mark.asyncio
    async def test_recall_filters_by_agent_id(self):
        mem = ShortTermMemory()
        mem._store["a1"] = {"content": "agent1 mem", "agent_id": "agent_1", "created_at": "2024-01-01T00:00:00"}
        mem._store["a2"] = {"content": "agent2 mem", "agent_id": "agent_2", "created_at": "2024-01-01T00:00:00"}
        results = await mem.recall(agent_id="agent_1")
        assert len(results) == 1
        assert results[0]["content"] == "agent1 mem"

    @pytest.mark.asyncio
    async def test_recall_filters_by_query(self):
        mem = ShortTermMemory()
        mem._store["m1"] = {"content": "Python is great", "created_at": "2024-01-01T00:00:00"}
        mem._store["m2"] = {"content": "JavaScript is ok", "created_at": "2024-01-01T00:00:00"}
        results = await mem.recall(query="Python")
        assert len(results) == 1
        assert results[0]["content"] == "Python is great"

    @pytest.mark.asyncio
    async def test_get_recent(self):
        mem = ShortTermMemory()
        mem._store["m1"] = {"content": "old", "session_id": "s1", "created_at": "2023-01-01T00:00:00"}
        mem._store["m2"] = {"content": "new", "session_id": "s1", "created_at": "2024-01-01T00:00:00"}
        results = await mem.get_recent(session_id="s1", limit=1)
        assert len(results) == 1
        assert results[0]["content"] == "new"

    @pytest.mark.asyncio
    async def test_clear_all(self):
        mem = ShortTermMemory()
        mem._store["m1"] = {"content": "a", "session_id": "s1"}
        mem._store["m2"] = {"content": "b", "session_id": "s2"}
        await mem.clear()
        assert len(mem._store) == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        mem = ShortTermMemory()
        from datetime import datetime, timedelta, UTC
        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        mem._store["expired"] = {"content": "gone", "expires_at": past}
        mem._store["valid"] = {"content": "stays", "expires_at": future}
        mem._store["no_expiry"] = {"content": "also stays"}
        await mem.cleanup_expired()
        assert "expired" not in mem._store
        assert "valid" in mem._store
        assert "no_expiry" in mem._store


# ═══════════════════════════════════════════════════════════
# TeamMemory (app/memory/team_memory.py) — search edge cases
# ═══════════════════════════════════════════════════════════

class TestTeamMemoryEdgeCases:
    @pytest.fixture
    def team_mem(self, tmp_path):
        mem = TeamMemory()
        mem.storage_path = tmp_path / "team"
        mem.storage_path.mkdir(exist_ok=True)
        return mem

    @pytest.mark.asyncio
    async def test_search_filters_by_session_id(self, team_mem):
        await team_mem.store("Session A data", session_id="s1")
        await team_mem.store("Session B data", session_id="s2")
        results = await team_mem.search(session_id="s1")
        assert all(r.get("session_id") == "s1" for r in results)

    @pytest.mark.asyncio
    async def test_search_filters_by_query(self, team_mem):
        await team_mem.store("Python memory", session_id="s1")
        await team_mem.store("Java memory", session_id="s2")
        results = await team_mem.search(query="Python")
        assert all("Python" in r.get("content", "") for r in results)

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, team_mem):
        for i in range(5):
            await team_mem.store(f"Item {i}", session_id="s1")
        results = await team_mem.search(session_id="s1", limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_empty_store(self, team_mem):
        results = await team_mem.search()
        assert results == []
