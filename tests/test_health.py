"""Health check endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint returns OK status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["name"] == "HaloLight API"
    assert "version" in data
    assert "timestamp" in data


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns welcome HTML page."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # Check that the HTML contains expected content
    html_content = response.text
    assert "HaloLight API" in html_content
    assert "<!DOCTYPE html>" in html_content


def test_openapi_docs(client: TestClient) -> None:
    """Test OpenAPI docs are accessible."""
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_redoc_docs(client: TestClient) -> None:
    """Test ReDoc docs are accessible."""
    response = client.get("/api/redoc")
    assert response.status_code == 200
