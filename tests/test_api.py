"""
Integration Tests for FastAPI Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dynamic Pricing" in response.text

def test_catalog_samples_endpoint():
    response = client.get("/api/catalog-samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)
    assert len(samples) > 0
    assert "product_id" in samples[0]

def test_predict_endpoint_valid():
    payload = {
        "product_id": "PROD-ELEC-001",
        "product_name": "Wireless Noise Cancelling Headphones Pro",
        "category": "Electronics",
        "city": "Ahmedabad",
        "cost_price": 2500.0,
        "current_price": 4200.0,
        "mrp": 4999.0,
        "competitor_avg_price": 4150.0,
        "stock_level": 25,
        "orders": 65,
        "days_until_next_festival": 3,
        "weather_type": "Clear",
        "competitor_stock_status": "In_Stock"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_price" in data
    assert "price_change" in data
    assert "recommendation" in data
    assert len(data["insights"]) > 0

def test_predict_endpoint_invalid():
    # Cost price missing
    invalid_payload = {
        "product_name": "Invalid Item",
        "category": "Electronics",
        "current_price": 4200.0
    }
    response = client.post("/predict", json=invalid_payload)
    assert response.status_code == 422
