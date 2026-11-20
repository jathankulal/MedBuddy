"""Page-aware text chunking service.

Splits extracted PDF text into overlapping chunks while preserving document
ID, filename, and original page number metadata.
"""

import hashlib
from dataclasses import dataclass
from typing import List, Optional


CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 100  # overlap between consecutive chunks


@dataclass
class Chunk:
    """Represents a text chunk with source metadata."""

    chunk_id: str
    document_id: str
    filename: str
    page_number: int  # 1-based page in the source PDF
    text: str


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks of approximately `size` characters."""
    if not text.strip():
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


def chunk_document(
    document_id: str,
    filename: str,
    pages: List[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Chunk]:
    """Chunk a document page by page, preserving page references.

    Each page is chunked independently so page references are never lost.
    Chunks spanning multiple pages are split at page boundaries.
    """
    chunks: List[Chunk] = []

    for page in pages:
        page_number = page["page_number"]
        page_text = page["text"]

        page_chunks = _chunk_text(page_text, size=chunk_size, overlap=chunk_overlap)
        for idx, chunk_text in enumerate(page_chunks):
            # Stable, unique chunk ID: hash of document + page + index
            hash_input = f"{document_id}:{page_number}:{idx}".encode("utf-8")
            chunk_id = hashlib.sha256(hash_input).hexdigest()[:16]

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename=filename,
                    page_number=page_number,
                    text=chunk_text,
                )
            )

    return chunks


def chunks_to_records(chunks: List[Chunk]) -> List[dict]:
    """Convert Chunk dataclasses to plain dict records for persistence/indexing."""
    return [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "filename": c.filename,
            "page_number": c.page_number,
            "text": c.text,
        }
        for c in chunks
    ]
