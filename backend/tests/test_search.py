import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


def test_search_by_query_text():
    response = client.get("/api/search?q=wireless+keyboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    # Top result should match "Wireless Mechanical Keyboard"
    titles = [item["title"] for item in data["results"]]
    assert "Wireless Mechanical Keyboard" in titles


def test_search_with_category_filter():
    response = client.get("/api/search?category=Audio")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["results"]:
        assert item["category"] == "Audio"


def test_search_with_price_filter():
    response = client.get("/api/search?min_price=50&max_price=100")
    assert response.status_code == 200
    data = response.json()
    for item in data["results"]:
        assert 50 <= item["price"] <= 100


def test_search_invalid_price_range():
    response = client.get("/api/search?min_price=100&max_price=50")
    assert response.status_code == 400


def test_search_with_sorting():
    response = client.get("/api/search?sort_by=price_asc")
    assert response.status_code == 200
    prices = [item["price"] for item in response.json()["results"]]
    assert prices == sorted(prices)


def test_get_product_by_id():
    response = client.get("/api/products/prod-001")
    assert response.status_code == 200
    item = response.json()
    assert item["id"] == "prod-001"
    assert "Wireless Mechanical Keyboard" in item["title"]


def test_get_product_not_found():
    response = client.get("/api/products/prod-unknown")
    assert response.status_code == 404

