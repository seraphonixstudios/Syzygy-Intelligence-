"""Lightweight Ollama API mock for CI — responds with plausible JSON to keep tests happy."""

from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.post("/api/generate")
async def generate():
    return {"response": "mock output", "done": True}


@app.post("/api/embed")
async def embed():
    return {"embeddings": [[0.1] * 384]}


@app.get("/api/tags")
async def tags():
    return {"models": [{"name": "qwen3:8b-gpu"}]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=11434)
