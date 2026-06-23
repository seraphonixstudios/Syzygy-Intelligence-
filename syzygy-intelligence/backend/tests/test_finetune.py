"""Tests for the fine-tuning workflow module — demo/simulated mode."""

from __future__ import annotations

import json
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workflows.finetune import (
    DEFAULT_HYPERPARAMS,
    FINETUNE_WORKFLOW,
    FineTuneConfig,
    FineTuneWorkflow,
    TrainingMetrics,
)


@pytest.fixture
def workflow() -> FineTuneWorkflow:
    return FineTuneWorkflow()


class TestFineTuneConfig:
    def test_default_config(self) -> None:
        cfg = FineTuneConfig()
        assert cfg.model_name == "tinyllama:latest"
        assert cfg.method == "qlora"
        assert cfg.hyperparams["learning_rate"] == DEFAULT_HYPERPARAMS["learning_rate"]

    def test_custom_config(self) -> None:
        cfg = FineTuneConfig(model_name="llama3.2:3b", method="lora", hyperparams={"learning_rate": 1e-4})
        assert cfg.model_name == "llama3.2:3b"
        assert cfg.method == "lora"
        assert cfg.hyperparams["learning_rate"] == 1e-4

    def test_invalid_method_build_config(self) -> None:
        wf = FineTuneWorkflow()
        cfg = wf._build_config("test", {"method": "invalid"})
        assert cfg.method == "qlora"  # _build_config validates and falls back

    def test_target_modules_default(self) -> None:
        cfg = FineTuneConfig()
        assert "q_proj" in cfg.target_modules
        assert len(cfg.target_modules) == 4


class TestTrainingMetrics:
    def test_default_values(self) -> None:
        m = TrainingMetrics()
        assert m.total_steps == 0
        assert m.final_loss == 0.0
        assert m.loss_points == []

    def test_add_loss_points(self) -> None:
        m = TrainingMetrics()
        m.loss_points.append({"step": 1, "loss": 2.5})
        m.loss_points.append({"step": 2, "loss": 1.8})
        assert len(m.loss_points) == 2
        assert m.loss_points[-1]["loss"] == 1.8


class TestFineTuneWorkflow:
    @pytest.mark.asyncio
    async def test_execute_simulated_returns_result_dict(self, workflow: FineTuneWorkflow) -> None:
        result = await workflow.execute(
            task="Fine-tune on custom data",
            context={"dataset_text": "Example 1\nExample 2\nExample 3", "method": "qlora"},
        )
        assert isinstance(result, dict)
        assert result["status"] == "completed"
        assert result["model"] == "tinyllama:latest"
        assert result["method"] == "qlora"

    @pytest.mark.asyncio
    async def test_execute_returns_metrics(self, workflow: FineTuneWorkflow) -> None:
        result = await workflow.execute(task="Test task", context={"dataset_text": "Sample data"})
        metrics = result["metrics"]
        assert metrics["total_steps"] > 0
        assert metrics["final_loss"] > 0
        assert metrics["perplexity"] > 0
        assert len(metrics["loss_curve"]) > 0

    @pytest.mark.asyncio
    async def test_execute_includes_config(self, workflow: FineTuneWorkflow) -> None:
        result = await workflow.execute(task="Test", context={"model": "llama3.2:3b", "method": "lora"})
        cfg = result["config"]
        assert cfg["model"] == "llama3.2:3b"
        assert cfg["method"] == "lora"

    @pytest.mark.asyncio
    async def test_execute_simulated_progress_callback(self, workflow: FineTuneWorkflow) -> None:
        callback = AsyncMock()
        result = await workflow.execute(
            task="Test",
            context={"dataset_text": "Test data"},
            on_progress=callback,
        )
        assert callback.called
        calls = [c.args for c in callback.call_args_list]
        step_names = {c[0] for c in calls}
        assert "initializing" in step_names
        assert "training" in step_names
        assert "complete" in step_names
        # Verify progress percentages are in order
        percentages = [c[1] for c in calls]
        assert percentages == sorted(percentages)

    @pytest.mark.asyncio
    async def test_execute_simulated_loss_curve_decays(self, workflow: FineTuneWorkflow) -> None:
        result = await workflow.execute(task="Test", context={"dataset_text": "Train data"})
        losses = [pt["loss"] for pt in result["metrics"]["loss_curve"]]
        # Final loss should be lower than initial
        assert losses[-1] < losses[0]
        # Loss should be non-negative
        assert all(l >= 0 for l in losses)

    @pytest.mark.asyncio
    async def test_execute_json_task(self, workflow: FineTuneWorkflow) -> None:
        task_json = json.dumps({
            "model": "mistral:7b",
            "method": "qlora",
            "hyperparams": {"learning_rate": 1e-4, "num_epochs": 5},
        })
        result = await workflow.execute(task=task_json, context={"dataset_text": "Data"})
        assert result["config"]["model"] == "mistral:7b"
        assert result["config"]["method"] == "qlora"
        assert result["config"]["hyperparams"]["learning_rate"] == 1e-4
        assert result["config"]["hyperparams"]["num_epochs"] == 5

    @pytest.mark.asyncio
    async def test_execute_hf_dataset(self, workflow: FineTuneWorkflow) -> None:
        result = await workflow.execute(task="Test", context={"hf_dataset": "databricks/databricks-dolly-15k", "dataset_source": "hf", "method": "lora"})
        assert result["status"] == "completed"
        assert result["config"]["dataset_source"] == "hf"

    @pytest.mark.asyncio
    async def test_execute_default_dataset_when_no_source(self, workflow: FineTuneWorkflow) -> None:
        result = await workflow.execute(task="Test", context={"method": "full"})
        assert result["status"] == "completed"
        assert result["method"] == "full"

    @pytest.mark.asyncio
    async def test_ml_check_returns_false_without_deps(self, workflow: FineTuneWorkflow) -> None:
        assert workflow._ml_available is False

    @pytest.mark.asyncio
    async def test_execute_no_context(self, workflow: FineTuneWorkflow) -> None:
        """Should work with just a task string and no context."""
        result = await workflow.execute(task="Train a model")
        assert result["status"] == "completed"

    def test_get_status_idle(self, workflow: FineTuneWorkflow) -> None:
        status = workflow.get_status()
        assert status["status"] == "idle"
        assert status["trainable_params"] == 0

    def test_build_config_invalid_json(self, workflow: FineTuneWorkflow) -> None:
        cfg = workflow._build_config("not json at all", {})
        assert cfg.method == "qlora"
        assert cfg.model_name == "tinyllama:latest"

    def test_ml_available_property(self) -> None:
        wf = FineTuneWorkflow()
        # Without torch/transformers, this should be False
        assert wf._ml_available is False

    @pytest.mark.asyncio
    async def test_execute_with_callbacks_all_phases(self, workflow: FineTuneWorkflow) -> None:
        callback = AsyncMock()
        await workflow.execute(task="Test", context={"dataset_text": "x"}, on_progress=callback)
        all_args = [c.args for c in callback.call_args_list]
        phases = [a[0] for a in all_args]
        assert "initializing" in phases
        assert "preparing_data" in phases
        assert "configuring" in phases
        assert "training" in phases
        assert "evaluating" in phases
        assert "exporting" in phases
        assert "complete" in phases

    @pytest.mark.asyncio
    async def test_compute_metrics_perplexity(self) -> None:
        m = TrainingMetrics()
        m.final_loss = 1.5
        workflow = FineTuneWorkflow()
        workflow._compute_metrics(m)
        assert m.perplexity == pytest.approx(math.exp(1.5), rel=0.01)
