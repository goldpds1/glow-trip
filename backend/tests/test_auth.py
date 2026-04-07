"""Authentication API tests."""


def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "email": "new@test.com",
        "password": "securepass123",
        "name": "New User",
        "language": "en",
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user_id" in data


def test_register_duplicate_email(client, customer):
    res = client.post("/api/auth/register", json={
        "email": "customer@test.com",
        "password": "securepass123",
    })
    assert res.status_code == 409


def test_register_short_password(client):
    res = client.post("/api/auth/register", json={
        "email": "short@test.com",
        "password": "123",
    })
    assert res.status_code == 400


def test_login_success(client, customer):
    res = client.post("/api/auth/login", json={
        "email": "customer@test.com",
        "password": "password123",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client, customer):
    res = client.post("/api/auth/login", json={
        "email": "customer@test.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_login_nonexistent_email(client):
    res = client.post("/api/auth/login", json={
        "email": "nobody@test.com",
        "password": "whatever",
    })
    assert res.status_code == 401


def test_me_authenticated(client, customer_headers):
    res = client.get("/api/auth/me", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["email"] == "customer@test.com"
    assert data["role"] == "customer"


def test_me_no_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_invalid_token(client):
    res = client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalid.token.here",
    })
    assert res.status_code == 401


def test_refresh_token(client, customer):
    # Login first
    login_res = client.post("/api/auth/login", json={
        "email": "customer@test.com",
        "password": "password123",
    })
    refresh = login_res.get_json()["refresh_token"]

    # Refresh
    res = client.post("/api/auth/refresh", json={
        "refresh_token": refresh,
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data


# ── Profile update tests ────────────────────────────────


def test_update_profile_full(client, customer_headers):
    res = client.patch("/api/auth/me", headers=customer_headers, json={
        "name": "Updated Name",
        "phone": "010-1234-5678",
        "language": "ko",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Updated Name"
    assert data["phone"] == "010-1234-5678"
    assert data["language"] == "ko"


def test_update_profile_partial(client, customer_headers):
    res = client.patch("/api/auth/me", headers=customer_headers, json={
        "name": "Only Name",
    })
    assert res.status_code == 200
    assert res.get_json()["name"] == "Only Name"


def test_update_profile_invalid_language(client, customer_headers):
    res = client.patch("/api/auth/me", headers=customer_headers, json={
        "language": "fr",
    })
    assert res.status_code == 400


def test_update_profile_name_too_long(client, customer_headers):
    res = client.patch("/api/auth/me", headers=customer_headers, json={
        "name": "x" * 101,
    })
    assert res.status_code == 400


def test_update_profile_no_auth(client):
    res = client.patch("/api/auth/me", json={"name": "Hacker"})
    assert res.status_code == 401
