"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient backed by the application."""
    return TestClient(app)


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Provide a temporary data directory and override settings.data_dir.

    Uses pytest's tmp_path so each test gets a fresh directory. monkeypatch
    restores the original settings.data_dir after the test.
    """
    data_dir = str(tmp_path / "data")
    monkeypatch.setattr(settings, "data_dir", data_dir)
    return data_dir
