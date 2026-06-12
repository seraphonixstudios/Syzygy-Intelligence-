"""WebSocket handler for live consensus visualization and streaming.

Integrates with the notification system for persistent message delivery.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.agents.registry import agent_registry
from app.consensus.engine import ConsensusEngine
from app.logging_setup import logger
from app.notifications import NotificationSeverity, NotificationType, notification_manager
from app.orchestration.consensus_integration import run_consensus_with_memory


class ConnectionManager:
    """Manages WebSocket connections for live streaming with health tracking."""

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self._connection_health: dict[str, int] = {}

    async def connect(self, websocket: WebSocket, client_id: str = "") -> str:
        await websocket.accept()
        cid = client_id or f"ws_{id(websocket)}"
        self.active_connections[cid] = websocket
        self._connection_health[cid] = 0

        async def send_json(data: dict[str, Any]) -> None:
            await websocket.send_json(data)

        notification_manager.register_ws(cid, send_json)
        logger.info("WebSocket client connected", client_id=cid, active_connections=len(self.active_connections))
        return cid

    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)
        self._connection_health.pop(client_id, None)
        notification_manager.unregister_ws(client_id)
        logger.info(
            "WebSocket client disconnected",
            client_id=client_id, active_connections=len(self.active_connections),
        )

    async def send_to(self, client_id: str, message: dict[str, Any]) -> bool:
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
                return True
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}", error=str(e))
                self.disconnect(client_id)
        return False

    async def broadcast(self, message: dict[str, Any]) -> None:
        disconnected = []
        for cid, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(cid)
        for cid in disconnected:
            self.disconnect(cid)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_connection_ids(self) -> list[str]:
        return list(self.active_connections.keys())


manager = ConnectionManager()


async def ws_handler(websocket: WebSocket) -> None:
    client_id = await manager.connect(websocket)
    engine = ConsensusEngine()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            action = data.get("action", "")

            if action == "ping":
                from datetime import datetime as _dt
                await manager.send_to(client_id, {"type": "pong", "timestamp": _dt.now().isoformat()})

            elif action == "subscribe":
                event_types = data.get("event_types", ["*"])
                logger.info("Client subscribed to events", client_id=client_id, events=event_types)
                await manager.send_to(client_id, {"type": "subscribed", "event_types": event_types})

            elif action == "run_consensus":
                task = data.get("task", "")
                if not task:
                    await manager.send_to(client_id, {"type": "error", "message": "Task is required"})
                    continue

                await manager.send_to(client_id, {"type": "consensus_started", "task": task})

                await notification_manager.notify(
                    type=NotificationType.CONSENSUS_STARTED,
                    title="Consensus process started",
                    body=f"Task: {task[:100]}",
                    severity=NotificationSeverity.INFO,
                    source="consensus_engine",
                    data={"task": task},
                )

                async def on_event(event_type: str, payload: dict[str, Any]) -> None:
                    await manager.send_to(client_id, {
                        "type": f"consensus_{event_type}",
                        **payload,
                    })

                agents = agent_registry.create_default_team()
                session = await run_consensus_with_memory(
                    engine=engine,
                    task=task,
                    agents=agents,
                    on_event=on_event,
                )

                await manager.send_to(client_id, {
                    "type": "consensus_complete",
                    "session_id": session.id,
                    "synthesis": session.final_synthesis,
                    "fusion_report": session.polarity_fusion_report,
                    "total_rounds": session.current_round,
                })

                await notification_manager.notify(
                    type=NotificationType.CONSENSUS_COMPLETE,
                    title="Consensus complete",
                    body=f"Synthesis generated after {session.current_round} rounds",
                    severity=NotificationSeverity.INFO,
                    source="consensus_engine",
                    session_id=session.id,
                    data={"rounds": session.current_round},
                )

            elif action == "get_status":
                await manager.send_to(client_id, {
                    "type": "status",
                    "connection_count": manager.get_connection_count(),
                    "connection_id": client_id,
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally", client_id=client_id)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from WebSocket client", client_id=client_id)
    except Exception as e:
        logger.error("WebSocket error", client_id=client_id, error=str(e))
    finally:
        manager.disconnect(client_id)
