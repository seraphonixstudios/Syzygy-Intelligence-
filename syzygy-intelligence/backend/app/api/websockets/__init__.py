"""WebSocket handler for live consensus visualization and streaming.

Integrates with the notification system for persistent message delivery.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.consensus.engine import ConsensusEngine
from app.agents.registry import agent_registry
from app.logging_setup import logger
from app.notifications import notification_manager, NotificationType, NotificationSeverity


class ConnectionManager:
    """Manages WebSocket connections for live streaming with health tracking."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._connection_health: dict[str, int] = {}

    async def connect(self, websocket: WebSocket, client_id: str = ""):
        await websocket.accept()
        cid = client_id or f"ws_{id(websocket)}"
        self.active_connections[cid] = websocket
        self._connection_health[cid] = 0

        async def send_json(data: dict):
            await websocket.send_json(data)

        notification_manager.register_ws(cid, send_json)
        logger.info(f"WebSocket client connected", client_id=cid, active_connections=len(self.active_connections))
        return cid

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self._connection_health.pop(client_id, None)
        notification_manager.unregister_ws(client_id)
        logger.info(f"WebSocket client disconnected", client_id=client_id, active_connections=len(self.active_connections))

    async def send_to(self, client_id: str, message: dict):
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
                return True
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}", error=str(e))
                self.disconnect(client_id)
        return False

    async def broadcast(self, message: dict):
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


async def ws_handler(websocket: WebSocket):
    client_id = await manager.connect(websocket)
    engine = ConsensusEngine()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            action = data.get("action", "")

            if action == "ping":
                await manager.send_to(client_id, {"type": "pong", "timestamp": __import__("datetime").datetime.now().isoformat()})

            elif action == "subscribe":
                event_types = data.get("event_types", ["*"])
                logger.info(f"Client subscribed to events", client_id=client_id, events=event_types)
                await manager.send_to(client_id, {"type": "subscribed", "event_types": event_types})

            elif action == "run_consensus":
                task = data.get("task", "")
                if not task:
                    await manager.send_to(client_id, {"type": "error", "message": "Task is required"})
                    continue

                await notification_manager.notify(
                    type=NotificationType.CONSENSUS_STARTED,
                    title="Consensus process started",
                    body=f"Task: {task[:100]}",
                    severity=NotificationSeverity.INFO,
                    source="consensus_engine",
                    data={"task": task},
                )

                session = await engine.run_consensus(task)

                for i, round_data in enumerate(session.rounds):
                    round_msg = {
                        "type": "consensus_round",
                        "round": round_data.round_number,
                        "proposals": list(round_data.proposals.values()),
                        "critiques": list(round_data.critiques.values()),
                        "refinements": list(round_data.refinements.values()),
                        "scores": round_data.scores,
                        "convergence_score": round_data.convergence_score,
                        "polarity_balance": round_data.polarity_balance,
                    }
                    await manager.send_to(client_id, round_msg)

                    await notification_manager.notify(
                        type=NotificationType.CONSENSUS_ROUND,
                        title=f"Round {round_data.round_number} completed",
                        body=f"Convergence: {round_data.convergence_score:.2f}",
                        severity=NotificationSeverity.INFO,
                        source="consensus_engine",
                        session_id=session.id,
                        data={"round": round_data.round_number, "convergence": round_data.convergence_score},
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
        logger.info(f"WebSocket client disconnected normally", client_id=client_id)
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON from WebSocket client", client_id=client_id)
    except Exception as e:
        logger.error(f"WebSocket error", client_id=client_id, error=str(e))
    finally:
        manager.disconnect(client_id)
