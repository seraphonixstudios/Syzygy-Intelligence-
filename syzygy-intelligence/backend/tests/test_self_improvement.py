"""Unit tests for the recursive self-improvement engine.

Tests cover the three core classes without requiring LLM calls:
- SelfAssessmentEngine (assessment.py)
- PerformanceTracker (performance_tracker.py)
- LearningOptimizer (learning_optimizer.py)
"""

from __future__ import annotations

import math
from unittest.mock import AsyncMock

import pytest

from app.self_improvement.assessment import AssessmentResult, SelfAssessmentEngine
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


# ═══════════════════════════════════════════════════════════
# SelfAssessmentEngine
# ═══════════════════════════════════════════════════════════

class TestParseScore:
    def test_parses_standard_decimal(self):
        assert SelfAssessmentEngine._parse_score(None, "0.75") == 0.75

    def test_parses_first_of_many(self):
        assert SelfAssessmentEngine._parse_score(None, "Score: 0.82 out of 1.0") == 0.82

    def test_parses_whole_number_as_percentage(self):
        assert SelfAssessmentEngine._parse_score(None, "75") == 0.75

    def test_parses_low_percentage(self):
        assert SelfAssessmentEngine._parse_score(None, "12") == 0.12

    def test_fallback_to_0_5_on_garbage(self):
        assert SelfAssessmentEngine._parse_score(None, "invalid") == 0.5

    def test_clamps_above_1(self):
        assert SelfAssessmentEngine._parse_score(None, "150") == 1.0

    def test_clamps_below_0(self):
        assert SelfAssessmentEngine._parse_score(None, "-0.5") == 0.0


class TestExtractBullets:
    def test_hand_dash_bullets(self):
        text = "- First item\n- Second item"
        result = SelfAssessmentEngine._extract_bullets(None, text)
        assert result == ["First item", "Second item"]

    def test_hand_asterisk_bullets(self):
        text = "* Alpha\n* Beta"
        result = SelfAssessmentEngine._extract_bullets(None, text)
        assert result == ["Alpha", "Beta"]

    def test_hand_numbered_list(self):
        text = "1. First\n2. Second"
        result = SelfAssessmentEngine._extract_bullets(None, text)
        assert result == ["First", "Second"]

    def test_hand_unicode_bullet(self):
        text = "• Item one\n• Item two"
        result = SelfAssessmentEngine._extract_bullets(None, text)
        assert result == ["Item one", "Item two"]

    def test_fallback_to_first_100_chars(self):
        text = "Plain paragraph without bullets"
        result = SelfAssessmentEngine._extract_bullets(None, text)
        assert result == [text[:100]]


class TestIdentifyStrengthsWeaknesses:
    def test_high_scores_are_strengths(self):
        scores = {"accuracy": 0.85, "coherence": 0.75, "creativity": 0.3}
        strengths, weaknesses = SelfAssessmentEngine._identify_strengths_weaknesses(None, scores)
        assert "accuracy" in strengths
        assert "coherence" in strengths
        assert "creativity" not in strengths

    def test_low_scores_are_weaknesses(self):
        scores = {"accuracy": 0.9, "coherence": 0.5, "creativity": 0.2}
        strengths, weaknesses = SelfAssessmentEngine._identify_strengths_weaknesses(None, scores)
        assert "coherence" in weaknesses
        assert "creativity" in weaknesses
        assert "accuracy" not in weaknesses

    def test_medium_scores_are_neither(self):
        scores = {"accuracy": 0.65}
        strengths, weaknesses = SelfAssessmentEngine._identify_strengths_weaknesses(None, scores)
        assert len(strengths) == 0
        assert len(weaknesses) == 0


class TestComputeOverall:
    def test_average_of_scores(self):
        scores = {"a": 0.8, "b": 0.6, "c": 0.4}
        overall = SelfAssessmentEngine._compute_overall(None, scores)
        assert overall == 0.6

    def test_empty_returns_half(self):
        assert SelfAssessmentEngine._compute_overall(None, {}) == 0.5

    def test_rounds_to_four_decimals(self):
        scores = {"a": 0.33333, "b": 0.66666}
        overall = SelfAssessmentEngine._compute_overall(None, scores)
        assert overall == 0.5


class TestGetDimensions:
    def test_general_domain_returns_only_universal(self):
        engine = SelfAssessmentEngine(AsyncMock())
        dims = engine._get_dimensions("general")
        assert dims == engine.UNIVERSAL_DIMENSIONS

    def test_code_domain_returns_universal_plus_code(self):
        engine = SelfAssessmentEngine(AsyncMock())
        dims = engine._get_dimensions("code")
        for u in engine.UNIVERSAL_DIMENSIONS:
            assert u in dims
        for c in engine.DOMAIN_DIMENSIONS["code"]:
            assert c in dims

    def test_domain_case_insensitive(self):
        engine = SelfAssessmentEngine(AsyncMock())
        upper = engine._get_dimensions("RESEARCH")
        lower = engine._get_dimensions("research")
        assert upper == lower

    def test_content_domain_extra_dimensions(self):
        engine = SelfAssessmentEngine(AsyncMock())
        dims = engine._get_dimensions("content")
        for c in engine.DOMAIN_DIMENSIONS["content"]:
            assert c in dims


class TestComputeMetrics:
    @pytest.mark.asyncio
    async def test_code_metrics(self):
        code = "def foo():\n    pass\n# comment\nassert True"
        metrics = await SelfAssessmentEngine._compute_metrics(None, code, "code", "")
        assert metrics["line_count"] == 3
        assert metrics["has_comments"] is True
        assert metrics["has_tests"] is True

    @pytest.mark.asyncio
    async def test_code_no_tests(self):
        code = "def foo():\n    pass"
        metrics = await SelfAssessmentEngine._compute_metrics(None, code, "code", "")
        assert metrics["has_tests"] is False

    @pytest.mark.asyncio
    async def test_content_metrics(self):
        engine = SelfAssessmentEngine(AsyncMock())
        text = "# Title\n\n## Section 1\nSome text with examples like e.g."
        metrics = await engine._compute_metrics(text, "content", "")
        assert metrics["section_count"] >= 1
        assert metrics["has_examples"] is True

    @pytest.mark.asyncio
    async def test_research_metrics(self):
        text = "Introduction\n\nSome claim [1] and another [2].\n\nConclusion"
        metrics = await SelfAssessmentEngine._compute_metrics(None, text, "research", "")
        assert metrics["citation_count"] == 2
        assert metrics["section_structure"] is True

    @pytest.mark.asyncio
    async def test_research_no_structure(self):
        text = "Just a paragraph without sections."
        metrics = await SelfAssessmentEngine._compute_metrics(None, text, "research", "")
        assert metrics["section_structure"] is False

    @pytest.mark.asyncio
    async def test_general_domain_metrics(self):
        text = "Some words here and there"
        metrics = await SelfAssessmentEngine._compute_metrics(None, text, "general", "")
        assert metrics["length_tokens"] == 5
        assert metrics["length_chars"] == len(text)

    @pytest.mark.asyncio
    async def test_token_count_is_word_count(self):
        text = "a b c d e"
        metrics = await SelfAssessmentEngine._compute_metrics(None, text, "general", "")
        assert metrics["length_tokens"] == 5


class TestEstimateReadability:
    def test_returns_between_0_and_1(self):
        engine = SelfAssessmentEngine(AsyncMock())
        score = engine._estimate_readability("This is a short sentence. Here is another one.")
        assert 0.0 <= score <= 1.0

    def test_short_sentences_score_higher(self):
        engine = SelfAssessmentEngine(AsyncMock())
        easy = engine._estimate_readability("I see the cat. The cat is big. It runs fast.")
        hard = engine._estimate_readability(
            "Notwithstanding the aforementioned complexities, this particular implementation "
            "demonstrates significant methodological advancement."
        )
        assert easy > hard

    def test_empty_text_returns_half(self):
        engine = SelfAssessmentEngine(AsyncMock())
        assert engine._estimate_readability("") == 0.5


class TestAssessMethod:
    @pytest.mark.asyncio
    async def test_assess_returns_assessment_result(self):
        llm = AsyncMock()
        llm.generate.return_value = "0.75"
        engine = SelfAssessmentEngine(llm)
        result = await engine.assess("Write code", "def foo(): pass", domain="code")
        assert isinstance(result, AssessmentResult)
        assert 0.0 <= result.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_assess_strengths_empty_for_low_scores(self):
        llm = AsyncMock()
        llm.generate.return_value = "0.3"
        engine = SelfAssessmentEngine(llm)
        result = await engine.assess("Write something", "bad output", domain="general")
        assert len(result.strengths) == 0


# ═══════════════════════════════════════════════════════════
# PerformanceTracker
# ═══════════════════════════════════════════════════════════

class TestRecordMetric:
    def test_records_first_metric(self):
        tracker = PerformanceTracker()
        m = tracker.record_metric(1, 0.7)
        assert m.cycle_number == 1
        assert m.score == 0.7
        assert m.delta_from_previous == 0.0
        assert len(tracker.metrics) == 1

    def test_records_subsequent_deltas(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.5)
        m = tracker.record_metric(2, 0.8)
        assert m.delta_from_previous == pytest.approx(0.3)
        assert m.cumulative_gain == pytest.approx(0.3)

    def test_records_decline(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.8)
        m = tracker.record_metric(2, 0.6)
        assert m.delta_from_previous == pytest.approx(-0.2)

    def test_dimension_scores_stored(self):
        tracker = PerformanceTracker()
        dims = {"accuracy": 0.8, "coherence": 0.7}
        m = tracker.record_metric(1, 0.75, dimension_scores=dims)
        assert m.dimension_scores == dims


class TestAnalyzeTrend:
    def test_empty_returns_default(self):
        tracker = PerformanceTracker()
        trend = tracker.analyze_trend()
        assert trend.average_score == 0.0
        assert trend.trend_direction == "flat"

    def test_improving_trend(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.4)
        tracker.record_metric(2, 0.6)
        tracker.record_metric(3, 0.8)
        trend = tracker.analyze_trend()
        assert trend.trend_direction == "improving"
        assert trend.best_score == 0.8
        assert trend.worst_score == 0.4

    def test_declining_trend(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.9)
        tracker.record_metric(2, 0.7)
        tracker.record_metric(3, 0.5)
        trend = tracker.analyze_trend()
        assert trend.trend_direction == "declining"

    def test_flat_trend(self):
        tracker = PerformanceTracker()
        for i in range(1, 5):
            tracker.record_metric(i, 0.6)
        trend = tracker.analyze_trend()
        assert trend.trend_direction == "flat"

    def test_plateau_detected(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.5)
        tracker.record_metric(2, 0.7)
        tracker.record_metric(3, 0.701)  # < 0.01 improvement
        tracker.record_metric(4, 0.702)  # < 0.01 improvement
        trend = tracker.analyze_trend()
        assert trend.plateau_detected

    def test_variance_and_std_deviation(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.3)
        tracker.record_metric(2, 0.6)
        tracker.record_metric(3, 0.9)
        trend = tracker.analyze_trend()
        assert trend.variance > 0
        assert trend.std_deviation > 0

    def test_total_improvement_calculated(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.4)
        tracker.record_metric(2, 0.7)
        tracker.record_metric(3, 0.85)
        trend = tracker.analyze_trend()
        assert trend.total_improvement == pytest.approx(0.45)


class TestGetDimensionTrends:
    def test_returns_scores_for_dimension(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.7, dimension_scores={"acc": 0.6})
        tracker.record_metric(2, 0.8, dimension_scores={"acc": 0.75})
        trends = tracker.get_dimension_trends("acc")
        assert trends == [0.6, 0.75]

    def test_missing_dimension_returns_zeros(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.7)
        trends = tracker.get_dimension_trends("missing")
        assert trends == [0.0]


class TestIdentifyImprovementOpportunities:
    def test_plateau_opportunity(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.5)
        tracker.record_metric(2, 0.7)
        tracker.record_metric(3, 0.701)
        tracker.record_metric(4, 0.702)
        trend = tracker.analyze_trend()
        ops = tracker.identify_improvement_opportunities(trend)
        assert any("plateau" in op.lower() for op in ops)

    def test_declining_opportunity(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.85)
        tracker.record_metric(2, 0.75)
        tracker.record_metric(3, 0.65)
        trend = tracker.analyze_trend()
        ops = tracker.identify_improvement_opportunities(trend)
        assert any("declining" in op.lower() for op in ops)

    def test_high_variance_opportunity(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.2)
        tracker.record_metric(2, 0.9)
        tracker.record_metric(3, 0.3)
        trend = tracker.analyze_trend()
        ops = tracker.identify_improvement_opportunities(trend)
        assert any("variability" in op.lower() for op in ops)

    def test_low_average_opportunity(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.5)
        tracker.record_metric(2, 0.55)
        trend = tracker.analyze_trend()
        ops = tracker.identify_improvement_opportunities(trend)
        assert any(op for op in ops if "below 0.7" in op)


class TestEstimateConvergenceCycle:
    def test_already_at_target_returns_zero(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.95)
        assert tracker.estimate_convergence_cycle(0.9) == 0

    def test_insufficient_data_returns_none(self):
        tracker = PerformanceTracker()
        assert tracker.estimate_convergence_cycle(0.9) is None

    def test_estimates_future_cycles(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.3)
        tracker.record_metric(2, 0.5)  # delta = 0.2
        # improvement_rate will be ~0.2, need (0.9 - 0.5) / 0.2 = 2 cycles
        estimate = tracker.estimate_convergence_cycle(0.9)
        assert estimate is not None
        assert estimate > 0

    def test_no_improvement_returns_none(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.5)
        tracker.record_metric(2, 0.5)
        # improvement_rate = 0.0
        assert tracker.estimate_convergence_cycle(0.9) is None


class TestPerformanceTrackerReset:
    def test_reset_clears_metrics(self):
        tracker = PerformanceTracker()
        tracker.record_metric(1, 0.8)
        tracker.reset()
        assert len(tracker.metrics) == 0
        assert tracker.analyze_trend().average_score == 0.0


# ═══════════════════════════════════════════════════════════
# LearningOptimizer
# ═══════════════════════════════════════════════════════════

class TestConstantSchedule:
    def test_constant_rate(self):
        opt = LearningOptimizer(LearningRateConfig(schedule=LearningRateSchedule.CONSTANT))
        rate = opt.get_learning_rate(5, 10)
        assert rate == 0.1

    def test_constant_rate_all_cycles(self):
        opt = LearningOptimizer(LearningRateConfig(schedule=LearningRateSchedule.CONSTANT))
        rates = [opt.get_learning_rate(i, 10) for i in range(1, 11)]
        assert all(r == 0.1 for r in rates)


class TestLinearDecaySchedule:
    def test_linear_decay_start(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.LINEAR_DECAY,
            initial_rate=0.1,
            min_rate=0.01,
        ))
        rate = opt.get_learning_rate(1, 10)
        assert rate == pytest.approx(0.1)

    def test_linear_decay_end(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.LINEAR_DECAY,
            initial_rate=0.1,
            min_rate=0.01,
        ))
        rate = opt.get_learning_rate(10, 10)
        assert rate == pytest.approx(0.01)

    def test_linear_decay_midpoint(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.LINEAR_DECAY,
            initial_rate=0.1,
            min_rate=0.01,
        ))
        rate = opt.get_learning_rate(5, 10)
        assert rate == pytest.approx(0.055, abs=0.01)


class TestExponentialDecaySchedule:
    def test_exponential_decay_first_cycle(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.EXPONENTIAL_DECAY,
            initial_rate=0.1,
            decay_rate=0.5,
        ))
        rate = opt.get_learning_rate(1, 10)
        assert rate == pytest.approx(0.1)

    def test_exponential_decay_second_cycle(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.EXPONENTIAL_DECAY,
            initial_rate=0.1,
            decay_rate=0.5,
        ))
        rate = opt.get_learning_rate(2, 10)
        assert rate == pytest.approx(0.05)

    def test_exponential_decay_fifth_cycle(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.EXPONENTIAL_DECAY,
            initial_rate=0.1,
            min_rate=0.001,
            decay_rate=0.5,
        ))
        rate = opt.get_learning_rate(5, 10)
        assert rate == pytest.approx(0.00625, abs=0.001)

    def test_exponential_decay_floors_at_min(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.EXPONENTIAL_DECAY,
            initial_rate=0.1,
            min_rate=0.02,
            decay_rate=0.1,
        ))
        rate = opt.get_learning_rate(10, 10)
        assert rate >= 0.02


class TestCosineAnnealingSchedule:
    def test_cosine_annealing_oscillates(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.COSINE_ANNEALING,
            initial_rate=0.1,
            min_rate=0.01,
            cycle_length=4,
        ))
        # At cycle 1 (position 0 of cycle), cos(0) = 1, so rate should be max
        rate_start = opt.get_learning_rate(1, 10)
        # At cycle 2 (position 1 of cycle), cos(pi/4) < 1
        rate_mid = opt.get_learning_rate(2, 10)
        # At cycle 4 (position 3 of cycle), cos(3pi/4) is lowest
        rate_end = opt.get_learning_rate(4, 10)
        # At cycle 5 (position 0 of next cycle), cos(0) = 1 again
        rate_restart = opt.get_learning_rate(5, 10)

        assert rate_start > rate_mid
        assert rate_end == pytest.approx(opt.config.min_rate, abs=0.01)
        assert rate_restart == pytest.approx(rate_start, abs=0.01)


class TestWarmupThenDecaySchedule:
    def test_warmup_increases(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.WARMUP_THEN_DECAY,
            initial_rate=0.1,
            warmup_cycles=3,
        ))
        r1 = opt.get_learning_rate(1, 10)
        r2 = opt.get_learning_rate(2, 10)
        r3 = opt.get_learning_rate(3, 10)
        assert r1 < r2 < r3
        assert r3 == pytest.approx(0.1)

    def test_post_warmup_decays(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.WARMUP_THEN_DECAY,
            initial_rate=0.1,
            min_rate=0.01,
            warmup_cycles=2,
        ))
        opt.get_learning_rate(1, 10)
        opt.get_learning_rate(2, 10)
        r3 = opt.get_learning_rate(3, 10)
        r4 = opt.get_learning_rate(4, 10)
        assert r3 > r4


class TestCyclicalSchedule:
    def test_cyclical_oscillates(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.CYCLICAL,
            initial_rate=0.1,
            min_rate=0.01,
            cycle_length=4,
        ))
        r1 = opt.get_learning_rate(1, 10)  # tri wave min (position 0)
        r2 = opt.get_learning_rate(2, 10)  # tri wave rising (position 1)
        r3 = opt.get_learning_rate(4, 10)  # tri wave falling (position 3)
        r4 = opt.get_learning_rate(3, 10)  # tri wave peak (position 2)
        assert r1 < r2
        assert r3 < r4
        assert r1 == pytest.approx(opt.config.min_rate, abs=0.01)

    def test_cyclical_restarts(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.CYCLICAL,
            initial_rate=0.1,
            min_rate=0.01,
            cycle_length=3,
        ))
        r1 = opt.get_learning_rate(1, 10)
        r4 = opt.get_learning_rate(4, 10)  # restart
        assert r1 == pytest.approx(r4, abs=0.01)


class TestPerformanceAdaptiveSchedule:
    def test_increases_on_improvement(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.PERFORMANCE_ADAPTIVE,
            initial_rate=0.1,
            adaptation_factor=2.0,
        ))
        opt.record_improvement(0.2)
        rate = opt.get_learning_rate(2, 10)
        assert rate == pytest.approx(0.2)

    def test_decreases_on_no_improvement(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.PERFORMANCE_ADAPTIVE,
            initial_rate=0.1,
            adaptation_factor=2.0,
        ))
        opt.current_rate = 0.1
        opt.best_improvement = 0.5
        opt.patience_counter = 1
        opt.improvement_history = [0.3]
        rate = opt.get_learning_rate(2, 10)
        assert rate < 0.1

    def test_rate_clamped_to_bounds(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.PERFORMANCE_ADAPTIVE,
            initial_rate=0.5,
            max_rate=0.5,
            adaptation_factor=2.0,
        ))
        opt.record_improvement(0.3)
        rate = opt.get_learning_rate(2, 10)
        assert rate == 0.5  # capped


class TestRecordImprovement:
    def test_records_improvement_and_updates_best(self):
        opt = LearningOptimizer()
        opt.record_improvement(0.1)
        assert opt.improvement_history == [0.1]
        assert opt.best_improvement == 0.1
        assert opt.patience_counter == 0

    def test_no_improvement_increments_patience(self):
        opt = LearningOptimizer()
        opt.record_improvement(0.5)
        opt.record_improvement(0.3)  # worse
        assert opt.patience_counter == 1


class TestShouldStopEarly:
    def test_no_stop_on_good_progress(self):
        opt = LearningOptimizer()
        assert not opt.should_stop_early()

    def test_stops_on_patience_exceeded(self):
        opt = LearningOptimizer()
        opt.record_improvement(1.0)
        opt.record_improvement(0.5)
        opt.record_improvement(0.3)
        opt.patience_counter = 3
        assert opt.should_stop_early()

    def test_stops_on_rate_too_low(self):
        opt = LearningOptimizer(LearningRateConfig(min_rate=0.1))
        opt.current_rate = 0.04  # below 50% of 0.1
        assert opt.should_stop_early()


class TestLearningOptimizerReset:
    def test_reset_restores_initial_state(self):
        opt = LearningOptimizer()
        opt.record_improvement(0.5)
        opt.get_learning_rate(5, 10)
        opt.reset()
        assert opt.current_rate == opt.config.initial_rate
        assert opt.cycle_number == 0
        assert opt.improvement_history == []
        assert opt.patience_counter == 0

    def test_get_config_dict(self):
        opt = LearningOptimizer(LearningRateConfig(
            schedule=LearningRateSchedule.WARMUP_THEN_DECAY,
            initial_rate=0.2,
        ))
        cfg = opt.get_config_dict()
        assert cfg["schedule"] == "warmup_then_decay"
        assert cfg["initial_rate"] == 0.2


# ═══════════════════════════════════════════════════════════
# PerformanceMetrics dataclass
# ═══════════════════════════════════════════════════════════

class TestPerformanceMetrics:
    def test_default_values(self):
        m = PerformanceMetrics()
        assert m.cycle_number == 0
        assert m.score == 0.0
        assert m.delta_from_previous == 0.0

    def test_custom_values(self):
        m = PerformanceMetrics(
            cycle_number=3,
            score=0.85,
            delta_from_previous=0.1,
            cumulative_gain=0.25,
            improvement_rate=0.08,
        )
        assert m.cycle_number == 3
        assert m.score == 0.85


# ═══════════════════════════════════════════════════════════
# AssessmentResult dataclass
# ═══════════════════════════════════════════════════════════

class TestAssessmentResult:
    def test_default_values(self):
        r = AssessmentResult(overall_score=0.7)
        assert r.overall_score == 0.7
        assert r.dimension_scores == {}
        assert r.strengths == []
        assert r.weaknesses == []
        assert r.root_causes == {}
        assert r.recommendations == []
        assert r.metrics == {}
