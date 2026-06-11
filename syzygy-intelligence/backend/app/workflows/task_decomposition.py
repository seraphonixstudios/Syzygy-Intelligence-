"""Task decomposition — breaks complex tasks into subtasks with LLM-powered analysis."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class Subtask:
    id: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    agent_archetype: str = "sage"
    polarity: str = "unified"
    priority: int = 0
    status: str = "pending"
    estimated_complexity: float = 0.5
    result: str = ""


@dataclass
class TaskDecompositionWorkflow:
    """Decomposes complex tasks into subtasks with dependency tracking using LLM."""

    name: str = "task_decomposition"
    description: str = "Break complex tasks into manageable subtasks with dependency analysis"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["analysis", "planning"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

    async def decompose(self, task: str, context: dict[str, Any] = None) -> list[Subtask]:
        prompt = (
            f"Decompose the following complex task into manageable subtasks:\n\n"
            f"Task: {task}\n\n"
            f"For each subtask, provide:\n"
            f"1. A unique ID (e.g., 'research_1', 'implement_2')\n"
            f"2. Description (one sentence)\n"
            f"3. Dependencies (list of subtask IDs it depends on)\n"
            f"4. Recommended agent archetype (choose from: sage, hero, ruler, magician, explorer, "
            f"great_mother, lover, innocent, creator, anima, self, hermes, trickster)\n"
            f"5. Polarity (masculine, feminine, or unified)\n"
            f"6. Priority (1-5, where 5 is highest)\n\n"
            f"Return the decomposition in this format (one per line):\n"
            f"SUBTASK: id | description | deps(semicolon-sep) | archetype | polarity | priority"
        )
        result = await self.llm.generate(prompt, temperature=0.3)
        subtasks = self._parse_subtasks(result)
        if not subtasks:
            subtasks = self._get_fallback_subtasks(task)
        subtasks.sort(key=lambda s: (-s.priority, len(s.dependencies)))
        logger.info("Task decomposed", task=task[:80], subtask_count=len(subtasks))
        return subtasks

    def _parse_subtasks(self, text: str) -> list[Subtask]:
        subtasks = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line.startswith("SUBTASK:"):
                continue
            try:
                parts = line[8:].strip().split(" | ")
                if len(parts) >= 6:
                    subtasks.append(Subtask(
                        id=parts[0].strip(),
                        description=parts[1].strip(),
                        dependencies=[d.strip() for d in parts[2].split(";") if d.strip()],
                        agent_archetype=parts[3].strip(),
                        polarity=parts[4].strip(),
                        priority=int(parts[5].strip()),
                    ))
            except (IndexError, ValueError) as e:
                logger.warning(f"Failed to parse subtask: {line[:50]}, error: {e}")
        return subtasks

    def _get_fallback_subtasks(self, task: str) -> list[Subtask]:
        return [
            Subtask(id="analysis_1", description=f"Analyze requirements for: {task[:100]}",
                    agent_archetype="sage", polarity="masculine", priority=1),
            Subtask(id="research_1", description="Gather relevant information",
                    dependencies=["analysis_1"], agent_archetype="sage", polarity="masculine", priority=2),
            Subtask(id="creative_1", description="Generate approaches and solutions",
                    dependencies=["research_1"], agent_archetype="creator", polarity="feminine", priority=3),
            Subtask(id="development_1", description="Execute the primary work",
                    dependencies=["creative_1"], agent_archetype="hero", polarity="masculine", priority=4),
            Subtask(id="review_1", description="Review and refine the output",
                    dependencies=["development_1"], agent_archetype="trickster", polarity="unified", priority=4),
            Subtask(id="synthesis_1", description="Synthesize final output with balanced perspective",
                    dependencies=["analysis_1", "research_1", "creative_1", "development_1", "review_1"],
                    agent_archetype="self", polarity="unified", priority=5),
        ]

    async def execute(
        self,
        task: str,
        context: dict[str, Any] = None,
        on_subtask_complete: Callable | None = None,
    ) -> list[Subtask]:
        subtasks = await self.decompose(task, context)
        completed = set()
        for i, subtask in enumerate(subtasks):
            deps_met = all(d in completed for d in subtask.dependencies)
            if deps_met:
                subtask.status = "in_progress"
                prompt = (
                    f"Task: {subtask.description}\n"
                    f"Main project: {task[:200]}\n"
                    f"Agent archetype: {subtask.agent_archetype}\n"
                    f"Polarity: {subtask.polarity}\n\n"
                    f"Provide a brief output for this subtask."
                )
                result = await self.llm.generate(prompt, temperature=0.3)
                subtask.result = result
                subtask.status = "completed"
                completed.add(subtask.id)
                if on_subtask_complete:
                    await on_subtask_complete(subtask)
        return subtasks


TASK_DECOMPOSITION_WORKFLOW = TaskDecompositionWorkflow()
