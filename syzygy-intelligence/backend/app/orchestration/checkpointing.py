"""Checkpointing for LangGraph persistence and time-travel debugging."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import settings


class CheckpointManager:
    """Manages LangGraph checkpoint persistence for time-travel debugging."""

    def __init__(self):
        self.storage_path = Path(f"{settings.data_dir}/checkpoints")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def save_checkpoint(
        self,
        session_id: str,
        round_number: int,
        state: dict[str, Any],
        metadata: dict[str, Any] = None,
    ) -> str:
        """Save a checkpoint at a given state."""
        checkpoint_id = str(uuid.uuid4())
        checkpoint = {
            "id": checkpoint_id,
            "session_id": session_id,
            "round_number": round_number,
            "state": state,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        path = self.storage_path / session_id
        path.mkdir(parents=True, exist_ok=True)
        (path / f"round_{round_number}_{checkpoint_id[:8]}.json").write_text(
            json.dumps(checkpoint, indent=2)
        )

        return checkpoint_id

    async def load_checkpoint(
        self,
        session_id: str,
        round_number: int,
    ) -> Optional[dict[str, Any]]:
        """Load the latest checkpoint for a session at a given round."""
        path = self.storage_path / session_id
        if not path.exists():
            return None

        checkpoints = sorted(path.glob(f"round_{round_number}_*.json"))
        if not checkpoints:
            return None

        return json.loads(checkpoints[-1].read_text())

    async def list_checkpoints(self, session_id: str) -> list[dict[str, Any]]:
        """List all checkpoints for a session."""
        path = self.storage_path / session_id
        if not path.exists():
            return []

        checkpoints = []
        for f in sorted(path.glob("*.json")):
            data = json.loads(f.read_text())
            checkpoints.append({
                "id": data["id"],
                "round_number": data["round_number"],
                "timestamp": data["timestamp"],
                "metadata": data.get("metadata", {}),
            })

        return checkpoints

    async def replay_to_round(
        self,
        session_id: str,
        target_round: int,
    ) -> Optional[dict[str, Any]]:
        """Replay to a specific round (time-travel debugging)."""
        return await self.load_checkpoint(session_id, target_round)
