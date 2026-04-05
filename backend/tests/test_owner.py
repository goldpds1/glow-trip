"""Owner dashboard API tests."""

from datetime import datetime, timezone, timedelta

from app import db as _db
from app.models import Booking


def test_owner_shops(client, owner_headers, shop):
    res = client.get("/api/owner/shops", headers=owner_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["shops"]) == 1
    assert data["shops"][0]["name"] == "Test Spa"


def test_owner_shops_forbidden_for_customer(client, customer_headers):
    res = client.get("/api/owner/shops", headers=customer_headers)
    assert res.status_code == 403


def test_owner_bookings(client, app, owner_headers, shop, menu, customer):
    with app.app_context():
        booking = Booking(
            user_id=customer.id,
            shop_id=shop.id,
            menu_id=menu.id,
            booking_time=datetime.now(timezone.utc) + timedelta(days=1),
            status="pending",
        )
        _db.session.add(booking)
        _db.session.commit()

    res = client.get(f"/api/owner/shops/{shop.id}/bookings", headers=owner_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1


def test_owner_change_status(client, app, owner_headers, shop, menu, customer):
    with app.app_context():
        booking = Booking(
            user_id=customer.id,
            shop_id=shop.id,
            menu_id=menu.id,
            booking_time=datetime.now(timezone.utc) + timedelta(days=1),
            status="pending",
        )
        _db.session.add(booking)
        _db.session.commit()
        booking_id = str(booking.id)

    res = client.patch(f"/api/owner/bookings/{booking_id}/status",
                       json={"status": "confirmed"},
                       headers=owner_headers)
    assert res.status_code == 200
    assert res.get_json()["status"] == "confirmed"


def test_owner_settlements(client, owner_headers, shop):
    res = client.get(f"/api/owner/shops/{shop.id}/settlements", headers=owner_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "total_sales" in data
    assert "total_settlement" in data
    assert "fee_rate" in data
