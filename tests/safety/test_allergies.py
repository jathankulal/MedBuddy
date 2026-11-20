"""Tests for allergy-to-medication matching."""

from safety.engine import check_medication_entry


def test_allergy_match_in_available_ingredient():
    result = check_medication_entry(
        {"name": "Example product", "active_ingredients": ["Peanut oil"]},
        {"allergies": ["peanut"]},
        [],
    )

    assert result["is_duplicate"] is False
    assert result["warnings"][0]["code"] == "MED_ALLERGY_POTENTIAL_MATCH"
    assert result["warnings"][0]["matched_item"] == "peanut"
    assert result["requires_human_review"] is True


def test_no_allergy_match_is_not_reported_as_proof_of_safety():
    result = check_medication_entry(
        {"name": "Example product", "active_ingredients": ["compound-x"]},
        {"allergies": ["peanut"]},
        [],
    )

    assert result["warnings"] == []
    assert "is_safe" not in result


def test_medication_entry_flags_unavailable_allergy_information():
    result = check_medication_entry(
        {"name": "Example product", "active_ingredients": ["compound-x"]},
        None,
        [],
    )

    assert result["is_duplicate"] is False
    assert result["requires_human_review"] is True
    assert result["warnings"][0]["code"] == "MED_ALLERGY_INFO_UNAVAILABLE"


def test_empty_allergy_list_does_not_mean_allergy_information_is_unavailable():
    result = check_medication_entry(
        {"name": "Example product", "active_ingredients": ["compound-x"]},
        {"allergies": []},
        [],
    )

    assert result["warnings"] == []
    assert result["requires_human_review"] is False
