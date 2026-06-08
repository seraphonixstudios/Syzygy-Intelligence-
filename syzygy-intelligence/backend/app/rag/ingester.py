"""Document parsing and text chunking for the RAG pipeline."""

from pathlib import Path


def parse_document(file_path: str) -> str:
    """Parse a file and return its plain-text content.

    Supports:
      - .txt  — plain text
      - .md   — Markdown (read as-is)
      - .pdf  — extracted via PyMuPDF (fitz)
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(path)
    if ext in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(path: Path) -> str:
    """Extract text from a PDF using PyMuPDF."""
    import fitz

    doc = fitz.open(str(path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph/sentence boundaries.

    Parameters
    ----------
    text : str
        Input text to chunk.
    chunk_size : int
        Target size in characters for each chunk.
    overlap : int
        Number of characters of overlap between consecutive chunks.

    Returns
    -------
    list[str]
        Ordered list of text chunks.
    """
    if not text or not text.strip():
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        break_at = _find_break_point(text, start, end)
        chunks.append(text[start:break_at])
        start = break_at - overlap
        if start < 0:
            start = 0

    return chunks


def _find_break_point(text: str, start: int, end: int) -> int:
    """Find the best position to break text between *start* and *end*."""
    midpoint = start + (end - start) // 2

    paragraph = text.rfind("\n\n", start, end)
    if paragraph > midpoint:
        return paragraph

    for sep in (". ", "! ", "? "):
        pos = text.rfind(sep, start, end)
        if pos > midpoint:
            return pos + 1  # include the punctuation mark

    space = text.rfind(" ", start, end)
    if space > midpoint:
        return space

    return end
