"""WebSocket handler for real-time chat and agent communication."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Session, User
from app.db.session import get_db_context
from app.logging_setup import logger


class ConnectionManager:
    """Manages WebSocket connections per session."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info("WebSocket connected", session_id=session_id)

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info("WebSocket disconnected", session_id=session_id)

    async def broadcast(
        self,
        session_id: str,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        """Broadcast message to all connections in a session."""
        if session_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[session_id]:
            if exclude and connection == exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(
                    "Failed to send WebSocket message",
                    session_id=session_id,
                    error=str(e),
                )
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect(session_id, conn)


manager = ConnectionManager()


async def ws_handler(websocket: WebSocket) -> None:
    """Handle WebSocket connections for real-time updates."""
    session_id = websocket.query_params.get("session_id", str(uuid.uuid4()))
    user_token = websocket.query_params.get("token", "")

    if not user_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        logger.warning("WebSocket rejected: missing token", session_id=session_id)
        return

    # Verify user and session
    try:
        async with get_db_context() as db:
            # In production, decode the token and verify user
            # This is a simplified version — integrate with your auth system
            result = await db.execute(select(Session).where(Session.id == session_id))
            session_obj = result.scalar_one_or_none()

            if not session_obj:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Session not found",
                )
                logger.warning("WebSocket rejected: session not found", session_id=session_id)
                return

    except Exception as e:
        await websocket.close(
            code=status.WS_1011_SERVER_ERROR,
            reason="Internal error",
        )
        logger.error("WebSocket authentication error", session_id=session_id, error=str(e))
        return

    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Log incoming message
            logger.debug(
                "WebSocket message received",
                session_id=session_id,
                message_type=message.get("type"),
            )

            # Handle different message types
            message_type = message.get("type", "unknown")

            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now(UTC).isoformat()})
            elif message_type == "message":
                # Broadcast to other clients in session
                await manager.broadcast(
                    session_id,
                    {
                        "type": "message",
                        "content": message.get("content"),
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                    exclude=websocket,
                )
            else:
                logger.warning(
                    "Unknown WebSocket message type",
                    session_id=session_id,
                    message_type=message_type,
                )

    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)
        logger.info("WebSocket disconnected normally", session_id=session_id)
    except json.JSONDecodeError as e:
        await manager.disconnect(session_id, websocket)
        logger.warning("WebSocket JSON decode error", session_id=session_id, error=str(e))
    except Exception as e:
        await manager.disconnect(session_id, websocket)
        logger.error("WebSocket error", session_id=session_id, error=str(e))
