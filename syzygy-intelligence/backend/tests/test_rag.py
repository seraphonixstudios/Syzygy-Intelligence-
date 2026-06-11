
import pytest

from app.rag.embeddings import embed
from app.rag.ingester import chunk_text, parse_document

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
