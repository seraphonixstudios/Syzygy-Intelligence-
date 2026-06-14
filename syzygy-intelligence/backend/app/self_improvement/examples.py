"""Example implementations and tests for recursive self-improvement workflow.

Demonstrates:
- Basic usage with different domains
- Custom assessment configurations
- Performance tracking and analysis
- Learning rate optimization
- Memory integration
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.agents.registry import agent_registry
from app.consensus.engine import ConsensusEngine
from app.llm.ollama_client import OllamaClient  # noqa: F401 — used in example configs; refactor planned
from app.self_improvement.assessment import SelfAssessmentEngine
from app.self_improvement.learning_optimizer import (
    LearningOptimizer,
    LearningRateConfig,
    LearningRateSchedule,
)
from app.self_improvement.performance_tracker import PerformanceTracker
from app.workflows.self_improvement import RecursiveSelfImprovementWorkflow


async def example_code_improvement():
    """Example: Recursive improvement of code generation."""

    print("\n" + "=" * 80)
    print("EXAMPLE 1: Code Generation with Recursive Improvement")
    print("=" * 80)

    task = (
        "Design and implement a Python concurrent download manager that:\n"
        "1. Supports parallel downloads with configurable worker pool\n"
        "2. Has robust error handling with exponential backoff retry\n"
        "3. Provides progress tracking and cancellation support\n"
        "4. Includes comprehensive unit tests\n"
        "5. Is production-ready with type hints and docstrings"
    )

    # Get code-specialized agent team
    agents = agent_registry.create_team_for_domain("code")

    # Initialize workflow with performance tracking
    consensus = ConsensusEngine()
    assessment = SelfAssessmentEngine()
    tracker = PerformanceTracker()
    optimizer = LearningOptimizer(
        config=LearningRateConfig(
            schedule=LearningRateSchedule.WARMUP_THEN_DECAY,
            initial_rate=0.10,
            warmup_cycles=1,
        )
    )

    workflow = RecursiveSelfImprovementWorkflow(
        consensus_engine=consensus,
        assessment_engine=assessment,
        performance_tracker=tracker,
        learning_optimizer=optimizer,
    )

    # Run improvement
    session = await workflow.execute(
        task=task,
        agents=agents,
        domain="code",
        max_cycles=4,
        convergence_threshold=0.88,
    )

    # Display results
    print(f"\n✓ Session completed: {session.status}")
    print(f"  Session ID: {session.id}")
    print(f"  Total cycles: {session.current_cycle}")
    print(f"  Performance gain: {session.total_performance_gain:+.1%}")

    for cycle in session.cycles:
        initial_score = (
            cycle.initial_assessment.overall_score
            if cycle.initial_assessment
            else 0.0
        )
        final_score = (
            cycle.final_assessment.overall_score
            if cycle.final_assessment
            else 0.0
        )
        print(
            f"\n  Cycle {cycle.cycle_number}:"
            f"\n    Initial: {initial_score:.3f}"
            f"\n    Final:   {final_score:.3f}"
            f"\n    Delta:   {cycle.performance_delta:+.3f}"
            f"\n    Improvements: {len(cycle.improvements_applied)}"
        )

        if cycle.initial_assessment:
            weaknesses = cycle.initial_assessment.weaknesses
            print(f"    Weaknesses: {', '.join(weaknesses) if weaknesses else 'None'}")

    print("\n  Meta-insights:")
    for insight in session.meta_insights:
        print(f"    • {insight}")

    return session


async def example_content_improvement():
    """Example: Recursive improvement of content writing."""

    print("\n" + "=" * 80)
    print("EXAMPLE 2: Content Writing with Recursive Improvement")
    print("=" * 80)

    task = (
        "Write a comprehensive guide on 'Async/Await Programming in Python' for "
        "intermediate developers. Include:\n"
        "1. Clear explanations of coroutines and event loops\n"
        "2. Practical examples with real-world use cases\n"
        "3. Common pitfalls and how to avoid them\n"
        "4. Performance considerations\n"
        "5. Integration with existing code patterns"
    )

    # Get content-specialized team
    agents = agent_registry.create_team_for_domain("content")

    # Custom learning rate for content (more gradual)
    optimizer = LearningOptimizer(
        config=LearningRateConfig(
            schedule=LearningRateSchedule.COSINE_ANNEALING,
            initial_rate=0.08,
            min_rate=0.02,
            cycle_length=3,
        )
    )

    workflow = RecursiveSelfImprovementWorkflow(
        learning_optimizer=optimizer,
    )

    session = await workflow.execute(
        task=task,
        agents=agents,
        domain="content",
        max_cycles=5,
        convergence_threshold=0.85,
    )

    print(f"\n✓ Session completed: {session.status}")
    print(f"  Performance gain: {session.total_performance_gain:+.1%}")

    # Display dimension breakdown
    if session.cycles and session.cycles[0].initial_assessment:
        print("\n  Dimension scores (final cycle):")
        final_assessment = session.cycles[-1].final_assessment
        if final_assessment:
            for dim, score in sorted(
                final_assessment.dimension_scores.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
                print(f"    {dim:20s} {score:.2f} [{bar}]")

    return session


async def example_with_performance_analysis():
    """Example: Detailed performance tracking and analysis."""

    print("\n" + "=" * 80)
    print("EXAMPLE 3: Performance Analysis Across Cycles")
    print("=" * 80)

    task = "Analyze the impact of transformer architectures on NLP performance"

    agents = agent_registry.create_team_for_domain("research")
    tracker = PerformanceTracker()

    workflow = RecursiveSelfImprovementWorkflow(
        performance_tracker=tracker,
    )

    session = await workflow.execute(
        task=task,
        agents=agents,
        domain="research",
        max_cycles=6,
        convergence_threshold=0.90,
    )

    # Analyze trend
    trend = tracker.analyze_trend()

    print(f"\n✓ Performance Analysis")
    print(f"  Average score: {trend.average_score:.3f}")
    print(f"  Best score:   {trend.best_score:.3f}")
    print(f"  Worst score:  {trend.worst_score:.3f}")
    print(f"  Total improvement: {trend.total_improvement:+.3f}")
    print(f"  Trend direction: {trend.trend_direction}")
    print(f"  Std deviation: {trend.std_deviation:.3f}")

    if trend.plateau_detected:
        print(
            f"  ⚠ Plateau detected at cycle {trend.plateau_cycle} "
            f"({trend.cycles_since_improvement} cycles since improvement)"
        )

    # Identify opportunities
    opportunities = tracker.identify_improvement_opportunities(trend)
    if opportunities:
        print("\n  Improvement opportunities:")
        for opp in opportunities:
            print(f"    • {opp}")

    # Convergence estimate
    est_cycles = tracker.estimate_convergence_cycle(target_score=0.95)
    if est_cycles is not None:
        print(
            f"\n  Estimated cycles to 0.95 quality: {est_cycles} "
            f"(from current {tracker.metrics[-1].score:.3f})"
        )

    return session


async def example_learning_rate_comparison():
    """Example: Compare different learning rate schedules."""

    print("\n" + "=" * 80)
    print("EXAMPLE 4: Learning Rate Schedule Comparison")
    print("=" * 80)

    schedules = [
        LearningRateSchedule.CONSTANT,
        LearningRateSchedule.LINEAR_DECAY,
        LearningRateSchedule.WARMUP_THEN_DECAY,
        LearningRateSchedule.COSINE_ANNEALING,
    ]

    print("\nLearning rate over 6 cycles:\n")

    for schedule in schedules:
        config = LearningRateConfig(
            schedule=schedule,
            initial_rate=0.10,
            warmup_cycles=1 if schedule != LearningRateSchedule.CONSTANT else 0,
        )
        optimizer = LearningOptimizer(config)

        rates = []
        for cycle in range(1, 7):
            rate = optimizer.get_learning_rate(cycle, max_cycles=6)
            rates.append(rate)

        print(f"  {schedule.value:25s}", end=" ")
        for rate in rates:
            print(f"{rate:.3f} ", end="")
        print()

    print("\n  → WARMUP_THEN_DECAY recommended: starts conservative, escalates safely")


async def example_custom_assessment():
    """Example: Custom assessment configuration."""

    print("\n" + "=" * 80)
    print("EXAMPLE 5: Custom Assessment Configuration")
    print("=" * 80)

    task = "Implement a distributed key-value store with consistency guarantees"

    agents = agent_registry.create_team_for_domain("code")
    assessment = SelfAssessmentEngine()

    # Custom context for stricter code review
    context = {
        "strictness": "high",
        "target_audience": "production",
        "test_coverage_threshold": 0.95,
        "security_level": "critical",
    }

    # Run initial assessment
    print("\nRunning assessment with STRICT settings...")

    initial_output = """
    class KVStore:
        def __init__(self):
            self.data = {}
        
        def get(self, key):
            return self.data.get(key)
        
        def set(self, key, value):
            self.data[key] = value
    """

    assessment_result = await assessment.assess(
        task=task,
        output=initial_output,
        domain="code",
        agents=agents,
        context=context,
    )

    print(f"\n  Overall score: {assessment_result.overall_score:.3f}")
    print(f"  Strengths: {', '.join(assessment_result.strengths) if assessment_result.strengths else 'None'}")
    print(f"  Weaknesses: {', '.join(assessment_result.weaknesses) if assessment_result.weaknesses else 'None'}")

    print("\n  Dimension scores:")
    for dim, score in assessment_result.dimension_scores.items():
        status = "✓" if score >= 0.7 else "✗"
        print(f"    {status} {dim:20s} {score:.3f}")

    if assessment_result.root_causes:
        print("\n  Root causes by dimension:")
        for dim, causes in assessment_result.root_causes.items():
            print(f"    {dim}:")
            for cause in causes:
                print(f"      • {cause}")

    print("\n  Recommendations:")
    for rec in assessment_result.recommendations:
        print(f"    • {rec}")

    return assessment_result


async def main():
    """Run all examples."""

    print("\n" + "=" * 80)
    print("RECURSIVE SELF-IMPROVEMENT WORKFLOW — COMPREHENSIVE EXAMPLES")
    print("=" * 80)
    print(f"Started at: {datetime.now(UTC).isoformat()}")

    try:
        # Run examples
        await example_code_improvement()
        await example_content_improvement()
        await example_with_performance_analysis()
        await example_learning_rate_comparison()
        await example_custom_assessment()

        print("\n" + "=" * 80)
        print("✓ All examples completed successfully")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error during examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
