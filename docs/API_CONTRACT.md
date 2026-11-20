# MedBuddy API Contract

**Version:** 1.2 (draft)
**Owner:** Developer 1 (backend) — shared agreement with Developer 2 (frontend/safety)
**Branch:** `backend-data`
**Scope:** Single-user local-first hackathon prototype. Not a medical device. No diagnosis, no prescriptions.

---

## 1. Base URL & Environment Configuration

The backend runs locally. All frontend requests go to the backend; the frontend never calls external AI services directly.

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| API base URL | `API_BASE_URL` | `http://localhost:8000` |
| API host | `API_HOST` | `0.0.0.0` |
| API port | `API_PORT` | `8000` |
| Data directory | `DATA_DIR` | `./data` |
| App env | `APP_ENV` | `development` |
| App debug | `APP_DEBUG` | `true` |
| CORS origins | `CORS_ORIGINS` | `http://localhost:8501` |
| Gemini API key | `GEMINI_API_KEY` | (required, backend only) |
| Gemini model | `GEMINI_MODEL` | `gemini-1.5-flash` |

- `GEMINI_API_KEY` is configured **only** on the backend.
- The frontend must never receive or access the Gemini API key.
- All Gemini calls happen server-side inside `/chat`.

---

## 2. CORS Configuration

Configured in `backend/main.py` via `CORS_ORIGINS` (comma-separated list).

| Setting | Value |
|---------|-------|
| Allowed origins | From `CORS_ORIGINS` env var (default `http://localhost:8501`) |
| Allowed methods | `*` |
| Allowed headers | `*` |
| Allow credentials | `true` |

The Streamlit frontend (default port 8501) must be listed in `CORS_ORIGINS`.

---

## 3. Consistent Error Response Format

All errors return a JSON body with this shape:

```json
{
  "error": {
    "code": "ERR_NOT_FOUND",
    "message": "Human-readable description",
    "details": null
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error.code` | string | Yes | Stable machine-readable error code |
| `error.message` | string | Yes | Human-readable message suitable for UI display |
| `error.details` | object\|null | No | Optional field-specific validation details |

FastAPI validation errors (422) use this same envelope; `error.code` is `ERR_VALIDATION` and `error.details` contains the field-level validation failures.

### HTTP Status Codes Used

| Status | When Used |
|--------|-----------|
| 200 | Successful GET / PUT |
| 201 | Successful POST (create) |
| 204 | Successful DELETE |
| 400 | Validation error / bad request (non-Pydantic) |
| 404 | Resource not found |
| 409 | Conflict (exact duplicate medication record) |
| 413 | Payload too large (uploaded file exceeds 10 MB) |
| 415 | Unsupported media type (uploaded file is not a PDF) |
| 422 | Unprocessable entity (Pydantic validation failure, or valid PDF violating document rules such as page count or password protection) |
| 500 | Internal server error (includes safety engine failure) |
| 502 | Backend Gemini call failed |

### Error Code to Status Mapping

| Code | Status | Meaning |
|------|--------|---------|
| `ERR_VALIDATION` | 400/422 | Invalid request body or query |
| `ERR_NOT_FOUND` | 404 | Requested resource does not exist |
| `ERR_CONFLICT` | 409 | Exact duplicate medication record |
| `ERR_UNSUPPORTED_FILE` | 415 | Uploaded file is not a PDF (validated by content, not filename/MIME type) |
| `ERR_PAYLOAD_TOO_LARGE` | 413 | Uploaded file exceeds 10 MB |
| `ERR_SAFETY_ENGINE` | 500 | Safety engine call failed or returned invalid result |
| `ERR_GEMINI` | 502 | Backend Gemini call failed |
| `ERR_INTERNAL` | 500 | Unexpected server error |

#### `error.details` for Medication Conflicts (409)

When `POST /medications` or `PUT /medications/{id}` returns `409 ERR_CONFLICT` for an exact duplicate:

```json
{
  "error": {
    "code": "ERR_CONFLICT",
    "message": "Exact duplicate medication record detected",
    "details": {
      "duplicate_type": "exact",
      "matched_item": "medication-id",
      "existing_medication_id": "medication-id-of-duplicate",
      "warnings": []
    }
  }
}
```

For ingredient overlap (not a conflict), the medication is saved and structured warnings are returned in the normal `MedicationRead` response alongside a `medication_warnings` field (see Section 4.4).

---

## 4. Endpoints

### 4.1 GET /health

Health check. No authentication.

**Request:** none

**Response (200):**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` |
| `service` | string | `"MedBuddy"` |
| `env` | string | Deployment environment |

**Pydantic model:** `HealthResponse`

---

### 4.2 Profile Management

Single-user prototype: one active health profile.

#### GET /profile

Returns the current health profile.

**Behavior when no profile exists:** Returns HTTP 200 with a default empty profile. All optional fields are absent or null; `id` is null. This indicates no profile has been created yet. The frontend should treat this as "no profile" and allow the user to create one via `PUT /profile`.

**Response (200):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string\|null | Yes | Profile identifier, or null if no profile exists |
| `full_name` | string | No | User's full name |
| `date_of_birth` | string (date) | No | ISO-8601 date |
| `allergies` | list[string] | No | Known allergies |
| `conditions` | list[string] | No | Existing medical conditions |
| `emergency_contact` | string | No | Emergency contact name/phone |
| `created_at` | string (datetime) | No | Creation timestamp, null if no profile |
| `updated_at` | string (datetime) | No | Last update timestamp, null if no profile |

**Pydantic models:** `ProfileRead` (response), `ProfileCreate` / `ProfileUpdate` (request bodies)

#### PUT /profile

Create or update (upsert) the single health profile.

**Request body:**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `full_name` | string | No | Max 200 chars |
| `date_of_birth` | string (date) | No | Must be valid ISO date, not in future |
| `allergies` | list[string] | No | Each item max 100 chars |
| `conditions` | list[string] | No | Each item max 100 chars |
| `emergency_contact` | string | No | Max 200 chars |

**Response (200):** `ProfileRead`

---

### 4.3 Recovery Episodes

Episodes represent recovery events (e.g., post-procedure, illness, injury).

#### GET /episodes

List all episodes.

**Response (200):** list of `EpisodeRead`

#### POST /episodes

Create a new episode.

**Request body:**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `title` | string | Yes | Max 200 chars, non-empty |
| `description` | string | No | Max 2000 chars |
| `start_date` | string (datetime) | Yes | Must be valid ISO datetime |
| `end_date` | string (datetime) | No | If present, must be >= start_date |
| `status` | string | Yes | One of: `active`, `recovering`, `resolved` |
| `notes` | string | No | Max 2000 chars |

**Response (201):** `EpisodeRead`

#### GET /episodes/{episode_id}

Get a single episode by ID.

**Response (200):** `EpisodeRead`
**Response (404):** `ERR_NOT_FOUND` if episode does not exist

#### PUT /episodes/{episode_id}

Update an existing episode.

**Request body:** same fields as POST (all optional for partial update)

**Response (200):** `EpisodeRead`
**Response (404):** `ERR_NOT_FOUND`

**Pydantic models:** `EpisodeRead`, `EpisodeCreate`, `EpisodeUpdate`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Episode UUID |
| `title` | string | Yes | Episode title |
| `description` | string | No | Episode description |
| `start_date` | string (datetime) | Yes | Start timestamp |
| `end_date` | string (datetime) | No | End timestamp |
| `status` | string | Yes | `active` \| `recovering` \| `resolved` |
| `notes` | string | No | Additional notes |
| `created_at` | string (datetime) | Yes | Creation timestamp |
| `updated_at` | string (datetime) | Yes | Last update timestamp |

---

### 4.4 Medication Management

Developer 2 implements safety checks (allergies, duplicates, ingredient overlap) in the `safety/` package and calls them through the backend integration. Developer 1 stores and returns medication data; Developer 1 does **not** implement safety logic.

The backend distinguishes three kinds of medication overlap:

| Kind | Meaning | Backend action |
|------|---------|----------------|
| Exact duplicate | Same medication record (same name, dosage, route, strength) as an existing record | Reject with `409 ERR_CONFLICT` |
| Active ingredient overlap | Different brands/products sharing active ingredient(s) | Save the medication; return structured `medication_warnings` in the response |
| Actual drug interaction | Pharmacodynamic/pharmacokinetic interaction between medications | **No** — not claimed as comprehensive |

#### GET /medications

List all medications.

**Response (200):** list of `MedicationRead`

#### POST /medications

Create a new medication.

**Request body:**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | Max 200 chars, non-empty |
| `generic_name` | string | No | Max 200 chars |
| `active_ingredients` | list[string] | No | Each item max 200 chars |
| `strength` | string | No | Max 100 chars |
| `route` | string | No | Max 100 chars |
| `dosage` | string | No | Max 100 chars |
| `frequency` | string | No | Max 100 chars |
| `start_date` | string (date) | No | Valid ISO date |
| `end_date` | string (date) | No | Valid ISO date, >= start_date |
| `prescribing_doctor` | string | No | Max 200 chars |
| `indication` | string | No | Max 500 chars |
| `notes` | string | No | Max 1000 chars |
| `status` | string | No | One of: `active`, `discontinued` |

**Backend integration:** Before saving, the backend calls `safety.engine.check_medication_entry(candidate_medication, health_profile, existing_medications)`.

- If `is_duplicate` is `true` and `duplicate_type` is `exact`: return `409 ERR_CONFLICT`. Do not save.
- If `is_duplicate` is `false` but ingredient overlap warnings exist: save the medication and return `201` with `MedicationRead` plus a `medication_warnings` field containing the structured `SafetyWarning` objects.
- If `duplicate_type` is `none`: save normally with `201`.

**Response (201):** `MedicationRead` (may include `medication_warnings`)
**Response (409):** `ERR_CONFLICT` for exact duplicate only

#### GET /medications/{medication_id}

Get a single medication by ID.

**Response (200):** `MedicationRead`
**Response (404):** `ERR_NOT_FOUND`

#### PUT /medications/{medication_id}

Update an existing medication. All fields optional (partial update).

**Backend integration:**
1. Load the existing medication record.
2. Merge submitted fields with the existing record to form the complete merged record.
3. Exclude the current medication from `existing_medications` when calling `check_medication_entry` (so a medication is not flagged as a duplicate of itself).
4. Call `safety.engine.check_medication_entry(merged_record, health_profile, existing_medications_except_self)`.
5. Validate date constraints (`end_date >= start_date`) against the complete merged record.
6. If `is_duplicate` is `true` and `duplicate_type` is `exact`: return `409 ERR_CONFLICT`. Do not save.
7. Otherwise save the merged record and return `200` with `MedicationRead` plus any `medication_warnings`.

**Response (200):** `MedicationRead` (may include `medication_warnings`)
**Response (404):** `ERR_NOT_FOUND`
**Response (409):** `ERR_CONFLICT` for exact duplicate only

#### DELETE /medications/{medication_id}

Delete a medication.

**Response (204):** No content
**Response (404):** `ERR_NOT_FOUND`

**Pydantic models:** `MedicationRead`, `MedicationCreate`, `MedicationUpdate`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Medication UUID |
| `name` | string | Yes | Medication name |
| `generic_name` | string | No | Generic/non-proprietary name |
| `active_ingredients` | list[string] | No | List of active ingredient names |
| `strength` | string | No | Strength (e.g., "500 mg") |
| `route` | string | No | Route of administration (e.g., "oral") |
| `dosage` | string | No | Dosage string |
| `frequency` | string | No | Frequency string |
| `start_date` | string (date) | No | Start date |
| `end_date` | string (date) | No | End date |
| `prescribing_doctor` | string | No | Doctor name |
| `indication` | string | No | Why it was prescribed |
| `notes` | string | No | Free-text notes |
| `status` | string | No | `active` \| `discontinued` |
| `created_at` | string (datetime) | Yes | Creation timestamp |
| `updated_at` | string (datetime) | Yes | Last update timestamp |

---

### 4.5 Document Management

Documents are uploaded PDFs. Contents are extracted, chunked, and indexed for RAG. Uploaded PDF binaries and extracted text are stored locally; the frontend does not receive full PDF text unless explicitly requested through chat citations.

#### GET /documents

List all uploaded documents (metadata only, no extracted text).

**Response (200):** list of `DocumentRead`

#### POST /documents/upload

Upload a PDF file.

**Request:** `multipart/form-data` with field `file`

**Backend validation:** The backend inspects the actual PDF file content (magic bytes / PDF header), not just the filename or supplied MIME type, to confirm it is a valid PDF.

**PDF Upload Restrictions:**

| Rule | Limit | Status Code |
|------|-------|-------------|
| File size | Max 10 MB | 413 `ERR_PAYLOAD_TOO_LARGE` |
| File type | Valid PDF content (not just `application/pdf` MIME) | 415 `ERR_UNSUPPORTED_FILE` |
| Page count | Max 100 pages | 422 `ERR_VALIDATION` |
| Encrypted/password-protected PDFs | Rejected | 422 `ERR_VALIDATION` |

**Response (201):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Document UUID |
| `filename` | string | Original filename |
| `content_type` | string | `application/pdf` |
| `size_bytes` | integer | File size in bytes |
| `page_count` | integer | Number of pages |
| `chunk_count` | integer | Number of text chunks extracted |
| `uploaded_at` | string (datetime) | Upload timestamp |
| `status` | string | `uploaded` \| `indexed` \| `failed` |

**Response (400):** `ERR_VALIDATION` for invalid form fields
**Response (413):** `ERR_PAYLOAD_TOO_LARGE` if file exceeds 10 MB
**Response (415):** `ERR_UNSUPPORTED_FILE` if file is not a valid PDF
**Response (422):** `ERR_VALIDATION` if a valid PDF violates document rules (excessive page count, password protection)

**Upload succeeds but extraction/indexing fails:** The document record is created with `status: "failed"`, `chunk_count: 0`, and the PDF binary is retained locally. The frontend can show the document as failed and offer retry or delete. Extraction/indexing failure does not return an error to the upload request; it is reflected in the document's `status` field.

**Pydantic models:** `DocumentRead`, `DocumentUploadResponse`

---

### 4.6 Chat / RAG

POST /chat

The user sends a message. The backend:

1. Loads health profile, medications, and episodes from JSON persistence.
2. Calls Developer 2's safety engine (`assess_safety`) **before** any Gemini generation.
3. If `safety.emergency` is `true`: returns an emergency safety response, does **not** call Gemini, `response_mode` = `"emergency"`.
4. If the safety engine fails or returns an invalid result: returns `ERR_SAFETY_ENGINE` (500), does **not** call Gemini.
5. Otherwise assembles document context from ChromaDB and calls Gemini for generation.
6. Returns answer with citations and safety metadata, `response_mode` = `"normal"`.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's natural-language query, non-empty, max 2000 chars |
| `document_ids` | list[string] | No | Optional subset of document IDs to restrict retrieval to |
| `episode_id` | string | No | Optional episode ID to scope recovery context |

**Response (200):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | string | Yes | Generated response text (safety refusal message if emergency) |
| `citations` | list[Citation] | Yes | Retrieved source excerpts (empty if emergency) |
| `safety` | SafetyResult | Yes | Safety engine output |
| `context_used` | boolean | Yes | Whether **retrieved PDF document context** was used in generation |
| `context_sources` | list[string] | Yes | List of source types actually supplied to Gemini (e.g., `"profile"`, `"medications"`, `"episodes"`, `"documents"`). Only sources that were actually included are listed. |
| `missing_information` | list[string] | No | Information needed to answer more completely |
| `disclaimer` | string | Yes | Fixed medical disclaimer text |
| `response_mode` | string | Yes | `normal` \| `emergency` |

**Pydantic models:** `ChatRequest`, `ChatResponse`

> Emergency responses clearly indicate that Gemini was **not** called. The `answer` contains urgent safety guidance generated by the backend, not by Gemini.

---

## 5. Citation Object Structure

Each citation references a specific chunk of an indexed document.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_id` | string | Yes | ID of the source document |
| `filename` | string | Yes | Original PDF filename |
| `page_number` | integer | Yes | 1-based page number in the PDF |
| `excerpt` | string | Yes | Relevant text excerpt (max ~500 chars) |
| `chunk_id` | string | Yes | Internal chunk identifier |
| `relevance_score` | float | No | Similarity score (0.0–1.0) |

**Pydantic model:** `Citation`

> Uploaded PDF full contents are never returned directly. Only small excerpts appear as citations in chat responses.

---

## 6. Safety Result Structure (Developer 2's Safety Engine)

Returned by the safety engine and included in every `/chat` response. Absence of a warning **does not** prove a medication or situation is safe. The safety engine is **not** a diagnostic system.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `emergency` | boolean | Yes | `true` if the message indicates a medical emergency |
| `emergency_reason` | string | No | Reason if `emergency` is true |
| `warnings` | list[SafetyWarning] | Yes | Structured safety warnings |
| `checked_items` | list[string] | Yes | What was checked (e.g., medications, allergies) |

### SafetyWarning Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Stable machine-readable warning code |
| `severity` | string | Yes | One of: `critical`, `high`, `warning`, `info` |
| `message` | string | Yes | Human-readable warning message |
| `recommended_action` | string | No | Suggested action for the user |
| `matched_item` | string | No | The medication/item that triggered the warning |

**Pydantic model:** `SafetyWarning`

### Example (non-emergency)

```json
{
  "emergency": false,
  "emergency_reason": null,
  "warnings": [
    {
      "code": "MED_INGREDIENT_OVERLAP",
      "severity": "warning",
      "message": "Two medications share the same active ingredient (acetaminophen).",
      "recommended_action": "Confirm total daily dose does not exceed the recommended maximum.",
      "matched_item": "acetaminophen"
    }
  ],
  "checked_items": ["medications", "allergies"]
}
```

### Example (emergency)

```json
{
  "emergency": true,
  "emergency_reason": "User mentions chest pain and shortness of breath",
  "warnings": [
    {
      "code": "EMERGENCY_SYMPTOMS",
      "severity": "critical",
      "message": "Potential medical emergency detected.",
      "recommended_action": "Seek immediate medical attention or call emergency services.",
      "matched_item": null
    }
  ],
  "checked_items": ["symptoms"]
}
```

---

## 7. Backend ↔ Safety Engine Interfaces

Developer 2 implements the safety engine in a root-level `safety/` package. Developer 1 integrates it into the backend `/chat` and medication endpoints before any Gemini call. Developer 2 owns the safety logic; Developer 1 owns backend integration.

### 7.1 assess_safety — Chat safety assessment

**Module:** `safety.engine`
**Function:** `assess_safety`

```python
def assess_safety(
    user_message: str,
    health_profile: dict | None,
    medications: list[dict],
    episodes: list[dict],
) -> SafetyResult:
    ...
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_message` | str | The raw user chat message |
| `health_profile` | dict \| None | Current profile (`ProfileRead` as dict) or `None` |
| `medications` | list[dict] | Current medications (`[MedicationRead ...]`) |
| `episodes` | list[dict] | Relevant recovery episodes (`[EpisodeRead ...]`) |

**Returns:** a `SafetyResult`-compatible object/dict with fields:
- `emergency` (bool)
- `emergency_reason` (str \| None)
- `warnings` (list[SafetyWarning])
- `checked_items` (list[str])

### 7.2 check_medication_entry — Medication safety validation

**Module:** `safety.engine`
**Function:** `check_medication_entry`

```python
def check_medication_entry(
    candidate_medication: dict,
    health_profile: dict | None,
    existing_medications: list[dict],
) -> MedicationSafetyResult:
    ...
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `candidate_medication` | dict | The medication being added/updated (`MedicationCreate`/`MedicationUpdate` as dict, or the merged record for updates) |
| `health_profile` | dict \| None | Current profile (`ProfileRead` as dict) or `None` |
| `existing_medications` | list[dict] | Current medications excluding the record being updated (`[MedicationRead ...]`) |

**Returns:** a `MedicationSafetyResult`-compatible object/dict with fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_duplicate` | boolean | Yes | `true` only for an **exact duplicate** medication record |
| `duplicate_type` | string | No | One of: `exact`, `ingredient_overlap`, `none` |
| `warnings` | list[SafetyWarning] | No | Structured warnings (e.g., ingredient overlap, allergy match). Returned even when `is_duplicate` is `false`. |
| `matched_item` | string | No | The medication/item that triggered the match or warning |
| `checked_items` | list[string] | Yes | What was checked (e.g., `medications`, `allergies`) |

**Behavior:**
- `is_duplicate = true` only when `duplicate_type == "exact"`. In this case the backend rejects the medication with `409 ERR_CONFLICT`.
- When `duplicate_type == "ingredient_overlap"`: `is_duplicate` is `false`. The backend saves the medication and returns the structured warnings to the frontend.
- When `duplicate_type == "none"`: no warnings, save normally.

### Integration flow

1. **`POST /medications`:** Backend calls `check_medication_entry(candidate, health_profile, all_existing_medications)`. If `is_duplicate` is `true` (exact), return `409 ERR_CONFLICT`. Otherwise save and return warnings if present.
2. **`PUT /medications/{id}`:** Backend merges submitted fields with the existing record, excludes the current record from `existing_medications`, validates date constraints on the merged record, then calls `check_medication_entry`. If exact duplicate, return `409 ERR_CONFLICT`. Otherwise save merged record and return warnings if present.
3. **`POST /chat`:** Backend calls `assess_safety`. If `safety.emergency` is `true`, return emergency response (no Gemini). If safety engine fails/invalid, return `ERR_SAFETY_ENGINE` (no Gemini). Otherwise proceed to retrieval + Gemini.

---

## 8. Chat Response Example (normal mode)

```json
{
  "answer": "Based on your uploaded discharge summary, your follow-up appointment is scheduled for two weeks after the procedure.",
  "citations": [
    {
      "document_id": "doc-123",
      "filename": "discharge_summary.pdf",
      "page_number": 2,
      "excerpt": "Follow-up appointment: 2026-12-05 at 10:00 AM.",
      "chunk_id": "doc-123-chunk-4",
      "relevance_score": 0.92
    }
  ],
  "safety": {
    "emergency": false,
    "emergency_reason": null,
    "warnings": [
      {
        "code": "MED_INGREDIENT_OVERLAP",
        "severity": "warning",
        "message": "Two medications share the same active ingredient (acetaminophen).",
        "recommended_action": "Confirm total daily dose does not exceed the recommended maximum.",
        "matched_item": "acetaminophen"
      }
    ],
    "checked_items": ["medications", "allergies"]
  },
  "context_used": true,
  "context_sources": ["profile", "medications", "documents"],
  "missing_information": [],
  "disclaimer": "This information is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.",
  "response_mode": "normal"
}
```

### Chat Response Example (emergency mode — Gemini not called)

```json
{
  "answer": "Based on your message, this may be a medical emergency. Please seek immediate medical attention or call emergency services right away. This system is not a diagnostic tool.",
  "citations": [],
  "safety": {
    "emergency": true,
    "emergency_reason": "User mentions chest pain and shortness of breath",
    "warnings": [
      {
        "code": "EMERGENCY_SYMPTOMS",
        "severity": "critical",
        "message": "Potential medical emergency detected.",
        "recommended_action": "Seek immediate medical attention or call emergency services.",
        "matched_item": null
      }
    ],
    "checked_items": ["symptoms"]
  },
  "context_used": false,
  "context_sources": [],
  "missing_information": [],
  "disclaimer": "This information is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.",
  "response_mode": "emergency"
}
```

---

## 9. How the Frontend Consumes Each Endpoint

| Endpoint | Frontend Use |
|----------|--------------|
| `GET /health` | On app load, verify backend is reachable before enabling UI. |
| `GET /profile` | Load user profile into the Health Profile UI on startup. If `id` is null, treat as "no profile" and prompt the user to create one. |
| `PUT /profile` | Save changes from the Health Profile UI. |
| `GET /episodes` | Populate the Recovery Episode list UI. |
| `POST /episodes` | Create a new episode from the Recovery Episode UI. |
| `GET /episodes/{id}` | Open episode detail view. |
| `PUT /episodes/{id}` | Edit episode details. |
| `GET /medications` | Populate the Medication list UI. Show `generic_name`, `active_ingredients`, `strength`, `route`, `status`, and any `medication_warnings`. |
| `POST /medications` | Add a new medication. If backend returns 409, show exact-duplicate conflict and do not save. If 201 with `medication_warnings`, save and display the structured warnings to the user (ingredient overlap does not block saving). |
| `GET /medications/{id}` | Open medication detail view. |
| `PUT /medications/{id}` | Edit medication. If backend returns 409, show exact-duplicate conflict. If 200 with `medication_warnings`, save and display warnings. |
| `DELETE /medications/{id}` | Remove a medication. |
| `GET /documents` | Show uploaded document list in Document Upload UI. |
| `POST /documents/upload` | Upload PDF; show `page_count`, `chunk_count`, `status` after upload. Handle 413 (too large), 415 (not PDF), and 422 (valid PDF but page count/password violation). If `status` is `failed`, show retry/delete options. |
| `POST /chat` | Send user query (optional `episode_id`) to Copilot chat UI. Render `answer`, show `citations` as source references, surface `safety.warnings` as severity-coded banners, show `disclaimer`. Use `context_used` and `context_sources` to show which sources informed the answer. If `response_mode` is `emergency`, display urgent guidance prominently and indicate Gemini was not used. |

---

## 10. Data Conventions

### Timezone Handling

All datetime fields use ISO-8601 format. Backend stores and returns datetimes in UTC. Clients should send timezone-aware datetimes where possible; naive datetimes are interpreted as local time by the backend and normalized to UTC on storage. Date-only fields (e.g., `start_date`, `end_date` on medications) use ISO-8601 date format (`YYYY-MM-DD`) with no time component.

---

## 11. Medical Disclaimers (Required)

- This is a hackathon prototype, not a medical device.
- No diagnosis, treatment recommendations, or prescriptions are provided.
- Absence of a safety warning does **not** mean a medication, symptom, or situation is safe.
- The safety engine is **not** a diagnostic system.
- Actual drug interactions are not comprehensively detected; only exact duplicates and active ingredient overlap are flagged.
- Always consult a qualified healthcare provider for medical decisions.

---

**End of contract.**
No backend endpoints or functionality are implemented by this document. Developer 1 implements the endpoints per this contract in Phase 2; Developer 2 implements `safety/` and the Streamlit frontend per this contract.
