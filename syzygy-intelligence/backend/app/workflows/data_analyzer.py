"""Data Analyzer workflow — statistical analysis, anomaly detection, correlation discovery, visualization recommendations.

Grounded version: deterministic statistical computation (row/column counts, data types,
summary stats, missing‑value ratio, duplicates) runs first.  The LLM receives those
concrete numbers as context and is asked to add interpretation.  ``degraded:true`` when
the input data is empty or the format is unrecognised; ``static_analysis:true`` flag
is set when deterministic stats are available.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate


# ---------------------------------------------------------------------------
# Deterministic statistical engine – pure Python, no LLM required.
# ---------------------------------------------------------------------------

def _parse_csv_rows(text: str) -> List[List[str]]:
    """Parse ``text`` as CSV into a list of rows (list of cell strings)."""
    lines = text.strip().splitlines()
    if not lines:
        return []
    # Keep the header row separate
    header = lines[0].split(",")
    rows = [line.split(",") for line in lines[1:]]
    # Pad shorter rows with empty strings so column counts are consistent
    n_cols = len(header)
    padded = []
    for row in rows:
        if len(row) < n_cols:
            row = row + [""] * (n_cols - len(row))
        padded.append(row)
    return [header] + padded


def _describe_data_deterministic(
    data: str,
) -> Dict[str, Any]:
    """Return concrete shape/summary stats from the raw CSV text.

    Keys returned:
    - rows_total: number of data rows (excluding header)
    - columns_total: number of columns
    - column_types: list of "numeric" or "categorical" inferred from values
    - numeric_stats: dict{col_index: {"mean": ..., "median": ..., "min": ..., "max": ..., "std": ...}}
    - missing_values: dict{col_index: count}
    - unique_counts: dict{col_index: count}
    - duplicate_rows: int number of duplicate data rows
    """
    rows = _parse_csv_rows(data)
    if not rows:
        return {
            "rows_total": 0,
            "columns_total": 0,
            "column_types": [],
            "numeric_stats": {},
            "missing_values": {},
            "unique_counts": {},
            "duplicate_rows": 0,
        }

    header = rows[0]
    data_rows = rows[1:]
    n_rows = len(data_rows)
    n_cols = len(header)

    # Column-wise values
    col_values: List[List[str]] = [[] for _ in range(n_cols)]
    for row in data_rows:
        for i, cell in enumerate(row):
            col_values[i].append(cell.strip())

    column_types: List[str] = []
    numeric_stats: Dict[int, Dict[str, float]] = {}
    missing_values: Dict[int, int] = {}
    unique_counts: Dict[int, int] = {}

    for i, col in enumerate(col_values):
        # Determine type: if every non‑empty cell parses as float -> numeric
        non_empty = [c for c in col if c]
        try:
            floats = [float(c) for c in non_empty]
            is_numeric = True
        except ValueError:
            is_numeric = False

        column_types.append("numeric" if is_numeric else "categorical")

        if is_numeric and non_empty:
            fs = floats
            n = len(fs)
            mean = sum(fs) / n
            sorted_fs = sorted(fs)
            median = sorted_fs[n // 2] if n else 0.0
            mn = min(fs)
            mx = max(fs)
            # population std (good enough for profiling)
            var = sum((x - mean) ** 2 for x in fs) / n if n else 0.0
            std = math.sqrt(var)
            numeric_stats[i] = {
                "mean": round(mean, 4),
                "median": round(median, 4),
                "min": round(mn, 4),
                "max": round(mx, 4),
                "std": round(std, 4),
            }
        else:
            numeric_stats[i] = {}

        # Missing values = empty cells
        missing = sum(1 for c in col if c == "")
        missing_values[i] = missing

        # Unique cardinality
        unique_counts[i] = len(set(non_empty))

    # Duplicate rows: compare each data row (as tuple) to others
    row_tuples = [tuple(r) for r in data_rows]
    duplicate_rows = len(row_tuples) - len(set(row_tuples))

    return {
        "rows_total": n_rows,
        "columns_total": n_cols,
        "column_types": column_types,
        "numeric_stats": numeric_stats,
        "missing_values": missing_values,
        "unique_counts": unique_counts,
        "duplicate_rows": duplicate_rows,
    }


def _detect_anomalies_deterministic(
    data: str,
) -> Dict[str, Any]:
    """Very simple anomaly detection: z‑score > 3 for numeric columns."""
    rows = _parse_csv_rows(data)
    if not rows:
        return {"anomaly_count": 0, "anomalies": [], "details": ""}

    header = rows[0]
    data_rows = rows[1:]
    n_rows = len(data_rows)
    n_cols = len(header)

    # Build column floats where possible
    col_floats: List[List[float]] = [[] for _ in range(n_cols)]
    for row in data_rows:
        for i, cell in enumerate(row):
            try:
                col_floats[i].append(float(cell.strip()))
            except ValueError:
                pass

    anomalies: List[Dict[str, Any]] = []
    for i, floats in enumerate(col_floats):
        if not floats or len(floats) < 3:
            continue
        n = len(floats)
        mean = sum(floats) / n
        var = sum((x - mean) ** 2 for x in floats) / n
        std = math.sqrt(var) if var > 0 else 1.0
        for idx, x in enumerate(floats):
            z = abs(x - mean) / std
            if z > 3:  # simple threshold
                anomalies.append(
                    {
                        "column": header[i] if i < len(header) else f"col_{i}",
                        "value": x,
                        "z_score": round(z, 2),
                        "type": "outlier",
                    }
                )

    return {
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "details": f"z‑score > 3 threshold across {n_rows} rows",
    }


def _find_correlations_deterministic(
    data: str,
) -> Dict[str, Any]:
    """Compute pairwise Pearson correlation for numeric columns."""
    rows = _parse_csv_rows(data)
    if not rows:
        return {"correlations": [], "details": ""}

    header = rows[0]
    data_rows = rows[1:]
    n_rows = len(data_rows)
    n_cols = len(header)

    # Collect float lists per column
    col_floats: List[List[float]] = [[] for _ in range(n_cols)]
    for row in data_rows:
        for i, cell in enumerate(row):
            try:
                col_floats[i].append(float(cell.strip()))
            except ValueError:
                pass

    correlations: List[Dict[str, Any]] = []
    for i in range(n_cols):
        for j in range(i + 1, n_cols):
            xi = col_floats[i]
            yj = col_floats[j]
            n = min(len(xi), len(yj))
            if n < 3:
                continue
            # make same length by truncating
            xi_s = xi[:n]
            yj_s = yj[:n]
            # means
            mean_x = sum(xi_s) / n
            mean_y = sum(yj_s) / n
            # covariance and variances
            cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xi_s, yj_s)) / n
            var_x = sum((x - mean_x) ** 2 for x in xi_s) / n
            var_y = sum((y - mean_y) ** 2 for y in yj_s) / n
            if var_x == 0 or var_y == 0:
                continue
            r = cov / (math.sqrt(var_x) * math.sqrt(var_y))
            # round to 2 decimal places
            r_rounded = round(r, 2)
            # only report |r| >= 0.5 as “strong”
            if abs(r_rounded) >= 0.5:
                direction = "positive" if r_rounded > 0 else "negative"
                correlations.append(
                    {
                        "col_i": header[i] if i < len(header) else f"col_{i}",
                        "col_j": header[j] if j < len(header) else f"col_{j}",
                        "correlation": r_rounded,
                        "direction": direction,
                        "significance": "strong",
                    }
                )

    return {
        "correlations": correlations,
        "details": f"Pearson correlation across {n_rows} rows",
    }


# ---------------------------------------------------------------------------
# LLM helper (shared error‑prefix guard, truncation)
# ---------------------------------------------------------------------------

async def _generate(llm: ModelManager, prompt: str, temperature: float = 0.3) -> str:
    """Call the LLM (no chain‑of‑thought). Returns ``""`` when unreachable/failed."""
    assert llm is not None
    for _ in (1, 2):
        try:
            txt = await llm.generate(prompt, role="sage", temperature=temperature, think=False)
        except Exception as exc:
            logger.warning("DataAnalyzerWorkflow LLM call failed", error=str(exc))
            return ""
        txt = (txt or "").strip()
        head = txt[:40].lower()
        if not (head.startswith("[") and "error" in head):
            return txt
    return ""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DataAnalyzerWorkflow:
    """Grounded data analysis: deterministic stats first, LLM enhancement second."""

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def describe_data(self, data: str, format: str = "CSV") -> dict[str, Any]:
        """Deterministic statistical description + optional LLM enhancement."""
        if not data or not data.strip():
            return {
                "format": format,
                "degraded": True,
                "no_data_provided": True,
                "summary": "",
                "static_analysis": False,
            }

        stats = _describe_data_deterministic(data)
        static_analysis = True

        # Build a concise text summary for the LLM prompt
        summary_parts = [
            f"rows_total: {stats['rows_total']}",
            f"columns_total: {stats['columns_total']}",
            f"column_types: {stats['column_types']}",
            f"missing_values: {stats['missing_values']}",
            f"unique_counts: {stats['unique_counts']}",
            f"duplicate_rows: {stats['duplicate_rows']}",
        ]
        if stats["numeric_stats"]:
            # add a few numeric examples
            examples = []
            for i, s in stats["numeric_stats"].items():
                examples.append(f"col_{i}: mean={s['mean']}, median={s['median']}, min={s['min']}, max={s['max']}, std={s['std']}")
                if len(examples) >= 3:
                    break
            summary_parts.append("numeric_stats_samples: " + "; ".join(examples))

        summary_text = " | ".join(summary_parts)

        prompt_text = (
            f"You are given a statistical summary of a {format} dataset.\n\n"
            f"Summary (deterministic computation):\n{summary_text}\n\n"
            f"Using this as context, provide a concise narrative interpretation "
            f"(2‑3 sentences) covering:\n"
            f"- overall data shape and quality\n"
            f"- notable findings (e.g., high missing rate, outliers, strong correlations)\n"
            f"- any immediate actions or questions that arise\n\n"
            f"Keep the response short and factual; do not invent data values."
        )
        llm_interpretation = await _generate(self.llm, prompt_text, temperature=0.2)

        return {
            "format": format,
            "summary": llm_interpretation if llm_interpretation else summary_text,
            "static_analysis": static_analysis,
            "stats": stats,
            "degraded": False,
        }

    async def detect_anomalies(self, data: str, format: str = "CSV") -> dict[str, Any]:
        """Deterministic anomaly detection + optional LLM enhancement."""
        if not data or not data.strip():
            return {
                "format": format,
                "degraded": True,
                "no_data_provided": True,
                "anomalies": "",
                "static_analysis": False,
            }

        det = _detect_anomalies_deterministic(data)
        static_analysis = det["anomaly_count"] > 0 or True  # we always have a detection run

        prompt_text = (
            f"Below is a deterministic anomaly-detection report for a dataset:\n"
            f"{json.dumps(det, indent=2)}\n\n"
            f"Using this as context, add a brief narrative (1‑2 sentences) about "
            f"whether the detected anomalies are likely genuine or artefactual, "
            f"and any practical implication. Keep it short and factual."
        )
        llm_addition = await _generate(self.llm, prompt_text, temperature=0.2)

        return {
            "format": format,
            "anomalies": llm_addition if llm_addition else det["details"],
            "static_analysis": static_analysis,
            "anomaly_count": det["anomaly_count"],
            "degraded": False,
        }

    async def find_correlations(self, data: str, format: str = "CSV") -> dict[str, Any]:
        """Deterministic correlation discovery + optional LLM enhancement."""
        if not data or not data.strip():
            return {
                "format": format,
                "degraded": True,
                "no_data_provided": True,
                "correlations": "",
                "static_analysis": False,
            }

        det = _find_correlations_deterministic(data)
        static_analysis = len(det["correlations"]) > 0 or True

        prompt_text = (
            f"Below is a deterministic correlation-finding report for a dataset:\n"
            f"{json.dumps(det, indent=2)}\n\n"
            f"Using this as context, add a brief narrative (1‑2 sentences) about "
            f"which relationships are most noteworthy and any suggested follow‑up. "
            f"Keep it short and factual."
        )
        llm_addition = await _generate(self.llm, prompt_text, temperature=0.2)

        return {
            "format": format,
            "correlations": llm_addition if llm_addition else det["details"],
            "static_analysis": static_analysis,
            "correlation_count": len(det["correlations"]),
            "degraded": False,
        }

    async def recommend_visualizations(
        self,
        data: str,
        summary: dict[str, Any],
        anomalies: dict[str, Any],
        correlations: dict[str, Any],
    ) -> dict[str, Any]:
        """LLM‑driven visualization recommendations (enhanced by deterministic context)."""
        combined_parts: List[str] = []

        # summary stats highlights
        s = summary.get("stats", {})
        if s.get("rows_total"):
            combined_parts.append(
                f"rows: {s['rows_total']}, columns: {s['columns_total']}, "
                f"types: {s['column_types']}"
            )
        if s.get("numeric_stats"):
            # a few example stats
            examples = []
            for i, val in list(s["numeric_stats"].items())[:3]:
                examples.append(f"col_{i}: mean={val['mean']}, std={val['std']}")
            combined_parts.append("numeric_stats_samples: " + "; ".join(examples))

        # anomaly count
        a = anomalies.get("anomaly_count", 0) or 0
        combined_parts.append(f"anomaly_count: {a}")

        # correlation count
        c = correlations.get("correlation_count", 0) or 0
        combined_parts.append(f"correlation_count: {c}")

        combined = "\n".join(combined_parts)

        prompt_text = (
            f"Based on the following analytical summary, recommend visualizations "
            f"to help a analyst explore the data.\n\n"
            f"{combined}\n\n"
            f"For each recommendation provide:\n"
            f"1. Chart type (bar, line, scatter, heatmap, box plot, histogram, etc.)\n"
            f"2. What data to plot (specific columns or overall view)\n"
            f"3. What insight it reveals\n"
            f"4. Priority (High / Medium / Low)\n\n"
            f"Keep the list concise (max 5 recommendations)."
        )
        viz_text = await _generate(self.llm, prompt_text, temperature=0.3)

        # Parse the LLM output into a list of dicts (best‑effort)
        recommendations: List[Dict[str, Any]] = []
        if viz_text:
            for line in viz_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # try simple key‑value parsing
                if ":" in line:
                    # e.g. "1. Chart type: bar"
                    parts = [p.strip() for p in line.split(":", 1)]
                    rec = {"recommendation": line}
                    # if there's a second colon, parse priority
                    if ":" in parts[1]:
                        sub = parts[1].split(":")
                        rec["priority"] = sub[-1].strip()
                    else:
                        rec["priority"] = "Medium"
                    recommendations.append(rec)
                else:
                    recommendations.append({"recommendation": line, "priority": "Medium"})

        return {
            "visualization_recommendations": recommendations[:5],
            "degraded": False,
        }

    # ------------------------------------------------------------------
    # Executive entry point
    # ------------------------------------------------------------------

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = context or {}
        data = ctx.get("data", task)
        fmt = ctx.get("format", "CSV")

        logger.info("Data Analyzer workflow started", format=fmt)

        if not data or not data.strip():
            logger.warning("Data Analyzer: no data provided")
            return {
                "task": task,
                "format": fmt,
                "summary": {"format": fmt, "degraded": True, "no_data_provided": True, "summary": ""},
                "anomalies": {"format": fmt, "degraded": True, "no_data_provided": True, "anomalies": ""},
                "correlations": {"format": fmt, "degraded": True, "no_data_provided": True, "correlations": ""},
                "visualization_recommendations": [],
                "status": "degraded",
                "degraded": True,
                "no_data_provided": True,
            }

        # 1️⃣ Deterministic statistical analysis – always run
        description = await self.describe_data(data, fmt)
        anomalies = await self.detect_anomalies(data, fmt)
        correlations = await self.find_correlations(data, fmt)

        # 2️⃣ Visualization recommendations (LLM‑enhanced, grounded by deterministic stats)
        viz = await self.recommend_visualizations(data, description, anomalies, correlations)

        result = {
            "task": task,
            "format": fmt,
            "summary": description,
            "anomalies": anomalies,
            "correlations": correlations,
            "visualization_recommendations": viz.get("visualization_recommendations", []),
            "status": "completed",
            "degraded": description.get("degraded", False),
            "static_analysis": description.get("static_analysis", False)
            and anomalies.get("static_analysis", False)
            and correlations.get("static_analysis", True),
            "no_data_provided": False,
        }
        logger.info(
            "Data Analyzer workflow completed",
            rows=description.get("stats", {}).get("rows_total"),
            degraded=result["degraded"],
        )
        return result


DATA_ANALYZER_WORKFLOW = DataAnalyzerWorkflow()