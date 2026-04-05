"""Booking API tests."""

from datetime import datetime, timezone, timedelta


def test_create_booking(client, customer_headers, shop, menu):
    future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    res = client.post("/api/bookings", json={
        "shop_id": str(shop.id),
        "menu_id": str(menu.id),
        "booking_time": future,
        "request_original": "I have sensitive skin",
    }, headers=customer_headers)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "pending"
    assert "id" in data


def test_create_booking_missing_fields(client, customer_headers):
    res = client.post("/api/bookings", json={}, headers=customer_headers)
    assert res.status_code == 400


def test_create_booking_no_auth(client, shop, menu):
    future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    res = client.post("/api/bookings", json={
        "shop_id": str(shop.id),
        "menu_id": str(menu.id),
        "booking_time": future,
    })
    assert res.status_code == 401


def test_list_my_bookings(client, customer_headers, shop, menu):
    future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    client.post("/api/bookings", json={
        "shop_id": str(shop.id),
        "menu_id": str(menu.id),
        "booking_time": future,
    }, headers=customer_headers)

    res = client.get("/api/bookings", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1


def test_cancel_booking(client, customer_headers, shop, menu):
    future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    create_res = client.post("/api/bookings", json={
        "shop_id": str(shop.id),
        "menu_id": str(menu.id),
        "booking_time": future,
    }, headers=customer_headers)
    booking_id = create_res.get_json()["id"]

    res = client.post(f"/api/bookings/{booking_id}/cancel", headers=customer_headers)
    assert res.status_code == 200
    assert res.get_json()["status"] == "cancelled"
