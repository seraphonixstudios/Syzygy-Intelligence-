"""Tests for performance tracker."""

from __future__ import annotations

import pytest


class TestPerformanceTracker:
    def test_single_metric_trend_is_flat(self):
        from app.self_improvement.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.7, {"accuracy": 0.7})
        trend = tracker.analyze_trend()
        assert trend.trend_direction == "flat"

    def test_estimate_convergence_cycle_empty_returns_none(self):
        from app.self_improvement.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        assert tracker.estimate_convergence_cycle() is None

    def test_estimate_convergence_cycle_single_metric_returns_none(self):
        from app.self_improvement.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.5)
        assert tracker.estimate_convergence_cycle() is None
