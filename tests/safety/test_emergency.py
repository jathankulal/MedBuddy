"""Tests for configured emergency warning-sign detection."""

from safety.engine import assess_safety
from safety.rules.emergency import detect_emergency_signals


def test_genuine_chest_pain_is_detected():
    assert detect_emergency_signals("I am having chest pain.") == ["chest pain"]


def test_existing_emergency_phrase_is_detected():
    assert detect_emergency_signals("I have shortness of breath.") == [
        "shortness of breath"
    ]


def test_ordinary_message_has_no_configured_emergency_signal():
    assert detect_emergency_signals("I would like to organize my health notes.") == []


def test_negated_chest_pain_is_not_reported():
    statements = (
        "I am not experiencing chest pain.",
        "I do not have chest pain.",
        "I have no chest pain.",
    )

    for statement in statements:
        assert detect_emergency_signals(statement) == []


def test_negated_breathing_difficulty_is_not_reported():
    assert detect_emergency_signals("I do not have trouble breathing.") == []


def test_crushing_chest_descriptions_map_to_chest_pressure():
    statements = (
        "Crushing sensation in my chest.",
        "Crushing chest sensation.",
        "Crushing pressure in my chest.",
        "Heavy pressure in my chest.",
    )

    for statement in statements:
        assert detect_emergency_signals(statement) == ["chest pressure"]


def test_negated_symptom_does_not_suppress_affirmative_emergency_symptom():
    assert detect_emergency_signals(
        "I am not experiencing chest pain, but I have severe chest pressure."
    ) == ["chest pressure"]


def test_historical_negation_does_not_suppress_current_symptom():
    assert detect_emergency_signals(
        "I had no chest pain yesterday, but now I have chest pain."
    ) == ["chest pain"]


def test_no_longer_symptom_does_not_suppress_new_breathing_signal():
    assert detect_emergency_signals(
        "I no longer have chest pain, but I am having trouble breathing."
    ) == ["trouble breathing"]


def test_multiple_emergency_symptoms_are_returned():
    assert detect_emergency_signals(
        "I have chest pain and shortness of breath."
    ) == ["chest pain", "shortness of breath"]


def test_unrelated_negation_does_not_suppress_emergency_symptom():
    assert detect_emergency_signals(
        "I am not worried, but I have chest pain."
    ) == ["chest pain"]


def test_chest_or_pressure_words_alone_do_not_trigger():
    assert detect_emergency_signals(
        "There is pressure on the desk and a bruise on my chest."
    ) == []


def test_assessment_keeps_emergency_result_structure():
    result = assess_safety(
        "I am having chest pain and trouble breathing.",
        {},
        [],
        [],
    )

    assert result["is_emergency"] is True
    assert "chest pain" in result["emergency_reason"]
    assert result["warnings"][0]["code"] == "EMERGENCY_SYMPTOMS"
    assert result["warnings"][0]["severity"] == "critical"
    assert set(result["warnings"][0]) == {
        "code",
        "severity",
        "message",
        "recommended_action",
        "matched_item",
    }
    assert result["requires_human_review"] is True
    assert result["checked_items"] == ["emergency_signals"]
