"""Tests for the public safety-engine interface and input validation."""

import pytest

from safety.engine import assess_safety, check_medication_entry


def test_empty_profile_and_medication_lists_return_empty_assessment():
    result = assess_safety("", {"allergies": []}, [], [])

    assert result == {
        "is_emergency": False,
        "emergency_reason": None,
        "warnings": [],
        "requires_human_review": False,
        "checked_items": ["allergies", "medications", "emergency_signals"],
    }


@pytest.mark.parametrize(
    "profile",
    [None, {}, {"allergies": None}],
    ids=["missing-profile", "missing-allergies-field", "allergies-none"],
)
def test_unavailable_allergy_information_requires_review(profile):
    result = assess_safety("No configured warning signs.", profile, [], [])

    assert result["is_emergency"] is False
    assert result["requires_human_review"] is True
    assert result["warnings"] == [
        {
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
    ]


def test_explicit_empty_allergy_list_is_available_information():
    result = assess_safety(
        "No configured warning signs.",
        {"allergies": []},
        [],
        [],
    )

    assert result["warnings"] == []
    assert result["requires_human_review"] is False


@pytest.mark.parametrize(
    ("medications", "episodes"),
    [
        ([{"name": None}], []),
        ([], [None]),
    ],
    ids=["invalid-medication", "invalid-episode"],
)
def test_emergency_is_returned_before_validating_other_records(
    medications, episodes
):
    result = assess_safety(
        "I am having chest pain.",
        {},
        medications,
        episodes,
    )

    assert result["is_emergency"] is True
    assert result["warnings"][0]["code"] == "EMERGENCY_SYMPTOMS"
    assert result["requires_human_review"] is True
    assert result["checked_items"] == ["emergency_signals"]


@pytest.mark.parametrize(
    ("args", "error"),
    [
        ((None, {}, [], []), TypeError),
        (("A message", [], [], []), TypeError),
        (("A message", {}, [{}], None), TypeError),
        (("A message", {"allergies": "peanut"}, [], []), TypeError),
        (
            (
                "A message",
                {"allergies": [None]},
                [{"name": "Example medication"}],
                [],
            ),
            TypeError,
        ),
    ],
)
def test_invalid_or_incomplete_assessment_input_raises(args, error):
    with pytest.raises(error):
        assess_safety(*args)


def test_invalid_ingredient_input_raises():
    with pytest.raises(TypeError):
        check_medication_entry(
            {"name": "Example medication", "active_ingredients": "compound-x"},
            {},
            [],
        )
