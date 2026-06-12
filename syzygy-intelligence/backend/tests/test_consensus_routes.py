"""Integration tests for consensus API routes using FastAPI TestClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import require_user
from app.api.routes.consensus import router as consensus_router
from app.consensus.engine import ConsensusRound, ConsensusSession
from app.db.session import get_db

# Build minimal test app with only the consensus router
test_app = FastAPI()
test_app.include_router(consensus_router, prefix="/api/consensus")


def _fake_session(task="Test task"):
    """Build a minimal ConsensusSession for test mocks."""
    r1 = ConsensusRound(round_number=1)
    r1.proposals = {"a1": "Proposal A"}
    r1.critiques = {"a1": "Critique A"}
    r1.refinements = {"a1": "Refined A"}
    r1.scores = {"a1": 0.85}
    r1.convergence_score = 0.92
    r1.polarity_balance = 0.55
    r1.completed = True
    return ConsensusSession(
        task=task,
        agents=[],
        rounds=[r1],
        current_round=1,
        status="completed",
        final_synthesis="This is the final synthesized response.",
        polarity_fusion_report={
            "masculine_forces": [],
            "feminine_forces": [],
            "unified_perspective": [],
            "polarity_balance_scores": [0.55],
            "rounds_completed": 1,
            "individuation_notes": "Test individuation notes.",
        },
    )


@pytest.fixture(autouse=True)
def _override_auth_and_db():
    """Replace FastAPI dependencies so routes don't need real auth/DB."""
    async def _mock_user():
        return MagicMock()

    async def _mock_db():
        return AsyncMock()

    test_app.dependency_overrides[require_user] = _mock_user
    test_app.dependency_overrides[get_db] = _mock_db

    yield

    test_app.dependency_overrides.clear()


# ===================================================================
# POST /api/consensus/run
# ===================================================================

class TestConsensusRunEndpoint:
    """Tests for the main consensus execution endpoint."""

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_success_default_agents(self, mock_run, _check):
        """Returns session data with correct structure."""
        fake = _fake_session()
        mock_run.return_value = fake

        resp = TestClient(test_app).post("/api/consensus/run", json={"task": "Test task"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == fake.id
        assert data["rounds_completed"] == 1
        assert data["synthesis"] == fake.final_synthesis
        assert data["status"] == "completed"
        assert "fusion_report" in data
        assert "round_details" in data

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_custom_params_forwarded(self, mock_run, _check):
        """max_rounds, min_rounds, threshold are forwarded to the integration."""
        fake = _fake_session()
        mock_run.return_value = fake

        TestClient(test_app).post("/api/consensus/run", json={
            "task": "Test",
            "max_rounds": 4,
            "min_rounds": 2,
            "threshold": 0.9,
        })
        _, kwargs = mock_run.call_args
        assert kwargs["max_rounds"] == 4
        assert kwargs["min_rounds"] == 2
        assert kwargs["convergence_threshold"] == 0.9

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_empty_task_returns_400(self, mock_run, _check):
        """Empty task string returns validation error."""
        resp = TestClient(test_app).post("/api/consensus/run", json={"task": ""})
        assert resp.status_code == 400
        assert "Task is required" in resp.text

    @patch("app.api.routes.consensus.check_usage_limit")
    def test_invalid_agent_ids_returns_400(self, _check):
        """When agent_ids don't match any registered agents."""
        resp = TestClient(test_app).post("/api/consensus/run", json={
            "task": "Test task",
            "agent_ids": ["nonexistent-id"],
        })
        assert resp.status_code == 400

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_ws_client_creates_on_event(self, mock_run, _check):
        """ws_client_id creates a non-None on_event callback."""
        mock_run.return_value = _fake_session()

        TestClient(test_app).post("/api/consensus/run", json={
            "task": "Test",
            "ws_client_id": "ws-123",
        })
        _, kwargs = mock_run.call_args
        assert kwargs["on_event"] is not None

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_no_ws_client_no_on_event(self, mock_run, _check):
        """Without ws_client_id, on_event is None."""
        mock_run.return_value = _fake_session()

        TestClient(test_app).post("/api/consensus/run", json={"task": "Test"})
        _, kwargs = mock_run.call_args
        assert kwargs["on_event"] is None

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_round_details_structure(self, mock_run, _check):
        """Round details contain all expected fields."""
        fake = _fake_session()
        mock_run.return_value = fake

        resp = TestClient(test_app).post("/api/consensus/run", json={"task": "Test"})
        details = resp.json()["round_details"]
        assert len(details) == 1
        rd = details[0]
        assert rd["round"] == 1
        assert "Proposal A" in rd["proposals"]
        assert "Critique A" in rd["critiques"]
        assert "Refined A" in rd["refinements"]
        assert rd["scores"]["a1"] == 0.85
        assert rd["convergence_score"] == 0.92

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_fusion_report_in_response(self, mock_run, _check):
        """Fusion report is included in the response."""
        fake = _fake_session()
        mock_run.return_value = fake

        resp = TestClient(test_app).post("/api/consensus/run", json={"task": "Test"})
        report = resp.json()["fusion_report"]
        assert report["rounds_completed"] == 1
        assert report["individuation_notes"] == "Test individuation notes."

    @patch("app.api.routes.consensus.check_usage_limit")
    @patch("app.api.routes.consensus.run_consensus_with_memory")
    def test_session_id_stable(self, mock_run, _check):
        """The returned session_id is stable (same as the ConsensusSession.id)."""
        fake = _fake_session()
        mock_run.return_value = fake

        resp = TestClient(test_app).post("/api/consensus/run", json={"task": "Test"})
        assert resp.json()["session_id"] == fake.id


# ===================================================================
# GET /api/consensus/sessions/{session_id}
# ===================================================================

class TestConsensusGetSessionEndpoint:
    """Tests for retrieving consensus sessions."""

    def test_get_existing_session(self):
        """Returns session data for an active in-memory session."""
        from app.api.routes.consensus import engine

        fake = _fake_session()
        engine.active_sessions[fake.id] = fake

        try:
            resp = TestClient(test_app).get(f"/api/consensus/sessions/{fake.id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["session_id"] == fake.id
            assert data["task"] == fake.task
            assert data["rounds_completed"] == 1
            assert data["synthesis"] == fake.final_synthesis
            assert data["status"] == "completed"
            assert "fusion_report" in data
        finally:
            del engine.active_sessions[fake.id]

    def test_get_nonexistent_session_returns_404(self):
        """Unknown session ID returns 404."""
        resp = TestClient(test_app).get("/api/consensus/sessions/nonexistent-id")
        assert resp.status_code == 404

    def test_get_session_with_multiple_rounds(self):
        """Session with multiple rounds is returned correctly."""
        from app.api.routes.consensus import engine

        r1 = ConsensusRound(round_number=1, scores={"a1": 0.7}, convergence_score=0.6, polarity_balance=0.5)
        r2 = ConsensusRound(round_number=2, scores={"a1": 0.9}, convergence_score=0.95, polarity_balance=0.55)
        session = ConsensusSession(
            task="Multi-round test",
            agents=[],
            rounds=[r1, r2],
            current_round=2,
            status="completed",
            final_synthesis="Multi-round synthesis",
            polarity_fusion_report={
                "rounds_completed": 2,
                "masculine_forces": [],
                "feminine_forces": [],
                "unified_perspective": [],
                "polarity_balance_scores": [0.5, 0.55],
                "individuation_notes": "",
            },
        )
        engine.active_sessions[session.id] = session

        try:
            resp = TestClient(test_app).get(f"/api/consensus/sessions/{session.id}")
            assert resp.status_code == 200
            assert resp.json()["rounds_completed"] == 2
            assert resp.json()["synthesis"] == "Multi-round synthesis"
        finally:
            del engine.active_sessions[session.id]

    def test_get_session_status_pending(self):
        """Pending session still retrievable."""
        from app.api.routes.consensus import engine

        session = ConsensusSession(task="Pending task", status="pending")
        engine.active_sessions[session.id] = session

        try:
            resp = TestClient(test_app).get(f"/api/consensus/sessions/{session.id}")
            assert resp.status_code == 200
            assert resp.json()["status"] == "pending"
            assert resp.json()["synthesis"] == ""
        finally:
            del engine.active_sessions[session.id]
