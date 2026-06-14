"""Data Analyzer workflow — statistical analysis, anomaly detection, correlation discovery, visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger


@dataclass
class DataAnalyzerWorkflow:
    """Statistical analysis, anomaly detection, correlation discovery, and visualization recommendations."""

    name: str = "data_analyzer"
    description: str = (
        "Statistical analysis, anomaly detection, "
        "correlation discovery, and visualization recommendations"
    )
    required_capabilities: list[str] = field(
        default_factory=lambda: ["statistical_analysis", "anomaly_detection", "visualization"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def describe_data(self, data: str, format: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Analyze the following {format} data and provide a statistical summary:\n\n"
            f"{data[:3000]}\n\n"
            f"Describe:\n"
            f"1. Data shape — rows, columns, data types\n"
            f"2. Summary statistics — mean, median, min, max, std for numeric columns\n"
            f"3. Distribution — skewness, outliers, missing values\n"
            f"4. Unique values — cardinality of categorical columns\n"
            f"5. Data quality issues — duplicates, nulls, inconsistencies"
        )
        summary = await self.llm.generate(prompt, temperature=0.2)
        return {"summary": summary, "format": format}

    async def detect_anomalies(self, data: str, format: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Detect anomalies in the following {format} data:\n\n"
            f"{data[:3000]}\n\n"
            f"Identify:\n"
            f"1. Statistical outliers (z-score / IQR based)\n"
            f"2. Trend anomalies — unexpected spikes or drops\n"
            f"3. Correlation anomalies — relationships that break expected patterns\n"
            f"4. Data integrity issues — impossible values, broken constraints\n"
            f"5. Seasonality breaches — values outside expected seasonal ranges\n\n"
            f"Rate each anomaly: Critical / Major / Minor"
        )
        anomalies = await self.llm.generate(prompt, temperature=0.2)
        return {"anomalies": anomalies}

    async def find_correlations(self, data: str, format: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Discover correlations and relationships in the following {format} data:\n\n"
            f"{data[:3000]}\n\n"
            f"Find:\n"
            f"1. Strong positive correlations (e.g., >0.7)\n"
            f"2. Strong negative correlations (e.g., <-0.7)\n"
            f"3. Non-linear relationships\n"
            f"4. Causal-looking patterns (caveated)\n"
            f"5. Confounding variables to consider\n\n"
            f"For each, state confidence level and suggested follow-up."
        )
        correlations = await self.llm.generate(prompt, temperature=0.3)
        return {"correlations": correlations}

    async def recommend_visualizations(
        self, data: str, summary: dict[str, Any],
        anomalies: dict[str, Any], correlations: dict[str, Any],
    ) -> str:
        assert self.llm is not None
        combined = (
            f"Data Summary:\n{summary.get('summary', 'N/A')[:1000]}\n\n"
            f"Anomalies:\n{anomalies.get('anomalies', 'N/A')[:1000]}\n\n"
            f"Correlations:\n{correlations.get('correlations', 'N/A')[:1000]}"
        )
        prompt = (
            f"Based on this analysis, recommend visualizations:\n\n{combined}\n\n"
            f"For each recommendation provide:\n"
            f"1. Chart type (bar, line, scatter, heatmap, box plot, histogram, etc.)\n"
            f"2. What data to plot (specific columns)\n"
            f"3. What insight it reveals\n"
            f"4. Priority (High / Medium / Low)"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        data = ctx.get("data", task)
        format = ctx.get("format", "CSV")

        logger.info("Data Analyzer workflow started", format=format)
        summary = await self.describe_data(data, format)
        anomalies = await self.detect_anomalies(data, format)
        correlations = await self.find_correlations(data, format)
        viz = await self.recommend_visualizations(data, summary, anomalies, correlations)

        result = {
            "task": task,
            "format": format,
            "summary": summary,
            "anomalies": anomalies,
            "correlations": correlations,
            "visualization_recommendations": viz,
            "status": "completed",
        }
        logger.info("Data Analyzer workflow completed")
        return result


DATA_ANALYZER_WORKFLOW = DataAnalyzerWorkflow()
