"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient backed by the application."""
    return TestClient(app)
