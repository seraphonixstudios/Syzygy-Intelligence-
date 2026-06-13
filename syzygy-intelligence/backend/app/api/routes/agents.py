"""Agent management API routes — primary and shadow agents."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.agents.registry import agent_registry
from app.logging_setup import logger

router = APIRouter()


# ── Primary agents ──────────────────────────────────────────


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


# ── Shadow agents ───────────────────────────────────────────


@router.get("/shadow/list")
async def list_shadow_agents(
    parent_archetype: str | None = None,
) -> dict[str, Any]:
    try:
        agents = agent_registry.list_shadow_agents(parent_archetype)
        return {"shadow_agents": [a.to_dict() for a in agents]}
    except Exception as e:
        logger.error("Failed to list shadow agents", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list shadow agents")


@router.post("/shadow/create")
async def create_shadow_agent(data: dict[str, Any]) -> dict[str, Any]:
    try:
        agent = agent_registry.create_shadow_agent(
            parent_archetype_key=data.get("parent_archetype", "sage"),
            name=data.get("name", ""),
            model=data.get("model", ""),
            alignment_score=data.get("alignment_score", 0.5),
        )
        return {"shadow_agent": agent.to_dict()}
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        logger.error("Failed to create shadow agent", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create shadow agent")


@router.get("/shadow/{shadow_id}")
async def get_shadow_agent(shadow_id: str) -> dict[str, Any]:
    try:
        agent = agent_registry.get_shadow(shadow_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shadow agent not found")
        return {"shadow_agent": agent.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get shadow agent", error=str(e), shadow_id=shadow_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get shadow agent")


@router.delete("/shadow/{shadow_id}")
async def delete_shadow_agent(shadow_id: str) -> dict[str, Any]:
    try:
        if agent_registry.remove_shadow(shadow_id):
            return {"status": "deleted"}
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shadow agent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete shadow agent", error=str(e), shadow_id=shadow_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete shadow agent")


@router.post("/shadow/{shadow_id}/align")
async def align_shadow_agent(
    shadow_id: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Increase a shadow agent's alignment score."""
    try:
        agent = agent_registry.get_shadow(shadow_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shadow agent not found")
        delta = data.get("delta", 0.1) if data else 0.1
        new_score = agent.align(delta)
        return {
            "shadow_agent_id": shadow_id,
            "alignment_score": round(new_score, 2),
            "delta": delta,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to align shadow agent", error=str(e), shadow_id=shadow_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to align shadow agent")


@router.post("/shadow/{shadow_id}/misalign")
async def misalign_shadow_agent(
    shadow_id: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decrease a shadow agent's alignment score."""
    try:
        agent = agent_registry.get_shadow(shadow_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shadow agent not found")
        delta = data.get("delta", 0.1) if data else 0.1
        new_score = agent.misalign(delta)
        return {
            "shadow_agent_id": shadow_id,
            "alignment_score": round(new_score, 2),
            "delta": delta,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to misalign shadow agent", error=str(e), shadow_id=shadow_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to misalign shadow agent")


@router.post("/shadow/{shadow_id}/integrate/{parent_id}")
async def integrate_shadow_agent(
    shadow_id: str,
    parent_id: str,
) -> dict[str, Any]:
    """Integrate shadow insights back to the parent agent."""
    try:
        shadow = agent_registry.get_shadow(shadow_id)
        if not shadow:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shadow agent not found")
        parent = agent_registry.get(parent_id)
        if not parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent agent not found")

        report = shadow.integrate(parent)
        return {
            "integration_report": {
                "parent_agent_id": report.parent_agent_id,
                "shadow_agent_id": report.shadow_agent_id,
                "insights": report.insights,
                "alignment_delta": report.alignment_delta,
                "new_alignment_score": report.new_alignment_score,
                "timestamp": report.timestamp,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to integrate shadow", error=str(e), shadow_id=shadow_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to integrate shadow")


@router.post("/shadow/compose")
async def compose_shadow_team() -> dict[str, Any]:
    try:
        agent_registry.clear_shadows()
        team = agent_registry.create_shadow_balanced_team()
        return {"shadow_agents": [a.to_dict() for a in team]}
    except Exception as e:
        logger.error("Failed to compose shadow team", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to compose shadow team")
