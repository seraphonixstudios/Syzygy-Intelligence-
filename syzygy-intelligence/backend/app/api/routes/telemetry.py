"""Telemetry endpoint — receives frontend observability events."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.logging_setup import logger

router = APIRouter()


@router.post("/api/telemetry")
async def receive_telemetry(request: Request) -> dict[str, str]:
    """Receive batched telemetry events from the frontend."""
    try:
        body = await request.json()
        events: list[dict[str, Any]] = body.get("events", [])

        for event in events:
            event_type = event.get("type", "unknown")
            name = event.get("name", "")
            duration = event.get("duration")
            status = event.get("status")

            log_data: dict[str, Any] = {
                "telemetry_type": event_type,
                "event_name": name,
            }
            if duration is not None:
                log_data["duration_ms"] = int(duration)
            if status is not None:
                log_data["status"] = status

            if event_type == "error":
                logger.warning(f"Frontend error: {name}", **log_data)
            elif event_type == "api_call":
                logger.info(f"Frontend API call: {name}", **log_data)
            elif event_type == "page_view":
                logger.info(f"Frontend page view: {name}", **log_data)
            elif event_type == "web_vital":
                logger.info(f"Frontend Web Vital: {name}", **log_data)
            else:
                logger.debug(f"Frontend telemetry: {event_type}/{name}", **log_data)

        return {"status": "ok", "count": str(len(events))}
    except Exception as e:
        logger.warning("Failed to process telemetry", error=str(e))
        return {"status": "error", "count": "0"}
