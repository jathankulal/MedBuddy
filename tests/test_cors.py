"""CORS configuration tests verifying origin validation and header reflection."""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_cors_allowed_origin_reflected_with_credentials():
    """Requests from configured origins get Access-Control-Allow-Origin reflecting the origin."""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_allowed_origin_ip_variant():
    """Requests from 127.0.0.1:5173 are permitted and reflected."""
    response = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin_rejected():
    """Untrusted origins do not receive Access-Control-Allow-Origin headers."""
    response = client.get("/health", headers={"Origin": "http://malicious-attacker.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_allowed_origin():
    """Preflight OPTIONS request from allowed origin returns permitted methods and headers."""
    response = client.options(
        "/documents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
