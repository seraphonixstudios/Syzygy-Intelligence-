"""Performance tracking and longitudinal analytics for recursive improvement.

Tracks performance across improvement cycles with:
- Time-series metrics collection
- Trend analysis and anomaly detection
- Performance plateau detection
- Learning curve estimation
- Regression diagnostics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger


@dataclass
class PerformanceMetrics:
    """Snapshot of performance at a point in time."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    cycle_number: int = 0
    score: float = 0.0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    delta_from_previous: float = 0.0
    cumulative_gain: float = 0.0
    improvement_rate: float = 0.0  # score improvement per cycle


@dataclass
class PerformanceTrend:
    """Analysis of performance over time."""

    metrics: list[PerformanceMetrics] = field(default_factory=list)
    average_score: float = 0.0
    best_score: float = 0.0
    worst_score: float = 0.0
    total_improvement: float = 0.0
    average_improvement_rate: float = 0.0
    variance: float = 0.0
    std_deviation: float = 0.0
    trend_direction: str = "flat"  # "improving", "declining", "flat"
    plateau_detected: bool = False
    plateau_cycle: int | None = None
    cycles_since_improvement: int = 0


class PerformanceTracker:
    """Tracks and analyzes performance metrics across improvement cycles."""

    def __init__(self):
        self.metrics: list[PerformanceMetrics] = []
        self.improvement_threshold: float = 0.01  # 1% improvement to count as progress

    def record_metric(
        self,
        cycle_number: int,
        score: float,
        dimension_scores: dict[str, float] | None = None,
    ) -> PerformanceMetrics:
        """Record a performance metric for a cycle."""

        delta = score - self.metrics[-1].score if self.metrics else 0.0
        cumulative = (self.metrics[-1].cumulative_gain if self.metrics else 0.0) + delta

        metric = PerformanceMetrics(
            cycle_number=cycle_number,
            score=score,
            dimension_scores=dimension_scores or {},
            delta_from_previous=delta,
            cumulative_gain=cumulative,
            improvement_rate=self._estimate_rate(delta),
        )

        self.metrics.append(metric)
        logger.debug(
            f"Recorded metric: cycle={cycle_number}, score={score:.3f}, delta={delta:+.3f}"
        )

        return metric

    def analyze_trend(self) -> PerformanceTrend:
        """Analyze performance trend across all metrics."""

        if not self.metrics:
            return PerformanceTrend()

        scores = [m.score for m in self.metrics]
        deltas = [m.delta_from_previous for m in self.metrics[1:]]

        avg_score = sum(scores) / len(scores)
        best_score = max(scores)
        worst_score = min(scores)
        total_improvement = scores[-1] - scores[0]
        avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

        # Compute variance and std deviation
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # Detect trend direction (compare first half to second half)
        mid = len(scores) // 2
        if mid > 0:
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
            if second_half_avg > first_half_avg + self.improvement_threshold:
                trend = "improving"
            elif second_half_avg < first_half_avg - self.improvement_threshold:
                trend = "declining"
            else:
                trend = "flat"
        else:
            trend = "flat"

        # Detect plateau
        plateau_detected = False
        plateau_cycle = None
        cycles_since_improvement = 0

        if len(deltas) >= 2:
            # If last 2 improvements are < threshold, plateau likely
            if all(abs(d) < self.improvement_threshold for d in deltas[-2:]):
                plateau_detected = True
                plateau_cycle = self.metrics[-2].cycle_number
                cycles_since_improvement = len(
                    [d for d in deltas if abs(d) < self.improvement_threshold]
                )

        return PerformanceTrend(
            metrics=self.metrics,
            average_score=avg_score,
            best_score=best_score,
            worst_score=worst_score,
            total_improvement=total_improvement,
            average_improvement_rate=avg_delta,
            variance=variance,
            std_deviation=std_dev,
            trend_direction=trend,
            plateau_detected=plateau_detected,
            plateau_cycle=plateau_cycle,
            cycles_since_improvement=cycles_since_improvement,
        )

    def get_dimension_trends(self, dimension: str) -> list[float]:
        """Get trend of a specific dimension across cycles."""

        return [
            m.dimension_scores.get(dimension, 0.0)
            for m in self.metrics
        ]

    def identify_improvement_opportunities(self, trend: PerformanceTrend) -> list[str]:
        """Identify dimensions and strategies to improve."""

        opportunities = []

        if trend.plateau_detected:
            opportunities.append(
                f"Plateau detected at cycle {trend.plateau_cycle}; "
                f"consider structural changes to agent team or task approach"
            )

        if trend.trend_direction == "declining":
            opportunities.append(
                "Performance declining; recent changes may be counterproductive; review last cycle"
            )

        if trend.std_deviation > 0.15:
            opportunities.append(
                "High variability in performance; agent consensus may be poor; "
                "consider increasing debate rounds or refining team composition"
            )

        if trend.average_score < 0.7:
            opportunities.append(
                f"Average score below 0.7 ({trend.average_score:.2f}); "
                "fundamental agent capability or tool gaps likely present"
            )

        return opportunities

    def estimate_convergence_cycle(self, target_score: float = 0.9) -> int | None:
        """Estimate how many more cycles needed to reach target score."""

        if not self.metrics:
            return None

        current_score = self.metrics[-1].score

        if current_score >= target_score:
            return 0

        if len(self.metrics) < 2:
            return None

        # Linear extrapolation from avg improvement rate
        avg_improvement = self.metrics[-1].improvement_rate
        if avg_improvement <= 0.001:  # Very slow or no improvement
            return None

        cycles_needed = (target_score - current_score) / avg_improvement
        return int(cycles_needed)

    def _estimate_rate(self, delta: float) -> float:
        """Estimate improvement rate based on delta."""

        # Smooth estimate to avoid noise
        if len(self.metrics) < 2:
            return delta

        recent_deltas = [m.delta_from_previous for m in self.metrics[-3:]]
        return sum(recent_deltas) / len(recent_deltas)

    def reset(self) -> None:
        """Clear all metrics."""

        self.metrics = []
        logger.info("Performance tracker reset")


__all__ = [
    "PerformanceTracker",
    "PerformanceMetrics",
    "PerformanceTrend",
]
