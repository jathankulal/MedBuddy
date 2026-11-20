"""Safety engine integration for the MedBuddy backend.

Developer 2 owns the safety engine (`safety/` package). This module serves as
the centralized integration adapter. All safety failures fail closed (raising
RuntimeError). Gemini and medication persistence must never proceed when safety
checks fail.
"""

from typing import Any, Dict, List, Optional, Tuple

from backend.schemas import MedicationSafetyResult, SafetyResult, SafetyWarning

VALID_SEVERITIES = {"critical", "high", "warning", "info"}

MEDICATION_IDENTITY_FIELDS = ("name", "dosage", "route", "strength")


def _strict_bool(value: Any, field_name: str) -> bool:
    """Validate that a value is strictly of type bool.

    Prevents truthy/falsy coercion (e.g. bool("false") -> True).
    """
    if type(value) is bool:
        return value
    raise RuntimeError(
        f"Invalid safety engine output: '{field_name}' must be a strict boolean, got {type(value).__name__}: {value!r}"
    )


def _normalize_text(value: Any) -> str:
    """Normalize a text value for comparison.

    Returns empty string for any non-string value (including None, int, bool,
    list, dict) to prevent false identity matches from silent type coercion.
    Only genuine string values are lowercased and stripped.
    """
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _medication_identity(medication: dict) -> Optional[Tuple[str, str, str, str]]:
    """Return the normalized identity tuple (name, dosage, route, strength).

    Returns None if any identity field is missing or empty, so callers can
    distinguish "no match" from "incomplete identity".
    """
    values = tuple(
        _normalize_text(medication.get(field, "")) for field in MEDICATION_IDENTITY_FIELDS
    )
    if any(not value for value in values):
        return None
    return values


def _validate_warning(warning_data: Any, index: int) -> SafetyWarning:
    """Validate and convert raw warning output or SafetyWarning instance.

    Both model instances and dicts are strictly validated for code, severity,
    message, matched_item, and recommended_action.
    """
    missing = object()
    if isinstance(warning_data, SafetyWarning):
        code = getattr(warning_data, "code", missing)
        severity = getattr(warning_data, "severity", missing)
        message = getattr(warning_data, "message", missing)
        action = getattr(warning_data, "recommended_action", None)
        matched_item = getattr(warning_data, "matched_item", None)
    elif isinstance(warning_data, dict):
        code = warning_data.get("code")
        severity = warning_data.get("severity")
        message = warning_data.get("message")
        action = warning_data.get("recommended_action")
        matched_item = warning_data.get("matched_item")
    else:
        raise RuntimeError(
            f"Invalid safety engine output: warning[{index}] must be a dict or SafetyWarning, got {type(warning_data).__name__}"
        )

    for field_name, val in (("code", code), ("severity", severity), ("message", message)):
        if not isinstance(val, str) or not val.strip():
            raise RuntimeError(
                f"Invalid safety engine output: warning[{index}].{field_name} must be a non-empty string"
            )

    if severity not in VALID_SEVERITIES:
        raise RuntimeError(
            f"Invalid safety engine output: warning[{index}].severity '{severity}' must be one of {sorted(VALID_SEVERITIES)}"
        )

    if matched_item is not None and not isinstance(matched_item, str):
        raise RuntimeError(f"Invalid safety engine output: warning[{index}].matched_item must be a string or None")

    if action is not None and not isinstance(action, str):
        raise RuntimeError(f"Invalid safety engine output: warning[{index}].recommended_action must be a string or None")

    return SafetyWarning(
        code=code,
        severity=severity,
        message=message,
        recommended_action=action,
        matched_item=matched_item,
    )


def _load_profile(data_dir: str) -> Optional[dict]:
    from backend.database import read_json

    return read_json(data_dir, "profile.json", default=None)


def _load_medications(data_dir: str) -> List[dict]:
    from backend.database import read_json

    return read_json(data_dir, "medications.json", default=[]) or []


def _load_episodes(data_dir: str) -> List[dict]:
    from backend.database import read_json

    return read_json(data_dir, "episodes.json", default=[]) or []


def _normalize_safety_result(result: Any) -> SafetyResult:
    """Normalize raw safety engine output to SafetyResult with strict validation.

    Both model instances and dicts are strictly validated.
    """
    missing = object()
    if isinstance(result, SafetyResult):
        raw_emergency = getattr(result, "emergency", missing)
        raw_review = getattr(result, "requires_human_review", missing)
        emergency_reason = getattr(result, "emergency_reason", None)
        raw_warnings = getattr(result, "warnings", missing)
        raw_checked = getattr(result, "checked_items", missing)
    elif isinstance(result, dict):
        # Map is_emergency -> emergency, supporting both keys
        if "is_emergency" in result:
            raw_emergency = result["is_emergency"]
        elif "emergency" in result:
            raw_emergency = result["emergency"]
        else:
            raise RuntimeError("Invalid safety engine output: missing 'is_emergency' / 'emergency' field")

        if "requires_human_review" not in result:
            raise RuntimeError("Invalid safety engine output: missing 'requires_human_review' field")
        raw_review = result["requires_human_review"]

        emergency_reason = result.get("emergency_reason")
        raw_warnings = result.get("warnings")
        raw_checked = result.get("checked_items")
    else:
        raise RuntimeError(f"Invalid safety engine output: expected dict or SafetyResult, got {type(result).__name__}")

    emergency = _strict_bool(raw_emergency, "is_emergency")
    requires_human_review = _strict_bool(raw_review, "requires_human_review")

    if emergency_reason is not None and not isinstance(emergency_reason, str):
        raise RuntimeError("Invalid safety engine output: 'emergency_reason' must be a string or None")

    if not isinstance(raw_warnings, list):
        raise RuntimeError(f"Invalid safety engine output: 'warnings' must be a list, got {type(raw_warnings).__name__}")

    warnings = [_validate_warning(w, i) for i, w in enumerate(raw_warnings)]

    if not isinstance(raw_checked, list):
        raise RuntimeError(f"Invalid safety engine output: 'checked_items' must be a list, got {type(raw_checked).__name__}")
    for item in raw_checked:
        if not isinstance(item, str):
            raise RuntimeError(f"Invalid safety engine output: 'checked_items' elements must be strings, got {type(item).__name__}")

    return SafetyResult(
        emergency=emergency,
        emergency_reason=emergency_reason,
        warnings=warnings,
        requires_human_review=requires_human_review,
        checked_items=list(raw_checked),
    )


def run_safety_assessment(
    data_dir: str,
    user_message: str,
) -> SafetyResult:
    """Call Developer 2's safety engine (assess_safety) before Gemini.

    Returns a normalized SafetyResult. Raises RuntimeError if the safety engine is
    unavailable, crashes, or returns invalid output (fail closed).

    Emergency signals are checked first on user_message before personal JSON records
    are loaded, ensuring emergency bypass is never blocked by malformed files on disk.
    """
    try:
        from safety.engine import assess_safety  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Safety engine is not integrated") from exc

    if not isinstance(user_message, str):
        raise RuntimeError("Invalid input: 'user_message' must be a string")

    # Step 1: Emergency pre-check before reading/validating personal records
    try:
        pre_check = assess_safety(
            user_message=user_message,
            health_profile=None,
            medications=[],
            episodes=[],
        )
    except Exception as exc:
        raise RuntimeError(f"Safety engine call failed: {exc}") from exc

    normalized_pre = _normalize_safety_result(pre_check)
    if normalized_pre.emergency:
        return normalized_pre

    # Step 2: Full assessment with personal health context
    try:
        profile = _load_profile(data_dir)
        medications = _load_medications(data_dir)
        episodes = _load_episodes(data_dir)
    except Exception as exc:
        raise RuntimeError(f"Failed to load patient records for safety check: {exc}") from exc

    try:
        result = assess_safety(
            user_message=user_message,
            health_profile=profile,
            medications=medications,
            episodes=episodes,
        )
    except Exception as exc:
        raise RuntimeError(f"Safety engine call failed: {exc}") from exc

    return _normalize_safety_result(result)


def check_medication_safety(
    candidate_medication: dict,
    health_profile: Optional[dict],
    existing_medications: List[dict],
) -> MedicationSafetyResult:
    """Call Developer 2's medication safety check with fail-closed validation.

    Returns a normalized MedicationSafetyResult. Raises RuntimeError if the safety
    engine is unavailable, crashes, or returns invalid output.

    Both model instances and dicts are strictly validated.
    """
    try:
        from safety.engine import check_medication_entry  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Safety engine is not integrated") from exc

    if not isinstance(candidate_medication, dict):
        raise RuntimeError("Invalid candidate medication: expected dict")
    if not isinstance(existing_medications, list):
        raise RuntimeError("Invalid existing medications: expected list")

    try:
        raw_result = check_medication_entry(
            candidate_medication=candidate_medication,
            health_profile=health_profile,
            existing_medications=existing_medications,
        )
    except Exception as exc:
        raise RuntimeError(f"Safety engine medication check failed: {exc}") from exc

    missing = object()
    if isinstance(raw_result, MedicationSafetyResult):
        raw_is_duplicate = getattr(raw_result, "is_duplicate", missing)
        raw_review = getattr(raw_result, "requires_human_review", missing)
        raw_warnings = getattr(raw_result, "warnings", missing)
        raw_matched_item = getattr(raw_result, "matched_item", None)
        raw_checked = getattr(raw_result, "checked_items", missing)
        raw_dup_type = getattr(raw_result, "duplicate_type", None)
        raw_existing_id = getattr(raw_result, "existing_medication_id", None)
    elif isinstance(raw_result, dict):
        if "is_duplicate" not in raw_result:
            raise RuntimeError("Invalid safety engine output: missing 'is_duplicate' field")
        raw_is_duplicate = raw_result["is_duplicate"]

        if "requires_human_review" not in raw_result:
            raise RuntimeError("Invalid safety engine output: missing 'requires_human_review' field")
        raw_review = raw_result["requires_human_review"]

        if "warnings" not in raw_result:
            raise RuntimeError("Invalid safety engine output: missing 'warnings' field")
        raw_warnings = raw_result["warnings"]
        raw_matched_item = raw_result.get("matched_item")
        raw_checked = raw_result["checked_items"] if "checked_items" in raw_result else missing
        raw_dup_type = raw_result.get("duplicate_type")
        raw_existing_id = raw_result.get("existing_medication_id")
    else:
        raise RuntimeError(f"Invalid safety engine output: expected dict or MedicationSafetyResult, got {type(raw_result).__name__}")

    is_duplicate = _strict_bool(raw_is_duplicate, "is_duplicate")
    requires_human_review = _strict_bool(raw_review, "requires_human_review")

    if not isinstance(raw_warnings, list):
        raise RuntimeError(f"Invalid safety engine output: 'warnings' must be a list, got {type(raw_warnings).__name__}")

    warnings: List[SafetyWarning] = [_validate_warning(w, i) for i, w in enumerate(raw_warnings)]

    if raw_matched_item is not None and not isinstance(raw_matched_item, str):
        raise RuntimeError("Invalid safety engine output: 'matched_item' must be a string or None")
    if raw_existing_id is not None and not isinstance(raw_existing_id, str):
        raise RuntimeError("Invalid safety engine output: 'existing_medication_id' must be a string or None")

    # Derive matched_item and check for ingredient overlap
    derived_matched_item: Optional[str] = raw_matched_item
    has_ingredient_overlap = False
    for w in warnings:
        if w.code == "MED_EXACT_DUPLICATE" and w.matched_item:
            derived_matched_item = w.matched_item
        elif w.code == "MED_INGREDIENT_OVERLAP":
            has_ingredient_overlap = True

    if is_duplicate:
        duplicate_type = "exact"
    elif has_ingredient_overlap:
        duplicate_type = "ingredient_overlap"
    else:
        duplicate_type = "none"

    if raw_dup_type is not None:
        if raw_dup_type not in ("exact", "ingredient_overlap", "none"):
            raise RuntimeError(
                f"Invalid safety engine output: 'duplicate_type' must be one of "
                f"'exact', 'ingredient_overlap', 'none'; got '{raw_dup_type}'"
            )
        if raw_dup_type != duplicate_type:
            raise RuntimeError(
                f"Invalid safety engine output: 'duplicate_type' value '{raw_dup_type}' "
                f"contradicts is_duplicate={is_duplicate} and warning codes "
                f"(adapter derived type: '{duplicate_type}')"
            )

    # Identify existing medication ID only when full medication identity matches:
    # name, dosage, route, and strength must all match exactly.
    existing_medication_id: Optional[str] = None
    if is_duplicate:
        cand_key = _medication_identity(candidate_medication)
        if cand_key is not None:
            for existing in existing_medications:
                if _medication_identity(existing) == cand_key:
                    medication_id = existing.get("id")
                    if isinstance(medication_id, str) and medication_id:
                        existing_medication_id = medication_id
                        break

    checked_items = ["medications", "allergies"]
    if raw_checked is not missing:
        if not isinstance(raw_checked, list):
            raise RuntimeError("Invalid safety engine output: 'checked_items' must be a list")
        for item in raw_checked:
            if not isinstance(item, str):
                raise RuntimeError("Invalid safety engine output: 'checked_items' elements must be strings")
        checked_items = list(raw_checked)

    return MedicationSafetyResult(
        is_duplicate=is_duplicate,
        duplicate_type=duplicate_type,
        warnings=warnings,
        matched_item=derived_matched_item,
        existing_medication_id=existing_medication_id,
        checked_items=checked_items,
        requires_human_review=requires_human_review,
    )
