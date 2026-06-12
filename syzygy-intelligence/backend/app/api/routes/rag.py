"""RAG API routes — document ingestion and semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.logging_setup import logger
from app.rag import retriever

router = APIRouter()

UPLOAD_DIR = Path(settings.data_dir) / "rag_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


# ── Request / Response models ──────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class DeleteRequest(BaseModel):
    source: str


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/ingest")
async def ingest(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    source: str = Form(""),
) -> dict[str, Any]:
    """Ingest a document via file upload or raw text (multipart/form-data)."""
    if file is not None:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        dest = UPLOAD_DIR / (file.filename or f"upload{ext}")
        content = await file.read()
        dest.write_bytes(content)
        count = await retriever.ingest_document(
            str(dest),
            metadata={"source": file.filename or str(dest)},
        )
        return {"source": file.filename or str(dest), "chunks": count, "status": "ingested"}

    if text:
        count = await retriever.ingest_text(text, source=source or "text_input")
        return {"source": source or "text_input", "chunks": count, "status": "ingested"}

    raise HTTPException(status_code=400, detail="Provide either a file or raw text")


@router.post("/ingest/batch")
async def ingest_batch(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    """Ingest multiple documents in a single request (multipart/form-data)."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append({"file": f.filename, "error": f"Unsupported type: {ext}"})
            continue

        dest = UPLOAD_DIR / (f.filename or f"upload{ext}")
        try:
            content = await f.read()
            dest.write_bytes(content)
            count = await retriever.ingest_document(
                str(dest),
                metadata={"source": f.filename or str(dest)},
            )
            results.append({"file": f.filename, "chunks": count, "status": "ingested"})
        except Exception as exc:
            errors.append({"file": f.filename, "error": str(exc)})

    logger.info("Batch ingest completed", total=len(files), ok=len(results), err=len(errors))
    return {"results": results, "errors": errors, "total": len(files)}


@router.post("/query")
async def search(payload: QueryRequest) -> dict[str, Any]:
    """Semantic search over ingested documents."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = await retriever.query(payload.query, top_k=payload.top_k)
    return {"query": payload.query, "results": results, "count": len(results)}


@router.get("/documents")
async def list_docs() -> dict[str, Any]:
    """List all ingested documents with chunk counts."""
    docs = await retriever.list_documents()
    return {"documents": docs, "count": len(docs)}


@router.delete("/documents")
async def delete_doc(payload: DeleteRequest) -> dict[str, Any]:
    """Delete a document and all its chunks by source identifier."""
    if not payload.source.strip():
        raise HTTPException(status_code=400, detail="Source is required")
    deleted = await retriever.delete_document(payload.source)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{payload.source}' not found",
        )
    return {"source": payload.source, "status": "deleted"}
