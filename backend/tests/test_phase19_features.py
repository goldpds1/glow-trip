from datetime import datetime, timedelta, timezone

from app import db as _db
from app.models import Booking, Payment, Review, User
from app.auth.jwt_utils import create_tokens


def _create_completed_booking(customer, shop, menu):
    b = Booking(
        user_id=customer.id,
        shop_id=shop.id,
        menu_id=menu.id,
        booking_time=datetime.now(timezone.utc) + timedelta(days=1),
        status="completed",
    )
    _db.session.add(b)
    _db.session.flush()
    _db.session.add(Payment(booking_id=b.id, amount=menu.price, currency="KRW", payment_status="captured"))
    _db.session.commit()
    return b


def test_hold_slot_and_slots_reflect_hold(client, app, customer, customer_headers, shop):
    target = datetime.utcnow() + timedelta(days=1)
    date_str = target.strftime("%Y-%m-%d")
    time_str = "11:00"

    hold_res = client.post(
        f"/api/shops/{shop.id}/slots/hold",
        json={"date": date_str, "time": time_str},
        headers=customer_headers,
    )
    assert hold_res.status_code == 200

    slots_res = client.get(f"/api/shops/{shop.id}/slots?date={date_str}")
    assert slots_res.status_code == 200
    slot = next(s for s in slots_res.get_json()["slots"] if s["time"] == time_str)
    assert slot["available"] is False


def test_reschedule_booking(client, customer_headers, shop, menu):
    t1 = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_res = client.post(
        "/api/bookings",
        json={"shop_id": str(shop.id), "menu_id": str(menu.id), "booking_time": t1},
        headers=customer_headers,
    )
    assert create_res.status_code == 201
    booking_id = create_res.get_json()["id"]

    t2 = (datetime.now(timezone.utc) + timedelta(days=3)).replace(minute=0, second=0, microsecond=0).isoformat()
    res = client.post(
        f"/api/bookings/{booking_id}/reschedule",
        json={"booking_time": t2},
        headers=customer_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["booking_time"].startswith(t2[:13])


def test_booking_ics_download(client, customer_headers, shop, menu):
    t1 = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_res = client.post(
        "/api/bookings",
        json={"shop_id": str(shop.id), "menu_id": str(menu.id), "booking_time": t1},
        headers=customer_headers,
    )
    booking_id = create_res.get_json()["id"]

    ics_res = client.get(f"/api/bookings/{booking_id}/ics", headers=customer_headers)
    assert ics_res.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_res.get_data(as_text=True)


def test_owner_special_schedule_closes_day(client, owner_headers, shop):
    target = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    set_res = client.put(
        f"/api/owner/shops/{shop.id}/special-schedules",
        json={"schedules": [{"date": target, "is_closed": True, "note": "holiday"}]},
        headers=owner_headers,
    )
    assert set_res.status_code == 200

    slots_res = client.get(f"/api/shops/{shop.id}/slots?date={target}")
    assert slots_res.status_code == 200
    assert slots_res.get_json()["closed"] is True


def test_review_report_hides_review_after_three_reports(client, app, customer, customer_headers, owner, admin, shop, menu, owner_headers, admin_headers):
    with app.app_context():
        other = User(
            email="reporter3@test.com",
            password_hash=owner.password_hash,
            role="customer",
            auth_provider="email",
            language="en",
        )
        _db.session.add(other)
        _db.session.commit()
        other_headers = {"Authorization": f"Bearer {create_tokens(str(other.id))['access_token']}"}

    booking = _create_completed_booking(customer, shop, menu)
    create_review_res = client.post(
        "/api/reviews",
        json={"booking_id": str(booking.id), "rating": 5, "comment": "nice"},
        headers=customer_headers,
    )
    review_id = create_review_res.get_json()["id"]

    r1 = client.post(f"/api/reviews/{review_id}/report", json={"reason": "spam"}, headers=owner_headers)
    r2 = client.post(f"/api/reviews/{review_id}/report", json={"reason": "abuse"}, headers=admin_headers)
    r3 = client.post(f"/api/reviews/{review_id}/report", json={"reason": "other"}, headers=other_headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r3.status_code == 201
    assert r3.get_json()["review_hidden"] is True


def test_register_push_token(client, customer_headers):
    res = client.post(
        "/api/auth/push-token",
        json={"device_token": "test-device-token-123", "platform": "android"},
        headers=customer_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["registered"] is True
