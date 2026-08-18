"""
Unit and Integration Tests for Product Price Analysis, Guardrails, Provenance, and Apply Flow.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def auth_client():
    client = TestClient(app)
    uid = uuid.uuid4().hex[:8]
    email = f"analysis_tester_{uid}@example.com"
    pwd = "securepassword123"
    reg_resp = client.post("/api/auth/register", json={"email": email, "password": pwd, "display_name": "Analyst"})
    cookie = reg_resp.cookies.get("auraprice_session")
    return TestClient(app, cookies={"auraprice_session": cookie})

def test_complete_analysis_and_apply_flow(auth_client):
    # 1. Create a product
    prod_resp = auth_client.post("/api/products", json={
        "product_name": "Premium Cotton Bedding Set",
        "category": "Home & Kitchen",
        "cost_price": 1200.0,
        "current_price": 1899.0,
        "mrp": 2999.0,
        "stock_quantity": 40,
        "average_daily_sales": 5.0,
        "competitor_price": 1799.0,
        "competitor_name": "Flipkart"
    })
    assert prod_resp.status_code == 201
    prod = prod_resp.json()
    product_id = prod["product_id"]

    # 2. Run Analysis
    analyze_resp = auth_client.post(f"/api/products/{product_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    assert "analysis_id" in analysis
    assert "recommended_price" in analysis
    assert analysis["recommended_price"] >= prod["cost_price"] * 1.055
    assert analysis["confidence_level"] in ["high", "medium", "low"]
    assert len(analysis["insights"]) > 0
    assert "feature_provenance" in analysis
    assert analysis["feature_provenance"]["Cost_Price"] == "USER_INPUT"
    assert analysis["status"] == "pending"

    analysis_id = analysis["analysis_id"]

    # 3. Apply Recommendation
    apply_resp = auth_client.put(f"/api/analyses/{analysis_id}/apply")
    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()
    assert apply_data["status"] == "applied"
    assert apply_data["new_price"] == analysis["recommended_price"]

    # 4. Verify product's current_price in database was updated
    prod_check = auth_client.get(f"/api/products/{product_id}")
    assert prod_check.status_code == 200
    assert prod_check.json()["current_price"] == analysis["recommended_price"]

    # 5. Verify analysis status changed in database
    analyses_list = auth_client.get(f"/api/products/{product_id}/analyses")
    assert analyses_list.status_code == 200
    matching = [a for a in analyses_list.json() if a["analysis_id"] == analysis_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "applied"

def test_missing_data_confidence_classification(auth_client):
    # Minimal product (no competitor price, no stock, no orders)
    prod_resp = auth_client.post("/api/products", json={
        "product_name": "Minimal Specs Product",
        "category": "Fashion",
        "cost_price": 500.0,
        "current_price": 999.0,
        "mrp": 1499.0
    })
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["product_id"]

    analyze_resp = auth_client.post(f"/api/products/{prod_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    # Confidence must be LOW or MEDIUM because key business inputs are missing
    assert analysis["confidence_level"] in ["medium", "low"]
    assert any("Competitor price unavailable" in d for d in analysis["confidence_details"])
    assert analysis["competitor_gap_pct"] is None
    assert analysis["stock_runway_days"] is None

def test_store_location_in_analysis(auth_client):
    # Product with Surat location
    prod_resp = auth_client.post("/api/products", json={
        "product_name": "Surat Silk Saree Collection",
        "category": "Fashion",
        "location": "Surat",
        "cost_price": 2000.0,
        "current_price": 3499.0,
        "mrp": 4999.0,
        "competitor_price": 3299.0,
        "stock_quantity": 50,
        "average_daily_sales": 4.0
    })
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["product_id"]

    analyze_resp = auth_client.post(f"/api/products/{prod_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    assert any("Store location verified (Surat)" in d for d in analysis["confidence_details"])
    assert analysis["feature_provenance"]["City_Code"] == "USER_INPUT"
    assert "topology_curve" in analysis
    assert len(analysis["topology_curve"]) > 0

