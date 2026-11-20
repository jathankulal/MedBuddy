"""Recovery episode API routes."""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.database import data_file_path, ensure_data_dir, read_json, write_json
from backend.schemas import (
    EpisodeCreate,
    EpisodeRead,
    EpisodeUpdate,
    EpisodeProgressUpdateCreate,
    EpisodeProgressUpdateRead,
)

router = APIRouter(prefix="", tags=["episodes"])

EPISODES_FILENAME = "episodes.json"
EPISODE_UPDATES_FILENAME = "episode_updates.json"


def _load_episodes() -> List[dict]:
    return read_json(settings.data_dir, EPISODES_FILENAME, default=[]) or []


def _load_updates() -> List[dict]:
    return read_json(settings.data_dir, EPISODE_UPDATES_FILENAME, default=[]) or []


@router.get("/episodes", response_model=List[EpisodeRead])
def list_episodes():
    """List all recovery episodes."""
    return _load_episodes()


@router.post("/episodes", response_model=EpisodeRead, status_code=201)
def create_episode(episode: EpisodeCreate):
    """Create a new recovery episode."""
    episodes = _load_episodes()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid4()),
        "created_at": now,
        "updated_at": now,
        **episode.model_dump(),
    }
    episodes.append(record)
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, EPISODES_FILENAME, episodes)
    return EpisodeRead(**record)


@router.get("/episodes/{episode_id}", response_model=EpisodeRead)
def get_episode(episode_id: str):
    """Get a single recovery episode by ID."""
    episodes = _load_episodes()
    for ep in episodes:
        if ep["id"] == episode_id:
            return EpisodeRead(**ep)
    raise HTTPException(status_code=404, detail="Episode not found")


@router.put("/episodes/{episode_id}", response_model=EpisodeRead)
def update_episode(episode_id: str, episode: EpisodeUpdate):
    """Update an existing recovery episode. Preserves created_at, refreshes updated_at."""
    episodes = _load_episodes()
    for idx, ep in enumerate(episodes):
        if ep["id"] == episode_id:
            merged = dict(ep)
            updates = episode.model_dump(exclude_unset=True)
            merged.update(updates)

            # Validate date ordering on the merged record before persistence
            start_val = merged.get("start_date")
            end_val = merged.get("end_date")
            if start_val is not None and end_val is not None:
                start_dt = datetime.fromisoformat(start_val) if isinstance(start_val, str) else start_val
                end_dt = datetime.fromisoformat(end_val) if isinstance(end_val, str) else end_val
                if start_dt.tzinfo is not None and end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=start_dt.tzinfo)
                elif start_dt.tzinfo is None and end_dt.tzinfo is not None:
                    start_dt = start_dt.replace(tzinfo=end_dt.tzinfo)
                if end_dt < start_dt:
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

            merged["updated_at"] = datetime.now(timezone.utc).isoformat()
            # created_at is preserved from the existing record
            episodes[idx] = merged
            ensure_data_dir(settings.data_dir)
            write_json(settings.data_dir, EPISODES_FILENAME, episodes)
            return EpisodeRead(**merged)
    raise HTTPException(status_code=404, detail="Episode not found")


@router.delete("/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: str):
    """Delete a recovery episode."""
    episodes = _load_episodes()
    filtered = [ep for ep in episodes if ep["id"] != episode_id]
    if len(filtered) == len(episodes):
        raise HTTPException(status_code=404, detail="Episode not found")
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, EPISODES_FILENAME, filtered)
    # Also delete all associated progress updates
    updates = _load_updates()
    remaining_updates = [u for u in updates if u["episode_id"] != episode_id]
    write_json(settings.data_dir, EPISODE_UPDATES_FILENAME, remaining_updates)
    return None


# --- Episode Progress Updates ---

@router.get("/episodes/{episode_id}/updates", response_model=List[EpisodeProgressUpdateRead])
def list_episode_updates(episode_id: str):
    """List all progress updates for an episode, ordered by update_date ascending."""
    episodes = _load_episodes()
    if not any(ep["id"] == episode_id for ep in episodes):
        raise HTTPException(status_code=404, detail="Episode not found")
    updates = _load_updates()
    episode_updates = [u for u in updates if u["episode_id"] == episode_id]
    episode_updates.sort(key=lambda u: u.get("update_date", ""))
    return [EpisodeProgressUpdateRead(**u) for u in episode_updates]


@router.post("/episodes/{episode_id}/updates", response_model=EpisodeProgressUpdateRead, status_code=201)
def create_episode_update(episode_id: str, update: EpisodeProgressUpdateCreate):
    """Add a progress update to an episode."""
    episodes = _load_episodes()
    if not any(ep["id"] == episode_id for ep in episodes):
        raise HTTPException(status_code=404, detail="Episode not found")

    updates = _load_updates()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid4()),
        "episode_id": episode_id,
        "created_at": now,
        **update.model_dump(),
    }
    updates.append(record)
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, EPISODE_UPDATES_FILENAME, updates)
    return EpisodeProgressUpdateRead(**record)


@router.delete("/episodes/{episode_id}/updates/{update_id}", status_code=204)
def delete_episode_update(episode_id: str, update_id: str):
    """Delete a specific progress update from an episode."""
    episodes = _load_episodes()
    if not any(ep["id"] == episode_id for ep in episodes):
        raise HTTPException(status_code=404, detail="Episode not found")
    updates = _load_updates()
    filtered = [u for u in updates if not (u["id"] == update_id and u["episode_id"] == episode_id)]
    if len(filtered) == len(updates):
        raise HTTPException(status_code=404, detail="Update not found")
    ensure_data_dir(settings.data_dir)
    write_json(settings.data_dir, EPISODE_UPDATES_FILENAME, filtered)
    return None
