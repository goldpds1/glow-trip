"""Phase 10: Payment API tests."""

from datetime import datetime, timezone, timedelta

from app import db as _db
from app.models import Booking, Payment


def _create_booking_with_payment(app, customer, shop, menu, status="pending", payment_status="pending"):
    with app.app_context():
        booking = Booking(
            user_id=customer.id,
            shop_id=shop.id,
            menu_id=menu.id,
            booking_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=status,
        )
        _db.session.add(booking)
        _db.session.flush()
        payment = Payment(
            booking_id=booking.id,
            amount=menu.price,
            currency="KRW",
            payment_status=payment_status,
        )
        _db.session.add(payment)
        _db.session.commit()
        return str(booking.id)


def test_checkout_no_stripe_key(client, app, customer_headers, customer, shop, menu):
    """Without STRIPE_SECRET_KEY, checkout should return 503."""
    booking_id = _create_booking_with_payment(app, customer, shop, menu)
    res = client.post(f"/api/payments/{booking_id}/checkout", headers=customer_headers)
    assert res.status_code == 503


def test_checkout_not_found(client, customer_headers):
    res = client.post("/api/payments/00000000-0000-0000-0000-000000000000/checkout",
                      headers=customer_headers)
    assert res.status_code == 404


def test_checkout_no_auth(client, app, customer, shop, menu):
    booking_id = _create_booking_with_payment(app, customer, shop, menu)
    res = client.post(f"/api/payments/{booking_id}/checkout")
    assert res.status_code == 401


def test_payment_status(client, app, customer_headers, customer, shop, menu):
    booking_id = _create_booking_with_payment(app, customer, shop, menu)
    res = client.get(f"/api/payments/{booking_id}/status", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["payment_status"] == "pending"
    assert data["amount"] == menu.price


def test_payment_status_not_found(client, customer_headers):
    res = client.get("/api/payments/00000000-0000-0000-0000-000000000000/status",
                     headers=customer_headers)
    assert res.status_code == 404


def test_refund_no_pg_tid(client, app, owner_headers, customer, shop, menu):
    """Refund without pg_tid (no Stripe payment made) should return 400."""
    booking_id = _create_booking_with_payment(app, customer, shop, menu,
                                               payment_status="authorized")
    # Set pg_tid to None to simulate no stripe payment
    with app.app_context():
        booking = Booking.query.get(booking_id)
        booking.payment.pg_tid = None
        _db.session.commit()

    res = client.post(f"/api/payments/{booking_id}/refund", headers=owner_headers)
    assert res.status_code == 400


def test_refund_forbidden_for_customer(client, app, customer_headers, customer, shop, menu):
    booking_id = _create_booking_with_payment(app, customer, shop, menu,
                                               payment_status="authorized")
    res = client.post(f"/api/payments/{booking_id}/refund", headers=customer_headers)
    assert res.status_code == 403


def test_booking_list_includes_payment_info(client, app, customer_headers, customer, shop, menu):
    _create_booking_with_payment(app, customer, shop, menu)
    res = client.get("/api/bookings", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    booking = data["bookings"][0]
    assert "payment_status" in booking
    assert "amount" in booking
