"""Pydantic schemas for MedBuddy API (Phase 2)."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# --- Health ---

class HealthResponse(BaseModel):
    status: str
    service: str
    env: str


# --- Profile ---

class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=200)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=50)
    allergies: Optional[List[str]] = Field(default=None)
    conditions: Optional[List[str]] = Field(default=None)
    emergency_contact: Optional[str] = Field(default=None, max_length=200)
    emergency_name: Optional[str] = Field(default=None, max_length=200)
    emergency_phone: Optional[str] = Field(default=None, max_length=50)
    preferred_language: Optional[str] = Field(default=None, max_length=50)
    accessibility_notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("allergies", "conditions", mode="before")
    @classmethod
    def _validate_list_items(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("must be a list")
        for item in v:
            if not isinstance(item, str) or len(item) > 100:
                raise ValueError("list items must be strings max 100 chars")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def _dob_not_in_future(cls, v):
        if v is not None and v > date.today():
            raise ValueError("date_of_birth must not be in the future")
        return v


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileRead(ProfileBase):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Episodes ---

class EpisodeBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = Field(pattern=r"^(active|recovering|resolved)$")
    category: Optional[str] = Field(default=None, max_length=100)
    symptoms: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)


class EpisodeCreate(EpisodeBase):
    @field_validator("end_date")
    @classmethod
    def _end_after_start(cls, v, info):
        if v is not None and "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be >= start_date")
        return v


class EpisodeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = Field(default=None, pattern=r"^(active|recovering|resolved)$")
    category: Optional[str] = Field(default=None, max_length=100)
    symptoms: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)


class EpisodeRead(EpisodeBase):
    id: str
    created_at: datetime
    updated_at: datetime


# --- Episode Progress Updates ---

class EpisodeProgressUpdateBase(BaseModel):
    update_date: datetime
    feeling: str = Field(min_length=1, max_length=200)
    changes: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)


class EpisodeProgressUpdateCreate(EpisodeProgressUpdateBase):
    pass


class EpisodeProgressUpdateRead(EpisodeProgressUpdateBase):
    id: str
    episode_id: str
    created_at: datetime


# --- Medications ---

class MedicationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    generic_name: Optional[str] = Field(default=None, max_length=200)
    active_ingredients: Optional[List[str]] = Field(default=None)
    strength: Optional[str] = Field(default=None, max_length=100)
    route: Optional[str] = Field(default=None, max_length=100)
    dosage: Optional[str] = Field(default=None, max_length=100)
    frequency: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = Field(default=None, max_length=200)
    indication: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, pattern=r"^(active|discontinued)$")

    @field_validator("active_ingredients", mode="before")
    @classmethod
    def _validate_ingredients(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("must be a list")
        for item in v:
            if not isinstance(item, str) or len(item) > 200:
                raise ValueError("active_ingredients items must be strings max 200 chars")
        return v


class MedicationCreate(MedicationBase):
    @field_validator("end_date")
    @classmethod
    def _end_after_start(cls, v, info):
        if (
            v is not None
            and "start_date" in info.data
            and info.data["start_date"] is not None
            and v < info.data["start_date"]
        ):
            raise ValueError("end_date must be >= start_date")
        return v


class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    generic_name: Optional[str] = Field(default=None, max_length=200)
    active_ingredients: Optional[List[str]] = None
    strength: Optional[str] = Field(default=None, max_length=100)
    route: Optional[str] = Field(default=None, max_length=100)
    dosage: Optional[str] = Field(default=None, max_length=100)
    frequency: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = Field(default=None, max_length=200)
    indication: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, pattern=r"^(active|discontinued)$")


class MedicationRead(MedicationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    medication_warnings: Optional[List[dict]] = None


# --- Safety ---

class SafetyWarning(BaseModel):
    code: str
    severity: str
    message: str
    recommended_action: Optional[str] = None
    matched_item: Optional[str] = None


class MedicationSafetyResult(BaseModel):
    is_duplicate: bool
    duplicate_type: Optional[str] = None
    warnings: Optional[List[SafetyWarning]] = None
    matched_item: Optional[str] = None
    existing_medication_id: Optional[str] = None
    checked_items: List[str]
    requires_human_review: bool = False


# --- Documents ---

class DocumentRead(BaseModel):
    id: str
    filename: str
    content_type: str = "application/pdf"
    size_bytes: int
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    status: str  # "uploaded" | "indexed" | "failed"


# --- Chat / RAG ---

class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int
    excerpt: str
    chunk_id: str
    relevance_score: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    document_ids: Optional[List[str]] = None
    episode_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    safety: dict
    context_used: bool
    context_sources: List[str]
    missing_information: Optional[List[str]] = None
    disclaimer: str
    response_mode: str  # "normal" | "emergency"


# --- Safety Result for chat ---

class SafetyResult(BaseModel):
    emergency: bool
    emergency_reason: Optional[str] = None
    warnings: Optional[List[SafetyWarning]] = None
    checked_items: List[str]
    requires_human_review: bool = False
