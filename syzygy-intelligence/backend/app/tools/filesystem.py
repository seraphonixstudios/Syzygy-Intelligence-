"""File system tool — read, write, list files and directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FileSystemTool:
    name: str = "filesystem"
    description: str = "Read, write, list, and manage files and directories"

    async def execute(
        self,
        action: str = "read",
        path: str = "",
        content: str = "",
        pattern: str = "",
    ) -> dict[str, Any]:
        try:
            p = Path(path)

            if action == "read":
                if not p.exists():
                    return {"error": f"Path not found: {path}"}
                if p.is_file():
                    return {"content": p.read_text(encoding="utf-8"), "path": path}
                else:
                    items = [str(x.relative_to(p)) for x in p.iterdir()]
                    return {"directory": path, "items": items}

            elif action == "write":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return {"status": "written", "path": path, "size": len(content)}

            elif action == "list":
                if not p.exists():
                    return {"error": f"Path not found: {path}"}
                items = []
                for x in p.iterdir():
                    items.append({
                        "name": x.name,
                        "type": "directory" if x.is_dir() else "file",
                        "size": x.stat().st_size if x.is_file() else 0,
                    })
                return {"path": path, "items": items}

            elif action == "delete":
                if p.exists():
                    if p.is_file():
                        p.unlink()
                    elif p.is_dir():
                        import shutil
                        shutil.rmtree(p)
                    return {"status": "deleted", "path": path}
                return {"error": f"Path not found: {path}"}

            return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}
