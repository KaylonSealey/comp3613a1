"""Integration tests: authentication and role-based authorization (IT01–IT10)."""
import pytest

pytestmark = pytest.mark.integration


def test_login_returns_bearer_token(client):  # IT01
    response = client.post("/api/auth/login", json={"username": "bob", "password": "bobpass"})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["role"] == "regular_user"


def test_login_wrong_password_is_401(client):  # IT02
    response = client.post("/api/auth/login", json={"username": "bob", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_missing_password_is_422(client):  # IT03
    response = client.post("/api/auth/login", json={"username": "bob"})
    assert response.status_code == 422


def test_me_returns_current_user(client, auth):  # IT04
    response = client.get("/api/auth/me", headers=auth("bob"))
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "bob"
    assert body["role"] == "regular_user"
    assert "password" not in body


def test_no_token_returns_json_401(client):  # IT05
    response = client.get("/api/me/plan")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")
    assert "detail" in response.json()


def test_invalid_token_is_401(client):  # IT06
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_web_login_cookie_works_for_api(client):  # IT07
    login = client.post("/login", data={"username": "bob", "password": "bobpass"},
                        follow_redirects=False)
    assert login.status_code == 303
    assert "access_token" in login.cookies
    response = client.get("/api/auth/me")  # no header: the cookie authenticates
    assert response.status_code == 200
    assert response.json()["username"] == "bob"


def test_student_cannot_use_advisor_endpoints(client, auth):  # IT08
    bob = auth("bob")
    assert client.get("/api/advisor/plans", headers=bob).status_code == 403
    decision = client.post("/api/advisor/plans/1/decision", headers=bob,
                           json={"decision": "approve", "notes": ""})
    assert decision.status_code == 403


def test_advisor_cannot_use_student_endpoints(client, auth):  # IT09
    advisor = auth("advisor")
    assert client.get("/api/me/plan", headers=advisor).status_code == 403
    assert client.get("/api/me/audit", headers=advisor).status_code == 403


def test_user_list_is_admin_only(client, auth):  # IT10
    assert client.get("/api/users", headers=auth("bob")).status_code == 403
    response = client.get("/api/users", headers=auth("admin"))
    assert response.status_code == 200
    users = response.json()
    assert {u["username"] for u in users} == {"bob", "alice", "advisor", "advisor2", "admin"}
    assert all("password" not in u for u in users)
