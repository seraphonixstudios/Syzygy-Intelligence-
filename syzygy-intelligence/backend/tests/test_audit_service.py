"""Tests for AuditService — real SQLite DB for query/count filter logic."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import AuditLog
from app.db.session import Base


@pytest_asyncio.fixture
async def engine_and_factory():
    """Create in-memory SQLite and return (engine, factory)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine_and_factory):
    engine, factory = engine_and_factory
    session = factory()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def seeded_db(engine_and_factory):
    """Insert sample audit logs using valid UUIDs for agent_id and session_id."""
    engine, factory = engine_and_factory
    session = factory()
    try:
        entries = [
            AuditLog(
                id=uuid.uuid4(),
                event_type="login",
                action="user_login",
                agent_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
            ),
            AuditLog(
                id=uuid.uuid4(),
                event_type="login",
                action="user_login",
                agent_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
            ),
            AuditLog(
                id=uuid.uuid4(),
                event_type="consensus",
                action="round_complete",
                agent_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
            ),
        ]
        for e in entries:
            session.add(e)
        await session.commit()
        return {"session": session, "factory": factory, "entries": entries}
    except Exception:
        await session.close()
        raise


class TestAuditServiceLog:
    @pytest.mark.asyncio
    async def test_log_creates_entry(self, engine_and_factory):
        engine, factory = engine_and_factory
        session = factory()
        try:
            from app.audit import AuditService
            with patch("app.audit._get_session_factory", return_value=factory):
                entry_id = await AuditService.log("test", "action", agent_id="a1")
                assert entry_id
                result = await session.execute(select(AuditLog))
                assert len(result.scalars().all()) == 1
        finally:
            await session.close()

    @pytest.mark.asyncio
    async def test_log_returns_empty_on_error(self):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            entry_id = await AuditService.log("test", "action")
            assert entry_id == ""


class TestAuditServiceQuery:
    @pytest.mark.asyncio
    async def test_query_all(self, seeded_db):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            results = await AuditService.query()
            assert len(results) >= 3

    @pytest.mark.asyncio
    async def test_query_by_event_type(self, seeded_db):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            results = await AuditService.query(event_type="login")
            assert len(results) == 2
            assert all(r["event_type"] == "login" for r in results)

    @pytest.mark.asyncio
    async def test_query_by_agent_id(self, seeded_db):
        agent_id = seeded_db["entries"][0].agent_id
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            results = await AuditService.query(agent_id=agent_id)
            assert len(results) == 1
            assert all(r["agent_id"] == str(agent_id) for r in results)

    @pytest.mark.asyncio
    async def test_query_by_session_id(self, seeded_db):
        session_id = seeded_db["entries"][0].session_id
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            results = await AuditService.query(session_id=session_id)
            assert len(results) == 1
            assert all(r["session_id"] == str(session_id) for r in results)

    @pytest.mark.asyncio
    async def test_query_with_limit_and_offset(self, seeded_db):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            results = await AuditService.query(limit=1, offset=0)
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_query_returns_empty_on_error(self):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            results = await AuditService.query()
            assert results == []


class TestAuditServiceCount:
    @pytest.mark.asyncio
    async def test_count_all(self, seeded_db):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            count = await AuditService.count()
            assert count == 3

    @pytest.mark.asyncio
    async def test_count_by_event_type(self, seeded_db):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            count = await AuditService.count(event_type="login")
            assert count == 2

    @pytest.mark.asyncio
    async def test_count_by_agent_id(self, seeded_db):
        agent_id = seeded_db["entries"][0].agent_id
        from app.audit import AuditService
        with patch("app.audit._get_session_factory", return_value=seeded_db["factory"]):
            count = await AuditService.count(agent_id=agent_id)
            assert count == 1

    @pytest.mark.asyncio
    async def test_count_returns_zero_on_error(self):
        from app.audit import AuditService
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            count = await AuditService.count()
            assert count == 0
