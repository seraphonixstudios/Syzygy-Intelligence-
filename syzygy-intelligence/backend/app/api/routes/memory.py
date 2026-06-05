"""Memory API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.memory import memory_system

router = APIRouter()


@router.post("/store")
async def store_memory(data: dict):
    memory_id = await memory_system.store(
        content=data.get("content", ""),
        memory_type=data.get("type", "short_term"),
        agent_id=data.get("agent_id", ""),
        session_id=data.get("session_id", ""),
        polarity=data.get("polarity", ""),
        archetype=data.get("archetype", ""),
        importance=data.get("importance", 0.5),
        tags=data.get("tags", []),
    )
    return {"memory_id": memory_id}


@router.get("/recall")
async def recall_memory(
    query: str = Query(""),
    agent_id: str = Query(""),
    polarity: str = Query(""),
    limit: int = Query(10),
):
    results = await memory_system.recall(
        query=query,
        agent_id=agent_id,
        polarity=polarity,
        limit=limit,
    )
    return {"memories": results}


@router.get("/recent")
async def recent_memories(session_id: str = Query(""), limit: int = Query(5)):
    results = await memory_system.remember_recent(
        session_id=session_id,
        limit=limit,
    )
    return {"memories": results}
