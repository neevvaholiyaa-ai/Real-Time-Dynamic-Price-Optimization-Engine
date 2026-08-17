"""
Unit and Integration Tests for User Authentication and Session Management.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_register_and_login_flow():
    client = TestClient(app)
    uid = uuid.uuid4().hex[:8]
    email = f"auth_user_{uid}@example.com"
    pwd = "securepassword123"

    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "display_name": "Auth Test User"
    })
    assert reg_resp.status_code == 200
    user_data = reg_resp.json()
    assert "user_id" in user_data
    assert user_data["email"] == email
    assert user_data["display_name"] == "Auth Test User"
    assert "auraprice_session" in reg_resp.cookies

    session_cookie = reg_resp.cookies.get("auraprice_session")
    auth_client = TestClient(app, cookies={"auraprice_session": session_cookie})

    # 2. Get Me with session cookie
    me_resp = auth_client.get("/api/auth/me")
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user_id"] == user_data["user_id"]
    assert me_data["email"] == email

    # 3. Duplicate registration should fail
    dup_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd
    })
    assert dup_resp.status_code == 400

    # 4. Login with correct credentials
    login_resp = client.post("/api/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["user_id"] == user_data["user_id"]

    # 5. Login with invalid password
    bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401

    # 6. Unauthenticated /api/auth/me fails
    unauth_client = TestClient(app)
    unauth_resp = unauth_client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # 7. Logout clears cookie
    logout_resp = auth_client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
