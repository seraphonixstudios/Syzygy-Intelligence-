"""Git tool — perform git operations programmatically."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GitTool:
    name: str = "git"
    description: str = "Git operations: clone, commit, push, status, diff, log"

    async def execute(
        self,
        action: str = "status",
        repo_path: str = ".",
        message: str = "",
        url: str = "",
        branch: str = "",
    ) -> dict[str, Any]:
        import subprocess

        def run_git(*args: str) -> str:
            result = subprocess.run(
                ["git"] + list(args),
                capture_output=True,
                text=True,
                cwd=repo_path,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip())
            return result.stdout.strip()

        try:
            if action == "status":
                output = run_git("status")
                return {"status": output}

            elif action == "diff":
                output = run_git("diff")
                return {"diff": output}

            elif action == "log":
                count = 10
                output = run_git("log", f"--max-count={count}", "--oneline")
                return {"log": output.split("\n") if output else []}

            elif action == "commit":
                run_git("add", "-A")
                run_git("commit", "-m", message)
                return {"committed": True, "message": message}

            elif action == "clone":
                run_git("clone", url, repo_path)
                return {"cloned": True, "url": url, "path": repo_path}

            elif action == "branch":
                output = run_git("branch")
                return {"branches": output.split("\n")}

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}
