"""Deterministic matching of supplied allergies to medication details."""

import re
import unicodedata
from typing import Any


def normalize_text(value: str) -> str:
    """Normalize case, Unicode form, punctuation, and whitespace for matching."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))


def get_profile_allergies(
    health_profile: dict[str, Any] | None,
) -> list[str]:
    if health_profile is None:
        return []
    allergies = health_profile.get("allergies", [])
    if allergies is None:
        return []
    if not isinstance(allergies, list):
        raise TypeError("health_profile['allergies'] must be a list of strings")
    for index, allergy in enumerate(allergies):
        if not isinstance(allergy, str):
            raise TypeError(
                f"health_profile['allergies'][{index}] must be a string"
            )
    return allergies


def allergy_information_available(
    health_profile: dict[str, Any] | None,
) -> bool:
    return (
        health_profile is not None
        and "allergies" in health_profile
        and health_profile["allergies"] is not None
    )


def allergy_information_warning() -> dict[str, str]:
    return {
        "code": "MED_ALLERGY_INFO_UNAVAILABLE",
        "severity": "info",
        "message": (
            "Allergy information is unavailable, so allergy matching "
            "could not be completed."
        ),
        "recommended_action": (
            "Add known allergies to the health profile or ask a qualified "
            "healthcare professional or pharmacist to review."
        ),
        "matched_item": "allergy information",
    }


def _medication_terms(medication: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for field in ("name", "generic_name"):
        value = medication.get(field)
        if value is not None:
            if not isinstance(value, str):
                raise TypeError(f"medication['{field}'] must be a string")
            terms.append(value)

    ingredients = medication.get("active_ingredients")
    if ingredients is not None:
        if not isinstance(ingredients, list):
            raise TypeError("medication['active_ingredients'] must be a list")
        for index, ingredient in enumerate(ingredients):
            if not isinstance(ingredient, str):
                raise TypeError(
                    f"medication['active_ingredients'][{index}] must be a string"
                )
            terms.append(ingredient)
    return terms


def find_allergy_matches(
    health_profile: dict[str, Any] | None,
    medication: dict[str, Any],
) -> list[dict[str, str]]:
    """Return potential allergy matches in medication names or ingredients."""
    allergies = get_profile_allergies(health_profile)
    terms = [normalize_text(term) for term in _medication_terms(medication)]
    warnings = []
    seen: set[str] = set()

    for allergy in allergies:
        normalized_allergy = normalize_text(allergy)
        if not normalized_allergy or normalized_allergy in seen:
            continue
        allergy_phrase = f" {normalized_allergy} "
        if any(allergy_phrase in f" {term} " for term in terms):
            seen.add(normalized_allergy)
            warnings.append(
                {
                    "code": "MED_ALLERGY_POTENTIAL_MATCH",
                    "severity": "high",
                    "message": (
                        f"The medication information may match the recorded "
                        f"allergy '{allergy}'."
                    ),
                    "recommended_action": (
                        "Consult a qualified healthcare professional or "
                        "pharmacist before relying on this medication entry."
                    ),
                    "matched_item": allergy,
                }
            )
    return warnings
