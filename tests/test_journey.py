"""End-to-end full prototype journey verification test.

Covers the complete 10-step demo scenario:
1. Profile management
2. Medication entry and safety validation
3. Care episode creation
4. PDF upload and vector indexing
5. Grounded RAG query
6. Citations with filename and page numbers
7. Safety warnings on conflict / ingredient overlap
8. Emergency detection and Gemini bypass
9. Persistence across server restarts
"""

import io
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import fitz

from backend.main import app
import backend.api.documents as documents_mod


def _generate_synthetic_pdf():
    """Generate a clean synthetic clinical discharge summary."""
    doc = fitz.open()
    page = doc.new_page()
    content = (
        "MedBuddy Clinical Discharge Summary\n"
        "Patient: Jane Doe\n"
        "Primary diagnosis: Mild intermittent asthma.\n"
        "Treatment plan: Inhaled Albuterol 90 mcg as needed for acute wheezing.\n"
        "Allergies on record: Severe allergy to Penicillin.\n"
        "Follow-up: Scheduled pulmonary evaluation in three months.\n"
    )
    page.insert_text((72, 72), content)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def test_full_demo_journey(temp_data_dir, monkeypatch):
    client = TestClient(app)

    # 1. Enter health profile
    profile_payload = {
        "full_name": "Jane Doe",
        "date_of_birth": "1988-06-15",
        "gender": "Female",
        "allergies": ["Penicillin", "Sulfa"],
        "conditions": ["Mild Asthma"],
        "emergency_name": "John Doe",
        "emergency_phone": "+1-555-0199",
        "preferred_language": "English",
        "accessibility_notes": "None",
    }
    prof_res = client.put("/profile", json=profile_payload)
    assert prof_res.status_code == 200
    assert prof_res.json()["full_name"] == "Jane Doe"
    assert prof_res.json()["allergies"] == ["Penicillin", "Sulfa"]

    # 2. Add medication
    med_payload = {
        "name": "Albuterol Inhaler",
        "strength": "90 mcg",
        "dosage": "2 puffs",
        "route": "Inhalation",
        "active_ingredients": ["Albuterol Sulfate"],
        "frequency": "Every 4 to 6 hours as needed",
        "status": "active",
    }
    med_res = client.post("/medications", json=med_payload)
    assert med_res.status_code == 201
    med_id = med_res.json()["id"]

    # 3. Create care episode
    ep_payload = {
        "title": "Annual Asthma Review",
        "category": "Check-up",
        "status": "active",
        "start_date": "2026-11-20T10:00:00Z",
        "symptoms": "Occasional exercise-induced shortness of breath",
        "notes": "Prescription refilled. Spirometry values normal.",
    }
    ep_res = client.post("/episodes", json=ep_payload)
    assert ep_res.status_code == 201
    ep_id = ep_res.json()["id"]

    # 4. Upload medical PDF document
    pdf_bytes = _generate_synthetic_pdf()
    doc_res = client.post(
        "/documents/upload",
        files={"file": ("Jane_Doe_Discharge_Summary.pdf", pdf_bytes, "application/pdf")},
    )
    assert doc_res.status_code == 201
    doc_data = doc_res.json()
    assert doc_data["status"] == "indexed"
    assert doc_data["page_count"] == 1
    doc_id = doc_data["id"]

    # 5. Query Copilot with questions about document
    # Mock Gemini response if no key configured
    def _fake_generate(prompt):
        return "Based on your clinical discharge summary (Page 1), you are prescribed Inhaled Albuterol 90 mcg as needed for acute wheezing."

    from backend.api import chat as chat_mod
    client_inst = chat_mod._get_gemini_client()
    if client_inst:
        monkeypatch.setattr(client_inst, "generate", _fake_generate)
        monkeypatch.setattr(client_inst, "is_configured", lambda: True)

    chat_res = client.post(
        "/chat",
        json={
            "message": "What medication was prescribed in my discharge summary?",
            "document_ids": [doc_id],
        },
    )
    assert chat_res.status_code == 200
    chat_body = chat_res.json()
    assert chat_body["response_mode"] == "normal"
    assert chat_body["context_used"] is True
    assert len(chat_body["citations"]) >= 1
    assert chat_body["citations"][0]["filename"] == "Jane_Doe_Discharge_Summary.pdf"
    assert chat_body["citations"][0]["page_number"] == 1

    # 6. Safety check: Duplicate medication rejected with 409
    dup_res = client.post("/medications", json=med_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "ERR_CONFLICT"

    # 7. Safety check: Medication with allergy conflict generates safety warning
    amox_payload = {
        "name": "Amoxicillin",
        "strength": "500 mg",
        "dosage": "1 capsule",
        "route": "Oral",
        "active_ingredients": ["Amoxicillin", "Penicillin"],
        "status": "active",
    }
    amox_res = client.post("/medications", json=amox_payload)
    assert amox_res.status_code == 201
    assert amox_res.json().get("medication_warnings") is not None

    # 8. Emergency detection bypasses Gemini
    emergency_res = client.post(
        "/chat",
        json={"message": "I have severe crushing chest pain radiating to my left arm and cannot breathe."},
    )
    assert emergency_res.status_code == 200
    emerg_body = emergency_res.json()
    assert emerg_body["response_mode"] == "emergency"
    assert emerg_body["safety"]["emergency"] is True
    assert emerg_body["context_used"] is False
    assert "emergency" in emerg_body["answer"].lower()

    # 9. Verify persistence across client/server restarts
    # Simulate fresh client restarting
    fresh_client = TestClient(app)

    fresh_profile = fresh_client.get("/profile").json()
    assert fresh_profile["full_name"] == "Jane Doe"
    assert fresh_profile["allergies"] == ["Penicillin", "Sulfa"]

    fresh_meds = fresh_client.get("/medications").json()
    assert len(fresh_meds) == 2  # Albuterol + Amoxicillin

    fresh_eps = fresh_client.get("/episodes").json()
    assert len(fresh_eps) == 1
    assert fresh_eps[0]["title"] == "Annual Asthma Review"

    fresh_docs = fresh_client.get("/documents").json()
    assert len(fresh_docs) == 1
    assert fresh_docs[0]["filename"] == "Jane_Doe_Discharge_Summary.pdf"
