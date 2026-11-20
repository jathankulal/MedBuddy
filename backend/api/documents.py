"""Document management API routes (GET /documents, POST /documents/upload)."""

import os
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.config import settings
from backend.database import ensure_data_dir, read_json, write_json
from backend.schemas import DocumentRead
from backend.services.pdf_service import (
    MAX_PAGES,
    PdfEmptyTextError,
    PdfInvalidFormatError,
    PdfPageCountLimitError,
    PdfPasswordProtectedError,
    PdfValidationError,
    extract_pdf,
    save_pdf,
)
from backend.services.chunking_service import chunk_document, chunks_to_records
from backend.services.vector_store import VectorStore

router = APIRouter(prefix="", tags=["documents"])

DOCUMENTS_FILENAME = "documents_metadata.json"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _load_documents() -> List[dict]:
    return read_json(settings.data_dir, DOCUMENTS_FILENAME, default=[]) or []


def _init_vector_store() -> VectorStore:
    """Initialize the persistent ChromaDB vector store."""
    return VectorStore(data_dir=settings.data_dir)


@router.get("/documents", response_model=List[DocumentRead])
def list_documents():
    """List all uploaded documents (metadata only, no extracted text or internal file paths)."""
    return [DocumentRead(**doc) for doc in _load_documents()]


@router.post("/documents/upload", response_model=DocumentRead, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF file, extract text, chunk, embed, and index for RAG."""
    # Read the uploaded file into memory
    file_bytes = await file.read()

    # 1. Size check
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "ERR_PAYLOAD_TOO_LARGE",
                    "message": "Uploaded file exceeds 10 MB size limit",
                    "details": None,
                }
            },
        )

    # 2. Validate actual PDF content (magic bytes), not just MIME type/filename
    try:
        pdf_doc = extract_pdf(file_bytes, file.filename or "uploaded.pdf")
    except (PdfPasswordProtectedError, PdfPageCountLimitError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "ERR_VALIDATION",
                    "message": str(exc),
                    "details": None,
                }
            },
        )
    except PdfValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": {
                    "code": "ERR_UNSUPPORTED_FILE",
                    "message": str(exc),
                    "details": None,
                }
            },
        )

    # 3. Save the PDF locally with collision-safe name
    saved_path = save_pdf(file_bytes, settings.data_dir, file.filename or "uploaded.pdf")

    # 4. Create document metadata record
    now = datetime.now(timezone.utc).isoformat()
    document_id = str(uuid4())

    # Chunk the extracted text
    pages = [
        {"page_number": p.page_number, "text": p.text} for p in pdf_doc.pages
    ]
    chunks = chunk_document(
        document_id=document_id,
        filename=pdf_doc.filename,
        pages=pages,
    )
    chunk_records = chunks_to_records(chunks)

    # 5. Index chunks in the vector store
    indexing_status = "indexed"
    try:
        vector_store = _init_vector_store()
        vector_store.add_chunks(chunk_records)
    except Exception as exc:
        indexing_status = "failed"
        # Extraction succeeded but indexing failed — still return 201 with status=failed

    document_record = {
        "id": document_id,
        "filename": pdf_doc.filename,
        "content_type": "application/pdf",
        "size_bytes": len(file_bytes),
        "page_count": pdf_doc.page_count,
        "chunk_count": len(chunk_records),
        "uploaded_at": now,
        "status": indexing_status,
        "file_path": str(saved_path),
    }

    # 6. Persist metadata in JSON
    documents = _load_documents()
    documents.append(document_record)
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, DOCUMENTS_FILENAME, documents)

    return DocumentRead(**document_record)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str):
    """Delete an uploaded document, its indexed chunks, and local file."""
    from pathlib import Path

    documents = _load_documents()
    target_idx = None
    target_doc = None
    for idx, doc in enumerate(documents):
        if doc.get("id") == document_id:
            target_idx = idx
            target_doc = doc
            break

    if target_doc is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_NOT_FOUND",
                    "message": "Document not found",
                    "details": None,
                }
            },
        )

    # 1. Delete vector store chunks
    vector_store = _init_vector_store()
    try:
        vector_store.delete_document(document_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ERR_INTERNAL",
                    "message": f"Failed to delete document chunks: {exc}",
                    "details": None,
                }
            },
        )

    # 2. Delete local PDF file if safely within documents directory
    raw_path = target_doc.get("file_path")
    if raw_path:
        file_path = Path(raw_path).resolve()
        configured_docs_dir = (Path(settings.data_dir) / "documents").resolve()
        if configured_docs_dir not in file_path.parents and file_path.parent != configured_docs_dir:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "ERR_INVALID_PATH",
                        "message": "Document file path is invalid or outside allowed directory",
                        "details": None,
                    }
                },
            )
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError as exc:
                target_doc["status"] = "deletion_failed"
                ensure_data_dir(settings.data_dir)
                write_json(settings.data_dir, DOCUMENTS_FILENAME, documents)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": {
                            "code": "ERR_INTERNAL",
                            "message": f"Failed to delete local document file from disk: {exc}",
                            "details": None,
                        }
                    },
                )

    # 3. Update metadata only after vector store and file deletion succeed
    documents.pop(target_idx)
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, DOCUMENTS_FILENAME, documents)
    return None
