"""Chat / RAG tests with safety engine integration and fail-closed validation."""

import pytest
from fastapi.testclient import TestClient

import backend.api.chat as chat_mod
from backend.services import safety_integration
from backend.main import app


def test_chat_normal_mode_with_real_safety(temp_data_dir, monkeypatch):
    """POST /chat in normal mode passes safety assessment and calls generation."""
    # Mock Gemini client to avoid external API calls
    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            return "Your follow-up is in two weeks."

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    # Mock retrieval service to return known chunks
    class FakeRetrievalService:
        def retrieve(self, query, document_ids=None, n_results=5):
            return [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-123",
                    "filename": "discharge.pdf",
                    "page_number": 2,
                    "text": "Follow-up appointment scheduled for two weeks after the procedure.",
                    "relevance_score": 0.92,
                }
            ]

    monkeypatch.setattr(chat_mod, "_get_retrieval_service", lambda: FakeRetrievalService())

    client = TestClient(app)
    response = client.post("/chat", json={"message": "When is my follow-up?"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answer"] == "Your follow-up is in two weeks."
    assert body["response_mode"] == "normal"
    assert body["context_used"] is True
    assert "documents" in body["context_sources"]
    assert len(body["citations"]) == 1
    assert body["citations"][0]["document_id"] == "doc-123"
    assert body["citations"][0]["filename"] == "discharge.pdf"
    assert body["citations"][0]["page_number"] == 2
    assert body["safety"]["emergency"] is False
    assert body["disclaimer"]


def test_chat_emergency_normalization_and_bypass(temp_data_dir, monkeypatch):
    """1. is_emergency=True is normalized; 2. Gemini not called; 3. Retrieval not called."""
    gemini_called = []
    retrieval_called = []

    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            gemini_called.append(True)
            return "should not be called"

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    class FakeRetrievalService:
        def retrieve(self, query, document_ids=None, n_results=5):
            retrieval_called.append(True)
            return []

    monkeypatch.setattr(chat_mod, "_get_retrieval_service", lambda: FakeRetrievalService())

    client = TestClient(app)
    # "chest pain" triggers real safety engine emergency detection
    response = client.post("/chat", json={"message": "I am experiencing severe chest pain and trouble breathing"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["response_mode"] == "emergency"
    assert body["safety"]["emergency"] is True
    assert body["safety"]["requires_human_review"] is True
    assert body["safety"]["emergency_reason"] is not None
    assert "chest pain" in body["safety"]["emergency_reason"]
    assert body["context_used"] is False
    assert body["context_sources"] == []
    assert body["citations"] == []
    assert "emergency" in body["answer"].lower()

    # Verify Gemini was NEVER called
    assert len(gemini_called) == 0
    # Verify Document retrieval was NEVER called
    assert len(retrieval_called) == 0


def test_chat_emergency_precheck_ignores_malformed_personal_records(temp_data_dir, monkeypatch):
    """Emergency detection happens before loading malformed personal JSON records."""
    gemini_called = []

    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            gemini_called.append(True)
            return "should not be called"

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    # Simulate corrupted profile loader that throws error
    def _broken_load(data_dir):
        raise ValueError("Corrupt JSON file on disk")

    monkeypatch.setattr(safety_integration, "_load_profile", _broken_load)

    client = TestClient(app)
    # Even if profile loading would crash, emergency pre-check catches chest pain first
    response = client.post("/chat", json={"message": "I have chest pain"})
    assert response.status_code == 200
    body = response.json()
    assert body["response_mode"] == "emergency"
    assert body["safety"]["emergency"] is True
    assert len(gemini_called) == 0


def test_chat_missing_safety_engine_returns_err_safety(temp_data_dir, monkeypatch):
    """4. Missing Safety Engine returns ERR_SAFETY_ENGINE."""
    gemini_called = []

    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            gemini_called.append(True)
            return "should not be called"

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    # Monkeypatch the safety import to raise ImportError
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("safety"):
            raise ImportError("No module named 'safety'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    client = TestClient(app)
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 500, response.text
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"
    assert "Safety engine is not integrated" in body["error"]["message"]
    # 7. Safety failure never calls Gemini
    assert len(gemini_called) == 0


def test_chat_safety_engine_exception_returns_err_safety(temp_data_dir, monkeypatch):
    """5. Safety Engine exception returns ERR_SAFETY_ENGINE."""
    gemini_called = []

    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            gemini_called.append(True)
            return "should not be called"

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    import safety.engine as se_mod
    monkeypatch.setattr(
        se_mod,
        "assess_safety",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Unexpected engine crash")),
    )

    client = TestClient(app)
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 500, response.text
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"
    assert "Safety engine call failed" in body["error"]["message"]
    # 7. Safety failure never calls Gemini
    assert len(gemini_called) == 0


@pytest.mark.parametrize(
    "invalid_output,desc",
    [
        ("not a dict", "non-dict"),
        ({"is_emergency": "true", "requires_human_review": True, "warnings": [], "checked_items": []}, "string-bool-emergency"),
        ({"is_emergency": True, "requires_human_review": "false", "warnings": [], "checked_items": []}, "string-bool-review"),
        ({"is_emergency": False, "requires_human_review": True, "warnings": "not a list", "checked_items": []}, "non-list-warnings"),
        ({"is_emergency": False, "requires_human_review": True, "warnings": [{"code": "C", "severity": "invalid_sev", "message": "M"}], "checked_items": []}, "invalid-severity"),
        ({"is_emergency": False, "requires_human_review": True, "warnings": [{"code": "C"}], "checked_items": []}, "missing-warning-fields"),
        ({"is_emergency": False, "requires_human_review": True, "warnings": [], "checked_items": "not a list"}, "non-list-checked-items"),
    ],
)
def test_chat_invalid_safety_engine_output_returns_err_safety(temp_data_dir, monkeypatch, invalid_output, desc):
    """6. Invalid Safety Engine output returns ERR_SAFETY_ENGINE strictly."""
    gemini_called = []

    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            gemini_called.append(True)
            return "should not be called"

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    import safety.engine as se_mod
    monkeypatch.setattr(
        se_mod,
        "assess_safety",
        lambda *args, **kwargs: invalid_output,
    )

    client = TestClient(app)
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 500, f"Failed for {desc}: {response.text}"
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"
    # 7. Safety failure never calls Gemini
    assert len(gemini_called) == 0


def test_chat_invalid_pydantic_model_output_rejected(temp_data_dir, monkeypatch):
    """SafetyResult instance with invalid warning severity or non-string code is strictly rejected."""
    gemini_called = []

    class FakeGeminiClient:
        def is_configured(self):
            return True

        def generate(self, prompt, temperature=0.3, max_tokens=1024):
            gemini_called.append(True)
            return "should not be called"

    monkeypatch.setattr(chat_mod, "_get_gemini_client", lambda: FakeGeminiClient())

    from backend.schemas import SafetyResult, SafetyWarning

    # Create a SafetyResult with an invalid warning severity
    invalid_model = SafetyResult(
        emergency=False,
        emergency_reason=None,
        warnings=[SafetyWarning(code="INVALID", severity="not_a_valid_severity", message="test")],
        requires_human_review=True,
        checked_items=["emergency_signals"],
    )

    import safety.engine as se_mod
    monkeypatch.setattr(se_mod, "assess_safety", lambda *args, **kwargs: invalid_model)

    client = TestClient(app)
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"
    assert len(gemini_called) == 0


def test_validate_warning_strictly_validates_safety_warning_instance():
    """_validate_warning does not blindly return SafetyWarning instances without checking."""
    from backend.services.safety_integration import _validate_warning
    from backend.schemas import SafetyWarning

    # Empty code
    with pytest.raises(RuntimeError, match="code must be a non-empty string"):
        _validate_warning(SafetyWarning(code="", severity="warning", message="msg"), 0)

    # Invalid severity
    with pytest.raises(RuntimeError, match="severity 'unrecognized' must be one of"):
        _validate_warning(SafetyWarning(code="TEST", severity="unrecognized", message="msg"), 0)

    # Empty message
    with pytest.raises(RuntimeError, match="message must be a non-empty string"):
        _validate_warning(SafetyWarning(code="TEST", severity="warning", message="   "), 0)
