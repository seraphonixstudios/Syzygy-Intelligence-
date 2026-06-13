"""Consensus engine API routes — memory-integrated, usage-gated, with optional WS streaming."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import agent_registry
from app.api.auth import check_usage_limit, require_user
from app.api.websockets import manager as ws_manager
from app.consensus.engine import ConsensusEngine
from app.db.models import User
from app.db.session import get_db
from app.logging_setup import logger
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
    ws_client_id: str | None = None


@router.post("/run")
async def run_consensus(
    data: RunConsensusRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        if not data.task:
            raise HTTPException(400, "Task is required")

        await check_usage_limit(user, db)

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

        async def on_event(event_type: str, payload: dict[str, Any]) -> None:
            if data.ws_client_id:
                await ws_manager.send_to(data.ws_client_id, {
                    "type": f"consensus_{event_type}",
                    **payload,
                })

        session = await run_consensus_with_memory(
            engine=engine,
            task=data.task,
            agents=agents,
            session_id=data.session_id,
            max_rounds=data.max_rounds,
            min_rounds=data.min_rounds,
            convergence_threshold=data.threshold,
            on_event=on_event if data.ws_client_id else None,
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Consensus run failed", error=str(e), task=data.task[:100], user_id=str(user.id))
        raise HTTPException(500, f"Consensus execution failed: {str(e)[:200]}")


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    try:
        session = engine.active_sessions.get(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get consensus session", error=str(e), session_id=session_id)
        raise HTTPException(500, "Failed to get session")

    return {
        "session_id": session.id,
        "task": session.task,
        "rounds_completed": session.current_round,
        "synthesis": session.final_synthesis,
        "fusion_report": session.polarity_fusion_report,
        "status": session.status,
    }
