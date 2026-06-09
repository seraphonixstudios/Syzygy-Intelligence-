"""Consensus engine API routes — memory-integrated."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.agents.registry import agent_registry
from app.consensus.engine import ConsensusEngine
from app.orchestration.consensus_integration import run_consensus_with_memory

router = APIRouter()
engine = ConsensusEngine()


class RunConsensusRequest(BaseModel):
    task: str
    max_rounds: int = 6
    min_rounds: int = 2
    threshold: float = 0.85
    agent_ids: list[str] | None = None
    session_id: str = ""


@router.post("/run")
async def run_consensus(data: RunConsensusRequest):
    if not data.task:
        raise HTTPException(400, "Task is required")

    if data.agent_ids:
        agents = []
        for aid in data.agent_ids:
            agent = agent_registry.get(aid)
            if agent:
                agents.append(agent)
        if not agents:
            raise HTTPException(400, "No valid agents found for the given IDs")
    else:
        agents = agent_registry.create_default_team()

    session = await run_consensus_with_memory(
        engine=engine,
        task=data.task,
        agents=agents,
        session_id=data.session_id,
        max_rounds=data.max_rounds,
        min_rounds=data.min_rounds,
        convergence_threshold=data.threshold,
    )

    return {
        "session_id": session.id,
        "rounds_completed": session.current_round,
        "synthesis": session.final_synthesis,
        "fusion_report": session.polarity_fusion_report,
        "round_details": [
            {
                "round": r.round_number,
                "proposals": list(r.proposals.values()),
                "critiques": list(r.critiques.values()),
                "refinements": list(r.refinements.values()),
                "scores": r.scores,
                "convergence_score": r.convergence_score,
            }
            for r in session.rounds
        ],
        "status": session.status,
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = engine.active_sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    return {
        "session_id": session.id,
        "task": session.task,
        "rounds_completed": session.current_round,
        "synthesis": session.final_synthesis,
        "fusion_report": session.polarity_fusion_report,
        "status": session.status,
    }
