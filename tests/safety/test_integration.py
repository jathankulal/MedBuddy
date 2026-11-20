"""Regression tests for safety engine integration hardening.

Covers:
- Medication identity matching only on full identity (name, dosage, route, strength).
- Strict validation of SafetyResult, MedicationSafetyResult, and SafetyWarning
  model instances (including model_construct bypass attempts).
- Existing valid behavior remains unchanged.
"""

import pytest

from backend.services.safety_integration import (
    _medication_identity,
    _normalize_safety_result,
    _validate_warning,
    check_medication_safety,
)
from backend.schemas import MedicationSafetyResult, SafetyResult, SafetyWarning


# ---------------------------------------------------------------------------
# Medication identity matching
# ---------------------------------------------------------------------------

def test_same_name_different_strength_does_not_match():
    """Same name but different strength must NOT produce matching identities."""
    candidate = {"name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "20 mg"}
    existing = {"id": "med-1", "name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is not None
    assert _medication_identity(candidate) != _medication_identity(existing)


def test_same_name_different_dosage_does_not_match():
    """Same name but different dosage must NOT produce matching identities."""
    candidate = {"name": "Lisinopril", "dosage": "20 mg", "route": "oral", "strength": "10 mg"}
    existing = {"id": "med-1", "name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) != _medication_identity(existing)


def test_same_name_different_route_does_not_match():
    """Same name but different route must NOT produce matching identities."""
    candidate = {"name": "Lisinopril", "dosage": "10 mg", "route": "IV", "strength": "10 mg"}
    existing = {"id": "med-1", "name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) != _medication_identity(existing)


def test_full_identity_match_resolves_same_key():
    """Full identity match (name, dosage, route, strength) produces identical keys."""
    candidate = {"name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    existing = {"id": "med-1", "name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) == _medication_identity(existing)


def test_incomplete_identity_returns_none():
    """Missing any identity field returns None."""
    assert _medication_identity({"name": "Lisinopril", "dosage": "10 mg", "route": "oral"}) is None
    assert _medication_identity({"name": "Lisinopril", "dosage": "10 mg", "strength": "10 mg"}) is None
    assert _medication_identity({"name": "Lisinopril", "route": "oral", "strength": "10 mg"}) is None
    assert _medication_identity({"dosage": "10 mg", "route": "oral", "strength": "10 mg"}) is None


def test_existing_medication_id_only_on_full_identity_match(monkeypatch):
    """existing_medication_id is only set when all identity fields match."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": True,
        "requires_human_review": True,
        "warnings": [],
        "checked_items": ["medications", "allergies"],
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)

    # Different strength -> no ID match even though is_duplicate=True
    candidate = {"name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "20 mg"}
    existing = [{"id": "med-1", "name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}]
    normalized = check_medication_safety(candidate, {}, existing)
    assert normalized.is_duplicate is True
    assert normalized.existing_medication_id is None

    # Full match -> ID resolved
    candidate2 = {"name": "Lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    normalized2 = check_medication_safety(candidate2, {}, existing)
    assert normalized2.is_duplicate is True
    assert normalized2.existing_medication_id == "med-1"


# ---------------------------------------------------------------------------
# SafetyResult strict validation
# ---------------------------------------------------------------------------

def test_valid_safety_result_dict_passes():
    """Valid dict SafetyResult is accepted."""
    result = {
        "is_emergency": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications", "allergies"],
    }
    normalized = _normalize_safety_result(result)
    assert normalized.emergency is False
    assert normalized.requires_human_review is False


def test_valid_safety_result_model_passes():
    """Valid SafetyResult model instance is accepted."""
    result = SafetyResult(
        emergency=False,
        requires_human_review=False,
        warnings=[],
        checked_items=["medications", "allergies"],
    )
    normalized = _normalize_safety_result(result)
    assert normalized.emergency is False


def test_safety_result_model_construct_non_bool_emergency_is_rejected():
    """SafetyResult.model_construct with non-bool emergency raises RuntimeError."""
    result = SafetyResult.model_construct(emergency="yes")
    with pytest.raises(RuntimeError, match="must be a strict boolean"):
        _normalize_safety_result(result)


def test_safety_result_model_construct_missing_required_is_rejected():
    """SafetyResult.model_construct with no fields raises RuntimeError."""
    result = SafetyResult.model_construct()
    with pytest.raises(RuntimeError):
        _normalize_safety_result(result)


def test_safety_result_invalid_warning_severity_is_rejected():
    """SafetyResult with invalid warning severity is rejected."""
    result = SafetyResult(
        emergency=False,
        requires_human_review=False,
        warnings=[
            SafetyWarning.model_construct(code="X", severity="invalid", message="test")
        ],
        checked_items=[],
    )
    with pytest.raises(RuntimeError, match="must be one of"):
        _normalize_safety_result(result)


def test_safety_result_non_list_warnings_is_rejected():
    """SafetyResult model_construct with non-list warnings raises RuntimeError in adapter."""
    # Use model_construct to bypass Pydantic validation and inject bad data,
    # simulating a Safety Engine that returns a model instance with invalid internals.
    result = SafetyResult.model_construct(
        emergency=False,
        requires_human_review=False,
        warnings="not a list",
        checked_items=[],
        emergency_reason=None,
    )
    with pytest.raises(RuntimeError, match="'warnings' must be a list"):
        _normalize_safety_result(result)


# ---------------------------------------------------------------------------
# MedicationSafetyResult strict validation
# ---------------------------------------------------------------------------

def test_valid_medication_safety_result_dict_passes(monkeypatch):
    """Valid dict MedicationSafetyResult is accepted."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications", "allergies"],
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    normalized = check_medication_safety({"name": "Test"}, {}, [])
    assert normalized.is_duplicate is False


def test_valid_medication_safety_result_model_passes(monkeypatch):
    """Valid MedicationSafetyResult model instance is accepted."""
    from safety import engine as safety_engine

    result = MedicationSafetyResult(
        is_duplicate=False,
        requires_human_review=False,
        warnings=[],
        checked_items=["medications", "allergies"],
    )
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    normalized = check_medication_safety({"name": "Test"}, {}, [])
    assert normalized.is_duplicate is False


def test_medication_safety_result_model_construct_non_bool_duplicate_is_rejected(monkeypatch):
    """MedicationSafetyResult.model_construct with non-bool is_duplicate raises RuntimeError."""
    from safety import engine as safety_engine

    invalid = MedicationSafetyResult.model_construct(is_duplicate="yes")
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: invalid)
    with pytest.raises(RuntimeError, match="must be a strict boolean"):
        check_medication_safety({"name": "Test"}, {}, [])


def test_medication_safety_result_model_construct_invalid_duplicate_type(monkeypatch):
    """MedicationSafetyResult.model_construct with invalid duplicate_type raises RuntimeError."""
    from safety import engine as safety_engine

    invalid = MedicationSafetyResult.model_construct(
        is_duplicate=False,
        duplicate_type="maybe",
        warnings=[],
        checked_items=["medications", "allergies"],
    )
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: invalid)
    with pytest.raises(RuntimeError, match="duplicate_type"):
        check_medication_safety({"name": "Test"}, {}, [])


def test_medication_safety_result_non_list_warnings_is_rejected(monkeypatch):
    """MedicationSafetyResult with non-list warnings raises RuntimeError."""
    from safety import engine as safety_engine

    invalid = MedicationSafetyResult.model_construct(
        is_duplicate=False,
        requires_human_review=False,
        warnings="not a list",
        checked_items=["medications", "allergies"],
    )
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: invalid)
    with pytest.raises(RuntimeError, match="'warnings' must be a list"):
        check_medication_safety({"name": "Test"}, {}, [])


# ---------------------------------------------------------------------------
# SafetyWarning strict validation
# ---------------------------------------------------------------------------

def test_valid_safety_warning_dict_passes():
    """Valid dict SafetyWarning is accepted."""
    warning = {
        "code": "TEST_CODE",
        "severity": "warning",
        "message": "Test message",
    }
    validated = _validate_warning(warning, 0)
    assert validated.code == "TEST_CODE"
    assert validated.severity == "warning"


def test_valid_safety_warning_model_passes():
    """Valid SafetyWarning model instance is accepted."""
    warning = SafetyWarning(code="TEST_CODE", severity="high", message="Test message")
    validated = _validate_warning(warning, 0)
    assert validated.code == "TEST_CODE"


def test_safety_warning_model_construct_non_string_code_is_rejected():
    """SafetyWarning.model_construct with non-string code raises RuntimeError."""
    warning = SafetyWarning.model_construct(code=123, severity="high", message="test")
    with pytest.raises(RuntimeError, match="must be a non-empty string"):
        _validate_warning(warning, 0)


def test_safety_warning_model_construct_invalid_severity_is_rejected():
    """SafetyWarning.model_construct with invalid severity raises RuntimeError."""
    warning = SafetyWarning.model_construct(code="X", severity="critical_high", message="test")
    with pytest.raises(RuntimeError, match="must be one of"):
        _validate_warning(warning, 0)


def test_safety_warning_empty_message_is_rejected():
    """SafetyWarning with empty message raises RuntimeError."""
    warning = SafetyWarning.model_construct(code="X", severity="high", message="   ")
    with pytest.raises(RuntimeError, match="must be a non-empty string"):
        _validate_warning(warning, 0)


# ---------------------------------------------------------------------------
# Existing valid behavior unchanged
# ---------------------------------------------------------------------------

def test_medication_identity_case_insensitive():
    """Identity matching is case-insensitive for name."""
    candidate = {"name": "LISINOPRIL", "dosage": "10 MG", "route": "ORAL", "strength": "10 MG"}
    existing = {"id": "med-1", "name": "lisinopril", "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) == _medication_identity(existing)


def test_check_medication_safety_passthrough_valid_dict(monkeypatch):
    """Valid dict input to check_medication_safety passes through unchanged."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications", "allergies"],
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    normalized = check_medication_safety(
        {"name": "Aspirin", "dosage": "81 mg", "route": "oral", "strength": "81 mg"},
        {},
        [],
    )
    assert normalized.is_duplicate is False
    assert normalized.duplicate_type == "none"
    assert normalized.warnings == []
    assert normalized.checked_items == ["medications", "allergies"]


# ---------------------------------------------------------------------------
# Duplicate-type contradiction detection
# ---------------------------------------------------------------------------


def test_duplicate_type_contradiction_is_duplicate_true_but_type_none_rejected(monkeypatch):
    """is_duplicate=True with duplicate_type='none' contradicts derived type and must be rejected."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": True,
        "requires_human_review": True,
        "warnings": [
            {
                "code": "MED_EXACT_DUPLICATE",
                "severity": "warning",
                "message": "dup",
                "recommended_action": "review",
                "matched_item": "Test",
            }
        ],
        "checked_items": ["medications"],
        "duplicate_type": "none",  # contradicts is_duplicate=True
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    with pytest.raises(RuntimeError, match="contradicts"):
        check_medication_safety({"name": "Test"}, {}, [])


def test_duplicate_type_contradiction_is_duplicate_false_but_type_exact_rejected(monkeypatch):
    """is_duplicate=False with duplicate_type='exact' contradicts derived type and must be rejected."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications"],
        "duplicate_type": "exact",  # contradicts is_duplicate=False, no MED_EXACT_DUPLICATE warning
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    with pytest.raises(RuntimeError, match="contradicts"):
        check_medication_safety({"name": "Test"}, {}, [])


def test_duplicate_type_contradiction_ingredient_overlap_mismatch_rejected(monkeypatch):
    """is_duplicate=True with duplicate_type='ingredient_overlap' contradicts derived 'exact' type."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": True,
        "requires_human_review": True,
        "warnings": [
            {
                "code": "MED_EXACT_DUPLICATE",
                "severity": "warning",
                "message": "dup",
                "recommended_action": "review",
                "matched_item": "Test",
            }
        ],
        "checked_items": ["medications"],
        "duplicate_type": "ingredient_overlap",  # contradicts is_duplicate=True → derived type is "exact"
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    with pytest.raises(RuntimeError, match="contradicts"):
        check_medication_safety({"name": "Test"}, {}, [])


def test_duplicate_type_unknown_value_rejected(monkeypatch):
    """An unrecognised duplicate_type value must be rejected before the contradiction check."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications"],
        "duplicate_type": "UNKNOWN_VALUE",
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    with pytest.raises(RuntimeError, match="duplicate_type"):
        check_medication_safety({"name": "Test"}, {}, [])


def test_duplicate_type_consistent_exact_is_accepted(monkeypatch):
    """is_duplicate=True with duplicate_type='exact' is consistent and must be accepted."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": True,
        "requires_human_review": True,
        "warnings": [
            {
                "code": "MED_EXACT_DUPLICATE",
                "severity": "warning",
                "message": "dup",
                "recommended_action": "review",
                "matched_item": "Test",
            }
        ],
        "checked_items": ["medications"],
        "duplicate_type": "exact",  # consistent with is_duplicate=True
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    normalized = check_medication_safety({"name": "Test"}, {}, [])
    assert normalized.is_duplicate is True
    assert normalized.duplicate_type == "exact"


def test_duplicate_type_absent_does_not_raise(monkeypatch):
    """Absent duplicate_type (key missing entirely) is accepted; adapter derives 'none'."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications"],
        # no duplicate_type key
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    normalized = check_medication_safety({"name": "Test"}, {}, [])
    assert normalized.duplicate_type == "none"


def test_duplicate_type_none_value_does_not_raise(monkeypatch):
    """Explicit duplicate_type=None is treated as absent; adapter derives 'none' without contradicting."""
    from safety import engine as safety_engine

    result = {
        "is_duplicate": False,
        "requires_human_review": False,
        "warnings": [],
        "checked_items": ["medications"],
        "duplicate_type": None,
    }
    monkeypatch.setattr(safety_engine, "check_medication_entry", lambda **kwargs: result)
    normalized = check_medication_safety({"name": "Test"}, {}, [])
    assert normalized.duplicate_type == "none"


# ---------------------------------------------------------------------------
# Medication identity: malformed field protection
# ---------------------------------------------------------------------------


def test_normalize_text_none_returns_empty():
    """None must produce an empty string."""
    from backend.services.safety_integration import _normalize_text
    assert _normalize_text(None) == ""


def test_normalize_text_integer_returns_empty():
    """Integer must produce an empty string (not '0' or similar)."""
    from backend.services.safety_integration import _normalize_text
    assert _normalize_text(0) == ""
    assert _normalize_text(10) == ""


def test_normalize_text_boolean_returns_empty():
    """Boolean must produce an empty string (not 'true'/'false')."""
    from backend.services.safety_integration import _normalize_text
    assert _normalize_text(True) == ""
    assert _normalize_text(False) == ""


def test_normalize_text_list_returns_empty():
    """List must produce an empty string."""
    from backend.services.safety_integration import _normalize_text
    assert _normalize_text(["10 mg"]) == ""
    assert _normalize_text([]) == ""


def test_normalize_text_dict_returns_empty():
    """Dict must produce an empty string."""
    from backend.services.safety_integration import _normalize_text
    assert _normalize_text({"value": "10 mg"}) == ""


def test_normalize_text_valid_string_normalized():
    """Valid string must be lowercased and stripped."""
    from backend.services.safety_integration import _normalize_text
    assert _normalize_text("  Aspirin  ") == "aspirin"
    assert _normalize_text("ORAL") == "oral"
    assert _normalize_text("10 MG") == "10 mg"


def test_identity_integer_dosage_treated_as_missing():
    """Integer dosage must not create a valid identity key (would match '0'/'10' as str otherwise)."""
    candidate = {"name": "Test", "dosage": 0, "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is None


def test_identity_boolean_dosage_treated_as_missing():
    """Boolean dosage must not create a valid identity key."""
    candidate = {"name": "Test", "dosage": False, "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is None


def test_identity_list_dosage_treated_as_missing():
    """List dosage must not create a valid identity key."""
    candidate = {"name": "Test", "dosage": ["10 mg"], "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is None


def test_identity_none_dosage_treated_as_missing():
    """Explicit None dosage must return None identity."""
    candidate = {"name": "Test", "dosage": None, "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is None


def test_identity_whitespace_only_treated_as_missing():
    """Whitespace-only string identity field must return None (strips to empty)."""
    candidate = {"name": "Test", "dosage": "   ", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is None


def test_identity_integer_name_treated_as_missing():
    """Integer name must not create a valid identity key."""
    candidate = {"name": 123, "dosage": "10 mg", "route": "oral", "strength": "10 mg"}
    assert _medication_identity(candidate) is None


def test_identity_malformed_cannot_false_match_valid():
    """A malformed field (int) must NOT produce the same identity as the equivalent string."""
    malformed = {"name": "Test", "dosage": 10, "route": "oral", "strength": "10 mg"}
    valid = {"name": "Test", "dosage": "10", "route": "oral", "strength": "10 mg"}
    # malformed returns None, valid returns a tuple — they must not be equal
    assert _medication_identity(malformed) is None
    assert _medication_identity(valid) is not None
    assert _medication_identity(malformed) != _medication_identity(valid)


def test_identity_all_valid_fields_case_insensitive():
    """Valid string fields with different cases must still match (case-insensitive)."""
    lower = {"name": "aspirin", "dosage": "81 mg", "route": "oral", "strength": "81 mg"}
    upper = {"name": "ASPIRIN", "dosage": "81 MG", "route": "ORAL", "strength": "81 MG"}
    assert _medication_identity(lower) is not None
    assert _medication_identity(lower) == _medication_identity(upper)
