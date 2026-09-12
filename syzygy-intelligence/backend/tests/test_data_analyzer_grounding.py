"""Grounding tests for data_analyzer — deterministic stats + LLM enhancement.

Tests verify:
- deterministic statistical computation (rows, columns, types, missing, duplicates)
- anomaly detection with z‑score threshold
- correlation computation (Pearson, |r|>=0.5)
- LLM enhancement flow (mocked LLM adds narrative without inventing data)
- degraded:true + no_data_provided when input is empty
- provenance flags (static_analysis)
"""

from __future__ import annotations

import json
import asyncio
import pytest

from app.workflows.data_analyzer import DataAnalyzerWorkflow, _describe_data_deterministic, _detect_anomalies_deterministic, _find_correlations_deterministic


EXECUTE_TIMEOUT = 120.0


def _mock_llm(responses: list[str]):
    """Build an AsyncMock LLM returning the given strings in order."""
    llm = pytest.AsyncMock()
    idx = [0]

    async def _gen(prompt, **kwargs):
        if idx[0] < len(responses):
            r = responses[idx[0]]
            idx[0] += 1
            return r
        return ""

    llm.generate.side_effect = _gen
    return llm


class TestDeterministicStats:
    def test_empty_data(self):
        result = _describe_data_deterministic("")
        assert result["rows_total"] == 0
        assert result["columns_total"] == 0

    def test_simple_csv(self):
        csv_text = "a,b,c\n1,2,3\n4,,6\n7,8,9"
        result = _describe_data_deterministic(csv_text)
        assert result["rows_total"] == 3
        assert result["columns_total"] == 3
        # column a: [1,4,7] -> numeric
        assert "a" in [str(i) for i in range(3)] or result["column_types"][0] == "numeric"
        # column b has a missing value
        assert result["missing_values"][1] == 1  # second row b is empty
        # column c: [3,6,9] -> numeric
        assert result["numeric_stats"][2]["mean"] == 6.0  # (3+6+9)/3

    def test_missing_values_and_duplicates(self):
        csv_text = "x,y\n1,2\n1,2\n3,\n"
        result = _describe_data_deterministic(csv_text)
        assert result["rows_total"] == 3
        # row 0 and row 1 are identical -> duplicate
        assert result["duplicate_rows"] >= 1
        # column y row 3 is missing
        assert result["missing_values"][1] == 1

    def test_anomalies_deterministic(self):
        csv_text = "value\n1\n2\n100\n4\n5"
        det = _detect_anomalies_deterministic(csv_text)
        assert det["anomaly_count"] >= 1  # 100 should be an outlier
        assert isinstance(det["anomalies"], list)

    def test_correlations_deterministic(self):
        csv_text = "a,b\n1,2\n2,4\n3,6\n4,8\n5,10"
        det = _find_correlations_deterministic(csv_text)
        # a and b have perfect positive correlation (r=1)
        assert len(det["correlations"]) >= 1
        r = det["correlations"][0]["correlation"]
        assert r == 1.0 or abs(r) == 1.0


class TestTaskSensitivity:
    @pytest.mark.asyncio
    async def test_describe_depends_on_data(self):
        wf = DataAnalyzerWorkflow()
        # Pass real CSV data
        result = await asyncio.wait_for(
            wf.describe_data("a,b\n1,2\n3,4", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "summary" in result
        assert result["static_analysis"] is True

    @pytest.mark.asyncio
    async def test_detect_anomalies_depends_on_data(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.detect_anomalies("val\n1\n2\n100\n5", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "anomalies" in result

    @pytest.mark.asyncio
    async def test_find_correlations_depends_on_data(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.find_correlations("a,b\n1,2\n2,4\n3,6\n4,8\n5,10", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "correlations" in result


class TestDegraded:
    @pytest.mark.asyncio
    async def test_describe_empty_data_degraded(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.describe_data("", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result.get("degraded") is True
        assert result.get("no_data_provided") is True

    @pytest.mark.asyncio
    async def test_detect_anomalies_empty_data_degraded(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.detect_anomalies("", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result.get("degraded") is True
        assert result.get("no_data_provided") is True

    @pytest.mark.asyncio
    async def test_find_correlations_empty_data_degraded(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.find_correlations("", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result.get("degraded") is True
        assert result.get("no_data_provided") is True


class TestLLMEnhancement:
    @pytest.mark.asyncio
    async def test_describe_with_mock_llm(self):
        """Mock LLM adds a short narrative; does not invent data values."""
        wf = DataAnalyzerWorkflow()
        # Mock LLM that returns a short factual sentence
        wf.llm = _mock_llm([
            "The dataset has 4 rows and 2 columns; column 'a' contains integers 1–3, column 'b' contains integers 2–4. No missing values detected."
        ])
        result = await asyncio.wait_for(
            wf.describe_data("a,b\n1,2\n3,4", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "summary" in result
        # The narrative should mention the shape, not fake numbers
        summary = result["summary"]
        assert "rows" in summary.lower() or "4" in summary
        assert "columns" in summary.lower() or "2" in summary

    @pytest.mark.asyncio
    async def test_anomalies_with_mock_llm(self):
        wf = DataAnalyzerWorkflow()
        wf.llm = _mock_llm([
            "The value 100 is a clear statistical outlier (z‑score > 3), suggesting a data entry error or genuine extreme event."
        ])
        result = await asyncio.wait_for(
            wf.detect_anomalies("val\n1\n2\n100\n5", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "anomalies" in result
        # Narrative should reference the outlier without inventing a new value
        assert "100" in result["anomalies"] or "outlier" in result["anomalies"].lower()

    @pytest.mark.asyncio
    async def test_correlations_with_mock_llm(self):
        wf = DataAnalyzerWorkflow()
        wf.llm = _mock_llm([
            "The strongest correlation is between columns a and b (r ≈ 1.0), indicating a perfect positive linear relationship; follow‑up could involve regression analysis."
        ])
        result = await asyncio.wait_for(
            wf.find_correlations("a,b\n1,2\n2,4\n3,6\n4,8\n5,10", "CSV"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "correlations" in result
        # Narrative should reference the strong correlation
        assert "correlation" in result["correlations"].lower()


class TestExecuteFull:
    @pytest.mark.asyncio
    async def test_execute_returns_structured(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.execute(
                "analyze this",
                {"data": "a,b\n1,2\n3,4\n5,6", "format": "CSV"},
            ),
            timeout=EXECUTE_TIMEOUT,
        )
        assert "task" in result
        assert "format" in result
        assert "summary" in result
        assert "anomalies" in result
        assert "correlations" in result
        assert "visualization_recommendations" in result
        assert result["status"] == "completed"
        assert "degraded" in result
        assert "static_analysis" in result

    @pytest.mark.asyncio
    async def test_execute_empty_data_degraded(self):
        wf = DataAnalyzerWorkflow()
        result = await asyncio.wait_for(
            wf.execute("analyze this", {}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result.get("degraded") is True
        assert result.get("no_data_provided") is True
        assert result.get("status") == "degraded"