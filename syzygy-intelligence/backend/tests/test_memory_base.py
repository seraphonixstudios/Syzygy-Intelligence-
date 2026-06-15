"""Tests for app.memory.base — Memory abstract base class."""

import pytest

from app.memory.base import Memory


class TestMemory:
    @pytest.fixture
    def memory(self):
        return Memory()

    @pytest.mark.asyncio
    async def test_init_creates_empty_store(self, memory):
        assert memory._store == {}

    @pytest.mark.asyncio
    async def test_add_memory_stores_value(self, memory):
        await memory.add_memory("key1", {"value": "hello"})
        assert memory._store["key1"] == {"value": "hello"}

    @pytest.mark.asyncio
    async def test_add_memory_overwrites_existing(self, memory):
        await memory.add_memory("key1", {"value": "first"})
        await memory.add_memory("key1", {"value": "second"})
        assert memory._store["key1"] == {"value": "second"}

    @pytest.mark.asyncio
    async def test_recall_returns_stored_value(self, memory):
        await memory.add_memory("key1", {"value": "hello"})
        result = await memory.recall("key1")
        assert result == {"value": "hello"}

    @pytest.mark.asyncio
    async def test_recall_returns_none_for_missing_key(self, memory):
        result = await memory.recall("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_add_memory_with_embedding_text(self, memory):
        await memory.add_memory("vec", {"data": [1, 2, 3]}, embedding_text="some text")
        assert memory._store["vec"] == {"data": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_recall_multiple_keys(self, memory):
        await memory.add_memory("a", {"val": 1})
        await memory.add_memory("b", {"val": 2})
        assert await memory.recall("a") == {"val": 1}
        assert await memory.recall("b") == {"val": 2}
        assert await memory.recall("c") is None
