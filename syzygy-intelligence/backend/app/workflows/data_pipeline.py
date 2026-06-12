"""Data Pipeline workflow — ingest, clean, transform, validate, and load data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class DataPipelineWorkflow:
    """ETL pipeline — ingest from CSV/JSON/API, clean, transform, validate schema, load to target."""

    name: str = "data_pipeline"
    description: str = "ETL pipeline — ingest, clean, transform, validate schema, and load data"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["data_ingestion", "data_cleaning", "schema_validation", "transformation"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = OllamaClient()

    async def ingest(self, source: str, source_type: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Analyze the following data source for ingestion:\n\n"
            f"Source: {source[:2000]}\n"
            f"Type: {source_type}\n\n"
            f"Describe:\n"
            f"1. Detected format and structure\n"
            f"2. Column names and inferred data types\n"
            f"3. Record count estimate\n"
            f"4. Encoding and delimiter (if tabular)\n"
            f"5. Potential ingestion issues (malformed rows, encoding problems)"
        )
        analysis = await self.llm.generate(prompt, temperature=0.2)
        return {"analysis": analysis, "source_type": source_type}

    async def clean(self, data: str, issues: list[str]) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Generate a data cleaning plan for the following data:\n\n{data[:2000]}\n\n"
            f"Issues to address: {', '.join(issues) if issues else 'Auto-detect'}\n\n"
            f"For each issue provide:\n"
            f"1. The specific problem\n"
            f"2. Cleaning strategy (remove, impute, transform)\n"
            f"3. Code snippet to implement the fix\n"
            f"4. Impact assessment (rows affected, data loss risk)"
        )
        plan = await self.llm.generate(prompt, temperature=0.2)
        return {"cleaning_plan": plan}

    async def transform(self, data: str, transformations: list[str]) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Design data transformations for:\n\n{data[:2000]}\n\n"
            f"Required transformations: "
            f"{', '.join(transformations) if transformations else 'Normalize and structure'}\n\n"
            f"For each transformation provide:\n"
            f"1. Input → Output mapping\n"
            f"2. Logic description\n"
            f"3. Edge cases handled\n"
            f"4. Code implementation"
        )
        transformed = await self.llm.generate(prompt, temperature=0.3)
        return {"transformations": transformed}

    async def validate_schema(self, data: str, target_schema: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Validate the following data against the target schema:\n\n"
            f"Data:\n{data[:2000]}\n\n"
            f"Target Schema:\n{target_schema[:1000]}\n\n"
            f"Check:\n"
            f"1. Column presence and naming\n"
            f"2. Data type compatibility\n"
            f"3. Nullability / required fields\n"
            f"4. Constraint violations (unique, foreign key, range)\n"
            f"5. Overall compatibility score (1-10)"
        )
        validation = await self.llm.generate(prompt, temperature=0.2)
        return {"validation": validation}

    async def load_plan(self, data: str, target: str) -> str:
        assert self.llm is not None
        prompt = (
            f"Create a data loading plan for:\n\n"
            f"Data summary: {data[:1500]}\n"
            f"Target: {target}\n\n"
            f"Provide:\n"
            f"1. Load strategy (full refresh / incremental / upsert)\n"
            f"2. Batch size recommendations\n"
            f"3. Error handling approach\n"
            f"4. Rollback plan\n"
            f"5. Performance considerations\n"
            f"6. Monitoring and alerting suggestions"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        source = ctx.get("source_data", task)
        source_type = ctx.get("source_type", "CSV")
        issues = ctx.get("known_issues", [])
        transformations = ctx.get("transformations", [])
        target_schema = ctx.get("target_schema", "")
        target = ctx.get("target", "database")

        logger.info("Data Pipeline workflow started", source_type=source_type, target=target)
        ingestion = await self.ingest(source, source_type)
        cleaning = await self.clean(source, issues)
        transformation = await self.transform(source, transformations)
        validation = {}
        if target_schema:
            validation = await self.validate_schema(source, target_schema)
        load = await self.load_plan(source, target)

        result = {
            "task": task,
            "source_type": source_type,
            "target": target,
            "ingestion_analysis": ingestion,
            "cleaning_plan": cleaning,
            "transformations": transformation,
            "schema_validation": validation,
            "load_plan": load,
            "status": "completed",
        }
        logger.info("Data Pipeline workflow completed")
        return result


DATA_PIPELINE_WORKFLOW = DataPipelineWorkflow()
