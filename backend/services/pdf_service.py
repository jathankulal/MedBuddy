"""PDF extraction service using PyMuPDF.

Extracts text page by page, preserves page numbers, handles encrypted/empty
PDFs, and validates actual PDF content (magic bytes) rather than relying on
filename or supplied MIME type.
"""

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF

MAX_PAGES = 100


class PdfValidationError(Exception):
    """Base exception for PDF validation errors."""


class PdfPageCountLimitError(PdfValidationError):
    """Raised when a PDF exceeds the maximum allowed page count."""


class PdfPasswordProtectedError(PdfValidationError):
    """Raised when a PDF is password-protected or encrypted."""


class PdfInvalidFormatError(PdfValidationError):
    """Raised when a file is not a valid PDF or corrupted."""


class PdfEmptyTextError(PdfValidationError):
    """Raised when a PDF contains no extractable text."""


@dataclass
class PdfPage:
    """Represents a single page of extracted text."""

    page_number: int  # 1-based
    text: str


@dataclass
class PdfDocument:
    """Represents an extracted PDF document."""

    filename: str
    page_count: int
    pages: List[PdfPage]
    total_characters: int


def is_valid_pdf(file_bytes: bytes) -> bool:
    """Validate actual PDF content by checking magic bytes (%PDF-)."""
    return file_bytes.startswith(b"%PDF-")


def extract_pdf(file_bytes: bytes, filename: str) -> PdfDocument:
    """Extract text page by page from a PDF.

    Raises PdfValidationError (or its subclasses) if the file is not a valid PDF,
    is encrypted, has too many pages, or contains no meaningful extractable text.
    """
    if not is_valid_pdf(file_bytes):
        raise PdfInvalidFormatError("File is not a valid PDF (invalid PDF header)")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise PdfInvalidFormatError(f"Cannot open PDF: {exc}") from exc

    try:
        if doc.is_encrypted or doc.needs_pass:
            raise PdfPasswordProtectedError("Password-protected or encrypted PDFs are not supported")

        page_count = len(doc)
        if page_count > MAX_PAGES:
            raise PdfPageCountLimitError(f"PDF exceeds maximum of {MAX_PAGES} pages")

        pages: List[PdfPage] = []
        total_characters = 0
        for i in range(page_count):
            page = doc[i]
            text = page.get_text() or ""
            pages.append(PdfPage(page_number=i + 1, text=text))
            total_characters += len(text.strip())

        if total_characters == 0:
            raise PdfEmptyTextError("No extractable text found in PDF")

        return PdfDocument(
            filename=filename,
            page_count=page_count,
            pages=pages,
            total_characters=total_characters,
        )
    finally:
        doc.close()


def save_pdf(file_bytes: bytes, data_dir: str, filename: str) -> Path:
    """Save uploaded PDF bytes to a local file with a collision-safe name.

    Returns the path to the saved file.
    """
    docs_dir = Path(data_dir) / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Collision-safe filename: prefix with UUID
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    safe_name = f"{stem}_{os.urandom(8).hex()}{suffix}"
    file_path = docs_dir / safe_name

    file_path.write_bytes(file_bytes)
    return file_path
