"""Phase 13: Admin API tests."""
from datetime import datetime, timezone

from app import db as _db
from app.models import Booking, Payment


def _create_booking(customer, shop, menu, status="pending"):
    booking = Booking(
        user_id=customer.id,
        shop_id=shop.id,
        menu_id=menu.id,
        booking_time=datetime(2025, 7, 1, 10, 0, tzinfo=timezone.utc),
        status=status,
    )
    _db.session.add(booking)
    _db.session.flush()
    payment = Payment(
        booking_id=booking.id,
        amount=menu.price,
        currency="KRW",
        payment_status="captured" if status == "completed" else "pending",
        paid_at=datetime(2025, 7, 1, 11, 0, tzinfo=timezone.utc) if status == "completed" else None,
    )
    _db.session.add(payment)
    _db.session.commit()
    _db.session.refresh(booking)
    return booking


# ── Users ──────────────────────────────────────────────


def test_admin_list_users(client, admin_headers, customer, owner):
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 3  # admin + customer + owner


def test_admin_list_users_filter_role(client, admin_headers, customer, owner):
    res = client.get("/api/admin/users?role=customer", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert all(u["role"] == "customer" for u in data["users"])


def test_admin_list_users_search(client, admin_headers, customer):
    res = client.get("/api/admin/users?keyword=customer", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1


def test_admin_update_user_role(client, admin_headers, customer):
    res = client.patch(
        f"/api/admin/users/{customer.id}",
        json={"role": "owner"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["role"] == "owner"


def test_admin_update_user_invalid_role(client, admin_headers, customer):
    res = client.patch(
        f"/api/admin/users/{customer.id}",
        json={"role": "superadmin"},
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_admin_users_forbidden_for_customer(client, customer_headers):
    res = client.get("/api/admin/users", headers=customer_headers)
    assert res.status_code == 403


def test_admin_users_forbidden_for_owner(client, owner_headers):
    res = client.get("/api/admin/users", headers=owner_headers)
    assert res.status_code == 403


# ── Shops ──────────────────────────────────────────────


def test_admin_list_shops(client, admin_headers, shop):
    res = client.get("/api/admin/shops", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    assert "owner_email" in data["shops"][0]


def test_admin_toggle_shop_active(client, admin_headers, shop):
    # Deactivate
    res = client.patch(
        f"/api/admin/shops/{shop.id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["is_active"] is False

    # Reactivate
    res = client.patch(
        f"/api/admin/shops/{shop.id}",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["is_active"] is True


def test_admin_shop_not_found(client, admin_headers):
    res = client.patch(
        "/api/admin/shops/00000000-0000-0000-0000-000000000000",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert res.status_code == 404


# ── Bookings ───────────────────────────────────────────


def test_admin_list_bookings(client, admin_headers, customer, shop, menu):
    _create_booking(customer, shop, menu)
    res = client.get("/api/admin/bookings", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    assert "user_email" in data["bookings"][0]


def test_admin_list_bookings_filter_status(client, admin_headers, customer, shop, menu):
    _create_booking(customer, shop, menu, status="completed")
    res = client.get("/api/admin/bookings?status=completed", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert all(b["status"] == "completed" for b in data["bookings"])


def test_admin_cancel_booking(client, admin_headers, customer, shop, menu):
    booking = _create_booking(customer, shop, menu, status="confirmed")
    res = client.post(
        f"/api/admin/bookings/{booking.id}/cancel",
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "cancelled"


def test_admin_cancel_completed_booking(client, admin_headers, customer, shop, menu):
    booking = _create_booking(customer, shop, menu, status="completed")
    res = client.post(
        f"/api/admin/bookings/{booking.id}/cancel",
        headers=admin_headers,
    )
    assert res.status_code == 400


# ── Settlements ────────────────────────────────────────


def test_admin_settlements(client, admin_headers, customer, shop, menu):
    _create_booking(customer, shop, menu, status="completed")
    res = client.get("/api/admin/settlements", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["grand_total_sales"] >= 50000
    assert len(data["shops"]) >= 1


def test_admin_settlements_empty(client, admin_headers):
    res = client.get("/api/admin/settlements", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["grand_total_sales"] == 0
    assert data["shops"] == []


# ── Stats ──────────────────────────────────────────────


def test_admin_stats(client, admin_headers, customer, shop, menu):
    _create_booking(customer, shop, menu, status="completed")
    res = client.get("/api/admin/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_users"] >= 1
    assert data["total_shops"] >= 1
    assert data["total_bookings"] >= 1
    assert "status_counts" in data
    assert "daily_bookings" in data
    assert len(data["daily_bookings"]) == 7
    assert "popular_shops" in data


def test_admin_stats_forbidden(client, customer_headers):
    res = client.get("/api/admin/stats", headers=customer_headers)
    assert res.status_code == 403
