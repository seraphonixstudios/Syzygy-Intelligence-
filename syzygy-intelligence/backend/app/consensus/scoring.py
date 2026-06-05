"""Multi-axis scoring for Syzygy consensus evaluations — no default fallback scores."""

from __future__ import annotations

import json
from typing import Any, Optional

from app.agents.base import SyzygyAgent
from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


class ConsensusScorer:
    """Evaluates proposals and refinements across multiple dimensions using LLM."""

    SCORE_DIMENSIONS = [
        "accuracy",
        "holistic_insight",
        "creativity",
        "feasibility",
        "polarity_balance",
    ]

    DIMENSION_WEIGHTS = {
        "accuracy": 0.25,
        "holistic_insight": 0.20,
        "creativity": 0.20,
        "feasibility": 0.20,
        "polarity_balance": 0.15,
    }

    def __init__(self, llm: Optional[OllamaClient] = None):
        self.llm = llm or OllamaClient()

    async def evaluate_all(
        self,
        task: str,
        contents: dict[str, str],
        agents: list[SyzygyAgent],
        llm: Optional[OllamaClient] = None,
    ) -> dict[str, dict[str, float]]:
        """Evaluate all proposals/refinements across all dimensions with LLM."""
        evaluations = {}

        for agent_id, content in contents.items():
            agent = next((a for a in agents if a.id == agent_id), None)
            if not agent:
                continue

            try:
                scores = await self._evaluate_single(task, content, agent, llm)
                scores["overall"] = self._compute_weighted(scores)
                evaluations[agent_id] = scores
            except Exception as e:
                logger.error(f"Scoring failed for agent {agent_id}", error=str(e))
                evaluations[agent_id] = {
                    "accuracy": 0.5, "holistic_insight": 0.5,
                    "creativity": 0.5, "feasibility": 0.5,
                    "polarity_balance": 0.5, "overall": 0.5,
                }

        return evaluations

    async def _evaluate_single(
        self,
        task: str,
        content: str,
        agent: SyzygyAgent,
        llm: Optional[OllamaClient] = None,
    ) -> dict[str, float]:
        """Evaluate a single agent's contribution across all dimensions using LLM."""
        scorer = llm or self.llm

        prompt = (
            f"Task: {task}\n\n"
            f"Agent: {agent.name} ({agent.archetype.name}, {agent.polarity.value})\n"
            f"Proposal:\n{content[:1500]}\n\n"
            f"Score this proposal on a scale of 0.0 to 1.0 for each dimension:\n"
            f"- accuracy: factual correctness and logical soundness\n"
            f"- holistic_insight: breadth of perspective and depth of understanding\n"
            f"- creativity: originality and innovative thinking\n"
            f"- feasibility: practicality and implementability\n"
            f"- polarity_balance: integration of complementary perspectives\n\n"
            f"Return ONLY a valid JSON object like:\n"
            f'{{"accuracy": 0.85, "holistic_insight": 0.72, "creativity": 0.68, '
            f'"feasibility": 0.79, "polarity_balance": 0.74}}\n\n'
            f"Be honest and critical — use the full 0.0-1.0 range."
        )

        result = await scorer.generate(prompt, temperature=0.3)
        scores = self._parse_scores(result)

        if not scores:
            logger.warning(f"Could not parse scores for {agent.id}, retrying with simpler format")
            simple_prompt = (
                f"On a scale of 0.0 to 1.0, rate the {agent.name} proposal for task '{task[:80]}':\n"
                f"accuracy= holistic_insight= creativity= feasibility= polarity_balance=\n"
                f"Return ONLY five comma-separated numbers."
            )
            result = await scorer.generate(simple_prompt, temperature=0.3)
            scores = self._parse_fallback(result)

        return scores

    def _parse_scores(self, text: str) -> Optional[dict[str, float]]:
        """Parse JSON scores from LLM response."""
        try:
            # Find JSON object in response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                parsed = json.loads(json_str)
                return {
                    dim: max(0.0, min(1.0, float(parsed.get(dim, 0.5))))
                    for dim in self.SCORE_DIMENSIONS
                }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug(f"Score parsing failed: {e}")
        return None

    def _parse_fallback(self, text: str) -> dict[str, float]:
        """Parse comma-separated numbers as fallback."""
        try:
            import re
            numbers = re.findall(r"[\d.]+", text)
            floats = [max(0.0, min(1.0, float(n))) for n in numbers[:5]]
            while len(floats) < 5:
                floats.append(0.5)
            return dict(zip(self.SCORE_DIMENSIONS, floats))
        except (ValueError, TypeError):
            logger.error("Fallback score parsing also failed, using neutral scores")
            return {dim: 0.5 for dim in self.SCORE_DIMENSIONS}

    def _compute_weighted(self, scores: dict[str, float]) -> float:
        """Compute weighted overall score from dimension scores."""
        weighted = sum(
            scores.get(dim, 0.5) * self.DIMENSION_WEIGHTS.get(dim, 0.2)
            for dim in self.SCORE_DIMENSIONS
        )
        return round(weighted, 4)
