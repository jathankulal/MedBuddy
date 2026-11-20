"""Recovery episode endpoint tests."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from backend.main import app


def _make_episode_payload(title="Post-surgery recovery", days_offset=0, status="recovering"):
    start = datetime.now(timezone.utc) + timedelta(days=days_offset)
    end = start + timedelta(days=7)
    return {
        "title": title,
        "description": "Recovering from knee surgery",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "status": status,
        "notes": "Physical therapy twice weekly",
    }


def test_get_episodes_empty_when_none(temp_data_dir):
    """GET /episodes returns an empty list when no episodes exist."""
    client = TestClient(app)
    response = client.get("/episodes")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_episode(temp_data_dir):
    """POST /episodes creates an episode; GET /episodes lists it."""
    client = TestClient(app)
    payload = _make_episode_payload()
    response = client.post("/episodes", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    UUID(body["id"])
    assert body["title"] == "Post-surgery recovery"
    assert body["status"] == "recovering"
    assert body["created_at"] is not None
    assert body["updated_at"] == body["created_at"]

    list_response = client.get("/episodes")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == body["id"]


def test_create_episode_with_status_values(temp_data_dir):
    """POST /episodes accepts all valid status values."""
    client = TestClient(app)
    for status in ["active", "recovering", "resolved"]:
        payload = _make_episode_payload(title=f"Episode {status}", status=status)
        response = client.post("/episodes", json=payload)
        assert response.status_code == 201, f"Failed for status {status}"
        assert response.json()["status"] == status


def test_get_episode_by_id(temp_data_dir):
    """GET /episodes/{id} returns the correct episode."""
    client = TestClient(app)
    created = client.post("/episodes", json=_make_episode_payload()).json()
    response = client.get(f"/episodes/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["title"] == created["title"]


def test_get_episode_unknown_id_returns_404(temp_data_dir):
    """GET /episodes/{id} returns 404 for unknown IDs."""
    client = TestClient(app)
    response = client.get("/episodes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "ERR_NOT_FOUND"


def test_update_episode_preserves_created_at_refreshes_updated_at(temp_data_dir):
    """PUT /episodes/{id} preserves created_at and updates updated_at."""
    client = TestClient(app)
    created = client.post("/episodes", json=_make_episode_payload()).json()
    first_updated = created["updated_at"]

    import time
    time.sleep(0.01)

    response = client.put(
        f"/episodes/{created['id']}",
        json={"title": "Updated title", "status": "resolved"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Updated title"
    assert body["status"] == "resolved"
    assert body["created_at"] == created["created_at"]  # preserved
    assert body["updated_at"] != first_updated  # refreshed


def test_update_episode_unknown_id_returns_404(temp_data_dir):
    """PUT /episodes/{id} returns 404 for unknown IDs."""
    client = TestClient(app)
    response = client.put(
        "/episodes/00000000-0000-0000-0000-000000000000",
        json={"title": "Nope"},
    )
    assert response.status_code == 404


def test_episode_end_date_before_start_date_rejected(temp_data_dir):
    """POST /episodes rejects end_date before start_date."""
    client = TestClient(app)
    start = datetime.now(timezone.utc)
    end = start - timedelta(days=1)
    payload = {
        "title": "Bad dates",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "status": "active",
    }
    response = client.post("/episodes", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ERR_VALIDATION"


def test_episode_title_required_and_length(temp_data_dir):
    """POST /episodes requires a non-empty title and enforces max length."""
    client = TestClient(app)
    # Empty title
    response = client.post(
        "/episodes",
        json={"title": "", "start_date": datetime.now(timezone.utc).isoformat(), "status": "active"},
    )
    assert response.status_code == 422

    # Title too long
    response = client.post(
        "/episodes",
        json={"title": "A" * 201, "start_date": datetime.now(timezone.utc).isoformat(), "status": "active"},
    )
    assert response.status_code == 422

    # Missing title
    response = client.post(
        "/episodes",
        json={"start_date": datetime.now(timezone.utc).isoformat(), "status": "active"},
    )
    assert response.status_code == 422


def test_delete_episode_success(temp_data_dir):
    """DELETE /episodes/{id} removes the episode from storage."""
    client = TestClient(app)
    created = client.post("/episodes", json=_make_episode_payload()).json()
    assert len(client.get("/episodes").json()) == 1

    del_resp = client.delete(f"/episodes/{created['id']}")
    assert del_resp.status_code == 204
    assert len(client.get("/episodes").json()) == 0


def test_delete_episode_unknown_id_returns_404(temp_data_dir):
    """DELETE /episodes/{id} returns 404 for unknown IDs."""
    client = TestClient(app)
    del_resp = client.delete("/episodes/00000000-0000-0000-0000-000000000000")
    assert del_resp.status_code == 404


def test_update_episode_start_date_after_existing_end_date_rejected(temp_data_dir):
    """PUT /episodes/{id} rejects updating start_date beyond existing end_date."""
    client = TestClient(app)
    created = client.post(
        "/episodes",
        json={
            "title": "Knee surgery",
            "start_date": "2026-03-01T10:00:00Z",
            "end_date": "2026-03-05T10:00:00Z",
            "status": "active",
        },
    ).json()

    # Attempt to update start_date to after end_date without specifying end_date
    res = client.put(
        f"/episodes/{created['id']}",
        json={"start_date": "2026-03-10T10:00:00Z"},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "ERR_VALIDATION"
    assert "end_date must be >= start_date" in res.json()["error"]["message"]

    # Verify existing record in storage is untouched
    persisted = client.get(f"/episodes/{created['id']}").json()
    assert "2026-03-01" in persisted["start_date"]


def test_update_episode_end_date_before_existing_start_date_rejected(temp_data_dir):
    """PUT /episodes/{id} rejects updating end_date before existing start_date."""
    client = TestClient(app)
    created = client.post(
        "/episodes",
        json={
            "title": "Physical therapy",
            "start_date": "2026-03-10T10:00:00Z",
            "end_date": "2026-03-20T10:00:00Z",
            "status": "active",
        },
    ).json()

    # Attempt to update end_date to before start_date without specifying start_date
    res = client.put(
        f"/episodes/{created['id']}",
        json={"end_date": "2026-03-05T10:00:00Z"},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "ERR_VALIDATION"

    # Verify existing record in storage is untouched
    persisted = client.get(f"/episodes/{created['id']}").json()
    assert "2026-03-20" in persisted["end_date"]


def test_update_episode_valid_partial_update(temp_data_dir):
    """PUT /episodes/{id} succeeds for valid partial updates."""
    client = TestClient(app)
    created = client.post(
        "/episodes",
        json={
            "title": "Original title",
            "start_date": "2026-03-01T10:00:00Z",
            "end_date": "2026-03-10T10:00:00Z",
            "status": "active",
        },
    ).json()

    res = client.put(
        f"/episodes/{created['id']}",
        json={"title": "Updated title", "notes": "Healing well"},
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "Updated title"
    assert updated["notes"] == "Healing well"
    assert "2026-03-01" in updated["start_date"]
    assert "2026-03-10" in updated["end_date"]


def test_update_episode_without_end_date(temp_data_dir):
    """PUT /episodes/{id} succeeds for an episode that has no end_date."""
    client = TestClient(app)
    created = client.post(
        "/episodes",
        json={
            "title": "Ongoing wellness",
            "start_date": "2026-03-01T10:00:00Z",
            "status": "active",
        },
    ).json()

    res = client.put(
        f"/episodes/{created['id']}",
        json={"description": "Regular checkups"},
    )
    assert res.status_code == 200
    assert res.json()["description"] == "Regular checkups"
    assert res.json()["end_date"] is None
