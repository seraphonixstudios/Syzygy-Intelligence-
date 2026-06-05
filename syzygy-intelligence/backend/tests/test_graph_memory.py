"""Tests for GraphMemory (Neo4j knowledge graph)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


def _make_mock_driver(session_run=None):
    """Helper to create a mock Neo4j driver with async context manager."""
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.run = session_run or AsyncMock(return_value=AsyncMock())
    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_session)
    mock_driver.close = AsyncMock()
    return mock_driver


@pytest.fixture(autouse=True)
def mock_neo4j(monkeypatch):
    """Provide a fake neo4j module so GraphMemory can import it."""
    import sys
    fake_neo4j = MagicMock()
    # Simulate connection failure so _ensure_init catches the error and sets _initialized=True without _driver
    fake_neo4j.GraphDatabase.driver = MagicMock(side_effect=Exception("Neo4j unavailable"))
    monkeypatch.setitem(sys.modules, "neo4j", fake_neo4j)
    yield


@pytest.fixture
def graph_mem():
    with patch("app.memory.graph_memory.settings") as ms:
        ms.neo4j_uri = "bolt://localhost:7687"
        ms.neo4j_user = "neo4j"
        ms.neo4j_password = "password"
        from app.memory.graph_memory import GraphMemory
        gm = GraphMemory()
        yield gm


@pytest.mark.asyncio
async def test_init_no_driver(graph_mem):
    assert graph_mem._driver is None
    assert graph_mem._initialized is False
    await graph_mem._ensure_init()
    assert graph_mem._initialized is True


@pytest.mark.asyncio
async def test_store_driver_none(graph_mem):
    mid = await graph_mem.store("test content")
    assert mid is not None
    assert len(mid) > 0


@pytest.mark.asyncio
async def test_store_with_mock_driver(graph_mem):
    mock_driver = _make_mock_driver()
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    mid = await graph_mem.store("test", agent_id="a1", session_id="s1", tags=["tag1"])
    assert mid is not None
    assert mock_driver.session().run.call_count >= 3


@pytest.mark.asyncio
async def test_store_fallback():
    with patch("app.memory.graph_memory.settings") as ms:
        ms.neo4j_uri = "bolt://localhost:7687"
        ms.neo4j_user = "neo4j"
        ms.neo4j_password = "password"
        from app.memory.graph_memory import GraphMemory
        gm = GraphMemory()
        mid = await gm.store("content")
        assert mid is not None
        assert gm._initialized is True


@pytest.mark.asyncio
async def test_query_driver_none(graph_mem):
    results = await graph_mem.query(query_text="test")
    assert results == []


@pytest.mark.asyncio
async def test_query_with_mock(graph_mem):
    mock_record = MagicMock()
    mock_record.get.side_effect = lambda k, d=None: {
        "id": "mem1", "content": "hello", "agent_id": "a1",
        "session_id": "s1", "polarity": "masculine",
        "archetype": "sage", "tags": ["tag1"], "created_at": "now"
    }.get(k, d)
    mock_cursor = AsyncMock()
    mock_cursor.fetch = AsyncMock(return_value=[{"m": mock_record}])
    mock_driver = _make_mock_driver(session_run=AsyncMock(return_value=mock_cursor))
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    results = await graph_mem.query(polarity="masculine", limit=5)
    assert len(results) == 1
    assert results[0]["id"] == "mem1"
    assert results[0]["memory_type"] == "graph"
    assert results[0]["importance"] == 0.6


@pytest.mark.asyncio
async def test_query_with_filters(graph_mem):
    mock_cursor = AsyncMock()
    mock_cursor.fetch = AsyncMock(return_value=[])
    mock_driver = _make_mock_driver(session_run=AsyncMock(return_value=mock_cursor))
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    await graph_mem.query(agent_id="a1", archetype="sage", tags=["t1"])
    call_kwargs = mock_driver.session().run.call_args[1]
    assert "agent_id" in call_kwargs
    assert call_kwargs["agent_id"] == "a1"


@pytest.mark.asyncio
async def test_get_related_memories_driver_none(graph_mem):
    results = await graph_mem.get_related_memories("mem1")
    assert results == []


@pytest.mark.asyncio
async def test_get_related_memories_with_mock(graph_mem):
    connected_node = MagicMock()
    connected_node.get.side_effect = lambda k, d=None: {
        "id": "mem2", "content": "related", "agent_id": "a1",
        "polarity": "feminine", "tags": ["tag2"]
    }.get(k, d)
    mock_cursor = AsyncMock()
    mock_cursor.fetch = AsyncMock(return_value=[{"connected": connected_node}])
    mock_driver = _make_mock_driver(session_run=AsyncMock(return_value=mock_cursor))
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    results = await graph_mem.get_related_memories("mem1")
    assert len(results) == 1
    assert results[0]["id"] == "mem2"


@pytest.mark.asyncio
async def test_get_polarity_cluster(graph_mem):
    mock_cursor = AsyncMock()
    mock_cursor.fetch = AsyncMock(return_value=[])
    mock_driver = _make_mock_driver(session_run=AsyncMock(return_value=mock_cursor))
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    results = await graph_mem.get_polarity_cluster("feminine", limit=15)
    assert results == []


@pytest.mark.asyncio
async def test_delete_memory_driver_none(graph_mem):
    assert await graph_mem.delete_memory("mem1") is False


@pytest.mark.asyncio
async def test_delete_memory_success(graph_mem):
    mock_driver = _make_mock_driver()
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    assert await graph_mem.delete_memory("mem1") is True


@pytest.mark.asyncio
async def test_delete_memory_exception(graph_mem):
    mock_driver = _make_mock_driver(session_run=AsyncMock(side_effect=Exception("DB error")))
    graph_mem._driver = mock_driver
    graph_mem._initialized = True

    result = await graph_mem.delete_memory("mem1")
    assert result is False


@pytest.mark.asyncio
async def test_close(graph_mem):
    mock_driver = _make_mock_driver()
    graph_mem._driver = mock_driver
    await graph_mem.close()
    assert graph_mem._driver is None
    assert graph_mem._initialized is False


@pytest.mark.asyncio
async def test_close_no_driver(graph_mem):
    await graph_mem.close()
    assert graph_mem._driver is None
