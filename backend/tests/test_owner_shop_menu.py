"""Phase 8: Shop update + Menu CRUD tests."""

from app import db as _db
from app.models import Menu


# ── Shop Update ────────────────────────────────────────

def test_update_shop(client, owner_headers, shop):
    res = client.patch(f"/api/owner/shops/{shop.id}", json={
        "name": "Updated Spa",
        "address": "Busan, Korea",
        "phone": "010-9999-0000",
        "description": "New description",
    }, headers=owner_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Updated Spa"
    assert data["address"] == "Busan, Korea"
    assert data["phone"] == "010-9999-0000"
    assert data["description"] == "New description"


def test_update_shop_partial(client, owner_headers, shop):
    res = client.patch(f"/api/owner/shops/{shop.id}", json={
        "phone": "010-1111-2222",
    }, headers=owner_headers)
    assert res.status_code == 200
    assert res.get_json()["phone"] == "010-1111-2222"
    assert res.get_json()["name"] == "Test Spa"


def test_update_shop_not_owner(client, customer_headers, shop):
    res = client.patch(f"/api/owner/shops/{shop.id}", json={
        "name": "Hacked",
    }, headers=customer_headers)
    assert res.status_code == 403


def test_update_shop_not_found(client, owner_headers):
    res = client.patch("/api/owner/shops/00000000-0000-0000-0000-000000000000", json={
        "name": "Ghost",
    }, headers=owner_headers)
    assert res.status_code == 404


# ── Menu Create ────────────────────────────────────────

def test_create_menu(client, owner_headers, shop):
    res = client.post(f"/api/owner/shops/{shop.id}/menus", json={
        "title": "Deep Cleansing",
        "description": "90min deep cleansing facial",
        "price": 80000,
        "duration": 90,
    }, headers=owner_headers)
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Deep Cleansing"
    assert data["price"] == 80000
    assert data["duration"] == 90
    assert "id" in data


def test_create_menu_missing_fields(client, owner_headers, shop):
    res = client.post(f"/api/owner/shops/{shop.id}/menus", json={
        "title": "Incomplete",
    }, headers=owner_headers)
    assert res.status_code == 400


def test_create_menu_not_owner(client, customer_headers, shop):
    res = client.post(f"/api/owner/shops/{shop.id}/menus", json={
        "title": "Hijack", "price": 1000, "duration": 30,
    }, headers=customer_headers)
    assert res.status_code == 403


# ── Menu Update ────────────────────────────────────────

def test_update_menu(client, owner_headers, menu):
    res = client.patch(f"/api/owner/menus/{menu.id}", json={
        "title": "Premium Facial",
        "price": 70000,
    }, headers=owner_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["title"] == "Premium Facial"
    assert data["price"] == 70000


def test_update_menu_not_owner(client, customer_headers, menu):
    res = client.patch(f"/api/owner/menus/{menu.id}", json={
        "title": "Hacked",
    }, headers=customer_headers)
    assert res.status_code == 403


def test_update_menu_not_found(client, owner_headers):
    res = client.patch("/api/owner/menus/00000000-0000-0000-0000-000000000000", json={
        "title": "Ghost",
    }, headers=owner_headers)
    assert res.status_code == 404


# ── Menu Delete ────────────────────────────────────────

def test_delete_menu(client, app, owner_headers, menu):
    menu_id = str(menu.id)
    res = client.delete(f"/api/owner/menus/{menu_id}", headers=owner_headers)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Menu deleted"

    with app.app_context():
        assert Menu.query.get(menu_id) is None


def test_delete_menu_not_owner(client, customer_headers, menu):
    res = client.delete(f"/api/owner/menus/{menu.id}", headers=customer_headers)
    assert res.status_code == 403


def test_delete_menu_not_found(client, owner_headers):
    res = client.delete("/api/owner/menus/00000000-0000-0000-0000-000000000000",
                        headers=owner_headers)
    assert res.status_code == 404
