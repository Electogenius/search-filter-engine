import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.recommendations.cooccurrence import CooccurrenceRecommender

client = TestClient(app)

SAMPLE_PRODUCTS = {
    "prod-001": {"id": "prod-001", "title": "Keyboard", "category": "Computers", "price": 89.99, "rating": 4.7, "available": True},
    "prod-002": {"id": "prod-002", "title": "Mouse", "category": "Computers", "price": 45.50, "rating": 4.5, "available": True},
    "prod-003": {"id": "prod-003", "title": "Headphones", "category": "Audio", "price": 179.99, "rating": 4.8, "available": True},
    "prod-010": {"id": "prod-010", "title": "Hub", "category": "Accessories", "price": 34.99, "rating": 4.4, "available": True},
    "prod-999": {"id": "prod-999", "title": "Solo Product", "category": "Misc", "price": 10.0, "rating": 3.0, "available": True},
}

SAMPLE_BASKETS = [
    {"basket_id": "b-1", "items": ["prod-001", "prod-002", "prod-010"]},
    {"basket_id": "b-2", "items": ["prod-001", "prod-002"]},
    {"basket_id": "b-3", "items": ["prod-001", "prod-003"]},
    {"basket_id": "b-4", "items": ["prod-002", "prod-010"]},
]


def test_cooccurrence_matrix_symmetry():
    """Verify that co-occurrence count(A, B) == count(B, A)."""
    rec = CooccurrenceRecommender(baskets_data=SAMPLE_BASKETS, products=SAMPLE_PRODUCTS)

    count_1_2 = rec.get_cooccurrence_count("prod-001", "prod-002")
    count_2_1 = rec.get_cooccurrence_count("prod-002", "prod-001")
    assert count_1_2 == count_2_1 == 2

    count_1_10 = rec.get_cooccurrence_count("prod-001", "prod-010")
    count_10_1 = rec.get_cooccurrence_count("prod-010", "prod-001")
    assert count_1_10 == count_10_1 == 1


def test_recommendation_ranking():
    """Verify products with higher co-occurrence frequency are ranked before lower frequency items."""
    rec = CooccurrenceRecommender(baskets_data=SAMPLE_BASKETS, products=SAMPLE_PRODUCTS)
    recs = rec.get_recommendations("prod-001", limit=4)

    assert len(recs) == 3
    # prod-002 has count 2, prod-010 has count 1, prod-003 has count 1
    assert recs[0]["id"] == "prod-002"
    assert recs[0]["co_occurrence_count"] == 2
    assert recs[1]["co_occurrence_count"] == 1


def test_product_without_baskets():
    """Verify product never appearing in baskets returns empty recommendation list cleanly."""
    rec = CooccurrenceRecommender(baskets_data=SAMPLE_BASKETS, products=SAMPLE_PRODUCTS)
    recs = rec.get_recommendations("prod-999", limit=4)
    assert recs == []


def test_api_related_endpoint_success():
    """Verify GET /api/products/{id}/related returns 200 with matching schema."""
    response = client.get("/api/products/prod-001/related?limit=3")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == "prod-001"
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) <= 3

    if len(data["recommendations"]) > 0:
        first = data["recommendations"][0]
        assert "id" in first
        assert "title" in first
        assert "co_occurrence_count" in first
        assert first["co_occurrence_count"] >= 1


def test_api_related_endpoint_404():
    """Verify GET /api/products/{id}/related returns 404 for non-existent product."""
    response = client.get("/api/products/non-existent-product-id/related")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
