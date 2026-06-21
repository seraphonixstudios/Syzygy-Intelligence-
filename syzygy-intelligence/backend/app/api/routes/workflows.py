"""Workflow API routes — usage-gated."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import check_usage_limit, require_user
from app.db.models import User
from app.db.session import get_db
from app.logging_setup import logger
from app.workflows import WORKFLOW_REGISTRY, get_workflow

router = APIRouter()


@router.get("/")
async def list_workflows() -> dict[str, Any]:
    return {
        "workflows": [
            {"name": w.name, "description": w.description}
            for w in WORKFLOW_REGISTRY.values()
        ]
    }


@router.post("/{workflow_name}/execute")
async def execute_workflow(
    workflow_name: str,
    data: dict[str, Any],
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        workflow = get_workflow(workflow_name)
        if not workflow:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Workflow '{workflow_name}' not found")

        await check_usage_limit(user, db)

        result = await workflow.execute(
            task=data.get("task", ""),
            context=data.get("context", {}),
        )

        user.message_count += 1
        db.add(user)
        await db.commit()

        return {"workflow": workflow_name, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workflow execution failed", error=str(e), workflow=workflow_name, user_id=str(user.id))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow execution failed: {str(e)[:200]}")


@router.post("/{workflow_name}/execute/stream")
async def execute_workflow_stream(
    workflow_name: str,
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    try:
        workflow = get_workflow(workflow_name)
        if not workflow:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Workflow '{workflow_name}' not found")

        await check_usage_limit(user, db)

        data = await request.json()
        task = data.get("task", "")
        context = data.get("context", {})

        async def event_stream():
            queue: asyncio.Queue = asyncio.Queue()

            async def on_progress(step: str, pct: int, step_info: dict[str, Any]) -> None:
                await queue.put({"type": "progress", "step": step, "progress": pct, "reasoning": step_info})

            async def run_workflow() -> None:
                try:
                    result = await workflow.execute(task=task, context=context, on_progress=on_progress)
                    user.message_count += 1
                    db.add(user)
                    await db.commit()
                    await queue.put({"type": "complete", "result": {"workflow": workflow_name, "result": result}})
                except Exception as e:
                    await queue.put({"type": "error", "error": str(e)[:500]})

            asyncio.create_task(run_workflow())

            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] in ("complete", "error"):
                    break

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workflow stream execution failed", error=str(e), workflow=workflow_name, user_id=str(user.id))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow execution failed: {str(e)[:200]}")
