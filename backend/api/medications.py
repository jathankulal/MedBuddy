"""Medication API routes with safety engine integration.

Developer 2 owns the safety engine (`safety/` package). Developer 1 owns this
integration. The safety engine is consulted before every medication create or
update. If the safety engine is unavailable, crashes, or produces invalid
output, medication creation and updates fail closed with ERR_SAFETY_ENGINE (500).
Medication CRUD is not allowed to continue while safety validation is unavailable.
Exact duplicates (matching name, dosage, route, and strength) are rejected with
ERR_CONFLICT (409). The existing medication ID is only reported when the full
medication identity matches; ingredient overlap alone does not resolve an ID.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.database import data_file_path, ensure_data_dir, read_json, write_json
from backend.schemas import (
    MedicationCreate,
    MedicationRead,
    MedicationSafetyResult,
    MedicationUpdate,
)
from backend.services.safety_integration import check_medication_safety

router = APIRouter(prefix="", tags=["medications"])

MEDICATIONS_FILENAME = "medications.json"


def _load_medications() -> List[dict]:
    return read_json(settings.data_dir, MEDICATIONS_FILENAME, default=[]) or []


def _load_profile() -> Optional[dict]:
    return read_json(settings.data_dir, "profile.json", default=None)


@router.get("/medications", response_model=List[MedicationRead])
def list_medications():
    """List all medications."""
    return _load_medications()


@router.post("/medications", response_model=MedicationRead, status_code=201)
def create_medication(medication: MedicationCreate):
    """Create a new medication with safety-engine duplicate and safety check."""
    medications = _load_medications()
    health_profile = _load_profile()

    candidate = medication.model_dump()
    existing = [m for m in medications]

    try:
        safety_result = check_medication_safety(candidate, health_profile, existing)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ERR_SAFETY_ENGINE",
                    "message": str(exc),
                    "details": None,
                }
            },
        )

    if safety_result.is_duplicate and safety_result.duplicate_type == "exact":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "ERR_CONFLICT",
                    "message": "Exact duplicate medication record detected",
                    "details": {
                        "duplicate_type": "exact",
                        "matched_item": safety_result.matched_item,
                        "existing_medication_id": safety_result.existing_medication_id,
                        "warnings": [w.model_dump() for w in (safety_result.warnings or [])],
                        "checked_items": safety_result.checked_items,
                    },
                }
            },
        )

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid4()),
        "created_at": now,
        "updated_at": now,
        **candidate,
    }
    if safety_result.warnings:
        record["medication_warnings"] = [w.model_dump() for w in safety_result.warnings]

    medications.append(record)
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, MEDICATIONS_FILENAME, medications)
    return MedicationRead(**record)


@router.get("/medications/{medication_id}", response_model=MedicationRead)
def get_medication(medication_id: str):
    """Get a single medication by ID."""
    medications = _load_medications()
    for med in medications:
        if med["id"] == medication_id:
            return MedicationRead(**med)
    raise HTTPException(status_code=404, detail="Medication not found")


@router.put("/medications/{medication_id}", response_model=MedicationRead)
def update_medication(medication_id: str, medication: MedicationUpdate):
    """Update an existing medication. Merges fields, preserves created_at, refreshes updated_at."""
    medications = _load_medications()
    health_profile = _load_profile()

    for idx, med in enumerate(medications):
        if med["id"] == medication_id:
            merged = dict(med)
            updates = medication.model_dump(exclude_unset=True)
            merged.update(updates)

            # Validate date constraint on the merged record
            start = merged.get("start_date")
            end = merged.get("end_date")
            if start is not None and end is not None and end < start:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": {
                            "code": "ERR_VALIDATION",
                            "message": "end_date must be >= start_date",
                            "details": None,
                        }
                    },
                )

            # Safety check: exclude self from existing medications
            existing_others = [m for m in medications if m["id"] != medication_id]
            try:
                safety_result = check_medication_safety(
                    merged, health_profile, existing_others
                )
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": {
                            "code": "ERR_SAFETY_ENGINE",
                            "message": str(exc),
                            "details": None,
                        }
                    },
                )

            if safety_result.is_duplicate and safety_result.duplicate_type == "exact":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": {
                            "code": "ERR_CONFLICT",
                            "message": "Exact duplicate medication record detected",
                            "details": {
                                "duplicate_type": "exact",
                                "matched_item": safety_result.matched_item,
                                "existing_medication_id": safety_result.existing_medication_id,
                                "warnings": [w.model_dump() for w in (safety_result.warnings or [])],
                                "checked_items": safety_result.checked_items,
                            },
                        }
                    },
                )

            merged["updated_at"] = datetime.now(timezone.utc).isoformat()
            if safety_result.warnings:
                merged["medication_warnings"] = [w.model_dump() for w in safety_result.warnings]
            else:
                merged["medication_warnings"] = None

            medications[idx] = merged
            ensure_data_dir(settings.data_dir)
            write_json(settings.data_dir, MEDICATIONS_FILENAME, medications)
            return MedicationRead(**merged)

    raise HTTPException(status_code=404, detail="Medication not found")


@router.delete("/medications/{medication_id}", status_code=204)
def delete_medication(medication_id: str):
    """Delete a medication by ID."""
    medications = _load_medications()
    for idx, med in enumerate(medications):
        if med["id"] == medication_id:
            medications.pop(idx)
            ensure_data_dir(settings.data_dir)
            write_json(settings.data_dir, MEDICATIONS_FILENAME, medications)
            return
    raise HTTPException(status_code=404, detail="Medication not found")
