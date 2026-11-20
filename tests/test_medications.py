"""Medication endpoint tests."""

from datetime import date
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.main import app


def _make_medication_payload(name="Lisinopril", **overrides):
    payload = {
        "name": name,
        "generic_name": "lisinopril",
        "active_ingredients": ["lisinopril"],
        "strength": "10 mg",
        "route": "oral",
        "dosage": "10 mg",
        "frequency": "once daily",
        "start_date": "2026-01-10",
        "end_date": "2026-12-31",
        "prescribing_doctor": "Dr. Smith",
        "indication": "hypertension",
        "notes": "Take with food",
        "status": "active",
    }
    payload.update(overrides)
    return payload


def test_get_medications_empty_when_none(temp_data_dir):
    """GET /medications returns an empty list when no medications exist."""
    client = TestClient(app)
    response = client.get("/medications")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_medication(temp_data_dir):
    """POST /medications creates a medication; GET /medications lists it."""
    client = TestClient(app)
    payload = _make_medication_payload()
    response = client.post("/medications", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    UUID(body["id"])
    assert body["name"] == "Lisinopril"
    assert body["generic_name"] == "lisinopril"
    assert body["active_ingredients"] == ["lisinopril"]
    assert body["strength"] == "10 mg"
    assert body["route"] == "oral"
    assert body["status"] == "active"
    assert body["created_at"] is not None
    assert body["updated_at"] == body["created_at"]

    list_response = client.get("/medications")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_medication_with_all_fields(temp_data_dir):
    """POST /medications accepts every contract-defined field."""
    client = TestClient(app)
    payload = _make_medication_payload()
    response = client.post("/medications", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["generic_name"] == "lisinopril"
    assert body["strength"] == "10 mg"
    assert body["route"] == "oral"
    assert body["dosage"] == "10 mg"
    assert body["frequency"] == "once daily"
    assert body["start_date"] == "2026-01-10"
    assert body["end_date"] == "2026-12-31"
    assert body["prescribing_doctor"] == "Dr. Smith"
    assert body["indication"] == "hypertension"
    assert body["notes"] == "Take with food"
    assert body["status"] == "active"
    # When safety engine is active and profile is empty, allergy warning is returned
    assert isinstance(body.get("medication_warnings"), list)


def test_create_medication_name_required(temp_data_dir):
    """POST /medications requires a non-empty name."""
    client = TestClient(app)
    response = client.post("/medications", json={"name": ""})
    assert response.status_code == 422

    response = client.post("/medications", json={})
    assert response.status_code == 422


def test_get_medication_by_id(temp_data_dir):
    """GET /medications/{id} returns the correct medication."""
    client = TestClient(app)
    created = client.post("/medications", json=_make_medication_payload()).json()
    response = client.get(f"/medications/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["name"] == "Lisinopril"


def test_get_medication_unknown_id_returns_404(temp_data_dir):
    """GET /medications/{id} returns 404 for unknown IDs."""
    client = TestClient(app)
    response = client.get("/medications/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "ERR_NOT_FOUND"


def test_update_medication_preserves_created_at_refreshes_updated_at(temp_data_dir):
    """PUT /medications/{id} preserves created_at and updates updated_at."""
    client = TestClient(app)
    created = client.post("/medications", json=_make_medication_payload()).json()
    first_updated = created["updated_at"]

    import time
    time.sleep(0.01)

    response = client.put(
        f"/medications/{created['id']}",
        json={"dosage": "20 mg", "status": "discontinued"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["dosage"] == "20 mg"
    assert body["status"] == "discontinued"
    assert body["name"] == "Lisinopril"  # unchanged fields preserved
    assert body["created_at"] == created["created_at"]  # preserved
    assert body["updated_at"] != first_updated  # refreshed


def test_update_medication_unknown_id_returns_404(temp_data_dir):
    """PUT /medications/{id} returns 404 for unknown IDs."""
    client = TestClient(app)
    response = client.put(
        "/medications/00000000-0000-0000-0000-000000000000",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


def test_delete_medication(temp_data_dir):
    """DELETE /medications/{id} removes the medication."""
    client = TestClient(app)
    created = client.post("/medications", json=_make_medication_payload()).json()
    response = client.delete(f"/medications/{created['id']}")
    assert response.status_code == 204

    list_response = client.get("/medications")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0

    get_response = client.get(f"/medications/{created['id']}")
    assert get_response.status_code == 404


def test_delete_medication_unknown_id_returns_404(temp_data_dir):
    """DELETE /medications/{id} returns 404 for unknown IDs."""
    client = TestClient(app)
    response = client.delete("/medications/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_medication_end_date_before_start_date_rejected(temp_data_dir):
    """POST /medications rejects end_date before start_date."""
    client = TestClient(app)
    payload = _make_medication_payload(start_date="2026-12-31", end_date="2026-01-01")
    response = client.post("/medications", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ERR_VALIDATION"


def test_medication_status_values(temp_data_dir):
    """POST /medications accepts active and discontinued status values."""
    client = TestClient(app)
    for status in ["active", "discontinued"]:
        payload = _make_medication_payload(name=f"Med {status}", status=status)
        response = client.post("/medications", json=payload)
        assert response.status_code == 201, f"Failed for status {status}"
        assert response.json()["status"] == status


def test_medication_invalid_status_rejected(temp_data_dir):
    """POST /medications rejects invalid status values."""
    client = TestClient(app)
    payload = _make_medication_payload(status="invalid")
    response = client.post("/medications", json=payload)
    assert response.status_code == 422


def test_medication_active_ingredients_length_enforced(temp_data_dir):
    """POST /medications rejects active_ingredients items over 200 chars."""
    client = TestClient(app)
    payload = _make_medication_payload(active_ingredients=["A" * 201])
    response = client.post("/medications", json=payload)
    assert response.status_code == 422


def test_medication_persists_across_test_client_instances(temp_data_dir):
    """Medication data persists when creating a new TestClient (simulates restart)."""
    client = TestClient(app)
    created = client.post("/medications", json=_make_medication_payload()).json()

    client2 = TestClient(app)
    response = client2.get(f"/medications/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Lisinopril"


def test_error_response_format_is_consistent(temp_data_dir):
    """Validation errors follow the documented error envelope."""
    client = TestClient(app)
    response = client.post("/medications", json={})
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "ERR_VALIDATION"
    assert "message" in body["error"]
    assert "details" in body["error"]


# --- Safety Engine Integration Tests ---

def test_missing_safety_engine_blocks_medication_creation(temp_data_dir, monkeypatch):
    """1. Missing Safety Engine blocks medication creation with 500 ERR_SAFETY_ENGINE."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("safety"):
            raise ImportError("No module named 'safety'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    client = TestClient(app)
    response = client.post("/medications", json=_make_medication_payload())
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"
    assert "Safety engine is not integrated" in body["error"]["message"]


def test_safety_engine_exception_blocks_medication_creation(temp_data_dir, monkeypatch):
    """2. Safety Engine exception blocks medication creation with 500 ERR_SAFETY_ENGINE."""
    import safety.engine as se_mod
    monkeypatch.setattr(
        se_mod,
        "check_medication_entry",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Engine crash")),
    )

    client = TestClient(app)
    response = client.post("/medications", json=_make_medication_payload())
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"
    assert "Safety engine medication check failed" in body["error"]["message"]


@pytest.mark.parametrize(
    "invalid_output",
    [
        "not a dict",
        {"is_duplicate": "true", "requires_human_review": True, "warnings": []},
        {"is_duplicate": True, "requires_human_review": "false", "warnings": []},
        {"is_duplicate": False, "requires_human_review": True, "warnings": "not a list"},
        {"is_duplicate": False, "requires_human_review": True, "warnings": [{"code": "X"}]},
    ],
)
def test_invalid_safety_engine_output_blocks_medication_creation(temp_data_dir, monkeypatch, invalid_output):
    """3. Invalid Safety Engine output blocks medication creation with 500 ERR_SAFETY_ENGINE."""
    import safety.engine as se_mod
    monkeypatch.setattr(
        se_mod,
        "check_medication_entry",
        lambda *args, **kwargs: invalid_output,
    )

    client = TestClient(app)
    response = client.post("/medications", json=_make_medication_payload())
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"


def test_safety_failure_blocks_medication_updates(temp_data_dir, monkeypatch):
    """4. Safety failure blocks medication updates with 500 ERR_SAFETY_ENGINE."""
    client = TestClient(app)
    created = client.post("/medications", json=_make_medication_payload()).json()
    med_id = created["id"]

    # Now make the safety engine crash on update
    import safety.engine as se_mod
    monkeypatch.setattr(
        se_mod,
        "check_medication_entry",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Update check failed")),
    )

    response = client.put(f"/medications/{med_id}", json={"dosage": "20 mg"})
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "ERR_SAFETY_ENGINE"

    # Verify original record was NOT modified
    unmodified = client.get(f"/medications/{med_id}").json()
    assert unmodified["dosage"] == "10 mg"


def test_exact_duplicate_returns_409(temp_data_dir):
    """5. Exact duplicate returns HTTP 409 ERR_CONFLICT."""
    client = TestClient(app)
    payload = _make_medication_payload()
    first = client.post("/medications", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/medications", json=payload)
    assert duplicate.status_code == 409
    body = duplicate.json()
    assert body["error"]["code"] == "ERR_CONFLICT"


def test_duplicate_response_contains_correct_metadata(temp_data_dir):
    """6. Duplicate response contains correct metadata in error details."""
    client = TestClient(app)
    payload = _make_medication_payload(
        name="Metformin",
        dosage="500 mg",
        route="oral",
        strength="500 mg",
    )
    first_resp = client.post("/medications", json=payload)
    assert first_resp.status_code == 201
    first_id = first_resp.json()["id"]

    dup_resp = client.post("/medications", json=payload)
    assert dup_resp.status_code == 409
    details = dup_resp.json()["error"]["details"]
    assert details["duplicate_type"] == "exact"
    assert details["matched_item"] == "Metformin"
    assert details["existing_medication_id"] == first_id
    assert details["checked_items"] == ["medications", "allergies"]
    assert len(details["warnings"]) > 0
    assert any(w["code"] == "MED_EXACT_DUPLICATE" for w in details["warnings"])


def test_ingredient_overlap_creates_warning_without_rejection(temp_data_dir):
    """7. Ingredient overlap creates a warning but does not reject the medication."""
    client = TestClient(app)
    # First med: Tylenol with acetaminophen
    med1 = _make_medication_payload(
        name="Tylenol",
        active_ingredients=["acetaminophen"],
        dosage="500 mg",
        strength="500 mg",
        route="oral",
    )
    r1 = client.post("/medications", json=med1)
    assert r1.status_code == 201

    # Second med: Panadol with acetaminophen (different name/dosage -> not exact duplicate)
    med2 = _make_medication_payload(
        name="Panadol",
        active_ingredients=["acetaminophen"],
        dosage="650 mg",
        strength="650 mg",
        route="oral",
    )
    r2 = client.post("/medications", json=med2)
    assert r2.status_code == 201
    body2 = r2.json()
    assert body2["name"] == "Panadol"
    warnings = body2.get("medication_warnings", [])
    assert any(w["code"] == "MED_INGREDIENT_OVERLAP" for w in warnings)
    overlap_warn = next(w for w in warnings if w["code"] == "MED_INGREDIENT_OVERLAP")
    assert overlap_warn["matched_item"] == "acetaminophen"


def test_failed_safety_check_never_persists_medication(temp_data_dir, monkeypatch):
    """8. A failed safety check never persists a medication."""
    client = TestClient(app)
    initial_list = client.get("/medications").json()
    initial_count = len(initial_list)

    # 1. Failure due to engine error
    import safety.engine as se_mod
    original_check = se_mod.check_medication_entry
    monkeypatch.setattr(
        se_mod,
        "check_medication_entry",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Crashed")),
    )
    failed_resp = client.post("/medications", json=_make_medication_payload(name="ShouldNotPersist"))
    assert failed_resp.status_code == 500
    after_failed = client.get("/medications").json()
    assert len(after_failed) == initial_count

    # 2. Rejection due to exact duplicate
    monkeypatch.setattr(se_mod, "check_medication_entry", original_check)
    valid_resp = client.post("/medications", json=_make_medication_payload(name="Persisted"))
    assert valid_resp.status_code == 201
    count_with_one = len(client.get("/medications").json())
    assert count_with_one == initial_count + 1

    dup_resp = client.post("/medications", json=_make_medication_payload(name="Persisted"))
    assert dup_resp.status_code == 409
    after_dup = client.get("/medications").json()
    assert len(after_dup) == count_with_one


def test_duplicate_id_requires_full_identity_key_match_not_name_only(temp_data_dir, monkeypatch):
    """existing_medication_id is populated ONLY when full identity key matches, returning None on name-only match."""
    client = TestClient(app)
    # Create initial medication: Metformin 500 mg oral 500 mg
    initial_med = _make_medication_payload(
        name="Metformin",
        dosage="500 mg",
        route="oral",
        strength="500 mg",
    )
    first_resp = client.post("/medications", json=initial_med)
    assert first_resp.status_code == 201
    first_id = first_resp.json()["id"]

    # Scenario A: Candidate has same name but DIFFERENT dosage/strength (not full identity match)
    # Even if safety engine returned is_duplicate=True, existing_medication_id must remain None (no name-only fallback)
    import safety.engine as se_mod
    monkeypatch.setattr(
        se_mod,
        "check_medication_entry",
        lambda candidate_medication, health_profile, existing_medications: {
            "is_duplicate": True,
            "requires_human_review": True,
            "warnings": [
                {
                    "code": "MED_EXACT_DUPLICATE",
                    "severity": "warning",
                    "message": "Duplicate",
                    "matched_item": "Metformin",
                }
            ],
        },
    )

    different_dose_med = _make_medication_payload(
        name="Metformin",
        dosage="1000 mg",  # Different dosage!
        route="oral",
        strength="1000 mg",  # Different strength!
    )
    resp_diff = client.post("/medications", json=different_dose_med)
    assert resp_diff.status_code == 409
    # Must be None because full identity key did NOT match
    assert resp_diff.json()["error"]["details"]["existing_medication_id"] is None
    assert resp_diff.json()["error"]["details"]["matched_item"] == "Metformin"

    # Scenario B: Candidate matches full identity key exactly
    resp_exact = client.post("/medications", json=initial_med)
    assert resp_exact.status_code == 409
    assert resp_exact.json()["error"]["details"]["existing_medication_id"] == first_id


def test_check_medication_safety_strictly_validates_model_instance(temp_data_dir, monkeypatch):
    """check_medication_safety strictly validates MedicationSafetyResult model instances."""
    from backend.schemas import MedicationSafetyResult, SafetyWarning
    import safety.engine as se_mod

    # Case 1: Model with invalid warning severity
    invalid_model = MedicationSafetyResult(
        is_duplicate=False,
        duplicate_type="none",
        warnings=[SafetyWarning(code="INVALID", severity="illegal_severity", message="msg")],
        requires_human_review=False,
        checked_items=["medications"],
    )
    monkeypatch.setattr(se_mod, "check_medication_entry", lambda *args, **kwargs: invalid_model)

    client = TestClient(app)
    resp1 = client.post("/medications", json=_make_medication_payload())
    assert resp1.status_code == 500
    assert resp1.json()["error"]["code"] == "ERR_SAFETY_ENGINE"

    # Case 2: Model with invalid duplicate_type
    invalid_type_model = MedicationSafetyResult(
        is_duplicate=False,
        duplicate_type="unrecognized_duplicate_type",
        warnings=[],
        requires_human_review=False,
        checked_items=["medications"],
    )
    monkeypatch.setattr(se_mod, "check_medication_entry", lambda *args, **kwargs: invalid_type_model)
    resp2 = client.post("/medications", json=_make_medication_payload())
    assert resp2.status_code == 500
    assert resp2.json()["error"]["code"] == "ERR_SAFETY_ENGINE"
