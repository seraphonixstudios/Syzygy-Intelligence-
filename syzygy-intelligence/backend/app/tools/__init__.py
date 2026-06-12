"""Syzygy Tool System — rich tool ecosystem for agents."""

from __future__ import annotations

from typing import Any

from app.tools.browser import BrowserTool
from app.tools.code_execution import CodeExecutionTool
from app.tools.filesystem import FileSystemTool
from app.tools.git_tool import GitTool
from app.tools.search import SearchTool


class ToolRegistry:
    """Central registry of all tools available to agents."""

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {
            "browser": BrowserTool(),
            "filesystem": FileSystemTool(),
            "git": GitTool(),
            "code_execution": CodeExecutionTool(),
            "search": SearchTool(),
        }

    def get(self, name: str) -> Any:
        return self._tools.get(name)

    def list(self) -> list[dict[str, Any]]:
        return [
            {"id": k, "name": v.name, "description": v.description}
            for k, v in self._tools.items()
        ]

    async def execute(self, tool_id: str, params: dict[str, Any]) -> dict[str, Any]:
        tool = self.get(tool_id)
        if not tool:
            return {"error": f"Tool '{tool_id}' not found"}
        return await tool.execute(**params)  # type: ignore


tool_registry = ToolRegistry()
