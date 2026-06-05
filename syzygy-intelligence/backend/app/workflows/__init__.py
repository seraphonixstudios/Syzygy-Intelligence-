"""Workflow definitions for Syzygy — task decomposition, parallel execution, priority queuing."""

from __future__ import annotations

from typing import Any

from app.workflows.coding import CodingWorkflow, CODING_WORKFLOW
from app.workflows.research import ResearchWorkflow, RESEARCH_WORKFLOW
from app.workflows.content import ContentWorkflow, CONTENT_WORKFLOW
from app.workflows.debate import DebateWorkflow, DEBATE_WORKFLOW
from app.workflows.task_decomposition import TaskDecompositionWorkflow, TASK_DECOMPOSITION_WORKFLOW


WORKFLOW_REGISTRY: dict[str, Any] = {
    "coding": CODING_WORKFLOW,
    "research": RESEARCH_WORKFLOW,
    "content": CONTENT_WORKFLOW,
    "debate": DEBATE_WORKFLOW,
    "task_decomposition": TASK_DECOMPOSITION_WORKFLOW,
}


def get_workflow(name: str):
    return WORKFLOW_REGISTRY.get(name)


__all__ = [
    "WORKFLOW_REGISTRY", "get_workflow",
    "CodingWorkflow", "ResearchWorkflow",
    "ContentWorkflow", "DebateWorkflow",
    "TaskDecompositionWorkflow",
]
