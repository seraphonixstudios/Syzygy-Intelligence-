"""Audit log API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.audit import audit_service

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    event_type: str = Query(""),
    agent_id: str = Query(""),
    session_id: str = Query(""),
    limit: int = Query(100),
    offset: int = Query(0),
) -> dict[str, Any]:
    entries = await audit_service.query(
        event_type=event_type or None,
        agent_id=agent_id or None,
        session_id=session_id or None,
        limit=limit,
        offset=offset,
    )
    return {"entries": entries, "total": len(entries)}


@router.get("/count")
async def count_audit_logs(
    event_type: str = Query(""),
    agent_id: str = Query(""),
    session_id: str = Query(""),
) -> dict[str, Any]:
    count = await audit_service.count(
        event_type=event_type or None,
        agent_id=agent_id or None,
        session_id=session_id or None,
    )
    return {"count": count}
