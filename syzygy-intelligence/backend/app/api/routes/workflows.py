"""Workflow API routes — usage-gated."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import check_usage_limit, require_user
from app.db.models import User
from app.db.session import get_db
from app.workflows import WORKFLOW_REGISTRY, get_workflow

router = APIRouter()


@router.get("/")
async def list_workflows():
    return {
        "workflows": [
            {"name": w.name, "description": w.description}
            for w in WORKFLOW_REGISTRY.values()
        ]
    }


@router.post("/{workflow_name}/execute")
async def execute_workflow(
    workflow_name: str,
    data: dict,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    workflow = get_workflow(workflow_name)
    if not workflow:
        raise HTTPException(404, f"Workflow '{workflow_name}' not found")

    await check_usage_limit(user, db)

    result = await workflow.execute(
        task=data.get("task", ""),
        context=data.get("context", {}),
    )

    user.message_count += 1
    db.add(user)
    await db.commit()

    return {"workflow": workflow_name, "result": result}
