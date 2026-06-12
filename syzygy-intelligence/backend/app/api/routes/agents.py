"""Agent management API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.registry import agent_registry

router = APIRouter()


@router.get("/")
async def list_agents() -> dict[str, Any]:
    agents = agent_registry.list_agents()
    return {"agents": [a.to_dict() for a in agents]}


@router.post("/")
async def create_agent(data: dict[str, Any]) -> dict[str, Any]:
    agent = agent_registry.create_agent(
        archetype_key=data.get("archetype", "sage"),
        name=data.get("name", ""),
        model=data.get("model", ""),
        shadow_active=data.get("shadow_active", False),
    )
    return {"agent": agent.to_dict()}


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return {"agent": agent.to_dict()}


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> dict[str, Any]:
    if agent_registry.remove(agent_id):
        return {"status": "deleted"}
    raise HTTPException(404, "Agent not found")


@router.post("/compose")
async def compose_team() -> dict[str, Any]:
    agent_registry.clear()
    team = agent_registry.create_default_team()
    return {"agents": [a.to_dict() for a in team]}


@router.post("/{agent_id}/shadow/toggle")
async def toggle_shadow(agent_id: str) -> dict[str, Any]:
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent.shadow_active:
        agent.deactivate_shadow()
    else:
        agent.activate_shadow()
    return {"agent_id": agent_id, "shadow_active": agent.shadow_active}
