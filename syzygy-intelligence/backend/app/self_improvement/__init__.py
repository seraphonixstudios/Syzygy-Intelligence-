"""Self-improvement package initialization."""

from __future__ import annotations

from app.self_improvement.assessment import (
    AssessmentResult,
    SelfAssessmentEngine,
)
from app.self_improvement.learning_optimizer import (
    LearningOptimizer,
    LearningRateConfig,
    LearningRateSchedule,
)
from app.self_improvement.performance_tracker import (
    PerformanceMetrics,
    PerformanceTracker,
    PerformanceTrend,
)


__all__ = [
    "SelfAssessmentEngine",
    "AssessmentResult",
    "PerformanceTracker",
    "PerformanceMetrics",
    "PerformanceTrend",
    "LearningOptimizer",
    "LearningRateConfig",
    "LearningRateSchedule",
]
