"""Tests for session management API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _make_session(sid="00000000-0000-0000-0000-000000000001", name="Test Session",
                  task="Do something", state_val="active", workflow_type="general",
                  rounds=0, synthesis=None, polarity=0.5):
    s = MagicMock()
    s.id = sid
    s.name = name
    s.task_description = task
    s.state = MagicMock()
    s.state.value = state_val
    s.workflow_type = workflow_type
    s.consensus_rounds_completed = rounds
    s.final_synthesis = synthesis
    s.polarity_balance_score = polarity
    s.created_at = MagicMock()
    s.created_at.isoformat.return_value = "2026-01-01T00:00:00"
    s.updated_at = MagicMock()
    s.updated_at.isoformat.return_value = "2026-01-01T01:00:00"
    s.consensus_rounds = []
    return s


def _make_round(rnum=1, status_val="completed"):
    r = MagicMock()
    r.round_number = rnum
    r.status = MagicMock()
    r.status.value = status_val
    r.proposals = {}
    r.critiques = {}
    r.refinements = {}
    r.scores = {}
    r.convergence_score = 0.9
    return r


def _mock_user(uid="u1"):
    u = MagicMock()
    u.id = uid
    return u


class MockScalarsResult:
    def __init__(self, sessions=None):
        self._sessions = sessions or []

    def scalars(self):
        return self

    def all(self):
        return self._sessions

    def scalar_one_or_none(self):
        return None


class TestListSessions:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        db = AsyncMock()
        db.execute.return_value = MockScalarsResult([])

        from app.api.routes.sessions import list_sessions
        result = await list_sessions(user=_mock_user(), db=db)
        assert result["sessions"] == []

    @pytest.mark.asyncio
    async def test_returns_sessions_list(self):
        sessions = [
            _make_session(sid="id1", name="Session 1", task="Task 1", rounds=3),
            _make_session(sid="id2", name="Session 2", task="Task 2", rounds=5),
        ]
        db = AsyncMock()
        db.execute.return_value = MockScalarsResult(sessions)

        from app.api.routes.sessions import list_sessions
        result = await list_sessions(user=_mock_user(), db=db)
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["name"] == "Session 1"
        assert result["sessions"][1]["name"] == "Session 2"

    @pytest.mark.asyncio
    async def test_passes_limit_and_offset(self):
        db = AsyncMock()
        db.execute.return_value = MockScalarsResult([])

        from app.api.routes.sessions import list_sessions
        await list_sessions(user=_mock_user(), db=db, limit=10, offset=20)
        call_kwargs = db.execute.call_args[0][0]
        assert call_kwargs._limit == 10
        assert call_kwargs._offset == 20

    @pytest.mark.asyncio
    async def test_truncates_long_synthesis(self):
        long_text = "x" * 300
        s = _make_session(synthesis=long_text)
        db = AsyncMock()
        db.execute.return_value = MockScalarsResult([s])

        from app.api.routes.sessions import list_sessions
        result = await list_sessions(user=_mock_user(), db=db)
        assert result["sessions"][0]["final_synthesis"] == "x" * 200 + "..."

    @pytest.mark.asyncio
    async def test_short_synthesis_not_truncated(self):
        short_text = "short"
        s = _make_session(synthesis=short_text)
        db = AsyncMock()
        db.execute.return_value = MockScalarsResult([s])

        from app.api.routes.sessions import list_sessions
        result = await list_sessions(user=_mock_user(), db=db)
        assert result["sessions"][0]["final_synthesis"] == "short"

    @pytest.mark.asyncio
    async def test_none_fields_handled(self):
        s = _make_session()
        s.state = None
        s.created_at = None
        s.final_synthesis = None
        db = AsyncMock()
        db.execute.return_value = MockScalarsResult([s])

        from app.api.routes.sessions import list_sessions
        result = await list_sessions(user=_mock_user(), db=db)
        assert result["sessions"][0]["state"] == "unknown"
        assert result["sessions"][0]["created_at"] == ""
        assert result["sessions"][0]["final_synthesis"] is None

    @pytest.mark.asyncio
    async def test_logs_and_raises_on_error(self):
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("db fail")

        from app.api.routes.sessions import list_sessions
        with pytest.raises(HTTPException) as exc:
            await list_sessions(user=_mock_user(), db=db)
        assert exc.value.status_code == 500


class TestCreateSession:
    @pytest.mark.asyncio
    async def test_creates_session(self):
        agent = MagicMock()
        agent.id = "agent-1"
        session = _make_session(name="New Session")
        db = AsyncMock()
        db.execute = AsyncMock()
        result_mock = MockScalarsResult()
        result_mock.scalar_one_or_none = MagicMock(return_value=agent)
        db.execute.return_value = result_mock
        db.add = MagicMock()
        db.refresh = AsyncMock()

        from app.api.routes.sessions import create_session
        result = await create_session(
            data={"name": "New Session", "task": "Do work", "workflow_type": "research"},
            user=_mock_user(),
            db=db,
        )
        assert result["name"] == "New Session"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_creates_default_agent(self):
        db = AsyncMock()
        no_agent = MockScalarsResult()
        no_agent.scalar_one_or_none = MagicMock(return_value=None)
        agent = MagicMock()
        agent.id = "new-agent"
        with_agent = MockScalarsResult()
        with_agent.scalar_one_or_none = MagicMock(return_value=agent)
        db.execute = AsyncMock()
        db.execute.side_effect = [no_agent, with_agent]
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        from app.api.routes.sessions import create_session
        result = await create_session(
            data={"name": "New Session"},
            user=_mock_user(),
            db=db,
        )
        assert result["name"] == "New Session"
        assert db.add.called

    @pytest.mark.asyncio
    async def test_uses_defaults(self):
        agent = MagicMock()
        agent.id = "agent-1"
        db = AsyncMock()
        result_mock = MockScalarsResult()
        result_mock.scalar_one_or_none = MagicMock(return_value=agent)
        db.execute.return_value = result_mock
        db.add = MagicMock()
        db.refresh = AsyncMock()

        from app.api.routes.sessions import create_session
        result = await create_session(
            data={},
            user=_mock_user(),
            db=db,
        )
        assert result["name"] == "New Session"

    @pytest.mark.asyncio
    async def test_logs_and_raises_on_error(self):
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("db fail")

        from app.api.routes.sessions import create_session
        with pytest.raises(HTTPException) as exc:
            await create_session(data={}, user=_mock_user(), db=db)
        assert exc.value.status_code == 500


class TestGetSession:
    @pytest.mark.asyncio
    async def test_returns_session(self):
        s = _make_session(synthesis="Final result")
        s.consensus_rounds = [_make_round(1)]
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = s
        db.execute.return_value = result_mock

        from app.api.routes.sessions import get_session
        result = await get_session(session_id="00000000-0000-0000-0000-000000000001", user=_mock_user(), db=db)
        assert result["id"] == "00000000-0000-0000-0000-000000000001"
        assert result["task"] == "Do something"
        assert result["final_synthesis"] == "Final result"
        assert len(result["rounds"]) == 1

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        from app.api.routes.sessions import get_session
        with pytest.raises(HTTPException) as exc:
            await get_session(session_id="00000000-0000-0000-0000-000000000001", user=_mock_user(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_handles_none_state_and_dates(self):
        s = _make_session()
        s.state = None
        s.created_at = None
        s.updated_at = None
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = s
        db.execute.return_value = result_mock

        from app.api.routes.sessions import get_session
        result = await get_session(session_id="00000000-0000-0000-0000-000000000001", user=_mock_user(), db=db)
        assert result["state"] == "unknown"
        assert result["created_at"] == ""
        assert result["updated_at"] == ""

    @pytest.mark.asyncio
    async def test_handles_invalid_uuid(self):
        db = AsyncMock()

        from app.api.routes.sessions import get_session
        with pytest.raises(HTTPException) as exc:
            await get_session(session_id="not-a-uuid", user=_mock_user(), db=db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_logs_and_raises_on_error(self):
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("db fail")

        from app.api.routes.sessions import get_session
        with pytest.raises(HTTPException) as exc:
            await get_session(session_id="00000000-0000-0000-0000-000000000001", user=_mock_user(), db=db)
        assert exc.value.status_code == 500
