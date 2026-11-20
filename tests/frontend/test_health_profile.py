"""Tests for the session-only health profile form."""

from datetime import date, timedelta

import pytest
from streamlit.testing.v1 import AppTest

PROFILE_PAGE = r"..\..\frontend\pages\health_profile.py"


def _submit_profile(app):
    app.button[0].click().run()
    assert not app.exception, [str(error.value) for error in app.exception]


def test_profile_can_be_saved_and_updated_in_session():
    app = AppTest.from_file(PROFILE_PAGE).run()
    assert not app.exception, [str(error.value) for error in app.exception]

    app.text_input(key="health_profile_form_full_name").set_value("Alex Morgan")
    app.text_input(key="health_profile_form_date_of_birth").set_value("1990-05-12")
    app.text_input(key="health_profile_form_gender").set_value("Non-binary")
    app.text_input(key="health_profile_form_preferred_language").set_value("English")
    app.text_area(key="health_profile_form_conditions").set_value(
        "Condition one\nCondition two"
    )
    app.text_area(key="health_profile_form_allergies").set_value(
        "Allergy one\nAllergy two"
    )
    app.text_input(key="health_profile_form_emergency_contact_name").set_value(
        "Taylor Morgan"
    )
    app.text_input(key="health_profile_form_emergency_contact_phone").set_value(
        "+1 555 010 1234"
    )
    app.text_area(key="health_profile_form_accessibility_notes").set_value(
        "Prefers written instructions."
    )
    _submit_profile(app)

    saved = app.session_state["health_profile_demo"]
    assert saved["full_name"] == "Alex Morgan"
    assert saved["date_of_birth"] == date(1990, 5, 12)
    assert saved["gender"] == "Non-binary"
    assert saved["preferred_language"] == "English"
    assert saved["conditions"] == ["Condition one", "Condition two"]
    assert saved["allergies"] == ["Allergy one", "Allergy two"]
    assert saved["emergency_contact_name"] == "Taylor Morgan"
    assert saved["emergency_contact_phone"] == "+1 555 010 1234"
    assert saved["accessibility_notes"] == "Prefers written instructions."
    assert "not permanently saved" in app.success[0].value

    app.text_input(key="health_profile_form_full_name").set_value("Alex Updated")
    _submit_profile(app)
    assert app.session_state["health_profile_demo"]["full_name"] == "Alex Updated"


def test_profile_requires_name_and_valid_contact_phone():
    app = AppTest.from_file(PROFILE_PAGE).run()
    app.text_input(key="health_profile_form_emergency_contact_phone").set_value(
        "123"
    )
    _submit_profile(app)

    assert app.session_state["health_profile_demo_saved"] is False
    assert len(app.error) == 1
    assert "full name" in app.error[0].value
    assert "7 to 15 digits" in app.error[0].value


@pytest.mark.parametrize(
    "birth_date",
    [
        "2020/01/01",
        "2021-02-29",
        (date.today() + timedelta(days=1)).isoformat(),
    ],
    ids=["invalid-format", "invalid-calendar-date", "future-date"],
)
def test_profile_rejects_invalid_date_of_birth(birth_date):
    app = AppTest.from_file(PROFILE_PAGE).run()
    app.text_input(key="health_profile_form_full_name").set_value("Alex Morgan")
    app.text_input(key="health_profile_form_date_of_birth").set_value(birth_date)
    _submit_profile(app)

    assert app.session_state["health_profile_demo_saved"] is False
    assert "date of birth" in app.error[0].value.casefold()
