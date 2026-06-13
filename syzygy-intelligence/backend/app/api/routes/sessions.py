"""Session management API routes — backed by database."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_user
from app.db.models import Agent, SessionState, User
from app.db.models import Session as DBSession
from app.db.session import get_db
from app.logging_setup import logger

router = APIRouter()


async def _get_or_create_agent(db: AsyncSession) -> Agent:
    result = await db.execute(select(Agent).limit(1))
    agent = result.scalar_one_or_none()
    if not agent:
        agent = Agent(
            id=uuid.uuid4(),
            name="Default Agent",
            polarity="unified",
            primary_archetype="sage",
            model="qwen3:8b-gpu",
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
    return agent


@router.get("/")
async def list_sessions(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(DBSession)
            .order_by(DBSession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        sessions = result.scalars().all()
        return {
            "sessions": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "task": s.task_description,
                    "state": s.state.value if s.state else "unknown",
                    "workflow_type": s.workflow_type,
                    "rounds_completed": s.consensus_rounds_completed,
                    "final_synthesis": (
                        s.final_synthesis[:200] + "..." if s.final_synthesis and len(s.final_synthesis) > 200
                        else s.final_synthesis
                    ),
                    "created_at": s.created_at.isoformat() if s.created_at else "",
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e), user_id=str(user.id))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list sessions")


@router.post("/")
async def create_session(
    data: dict[str, Any],
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        agent = await _get_or_create_agent(db)
        session = DBSession(
            id=uuid.uuid4(),
            agent_id=agent.id,
            name=data.get("name", "New Session"),
            task_description=data.get("task", ""),
            state=SessionState.ACTIVE,
            workflow_type=data.get("workflow_type", "general"),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return {
            "session_id": str(session.id),
            "name": session.name,
            "status": session.state.value,
            "task": session.task_description,
        }
    except Exception as e:
        logger.error("Failed to create session", error=str(e), user_id=str(user.id))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create session")


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(DBSession)
            .options(selectinload(DBSession.consensus_rounds))
            .where(DBSession.id == uuid.UUID(session_id))
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

        return {
            "id": str(session.id),
            "name": session.name,
            "task": session.task_description,
            "state": session.state.value if session.state else "unknown",
            "workflow_type": session.workflow_type,
            "rounds_completed": session.consensus_rounds_completed,
            "polarity_balance": session.polarity_balance_score,
            "final_synthesis": session.final_synthesis,
            "rounds": [
                {
                    "round": r.round_number,
                    "status": r.status.value if r.status else "unknown",
                    "proposals": r.proposals,
                    "critiques": r.critiques,
                    "refinements": r.refinements,
                    "scores": r.scores,
                    "convergence_score": r.convergence_score,
                }
                for r in (session.consensus_rounds or [])
            ],
            "created_at": session.created_at.isoformat() if session.created_at else "",
            "updated_at": session.updated_at.isoformat() if session.updated_at else "",
        }
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Invalid session ID format", error=str(e), session_id=session_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")
    except Exception as e:
        logger.error("Failed to get session", error=str(e), session_id=session_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get session")
