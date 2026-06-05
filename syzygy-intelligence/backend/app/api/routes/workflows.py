"""Workflow API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

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
async def execute_workflow(workflow_name: str, data: dict):
    workflow = get_workflow(workflow_name)
    if not workflow:
        raise HTTPException(404, f"Workflow '{workflow_name}' not found")

    result = await workflow.execute(
        task=data.get("task", ""),
        context=data.get("context", {}),
    )
    return {"workflow": workflow_name, "result": result}
