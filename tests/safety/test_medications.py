"""Tests for exact duplicates and active-ingredient overlap."""

from safety.engine import check_medication_entry


def _medication(**overrides):
    medication = {
        "name": "Example medication",
        "active_ingredients": ["compound-x"],
        "strength": "10 mg",
        "route": "oral",
        "dosage": "one unit",
    }
    medication.update(overrides)
    return medication


def test_exact_duplicate_medication():
    result = check_medication_entry(
        _medication(),
        {},
        [_medication(name="  example MEDICATION  ")],
    )

    assert result["is_duplicate"] is True
    assert any(warning["code"] == "MED_EXACT_DUPLICATE" for warning in result["warnings"])


def test_non_duplicate_medication():
    result = check_medication_entry(
        _medication(),
        {},
        [_medication(name="Different example medication")],
    )

    assert result["is_duplicate"] is False
    assert not any(
        warning["code"] == "MED_EXACT_DUPLICATE" for warning in result["warnings"]
    )


def test_ingredient_overlap_is_not_an_exact_duplicate():
    result = check_medication_entry(
        _medication(name="Example brand B"),
        {},
        [_medication(name="Example brand A")],
    )

    assert result["is_duplicate"] is False
    assert any(
        warning["code"] == "MED_INGREDIENT_OVERLAP"
        for warning in result["warnings"]
    )


def test_missing_ingredient_information_requires_review():
    result = check_medication_entry(
        _medication(name="Example brand B", active_ingredients=None),
        {},
        [_medication(name="Example brand A", active_ingredients=None)],
    )

    assert result["is_duplicate"] is False
    assert any(
        warning["code"] == "MED_INGREDIENTS_UNAVAILABLE"
        for warning in result["warnings"]
    )
    assert result["requires_human_review"] is True


def test_missing_ingredients_without_existing_medications_requires_review():
    result = check_medication_entry(
        {"name": "Example medication"},
        {"allergies": []},
        [],
    )

    assert result["is_duplicate"] is False
    assert any(
        warning["code"] == "MED_INGREDIENTS_UNAVAILABLE"
        for warning in result["warnings"]
    )
    assert result["requires_human_review"] is True


def test_incomplete_identity_does_not_claim_exact_duplicate():
    result = check_medication_entry(
        {"name": "Example medication"},
        {},
        [{"name": "Example medication"}],
    )

    assert result["is_duplicate"] is False
    assert any(
        warning["code"] == "MED_DUPLICATE_CHECK_INCOMPLETE"
        for warning in result["warnings"]
    )


def test_medication_without_required_name_is_rejected():
    try:
        check_medication_entry({}, {}, [])
    except ValueError as error:
        assert "'name'" in str(error)
    else:
        raise AssertionError("A medication without a name must be rejected")
