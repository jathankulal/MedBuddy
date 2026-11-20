"""Configured emergency-sign phrase detection."""

import re
import unicodedata

EMERGENCY_WARNING_SIGNS = (
    "chest pain",
    "chest pressure",
    "shortness of breath",
    "difficulty breathing",
    "trouble breathing",
    "can't breathe",
    "cannot breathe",
    "unconscious",
    "unresponsive",
    "severe bleeding",
    "bleeding heavily",
    "face drooping",
    "slurred speech",
    "weakness on one side",
    "throat closing",
    "swelling of the tongue",
    "severe allergic reaction",
)

EMERGENCY_SIGNAL_ALIASES = {
    "chest pressure": (
        "crushing sensation in my chest",
        "crushing sensation in chest",
        "crushing chest sensation",
        "crushing pressure in my chest",
        "crushing pressure in chest",
        "heavy pressure in my chest",
        "heavy pressure in chest",
    ),
}

_NEGATION_MODIFIERS = (
    r"(?:\s+(?:any|a|an|current|currently|severe|heavy|crushing|sharp|mild))*"
)
_NEGATION_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        rf"(?:^|\s)no{_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)(?:have|has|had)\s+no{_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)(?:do|does|did)\s+not\s+(?:have|experience|feel)"
        rf"{_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)(?:don t|doesn t|didn t)\s+"
        rf"(?:have|experience|feel){_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)(?:am|is|are|was|were)\s+not\s+"
        rf"(?:currently\s+)?(?:experiencing|having|feeling|reporting)"
        rf"{_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)not\s+(?:currently\s+)?"
        rf"(?:experiencing|having|feeling|reporting){_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)no\s+longer\s+(?:have|experience|experiencing|having)"
        rf"{_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)(?:deny|denies|denied)\s+(?:having\s+)?"
        rf"{_NEGATION_MODIFIERS}$",
        rf"(?:^|\s)without{_NEGATION_MODIFIERS}$",
    )
)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))


def _clauses(message: str) -> list[str]:
    return re.split(
        r"[.!?;,\n]+|\b(?:but|however|although|yet)\b",
        message,
        flags=re.IGNORECASE,
    )


def _is_negated(prefix: str) -> bool:
    return any(pattern.search(prefix) for pattern in _NEGATION_PATTERNS)


def _has_affirmative_phrase(clause: str, phrase: str) -> bool:
    normalized_clause = _normalize(clause)
    normalized_phrase = _normalize(phrase)
    pattern = re.compile(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)")

    for match in pattern.finditer(normalized_clause):
        if not _is_negated(normalized_clause[: match.start()].strip()):
            return True
    return False


def detect_emergency_signals(message: str) -> list[str]:
    """Return canonical configured signs with an affirmative phrase occurrence.

    Negation is recognized only for explicit local constructions within a
    clause. Unrecognized or ambiguous wording remains a possible signal.
    """
    clauses = _clauses(message)
    matches = set()

    for sign in EMERGENCY_WARNING_SIGNS:
        phrases = (sign, *EMERGENCY_SIGNAL_ALIASES.get(sign, ()))
        if any(
            _has_affirmative_phrase(clause, phrase)
            for clause in clauses
            for phrase in phrases
        ):
            matches.add(sign)

    return [sign for sign in EMERGENCY_WARNING_SIGNS if sign in matches]
