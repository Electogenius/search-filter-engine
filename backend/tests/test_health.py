import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend package can be imported directly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that the health check endpoint returns 200 OK and expected status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "search-filter-engine"
    assert "version" in data


def test_root_endpoint():
    """Verify root endpoint is reachable."""
    response = client.get("/")
    assert response.status_code == 200
    assert "docs" in response.json()


def test_placeholder_endpoints_return_501():
    """Verify suggest and related endpoints return 501 Not Implemented."""
    suggest_resp = client.get("/api/suggest?prefix=key")
    assert suggest_resp.status_code == 501

    related_resp = client.get("/api/products/prod-001/related")
    assert related_resp.status_code == 501

