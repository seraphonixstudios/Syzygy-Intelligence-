"""Chat API routes — natural language interface to Syzygy."""

from __future__ import annotations

from fastapi import APIRouter

from app.consensus.engine import ConsensusEngine
from app.agents.registry import agent_registry
from app.llm.ollama_client import OllamaClient

router = APIRouter()
llm = OllamaClient()
engine = ConsensusEngine()


@router.post("/completions")
async def chat_completion(data: dict):
    message = data.get("message", "")
    model = data.get("model", "")

    # Run consensus if requested
    if data.get("use_consensus", False):
        session = await engine.run_consensus(
            task=message,
            max_rounds=data.get("consensus_rounds", 4),
        )
        return {
            "response": session.final_synthesis,
            "session_id": session.id,
            "rounds": session.current_round,
            "fusion_report": session.polarity_fusion_report,
        }

    # Direct LLM response
    response = await llm.chat(
        messages=[{"role": "user", "content": message}],
        model=model or "",
    )
    return {"response": response}


@router.post("/stream")
async def chat_stream(data: dict):
    return {"type": "stream", "status": "streaming_started"}
