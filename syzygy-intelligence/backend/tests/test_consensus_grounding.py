"""Grounding tests for the consensus engine + shared truncate helper.

Proves critique faces the whole team (no arbitrary two-opponent cap),
scoring provenance is honest, and truncation marks what it drops.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.base import SyzygyAgent
from app.consensus.engine import ConsensusEngine, ConsensusRound, ConsensusSession
from app.consensus.scoring import ConsensusScorer
from app.text_utils import TRUNCATION_MARKER, truncate


class TestTruncate:
    def test_short_passthrough(self):
        assert truncate("small text", 100) == "small text"

    def test_marks_cut(self):
        out = truncate("word " * 1000, 200)
        assert out.endswith(TRUNCATION_MARKER)
        assert len(out) <= 200 + len(TRUNCATION_MARKER)

    def test_sentence_boundary(self):
        out = truncate("First sentence here. Second sentence is longer and keeps going.", 45)
        assert out.startswith("First sentence here")
        assert out.endswith(TRUNCATION_MARKER)

    def test_empty_and_tiny_limits(self):
        assert truncate("abc", 0) == ""
        assert truncate("abc", 1) == TRUNCATION_MARKER
        assert truncate("", 10) == ""
        assert truncate(42, 10) == 42


def _agent(key: str, agent_id: str):
    return SyzygyAgent(id=agent_id, archetype_key=key)


class TestCritiqueFacesWholeTeam:
    @pytest.mark.asyncio
    async def test_all_opponents_critiqued(self):
        engine = ConsensusEngine()
        seen = {}

        async def fake_critique(agent, task, target_proposals, previous_critiques=None):
            seen[agent.id] = list(target_proposals)
            return "critique"

        engine._agent_critique = fake_critique  # type: ignore
        agents = [
            _agent("sage", "a1"),
            _agent("lover", "a2"),
            _agent("self", "a3"),
        ]
        session = ConsensusSession(task="t", agents=agents)
        rd = ConsensusRound(round_number=2)
        rd.proposals = {a.id: f"proposal-{a.id}" for a in agents}
        session.rounds.append(rd)
        await engine._critique_phase(session, rd)

        # Every non-self opponent is covered — not just the first two.
        for a in agents:
            others = sorted(x.id for x in agents if x.id != a.id)
            assert sorted(seen[a.id]) == others


class TestDefaultTeamFallback:
    @pytest.mark.asyncio
    async def test_none_agents_uses_default_team(self):
        engine = ConsensusEngine()
        captured = {}

        async def skip_to_end(self, session):
            return session.status

        engine.run_consensus_core = None
        # Patch the phases out to isolate the agent_default branch.
        engine._proposal_phase = AsyncMock()
        engine._critique_phase = AsyncMock()
        engine._shadow_critique_phase = AsyncMock()
        engine._shadow_integration_phase = AsyncMock()
        engine._refinement_phase = AsyncMock()

        async def eval_phase(session, rd):
            rd.evaluations = {}
            rd.scores = {}

        engine._evaluation_phase = eval_phase  # type: ignore
        engine._convergence_check = AsyncMock(return_value=True)
        engine.synthesizer = AsyncMock()
        engine.synthesizer.generate_synthesis = AsyncMock(return_value="synth")
        captured["before"] = None
        session = await engine.run_consensus("task", agents=None, max_rounds=1, min_rounds=1)
        assert session.status == "completed"
        assert len(session.agents) == 5  # registry default team
        assert all(a.archetype is not None for a in session.agents)


class TestScoringProvenance:
    @pytest.mark.asyncio
    async def test_exception_is_labeled(self):
        scorer = ConsensusScorer()
        broken = AsyncMock()
        broken.generate.side_effect = RuntimeError("llm down")
        agent = _agent("sage", "a1")
        out = await scorer.evaluate_all("task", {agent.id: "text"}, [agent], broken)
        assert out[agent.id]["estimated"] is True
        assert "error" in out[agent.id]
        assert out[agent.id]["overall"] == 0.5

    @pytest.mark.asyncio
    async def test_missing_dims_flagged_via_fallback(self):
        scorer = ConsensusScorer()
        llm = AsyncMock()
        # First call: incomplete JSON (missing dims). Second: usable numbers.
        llm.generate.side_effect = [
            '{"accuracy": 0.9}',
            "0.9, 0.8, 0.7, 0.6, 0.5",
        ]
        agent = _agent("sage", "a1")
        out = await scorer.evaluate_all("task", {agent.id: "text"}, [agent], llm)
        assert out[agent.id]["estimated"] is True
        assert out[agent.id]["accuracy"] == 0.9

    @pytest.mark.asyncio
    async def test_full_parse_not_estimated(self):
        scorer = ConsensusScorer()
        llm = AsyncMock()
        llm.generate.return_value = (
            '{"accuracy": 0.9, "holistic_insight": 0.8, "creativity": 0.7, "feasibility": 0.6, "polarity_balance": 0.5}'
        )
        agent = _agent("sage", "a1")
        out = await scorer.evaluate_all("task", {agent.id: "text"}, [agent], llm)
        assert out[agent.id]["estimated"] is False

    @pytest.mark.asyncio
    async def test_truncation_helper_used(self):
        scorer = ConsensusScorer()
        llm = AsyncMock()
        llm.generate.return_value = (
            '{"accuracy": 1, "holistic_insight": 1, "creativity": 1, "feasibility": 1, "polarity_balance": 1}'
        )
        agent = _agent("sage", "a1")
        long_content = "x" * 50000
        await scorer.evaluate_all("task", {agent.id: long_content}, [agent], llm)
        prompt = llm.generate.call_args[0][0]
        assert TRUNCATION_MARKER in prompt
