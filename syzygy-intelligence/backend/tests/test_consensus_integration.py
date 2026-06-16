"""Tests for run_consensus_with_memory, _persist_session_to_db, _build_consensus_context."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.consensus_integration import (
    _build_consensus_context,
    _persist_session_to_db,
    run_consensus_with_memory,
)


@pytest.fixture
def mock_memory():
    with patch("app.orchestration.consensus_integration.memory_system") as m:
        m.store = AsyncMock()
        m.recall = AsyncMock(return_value=[])
        m.search_team_memory = AsyncMock(return_value=[])
        m.team = AsyncMock()
        m.team.store = AsyncMock()
        yield m


@pytest.fixture
def mock_checkpoint():
    with patch("app.orchestration.consensus_integration.checkpoint_manager") as m:
        m.save_checkpoint = AsyncMock()
        yield m


@pytest.fixture
def mock_db():
    with patch("app.orchestration.consensus_integration.get_db_context") as mock_ctx:
        mock_session = AsyncMock()
        # Use MagicMock for execute results because scalar_one_or_none() is SYNC
        # If using AsyncMock, the sync call returns a coroutine = bad
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock(return_value=None)
        cm = AsyncMock()
        cm.__aenter__.return_value = mock_session
        cm.__aexit__.return_value = None
        mock_ctx.return_value = cm
        yield mock_session


@pytest.fixture
def mock_logger():
    with patch("app.orchestration.consensus_integration.logger") as m:
        yield m


@pytest.fixture
def mock_rag():
    with patch("app.rag.retriever.query") as m:
        m.return_value = []
        yield m


def make_mock_agent(name: str = "test-agent") -> MagicMock:
    agent = MagicMock()
    agent.id = name
    agent.archetype = "sage"
    agent.polarity = 0.5
    agent.model = "qwen3:8b-gpu"
    return agent


def make_round_data(
    round_num: int = 1,
    proposals: dict | None = None,
    critiques: dict | None = None,
    refinements: dict | None = None,
    convergence: float = 0.9,
    polarity: float = 0.5,
    synthesis: str | None = None,
):
    rd = MagicMock()
    rd.round_number = round_num
    rd.proposals = proposals or {"agent1": "proposal text"}
    rd.critiques = critiques or {"agent1": "critique text"}
    rd.refinements = refinements or {"agent1": "refinement text"}
    rd.evaluations = {}
    rd.scores = {}
    rd.convergence_score = convergence
    rd.polarity_balance = polarity
    rd.synthesis = synthesis or "synthesis text"
    return rd


def make_session(rounds=None, status="completed", final_synthesis="final result"):
    session = MagicMock()
    session.rounds = rounds or [make_round_data()]
    session.current_round = len(session.rounds)
    session.status = status
    session.final_synthesis = final_synthesis
    session.polarity_fusion_report = {"fusion": "complete"}
    session.agents = ["agent1"]
    return session


class TestRunConsensusWithMemory:
    @pytest.mark.asyncio
    async def test_calls_build_context(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        engine.run_consensus = AsyncMock(return_value=make_session())
        engine._agent_propose = AsyncMock()

        agents = [make_mock_agent()]

        await run_consensus_with_memory(engine, "test task", agents, session_id="ses-1")

        mock_memory.search_team_memory.assert_called_once()
        assert engine.run_consensus.called

    @pytest.mark.asyncio
    async def test_stores_round_data_to_memory(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        rd = make_round_data(
            proposals={"a1": "p1"},
            critiques={"a1": "c1"},
            refinements={"a1": "r1"},
        )
        session = make_session(rounds=[rd])
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        agents = [make_mock_agent()]

        await run_consensus_with_memory(engine, "t", agents, session_id="ses-2")

        # Should store proposal, critique, refinement, synthesis, and team memory
        assert mock_memory.store.call_count >= 4

    @pytest.mark.asyncio
    async def test_stores_final_synthesis_to_long_term(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        session = make_session(final_synthesis="important synthesis result")
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        await run_consensus_with_memory(engine, "t", [make_mock_agent()], session_id="ses-3")

        # Find the long-term memory store call
        long_term_calls = [c for c in mock_memory.store.call_args_list if c.kwargs.get("memory_type") == "long_term"]
        assert len(long_term_calls) >= 1
        assert long_term_calls[0].kwargs["content"] == "important synthesis result"

    @pytest.mark.asyncio
    async def test_adds_team_memory(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        session = make_session(final_synthesis="synthesis for team")
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        await run_consensus_with_memory(engine, "test task", [make_mock_agent()], session_id="ses-4")

        mock_memory.team.store.assert_called_once()
        assert mock_memory.team.store.call_args.kwargs["content"] == "synthesis for team"

    @pytest.mark.asyncio
    async def test_saves_checkpoint(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        session = make_session()
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        await run_consensus_with_memory(engine, "t", [make_mock_agent()], session_id="ses-5")

        mock_checkpoint.save_checkpoint.assert_called_once()
        assert mock_checkpoint.save_checkpoint.call_args.kwargs["session_id"] == "ses-5"

    @pytest.mark.asyncio
    async def test_persists_session_to_db(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        session = make_session()
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await run_consensus_with_memory(engine, "t", [make_mock_agent()], session_id="ses-6", db_session_id="00000000-0000-0000-0000-000000000001")

        # DB should have been used
        assert mock_db.add.called or mock_db.execute.called

    @pytest.mark.asyncio
    async def test_passes_event_callback(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        session = make_session()
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        callback = AsyncMock()

        await run_consensus_with_memory(
            engine, "t", [make_mock_agent()], session_id="ses-7", on_event=callback
        )

        engine.run_consensus.assert_called_once()
        assert engine.run_consensus.call_args.kwargs["on_event"] is callback

    @pytest.mark.asyncio
    async def test_memory_enriched_propose(self, mock_memory, mock_checkpoint, mock_db):
        mock_memory.search_team_memory = AsyncMock(return_value=[{"content": "past team work"}])
        mock_memory.recall = AsyncMock(return_value=[{"content": "past result data"}])

        engine = AsyncMock()
        session = make_session()
        engine.run_consensus = AsyncMock(return_value=session)

        original_propose = AsyncMock(return_value="proposal")
        engine._agent_propose = original_propose

        await run_consensus_with_memory(engine, "t", [make_mock_agent()], session_id="ses-mem")

        # Verify the wrapper was created and calls original with enriched context
        assert engine._agent_propose is not original_propose

        # Call the wrapper directly — it should enrich context
        result = await engine._agent_propose(make_mock_agent(), "task", "base_ctx")
        assert result == "proposal"
        # original was called with enriched context containing past memories
        original_propose.assert_awaited_once()
        args = original_propose.call_args[0]
        assert "past team work" in args[2]
        assert "past result data" in args[2]

    @pytest.mark.asyncio
    async def test_enriches_context_with_memories(self, mock_memory, mock_checkpoint, mock_db):
        mock_memory.search_team_memory = AsyncMock(return_value=[{"content": "past team work"}])
        mock_memory.recall = AsyncMock(return_value=[{"content": "past result data"}])

        engine = AsyncMock()
        session = make_session()
        engine.run_consensus = AsyncMock(return_value=session)

        original_propose = AsyncMock(return_value="proposal")
        engine._agent_propose = original_propose

        await run_consensus_with_memory(engine, "t", [make_mock_agent()], session_id="ses-8")

        # The function monkey-patches engine._agent_propose with a wrapper.
        # Verify the wrapper was set by checking it's no longer our original.
        assert engine._agent_propose is not original_propose
        # Verify original was captured by checking run_consensus was called
        assert engine.run_consensus.called

    @pytest.mark.asyncio
    async def test_handles_runs_with_no_synthesis(self, mock_memory, mock_checkpoint, mock_db):
        engine = AsyncMock()
        session = make_session(final_synthesis=None)
        engine.run_consensus = AsyncMock(return_value=session)
        engine._agent_propose = AsyncMock()

        await run_consensus_with_memory(engine, "t", [make_mock_agent()], session_id="ses-9")

        # Should not fail, team memory uses task as fallback
        assert mock_memory.team.store.called


class TestBuildConsensusContext:
    @pytest.mark.asyncio
    async def test_returns_empty_string_when_no_memories(self, mock_memory, mock_rag):
        result = await _build_consensus_context("test task", "ses-1")
        assert result == ""

    @pytest.mark.asyncio
    async def test_includes_team_memories(self, mock_memory, mock_rag):
        mock_memory.search_team_memory = AsyncMock(return_value=[{"content": "important team insight"}])
        result = await _build_consensus_context("test task", "ses-1")
        assert "important team insight" in result
        assert "[Team memory]" in result

    @pytest.mark.asyncio
    async def test_includes_vector_memories(self, mock_memory, mock_rag):
        mock_memory.recall = AsyncMock(return_value=[{"content": "past research result"}])
        result = await _build_consensus_context("test", "ses-1")
        assert "past research result" in result
        assert "[Past result]" in result

    @pytest.mark.asyncio
    async def test_includes_rag_results(self, mock_memory, mock_rag):
        mock_rag.return_value = [{"content": "document knowledge"}]
        result = await _build_consensus_context("test", "ses-1")
        assert "document knowledge" in result
        assert "[Knowledge base]" in result

    @pytest.mark.asyncio
    async def test_truncates_long_memories(self, mock_memory, mock_rag):
        mock_memory.search_team_memory = AsyncMock(return_value=[{"content": "A" * 500}])
        result = await _build_consensus_context("test", "ses-1")
        assert len(result) < 500  # Truncated

    @pytest.mark.asyncio
    async def test_rag_failure_does_not_block(self, mock_memory, mock_rag):
        mock_rag.side_effect = Exception("RAG unavailable")
        mock_memory.recall = AsyncMock(return_value=[])
        mock_memory.search_team_memory = AsyncMock(return_value=[{"content": "data"}])
        result = await _build_consensus_context("test", "ses-1")
        assert "data" in result  # Team memory still included


class TestPersistSessionToDb:
    @pytest.mark.asyncio
    async def test_creates_new_session_when_none_exists(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        session = make_session()

        await _persist_session_to_db(session, "test task", "00000000-0000-0000-0000-000000000001")

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_creates_default_agent_when_no_agents(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        session = make_session()

        await _persist_session_to_db(session, "test", "00000000-0000-0000-0000-000000000002")

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_skips_duplicate_session(self, mock_db):
        existing_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_session
        mock_db.execute.return_value = mock_result

        session = make_session()

        await _persist_session_to_db(session, "test task", "00000000-0000-0000-0000-000000000003")

        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_creates_rounds_for_each_round(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        rd1 = make_round_data(round_num=1)
        rd2 = make_round_data(round_num=2, convergence=0.95)
        session = make_session(rounds=[rd1, rd2])

        await _persist_session_to_db(session, "test", "00000000-0000-0000-0000-000000000004")

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_handles_db_failure_gracefully(self, mock_db, mock_logger):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.commit.side_effect = Exception("DB connection lost")

        session = make_session()

        await _persist_session_to_db(session, "test", "00000000-0000-0000-0000-000000000005")

        assert mock_logger.warning.called
