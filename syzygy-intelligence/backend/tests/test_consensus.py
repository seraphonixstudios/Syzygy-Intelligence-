"""Unit tests for Syzygy Consensus Engine."""

import pytest

from app.agents.registry import AgentRegistry
from app.consensus.engine import ConsensusEngine, ConsensusRound, ConsensusSession
from app.consensus.scoring import ConsensusScorer
from app.consensus.synthesis import SynthesisGenerator


class TestConsensusRound:
    def test_round_creation(self):
        r = ConsensusRound(round_number=1)
        assert r.round_number == 1
        assert r.proposals == {}
        assert r.critiques == {}
        assert not r.completed

    def test_round_status(self):
        r = ConsensusRound(round_number=2)
        r.completed = True
        assert r.completed


class TestConsensusSession:
    def test_session_creation(self):
        s = ConsensusSession(task="Test task")
        assert s.task == "Test task"
        assert s.current_round == 0
        assert s.max_rounds == 6
        assert s.status == "pending"

    def test_session_with_agents(self):
        registry = AgentRegistry()
        agents = [registry.create_agent("sage"), registry.create_agent("great_mother")]
        s = ConsensusSession(task="Test", agents=agents)
        assert len(s.agents) == 2

    def test_session_custom_config(self):
        s = ConsensusSession(
            task="Test",
            max_rounds=4,
            min_rounds=2,
            convergence_threshold=0.9,
        )
        assert s.max_rounds == 4
        assert s.convergence_threshold == 0.9


class TestConsensusScorer:
    def test_scorer_dimensions(self):
        scorer = ConsensusScorer()
        assert len(scorer.SCORE_DIMENSIONS) == 5
        assert "accuracy" in scorer.SCORE_DIMENSIONS
        assert "creativity" in scorer.SCORE_DIMENSIONS

    def test_scorer_weights_sum_to_one(self):
        scorer = ConsensusScorer()
        total = sum(scorer.DIMENSION_WEIGHTS.values())
        assert total == pytest.approx(1.0)

    def test_compute_weighted(self):
        scorer = ConsensusScorer()
        scores = {"accuracy": 1.0, "holistic_insight": 1.0, "creativity": 1.0,
                  "feasibility": 1.0, "polarity_balance": 1.0}
        assert scorer._compute_weighted(scores) == 1.0

    def test_compute_weighted_partial(self):
        scorer = ConsensusScorer()
        scores = {"accuracy": 0.5, "holistic_insight": 0.5, "creativity": 0.5,
                  "feasibility": 0.5, "polarity_balance": 0.5}
        assert scorer._compute_weighted(scores) == 0.5

    def test_output_dimensions_must_not_be_empty(self):
        scorer = ConsensusScorer()
        assert len(scorer.SCORE_DIMENSIONS) > 0


class TestConsensusEngine:
    def test_engine_initialization(self):
        engine = ConsensusEngine()
        assert engine.active_sessions == {}

    def test_generate_fusion_report(self):
        registry = AgentRegistry()
        agents = [
            registry.create_agent("hero"),
            registry.create_agent("great_mother"),
            registry.create_agent("self"),
        ]
        session = ConsensusSession(task="Test", agents=agents)
        engine = ConsensusEngine()

        # Simulate rounds
        for i in range(3):
            r = ConsensusRound(round_number=i + 1)
            r.polarity_balance = 0.5 + (i * 0.1)
            r.scores = {a.id: 0.7 + (i * 0.05) for a in agents}
            session.rounds.append(r)
            session.current_round = i + 1

        report = engine._generate_fusion_report(session)
        assert "masculine_forces" in report
        assert "feminine_forces" in report
        assert "unified_perspective" in report
        assert "rounds_completed" in report
        assert report["rounds_completed"] == 3


class TestSynthesisGenerator:
    def test_build_synthesis_prompt(self):
        registry = AgentRegistry()
        agent = registry.create_agent("self", name="Rebis")
        generator = SynthesisGenerator()
        prompt = generator._build_synthesis_prompt(
            task="Test task",
            proposals={agent.id: "Proposal content"},
            critiques={},
            refinements={},
            evaluations={},
            agents=[agent],
        )
        assert "Test task" in prompt
        assert "Proposal content" in prompt or "Proposal" in prompt
