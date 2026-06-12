"""Tools API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"id": "browser", "name": "Web Browser", "description": "Browse and scrape web pages"},
            {"id": "filesystem", "name": "File System", "description": "Read and write files"},
            {"id": "git", "name": "Git", "description": "Git operations"},
            {"id": "code_execution", "name": "Code Execution", "description": "Run code in sandbox"},
            {"id": "search", "name": "Web Search", "description": "Search the web"},
        ]
    }


@router.post("/execute")
async def execute_tool(data: dict[str, Any]) -> dict[str, Any]:
    tool_id = data.get("tool_id", "")
    params = data.get("params", {})
    return {
        "tool_id": tool_id,
        "result": f"Executed {tool_id} with params: {params}",
        "status": "completed",
    }
