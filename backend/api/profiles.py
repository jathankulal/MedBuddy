"""Health profile API routes (GET /profile, PUT /profile)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.database import data_file_path, ensure_data_dir, read_json, write_json
from backend.schemas import ProfileCreate, ProfileRead, ProfileUpdate

router = APIRouter(prefix="", tags=["profile"])

PROFILE_FILENAME = "profile.json"


def _empty_profile() -> ProfileRead:
    """Return a default empty profile when none exists."""
    return ProfileRead(
        id=None,
        full_name=None,
        date_of_birth=None,
        allergies=None,
        conditions=None,
        emergency_contact=None,
        created_at=None,
        updated_at=None,
    )


@router.get("/profile", response_model=ProfileRead)
def get_profile():
    """Get the current health profile. Returns an empty profile if none exists."""
    data = read_json(settings.data_dir, PROFILE_FILENAME, default=None)
    if data is None:
        return _empty_profile()
    return ProfileRead(**data)


@router.put("/profile", response_model=ProfileRead)
def put_profile(profile: ProfileCreate):
    """Create or update (upsert) the single health profile."""
    data = read_json(settings.data_dir, PROFILE_FILENAME, default=None)
    now = datetime.now(timezone.utc).isoformat()

    if data is None:
        data = {
            "id": str(uuid4()),
            "created_at": now,
            "updated_at": now,
        }
    else:
        data["updated_at"] = now

    # Merge submitted fields (all optional)
    updates = profile.model_dump(exclude_unset=True)
    if ("emergency_name" in updates or "emergency_phone" in updates) and "emergency_contact" not in updates:
        name_val = updates.get("emergency_name") or data.get("emergency_name") or ""
        phone_val = updates.get("emergency_phone") or data.get("emergency_phone") or ""
        combined = f"{name_val} ({phone_val})".strip() if phone_val else name_val
        if combined:
            updates["emergency_contact"] = combined
    data.update(updates)

    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, PROFILE_FILENAME, data)
    return ProfileRead(**data)
