"""Audit logging service — persisted database-backed audit trail.

Uses lazy database initialization — safe to import even without a running database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.db.models import AuditLog
from app.db.session import _get_session_factory
from app.logging_setup import logger


class AuditService:
    """Persistent audit logging service with database storage."""

    @staticmethod
    async def log(
        event_type: str,
        action: str,
        agent_id: str | None = None,
        session_id: str | None = None,
        details: dict[str, Any] = None,
        ip_address: str | None = None,
    ) -> str:
        """Persist an audit event to the database."""
        try:
            factory = _get_session_factory()
            async with factory() as db:
                entry = AuditLog(
                    id=uuid.uuid4(),
                    event_type=event_type,
                    action=action,
                    agent_id=agent_id,
                    session_id=session_id,
                    details=details or {},
                    ip_address=ip_address,
                    created_at=datetime.now(UTC),
                )
                db.add(entry)
                await db.commit()
                return str(entry.id)
        except Exception as e:
            logger.warning(f"Audit log write failed (DB may not be available): {e}")
            return ""

    @staticmethod
    async def query(
        event_type: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query audit logs with filters."""
        try:
            factory = _get_session_factory()
            async with factory() as db:
                from sqlalchemy import select
                stmt = select(AuditLog).order_by(AuditLog.created_at.desc())

                if event_type:
                    stmt = stmt.where(AuditLog.event_type == event_type)
                if agent_id:
                    stmt = stmt.where(AuditLog.agent_id == agent_id)
                if session_id:
                    stmt = stmt.where(AuditLog.session_id == session_id)

                stmt = stmt.limit(limit).offset(offset)
                result = await db.execute(stmt)
                entries = result.scalars().all()

                return [
                    {
                        "id": str(e.id),
                        "event_type": e.event_type,
                        "action": e.action,
                        "agent_id": str(e.agent_id) if e.agent_id else None,
                        "session_id": str(e.session_id) if e.session_id else None,
                        "details": e.details,
                        "ip_address": e.ip_address,
                        "created_at": e.created_at.isoformat() if e.created_at else None,
                    }
                    for e in entries
                ]
        except Exception as e:
            logger.warning(f"Audit query failed (DB may not be available): {e}")
            return []

    @staticmethod
    async def count(
        event_type: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> int:
        """Count audit log entries matching filters."""
        try:
            factory = _get_session_factory()
            async with factory() as db:
                from sqlalchemy import func, select
                stmt = select(func.count()).select_from(AuditLog)
                if event_type:
                    stmt = stmt.where(AuditLog.event_type == event_type)
                if agent_id:
                    stmt = stmt.where(AuditLog.agent_id == agent_id)
                if session_id:
                    stmt = stmt.where(AuditLog.session_id == session_id)

                result = await db.execute(stmt)
                return result.scalar() or 0
        except Exception as e:
            logger.warning(f"Audit count failed (DB may not be available): {e}")
            return 0


audit_service = AuditService()
