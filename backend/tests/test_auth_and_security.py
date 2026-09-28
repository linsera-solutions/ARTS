import pytest
from app.db.init_db import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASS


def test_unauthenticated_requests_blocked(unauthenticated_client):
    """
    Verifies that all internal candidate and recruitment data endpoints
    return 401 Unauthorized when requested without a Bearer token.
    """
    # 1. Applications listing
    res1 = unauthenticated_client.get("/api/v1/applications")
    assert res1.status_code == 401
    assert "token required" in res1.json()["error"]["message"].lower()

    # 2. Roles listing
    res2 = unauthenticated_client.get("/api/v1/roles")
    assert res2.status_code == 401

    # 3. Team Overview
    res3 = unauthenticated_client.get("/api/v1/teams/overview")
    assert res3.status_code == 401

    # 4. Evaluations Criteria
    res4 = unauthenticated_client.get("/api/v1/evaluations/criteria")
    assert res4.status_code == 401

    # 5. User Profile /me
    res5 = unauthenticated_client.get("/api/v1/auth/me")
    assert res5.status_code == 401


def test_public_endpoints_accessible_unauthenticated(unauthenticated_client):
    """
    Verifies that public health and intake endpoints are accessible without a user token.
    """
    # Health check is public
    health_res = unauthenticated_client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # Google Forms webhook intake is public (webhook-token driven)
    webhook_res = unauthenticated_client.post(
        "/api/v1/intake/google-forms/webhook",
        json={
            "full_name": "Public Candidate",
            "email": "public.candidate@space.org",
            "role_name": "Game/App Developer",
        },
    )
    assert webhook_res.status_code == 200


def test_recruiter_login_success(unauthenticated_client):
    """
    Verifies successful sign-in with valid Team Lead credentials.
    """
    res = unauthenticated_client.post("/api/v1/auth/login", json={
        "email": DEFAULT_ADMIN_EMAIL,
        "password": DEFAULT_ADMIN_PASS,
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == DEFAULT_ADMIN_EMAIL
    assert data["user"]["user_role"] == "Administrator"

    # Verify token can access protected /auth/me
    token = data["access_token"]
    me_res = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == DEFAULT_ADMIN_EMAIL


def test_recruiter_login_invalid_credentials(unauthenticated_client):
    """
    Verifies that invalid email or password returns 401 without revealing account presence.
    """
    # 1. Wrong password
    res1 = unauthenticated_client.post("/api/v1/auth/login", json={
        "email": DEFAULT_ADMIN_EMAIL,
        "password": "WrongPassword123!",
    })
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json()["error"]["message"]

    # 2. Non-existent email
    res2 = unauthenticated_client.post("/api/v1/auth/login", json={
        "email": "nonexistent@nasa.org",
        "password": DEFAULT_ADMIN_PASS,
    })
    assert res2.status_code == 401
    assert "Invalid email or password" in res2.json()["error"]["message"]


def test_forged_or_invalid_token_rejected(unauthenticated_client):
    """
    Verifies that malformed or forged JWT tokens return 401 Unauthorized.
    """
    res = unauthenticated_client.get(
        "/api/v1/applications",
        headers={"Authorization": "Bearer forged.invalid.token.structure"},
    )
    assert res.status_code == 401
    assert "Invalid, expired, or forged" in res.json()["error"]["message"]


def test_logout_endpoint(client):
    """
    Verifies POST /api/v1/auth/logout succeeds for authenticated session.
    """
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert "signed out" in res.json()["message"].lower()