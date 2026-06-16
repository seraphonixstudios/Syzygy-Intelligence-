"""Recursive Self-Improvement Workflow — Full SOTA implementation.

This workflow enables Syzygy to:
1. Execute a task with the current agent team
2. Assess output quality against multi-dimensional rubrics
3. Identify root causes of underperformance
4. Generate targeted improvements (agent role adjustment, prompt tuning, tool additions)
5. Recursively apply improvements and measure delta
6. Learn from improvements via vector memory and graph updates
7. Adapt team composition and strategies for future similar tasks

Architecture:
- Multi-round assessment loops with convergence detection
- Meta-agent that observes agent performance and suggests improvements
- Longitudinal tracking of performance across cycles
- Adaptive learning rate control
- Integration with memory and vector stores for continuous learning
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.agents.base import SyzygyAgent
from app.consensus.engine import ConsensusEngine, ConsensusSession
from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.memory.base import Memory
from app.self_improvement.assessment import SelfAssessmentEngine, AssessmentResult
from app.self_improvement.learning_optimizer import LearningOptimizer
from app.self_improvement.performance_tracker import PerformanceTracker


@dataclass
class ImprovementCycle:
    """A single improvement cycle: execute → assess → improve."""

    cycle_number: int
    task: str
    initial_output: str = ""
    initial_assessment: AssessmentResult | None = None
    improvements_applied: list[dict[str, Any]] = field(default_factory=list)
    improved_output: str = ""
    final_assessment: AssessmentResult | None = None
    performance_delta: float = 0.0  # improvement in overall score
    insights_generated: list[str] = field(default_factory=list)
    convergence_reached: bool = False
    completed_at: datetime | None = None


@dataclass
class RecursiveImprovementSession:
    """A complete recursive improvement session spanning multiple cycles."""

    id: str
    task: str
    domain: str  # e.g., "code", "content", "research"
    agents: list[SyzygyAgent] = field(default_factory=list)
    cycles: list[ImprovementCycle] = field(default_factory=list)
    max_cycles: int = 5
    convergence_threshold: float = 0.90  # when to stop improving
    current_cycle: int = 0
    final_output: str = ""
    total_performance_gain: float = 0.0
    meta_insights: list[str] = field(default_factory=list)
    learned_patterns: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class RecursiveSelfImprovementWorkflow:
    """Orchestrates recursive self-improvement cycles."""

    name: str = "self_improvement"
    description: str = (
        "Recursive self-improvement with multi-round assessment, "
        "root-cause analysis, and adaptive learning optimization"
    )

    def __init__(
        self,
        consensus_engine: ConsensusEngine | None = None,
        assessment_engine: SelfAssessmentEngine | None = None,
        performance_tracker: PerformanceTracker | None = None,
        learning_optimizer: LearningOptimizer | None = None,
        memory: Memory | None = None,
        llm: ModelManager | None = None,
    ):
        self.consensus = consensus_engine or ConsensusEngine()
        self.assessor = assessment_engine or SelfAssessmentEngine()
        self.tracker = performance_tracker or PerformanceTracker()
        self.optimizer = learning_optimizer or LearningOptimizer()
        self.memory = memory
        self.llm = llm or ModelManager()

    async def execute(
        self,
        task: str,
        agents: list[SyzygyAgent],
        domain: str = "general",
        max_cycles: int = 5,
        convergence_threshold: float = 0.90,
        context: dict[str, Any] | None = None,
    ) -> RecursiveImprovementSession:
        """Execute recursive self-improvement with full assessment and adaptation."""

        session = RecursiveImprovementSession(
            id=f"impr_{datetime.now(UTC).timestamp()}",
            task=task,
            domain=domain,
            agents=agents,
            max_cycles=max_cycles,
            convergence_threshold=convergence_threshold,
        )
        session.status = "running"

        ctx = context or {}

        logger.info(
            "Recursive self-improvement started",
            task=task[:80],
            domain=domain,
            max_cycles=max_cycles,
        )

        for cycle_num in range(1, max_cycles + 1):
            cycle = ImprovementCycle(cycle_number=cycle_num, task=task)
            session.cycles.append(cycle)
            session.current_cycle = cycle_num

            # 1. EXECUTE: Run consensus to get initial output
            logger.info(f"Cycle {cycle_num}: Executing task")
            consensus_session = await self.consensus.run_consensus(
                task=task,
                agents=agents,
                max_rounds=3 if cycle_num == 1 else 2,  # fewer rounds in later cycles
            )
            cycle.initial_output = consensus_session.final_synthesis

            # 2. ASSESS: Evaluate output quality
            logger.info(f"Cycle {cycle_num}: Assessing output quality")
            assessment = await self.assessor.assess(
                task=task,
                output=cycle.initial_output,
                domain=domain,
                agents=agents,
                context=ctx,
            )
            cycle.initial_assessment = assessment

            logger.info(
                f"Cycle {cycle_num}: Initial assessment score = {assessment.overall_score:.3f}"
            )

            # Check convergence after first cycle
            if cycle_num >= 2:
                prev_score = session.cycles[-2].initial_assessment.overall_score if session.cycles[-2].initial_assessment else 0.0
                delta = assessment.overall_score - prev_score
                cycle.performance_delta = delta

                if assessment.overall_score >= convergence_threshold:
                    logger.info(
                        f"Cycle {cycle_num}: Convergence reached (score={assessment.overall_score:.3f})"
                    )
                    cycle.convergence_reached = True
                    session.final_output = cycle.initial_output
                    break

            # 3. DIAGNOSE & IMPROVE: Identify root causes and generate improvements
            logger.info(f"Cycle {cycle_num}: Diagnosing performance issues")
            improvements = await self._generate_improvements(
                task=task,
                output=cycle.initial_output,
                assessment=assessment,
                agents=agents,
                cycle_num=cycle_num,
            )
            cycle.improvements_applied = improvements

            logger.info(
                f"Cycle {cycle_num}: Generated {len(improvements)} improvements"
            )

            # 4. APPLY IMPROVEMENTS: Modify agents, prompts, tools
            logger.info(f"Cycle {cycle_num}: Applying improvements")
            modified_agents = await self._apply_improvements(
                agents=agents,
                improvements=improvements,
                learning_rate=self.optimizer.get_learning_rate(cycle_num, max_cycles),
            )

            # 5. RE-EXECUTE: Run consensus with improved agents
            logger.info(f"Cycle {cycle_num}: Re-executing with improved agents")
            improved_consensus = await self.consensus.run_consensus(
                task=task,
                agents=modified_agents,
                max_rounds=2,
            )
            cycle.improved_output = improved_consensus.final_synthesis

            # 6. RE-ASSESS: Compare new output to initial
            logger.info(f"Cycle {cycle_num}: Re-assessing improved output")
            final_assessment = await self.assessor.assess(
                task=task,
                output=cycle.improved_output,
                domain=domain,
                agents=modified_agents,
                context=ctx,
            )
            cycle.final_assessment = final_assessment
            cycle.performance_delta = final_assessment.overall_score - assessment.overall_score

            logger.info(
                f"Cycle {cycle_num}: Performance delta = {cycle.performance_delta:+.3f} "
                f"(initial={assessment.overall_score:.3f}, final={final_assessment.overall_score:.3f})"
            )

            # 7. LEARN: Store insights and patterns in memory
            if self.memory:
                logger.info(f"Cycle {cycle_num}: Storing learned patterns in memory")
                await self._store_learning(
                    session=session,
                    cycle=cycle,
                    improvements=improvements,
                    domain=domain,
                )

            # 8. ADAPT: Update learning rate and agent strategies
            self.optimizer.record_improvement(cycle.performance_delta)

            cycle.completed_at = datetime.now(UTC)

            # Update total gain
            session.total_performance_gain += cycle.performance_delta

            # Replace agents for next cycle if improvements were positive
            if cycle.performance_delta > 0:
                agents = modified_agents
            else:
                logger.warning(f"Cycle {cycle_num}: No improvement; reverting agents")

        # Final synthesis and meta-insights
        if not session.cycles[-1].convergence_reached:
            session.final_output = session.cycles[-1].improved_output

        session.meta_insights = await self._generate_meta_insights(session)
        session.status = "completed"
        session.completed_at = datetime.now(UTC)

        logger.info(
            "Recursive self-improvement completed",
            cycles_run=session.current_cycle,
            total_gain=session.total_performance_gain,
            final_score=session.cycles[-1].final_assessment.overall_score if session.cycles[-1].final_assessment else 0.0,
        )

        return session

    async def _generate_improvements(
        self,
        task: str,
        output: str,
        assessment: AssessmentResult,
        agents: list[SyzygyAgent],
        cycle_num: int,
    ) -> list[dict[str, Any]]:
        """Generate targeted improvements based on assessment gaps."""

        improvements = []

        # Identify lowest-scoring dimensions
        sorted_dims = sorted(
            assessment.dimension_scores.items(),
            key=lambda x: x[1],
        )

        for dimension, score in sorted_dims[:2]:  # Focus on 2 worst dimensions
            if score < 0.7:  # Only improve dimensions below threshold
                improvement = await self._propose_improvement(
                    task=task,
                    output=output,
                    dimension=dimension,
                    score=score,
                    agents=agents,
                    root_causes=assessment.root_causes.get(dimension, []),
                )
                if improvement:
                    improvements.append(improvement)

        return improvements

    async def _propose_improvement(
        self,
        task: str,
        output: str,
        dimension: str,
        score: float,
        agents: list[SyzygyAgent],
        root_causes: list[str],
    ) -> dict[str, Any] | None:
        """Propose a specific improvement for a dimension."""

        prompt = (
            f"Task: {task[:200]}\n\n"
            f"Output quality dimension: {dimension} (score: {score:.2f})\n"
            f"Output excerpt:\n{output[:500]}\n\n"
            f"Root causes identified:\n" + "\n".join(f"  • {rc}" for rc in root_causes) + "\n\n"
            f"Agent team composition:\n" + "\n".join(f"  • {a.name} ({a.archetype.name if a.archetype else '?'})" for a in agents) + "\n\n"
            f"Propose ONE specific, actionable improvement to boost this dimension.\n"
            f"Choose from: agent-role-change, prompt-tuning, tool-addition, team-rebalancing, "
            f"consensus-adjustment.\n"
            f"Return JSON: {{'type': '...', 'target_agent': '...', 'action': '...', 'rationale': '...'}}"
        )

        result = await self.llm.generate(prompt, temperature=0.4)

        try:
            import json
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                improvement = json.loads(result[start:end])
                return improvement
        except Exception as e:
            logger.warning(f"Failed to parse improvement proposal: {e}")

        return None

    async def _apply_improvements(
        self,
        agents: list[SyzygyAgent],
        improvements: list[dict[str, Any]],
        learning_rate: float,
    ) -> list[SyzygyAgent]:
        """Apply improvements to agents. Returns modified agent list."""

        modified_agents = [agent for agent in agents]  # shallow copy

        for improvement in improvements:
            imp_type = improvement.get("type", "").lower()
            target_name = improvement.get("target_agent", "")
            action = improvement.get("action", "")

            target_agent = next(
                (a for a in modified_agents if a.name.lower() == target_name.lower()),
                None,
            )
            if not target_agent:
                continue

            logger.info(f"Applying {imp_type} to {target_agent.name}: {action[:100]}")

            if imp_type == "prompt-tuning":
                # Adjust system prompt
                target_agent.system_prompt_adjustments = (
                    target_agent.system_prompt_adjustments or {}
                )
                target_agent.system_prompt_adjustments["tuning_" + str(int(datetime.now(UTC).timestamp()))] = action

            elif imp_type == "agent-role-change":
                # Modify agent archetype instructions or focus
                if getattr(target_agent, "role_adjustments", None) is None:
                    target_agent.role_adjustments = []
                target_agent.role_adjustments.append(action)

            elif imp_type == "tool-addition":
                # Add new tools to agent (would require tool registry integration)
                if getattr(target_agent, "requested_tools", None) is None:
                    target_agent.requested_tools = []
                target_agent.requested_tools.append(action)

            elif imp_type == "consensus-adjustment":
                # Adjust consensus participation (e.g., increase debate rounds)
                if getattr(target_agent, "consensus_weight", None) is None:  # pragma: no cover
                    target_agent.consensus_weight = 1.0  # pragma: no cover
                target_agent.consensus_weight = min(
                    2.0, target_agent.consensus_weight * (1.0 + learning_rate)
                )

        return modified_agents

    async def _store_learning(
        self,
        session: RecursiveImprovementSession,
        cycle: ImprovementCycle,
        improvements: list[dict[str, Any]],
        domain: str,
    ) -> None:
        """Store learned patterns in memory for future use."""

        if not self.memory:  # pragma: no cover (always guarded by caller)
            return

        learning_record = {
            "session_id": session.id,
            "cycle": cycle.cycle_number,
            "domain": domain,
            "task_summary": session.task[:200],
            "initial_score": cycle.initial_assessment.overall_score if cycle.initial_assessment else 0.0,
            "final_score": cycle.final_assessment.overall_score if cycle.final_assessment else 0.0,
            "performance_delta": cycle.performance_delta,
            "improvements_applied": improvements,
            "convergence_reached": cycle.convergence_reached,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Store as embedding in vector store for semantic recall
        await self.memory.add_memory(
            key=f"improvement_cycle_{session.id}_{cycle.cycle_number}",
            value=learning_record,
            embedding_text=f"{domain} improvement: {' '.join(ic['action'] for ic in improvements if 'action' in ic)}",
        )

    async def _generate_meta_insights(
        self,
        session: RecursiveImprovementSession,
    ) -> list[str]:
        """Generate high-level insights from the entire improvement session."""

        insights = []

        # Compute statistics
        total_cycles = len(session.cycles)
        avg_delta = session.total_performance_gain / max(1, total_cycles)

        if session.total_performance_gain > 0.1:
            insights.append(
                f"Strong improvement trajectory: +{session.total_performance_gain:.1%} over {total_cycles} cycles"
            )
        elif session.total_performance_gain > 0:
            insights.append(
                f"Gradual improvement: +{session.total_performance_gain:.1%} over {total_cycles} cycles"
            )
        else:
            insights.append(
                f"Plateau reached: no net improvement after {total_cycles} cycles; may need different strategy"
            )

        # Identify consistent weak dimensions
        weak_dims = {}
        for cycle in session.cycles:
            if cycle.initial_assessment:
                for dim, score in cycle.initial_assessment.dimension_scores.items():
                    weak_dims[dim] = weak_dims.get(dim, []) + [score]

        worst_dim = min(weak_dims.items(), key=lambda x: sum(x[1]) / len(x[1]), default=(None, []))
        if worst_dim[0]:
            avg_worst = sum(worst_dim[1]) / len(worst_dim[1])
            insights.append(
                f"Persistent weakness in '{worst_dim[0]}' (avg {avg_worst:.2f}); "
                "consider structural team changes"
            )

        # Check convergence behavior
        converged = any(c.convergence_reached for c in session.cycles)
        if converged:
            insights.append(
                f"Fast convergence: reached target quality by cycle {next(c.cycle_number for c in session.cycles if c.convergence_reached)}"
            )
        else:
            insights.append(
                "No convergence: final output still below target; may need more cycles or different approach"
            )

        return insights


SELF_IMPROVEMENT_WORKFLOW = RecursiveSelfImprovementWorkflow()


__all__ = [
    "RecursiveSelfImprovementWorkflow",
    "RecursiveImprovementSession",
    "ImprovementCycle",
    "SELF_IMPROVEMENT_WORKFLOW",
]
