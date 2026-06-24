from tests.conftest import REGISTER_PAYLOAD


# ════════════════════════════════════════════════════════════════════════════
# Register
# ════════════════════════════════════════════════════════════════════════════

def test_register_success(client):
    resp = client.post("/api/v1/users/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["username"] == REGISTER_PAYLOAD["username"]
    assert data["role"] == "SELLER"
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    client.post("/api/v1/users/register", json=REGISTER_PAYLOAD)
    resp = client.post("/api/v1/users/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409
    assert "Email" in resp.json()["detail"]


def test_register_duplicate_username(client):
    client.post("/api/v1/users/register", json=REGISTER_PAYLOAD)
    payload = {**REGISTER_PAYLOAD, "email": "other@solar.io", "wallet_address": None}
    resp = client.post("/api/v1/users/register", json=payload)
    assert resp.status_code == 409


def test_register_password_mismatch(client):
    payload = {**REGISTER_PAYLOAD, "confirm_password": "WrongPass1!"}
    resp = client.post("/api/v1/users/register", json=payload)
    assert resp.status_code == 422


def test_register_invalid_wallet(client):
    payload = {**REGISTER_PAYLOAD, "wallet_address": "not-an-eth-address"}
    resp = client.post("/api/v1/users/register", json=payload)
    assert resp.status_code == 422


# ════════════════════════════════════════════════════════════════════════════
# Login
# ════════════════════════════════════════════════════════════════════════════

def _register_and_login(client):
    client.post("/api/v1/users/register", json=REGISTER_PAYLOAD)
    resp = client.post("/api/v1/users/login", json={
        "email": REGISTER_PAYLOAD["email"],
        "password": REGISTER_PAYLOAD["password"],
    })
    assert resp.status_code == 200
    return resp.json()


def test_login_success(client):
    token_data = _register_and_login(client)
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["email"] == REGISTER_PAYLOAD["email"]


def test_login_wrong_password(client):
    client.post("/api/v1/users/register", json=REGISTER_PAYLOAD)
    resp = client.post("/api/v1/users/login", json={
        "email": REGISTER_PAYLOAD["email"],
        "password": "WrongPass!1",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/v1/users/login", json={
        "email": "nobody@solar.io",
        "password": "whatever",
    })
    assert resp.status_code == 401


# ════════════════════════════════════════════════════════════════════════════
# Protected endpoints
# ════════════════════════════════════════════════════════════════════════════

def _auth_header(client) -> dict:
    data = _register_and_login(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


def test_get_me(client):
    headers = _auth_header(client)
    resp = client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == REGISTER_PAYLOAD["email"]


def test_get_me_no_token(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_update_user(client):
    headers = _auth_header(client)
    me = client.get("/api/v1/users/me", headers=headers).json()
    resp = client.patch(f"/api/v1/users/{me['id']}", headers=headers, json={"city": "Toronto"})
    assert resp.status_code == 200
    assert resp.json()["city"] == "Toronto"


def test_change_password(client):
    headers = _auth_header(client)
    me = client.get("/api/v1/users/me", headers=headers).json()
    resp = client.post(f"/api/v1/users/{me['id']}/change-password", headers=headers, json={
        "current_password": REGISTER_PAYLOAD["password"],
        "new_password": "NewStr0ng!Pass",
        "confirm_new_password": "NewStr0ng!Pass",
    })
    assert resp.status_code == 200
    assert resp.json()["message"] == "Password updated successfully"


def test_deactivate_user(client):
    headers = _auth_header(client)
    me = client.get("/api/v1/users/me", headers=headers).json()
    resp = client.post(f"/api/v1/users/{me['id']}/deactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


# ════════════════════════════════════════════════════════════════════════════
# Health
# ════════════════════════════════════════════════════════════════════════════

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

