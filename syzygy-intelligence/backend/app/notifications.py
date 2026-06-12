"""Notification and messaging system for Syzygy.

Provides:
- Event bus for inter-component messaging
- Push notifications to WebSocket clients
- Alert management with severity levels
- Message queuing for async delivery
"""

from __future__ import annotations

import inspect
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.audit import audit_service
from app.logging_setup import logger


class NotificationSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationType(StrEnum):
    CONSENSUS_STARTED = "consensus_started"
    CONSENSUS_ROUND = "consensus_round"
    CONSENSUS_COMPLETE = "consensus_complete"
    CONSENSUS_ERROR = "consensus_error"
    AGENT_ACTIVATED = "agent_activated"
    AGENT_DEACTIVATED = "agent_deactivated"
    AGENT_ERROR = "agent_error"
    SHADOW_ACTIVATED = "shadow_activated"
    MEMORY_STORED = "memory_stored"
    MEMORY_RECALLED = "memory_recalled"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    TOOL_EXECUTED = "tool_executed"
    TOOL_ERROR = "tool_error"
    SYSTEM = "system"
    USER_ACTION = "user_action"


@dataclass
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.SYSTEM
    severity: NotificationSeverity = NotificationSeverity.INFO
    title: str = ""
    body: str = ""
    source: str = ""
    target_agent_id: str = ""
    target_session_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "body": self.body,
            "source": self.source,
            "target_agent_id": self.target_agent_id,
            "target_session_id": self.target_session_id,
            "data": self.data,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class MessageBus:
    """Async event bus for internal component communication."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[..., Any]]] = {}
        self._history: list[Notification] = []
        self._max_history = 1000

    def subscribe(self, event_type: str, callback: Callable[..., Any]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[..., Any]) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb is not callback
            ]

    async def publish(self, notification: Notification) -> None:
        self._history.append(notification)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        callbacks = self._subscribers.get(notification.type.value, []) + \
                    self._subscribers.get("*", [])

        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}", notification_type=notification.type.value)

    def get_history(self, limit: int = 50) -> list[Notification]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()


class NotificationManager:
    """Manages notifications — creation, persistence, WebSocket broadcast."""

    def __init__(self, bus: MessageBus | None = None) -> None:
        self.bus = bus or MessageBus()
        self._ws_connections: dict[str, Any] = {}

    def register_ws(self, client_id: str, send_func: Callable[..., Any]) -> None:
        self._ws_connections[client_id] = send_func

    def unregister_ws(self, client_id: str) -> None:
        self._ws_connections.pop(client_id, None)

    async def notify(
        self,
        type: NotificationType,
        title: str,
        body: str = "",
        severity: NotificationSeverity = NotificationSeverity.INFO,
        source: str = "",
        agent_id: str = "",
        session_id: str = "",
        data: dict[str, Any] | None = None,
    ) -> Notification:
        notification = Notification(
            type=type,
            severity=severity,
            title=title,
            body=body,
            source=source,
            target_agent_id=agent_id,
            target_session_id=session_id,
            data=data or {},
        )

        await self.bus.publish(notification)

        # Log to audit
        await audit_service.log(
            event_type=type.value,
            action=title,
            agent_id=agent_id or None,
            session_id=session_id or None,
            details={"body": body, **notification.data},
        )

        # Broadcast to WebSocket clients
        payload = notification.to_dict()
        disconnected = []
        for cid, send in self._ws_connections.items():
            try:
                await send(payload)
            except Exception as e:
                logger.error(
                    f"Failed to send notification to client {cid}: {e}",
                    client_id=cid,
                    notification_id=notification.id,
                )
                disconnected.append(cid)
        for cid in disconnected:
            self.unregister_ws(cid)

        return notification


notification_manager = NotificationManager()
message_bus = notification_manager.bus
