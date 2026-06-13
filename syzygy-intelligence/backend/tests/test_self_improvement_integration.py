"""Integration tests for the self-improvement workflow and API.

Tests exercise full flow with mocked LLM dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agents.base import SyzygyAgent
from app.agents.registry import agent_registry
from app.consensus.engine import ConsensusEngine, ConsensusSession
from app.self_improvement.assessment import AssessmentResult, SelfAssessmentEngine
from app.self_improvement.learning_optimizer import LearningOptimizer
from app.self_improvement.performance_tracker import PerformanceTracker
from app.workflows.self_improvement import (
    RecursiveSelfImprovementWorkflow,
    RecursiveImprovementSession,
)


# ═══════════════════════════════════════════════════════════
# Workflow integration tests
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def mock_consensus():
    engine = AsyncMock(spec=ConsensusEngine)
    session = ConsensusSession(task="test", agents=[])
    session.final_synthesis = "Improved output after consensus"
    engine.run_consensus.return_value = session
    return engine


@pytest.fixture
def mock_assessor():
    engine = AsyncMock(spec=SelfAssessmentEngine)
    # Return a decent assessment
    engine.assess.return_value = AssessmentResult(
        overall_score=0.75,
        dimension_scores={"accuracy": 0.8, "coherence": 0.7},
        strengths=["accuracy"],
        weaknesses=["coherence"],
        root_causes={"coherence": ["Poor structure"]},
        recommendations=["Improve paragraph transitions"],
    )
    return engine


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = '{"type": "prompt-tuning", "target_agent": "Sage", "action": "Add more structure", "rationale": "Improve coherence"}'
    return llm


@pytest.fixture
def workflow(mock_consensus, mock_assessor, mock_llm):
    wf = RecursiveSelfImprovementWorkflow(
        consensus_engine=mock_consensus,
        assessment_engine=mock_assessor,
        llm=mock_llm,
    )
    return wf


@pytest.fixture
def agents():
    return [
        SyzygyAgent.create("sage", name="Sage"),
        SyzygyAgent.create("hero", name="Hero"),
    ]


class TestWorkflowExecute:
    @pytest.mark.asyncio
    async def test_execute_returns_session(self, workflow, agents):
        session = await workflow.execute(
            task="Write a poem",
            agents=agents,
            domain="content",
            max_cycles=3,
        )
        assert isinstance(session, RecursiveImprovementSession)
        assert session.task == "Write a poem"
        assert session.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_runs_cycles(self, workflow, agents):
        session = await workflow.execute(
            task="Write code",
            agents=agents,
            max_cycles=3,
        )
        assert len(session.cycles) >= 1

    @pytest.mark.asyncio
    async def test_execute_calls_consensus_per_cycle(self, mock_consensus, workflow, agents):
        await workflow.execute(task="Test", agents=agents, max_cycles=2)
        assert mock_consensus.run_consensus.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_calls_assessor_per_cycle(self, mock_assessor, workflow, agents):
        await workflow.execute(task="Test", agents=agents, max_cycles=2)
        assert mock_assessor.assess.call_count >= 1

    @pytest.mark.asyncio
    async def test_converges_early_when_threshold_met(self, mock_assessor, workflow, agents):
        # Override assessor to return high scores immediately
        mock_assessor.assess.return_value = AssessmentResult(
            overall_score=0.95,
            dimension_scores={"accuracy": 0.95},
            strengths=[],
            weaknesses=[],
        )
        session = await workflow.execute(
            task="Test",
            agents=agents,
            max_cycles=5,
            convergence_threshold=0.9,
        )
        # Should converge quickly (likely cycle 1 since score >= 0.9 from cycle 2)
        assert len(session.cycles) <= 3

    @pytest.mark.asyncio
    async def test_final_output_set(self, workflow, agents):
        session = await workflow.execute(task="Test", agents=agents, max_cycles=2)
        assert session.final_output

    @pytest.mark.asyncio
    async def test_performance_gain_tracked(self, workflow, agents):
        session = await workflow.execute(task="Test", agents=agents, max_cycles=3)
        assert isinstance(session.total_performance_gain, float)


class TestWorkflowNoConvergence:
    @pytest.mark.asyncio
    async def test_executes_all_cycles_when_no_convergence(self, mock_assessor, workflow, agents):
        # Score stays below threshold
        mock_assessor.assess.return_value = AssessmentResult(
            overall_score=0.5,
            dimension_scores={"accuracy": 0.5},
            strengths=[],
            weaknesses=[],
        )
        session = await workflow.execute(
            task="Test",
            agents=agents,
            max_cycles=4,
            convergence_threshold=0.95,
        )
        assert len(session.cycles) == 4
        assert session.status == "completed"


# ═══════════════════════════════════════════════════════════
# API integration tests
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_client():
    """Build a minimal FastAPI test client with mocked workflow dependencies."""
    from unittest.mock import AsyncMock, patch

    from fastapi import FastAPI
    from app.api.routes.self_improvement import router

    app = FastAPI()
    app.include_router(router, prefix="/api")

    # Patch real dependencies that would hang without a running server
    patcher_consensus = patch("app.api.routes.self_improvement.ConsensusEngine")
    patcher_llm = patch("app.api.routes.self_improvement.OllamaClient")
    patcher_assessor = patch("app.api.routes.self_improvement.SelfAssessmentEngine")

    mock_consensus = patcher_consensus.start()
    mock_llm = patcher_llm.start()
    mock_assessor = patcher_assessor.start()

    # Wire mock returns so workflow.execute doesn't hang
    mock_consensus_instance = AsyncMock()
    mock_consensus_instance.run_consensus.side_effect = (
        lambda task, agents, max_rounds=2: AsyncMock(
            final_synthesis="Mocked output"
        )
    )
    mock_consensus.return_value = mock_consensus_instance

    mock_assessor_instance = AsyncMock()
    mock_assessor_instance.assess.return_value = AssessmentResult(
        overall_score=0.75,
        dimension_scores={"accuracy": 0.8},
        strengths=["accuracy"],
        weaknesses=[],
    )
    mock_assessor.return_value = mock_assessor_instance

    yield TestClient(app)

    patcher_consensus.stop()
    patcher_llm.stop()
    patcher_assessor.stop()


class TestSelfImprovementAPI:
    def test_start_session_returns_session_id(self, test_client):
        response = test_client.post(
            "/api/workflows/self_improvement/",
            json={
                "task": "Write a test",
                "domain": "general",
                "max_cycles": 2,
            },
        )
        assert response.status_code in (200, 202)
        body = response.json()
        assert "session_id" in body

    def test_start_session_invalid_domain(self, test_client):
        response = test_client.post(
            "/api/workflows/self_improvement/",
            json={
                "task": "Write code",
                "domain": "invalid_domain_xyz",
                "max_cycles": 1,
            },
        )
        # Should accept or gracefully handle unknown domains
        assert response.status_code in (200, 202, 400, 422)

    def test_start_session_missing_task(self, test_client):
        response = test_client.post(
            "/api/workflows/self_improvement/",
            json={"domain": "code", "max_cycles": 2},
        )
        assert response.status_code == 422  # validation error

    def test_start_session_invalid_max_cycles(self, test_client):
        response = test_client.post(
            "/api/workflows/self_improvement/",
            json={"task": "Test", "max_cycles": 20},
        )
        assert response.status_code == 422  # max is 10

    def test_get_nonexistent_session_returns_404(self, test_client):
        response = test_client.get("/api/workflows/self_improvement/nonexistent-id")
        assert response.status_code == 404

    def test_get_session_cycles_empty_for_nonexistent(self, test_client):
        response = test_client.get(
            "/api/workflows/self_improvement/nonexistent/cycles"
        )
        assert response.status_code == 404
