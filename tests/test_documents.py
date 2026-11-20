"""Document upload API tests using mocked dependencies."""

import os
from fastapi.testclient import TestClient

import backend.api.documents as documents_mod


def _make_pdf_file_bytes(text="Sample document content."):
    import fitz
    import io
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


def test_upload_valid_pdf_success(temp_data_dir, monkeypatch):
    """POST /documents/upload accepts a valid PDF and returns metadata."""
    from backend.main import app
    client = TestClient(app)

    pdf_bytes = _make_pdf_file_bytes("Follow-up appointment scheduled for two weeks.")

    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: _FakeVectorStore())

    response = client.post(
        "/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"]
    assert body["filename"] == "test.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] == len(pdf_bytes)
    assert body["page_count"] == 1
    assert body["chunk_count"] >= 1
    assert body["uploaded_at"]
    assert body["status"] == "indexed"


def test_upload_non_pdf_rejected(temp_data_dir, monkeypatch):
    """POST /documents/upload rejects a non-PDF file."""
    from backend.main import app
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415, response.text
    body = response.json()
    assert body["error"]["code"] == "ERR_UNSUPPORTED_FILE"


def test_upload_file_too_large(temp_data_dir, monkeypatch):
    """POST /documents/upload rejects files over 10 MB."""
    from backend.main import app
    client = TestClient(app)

    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: _FakeVectorStore())

    # Create a fake PDF header with 11 MB of padding
    large_bytes = b"%PDF-1.4 " + b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/documents/upload",
        files={"file": ("big.pdf", large_bytes, "application/pdf")},
    )
    assert response.status_code == 413, response.text
    body = response.json()
    assert body["error"]["code"] == "ERR_PAYLOAD_TOO_LARGE"


def test_get_documents_empty_when_none(temp_data_dir):
    """GET /documents returns empty list when no documents exist."""
    from backend.main import app
    client = TestClient(app)
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == []


class _FakeVectorStore:
    """Fake vector store that records added chunks without ChromaDB."""
    def __init__(self):
        self.chunks = []
        self.deleted = []
    def add_chunks(self, chunks):
        self.chunks.extend(chunks)
    def query(self, query_text, document_ids=None, n_results=5):
        return []
    def delete_document(self, document_id: str):
        self.deleted.append(document_id)


def test_delete_document_success(temp_data_dir, monkeypatch):
    """DELETE /documents/{id} removes chunks, file, and metadata."""
    from backend.main import app
    client = TestClient(app)

    fake_store = _FakeVectorStore()
    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: fake_store)

    pdf_bytes = _make_pdf_file_bytes("Temporary document to be deleted.")
    res = client.post(
        "/documents/upload",
        files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    assert len(client.get("/documents").json()) == 1

    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 204
    assert doc_id in fake_store.deleted
    assert len(client.get("/documents").json()) == 0


def test_delete_document_unknown_id_returns_404(temp_data_dir, monkeypatch):
    """DELETE /documents/{id} returns 404 for missing IDs."""
    from backend.main import app
    client = TestClient(app)

    del_res = client.delete("/documents/non-existent-id")
    assert del_res.status_code == 404
    assert del_res.json()["error"]["code"] == "ERR_NOT_FOUND"


def test_document_responses_do_not_expose_file_path(temp_data_dir, monkeypatch):
    """GET /documents and POST /documents/upload must never expose internal filesystem paths."""
    from backend.main import app
    client = TestClient(app)

    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: _FakeVectorStore())

    pdf_bytes = _make_pdf_file_bytes("Confidential lab report")
    upload_res = client.post(
        "/documents/upload",
        files={"file": ("lab_report.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert "file_path" not in upload_data

    list_res = client.get("/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) == 1
    assert "file_path" not in docs[0]


def test_upload_pdf_page_limit_returns_422(temp_data_dir, monkeypatch):
    """POST /documents/upload returns 422 ERR_VALIDATION when PDF exceeds page limit."""
    from backend.main import app
    import backend.services.pdf_service as pdf_service_mod
    client = TestClient(app)

    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: _FakeVectorStore())
    monkeypatch.setattr(pdf_service_mod, "MAX_PAGES", 2)
    monkeypatch.setattr(documents_mod, "MAX_PAGES", 2)

    import fitz
    import io
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i+1} content")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()

    res = client.post(
        "/documents/upload",
        files={"file": ("three_pages.pdf", buf.getvalue(), "application/pdf")},
    )
    assert res.status_code == 422
    body = res.json()
    assert body["error"]["code"] == "ERR_VALIDATION"
    assert "exceeds maximum of 2 pages" in body["error"]["message"]


def test_delete_document_vector_store_failure(temp_data_dir, monkeypatch):
    """DELETE /documents/{id} returns 500 ERR_INTERNAL if vector store deletion fails."""
    from backend.main import app
    client = TestClient(app)

    fake_store = _FakeVectorStore()
    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: fake_store)

    pdf_bytes = _make_pdf_file_bytes("Doc to fail vector deletion.")
    res = client.post(
        "/documents/upload",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    def _failing_delete(self, doc_id):
        raise RuntimeError("ChromaDB connection lost")

    monkeypatch.setattr(_FakeVectorStore, "delete_document", _failing_delete)

    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 500
    assert del_res.json()["error"]["code"] == "ERR_INTERNAL"


def test_delete_document_file_unlink_failure_marks_failed(temp_data_dir, monkeypatch):
    """DELETE /documents/{id} returns 500 and marks deletion_failed if disk unlink fails."""
    from pathlib import Path
    from backend.main import app
    client = TestClient(app)

    fake_store = _FakeVectorStore()
    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: fake_store)

    pdf_bytes = _make_pdf_file_bytes("Doc with locked file.")
    res = client.post(
        "/documents/upload",
        files={"file": ("locked.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    def _failing_unlink(self, *args, **kwargs):
        raise OSError("Permission denied: file locked")

    monkeypatch.setattr(Path, "unlink", _failing_unlink)

    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 500
    assert del_res.json()["error"]["code"] == "ERR_INTERNAL"

    raw_docs = documents_mod._load_documents()
    found = [d for d in raw_docs if d["id"] == doc_id]
    assert len(found) == 1
    assert found[0]["status"] == "deletion_failed"


def test_delete_document_path_traversal_rejected(temp_data_dir, monkeypatch):
    """DELETE /documents/{id} returns 400 if metadata contains unsafe path outside documents dir."""
    from backend.main import app
    client = TestClient(app)

    fake_store = _FakeVectorStore()
    monkeypatch.setattr(documents_mod, "_init_vector_store", lambda: fake_store)

    docs = documents_mod._load_documents()
    docs.append({
        "id": "malicious-doc",
        "filename": "passwd.pdf",
        "content_type": "application/pdf",
        "size_bytes": 100,
        "page_count": 1,
        "chunk_count": 1,
        "uploaded_at": "2026-03-01T00:00:00Z",
        "status": "indexed",
        "file_path": "/etc/shadow",
    })
    documents_mod.write_json(documents_mod.settings.data_dir, documents_mod.DOCUMENTS_FILENAME, docs)

    del_res = client.delete("/documents/malicious-doc")
    assert del_res.status_code == 400
    assert del_res.json()["error"]["code"] == "ERR_INVALID_PATH"
