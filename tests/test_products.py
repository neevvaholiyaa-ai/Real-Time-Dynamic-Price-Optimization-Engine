"""
Unit and Integration Tests for Product CRUD and Validation.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def auth_client():
    client = TestClient(app)
    uid = uuid.uuid4().hex[:8]
    email = f"product_tester_{uid}@example.com"
    pwd = "password123"
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "display_name": "Product Tester"
    })
    cookie = reg_resp.cookies.get("auraprice_session")
    return TestClient(app, cookies={"auraprice_session": cookie})

def test_product_crud_lifecycle(auth_client):
    # 1. Create Product
    prod_payload = {
        "product_name": "Ergonomic Office Chair",
        "category": "Home & Kitchen",
        "brand": "ComfortPlus",
        "cost_price": 4500.0,
        "current_price": 7999.0,
        "mrp": 9999.0,
        "stock_quantity": 25,
        "average_daily_sales": 3.5,
        "competitor_price": 7499.0,
        "competitor_name": "Amazon India",
        "business_goal": "maximize_profit"
    }
    create_resp = auth_client.post("/api/products", json=prod_payload)
    assert create_resp.status_code == 201
    prod = create_resp.json()
    product_id = prod["product_id"]
    assert prod["product_name"] == "Ergonomic Office Chair"
    assert prod["cost_price"] == 4500.0

    # 2. List Products
    list_resp = auth_client.get("/api/products")
    assert list_resp.status_code == 200
    prods = list_resp.json()
    assert any(p["product_id"] == product_id for p in prods)

    # 3. Get Single Product
    get_resp = auth_client.get(f"/api/products/{product_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["product_id"] == product_id

    # 4. Update Product
    update_resp = auth_client.put(f"/api/products/{product_id}", json={
        "current_price": 8299.0,
        "stock_quantity": 20
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["current_price"] == 8299.0
    assert update_resp.json()["stock_quantity"] == 20

    # 5. Delete Product
    del_resp = auth_client.delete(f"/api/products/{product_id}")
    assert del_resp.status_code == 200

    # 6. Verify Deleted
    get_after_del = auth_client.get(f"/api/products/{product_id}")
    assert get_after_del.status_code == 404

def test_cost_exceeding_mrp_validation(auth_client):
    invalid_payload = {
        "product_name": "Defective Item",
        "category": "Electronics",
        "cost_price": 10000.0,
        "current_price": 8000.0,
        "mrp": 7000.0  # Cost > MRP
    }
    resp = auth_client.post("/api/products", json=invalid_payload)
    assert resp.status_code == 400
