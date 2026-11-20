"""PDF service and document management tests."""

import io
import os

import fitz  # PyMuPDF
import pytest

from backend.services.pdf_service import MAX_PAGES, PdfValidationError, extract_pdf, is_valid_pdf, save_pdf
from backend.services.chunking_service import chunk_document, chunks_to_records


def _make_minimal_pdf_bytes(text_by_page):
    """Create a minimal PDF with the given text per page."""
    doc = fitz.open()
    for text in text_by_page:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


def test_is_valid_pdf_true_for_pdf():
    assert is_valid_pdf(b"%PDF-1.4 fake content") is True


def test_is_valid_pdf_false_for_non_pdf():
    assert is_valid_pdf(b"not a pdf") is False
    assert is_valid_pdf(b"") is False


def test_extract_pdf_preserves_page_numbers(temp_data_dir):
    pdf_bytes = _make_minimal_pdf_bytes(["Page one content.", "Page two content."])
    doc = extract_pdf(pdf_bytes, "test.pdf")
    assert doc.page_count == 2
    assert doc.pages[0].page_number == 1
    assert doc.pages[0].text.strip() == "Page one content."
    assert doc.pages[1].page_number == 2
    assert doc.pages[1].text.strip() == "Page two content."


def test_extract_pdf_rejects_non_pdf():
    with pytest.raises(PdfValidationError):
        extract_pdf(b"not a pdf", "fake.pdf")


def test_extract_pdf_rejects_empty_text():
    pdf_bytes = _make_minimal_pdf_bytes(["", "   "])
    with pytest.raises(PdfValidationError):
        extract_pdf(pdf_bytes, "empty.pdf")


def test_extract_pdf_page_count_limit(temp_data_dir):
    # Create a PDF with more than MAX_PAGES pages
    doc = fitz.open()
    for i in range(MAX_PAGES + 1):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i+1}")
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    with pytest.raises(PdfValidationError) as exc:
        extract_pdf(buffer.getvalue(), "too_many.pdf")
    assert str(MAX_PAGES) in str(exc.value)


def test_chunk_document_preserves_page_references():
    document_id = "doc-123"
    filename = "test.pdf"
    pages = [
        {"page_number": 1, "text": "This is page one content. " * 30},
        {"page_number": 2, "text": "This is page two content. " * 30},
    ]
    chunks = chunk_document(document_id, filename, pages, chunk_size=200, chunk_overlap=50)
    assert len(chunks) > 0

    # Each chunk must carry correct document_id, filename, page_number
    for chunk in chunks:
        assert chunk.document_id == document_id
        assert chunk.filename == filename
        assert chunk.page_number in (1, 2)
        assert chunk.text
        assert chunk.chunk_id

    # Page 1 chunks should reference page 1
    page1_chunks = [c for c in chunks if c.page_number == 1]
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(page1_chunks) > 0
    assert len(page2_chunks) > 0

    # Chunk IDs are stable and unique
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_chunks_to_records():
    chunks = [
        type("Chunk", (), {
            "chunk_id": "c1", "document_id": "d1", "filename": "f.pdf",
            "page_number": 1, "text": "hello"
        })(),
    ]
    records = chunks_to_records(chunks)
    assert len(records) == 1
    assert records[0]["chunk_id"] == "c1"
    assert records[0]["page_number"] == 1


def test_save_pdf_creates_file_and_unique_names(temp_data_dir):
    pdf_bytes = b"%PDF-1.4 fake"
    path1 = save_pdf(pdf_bytes, temp_data_dir, "test.pdf")
    path2 = save_pdf(pdf_bytes, temp_data_dir, "test.pdf")
    assert path1.exists()
    assert path2.exists()
    assert path1 != path2  # collision-safe names
    assert path1.suffix == ".pdf"
    assert path2.suffix == ".pdf"
