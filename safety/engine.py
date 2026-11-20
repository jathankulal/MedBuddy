"""Public safety-engine functions used by the backend integration."""

from typing import Any

from safety.rules.allergies import (
    allergy_information_available,
    allergy_information_warning,
    find_allergy_matches,
    get_profile_allergies,
)
from safety.rules.emergency import detect_emergency_signals
from safety.rules.medications import check_medication

CHECKED_ITEMS = ["allergies", "medications", "emergency_signals"]


def _validate_profile(health_profile: dict[str, Any] | None) -> None:
    if health_profile is not None and not isinstance(health_profile, dict):
        raise TypeError("health_profile must be a dict or None")
    get_profile_allergies(health_profile)


def _validate_record_list(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise TypeError(f"{name} must be a list of dicts")
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise TypeError(f"{name}[{index}] must be a dict")
    return value


def assess_safety(
    user_message: str,
    health_profile: dict[str, Any] | None,
    medications: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assess emergency signals, known allergy matches, and medication overlap.

    This function reports configured text signals and supplied-data matches;
    it does not diagnose, assess drug interactions, or establish that anything
    is safe.
    """
    if not isinstance(user_message, str):
        raise TypeError("user_message must be a string")

    emergency_signals = detect_emergency_signals(user_message)
    if emergency_signals:
        signal_text = ", ".join(emergency_signals)
        emergency_reason = (
            "The message mentions configured emergency warning sign(s): "
            f"{signal_text}. This is not a diagnosis."
        )
        return {
            "is_emergency": True,
            "emergency_reason": emergency_reason,
            "warnings": [
                {
                    "code": "EMERGENCY_SYMPTOMS",
                    "severity": "critical",
                    "message": (
                        "The message mentions a configured emergency warning "
                        "sign. This system cannot determine the cause."
                    ),
                    "recommended_action": (
                        "Seek immediate medical attention or contact local "
                        "emergency services."
                    ),
                    "matched_item": signal_text,
                }
            ],
            "requires_human_review": True,
            "checked_items": ["emergency_signals"],
        }

    _validate_profile(health_profile)
    medication_records = _validate_record_list(medications, "medications")
    _validate_record_list(episodes, "episodes")

    warnings: list[dict[str, str]] = []
    if not allergy_information_available(health_profile):
        warnings.append(allergy_information_warning())

    for medication in medication_records:
        allergy_warnings = find_allergy_matches(health_profile, medication)
        warnings.extend(allergy_warnings)

    for index, medication in enumerate(medication_records):
        result = check_medication(
            medication,
            health_profile,
            medication_records[:index],
            include_allergy_warnings=False,
        )
        warnings.extend(result["warnings"])

    return {
        "is_emergency": False,
        "emergency_reason": None,
        "warnings": warnings,
        "requires_human_review": bool(warnings),
        "checked_items": CHECKED_ITEMS.copy(),
    }


def check_medication_entry(
    candidate_medication: dict[str, Any],
    health_profile: dict[str, Any] | None,
    existing_medications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check a medication entry for allergy matches and medication overlap.

    ``is_duplicate`` is true only when all documented medication identity
    fields match an existing record. Ingredient overlap is reported separately
    and never sets ``is_duplicate``.
    """
    _validate_profile(health_profile)
    existing_records = _validate_record_list(
        existing_medications, "existing_medications"
    )
    result = check_medication(
        candidate_medication, health_profile, existing_records
    )
    return {
        "is_duplicate": result["is_duplicate"],
        "warnings": result["warnings"],
        "requires_human_review": result["requires_human_review"],
    }
