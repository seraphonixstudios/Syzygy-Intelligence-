"""Session management API routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_sessions():
    return {"sessions": []}


@router.post("/")
async def create_session(data: dict):
    return {
        "session_id": "new-session-id",
        "status": "created",
        "task": data.get("task", ""),
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    return {
        "session_id": session_id,
        "status": "active",
        "rounds_completed": 0,
    }
