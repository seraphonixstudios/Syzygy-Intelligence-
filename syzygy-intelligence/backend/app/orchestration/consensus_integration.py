"""Connects consensus engine with memory system and agent registry.

Ensures every consensus round:
- Recalls relevant memories before proposals
- Stores all phase outputs (proposals, critiques, refinements) to memory
- Saves synthesis to long-term memory
- Integrates with checkpoint manager
"""

from __future__ import annotations

from app.agents.base import SyzygyAgent
from app.consensus.engine import ConsensusEngine, ConsensusSession
from app.logging_setup import logger
from app.memory import MemorySystem
from app.orchestration.checkpointing import CheckpointManager

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
) -> ConsensusSession:
    """Run consensus with full memory integration."""

    # Recall relevant memories as context for all agents
    context = await _build_consensus_context(task, session_id)

    original_agent_propose = engine._agent_propose

    async def _agent_propose_with_memory(agent, task_text, ctx):
        enriched = f"{ctx}\n\nRelevant context from past work:\n{context}" if context else ctx
        return await original_agent_propose(agent, task_text, enriched)

    engine._agent_propose = _agent_propose_with_memory  # type: ignore

    session = await engine.run_consensus(
        task=task,
        agents=agents,
        max_rounds=max_rounds,
        min_rounds=min_rounds,
        convergence_threshold=convergence_threshold,
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

    logger.info(
        "Consensus with memory complete",
        session_id=session_id,
        rounds=session.current_round,
        convergence=session.rounds[-1].convergence_score if session.rounds else 0,
        source="consensus",
    )

    return session


async def _build_consensus_context(task: str, session_id: str) -> str:
    """Pull relevant memories from all layers to provide as context."""
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

    if parts:
        return "### Relevant context:\n" + "\n\n".join(parts)
    return ""
