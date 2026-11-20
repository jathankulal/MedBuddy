"""AI context engine.

Assembles grounded context from health profile, medications, episodes, and
retrieved document chunks for Gemini generation.
"""

from typing import List, Optional


class ContextEngine:
    """Builds a context string for Gemini from available health data."""

    DISCLAIMER = (
        "This information is for educational purposes only and is not a "
        "substitute for professional medical advice, diagnosis, or "
        "treatment. Always consult a qualified healthcare provider."
    )

    @staticmethod
    def build_context(
        profile: Optional[dict],
        medications: List[dict],
        episodes: List[dict],
        document_chunks: List[dict],
    ) -> str:
        """Assemble a context string from available health data sources."""
        parts: List[str] = []

        if profile and profile.get("id"):
            parts.append("=== USER HEALTH PROFILE ===")
            if profile.get("full_name"):
                parts.append(f"Name: {profile['full_name']}")
            if profile.get("date_of_birth"):
                parts.append(f"Date of Birth: {profile['date_of_birth']}")
            if profile.get("allergies"):
                parts.append(f"Allergies: {', '.join(profile['allergies'])}")
            if profile.get("conditions"):
                parts.append(f"Conditions: {', '.join(profile['conditions'])}")
            if profile.get("emergency_contact"):
                parts.append(f"Emergency Contact: {profile['emergency_contact']}")
            parts.append("")

        if medications:
            parts.append("=== MEDICATIONS ===")
            for med in medications:
                parts.append(f"- {med.get('name', 'Unknown')}")
                if med.get("dosage"):
                    parts.append(f"  Dosage: {med['dosage']}")
                if med.get("frequency"):
                    parts.append(f"  Frequency: {med['frequency']}")
                if med.get("status"):
                    parts.append(f"  Status: {med['status']}")
            parts.append("")

        if episodes:
            parts.append("=== RECOVERY EPISODES ===")
            for ep in episodes:
                parts.append(f"- {ep.get('title', 'Untitled')} ({ep.get('status', 'unknown')})")
                if ep.get("description"):
                    parts.append(f"  {ep['description']}")
            parts.append("")

        if document_chunks:
            parts.append("=== DOCUMENT EXCERPTS ===")
            seen = set()
            for chunk in document_chunks:
                doc_id = chunk.get("document_id", "unknown")
                page = chunk.get("page_number", "?")
                key = f"{doc_id}:{page}:{chunk.get('chunk_id', '')}"
                if key in seen:
                    continue
                seen.add(key)
                parts.append(
                    f"[{chunk.get('filename', 'document')} p.{page}]: {chunk.get('text', '')}"
                )
            parts.append("")

        parts.append("=== INSTRUCTIONS ===")
        parts.append(
            "Answer the user's question using only the information provided "
            "above. If the information is not present in the available "
            "records, say so clearly. Do not invent appointment dates, "
            "medication instructions, test results, or medical facts. "
            "Do not diagnose, prescribe, or recommend changing medication."
        )

        return "\n".join(parts)

    @staticmethod
    def identify_missing_information(
        profile: Optional[dict],
        medications: List[dict],
        episodes: List[dict],
        document_chunks: List[dict],
        user_message: str,
    ) -> List[str]:
        """Identify what information is missing to answer more completely."""
        missing: List[str] = []

        if not profile or not profile.get("id"):
            missing.append("health profile")

        if not medications:
            missing.append("medication list")

        if not episodes:
            missing.append("recovery episodes")

        if not document_chunks:
            missing.append("uploaded document context")

        return missing

    @staticmethod
    def get_disclaimer() -> str:
        return ContextEngine.DISCLAIMER