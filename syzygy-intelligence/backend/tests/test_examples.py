"""Tests for self-improvement example functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def make_mock_assessment(score=0.75, weaknesses=None, strengths=None):
    a = MagicMock()
    a.overall_score = score
    a.dimension_scores = {"accuracy": score, "coherence": score}
    a.weaknesses = weaknesses or []
    a.strengths = strengths or ["good"]
    a.root_causes = {}
    a.recommendations = ["improve x"]
    return a


def make_mock_cycle(num, init_score=0.5, final_score=0.8):
    c = MagicMock()
    c.cycle_number = num
    c.initial_assessment = make_mock_assessment(score=init_score, weaknesses=["bugs"])
    c.final_assessment = make_mock_assessment(score=final_score)
    c.performance_delta = final_score - init_score
    c.improvements_applied = [{"type": "refactor"}]
    return c


def make_mock_session(cycles=2, status="completed", perf_gain=0.3):
    s = MagicMock()
    s.status = status
    s.id = "impr_test_123"
    s.current_cycle = cycles
    s.total_performance_gain = perf_gain
    s.cycles = [make_mock_cycle(i + 1) for i in range(cycles)]
    s.meta_insights = ["Insight 1", "Insight 2"]
    return s


class MockAgentRegistry:
    def create_team_for_domain(self, domain):
        return [MagicMock()]


class TestExampleCodeImprovement:
    @pytest.mark.asyncio
    async def test_returns_session(self):
        mock_session = make_mock_session()
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.ConsensusEngine") as m_ce,
            patch("app.self_improvement.examples.SelfAssessmentEngine") as m_sae,
            patch("app.self_improvement.examples.PerformanceTracker") as m_pt,
            patch("app.self_improvement.examples.LearningOptimizer") as m_lo,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            from app.self_improvement.examples import example_code_improvement

            result = await example_code_improvement()
            assert result.status == "completed"
            assert result.id == "impr_test_123"
            assert result.current_cycle == 2
            m_wf.assert_called_once()
            m_wf.return_value.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_prints_cycle_details(self, capsys):
        mock_session = make_mock_session(cycles=2)
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.ConsensusEngine"),
            patch("app.self_improvement.examples.SelfAssessmentEngine"),
            patch("app.self_improvement.examples.PerformanceTracker"),
            patch("app.self_improvement.examples.LearningOptimizer"),
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            from app.self_improvement.examples import example_code_improvement

            await example_code_improvement()
            captured = capsys.readouterr()
            assert "Session completed" in captured.out
            assert "Cycle 1" in captured.out
            assert "Cycle 2" in captured.out
            assert "Meta-insights" in captured.out
            assert "Insight 1" in captured.out

    @pytest.mark.asyncio
    async def test_handles_empty_assessment(self):
        session = MagicMock()
        session.status = "completed"
        session.id = "test_id"
        session.current_cycle = 1
        session.total_performance_gain = 0.2
        cycle = MagicMock()
        cycle.cycle_number = 1
        cycle.initial_assessment = None
        cycle.final_assessment = None
        cycle.performance_delta = 0.0
        cycle.improvements_applied = []
        session.cycles = [cycle]
        session.meta_insights = []
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.ConsensusEngine"),
            patch("app.self_improvement.examples.SelfAssessmentEngine"),
            patch("app.self_improvement.examples.PerformanceTracker"),
            patch("app.self_improvement.examples.LearningOptimizer"),
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=session)
            from app.self_improvement.examples import example_code_improvement

            result = await example_code_improvement()
            assert result.status == "completed"


class TestExampleContentImprovement:
    @pytest.mark.asyncio
    async def test_returns_session(self):
        mock_session = make_mock_session(cycles=3)
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.LearningOptimizer") as m_lo,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            from app.self_improvement.examples import example_content_improvement

            result = await example_content_improvement()
            assert result.current_cycle == 3
            m_lo.assert_called_once()
            m_wf.assert_called_once()

    @pytest.mark.asyncio
    async def test_prints_dimension_breakdown(self, capsys):
        session = make_mock_session(cycles=1)
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.LearningOptimizer"),
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=session)
            from app.self_improvement.examples import example_content_improvement

            await example_content_improvement()
            captured = capsys.readouterr()
            assert "Session completed" in captured.out
            assert "Dimension scores" in captured.out


class TestExamplePerformanceAnalysis:
    @pytest.mark.asyncio
    async def test_returns_session(self):
        mock_session = make_mock_session()
        mock_trend = MagicMock()
        mock_trend.average_score = 0.7
        mock_trend.best_score = 0.9
        mock_trend.worst_score = 0.5
        mock_trend.total_improvement = 0.4
        mock_trend.trend_direction = "improving"
        mock_trend.std_deviation = 0.1
        mock_trend.plateau_detected = False
        mock_trend.plateau_cycle = None
        mock_trend.cycles_since_improvement = 0

        mock_opportunities = ["Opportunity 1"]

        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.PerformanceTracker") as m_pt,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            m_tracker = MagicMock()
            m_tracker.analyze_trend.return_value = mock_trend
            m_tracker.identify_improvement_opportunities.return_value = (
                mock_opportunities
            )
            m_tracker.estimate_convergence_cycle.return_value = 5
            m_tracker.metrics = [MagicMock()]
            m_tracker.metrics[0].score = 0.7
            m_pt.return_value = m_tracker

            from app.self_improvement.examples import example_with_performance_analysis

            result = await example_with_performance_analysis()
            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_prints_performance_analysis(self, capsys):
        mock_session = make_mock_session()
        mock_trend = MagicMock()
        mock_trend.average_score = 0.7
        mock_trend.best_score = 0.9
        mock_trend.worst_score = 0.5
        mock_trend.total_improvement = 0.4
        mock_trend.trend_direction = "improving"
        mock_trend.std_deviation = 0.1
        mock_trend.plateau_detected = False
        mock_trend.plateau_cycle = None
        mock_trend.cycles_since_improvement = 0

        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.PerformanceTracker") as m_pt,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            m_tracker = MagicMock()
            m_tracker.analyze_trend.return_value = mock_trend
            m_tracker.identify_improvement_opportunities.return_value = []
            m_tracker.estimate_convergence_cycle.return_value = None
            m_tracker.metrics = [MagicMock()]
            m_tracker.metrics[0].score = 0.7
            m_pt.return_value = m_tracker

            from app.self_improvement.examples import example_with_performance_analysis

            await example_with_performance_analysis()
            captured = capsys.readouterr()
            assert "Performance Analysis" in captured.out
            assert "Average score" in captured.out

    @pytest.mark.asyncio
    async def test_plateau_detected(self, capsys):
        mock_session = make_mock_session()
        mock_trend = MagicMock()
        mock_trend.plateau_detected = True
        mock_trend.plateau_cycle = 3
        mock_trend.cycles_since_improvement = 2
        mock_trend.average_score = 0.5
        mock_trend.best_score = 0.6
        mock_trend.worst_score = 0.4
        mock_trend.total_improvement = 0.1
        mock_trend.trend_direction = "flat"
        mock_trend.std_deviation = 0.05

        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.PerformanceTracker") as m_pt,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            m_tracker = MagicMock()
            m_tracker.analyze_trend.return_value = mock_trend
            m_tracker.identify_improvement_opportunities.return_value = []
            m_tracker.estimate_convergence_cycle.return_value = None
            m_tracker.metrics = [MagicMock()]
            m_tracker.metrics[0].score = 0.5
            m_pt.return_value = m_tracker

            from app.self_improvement.examples import example_with_performance_analysis

            await example_with_performance_analysis()
            captured = capsys.readouterr()
            assert "Plateau detected" in captured.out


class TestExampleLearningRateComparison:
    @pytest.mark.asyncio
    async def test_runs_schedules(self, capsys):
        with patch("app.self_improvement.examples.LearningOptimizer") as m_lo:
            m_lo.return_value.get_learning_rate.side_effect = lambda c, **kw: 0.1 - (
                0.09 * (c - 1) / (kw.get("max_cycles", 6) - 1)
            )

            from app.self_improvement.examples import example_learning_rate_comparison

            await example_learning_rate_comparison()
            captured = capsys.readouterr()
            assert "Learning rate over 6 cycles" in captured.out
            assert "WARMUP_THEN_DECAY" in captured.out

    @pytest.mark.asyncio
    async def test_creates_all_schedules(self):
        with patch("app.self_improvement.examples.LearningOptimizer") as m_lo:
            m_lo.return_value.get_learning_rate.return_value = 0.05

            from app.self_improvement.examples import example_learning_rate_comparison

            await example_learning_rate_comparison()
            assert m_lo.call_count >= 4


class TestExampleCustomAssessment:
    @pytest.mark.asyncio
    async def test_returns_assessment_result(self):
        mock_result = make_mock_assessment(
            score=0.6, weaknesses=["no tests", "poor security"]
        )
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.SelfAssessmentEngine") as m_sae,
        ):
            m_sae.return_value.assess = AsyncMock(return_value=mock_result)

            from app.self_improvement.examples import example_custom_assessment

            result = await example_custom_assessment()
            assert result.overall_score == 0.6
            assert "no tests" in result.weaknesses

    @pytest.mark.asyncio
    async def test_prints_assessment_details(self, capsys):
        mock_result = MagicMock()
        mock_result.overall_score = 0.65
        mock_result.strengths = ["basic structure"]
        mock_result.weaknesses = ["no error handling"]
        mock_result.dimension_scores = {"accuracy": 0.7, "security": 0.3}
        mock_result.root_causes = {"security": ["no input validation"]}
        mock_result.recommendations = ["add validation", "add tests"]

        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.SelfAssessmentEngine") as m_sae,
        ):
            m_sae.return_value.assess = AsyncMock(return_value=mock_result)

            from app.self_improvement.examples import example_custom_assessment

            await example_custom_assessment()
            captured = capsys.readouterr()
            assert "Overall score" in captured.out
            assert "Strengths" in captured.out
            assert "Weaknesses" in captured.out
            assert "Root causes" in captured.out
            assert "Recommendations" in captured.out
            assert "add validation" in captured.out

    @pytest.mark.asyncio
    async def test_handles_empty_lists(self, capsys):
        mock_result = MagicMock()
        mock_result.overall_score = 0.5
        mock_result.strengths = []
        mock_result.weaknesses = []
        mock_result.dimension_scores = {"accuracy": 0.5, "clarity": 0.5}
        mock_result.root_causes = {}
        mock_result.recommendations = []

        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.SelfAssessmentEngine") as m_sae,
        ):
            m_sae.return_value.assess = AsyncMock(return_value=mock_result)

            from app.self_improvement.examples import example_custom_assessment

            await example_custom_assessment()
            captured = capsys.readouterr()
            assert "Overall score" in captured.out


class TestMain:
    @pytest.mark.asyncio
    async def test_runs_all_examples(self):
        mock_session = make_mock_session()
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.ConsensusEngine"),
            patch("app.self_improvement.examples.SelfAssessmentEngine") as m_sae,
            patch("app.self_improvement.examples.PerformanceTracker") as m_pt,
            patch("app.self_improvement.examples.LearningOptimizer") as m_lo,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            m_sae.return_value.assess = AsyncMock(
                return_value=make_mock_assessment()
            )
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            m_lo.return_value.get_learning_rate.return_value = 0.05
            m_tracker = MagicMock()
            m_tracker.analyze_trend.return_value = MagicMock(
                average_score=0.7,
                best_score=0.9,
                worst_score=0.5,
                total_improvement=0.4,
                trend_direction="improving",
                std_deviation=0.1,
                plateau_detected=False,
                plateau_cycle=None,
                cycles_since_improvement=0,
            )
            m_tracker.identify_improvement_opportunities.return_value = []
            m_tracker.estimate_convergence_cycle.return_value = None
            m_tracker.metrics = [MagicMock()]
            m_tracker.metrics[0].score = 0.7
            m_pt.return_value = m_tracker

            from app.self_improvement.examples import main

            await main()

    @pytest.mark.asyncio
    async def test_handles_exception(self, capsys):
        with (
            patch(
                "app.self_improvement.examples.example_code_improvement",
                side_effect=ValueError("test error"),
            ),
            patch("traceback.print_exc") as m_print_exc,
        ):
            from app.self_improvement.examples import main

            await main()
            captured = capsys.readouterr()
            assert "Error during examples" in captured.out
            assert "test error" in captured.out
            m_print_exc.assert_called_once()

    @pytest.mark.asyncio
    async def test_prints_timestamp(self, capsys):
        with (
            patch("app.self_improvement.examples.agent_registry", MockAgentRegistry()),
            patch("app.self_improvement.examples.ConsensusEngine"),
            patch("app.self_improvement.examples.SelfAssessmentEngine") as m_sae,
            patch("app.self_improvement.examples.PerformanceTracker") as m_pt,
            patch("app.self_improvement.examples.LearningOptimizer") as m_lo,
            patch(
                "app.self_improvement.examples.RecursiveSelfImprovementWorkflow"
            ) as m_wf,
        ):
            mock_session = make_mock_session()
            m_sae.return_value.assess = AsyncMock(
                return_value=make_mock_assessment()
            )
            m_wf.return_value.execute = AsyncMock(return_value=mock_session)
            m_lo.return_value.get_learning_rate.return_value = 0.05
            m_tracker = MagicMock()
            m_tracker.analyze_trend.return_value = MagicMock(
                average_score=0.7,
                best_score=0.9,
                worst_score=0.5,
                total_improvement=0.4,
                trend_direction="improving",
                std_deviation=0.1,
                plateau_detected=False,
            )
            m_tracker.identify_improvement_opportunities.return_value = []
            m_tracker.estimate_convergence_cycle.return_value = None
            m_tracker.metrics = [MagicMock()]
            m_tracker.metrics[0].score = 0.7
            m_pt.return_value = m_tracker

            from app.self_improvement.examples import main

            await main()
            captured = capsys.readouterr()
            assert "Started at" in captured.out
            assert "All examples completed" in captured.out
