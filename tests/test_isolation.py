"""
Unit and Integration Tests for Strict Multi-User Data Isolation.
Verifies that User A's data is completely invisible and inaccessible to User B across all endpoints.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_multi_user_strict_data_isolation():
    client = TestClient(app)
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]

    # 1. Register User A
    user_a_email = f"user_alpha_{uid_a}@example.com"
    reg_a = client.post("/api/auth/register", json={
        "email": user_a_email,
        "password": "passwordA123",
        "display_name": "Store Alpha"
    })
    cookie_a = reg_a.cookies.get("auraprice_session")
    client_a = TestClient(app, cookies={"auraprice_session": cookie_a})

    # User A creates a product
    prod_a_resp = client_a.post("/api/products", json={
        "product_name": "Alpha Exclusive Laptop",
        "category": "Electronics",
        "cost_price": 50000.0,
        "current_price": 65000.0,
        "mrp": 75000.0,
        "competitor_price": 64000.0
    })
    assert prod_a_resp.status_code == 201
    prod_a = prod_a_resp.json()
    prod_a_id = prod_a["product_id"]

    # User A analyzes the product
    analyze_a = client_a.post(f"/api/products/{prod_a_id}/analyze")
    assert analyze_a.status_code == 200
    analysis_a_id = analyze_a.json()["analysis_id"]

    # 2. Register User B
    user_b_email = f"user_beta_{uid_b}@example.com"
    reg_b = client.post("/api/auth/register", json={
        "email": user_b_email,
        "password": "passwordB123",
        "display_name": "Store Beta"
    })
    cookie_b = reg_b.cookies.get("auraprice_session")
    client_b = TestClient(app, cookies={"auraprice_session": cookie_b})

    # 3. User B lists products -> must be empty (cannot see User A's laptop)
    prods_b_resp = client_b.get("/api/products")
    assert prods_b_resp.status_code == 200
    prods_b = prods_b_resp.json()
    assert len(prods_b) == 0
    assert not any(p["product_id"] == prod_a_id for p in prods_b)

    # 4. User B tries to directly fetch User A's product -> 404
    get_direct = client_b.get(f"/api/products/{prod_a_id}")
    assert get_direct.status_code == 404

    # 5. User B tries to update User A's product -> 404
    update_direct = client_b.put(f"/api/products/{prod_a_id}", json={"current_price": 1000.0})
    assert update_direct.status_code == 404

    # 6. User B tries to delete User A's product -> 404
    del_direct = client_b.delete(f"/api/products/{prod_a_id}")
    assert del_direct.status_code == 404

    # 7. User B tries to analyze User A's product -> 404
    analyze_direct = client_b.post(f"/api/products/{prod_a_id}/analyze")
    assert analyze_direct.status_code == 404

    # 8. User B tries to apply User A's recommendation -> 404
    apply_direct = client_b.put(f"/api/analyses/{analysis_a_id}/apply")
    assert apply_direct.status_code == 404

    # 9. User B dashboard overview & queue must be empty of User A's data
    overview_b = client_b.get("/api/dashboard/overview")
    assert overview_b.status_code == 200
    b_data = overview_b.json()
    assert b_data["products_analyzed_count"] == 0
    assert b_data["pending_actions_count"] == 0

    queue_b = client_b.get("/api/dashboard/queue")
    assert queue_b.status_code == 200
    assert len(queue_b.json()) == 0
