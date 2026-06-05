"""Unit tests for Syzygy Memory System."""

import pytest
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.team_memory import TeamMemory
from app.memory.vector_store import VectorMemory


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
