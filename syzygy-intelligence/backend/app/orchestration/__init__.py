"""Orchestration — team formation, task queue, checkpointing."""

from __future__ import annotations

from app.orchestration.team_formation import TeamFormation
from app.orchestration.task_queue import TaskQueue
from app.orchestration.checkpointing import CheckpointManager


class Orchestrator:
    """Central orchestrator for agent teams, task execution, and persistence."""

    def __init__(self):
        self.team_formation = TeamFormation()
        self.task_queue = TaskQueue()
        self.checkpoint_manager = CheckpointManager()


orchestrator = Orchestrator()
