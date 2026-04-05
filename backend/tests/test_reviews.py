"""Phase 12: Review / rating system tests."""
from datetime import datetime, timezone

from app import db as _db
from app.models import Booking, Payment, Review


def _create_completed_booking(customer, shop, menu):
    """Helper: create a completed booking with payment."""
    booking = Booking(
        user_id=customer.id,
        shop_id=shop.id,
        menu_id=menu.id,
        booking_time=datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
        status="completed",
    )
    _db.session.add(booking)
    _db.session.flush()
    payment = Payment(
        booking_id=booking.id,
        amount=menu.price,
        currency="KRW",
        payment_status="captured",
    )
    _db.session.add(payment)
    _db.session.commit()
    _db.session.refresh(booking)
    return booking


# ── Create Review ──────────────────────────────────────


def test_create_review(client, customer, customer_headers, shop, menu):
    booking = _create_completed_booking(customer, shop, menu)
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5, "comment": "Great!"},
        headers=customer_headers,
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["rating"] == 5
    assert data["comment"] == "Great!"


def test_create_review_no_comment(client, customer, customer_headers, shop, menu):
    booking = _create_completed_booking(customer, shop, menu)
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 4},
        headers=customer_headers,
    )
    assert res.status_code == 201
    assert res.get_json()["rating"] == 4


def test_create_review_invalid_rating(client, customer, customer_headers, shop, menu):
    booking = _create_completed_booking(customer, shop, menu)
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 6},
        headers=customer_headers,
    )
    assert res.status_code == 400


def test_create_review_not_completed(client, customer, customer_headers, shop, menu):
    """Cannot review a pending booking."""
    booking = Booking(
        user_id=customer.id,
        shop_id=shop.id,
        menu_id=menu.id,
        booking_time=datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
        status="pending",
    )
    _db.session.add(booking)
    _db.session.commit()
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5},
        headers=customer_headers,
    )
    assert res.status_code == 400
    assert "completed" in res.get_json()["error"].lower()


def test_create_review_duplicate(client, customer, customer_headers, shop, menu):
    """Cannot review same booking twice."""
    booking = _create_completed_booking(customer, shop, menu)
    client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5},
        headers=customer_headers,
    )
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 4},
        headers=customer_headers,
    )
    assert res.status_code == 400
    assert "already" in res.get_json()["error"].lower()


def test_create_review_not_own_booking(client, customer, owner, owner_headers, shop, menu):
    """Cannot review someone else's booking."""
    booking = _create_completed_booking(customer, shop, menu)
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5},
        headers=owner_headers,
    )
    assert res.status_code == 403


def test_create_review_unauthenticated(client, customer, shop, menu):
    booking = _create_completed_booking(customer, shop, menu)
    res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5},
    )
    assert res.status_code == 401


# ── Shop Reviews ───────────────────────────────────────


def test_shop_reviews_list(client, customer, customer_headers, shop, menu):
    booking = _create_completed_booking(customer, shop, menu)
    client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 4, "comment": "Nice"},
        headers=customer_headers,
    )
    res = client.get(f"/api/shops/{shop.id}/reviews")
    assert res.status_code == 200
    data = res.get_json()
    assert data["avg_rating"] == 4.0
    assert data["review_count"] == 1
    assert len(data["reviews"]) == 1
    assert data["reviews"][0]["rating"] == 4


def test_shop_reviews_empty(client, shop):
    res = client.get(f"/api/shops/{shop.id}/reviews")
    assert res.status_code == 200
    data = res.get_json()
    assert data["avg_rating"] == 0
    assert data["review_count"] == 0
    assert data["reviews"] == []


def test_shop_avg_rating_in_list(client, customer, customer_headers, shop, menu):
    """avg_rating should appear in shop list."""
    booking = _create_completed_booking(customer, shop, menu)
    client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5},
        headers=customer_headers,
    )
    res = client.get("/api/shops")
    data = res.get_json()
    assert data["shops"][0]["avg_rating"] == 5.0


def test_has_review_in_bookings(client, customer, customer_headers, shop, menu):
    """has_review flag in booking list."""
    booking = _create_completed_booking(customer, shop, menu)
    # Before review
    res = client.get("/api/bookings", headers=customer_headers)
    data = res.get_json()
    assert data["bookings"][0]["has_review"] is False

    # After review
    client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5},
        headers=customer_headers,
    )
    res = client.get("/api/bookings", headers=customer_headers)
    data = res.get_json()
    assert data["bookings"][0]["has_review"] is True
