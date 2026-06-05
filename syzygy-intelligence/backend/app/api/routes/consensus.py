"""Consensus engine API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.consensus.engine import ConsensusEngine
from app.agents.registry import agent_registry

router = APIRouter()
engine = ConsensusEngine()


@router.post("/run")
async def run_consensus(data: dict):
    task = data.get("task", "")
    if not task:
        raise HTTPException(400, "Task is required")

    session = await engine.run_consensus(
        task=task,
        max_rounds=data.get("max_rounds", 6),
        convergence_threshold=data.get("threshold", 0.85),
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
