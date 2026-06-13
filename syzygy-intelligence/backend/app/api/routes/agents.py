"""Agent management API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.agents.registry import agent_registry
from app.logging_setup import logger

router = APIRouter()


@router.get("/")
async def list_agents() -> dict[str, Any]:
    try:
        agents = agent_registry.list_agents()
        return {"agents": [a.to_dict() for a in agents]}
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list agents")


@router.post("/")
async def create_agent(data: dict[str, Any]) -> dict[str, Any]:
    try:
        agent = agent_registry.create_agent(
            archetype_key=data.get("archetype", "sage"),
            name=data.get("name", ""),
            model=data.get("model", ""),
            shadow_active=data.get("shadow_active", False),
        )
        return {"agent": agent.to_dict()}
    except Exception as e:
        logger.error("Failed to create agent", error=str(e), archetype=data.get("archetype"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create agent")


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    try:
        agent = agent_registry.get(agent_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
        return {"agent": agent.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get agent")


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> dict[str, Any]:
    try:
        if agent_registry.remove(agent_id):
            return {"status": "deleted"}
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete agent", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete agent")


@router.post("/compose")
async def compose_team() -> dict[str, Any]:
    try:
        agent_registry.clear()
        team = agent_registry.create_default_team()
        return {"agents": [a.to_dict() for a in team]}
    except Exception as e:
        logger.error("Failed to compose team", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to compose team")


@router.post("/{agent_id}/shadow/toggle")
async def toggle_shadow(agent_id: str) -> dict[str, Any]:
    try:
        agent = agent_registry.get(agent_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
        if agent.shadow_active:
            agent.deactivate_shadow()
        else:
            agent.activate_shadow()
        return {"agent_id": agent_id, "shadow_active": agent.shadow_active}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to toggle shadow", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to toggle shadow")
