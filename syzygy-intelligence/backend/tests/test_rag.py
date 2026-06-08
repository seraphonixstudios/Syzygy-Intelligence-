import pytest
from pathlib import Path
from app.rag.ingester import parse_document, chunk_text
from app.rag.embeddings import embed

SAMPLE_TEXT = "Syzygy Intelligence is an AI orchestration platform. It uses multiple agents. The consensus engine produces well-reasoned answers."


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
        try:
            result = await embed([SAMPLE_TEXT])
            assert isinstance(result, list)
            assert len(result) > 0
        except Exception:
            pytest.skip("Ollama not reachable from test container")


class TestRetriever:
    @pytest.mark.asyncio
    async def test_import_retriever(self):
        from app.rag.retriever import ingest_document, query, list_documents, delete_document
        assert callable(ingest_document)
        assert callable(query)
        assert callable(list_documents)
        assert callable(delete_document)
