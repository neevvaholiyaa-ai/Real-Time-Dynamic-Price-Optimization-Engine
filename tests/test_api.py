"""
Integration Tests for Common FastAPI Endpoints (Health, Categories, Stateless Simulation).
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "version" in data

def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "AuraPrice" in response.text or "Dynamic" in response.text

def test_categories_endpoint():
    response = client.get("/api/categories")
    assert response.status_code == 200
    cats = response.json()
    assert isinstance(cats, list)
    assert len(cats) >= 8
    cat_names = [c["category"] for c in cats]
    assert "Electronics" in cat_names
    assert "Grocery" in cat_names

def test_stateless_predict_simulation():
    payload = {
        "product_id": "PROD-SIM-001",
        "product_name": "What-If Wireless Earbuds",
        "category": "Electronics",
        "cost_price": 1200.0,
        "current_price": 1999.0,
        "mrp": 2499.0,
        "competitor_avg_price": 1899.0,
        "stock_level": 30,
        "orders": 15
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_price" in data
    assert "price_change" in data
    assert "recommendation" in data
    assert "topology_curve" in data
    assert len(data["topology_curve"]) == 40
    assert len(data["insights"]) > 0
    assert "feature_provenance" in data

def test_predict_invalid_cost_mrp():
    invalid_payload = {
        "product_name": "Impossible Pricing",
        "cost_price": 3000.0,
        "current_price": 2500.0,
        "mrp": 2000.0  # Cost > MRP
    }
    response = client.post("/predict", json=invalid_payload)
    assert response.status_code == 400
