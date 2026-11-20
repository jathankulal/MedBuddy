"""Exact-duplicate and active-ingredient overlap checks."""

from typing import Any

from safety.rules.allergies import (
    allergy_information_available,
    allergy_information_warning,
    find_allergy_matches,
    normalize_text,
)

IDENTITY_FIELDS = ("name", "dosage", "route", "strength")


def _validate_medication(
    medication: dict[str, Any],
    label: str,
) -> None:
    if not isinstance(medication, dict):
        raise TypeError(f"{label} must be a dict")
    name = medication.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{label} must include a non-empty 'name'")

    for field in ("generic_name", "dosage", "route", "strength"):
        value = medication.get(field)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{label}['{field}'] must be a string")

    ingredients = medication.get("active_ingredients")
    if ingredients is not None:
        if not isinstance(ingredients, list):
            raise TypeError(f"{label}['active_ingredients'] must be a list")
        for index, ingredient in enumerate(ingredients):
            if not isinstance(ingredient, str):
                raise TypeError(
                    f"{label}['active_ingredients'][{index}] must be a string"
                )


def _identity_key(medication: dict[str, Any]) -> tuple[str, ...] | None:
    values = tuple(
        normalize_text(medication.get(field, "") or "")
        for field in IDENTITY_FIELDS
    )
    if any(not value for value in values):
        return None
    return values


def _ingredients(medication: dict[str, Any]) -> set[str]:
    raw_ingredients = medication.get("active_ingredients")
    if not raw_ingredients:
        return set()
    return {
        normalized
        for item in raw_ingredients
        if (normalized := normalize_text(item))
    }


def _incomplete_identity_warning(matched_name: str) -> dict[str, str]:
    return {
        "code": "MED_DUPLICATE_CHECK_INCOMPLETE",
        "severity": "info",
        "message": (
            "An exact duplicate could not be determined because one or more "
            "identity details are missing."
        ),
        "recommended_action": (
            "Review the medication details with a qualified healthcare "
            "professional or pharmacist."
        ),
        "matched_item": matched_name,
    }


def _missing_ingredients_warning(matched_name: str) -> dict[str, str]:
    return {
        "code": "MED_INGREDIENTS_UNAVAILABLE",
        "severity": "info",
        "message": (
            "Ingredient overlap could not be assessed because ingredient "
            "details are missing."
        ),
        "recommended_action": (
            "Ask a qualified healthcare professional or pharmacist to review "
            "the medication list."
        ),
        "matched_item": matched_name,
    }


def check_medication(
    candidate_medication: dict[str, Any],
    health_profile: dict[str, Any] | None,
    existing_medications: list[dict[str, Any]],
    include_allergy_warnings: bool = True,
) -> dict[str, Any]:
    """Return deterministic medication checks without claiming interactions."""
    _validate_medication(candidate_medication, "candidate_medication")
    if not isinstance(existing_medications, list):
        raise TypeError("existing_medications must be a list of dicts")
    for index, existing in enumerate(existing_medications):
        _validate_medication(existing, f"existing_medications[{index}]")

    warnings = []
    if include_allergy_warnings:
        warnings.extend(find_allergy_matches(health_profile, candidate_medication))
        if not allergy_information_available(health_profile):
            warnings.append(allergy_information_warning())

    candidate_identity = _identity_key(candidate_medication)
    candidate_name = candidate_medication["name"].strip()
    candidate_ingredients = _ingredients(candidate_medication)
    is_duplicate = False

    for existing in existing_medications:
        existing_identity = _identity_key(existing)
        existing_name = existing["name"].strip()

        if (
            candidate_identity is not None
            and existing_identity is not None
            and candidate_identity == existing_identity
        ):
            is_duplicate = True
            warnings.append(
                {
                    "code": "MED_EXACT_DUPLICATE",
                    "severity": "warning",
                    "message": (
                        "A medication record with the same name, dosage, "
                        "route, and strength already exists."
                    ),
                    "recommended_action": (
                        "Review the existing medication record before adding "
                        "another entry."
                    ),
                    "matched_item": existing_name,
                }
            )
        elif (
            candidate_identity is None
            or existing_identity is None
        ) and normalize_text(candidate_name) == normalize_text(existing_name):
            warnings.append(_incomplete_identity_warning(existing_name))

        existing_ingredients = _ingredients(existing)
        if candidate_ingredients and existing_ingredients:
            for ingredient in sorted(candidate_ingredients & existing_ingredients):
                warnings.append(
                    {
                        "code": "MED_INGREDIENT_OVERLAP",
                        "severity": "warning",
                        "message": (
                            "The medication records share an active ingredient. "
                            "This check does not assess drug interactions."
                        ),
                        "recommended_action": (
                            "Ask a qualified healthcare professional or "
                            "pharmacist to review the medication list."
                        ),
                        "matched_item": ingredient,
                    }
                )

    ingredients_incomplete = not candidate_ingredients or any(
        not _ingredients(existing) for existing in existing_medications
    )
    if ingredients_incomplete:
        warnings.append(_missing_ingredients_warning(candidate_name))

    return {
        "is_duplicate": is_duplicate,
        "warnings": warnings,
        "requires_human_review": bool(warnings),
    }
