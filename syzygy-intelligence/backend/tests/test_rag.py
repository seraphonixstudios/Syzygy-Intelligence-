
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.embeddings import embed
from app.rag.ingester import chunk_text, parse_document

SAMPLE_TEXT = (
    "Syzygy Intelligence is an AI orchestration platform. "
    "It uses multiple agents. "
    "The consensus engine produces well-reasoned answers."
)


class TestIngester:
    def test_parse_plain_text(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text(SAMPLE_TEXT)
        content = parse_document(str(f))
        assert SAMPLE_TEXT in content

    def test_parse_markdown(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Title\n\nParagraph text.")
        content = parse_document(str(f))
        assert "Paragraph text." in content

    def test_parse_pdf_not_found(self, tmp_path):
        with pytest.raises((FileNotFoundError, RuntimeError)):
            parse_document(str(tmp_path / "nonexistent.pdf"))

    def test_parse_unsupported_extension(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("data")
        with pytest.raises(ValueError, match="(?i)unsupported"):
            parse_document(str(f))


class TestChunking:
    def test_chunk_text_basic(self):
        chunks = chunk_text(SAMPLE_TEXT, chunk_size=50, overlap=10)
        assert len(chunks) >= 2
        assert all(len(c) <= 55 for c in chunks)

    def test_chunk_text_single(self):
        chunks = chunk_text("Hello.", chunk_size=500, overlap=10)
        assert len(chunks) == 1

    def test_chunk_text_empty(self):
        chunks = chunk_text("", chunk_size=100, overlap=10)
        assert chunks == []

    def test_chunk_text_overlap_sequence(self):
        chunks = chunk_text("word " * 50, chunk_size=30, overlap=10)
        assert len(chunks) >= 2


class TestEmbed:
    @pytest.mark.asyncio
    async def test_embed_basic(self):
        from app.errors import LLMConnectionError
        try:
            result = await embed([SAMPLE_TEXT])
            assert isinstance(result, list)
            assert len(result) > 0
        except LLMConnectionError:
            pytest.skip("Ollama server does not support embeddings")

    @pytest.mark.asyncio
    async def test_embed_raises_on_unsupported_server(self):
        import app.config
        from app.errors import LLMConnectionError

        original = app.config.settings.ollama_base_url
        app.config.settings.ollama_base_url = "http://nonexistent.invalid:9999"
        try:
            with pytest.raises((LLMConnectionError, Exception)):
                await embed(["test"])
        finally:
            app.config.settings.ollama_base_url = original


class TestRetriever:
    @pytest.mark.asyncio
    async def test_import_retriever(self):
        from app.rag.retriever import delete_document, ingest_document, list_documents, query
        assert callable(ingest_document)
        assert callable(query)
        assert callable(list_documents)
        assert callable(delete_document)


# ===================================================================
# RAG retriever — full logic tests with mocked ChromaDB
# ===================================================================


@pytest.fixture
def mock_chroma():
    """Mock ChromaDB PersistentClient and collection for retriever tests."""
    with patch("chromadb.PersistentClient") as mock_client_cls:
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_cls.return_value = mock_client
        yield mock_collection


class TestRetrieverIngest:
    """Tests for retriever.ingest_document and retriever.ingest_text."""

    @pytest.mark.asyncio
    async def test_ingest_text_basic(self, mock_chroma):
        from app.rag.retriever import ingest_text

        mock_chroma.add = MagicMock()
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3]]
            with patch("app.rag.retriever.chunk_text", return_value=["chunk content"]):
                result = await ingest_text("test text", source="test_source")
                assert result == 1
                mock_chroma.add.assert_called_once()
                args, kwargs = mock_chroma.add.call_args
                assert kwargs["documents"] == ["chunk content"]
                assert kwargs["ids"][0] is not None

    @pytest.mark.asyncio
    async def test_ingest_text_empty_chunks(self, mock_chroma):
        from app.rag.retriever import ingest_text

        with patch("app.rag.retriever.chunk_text", return_value=[]):
            result = await ingest_text("", source="test")
            assert result == 0
            mock_chroma.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingest_text_with_metadata(self, mock_chroma):
        from app.rag.retriever import ingest_text

        mock_chroma.add = MagicMock()
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1]]
            with patch("app.rag.retriever.chunk_text", return_value=["c1", "c2"]):
                result = await ingest_text("text", source="src", metadata={"author": "test"})
                assert result == 2
                _, kwargs = mock_chroma.add.call_args
                assert kwargs["metadatas"][0]["source"] == "src"
                assert kwargs["metadatas"][0]["author"] == "test"
                assert kwargs["metadatas"][1]["source"] == "src"

    @pytest.mark.asyncio
    async def test_ingest_text_no_metadata(self, mock_chroma):
        from app.rag.retriever import ingest_text

        mock_chroma.add = MagicMock()
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1]]
            with patch("app.rag.retriever.chunk_text", return_value=["c1"]):
                result = await ingest_text("text", source="src", metadata=None)
                assert result == 1
                _, kwargs = mock_chroma.add.call_args
                assert kwargs["metadatas"][0]["source"] == "src"
                assert "author" not in kwargs["metadatas"][0]

    @pytest.mark.asyncio
    async def test_ingest_document_basic(self, mock_chroma, tmp_path):
        from app.rag.retriever import ingest_document

        mock_chroma.add = MagicMock()
        f = tmp_path / "test.txt"
        f.write_text("document content")
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1]]
            with patch("app.rag.retriever.chunk_text", return_value=["chunk"]):
                result = await ingest_document(str(f))
                assert result == 1

    @pytest.mark.asyncio
    async def test_ingest_document_with_metadata(self, mock_chroma, tmp_path):
        from app.rag.retriever import ingest_document

        mock_chroma.add = MagicMock()
        f = tmp_path / "doc.txt"
        f.write_text("content")
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1]]
            with patch("app.rag.retriever.chunk_text", return_value=["chunk"]):
                result = await ingest_document(str(f), metadata={"source": "custom"})
                assert result == 1
                _, kwargs = mock_chroma.add.call_args
                assert kwargs["metadatas"][0]["source"] == "custom"

    @pytest.mark.asyncio
    async def test_ingest_document_unsupported_ext(self, mock_chroma):
        from app.rag.retriever import ingest_document

        with pytest.raises(ValueError, match="(?i)unsupported"):
            await ingest_document("test.xyz")


class TestRetrieverQuery:
    """Tests for retriever.query."""

    @pytest.mark.asyncio
    async def test_query_returns_results(self, mock_chroma):
        from app.rag.retriever import query

        mock_chroma.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.25]],
            "documents": [["doc content", "another doc"]],
            "metadatas": [[{"source": "a"}, {"source": "b"}]],
        }
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5, 0.3, 0.1]]
            results = await query("test", top_k=5, min_score=0.0)
            assert len(results) == 2
            assert results[0]["score"] > results[1]["score"]
            assert results[0]["id"] == "id1"
            assert results[0]["content"] == "doc content"
            assert results[0]["metadata"]["source"] == "a"

    @pytest.mark.asyncio
    async def test_query_min_score_filters(self, mock_chroma):
        from app.rag.retriever import query

        mock_chroma.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.8]],
            "documents": [["relevant", "irrelevant"]],
            "metadatas": [[{}, {}]],
        }
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5]]
            results = await query("test", top_k=5, min_score=0.5)
            assert len(results) == 1
            assert results[0]["id"] == "id1"
            # id2 had score 0.2 (1.0 - 0.8), filtered out

    @pytest.mark.asyncio
    async def test_query_empty_results(self, mock_chroma):
        from app.rag.retriever import query

        mock_chroma.query.return_value = {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5]]
            results = await query("test")
            assert results == []

    @pytest.mark.asyncio
    async def test_query_none_results(self, mock_chroma):
        from app.rag.retriever import query

        mock_chroma.query.return_value = None
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5]]
            results = await query("test")
            assert results == []

    @pytest.mark.asyncio
    async def test_query_missing_keys(self, mock_chroma):
        from app.rag.retriever import query

        mock_chroma.query.return_value = {
            "ids": [["id1"]],
        }
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5]]
            results = await query("test", top_k=5, min_score=0.0)
            assert len(results) == 1
            assert results[0]["content"] == ""
            assert results[0]["metadata"] == {}
            # distance defaults to 0.0, so score = 1.0

    @pytest.mark.asyncio
    async def test_query_caps_top_k_at_50(self, mock_chroma):
        from app.rag.retriever import query

        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5]]
            await query("test", top_k=100)
            # n_results should be min(100, 50) = 50
            mock_chroma.query.assert_called_once()
            _, kwargs = mock_chroma.query.call_args
            assert kwargs["n_results"] == 50

    @pytest.mark.asyncio
    async def test_query_top_k_truncation(self, mock_chroma):
        from app.rag.retriever import query

        mock_chroma.query.return_value = {
            "ids": [["id1", "id2", "id3"]],
            "distances": [[0.1, 0.2, 0.3]],
            "documents": [["a", "b", "c"]],
            "metadatas": [[{}, {}, {}]],
        }
        with patch("app.rag.retriever.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.5]]
            results = await query("test", top_k=2, min_score=0.0)
            assert len(results) == 2


class TestRetrieverListDocuments:
    """Tests for retriever.list_documents."""

    @pytest.mark.asyncio
    async def test_list_documents_basic(self, mock_chroma):
        from app.rag.retriever import list_documents

        mock_chroma.get.return_value = {
            "metadatas": [
                {"source": "doc1", "char_count": 100, "ingested_at": "2024-01-01T00:00:00"},
                {"source": "doc1", "char_count": 200, "ingested_at": "2024-01-02T00:00:00"},
                {"source": "doc2", "char_count": 150, "ingested_at": "2024-01-03T00:00:00"},
            ],
        }
        docs = await list_documents()
        assert len(docs) == 2
        doc1 = [d for d in docs if d["source"] == "doc1"][0]
        assert doc1["chunk_count"] == 2
        assert doc1["total_chars"] == 300
        assert doc1["ingested_at"] == "2024-01-01T00:00:00"  # earliest

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, mock_chroma):
        from app.rag.retriever import list_documents

        mock_chroma.get.return_value = {}
        docs = await list_documents()
        assert docs == []

    @pytest.mark.asyncio
    async def test_list_documents_no_metadatas(self, mock_chroma):
        from app.rag.retriever import list_documents

        mock_chroma.get.return_value = {"metadatas": None}
        docs = await list_documents()
        assert docs == []

    @pytest.mark.asyncio
    async def test_list_documents_missing_fields(self, mock_chroma):
        from app.rag.retriever import list_documents

        mock_chroma.get.return_value = {
            "metadatas": [
                {"source": "doc1"},  # no char_count, no ingested_at
            ],
        }
        docs = await list_documents()
        assert len(docs) == 1
        assert docs[0]["total_chars"] == 0
        assert docs[0]["ingested_at"] == ""

    @pytest.mark.asyncio
    async def test_list_documents_unknown_source(self, mock_chroma):
        from app.rag.retriever import list_documents

        mock_chroma.get.return_value = {
            "metadatas": [
                {"char_count": 50, "ingested_at": "2024-01-01T00:00:00"},
            ],
        }
        docs = await list_documents()
        assert len(docs) == 1
        assert docs[0]["source"] == "unknown"


class TestRetrieverDeleteDocument:
    """Tests for retriever.delete_document."""

    @pytest.mark.asyncio
    async def test_delete_document_found(self, mock_chroma):
        from app.rag.retriever import delete_document

        mock_chroma.get.return_value = {"ids": ["id1", "id2"]}
        mock_chroma.delete = MagicMock()
        result = await delete_document("doc1")
        assert result is True
        mock_chroma.delete.assert_called_once_with(ids=["id1", "id2"])

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, mock_chroma):
        from app.rag.retriever import delete_document

        mock_chroma.get.return_value = {"ids": []}
        result = await delete_document("nonexistent")
        assert result is False
        mock_chroma.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_document_none_ids(self, mock_chroma):
        from app.rag.retriever import delete_document

        mock_chroma.get.return_value = {}  # no "ids" key
        result = await delete_document("doc1")
        assert result is False


class TestRetrieverCollection:
    """Tests for the internal _collection() helper."""

    def test_collection_creates_client(self):
        with patch("chromadb.PersistentClient") as mock_cls:
            from app.rag.retriever import ingest_text

            mock_cls.return_value.get_or_create_collection.return_value = MagicMock()
            # Trigger _collection() via ingest_text
            with patch("app.rag.retriever.embed", new_callable=AsyncMock):
                with patch("app.rag.retriever.chunk_text", return_value=["chunk"]):
                    import asyncio
                    asyncio.run(ingest_text("test", source="x"))
            mock_cls.assert_called_once()
            mock_cls.return_value.get_or_create_collection.assert_called_once_with(
                name="syzygy_documents",
                metadata={"hnsw:space": "cosine"},
            )


# ===================================================================
# RAG injector — build_rag_context
# ===================================================================


class TestInjector:
    """Tests for injector.build_rag_context."""

    @pytest.mark.asyncio
    async def test_success_single_result(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"score": 0.95, "content": "Relevant document content", "metadata": {"source": "doc1"}},
            ]
            from app.rag.injector import build_rag_context

            result = await build_rag_context("test query")
            assert "Relevant document content" in result
            assert "doc1" in result
            assert "95%" in result  # score formatted as percentage

    @pytest.mark.asyncio
    async def test_success_multiple_results(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"score": 0.95, "content": "First doc", "metadata": {"source": "a"}},
                {"score": 0.80, "content": "Second doc", "metadata": {"source": "b"}},
            ]
            from app.rag.injector import build_rag_context

            result = await build_rag_context("test")
            assert "[1]" in result
            assert "[2]" in result
            assert "First doc" in result
            assert "Second doc" in result
            assert result.index("[1]") < result.index("[2]")

    @pytest.mark.asyncio
    async def test_empty_results(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            from app.rag.injector import build_rag_context

            result = await build_rag_context("test")
            assert result == ""

    @pytest.mark.asyncio
    async def test_query_exception_returns_empty(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = RuntimeError("ChromaDB unavailable")
            from app.rag.injector import build_rag_context

            result = await build_rag_context("test")
            assert result == ""

    @pytest.mark.asyncio
    async def test_missing_metadata_source_fallback(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"score": 0.9, "content": "Content without source", "metadata": {}},
            ]
            from app.rag.injector import build_rag_context

            result = await build_rag_context("test")
            assert "unknown" in result
            assert "Content without source" in result

    @pytest.mark.asyncio
    async def test_missing_content_key(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"score": 0.9, "metadata": {"source": "doc"}},
            ]
            from app.rag.injector import build_rag_context

            result = await build_rag_context("test")
            assert "source: doc" in result  # content defaults to ""

    @pytest.mark.asyncio
    async def test_missing_score_key_raises_keyerror(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"content": "No score key", "metadata": {"source": "doc"}},
            ]
            from app.rag.injector import build_rag_context

            with pytest.raises(KeyError):
                await build_rag_context("test")

    @pytest.mark.asyncio
    async def test_passes_top_k_and_min_score(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            from app.rag.injector import build_rag_context

            await build_rag_context("test", top_k=10, min_score=0.7)
            mock_query.assert_called_once_with("test", top_k=10, min_score=0.7)

    @pytest.mark.asyncio
    async def test_none_metadata_handling(self):
        with patch("app.rag.injector.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"score": 0.9, "content": "Content", "metadata": None},
            ]
            from app.rag.injector import build_rag_context

            with pytest.raises(AttributeError):
                await build_rag_context("test")
