"""Tests for episode progress-update sub-resource."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.main import app


def _make_episode(client, title="Flu recovery", status="recovering"):
    payload = {
        "title": title,
        "start_date": "2026-03-01T00:00:00Z",
        "status": status,
    }
    res = client.post("/episodes", json=payload)
    assert res.status_code == 201, res.json()
    return res.json()


def _make_update_payload(feeling="Feeling better", date="2026-03-04T00:00:00Z"):
    return {
        "update_date": date,
        "feeling": feeling,
        "changes": "Less fever",
        "notes": "Drank more water",
    }


# --- Listing ---

def test_list_updates_empty(temp_data_dir):
    """GET /episodes/{id}/updates returns [] when no updates exist."""
    client = TestClient(app)
    ep = _make_episode(client)
    res = client.get(f"/episodes/{ep['id']}/updates")
    assert res.status_code == 200
    assert res.json() == []


def test_list_updates_unknown_episode(temp_data_dir):
    """GET /episodes/{id}/updates returns 404 for unknown episode."""
    client = TestClient(app)
    res = client.get("/episodes/00000000-0000-0000-0000-000000000000/updates")
    assert res.status_code == 404


# --- Creating ---

def test_create_update(temp_data_dir):
    """POST /episodes/{id}/updates creates a progress update."""
    client = TestClient(app)
    ep = _make_episode(client)
    res = client.post(f"/episodes/{ep['id']}/updates", json=_make_update_payload())
    assert res.status_code == 201
    body = res.json()
    assert body["id"] is not None
    assert body["episode_id"] == ep["id"]
    assert body["feeling"] == "Feeling better"
    assert body["changes"] == "Less fever"
    assert body["notes"] == "Drank more water"
    assert body["created_at"] is not None


def test_create_update_unknown_episode(temp_data_dir):
    """POST /episodes/{id}/updates returns 404 for unknown episode."""
    client = TestClient(app)
    res = client.post(
        "/episodes/00000000-0000-0000-0000-000000000000/updates",
        json=_make_update_payload(),
    )
    assert res.status_code == 404


def test_create_update_missing_feeling_rejected(temp_data_dir):
    """POST /episodes/{id}/updates requires a non-empty feeling field."""
    client = TestClient(app)
    ep = _make_episode(client)
    payload = {"update_date": "2026-03-04T00:00:00Z", "feeling": ""}
    res = client.post(f"/episodes/{ep['id']}/updates", json=payload)
    assert res.status_code == 422


# --- Retrieval after save ---

def test_updates_retrieved_in_chronological_order(temp_data_dir):
    """Updates are returned sorted by update_date ascending."""
    client = TestClient(app)
    ep = _make_episode(client)
    client.post(f"/episodes/{ep['id']}/updates", json=_make_update_payload("Day 5", "2026-03-05T00:00:00Z"))
    client.post(f"/episodes/{ep['id']}/updates", json=_make_update_payload("Day 2", "2026-03-02T00:00:00Z"))
    client.post(f"/episodes/{ep['id']}/updates", json=_make_update_payload("Day 10", "2026-03-10T00:00:00Z"))

    res = client.get(f"/episodes/{ep['id']}/updates")
    assert res.status_code == 200
    updates = res.json()
    assert len(updates) == 3
    dates = [u["update_date"] for u in updates]
    assert dates == sorted(dates), "Updates should be chronological"
    assert updates[0]["feeling"] == "Day 2"
    assert updates[-1]["feeling"] == "Day 10"


def test_updates_persist_after_re_query(temp_data_dir):
    """Updates created in one request are returned in a fresh query."""
    client = TestClient(app)
    ep = _make_episode(client)
    created = client.post(
        f"/episodes/{ep['id']}/updates", json=_make_update_payload()
    ).json()

    # Re-query
    res = client.get(f"/episodes/{ep['id']}/updates")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == created["id"]


# --- Deleting ---

def test_delete_update(temp_data_dir):
    """DELETE /episodes/{id}/updates/{uid} removes the update."""
    client = TestClient(app)
    ep = _make_episode(client)
    created = client.post(
        f"/episodes/{ep['id']}/updates", json=_make_update_payload()
    ).json()

    del_res = client.delete(f"/episodes/{ep['id']}/updates/{created['id']}")
    assert del_res.status_code == 204

    list_res = client.get(f"/episodes/{ep['id']}/updates")
    assert list_res.json() == []


def test_delete_update_unknown_id(temp_data_dir):
    """DELETE /episodes/{id}/updates/{uid} returns 404 for unknown update."""
    client = TestClient(app)
    ep = _make_episode(client)
    res = client.delete(f"/episodes/{ep['id']}/updates/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


# --- Episode deletion cascades ---

def test_delete_episode_also_removes_updates(temp_data_dir):
    """DELETE /episodes/{id} removes the episode and all its updates."""
    client = TestClient(app)
    ep = _make_episode(client)
    client.post(f"/episodes/{ep['id']}/updates", json=_make_update_payload("Day 1", "2026-03-01T00:00:00Z"))
    client.post(f"/episodes/{ep['id']}/updates", json=_make_update_payload("Day 3", "2026-03-03T00:00:00Z"))

    del_ep = client.delete(f"/episodes/{ep['id']}")
    assert del_ep.status_code == 204

    # Episode gone
    assert client.get(f"/episodes/{ep['id']}").status_code == 404

    # Updates endpoint also returns 404 (episode gone)
    updates_res = client.get(f"/episodes/{ep['id']}/updates")
    assert updates_res.status_code == 404


# --- Existing episode CRUD compatibility ---

def test_existing_episode_crud_unaffected(temp_data_dir):
    """Create / update / delete episode still works after updates feature addition."""
    client = TestClient(app)
    ep = _make_episode(client, title="Compatibility check")
    assert ep["title"] == "Compatibility check"

    upd = client.put(f"/episodes/{ep['id']}", json={"status": "resolved"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "resolved"

    del_res = client.delete(f"/episodes/{ep['id']}")
    assert del_res.status_code == 204
    assert client.get("/episodes").json() == []


# --- Isolation: updates of different episodes don't mix ---

def test_updates_isolated_between_episodes(temp_data_dir):
    """Updates belong only to their own episode."""
    client = TestClient(app)
    ep1 = _make_episode(client, "Episode A")
    ep2 = _make_episode(client, "Episode B")

    client.post(f"/episodes/{ep1['id']}/updates", json=_make_update_payload("A update"))
    client.post(f"/episodes/{ep2['id']}/updates", json=_make_update_payload("B update"))

    res1 = client.get(f"/episodes/{ep1['id']}/updates").json()
    res2 = client.get(f"/episodes/{ep2['id']}/updates").json()

    assert len(res1) == 1 and res1[0]["feeling"] == "A update"
    assert len(res2) == 1 and res2[0]["feeling"] == "B update"
