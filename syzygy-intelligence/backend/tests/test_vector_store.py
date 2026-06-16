"""Tests for memory/vector_store.py — ChromaDB vector memory store."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_chromadb():
    """Mock chromadb module to avoid native module crashes."""
    mock_ef = MagicMock()
    mock_ef.return_value = MagicMock()

    mock_collection = MagicMock()
    mock_collection.count.return_value = 3
    mock_collection.add.return_value = None
    mock_collection.delete.return_value = None
    mock_collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "distances": [[0.1, 0.3]],
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"agent_id": "a1"}, {"agent_id": "a2"}]],
    }

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    mock_chroma = MagicMock()
    mock_chroma.PersistentClient.return_value = mock_client
    mock_chroma.utils.embedding_functions.DefaultEmbeddingFunction = mock_ef

    # Ensure chromadb submodules are in sys.modules so `from chromadb.utils import ...`
    # works via the import machinery (Python needs submodule entries for mock packages).
    chroma_utils = MagicMock()
    chroma_utils.embedding_functions = MagicMock()
    chroma_utils.embedding_functions.DefaultEmbeddingFunction = mock_ef
    with patch.dict(
        "sys.modules",
        {
            "chromadb": mock_chroma,
            "chromadb.utils": chroma_utils,
            "chromadb.utils.embedding_functions": chroma_utils.embedding_functions,
        },
    ):
        yield mock_collection, mock_client


@pytest.mark.asyncio
async def test_init_success(mock_chromadb):
    mock_collection, mock_client = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    await vm._ensure_init()

    assert vm._initialized is True
    assert vm._collection is mock_collection
    mock_client.get_or_create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_store_adds_document(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    memory_id = await vm.store("test content", agent_id="agent1", session_id="session1", polarity="masculine")

    assert memory_id is not None
    assert isinstance(memory_id, str)
    mock_collection.add.assert_called_once()
    call_args = mock_collection.add.call_args
    assert call_args[1]["documents"] == ["test content"]
    assert call_args[1]["metadatas"][0]["agent_id"] == "agent1"
    assert call_args[1]["metadatas"][0]["session_id"] == "session1"
    assert call_args[1]["metadatas"][0]["polarity"] == "masculine"


@pytest.mark.asyncio
async def test_store_with_tags(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    await vm.store("content", tags=["important", "urgent"])

    meta = mock_collection.add.call_args[1]["metadatas"][0]
    assert meta["tags"] == "important,urgent"


@pytest.mark.asyncio
async def test_store_with_extra_metadata(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    await vm.store("content", metadata={"source": "test", "confidence": 0.9})

    meta = mock_collection.add.call_args[1]["metadatas"][0]
    assert meta["source"] == "test"
    assert meta["confidence"] == 0.9


@pytest.mark.asyncio
async def test_store_add_failure_logged(mock_chromadb):
    mock_collection, _ = mock_chromadb
    mock_collection.add.side_effect = Exception("storage error")

    from app.memory.vector_store import VectorMemory
    from app.logging_setup import logger

    vm = VectorMemory()
    with patch.object(logger, "error") as mock_log:
        memory_id = await vm.store("content")

    assert memory_id is not None
    mock_log.assert_called_once()
    assert "storage error" in str(mock_log.call_args)


@pytest.mark.asyncio
async def test_search_returns_results(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    results = await vm.search("test query")

    assert len(results) == 2
    assert results[0]["id"] == "id1"
    assert results[0]["content"] == "doc1"
    assert results[0]["score"] == 0.9
    assert results[0]["memory_type"] == "vector"


@pytest.mark.asyncio
async def test_search_with_filters(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    await vm.search("query", agent_id="agent1", polarity="feminine")

    call_kwargs = mock_collection.query.call_args[1]
    assert call_kwargs["where"]["agent_id"] == "agent1"
    assert call_kwargs["where"]["polarity"] == "feminine"


@pytest.mark.asyncio
async def test_search_with_min_score_filters_low(mock_chromadb):
    mock_collection, _ = mock_chromadb
    mock_collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "distances": [[0.1, 0.8]],
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{}, {}]],
    }
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    results = await vm.search("query", min_score=0.5)

    assert len(results) == 1
    assert results[0]["id"] == "id1"


@pytest.mark.asyncio
async def test_search_respects_limit(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    results = await vm.search("query", limit=1)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_error_returns_empty(mock_chromadb):
    mock_collection, _ = mock_chromadb
    mock_collection.query.side_effect = Exception("query failed")

    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    results = await vm.search("query")

    assert results == []


@pytest.mark.asyncio
async def test_delete_removes_document(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    result = await vm.delete("memory_id_1")

    assert result is True
    mock_collection.delete.assert_called_once_with(ids=["memory_id_1"])


@pytest.mark.asyncio
async def test_delete_failure_returns_false(mock_chromadb):
    mock_collection, _ = mock_chromadb
    mock_collection.delete.side_effect = Exception("delete failed")

    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    result = await vm.delete("memory_id_1")

    assert result is False


@pytest.mark.asyncio
async def test_delete_when_not_initialized():
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    # Block chromadb so _ensure_init fails silently
    chroma_keys = [k for k in __import__("sys").modules if k.startswith("chromadb")]
    with patch.dict("sys.modules", {"chromadb": None, **{k: None for k in chroma_keys}}):
        result = await vm.delete("memory_id_1")

    assert result is False


@pytest.mark.asyncio
async def test_count_returns_number(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    count = await vm.count()

    assert count == 3


@pytest.mark.asyncio
async def test_count_when_not_initialized():
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    chroma_keys = [k for k in __import__("sys").modules if k.startswith("chromadb")]
    with patch.dict("sys.modules", {"chromadb": None, **{k: None for k in chroma_keys}}):
        count = await vm.count()

    assert count == 0


@pytest.mark.asyncio
async def test_count_error_returns_zero(mock_chromadb):
    mock_collection, _ = mock_chromadb
    mock_collection.count.side_effect = Exception("count failed")

    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    count = await vm.count()

    assert count == 0


@pytest.mark.asyncio
async def test_search_without_agent_or_polarity_filter(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    await vm.search("query")

    call_kwargs = mock_collection.query.call_args[1]
    assert call_kwargs["where"] is None


@pytest.mark.asyncio
async def test_store_handles_empty_agent_id(mock_chromadb):
    mock_collection, _ = mock_chromadb
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    await vm.store("content")

    meta = mock_collection.add.call_args[1]["metadatas"][0]
    assert meta["agent_id"] == ""
    assert meta["session_id"] == ""
    assert meta["polarity"] == "unknown"


@pytest.mark.asyncio
async def test_chroma_generic_exception_disables_vector_store():
    """Verify generic Exception during Chroma init is handled gracefully."""
    from app.memory.vector_store import logger, VectorMemory

    vm = VectorMemory()
    with (
        patch("chromadb.PersistentClient", side_effect=Exception("Disk full")) as mock_client,
        patch.object(logger, "warning") as mock_warn,
    ):
        await vm._ensure_init()

    mock_warn.assert_called_once()
    assert "Disk full" in str(mock_warn.call_args)
    assert vm._initialized is True


@pytest.mark.asyncio
async def test_chroma_import_error_disables_vector_store():
    """Verify ImportError when chromadb is unavailable is handled gracefully."""
    from app.memory.vector_store import logger, VectorMemory

    vm = VectorMemory()
    # Block chromadb from sys.modules so import raises ImportError
    chroma_keys = [k for k in __import__("sys").modules if k.startswith("chromadb")]
    with (
        patch.dict("sys.modules", {"chromadb": None, **{k: None for k in chroma_keys}}),
        patch.object(logger, "warning") as mock_warn,
    ):
        await vm._ensure_init()

    mock_warn.assert_called_once()
    assert "Chroma import failed" in str(mock_warn.call_args)
    assert vm._initialized is True
    assert vm._collection is None


@pytest.mark.asyncio
async def test_store_when_not_initialized_does_not_crash(mock_chromadb):
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    memory_id = await vm.store("content")

    assert memory_id is not None
    assert isinstance(memory_id, str)


@pytest.mark.asyncio
async def test_search_when_not_initialized_returns_empty():
    from app.memory.vector_store import VectorMemory

    vm = VectorMemory()
    chroma_keys = [k for k in __import__("sys").modules if k.startswith("chromadb")]
    with patch.dict("sys.modules", {"chromadb": None, **{k: None for k in chroma_keys}}):
        results = await vm.search("query")

    assert results == []
