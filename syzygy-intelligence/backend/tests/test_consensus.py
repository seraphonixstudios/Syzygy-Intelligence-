"""Comprehensive unit tests for Syzygy Consensus Engine."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.agents.registry import AgentRegistry
from app.consensus.engine import ConsensusEngine, ConsensusRound, ConsensusSession
from app.consensus.phases import (
    CritiquePhase,
    EvaluationPhase,
    ProposalPhase,
    RefinementPhase,
)
from app.consensus.scoring import ConsensusScorer
from app.consensus.synthesis import SynthesisGenerator

# ===================================================================
# ConsensusRound
# ===================================================================

class TestConsensusRound:
    def test_round_creation_defaults(self):
        r = ConsensusRound(round_number=1)
        assert r.round_number == 1
        assert r.proposals == {}
        assert r.critiques == {}
        assert r.refinements == {}
        assert r.evaluations == {}
        assert r.scores == {}
        assert r.convergence_score == 0.0
        assert r.polarity_balance == 0.5
        assert r.synthesis == ""
        assert not r.completed

    def test_round_status(self):
        r = ConsensusRound(round_number=2)
        r.completed = True
        assert r.completed

    def test_round_with_all_fields(self):
        r = ConsensusRound(
            round_number=3,
            proposals={"a1": "proposal"},
            critiques={"a2": "critique"},
            refinements={"a1": "refined"},
            evaluations={"a1": {"accuracy": 0.9, "overall": 0.85}},
            scores={"a1": 0.85},
            convergence_score=0.92,
            polarity_balance=0.65,
            synthesis="Final synthesis text",
            completed=True,
        )
        assert r.round_number == 3
        assert r.proposals["a1"] == "proposal"
        assert r.critiques["a2"] == "critique"
        assert r.refinements["a1"] == "refined"
        assert r.evaluations["a1"]["accuracy"] == 0.9
        assert r.scores["a1"] == 0.85
        assert r.convergence_score == 0.92
        assert r.polarity_balance == 0.65
        assert r.synthesis == "Final synthesis text"
        assert r.completed


# ===================================================================
# ConsensusSession
# ===================================================================

class TestConsensusSession:
    def test_session_creation_defaults(self):
        s = ConsensusSession(task="Test task")
        assert s.task == "Test task"
        assert s.current_round == 0
        assert s.max_rounds == 6
        assert s.min_rounds == 2
        assert s.convergence_threshold == 0.85
        assert s.variance_threshold == 0.1
        assert s.status == "pending"
        assert s.completed_at is None
        assert s.final_synthesis == ""
        assert s.polarity_fusion_report == {}
        assert s.rounds == []
        assert isinstance(s.id, str) and len(s.id) > 0

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

    def test_session_status_transitions(self):
        s = ConsensusSession(task="Test")
        assert s.status == "pending"
        s.status = "running"
        assert s.status == "running"
        s.status = "completed"
        assert s.status == "completed"

    def test_session_unique_ids(self):
        s1 = ConsensusSession(task="Task 1")
        s2 = ConsensusSession(task="Task 2")
        assert s1.id != s2.id

    def test_session_rounds_list(self):
        s = ConsensusSession(task="Test")
        s.rounds.append(ConsensusRound(round_number=1))
        s.rounds.append(ConsensusRound(round_number=2))
        assert len(s.rounds) == 2
        assert s.rounds[0].round_number == 1
        assert s.rounds[1].round_number == 2


# ===================================================================
# ConsensusScorer
# ===================================================================

class TestConsensusScorer:
    def test_scorer_dimensions(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        assert len(scorer.SCORE_DIMENSIONS) == 5
        assert "accuracy" in scorer.SCORE_DIMENSIONS
        assert "creativity" in scorer.SCORE_DIMENSIONS

    def test_scorer_weights_sum_to_one(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        total = sum(scorer.DIMENSION_WEIGHTS.values())
        assert total == pytest.approx(1.0)

    def test_output_dimensions_must_not_be_empty(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        assert len(scorer.SCORE_DIMENSIONS) > 0

    # -- compute_weighted --

    def test_compute_weighted_all_max(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        scores = {
            "accuracy": 1.0, "holistic_insight": 1.0, "creativity": 1.0,
            "feasibility": 1.0, "polarity_balance": 1.0,
        }
        assert scorer._compute_weighted(scores) == 1.0

    def test_compute_weighted_all_half(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        scores = {
            "accuracy": 0.5, "holistic_insight": 0.5, "creativity": 0.5,
            "feasibility": 0.5, "polarity_balance": 0.5,
        }
        assert scorer._compute_weighted(scores) == 0.5

    def test_compute_weighted_custom_weights(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        scores = {
            "accuracy": 1.0, "holistic_insight": 0.0, "creativity": 0.0,
            "feasibility": 0.0, "polarity_balance": 0.0,
        }
        assert scorer._compute_weighted(scores) == 0.25

    def test_compute_weighted_partial_input(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        scores = {"accuracy": 0.8}
        assert scorer._compute_weighted(scores) == pytest.approx(0.8 * 0.25 + 0.5 * 0.75)

    # -- _parse_scores --

    def test_parse_scores_valid_json(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = (
            '{"accuracy": 0.9, "holistic_insight": 0.8, "creativity": 0.7, '
            '"feasibility": 0.6, "polarity_balance": 0.5}'
        )
        result = scorer._parse_scores(text)
        assert result is not None
        assert result["accuracy"] == 0.9
        assert result["holistic_insight"] == 0.8
        assert result["creativity"] == 0.7
        assert result["feasibility"] == 0.6
        assert result["polarity_balance"] == 0.5

    def test_parse_scores_json_with_surrounding_text(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = (
            "Here are my scores: "
            '{"accuracy": 0.85, "holistic_insight": 0.72, "creativity": 0.68, '
            '"feasibility": 0.79, "polarity_balance": 0.74}'
            " Hope this helps!"
        )
        result = scorer._parse_scores(text)
        assert result is not None
        assert result["accuracy"] == 0.85

    def test_parse_scores_no_json(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = "I think this proposal is well-reasoned and comprehensive."
        result = scorer._parse_scores(text)
        assert result is None

    def test_parse_scores_clamps_out_of_bounds(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = (
            '{"accuracy": 2.5, "holistic_insight": -0.5, "creativity": 0.7, '
            '"feasibility": 0.6, "polarity_balance": 0.5}'
        )
        result = scorer._parse_scores(text)
        assert result["accuracy"] == 1.0
        assert result["holistic_insight"] == 0.0
        assert result["creativity"] == 0.7

    def test_parse_scores_partial_json(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = '{"accuracy": 0.9}'
        result = scorer._parse_scores(text)
        assert result is not None
        assert result["accuracy"] == 0.9
        assert result["holistic_insight"] == 0.5

    def test_parse_scores_invalid_json_syntax(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = '{"accuracy": broken}'
        result = scorer._parse_scores(text)
        assert result is None

    def test_parse_scores_empty_string(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        result = scorer._parse_scores("")
        assert result is None

    # -- _parse_fallback --

    def test_parse_fallback_valid_comma_separated(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = "0.9, 0.8, 0.7, 0.6, 0.5"
        result = scorer._parse_fallback(text)
        assert result["accuracy"] == 0.9
        assert result["holistic_insight"] == 0.8
        assert result["creativity"] == 0.7
        assert result["feasibility"] == 0.6
        assert result["polarity_balance"] == 0.5

    def test_parse_fallback_fewer_than_five(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = "0.9, 0.8"
        result = scorer._parse_fallback(text)
        assert result["accuracy"] == 0.9
        assert result["holistic_insight"] == 0.8
        assert result["creativity"] == 0.5

    def test_parse_fallback_empty(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        result = scorer._parse_fallback("")
        assert all(v == 0.5 for v in result.values())

    def test_parse_fallback_nonsense_text(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = "I cannot provide numerical scores for this proposal"
        result = scorer._parse_fallback(text)
        assert all(v == 0.5 for v in result.values())

    def test_parse_fallback_clamps_high_values(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        text = "2.0, 0.5, 0.5, 0.5, 0.5"
        result = scorer._parse_fallback(text)
        assert result["accuracy"] == 1.0

    # -- evaluate_all --

    async def test_evaluate_all_empty_contents(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        result = await scorer.evaluate_all("task", {}, [], AsyncMock())
        assert result == {}

    async def test_evaluate_all_skips_missing_agents(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        contents = {"nonexistent_id": "some content"}
        result = await scorer.evaluate_all("task", contents, [], AsyncMock())
        assert result == {}

    async def test_evaluate_all_with_real_agent(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = (
            '{"accuracy": 0.8, "holistic_insight": 0.7, "creativity": 0.6, '
            '"feasibility": 0.7, "polarity_balance": 0.8}'
        )
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await scorer.evaluate_all(
            "task", {agent.id: "content"}, [agent], mock_llm
        )
        assert agent.id in result
        assert result[agent.id]["accuracy"] == 0.8
        expected_overall = 0.25 * 0.8 + 0.20 * 0.7 + 0.20 * 0.6 + 0.20 * 0.7 + 0.15 * 0.8
        assert result[agent.id]["overall"] == pytest.approx(expected_overall)

    async def test_evaluate_all_llm_error_fallback(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = Exception("LLM unavailable")
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await scorer.evaluate_all(
            "task", {agent.id: "content"}, [agent], mock_llm
        )
        assert agent.id in result
        assert result[agent.id]["overall"] == 0.5
        for dim in scorer.SCORE_DIMENSIONS:
            assert result[agent.id][dim] == 0.5

    async def test_evaluate_all_retry_on_parse_failure(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = [
            "I think this proposal is good but I cannot give scores",
            "0.9, 0.8, 0.7, 0.6, 0.5",
        ]
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await scorer.evaluate_all(
            "task", {agent.id: "content"}, [agent], mock_llm
        )
        assert agent.id in result
        assert result[agent.id]["accuracy"] == 0.9
        assert result[agent.id]["polarity_balance"] == 0.5

    async def test_evaluate_all_fallback_also_fails(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Nonsense response with no numbers"
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await scorer.evaluate_all(
            "task", {agent.id: "content"}, [agent], mock_llm
        )
        assert agent.id in result
        assert result[agent.id]["overall"] == 0.5

    async def test_evaluate_all_multiple_agents(self):
        scorer = ConsensusScorer(llm=AsyncMock())
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = (
            '{"accuracy": 0.8, "holistic_insight": 0.7, "creativity": 0.6, '
            '"feasibility": 0.7, "polarity_balance": 0.8}'
        )
        registry = AgentRegistry()
        a1 = registry.create_agent("sage")
        a2 = registry.create_agent("hero")
        result = await scorer.evaluate_all(
            "task", {a1.id: "c1", a2.id: "c2"}, [a1, a2], mock_llm
        )
        assert len(result) == 2
        assert a1.id in result
        assert a2.id in result


# ===================================================================
# ConsensusEngine
# ===================================================================

class TestConsensusEngine:
    def test_engine_initialization(self):
        engine = ConsensusEngine()
        assert engine.active_sessions == {}
        assert engine._timeout == 0

    def test_engine_initialization_with_custom_llm(self):
        mock_llm = AsyncMock()
        engine = ConsensusEngine(llm_client=mock_llm)
        assert engine.llm is mock_llm

    # -- _call_llm --

    async def test_call_llm_no_timeout(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "response"
        engine = ConsensusEngine(llm_client=mock_llm)
        result = await engine._call_llm("prompt", system="system")
        assert result == "response"
        mock_llm.generate.assert_called_once_with("prompt", system="system")

    async def test_call_llm_with_timeout_success(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "response"
        engine = ConsensusEngine(llm_client=mock_llm)
        engine._timeout = 30.0
        result = await engine._call_llm("prompt")
        assert result == "response"

    async def test_call_llm_timeout_expired(self):
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = asyncio.TimeoutError
        engine = ConsensusEngine(llm_client=mock_llm)
        engine._timeout = 0.001
        with pytest.raises(asyncio.TimeoutError):
            await engine._call_llm("prompt")

    # -- _agent_propose --

    async def test_agent_propose(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Proposal content"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await engine._agent_propose(agent, "Test task", "context")
        assert result == "Proposal content"

    async def test_agent_propose_includes_strengths_in_prompt(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "response"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        await engine._agent_propose(agent, "Test task", "context")
        call_kwargs = mock_llm.generate.call_args
        prompt = call_kwargs[0][0]
        assert "sage" in prompt.lower()
        assert "Test task" in prompt

    # -- _agent_critique --

    async def test_agent_critique(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Critique content"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await engine._agent_critique(
            agent, "Test task", {"other_id": "proposal text"}
        )
        assert result == "Critique content"

    async def test_agent_critique_with_shadow(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Shadow critique"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        agent.activate_shadow()
        result = await engine._agent_critique(
            agent, "Test task", {"other_id": "proposal text"}
        )
        assert result == "Shadow critique"

    async def test_agent_critique_empty_targets(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Critique"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await engine._agent_critique(agent, "Test task", {})
        assert result == "Critique"

    # -- _agent_refine --

    async def test_agent_refine(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Refined content"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await engine._agent_refine(
            agent, "Test task", "original", {"critic": "critique text"}
        )
        assert result == "Refined content"

    async def test_agent_refine_no_critiques(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Refined content"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await engine._agent_refine(agent, "Test task", "original", {})
        assert result == "Refined content"

    # -- _proposal_phase --

    async def test_proposal_phase_creates_proposals(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Proposal from agent"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        sage = registry.create_agent("sage")
        hero = registry.create_agent("hero")
        session = ConsensusSession(task="Test task", agents=[sage, hero])
        round_data = ConsensusRound(round_number=1)
        session.rounds.append(round_data)
        await engine._proposal_phase(session, round_data)
        assert sage.id in round_data.proposals
        assert hero.id in round_data.proposals
        assert "Proposal from agent" in round_data.proposals[sage.id]

    async def test_proposal_phase_error_handling(self):
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = Exception("API error")
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        round_data = ConsensusRound(round_number=1)
        session.rounds.append(round_data)
        await engine._proposal_phase(session, round_data)
        assert "Error generating proposal" in round_data.proposals[agent.id]

    # -- _critique_phase --

    async def test_critique_phase_creates_critiques(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Critique from agent"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        sage = registry.create_agent("sage")
        hero = registry.create_agent("great_mother")
        session = ConsensusSession(task="Test", agents=[sage, hero])
        round_data = ConsensusRound(
            round_number=1,
            proposals={sage.id: "proposal1", hero.id: "proposal2"},
        )
        session.rounds.append(round_data)
        await engine._critique_phase(session, round_data)
        assert sage.id in round_data.critiques
        assert hero.id in round_data.critiques

    async def test_critique_phase_error_handling(self):
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = Exception("API error")
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        other = registry.create_agent("great_mother")
        session = ConsensusSession(task="Test", agents=[agent, other])
        round_data = ConsensusRound(
            round_number=1,
            proposals={agent.id: "prop", other.id: "prop2"},
        )
        session.rounds.append(round_data)
        await engine._critique_phase(session, round_data)
        assert "Error during critique" in round_data.critiques[agent.id]

    async def test_critique_phase_shadow_deactivated(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "critique"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        other = registry.create_agent("great_mother")
        session = ConsensusSession(task="Test", agents=[agent, other])
        round_data = ConsensusRound(
            round_number=1,
            proposals={agent.id: "prop", other.id: "prop2"},
        )
        session.rounds.append(round_data)
        await engine._critique_phase(session, round_data)
        assert not agent.shadow_active
        assert not other.shadow_active

    # -- _refinement_phase --

    async def test_refinement_phase_creates_refinements(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Refined"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        sage = registry.create_agent("sage")
        hero = registry.create_agent("great_mother")
        session = ConsensusSession(task="Test", agents=[sage, hero])
        round_data = ConsensusRound(
            round_number=1,
            proposals={sage.id: "prop", hero.id: "prop2"},
            critiques={"critic": "critique"},
        )
        session.rounds.append(round_data)
        await engine._refinement_phase(session, round_data)
        assert sage.id in round_data.refinements
        assert hero.id in round_data.refinements

    async def test_refinement_phase_fallback_on_error(self):
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = Exception("API error")
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        round_data = ConsensusRound(
            round_number=1,
            proposals={agent.id: "original proposal"},
            critiques={"other": "critique"},
        )
        session.rounds.append(round_data)
        await engine._refinement_phase(session, round_data)
        assert round_data.refinements[agent.id] == "original proposal"

    # -- _evaluation_phase --

    async def test_evaluation_phase_uses_refinements_over_proposals(self):
        mock_scorer = AsyncMock()
        mock_scorer.evaluate_all.return_value = {
            "a1": {"accuracy": 0.8, "overall": 0.8},
        }
        engine = ConsensusEngine(llm_client=AsyncMock())
        engine.scorer = mock_scorer
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        round_data = ConsensusRound(
            round_number=1,
            proposals={agent.id: "proposal"},
            refinements={agent.id: "refinement"},
        )
        await engine._evaluation_phase(session, round_data)
        args = mock_scorer.evaluate_all.call_args[0]
        assert args[1][agent.id] == "refinement"

    async def test_evaluation_phase_falls_back_to_proposals(self):
        mock_scorer = AsyncMock()
        mock_scorer.evaluate_all.return_value = {
            "a1": {"accuracy": 0.8, "overall": 0.8},
        }
        engine = ConsensusEngine(llm_client=AsyncMock())
        engine.scorer = mock_scorer
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        round_data = ConsensusRound(
            round_number=1,
            proposals={agent.id: "proposal"},
        )
        await engine._evaluation_phase(session, round_data)
        args = mock_scorer.evaluate_all.call_args[0]
        assert args[1][agent.id] == "proposal"

    # -- _convergence_check --

    async def test_convergence_check_fewer_than_two_scores(self):
        engine = ConsensusEngine()
        session = ConsensusSession(task="Test")
        round_data = ConsensusRound(round_number=1)
        assert not await engine._convergence_check(session, round_data)

    async def test_convergence_check_no_scores(self):
        engine = ConsensusEngine()
        session = ConsensusSession(task="Test")
        round_data = ConsensusRound(round_number=1)
        round_data.scores = {}
        assert not await engine._convergence_check(session, round_data)

    async def test_convergence_check_identical_scores(self):
        engine = ConsensusEngine()
        session = ConsensusSession(task="Test")
        round_data = ConsensusRound(round_number=1)
        round_data.scores = {"a1": 0.8, "a2": 0.8}
        assert await engine._convergence_check(session, round_data)

    async def test_convergence_check_variance_threshold(self):
        engine = ConsensusEngine()
        session = ConsensusSession(task="Test", variance_threshold=0.5)
        round_data = ConsensusRound(round_number=1)
        round_data.scores = {"a1": 0.5, "a2": 0.55}
        result = await engine._convergence_check(session, round_data)
        assert result

    # -- _generate_fusion_report --

    def test_generate_fusion_report(self):
        registry = AgentRegistry()
        agents = [
            registry.create_agent("hero"),
            registry.create_agent("great_mother"),
            registry.create_agent("self"),
        ]
        session = ConsensusSession(task="Test", agents=agents)
        engine = ConsensusEngine()
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
        assert "individuation_notes" in report

    def test_generate_fusion_report_all_masculine(self):
        registry = AgentRegistry()
        agents = [registry.create_agent("hero"), registry.create_agent("sage")]
        session = ConsensusSession(task="Test", agents=agents)
        session.current_round = 2
        engine = ConsensusEngine()
        report = engine._generate_fusion_report(session)
        assert len(report["masculine_forces"]) == 2
        assert report["feminine_forces"] == []
        assert report["unified_perspective"] == []

    def test_generate_fusion_report_all_unified(self):
        registry = AgentRegistry()
        agents = [registry.create_agent("self"), registry.create_agent("hermes")]
        session = ConsensusSession(task="Test", agents=agents)
        session.current_round = 2
        engine = ConsensusEngine()
        report = engine._generate_fusion_report(session)
        assert report["masculine_forces"] == []
        assert report["feminine_forces"] == []
        assert "Hermes" in report["unified_perspective"]

    def test_generate_fusion_report_no_agents(self):
        session = ConsensusSession(task="Test", agents=[])
        session.current_round = 1
        engine = ConsensusEngine()
        report = engine._generate_fusion_report(session)
        assert report["masculine_forces"] == []
        assert report["feminine_forces"] == []
        assert report["unified_perspective"] == []

    def test_generate_fusion_report_polarity_balance_scores(self):
        registry = AgentRegistry()
        agents = [registry.create_agent("sage"), registry.create_agent("great_mother")]
        session = ConsensusSession(task="Test", agents=agents)
        engine = ConsensusEngine()
        for i in range(2):
            r = ConsensusRound(round_number=i + 1, polarity_balance=0.5 + i * 0.1)
            session.rounds.append(r)
        session.current_round = 2
        report = engine._generate_fusion_report(session)
        assert len(report["polarity_balance_scores"]) == 2

    # -- _build_proposal_context --

    def test_build_proposal_context_first_round(self):
        engine = ConsensusEngine()
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        round_data = ConsensusRound(round_number=1)
        session.rounds.append(round_data)
        context = engine._build_proposal_context(session, round_data, agent)
        assert "first round" in context.lower()

    def test_build_proposal_context_subsequent_round(self):
        engine = ConsensusEngine()
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        r1 = ConsensusRound(round_number=1)
        r1.critiques[agent.id] = "Good proposal but missing details"
        session.rounds.append(r1)
        r2 = ConsensusRound(round_number=2)
        session.rounds.append(r2)
        context = engine._build_proposal_context(session, r2, agent)
        assert "Previous round context" in context
        assert "missing details" in context

    def test_build_proposal_context_with_synthesis(self):
        engine = ConsensusEngine()
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        r1 = ConsensusRound(
            round_number=1, synthesis="Round 1 synthesis output"
        )
        session.rounds.append(r1)
        r2 = ConsensusRound(round_number=2)
        session.rounds.append(r2)
        context = engine._build_proposal_context(session, r2, agent)
        assert "Round 1 synthesis output" in context

    def test_build_proposal_context_no_previous_critique(self):
        engine = ConsensusEngine()
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        session = ConsensusSession(task="Test", agents=[agent])
        r1 = ConsensusRound(round_number=1)
        session.rounds.append(r1)
        r2 = ConsensusRound(round_number=2)
        session.rounds.append(r2)
        context = engine._build_proposal_context(session, r2, agent)
        assert "Previous round context" in context
        assert "critique" not in context.lower()

    # -- run_consensus integration --

    async def test_run_consensus_with_on_event(self):
        registry = AgentRegistry()
        agents = [
            registry.create_agent("sage"),
            registry.create_agent("great_mother"),
        ]
        engine = ConsensusEngine(llm_client=AsyncMock())
        engine.llm.generate.return_value = "mock response"
        engine.scorer = ConsensusScorer(llm=AsyncMock())
        engine.scorer._evaluate_single = AsyncMock(return_value={
            "accuracy": 0.8, "holistic_insight": 0.7, "creativity": 0.6,
            "feasibility": 0.7, "polarity_balance": 0.8,
        })
        events = []

        async def on_event(event_type, data):
            events.append((event_type, data))

        result = await engine.run_consensus(
            "Test task",
            agents=agents,
            max_rounds=2,
            min_rounds=1,
            on_event=on_event,
        )
        assert result.status == "completed"
        assert result.completed_at is not None
        event_types = {e[0] for e in events}
        assert "proposal" in event_types
        assert "synthesis" in event_types

    async def test_run_consensus_single_agent(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        engine = ConsensusEngine(llm_client=AsyncMock())
        engine.llm.generate.return_value = "mock response"
        engine.scorer = ConsensusScorer(llm=AsyncMock())
        engine.scorer._evaluate_single = AsyncMock(return_value={
            "accuracy": 0.8, "holistic_insight": 0.7, "creativity": 0.6,
            "feasibility": 0.7, "polarity_balance": 0.8,
        })
        result = await engine.run_consensus(
            "Test task", agents=[agent], max_rounds=1, min_rounds=1
        )
        assert result.status == "completed"
        assert len(result.rounds) == 1

    async def test_run_consensus_timeout_propagated(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "response"
        engine = ConsensusEngine(llm_client=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        engine.scorer = ConsensusScorer(llm=AsyncMock())
        engine.scorer._evaluate_single = AsyncMock(return_value={
            "accuracy": 0.8, "holistic_insight": 0.7, "creativity": 0.6,
            "feasibility": 0.7, "polarity_balance": 0.8,
        })
        result = await engine.run_consensus(
            "Test task", agents=[agent], max_rounds=1, min_rounds=1, timeout=10.0
        )
        assert result.status == "completed"
        assert engine._timeout == 10.0

    async def test_run_consensus_session_tracked(self):
        engine = ConsensusEngine(llm_client=AsyncMock())
        engine.llm.generate.return_value = "response"
        engine.scorer = ConsensusScorer(llm=AsyncMock())
        engine.scorer._evaluate_single = AsyncMock(return_value={
            "accuracy": 0.8, "holistic_insight": 0.7, "creativity": 0.6,
            "feasibility": 0.7, "polarity_balance": 0.8,
        })
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        result = await engine.run_consensus(
            "Test task", agents=[agent], max_rounds=1, min_rounds=1
        )
        assert result.id in engine.active_sessions


# ===================================================================
# SynthesisGenerator
# ===================================================================

class TestSynthesisGenerator:
    def test_build_synthesis_prompt_basic(self):
        registry = AgentRegistry()
        agent = registry.create_agent("self", name="Rebis")
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test task",
            proposals={agent.id: "Proposal content"},
            critiques={},
            refinements={},
            evaluations={},
            agents=[agent],
        )
        assert "Test task" in prompt
        assert "Proposal content" in prompt

    def test_build_synthesis_prompt_with_critiques(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage", name="Sage")
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test",
            proposals={agent.id: "Proposal"},
            critiques={agent.id: "Critique text"},
            refinements={},
            evaluations={},
            agents=[agent],
        )
        assert "Critique text" in prompt

    def test_build_synthesis_prompt_without_critiques(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage", name="Sage")
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test",
            proposals={agent.id: "Proposal"},
            critiques={},
            refinements={},
            evaluations={},
            agents=[agent],
        )
        assert "# Critiques" not in prompt

    def test_build_synthesis_prompt_with_refinements(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage", name="Sage")
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test",
            proposals={agent.id: "Proposal"},
            critiques={},
            refinements={agent.id: "Refined text"},
            evaluations={},
            agents=[agent],
        )
        assert "Refined text" in prompt

    def test_build_synthesis_prompt_refinement_same_as_proposal_omitted(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage", name="Sage")
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test",
            proposals={agent.id: "Same text"},
            critiques={},
            refinements={agent.id: "Same text"},
            evaluations={},
            agents=[agent],
        )
        assert "Sage refined" not in prompt

    def test_build_synthesis_prompt_with_evaluations(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage", name="Sage")
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test",
            proposals={agent.id: "Proposal"},
            critiques={},
            refinements={},
            evaluations={agent.id: {"accuracy": 0.8, "overall": 0.8}},
            agents=[agent],
        )
        assert "Evaluation Scores" in prompt
        assert "accuracy: 0.80" in prompt

    def test_build_synthesis_prompt_empty_proposals(self):
        generator = SynthesisGenerator(llm=AsyncMock())
        prompt = generator._build_synthesis_prompt(
            task="Test task",
            proposals={},
            critiques={},
            refinements={},
            evaluations={},
            agents=[],
        )
        assert "Test task" in prompt
        assert "# Proposals" in prompt

    async def test_generate_synthesis_calls_llm(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Synthesis output"
        generator = SynthesisGenerator(llm=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("self", name="Rebis")
        result = await generator.generate_synthesis(
            task="Test task",
            proposals={agent.id: "Proposal"},
            critiques={},
            refinements={},
            evaluations={},
            agents=[agent],
        )
        assert result == "Synthesis output"
        mock_llm.generate.assert_called_once()

    async def test_generate_synthesis_with_timeout(self):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Synthesis with timeout"
        generator = SynthesisGenerator(llm=mock_llm)
        registry = AgentRegistry()
        agent = registry.create_agent("self", name="Rebis")
        result = await generator.generate_synthesis(
            task="Test",
            proposals={agent.id: "Proposal"},
            critiques={},
            refinements={},
            evaluations={},
            agents=[agent],
            timeout=5.0,
        )
        assert result == "Synthesis with timeout"


# ===================================================================
# Phase prompt builders
# ===================================================================

class TestProposalPhase:
    def test_build_prompt_basic(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = ProposalPhase.build_prompt("Test task", agent)
        assert "Test task" in prompt
        assert "sage" in prompt.lower()

    def test_build_prompt_with_context(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = ProposalPhase.build_prompt("Task", agent, context="Previous round data")
        assert "Previous round data" in prompt

    def test_build_prompt_empty_task(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = ProposalPhase.build_prompt("", agent)
        assert prompt is not None and len(prompt) > 0

    def test_build_prompt_includes_strengths(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = ProposalPhase.build_prompt("Task", agent)
        strengths = agent.archetype.strengths
        for s in strengths:
            assert s in prompt


class TestCritiquePhase:
    def test_build_prompt_basic(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = CritiquePhase.build_prompt(
            "Test task", agent, {"other": "Some proposal"}
        )
        assert "Test task" in prompt
        assert "Some proposal" in prompt

    def test_build_prompt_with_shadow(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = CritiquePhase.build_prompt(
            "Task", agent, {"other": "Proposal"}, shadow_instruction="Trickster"
        )
        assert "Trickster" in prompt
        assert "shadow" in prompt.lower()

    def test_build_prompt_empty_targets(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = CritiquePhase.build_prompt("Task", agent, {})
        assert "Task" in prompt

    def test_build_prompt_truncates_long_proposals(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        long_proposal = "A" * 2000
        prompt = CritiquePhase.build_prompt(
            "Task", agent, {"other": long_proposal}
        )
        assert "A" * 800 in prompt
        assert "A" * 801 not in prompt


class TestRefinementPhase:
    def test_build_prompt_basic(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = RefinementPhase.build_prompt(
            "Task", agent, "My proposal", {"critic": "Great work"}
        )
        assert "My proposal" in prompt
        assert "Great work" in prompt

    def test_build_prompt_no_critiques(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = RefinementPhase.build_prompt("Task", agent, "Proposal", {})
        assert "Proposal" in prompt

    def test_build_prompt_truncates_own_proposal(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        long_proposal = "B" * 2000
        prompt = RefinementPhase.build_prompt("Task", agent, long_proposal, {})
        assert "B" * 1000 in prompt
        assert "B" * 1001 not in prompt


class TestEvaluationPhase:
    def test_build_evaluation_prompt_basic(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = EvaluationPhase.build_evaluation_prompt("Task", "Content", agent)
        assert "Task" in prompt
        assert "Content" in prompt

    def test_build_evaluation_prompt_empty_content(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        prompt = EvaluationPhase.build_evaluation_prompt("Task", "", agent)
        assert prompt is not None
