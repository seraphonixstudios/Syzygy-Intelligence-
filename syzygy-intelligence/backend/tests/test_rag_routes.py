"""Tests for RAG API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestIngest:
    @pytest.mark.asyncio
    async def test_ingests_text(self):
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.ingest_text = AsyncMock(return_value=3)
            from app.api.routes.rag import ingest

            result = await ingest(file=None, text="Hello world", source="manual")
            assert result["chunks"] == 3
            assert result["status"] == "ingested"
            m_ret.ingest_text.assert_awaited_with("Hello world", source="manual")

    @pytest.mark.asyncio
    async def test_ingests_text_with_default_source(self):
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.ingest_text = AsyncMock(return_value=1)
            from app.api.routes.rag import ingest

            result = await ingest(file=None, text="data", source="")
            assert result["source"] == "text_input"

    @pytest.mark.asyncio
    async def test_ingests_file(self):
        mock_file = MagicMock()
        mock_file.filename = "doc.txt"
        mock_file.read = AsyncMock(return_value=b"file content")

        with (
            patch("app.api.routes.rag.retriever") as m_ret,
            patch("app.api.routes.rag.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.rag.Path.write_bytes"),
        ):
            m_ret.ingest_document = AsyncMock(return_value=5)
            from app.api.routes.rag import ingest

            result = await ingest(file=mock_file, text=None, source="")
            assert result["chunks"] == 5
            assert result["status"] == "ingested"
            m_ret.ingest_document.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_unsupported_extension(self):
        mock_file = MagicMock()
        mock_file.filename = "doc.exe"
        mock_file.read = AsyncMock(return_value=b"data")

        from app.api.routes.rag import ingest

        with pytest.raises(HTTPException) as exc:
            await ingest(file=mock_file, text=None, source="")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_no_input(self):
        from app.api.routes.rag import ingest

        with pytest.raises(HTTPException) as exc:
            await ingest(file=None, text=None, source="")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_none_filename(self):
        mock_file = MagicMock()
        mock_file.filename = None
        mock_file.read = AsyncMock(return_value=b"data")

        from app.api.routes.rag import ingest

        with pytest.raises(HTTPException) as exc:
            await ingest(file=mock_file, text=None, source="")
        assert exc.value.status_code == 400


class TestIngestBatch:
    @pytest.mark.asyncio
    async def test_ingests_multiple_files(self):
        f1 = MagicMock()
        f1.filename = "a.txt"
        f1.read = AsyncMock(return_value=b"content a")
        f2 = MagicMock()
        f2.filename = "b.md"
        f2.read = AsyncMock(return_value=b"content b")

        with (
            patch("app.api.routes.rag.retriever") as m_ret,
            patch("app.api.routes.rag.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.rag.Path.write_bytes"),
        ):
            m_ret.ingest_document = AsyncMock(side_effect=[3, 7])
            from app.api.routes.rag import ingest_batch

            result = await ingest_batch(files=[f1, f2])
            assert len(result["results"]) == 2
            assert result["results"][0]["file"] == "a.txt"
            assert result["results"][0]["chunks"] == 3
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_skips_unsupported_types(self):
        f1 = MagicMock()
        f1.filename = "good.txt"
        f1.read = AsyncMock(return_value=b"data")
        f2 = MagicMock()
        f2.filename = "bad.zip"
        f2.read = AsyncMock(return_value=b"data")

        with (
            patch("app.api.routes.rag.retriever") as m_ret,
            patch("app.api.routes.rag.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.rag.Path.write_bytes"),
        ):
            m_ret.ingest_document = AsyncMock(return_value=1)
            from app.api.routes.rag import ingest_batch

            result = await ingest_batch(files=[f1, f2])
            assert len(result["results"]) == 1
            assert len(result["errors"]) == 1
            assert "Unsupported" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_handles_file_error(self):
        f1 = MagicMock()
        f1.filename = "bad.txt"
        f1.read = AsyncMock(side_effect=RuntimeError("read failed"))

        with (
            patch("app.api.routes.rag.retriever") as m_ret,
            patch("app.api.routes.rag.UPLOAD_DIR", MagicMock()),
        ):
            from app.api.routes.rag import ingest_batch

            result = await ingest_batch(files=[f1])
            assert len(result["errors"]) == 1
            assert "read failed" in result["errors"][0]["error"]


class TestSearch:
    @pytest.mark.asyncio
    async def test_returns_results(self):
        mock_results = [
            {"chunk_id": "c1", "text": "Result 1", "score": 0.9},
            {"chunk_id": "c2", "text": "Result 2", "score": 0.8},
        ]
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.query = AsyncMock(return_value=mock_results)
            from app.api.routes.rag import QueryRequest, search

            result = await search(QueryRequest(query="test query", top_k=3))
            assert result["query"] == "test query"
            assert len(result["results"]) == 2
            assert result["count"] == 2
            m_ret.query.assert_awaited_with("test query", top_k=3)

    @pytest.mark.asyncio
    async def test_rejects_empty_query(self):
        from app.api.routes.rag import QueryRequest, search

        with pytest.raises(HTTPException) as exc:
            await search(QueryRequest(query="  ", top_k=5))
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_empty_results(self):
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.query = AsyncMock(return_value=[])
            from app.api.routes.rag import QueryRequest, search

            result = await search(QueryRequest(query="nothing", top_k=5))
            assert result["count"] == 0


class TestListDocuments:
    @pytest.mark.asyncio
    async def test_returns_documents(self):
        mock_docs = [
            {"source": "doc1.txt", "chunks": 5},
            {"source": "doc2.md", "chunks": 3},
        ]
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.list_documents = AsyncMock(return_value=mock_docs)
            from app.api.routes.rag import list_docs

            result = await list_docs()
            assert len(result["documents"]) == 2
            assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_returns_empty(self):
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.list_documents = AsyncMock(return_value=[])
            from app.api.routes.rag import list_docs

            result = await list_docs()
            assert result["documents"] == []
            assert result["count"] == 0


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_deletes_document(self):
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.delete_document = AsyncMock(return_value=True)
            from app.api.routes.rag import DeleteRequest, delete_doc

            result = await delete_doc(DeleteRequest(source="doc.txt"))
            assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self):
        with patch("app.api.routes.rag.retriever") as m_ret:
            m_ret.delete_document = AsyncMock(return_value=False)
            from app.api.routes.rag import DeleteRequest, delete_doc

            with pytest.raises(HTTPException) as exc:
                await delete_doc(DeleteRequest(source="nonexistent.txt"))
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_rejects_empty_source(self):
        from app.api.routes.rag import DeleteRequest, delete_doc

        with pytest.raises(HTTPException) as exc:
            await delete_doc(DeleteRequest(source=""))
        assert exc.value.status_code == 400
