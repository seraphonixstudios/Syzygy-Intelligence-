"""Multi-dimensional self-assessment engine for recursive improvement.

Provides comprehensive evaluation across quality dimensions with:
- Multi-layered rubrics (lexical, semantic, structural, pragmatic)
- Root cause analysis of performance gaps
- Domain-specific assessment strategies
- LLM-based scoring and diagnosis
- Adaptive thresholds based on domain and task complexity
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.agents.base import SyzygyAgent
from app.llm.model_manager import ModelManager
from app.logging_setup import logger


@dataclass
class AssessmentResult:
    """Complete assessment of output quality."""

    overall_score: float  # 0.0-1.0
    dimension_scores: dict[str, float] = field(default_factory=dict)  # accuracy, coherence, creativity, etc.
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    root_causes: dict[str, list[str]] = field(default_factory=dict)  # dimension -> causes
    recommendations: list[str] = field(default_factory=list)
    detailed_feedback: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)  # domain-specific metrics


class SelfAssessmentEngine:
    """Evaluates output quality using multi-dimensional rubrics and LLM analysis."""

    # Default assessment dimensions
    UNIVERSAL_DIMENSIONS = [
        "accuracy",       # factual correctness, logical soundness
        "coherence",      # internal consistency, structure
        "creativity",     # originality, novelty, insight
        "completeness",   # coverage of task requirements
        "clarity",        # communication effectiveness
    ]

    DOMAIN_DIMENSIONS = {
        "code": ["correctness", "efficiency", "maintainability", "safety", "testing"],
        "content": ["relevance", "engagement", "authority", "originality", "structure"],
        "research": ["rigor", "coverage", "insight", "novelty", "accuracy"],
        "analysis": ["depth", "rigor", "completeness", "clarity", "impact"],
    }

    # Scoring rubrics
    RUBRICS = {
        "accuracy": {
            "0.0-0.3": "Contains significant factual errors or logical flaws",
            "0.3-0.6": "Mix of correct and incorrect information; some logical gaps",
            "0.6-0.8": "Mostly accurate with minor errors; generally sound logic",
            "0.8-1.0": "Highly accurate; logically rigorous; verifiable claims",
        },
        "coherence": {
            "0.0-0.3": "Disorganized, contradictory, hard to follow",
            "0.3-0.6": "Some structure but inconsistencies and jumps in logic",
            "0.6-0.8": "Generally well-structured with minor inconsistencies",
            "0.8-1.0": "Cohesive, logically consistent, well-organized",
        },
        "creativity": {
            "0.0-0.3": "Purely derivative, no original thinking",
            "0.3-0.6": "Minor originality; mostly recombines existing ideas",
            "0.6-0.8": "Solid original contribution; some novel insights",
            "0.8-1.0": "Highly innovative; surprising insights; breaks new ground",
        },
        "completeness": {
            "0.0-0.3": "Incomplete; major gaps in coverage",
            "0.3-0.6": "Partial coverage; some important elements missing",
            "0.6-0.8": "Mostly complete; minor gaps or omissions",
            "0.8-1.0": "Comprehensive; all requirements addressed",
        },
        "clarity": {
            "0.0-0.3": "Unclear, difficult to understand",
            "0.3-0.6": "Generally understandable but sometimes unclear",
            "0.6-0.8": "Clear with minor ambiguities",
            "0.8-1.0": "Crystal clear; easily understood by target audience",
        },
    }

    def __init__(self, llm: ModelManager | None = None):
        self.llm = llm or ModelManager()

    async def assess(
        self,
        task: str,
        output: str,
        domain: str = "general",
        agents: list[SyzygyAgent] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AssessmentResult:
        """Run comprehensive multi-dimensional assessment."""

        logger.info("Starting self-assessment", task=task[:80], domain=domain)

        # Select assessment dimensions for this domain
        dimensions = self._get_dimensions(domain)

        # Get scores for each dimension
        dimension_scores = {}
        for dim in dimensions:
            score = await self._score_dimension(
                task=task,
                output=output,
                dimension=dim,
                domain=domain,
                agents=agents,
                context=context,
            )
            dimension_scores[dim] = score

        # Compute overall score (weighted average)
        overall_score = self._compute_overall(dimension_scores)

        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(dimension_scores)

        # Diagnose root causes of weaknesses
        root_causes = await self._diagnose_root_causes(
            task=task,
            output=output,
            weaknesses=weaknesses,
            agents=agents,
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            task=task,
            output=output,
            dimension_scores=dimension_scores,
            root_causes=root_causes,
        )

        # Collect domain-specific metrics
        metrics = await self._compute_metrics(
            output=output,
            domain=domain,
            task=task,
        )

        result = AssessmentResult(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            root_causes=root_causes,
            recommendations=recommendations,
            metrics=metrics,
        )

        logger.info(
            "Assessment complete",
            overall_score=overall_score,
            strengths_count=len(strengths),
            weaknesses_count=len(weaknesses),
        )

        return result

    def _get_dimensions(self, domain: str) -> list[str]:
        """Get assessment dimensions for a domain."""
        domain_dims = self.DOMAIN_DIMENSIONS.get(domain.lower(), [])
        return self.UNIVERSAL_DIMENSIONS + domain_dims

    async def _score_dimension(
        self,
        task: str,
        output: str,
        dimension: str,
        domain: str,
        agents: list[SyzygyAgent] | None = None,
        context: dict[str, Any] | None = None,
    ) -> float:
        """Score a single dimension using rubric-guided LLM evaluation."""

        rubric = self.RUBRICS.get(dimension, {})

        prompt = (
            f"Task: {task[:300]}\n\n"
            f"Domain: {domain}\n"
            f"Dimension to assess: {dimension}\n\n"
            f"Output to evaluate:\n{output[:1500]}\n\n"
            f"Assessment Rubric for '{dimension}':\n"
        )

        for range_key, description in rubric.items():
            prompt += f"  {range_key}: {description}\n"

        prompt += (
            f"\nBased on this rubric, score the output from 0.0 to 1.0 for '{dimension}'.\n"
            f"Return ONLY a number between 0.0 and 1.0 (e.g., 0.75).\n"
            f"Be critical and use the full range."
        )

        result = await self.llm.generate(prompt, temperature=0.3)

        # Parse score
        score = self._parse_score(result)
        logger.debug(f"Scored {dimension}: {score:.2f}")

        return score

    async def _diagnose_root_causes(
        self,
        task: str,
        output: str,
        weaknesses: list[str],
        agents: list[SyzygyAgent] | None = None,
    ) -> dict[str, list[str]]:
        """Identify root causes for each weakness."""

        root_causes = {}

        for weakness in weaknesses:
            prompt = (
                f"Task: {task[:300]}\n\n"
                f"Output weakness identified: {weakness}\n\n"
                f"Output excerpt:\n{output[:1000]}\n\n"
            )

            if agents:
                prompt += f"Agent team:\n" + "\n".join(
                    f"  • {a.name} ({a.archetype.name if a.archetype else '?'}, {a.polarity.value})"
                    for a in agents
                ) + "\n\n"

            prompt += (
                f"Identify ROOT CAUSES for this weakness. "
                f"Consider: agent capability gaps, consensus disagreement, "
                f"tool limitations, insufficient context, conflicting priorities.\n"
                f"Return a bulleted list of 2-3 specific root causes."
            )

            result = await self.llm.generate(prompt, temperature=0.3)
            causes = self._extract_bullets(result)
            root_causes[weakness] = causes

        return root_causes

    async def _generate_recommendations(
        self,
        task: str,
        output: str,
        dimension_scores: dict[str, float],
        root_causes: dict[str, list[str]],
    ) -> list[str]:
        """Generate actionable improvement recommendations."""

        # Find lowest-scoring dimensions
        worst_dims = sorted(dimension_scores.items(), key=lambda x: x[1])[:3]

        prompt = (
            f"Task: {task[:300]}\n\n"
            f"Assessment Results:\n"
            f"Lowest-scoring dimensions: {', '.join(f'{d[0]} ({d[1]:.2f})' for d in worst_dims)}\n\n"
            f"Output sample:\n{output[:800]}\n\n"
            f"Generate 3-4 specific, actionable recommendations to improve this output. "
            f"Each recommendation should target a low-scoring dimension and suggest concrete changes.\n"
            f"Return as a bulleted list."
        )

        result = await self.llm.generate(prompt, temperature=0.4)
        recommendations = self._extract_bullets(result)

        return recommendations

    async def _compute_metrics(
        self,
        output: str,
        domain: str,
        task: str,
    ) -> dict[str, Any]:
        """Compute domain-specific metrics."""

        metrics = {
            "length_tokens": len(output.split()),
            "length_chars": len(output),
        }

        # Domain-specific metrics
        if domain.lower() == "code":
            metrics["line_count"] = output.count("\n")
            metrics["has_comments"] = "# " in output or "/* " in output or "//" in output
            metrics["has_tests"] = "test" in output.lower() or "assert" in output

        elif domain.lower() == "content":
            metrics["section_count"] = output.count("\n##") + output.count("\n# ")
            metrics["has_examples"] = "example" in output.lower() or "e.g." in output
            metrics["readability_grade"] = self._estimate_readability(output)

        elif domain.lower() == "research":
            metrics["citation_count"] = len(re.findall(r"\[\d+\]", output))
            metrics["section_structure"] = "introduction" in output.lower() and "conclusion" in output.lower()

        return metrics

    def _identify_strengths_weaknesses(
        self,
        dimension_scores: dict[str, float],
    ) -> tuple[list[str], list[str]]:
        """Separate strong (>0.7) and weak (<0.6) dimensions."""

        strengths = [
            dim for dim, score in dimension_scores.items()
            if score >= 0.7
        ]
        weaknesses = [
            dim for dim, score in dimension_scores.items()
            if score < 0.6
        ]

        return strengths, weaknesses

    def _compute_overall(self, dimension_scores: dict[str, float]) -> float:
        """Compute weighted overall score."""

        if not dimension_scores:
            return 0.5

        # Equal weighting by default
        overall = sum(dimension_scores.values()) / len(dimension_scores)
        return round(overall, 4)

    def _parse_score(self, text: str) -> float:
        """Extract score from LLM response."""

        try:
            # Find all numbers in 0.X format (not preceded by minus)
            numbers = re.findall(r"(?<!-)0\.\d+", text)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(1.0, score))
        except (ValueError, IndexError):
            pass

        # Fallback: search for any decimal (including negatives)
        try:
            matches = re.findall(r"-?\d+\.?\d*", text)
            if matches:
                num = float(matches[0])
                if 0 <= num <= 100:
                    return num / 100.0
                elif 0 <= num <= 1:  # pragma: no cover (dead code, caught by 0-100 check above)
                    return num
                elif num > 100:
                    return 1.0
                elif num < 0:
                    return 0.0
        except (ValueError, IndexError):
            pass

        logger.warning(f"Could not parse score from: {text[:100]}")
        return 0.5

    def _extract_bullets(self, text: str) -> list[str]:
        """Extract bulleted items from LLM response."""

        # Try to find lines starting with •, -, *, or numbers
        lines = text.split("\n")
        bullets = []
        for line in lines:
            line = line.strip()
            if line and (line[0] in "•-*" or (len(line) > 2 and line[0].isdigit() and line[1] in ".)")):
                # Remove leading bullet markers
                cleaned = re.sub(r"^[•\-*\d.)\s]+", "", line).strip()
                if cleaned:
                    bullets.append(cleaned)

        return bullets if bullets else [text[:100]]

    def _estimate_readability(self, text: str) -> float:
        """Rough estimate of readability (0-1, higher=easier)."""

        sentences = text.split(".")
        words = text.split()

        if not sentences or not words:
            return 0.5

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Flesch-Kincaid inspired (simplified)
        grade = 0.39 * avg_sentence_length + 11.8 * (avg_word_length / 5) - 15.59

        # Convert to 0-1 scale (lower grade = higher readability)
        readability = max(0.0, min(1.0, 1.0 - (grade / 16.0)))

        return round(readability, 2)


__all__ = [
    "SelfAssessmentEngine",
    "AssessmentResult",
]
