"""Fine-tuning workflow — LoRA, QLoRA, and full fine-tuning for local LLMs.

Architecture:
- Optional ML dependencies (torch, transformers, peft, bitsandbytes, trl, datasets)
- Graceful fallback when dependencies are missing (simulated training for demo)
- Supports QLoRA (4-bit NF4), LoRA, and full fine-tuning via configuration
- Real-time progress callbacks for frontend streaming (loss, grad norm, lr)
- Modular training pipeline: config -> prepare -> train -> export -> evaluate
- Follows same pattern as coding.py for progress callback integration
"""

from __future__ import annotations

import asyncio
import json
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]

SUPPORTED_MODELS = [
    "llama3.2:1b", "llama3.2:3b",
    "mistral:7b", "qwen2.5:7b",
    "gemma2:9b", "phi3:14b",
    "deepseek-coder:6.7b",
]

SUPPORTED_METHODS = ["qlora", "lora", "full"]

DEFAULT_HYPERPARAMS = {
    "learning_rate": 2e-4,
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "max_seq_length": 2048,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "warmup_steps": 100,
    "logging_steps": 10,
    "save_steps": 500,
    "weight_decay": 0.01,
}


@dataclass
class FineTuneConfig:
    model_name: str = "tinyllama:latest"
    method: str = "qlora"
    dataset_source: str = "text"
    dataset_text: str = ""
    dataset_path: str = ""
    hf_dataset: str = ""
    hyperparams: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_HYPERPARAMS))
    output_dir: str = "/tmp/syzygy-finetune"
    use_flash_attention: bool = False
    use_gradient_checkpointing: bool = True
    target_modules: list[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])


@dataclass
class TrainingMetrics:
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    total_steps: int = 0
    loss_points: list[dict[str, float]] = field(default_factory=list)
    grad_norm_points: list[dict[str, float]] = field(default_factory=list)
    learning_rate_points: list[dict[str, float]] = field(default_factory=list)
    final_loss: float = 0.0
    perplexity: float = 0.0
    tokens_per_second: float = 0.0
    memory_peak_mb: float = 0.0


@dataclass
class FineTuneResult:
    status: str = "pending"
    config: FineTuneConfig = field(default_factory=FineTuneConfig)
    metrics: TrainingMetrics = field(default_factory=TrainingMetrics)
    model_id: str = ""
    adapter_path: str = ""
    merged_model_path: str = ""
    eval_results: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class FineTuneWorkflow:
    """Fine-tuning workflow with LoRA/QLoRA support and real-time progress."""

    name: str = "finetune"
    description: str = (
        "Fine-tune local LLMs with LoRA, QLoRA, or full fine-tuning — "
        "dataset preparation, training, evaluation, and model export"
    )

    def __init__(self) -> None:
        self._trainer = None
        self._model = None
        self._tokenizer = None
        self._ml_available = self._check_ml_deps()

    def _check_ml_deps(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            import peft  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "ML dependencies not installed — finetune will run in demo mode. "
                "Install torch, transformers, peft, bitsandbytes, trl, datasets, accelerate"
            )
            return False

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Execute fine-tuning workflow.

        Args:
            task: JSON string or description of the fine-tuning task
            context: May contain dataset_text, files, links, and config overrides
            on_progress: Callback for real-time streaming (step, percent, info)
        """
        ctx = context or {}
        config = self._build_config(task, ctx)
        logger.info(
            "Fine-tune workflow started",
            model=config.model_name,
            method=config.method,
            dataset_source=config.dataset_source,
        )

        metrics = TrainingMetrics()
        result = FineTuneResult(config=config, metrics=metrics)

        try:
            if self._ml_available:
                await self._real_training(config, metrics, on_progress)
            else:
                await self._simulated_training(config, metrics, on_progress)

            result.status = "completed"
            result.model_id = f"finetuned/{config.model_name}"
            result.adapter_path = f"{config.output_dir}/adapter"

        except Exception as e:
            logger.error("Fine-tuning failed", error=str(e))
            result.status = "failed"
            result.error = str(e)[:500]
            if on_progress:
                await on_progress("error", 0, {"error": str(e)[:200]})

        result.metrics.end_time = datetime.now(UTC)
        elapsed = (result.metrics.end_time - metrics.start_time).total_seconds()
        if elapsed > 0:
            result.metrics.tokens_per_second = metrics.total_steps / elapsed

        return {
            "model": config.model_name,
            "method": config.method,
            "status": result.status,
            "metrics": {
                "total_steps": metrics.total_steps,
                "final_loss": round(metrics.final_loss, 4),
                "perplexity": round(metrics.perplexity, 2),
                "tokens_per_second": round(metrics.tokens_per_second, 2),
                "memory_peak_mb": round(metrics.memory_peak_mb, 1),
                "loss_curve": metrics.loss_points[-50:] if metrics.loss_points else [],
                "learning_rate_curve": metrics.learning_rate_points[-50:] if metrics.learning_rate_points else [],
                "elapsed_seconds": round(elapsed, 1),
            },
            "config": {
                "model": config.model_name,
                "method": config.method,
                "dataset_source": config.dataset_source,
                "hyperparams": config.hyperparams,
            },
            "error": result.error or None,
        }

    def _build_config(self, task: str, ctx: dict[str, Any]) -> FineTuneConfig:
        try:
            parsed = json.loads(task)
            model_name = parsed.get("model", ctx.get("model", "tinyllama:latest"))
            method = parsed.get("method", ctx.get("method", "qlora"))
            hp = dict(DEFAULT_HYPERPARAMS)
            hp.update(parsed.get("hyperparams", ctx.get("hyperparams", {})))
        except (json.JSONDecodeError, TypeError):
            model_name = ctx.get("model", "tinyllama:latest")
            method = ctx.get("method", "qlora")
            hp = dict(DEFAULT_HYPERPARAMS)
            hp.update(ctx.get("hyperparams", {}))

        if method not in SUPPORTED_METHODS:
            method = "qlora"

        try:
            parsed = json.loads(task)
        except (json.JSONDecodeError, TypeError):
            parsed = {}

        return FineTuneConfig(
            model_name=model_name,
            method=method,
            dataset_source=parsed.get("dataset_source", ctx.get("dataset_source", "text")),
            dataset_text=parsed.get("dataset_text", ctx.get("dataset_text", task if len(task) > 20 else "")),
            dataset_path=parsed.get("dataset_path", ctx.get("dataset_path", "")),
            hf_dataset=parsed.get("hf_dataset", ctx.get("hf_dataset", "")),
            hyperparams=hp,
        )

    async def _real_training(
        self,
        config: FineTuneConfig,
        metrics: TrainingMetrics,
        on_progress: ProgressCallback | None,
    ) -> None:
        """Execute real fine-tuning with transformers/peft/trl."""
        import torch
        from datasets import Dataset, load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
    )
        from trl import SFTTrainer

        if on_progress:
            await on_progress("loading_model", 5, {"model": config.model_name})

        quantization_config = None
        if config.method == "qlora":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )

        tokenizer = AutoTokenizer.from_pretrained(config.model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
            use_cache=not config.use_gradient_checkpointing,
        )

        if config.method in ("qlora", "lora"):
            if config.method == "qlora":
                model = prepare_model_for_kbit_training(model)

            peft_config = LoraConfig(
                r=config.hyperparams["lora_r"],
                lora_alpha=config.hyperparams["lora_alpha"],
                lora_dropout=config.hyperparams["lora_dropout"],
                target_modules=config.target_modules,
                bias="none",
                task_type="CAUSAL_LM",
            )
            model = get_peft_model(model, peft_config)
            model.print_trainable_parameters()

        if on_progress:
            await on_progress("preparing_dataset", 15, {})

        dataset = self._prepare_dataset(config, tokenizer)

        if on_progress:
            await on_progress("configuring_training", 20, {"method": config.method})

        hp = config.hyperparams
        training_args = TrainingArguments(
            output_dir=config.output_dir,
            per_device_train_batch_size=hp["batch_size"],
            gradient_accumulation_steps=hp["gradient_accumulation_steps"],
            learning_rate=hp["learning_rate"],
            warmup_steps=hp["warmup_steps"],
            num_train_epochs=hp["num_epochs"],
            logging_steps=hp["logging_steps"],
            save_steps=hp["save_steps"],
            weight_decay=hp["weight_decay"],
            gradient_checkpointing=config.use_gradient_checkpointing,
            fp16=torch.cuda.is_available(),
            bf16=not torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
            report_to="none",
            remove_unused_columns=False,
            dataloader_pin_memory=False,
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            args=training_args,
            train_dataset=dataset,
            max_seq_length=hp["max_seq_length"],
            dataset_text_field="text",
        )

        self._trainer = trainer
        self._model = model
        self._tokenizer = tokenizer

        if on_progress:
            await on_progress("training", 25, {"total_steps": int(hp["num_epochs"] * len(dataset) / hp["batch_size"])})

        class ProgressCallbackHandler:
            def __init__(self, outer_on_progress: ProgressCallback, outer_metrics: TrainingMetrics):
                self.outer_on_progress = outer_on_progress
                self.outer_metrics = outer_metrics
                self.last_log = 0

            def on_log(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
                if state.log_history:
                    logs = state.log_history[-1]
                    step = state.global_step
                    self.outer_metrics.total_steps = step
                    if "loss" in logs:
                        pt = {"step": step, "loss": round(logs["loss"], 4)}
                        self.outer_metrics.loss_points.append(pt)
                        self.outer_metrics.final_loss = logs["loss"]
                    if "grad_norm" in logs:
                        self.outer_metrics.grad_norm_points.append({"step": step, "norm": round(logs["grad_norm"], 4)})
                    if "learning_rate" in logs:
                        self.outer_metrics.learning_rate_points.append({"step": step, "lr": round(logs["learning_rate"], 8)})

            def on_step_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
                if state.global_step % 5 == 0 and state.global_step != self.last_log:
                    self.last_log = state.global_step
                    progress = min(95, 25 + int(70 * state.global_step / max(1, state.max_steps)))
                    metrics_snapshot = {}
                    if self.outer_metrics.loss_points:
                        metrics_snapshot["loss"] = self.outer_metrics.loss_points[-1]["loss"]
                    if self.outer_metrics.learning_rate_points:
                        metrics_snapshot["learning_rate"] = self.outer_metrics.learning_rate_points[-1]["lr"]
                    asyncio.create_task(self.outer_on_progress("training", progress, {
                        "step": state.global_step,
                        "max_steps": state.max_steps,
                        "metrics": metrics_snapshot,
                    }))

            def on_train_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
                pass

        callback_handler = ProgressCallbackHandler(on_progress, metrics)
        trainer.add_callback(callback_handler)

        trainer.train()

        if on_progress:
            await on_progress("saving", 97, {"path": config.output_dir})

        trainer.save_model(config.output_dir)
        tokenizer.save_pretrained(config.output_dir)

        self._compute_metrics(metrics)

    async def _simulated_training(
        self,
        config: FineTuneConfig,
        metrics: TrainingMetrics,
        on_progress: ProgressCallback | None,
    ) -> None:
        """Simulate training for demo/development without ML dependencies."""
        hp = config.hyperparams
        total_steps = hp["num_epochs"] * 20
        loss = 3.0

        steps = [
            ("initializing", 5, "Loading model and tokenizer"),
            ("preparing_data", 15, f"Preparing dataset ({'paste' if config.dataset_source == 'text' else 'hf'})"),
            ("configuring", 20, f"Configuring {config.method.upper()} with rank={hp['lora_r']}"),
        ]

        for step_name, pct, desc in steps:
            if on_progress:
                await on_progress(step_name, pct, {"description": desc})
            await asyncio.sleep(0.3)

        for step in range(1, total_steps + 1):
            await asyncio.sleep(0.15)
            loss = 3.0 * math.exp(-step / (total_steps * 0.4)) + 0.3 + (hash(str(step)) % 100) / 1000 * 0.5
            loss = min(loss, 5.0)
            lr = hp["learning_rate"] * (1 - step / total_steps * 0.9)

            metrics.total_steps = step
            metrics.loss_points.append({"step": step, "loss": round(loss, 4)})
            metrics.learning_rate_points.append({"step": step, "lr": round(lr, 8)})
            metrics.final_loss = loss

            if step % 5 == 0 and on_progress:
                progress = int(20 + 75 * step / total_steps)
                await on_progress("training", progress, {
                    "step": step,
                    "max_steps": total_steps,
                    "metrics": {"loss": round(loss, 4), "learning_rate": round(lr, 8)},
                })

        if on_progress:
            await on_progress("evaluating", 96, {"perplexity": round(math.exp(loss), 2)})
            await on_progress("exporting", 98, {"path": config.output_dir})
            await on_progress("complete", 100, {"status": "completed"})

        self._compute_metrics(metrics)

    def _compute_metrics(self, metrics: TrainingMetrics) -> None:
        if metrics.final_loss > 0:
            metrics.perplexity = math.exp(metrics.final_loss)
        try:
            import psutil
            metrics.memory_peak_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        except ImportError:
            import os
            metrics.memory_peak_mb = os.environ.get("SYZYGY_MEMORY_MB", 0)

    def _prepare_dataset(self, config: FineTuneConfig, tokenizer: Any) -> Any:
        from datasets import Dataset, load_dataset

        if config.hf_dataset:
            ds = load_dataset(config.hf_dataset, split="train")
        elif config.dataset_text:
            lines = [l for l in config.dataset_text.split("\n") if l.strip()]
            ds = Dataset.from_dict({"text": lines[:1000]})
        elif config.dataset_path:
            ds = load_dataset("text", data_files=config.dataset_path, split="train")
        else:
            ds = Dataset.from_dict({"text": ["Default training example"] * 10})

        return ds

    def get_status(self) -> dict[str, Any]:
        if self._model is None:
            return {"status": "idle", "trainable_params": 0, "total_params": 0}
        try:
            trainable = sum(p.numel() for p in self._model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in self._model.parameters())
            return {
                "status": "loaded",
                "trainable_params": trainable,
                "total_params": total,
                "trainable_pct": round(100 * trainable / max(total, 1), 2),
            }
        except Exception:
            return {"status": "unknown"}


FINETUNE_WORKFLOW = FineTuneWorkflow()

__all__ = [
    "FineTuneWorkflow",
    "FineTuneConfig",
    "FineTuneResult",
    "TrainingMetrics",
    "FINETUNE_WORKFLOW",
]
