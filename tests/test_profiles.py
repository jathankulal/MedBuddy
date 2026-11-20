"""Profile endpoint tests."""

from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

from backend.main import app


def test_get_profile_when_none_exists_returns_empty(temp_data_dir):
    """GET /profile returns an empty profile when none has been created."""
    client = TestClient(app)
    response = client.get("/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] is None
    assert body["full_name"] is None
    assert body["date_of_birth"] is None
    assert body["allergies"] is None
    assert body["conditions"] is None
    assert body["emergency_contact"] is None
    assert body["created_at"] is None
    assert body["updated_at"] is None


def test_put_profile_creates_and_get_profile_returns_it(temp_data_dir):
    """PUT /profile creates a profile; GET /profile returns it."""
    client = TestClient(app)
    payload = {
        "full_name": "Jane Doe",
        "date_of_birth": "1985-06-15",
        "allergies": ["penicillin"],
        "conditions": ["asthma"],
        "emergency_contact": "555-1234",
    }
    response = client.put("/profile", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] is not None
    UUID(body["id"])  # raises if not a valid UUID
    assert body["full_name"] == "Jane Doe"
    assert body["date_of_birth"] == "1985-06-15"
    assert body["allergies"] == ["penicillin"]
    assert body["conditions"] == ["asthma"]
    assert body["emergency_contact"] == "555-1234"
    assert body["created_at"] is not None
    assert body["updated_at"] is not None

    # GET should return the same data
    get_response = client.get("/profile")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["id"] == body["id"]
    assert get_body["full_name"] == "Jane Doe"


def test_put_profile_updates_and_refreshes_updated_at(temp_data_dir):
    """PUT /profile on an existing profile updates fields and refreshes updated_at."""
    client = TestClient(app)
    # Create
    client.put("/profile", json={"full_name": "Jane Doe"})
    created = client.get("/profile").json()
    first_updated_at = created["updated_at"]

    # Update
    response = client.put("/profile", json={"full_name": "Jane Smith", "allergies": ["nuts"]})
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]  # same profile
    assert body["full_name"] == "Jane Smith"
    assert body["allergies"] == ["nuts"]
    assert body["created_at"] == created["created_at"]  # preserved
    assert body["updated_at"] != first_updated_at  # refreshed


def test_profile_date_of_birth_in_future_rejected(temp_data_dir):
    """PUT /profile rejects a date_of_birth in the future."""
    client = TestClient(app)
    future = date.today().replace(year=date.today().year + 1)
    response = client.put("/profile", json={"date_of_birth": future.isoformat()})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "ERR_VALIDATION"


def test_profile_field_lengths_enforced(temp_data_dir):
    """PUT /profile enforces max length on string fields."""
    client = TestClient(app)
    response = client.put("/profile", json={"full_name": "A" * 201})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "ERR_VALIDATION"

    response = client.put("/profile", json={"emergency_contact": "A" * 201})
    assert response.status_code == 422


def test_profile_allergies_item_length_enforced(temp_data_dir):
    """PUT /profile rejects allergy items over 100 chars."""
    client = TestClient(app)
    response = client.put("/profile", json={"allergies": ["A" * 101]})
    assert response.status_code == 422


def test_profile_persists_across_test_client_instances(temp_data_dir):
    """Profile data persists when creating a new TestClient (simulates restart)."""
    client = TestClient(app)
    client.put("/profile", json={"full_name": "Persistent User"})

    # New client instance against same app/settings
    client2 = TestClient(app)
    response = client2.get("/profile")
    assert response.status_code == 200
    assert response.json()["full_name"] == "Persistent User"


def test_error_response_format_is_consistent(temp_data_dir):
    """Validation errors follow the documented error envelope."""
    client = TestClient(app)
    response = client.put("/profile", json={"full_name": "A" * 201})
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "ERR_VALIDATION"
    assert "message" in body["error"]
    assert "details" in body["error"]
