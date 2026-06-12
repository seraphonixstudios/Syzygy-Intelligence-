"""Connects consensus engine with memory system and agent registry.

Ensures every consensus round:
- Recalls relevant memories before proposals
- Stores all phase outputs (proposals, critiques, refinements) to memory
- Saves synthesis to long-term memory
- Integrates with checkpoint manager
- Persists session + rounds to database
- Forwards streaming events via callback
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select

from app.agents.base import SyzygyAgent
from app.consensus.engine import ConsensusEngine, ConsensusSession
from app.db.models import Agent as DBAgent
from app.db.models import ConsensusRound as DBConsensusRound
from app.db.models import ConsensusRoundStatus, SessionState
from app.db.models import Session as DBSession
from app.db.session import get_db_context
from app.logging_setup import logger
from app.memory import MemorySystem
from app.orchestration.checkpointing import CheckpointManager

ConsensusEventCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

memory_system = MemorySystem()
checkpoint_manager = CheckpointManager()


async def run_consensus_with_memory(
    engine: ConsensusEngine,
    task: str,
    agents: list[SyzygyAgent],
    session_id: str = "",
    max_rounds: int = 6,
    min_rounds: int = 2,
    convergence_threshold: float = 0.85,
    on_event: ConsensusEventCallback | None = None,
    db_session_id: str = "",
) -> ConsensusSession:
    """Run consensus with full memory integration and optional streaming events."""

    # Recall relevant memories as context for all agents
    context = await _build_consensus_context(task, session_id)

    original_agent_propose = engine._agent_propose

    async def _agent_propose_with_memory(agent: Any, task_text: str, ctx: str) -> Any:
        enriched = f"{ctx}\n\nRelevant context from past work:\n{context}" if context else ctx
        return await original_agent_propose(agent, task_text, enriched)

    engine._agent_propose = _agent_propose_with_memory  # type: ignore

    session = await engine.run_consensus(
        task=task,
        agents=agents,
        max_rounds=max_rounds,
        min_rounds=min_rounds,
        convergence_threshold=convergence_threshold,
        on_event=on_event,
    )

    # Store each round's outputs to memory
    for round_data in session.rounds:
        for agent_id, proposal in round_data.proposals.items():
            await memory_system.store(
                content=proposal,
                memory_type="short_term",
                agent_id=agent_id,
                session_id=session_id,
                tags=["consensus", "proposal"],
                importance=0.6,
            )

        for agent_id, critique in round_data.critiques.items():
            await memory_system.store(
                content=critique,
                memory_type="short_term",
                agent_id=agent_id,
                session_id=session_id,
                tags=["consensus", "critique"],
                importance=0.5,
            )

        for agent_id, refinement in round_data.refinements.items():
            await memory_system.store(
                content=refinement,
                memory_type="short_term",
                agent_id=agent_id,
                session_id=session_id,
                tags=["consensus", "refinement"],
                importance=0.7,
            )

    # Store final synthesis to long-term memory
    if session.final_synthesis:
        await memory_system.store(
            content=session.final_synthesis,
            memory_type="long_term",
            session_id=session_id,
            tags=["consensus", "synthesis", "rebis"],
            importance=0.9,
        )

    # Add to team memory
    await memory_system.team.store(
        content=session.final_synthesis or task,
        agent_id="__orchestrator__",
        session_id=session_id,
        tags=["consensus", "completed"],
        metadata={
            "task": task,
            "num_rounds": session.current_round,
            "convergence_score": session.rounds[-1].convergence_score if session.rounds else 0,
            "polarity_fusion": session.polarity_fusion_report,
        },
    )

    # Save checkpoint
    await checkpoint_manager.save_checkpoint(
        session_id=session_id,
        round_number=session.current_round,
        state={
            "task": task,
            "final_synthesis": session.final_synthesis,
            "polarity_fusion_report": session.polarity_fusion_report,
            "num_rounds": session.current_round,
        },
        metadata={"status": session.status},
    )

    # Persist to DB
    await _persist_session_to_db(session, task, db_session_id)

    logger.info(
        "Consensus with memory complete",
        session_id=session_id,
        rounds=session.current_round,
        convergence=session.rounds[-1].convergence_score if session.rounds else 0,
        source="consensus",
    )

    return session


async def _persist_session_to_db(session: ConsensusSession, task: str, db_session_id: str = "") -> None:
    """Save consensus session + rounds to database."""
    try:
        async with get_db_context() as db:
            sid = uuid.UUID(db_session_id) if db_session_id else uuid.uuid4()

            existing = await db.execute(select(DBSession).where(DBSession.id == sid))
            db_sesh = existing.scalar_one_or_none()

            if not db_sesh:
                # Get or create a default agent for the FK
                agent_result = await db.execute(select(DBAgent).limit(1))
                agent = agent_result.scalar_one_or_none()
                if not agent:
                    agent = DBAgent(
                        id=uuid.uuid4(),
                        name="Default Agent",
                        polarity="unified",
                        primary_archetype="sage",
                        model="qwen3:8b-gpu",
                    )
                    db.add(agent)
                    await db.flush()
                agent_id = agent.id

                db_sesh = DBSession(
                    id=sid,
                    agent_id=agent_id,
                    name=f"Consensus: {task[:60]}",
                    task_description=task,
                    state=SessionState.COMPLETED if session.status == "completed" else SessionState.COMPLETED,
                    workflow_type="consensus",
                    consensus_rounds_completed=session.current_round,
                    polarity_balance_score=session.rounds[-1].polarity_balance if session.rounds else None,
                    final_synthesis=session.final_synthesis,
                    metadata_={
                        "polarity_fusion_report": session.polarity_fusion_report,
                        "num_agents": len(session.agents),
                    },
                )
                db.add(db_sesh)
                await db.flush()

            for rd in session.rounds:
                db_round = DBConsensusRound(
                    session_id=db_sesh.id,
                    round_number=rd.round_number,
                    status=ConsensusRoundStatus.COMPLETED,
                    proposals=rd.proposals,
                    critiques=rd.critiques,
                    refinements=rd.refinements,
                    evaluations=rd.evaluations,
                    scores=rd.scores,
                    convergence_score=rd.convergence_score,
                    polarity_balance=rd.polarity_balance,
                    synthesis=rd.synthesis if rd.synthesis else None,
                )
                db.add(db_round)

            await db.commit()
            logger.debug("Consensus session persisted to DB", session_id=str(sid), source="consensus")
    except Exception as e:
        logger.warning("Failed to persist consensus session to DB", error=str(e), source="consensus")


async def _build_consensus_context(task: str, session_id: str) -> str:
    """Pull relevant memories from all layers + RAG to provide as context."""
    parts: list[str] = []

    team_memories = await memory_system.search_team_memory(task, limit=3)
    for mem in team_memories:
        parts.append(f"[Team memory] {mem.get('content', '')[:300]}")

    vector_memories = await memory_system.recall(
        query=task,
        memory_types=["long_term"],
        limit=3,
    )
    for mem in vector_memories:
        parts.append(f"[Past result] {mem.get('content', '')[:300]}")

    # Also pull from RAG document store
    try:
        from app.rag.retriever import query as rag_query
        rag_results = await rag_query(task, top_k=2, min_score=0.3)
        for r in rag_results:
            parts.append(f"[Knowledge base] {r.get('content', '')[:300]}")
    except Exception as e:
        logger.debug("RAG query failed (non-critical)", error=str(e))

    if parts:
        return "### Relevant context:\n" + "\n\n".join(parts)
    return ""
