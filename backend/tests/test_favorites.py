"""Favorites API tests."""


def test_toggle_favorite_add(client, customer_headers, shop):
    res = client.post(f"/api/favorites/{shop.id}", headers=customer_headers)
    assert res.status_code == 201
    assert res.get_json()["favorited"] is True


def test_toggle_favorite_remove(client, customer_headers, shop):
    client.post(f"/api/favorites/{shop.id}", headers=customer_headers)
    res = client.post(f"/api/favorites/{shop.id}", headers=customer_headers)
    assert res.status_code == 200
    assert res.get_json()["favorited"] is False


def test_list_favorites(client, customer_headers, shop):
    client.post(f"/api/favorites/{shop.id}", headers=customer_headers)
    res = client.get("/api/favorites", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["shops"]) == 1
    assert data["shops"][0]["id"] == str(shop.id)


def test_list_favorites_empty(client, customer_headers):
    res = client.get("/api/favorites", headers=customer_headers)
    assert res.status_code == 200
    assert len(res.get_json()["shops"]) == 0


def test_check_favorite_true(client, customer_headers, shop):
    client.post(f"/api/favorites/{shop.id}", headers=customer_headers)
    res = client.get(f"/api/favorites/check/{shop.id}", headers=customer_headers)
    assert res.status_code == 200
    assert res.get_json()["favorited"] is True


def test_check_favorite_false(client, customer_headers, shop):
    res = client.get(f"/api/favorites/check/{shop.id}", headers=customer_headers)
    assert res.status_code == 200
    assert res.get_json()["favorited"] is False


def test_toggle_favorite_not_found(client, customer_headers):
    res = client.post(
        "/api/favorites/00000000-0000-0000-0000-000000000000",
        headers=customer_headers,
    )
    assert res.status_code == 404


def test_toggle_favorite_no_auth(client, shop):
    res = client.post(f"/api/favorites/{shop.id}")
    assert res.status_code == 401
