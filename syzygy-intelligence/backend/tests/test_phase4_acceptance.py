"""Phase 4 acceptance — every workflow must prove its outputs depend on its inputs.

LLM-backed workflows run against an echo mock (outputs embed the prompt, so any
task text that reaches the model shows up in the result). Rule-based workflows
run for real (deterministic keyword routing must branch on the input).

Excluded: image_gen (needs an external image service), self_improvement
(different execute signature, covered elsewhere), coding/content/research/
test_gen (covered by dedicated tripwire suites).
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workflows import WORKFLOW_REGISTRY

TASK_A = "lunar greenhouse calibration procedures"
TASK_B = "harbor invoice reconciliation audit"

# Workflows needing task pairs that hit different deterministic branches.
BRANCH_TASKS = {
    "support": ("my bill is wrong, urgent outage, money lost", "help how do I change my account settings"),
}

# Registry names excluded from the generic loop (see module docstring).
EXCLUDED = {"image_gen", "self_improvement", "coding", "content", "research", "test_gen"}

EXECUTE_TIMEOUT = 120.0


def _echo_llm():
    llm = AsyncMock()
    llm.get_model_for_role = MagicMock(return_value="mock-model")

    async def _gen(prompt, **kwargs):
        return f"ECHO::{prompt[:200]}"

    llm.generate.side_effect = _gen
    return llm


def _fresh(name):
    wf = WORKFLOW_REGISTRY[name]
    try:
        fresh = type(wf)()
    except Exception:
        fresh = wf
    if hasattr(fresh, "llm"):
        fresh.llm = _echo_llm()
    return fresh


def _blob(result):
    return json.dumps(result, sort_keys=True, default=str)


def _tasks_for(name):
    if name == "finetune":
        return (
            '{"model": "tinyllama-alpha", "method": "qlora", "hyperparams": {"num_epochs": 1}}',
            '{"model": "tinyllama-beta", "method": "qlora", "hyperparams": {"num_epochs": 1}}',
        )
    if name == "translate":
        return TASK_A, TASK_B
    return BRANCH_TASKS.get(name, (TASK_A, TASK_B))


@pytest.mark.parametrize("name", sorted(set(WORKFLOW_REGISTRY) - EXCLUDED))
@pytest.mark.asyncio
async def test_workflow_outputs_depend_on_inputs(name):
    wf = _fresh(name)
    if name == "finetune" and getattr(wf, "_ml_available", False):
        pytest.skip("requires no-ML demo mode")
    task_a, task_b = _tasks_for(name)
    kwargs = {"context": {"target_language": "French"}} if name == "translate" else {}
    first = await asyncio.wait_for(wf.execute(task_a, **kwargs), timeout=EXECUTE_TIMEOUT)
    wf2 = _fresh(name)
    second = await asyncio.wait_for(wf2.execute(task_b, **kwargs), timeout=EXECUTE_TIMEOUT)
    assert _blob(first) != _blob(second), f"{name} returned identical output for different tasks"


@pytest.mark.asyncio
async def test_rule_based_results_echo_their_input():
    """Reports must be traceable to the analyzed input (no two inputs, same report)."""
    from app.workflows.legal import LegalWorkflow
    from app.workflows.sales import SalesWorkflow

    legal = await LegalWorkflow().execute("lunar greenhouse calibration procedures")
    assert legal["contract_text"] == "lunar greenhouse calibration procedures"
    assert legal["contract_length"] == len("lunar greenhouse calibration procedures")
    sales = await SalesWorkflow().execute("harbor invoice reconciliation audit")
    assert sales["lead_info"] == "harbor invoice reconciliation audit"
    assert sales["lead_length"] == len("harbor invoice reconciliation audit")


@pytest.mark.asyncio
async def test_finetune_demo_mode_is_labeled():
    wf = _fresh("finetune")
    if getattr(wf, "_ml_available", False):
        pytest.skip("requires no-ML demo mode")
    result = await asyncio.wait_for(
        wf.execute('{"model": "tinyllama-x", "hyperparams": {"num_epochs": 1}}'),
        timeout=EXECUTE_TIMEOUT,
    )
    assert result["status"] == "completed"
    assert result["simulated"] is True
    assert result["model"] == "tinyllama-x"
