"""Timeslot & BusinessHour API tests."""
from datetime import datetime, timedelta


def test_slots_default_hours(client, shop, customer_headers):
    """With no business hours set, default 10:00-20:00 slots."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    res = client.get(f"/api/shops/{shop.id}/slots?date={tomorrow}", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["date"] == tomorrow
    assert data["closed"] is False
    assert len(data["slots"]) == 20  # 10:00~19:30 = 20 slots


def test_slots_missing_date(client, shop, customer_headers):
    res = client.get(f"/api/shops/{shop.id}/slots", headers=customer_headers)
    assert res.status_code == 400


def test_slots_shop_not_found(client, customer_headers):
    import uuid
    res = client.get(f"/api/shops/{uuid.uuid4()}/slots?date=2026-04-10", headers=customer_headers)
    assert res.status_code == 404


def test_slots_closed_day(client, app, shop, owner_headers, customer_headers):
    """When business hours mark a day as closed, return empty slots."""
    from app import db as _db
    from app.models import BusinessHour
    from datetime import time as dt_time

    tomorrow = datetime.utcnow() + timedelta(days=1)
    dow = tomorrow.weekday()

    with app.app_context():
        bh = BusinessHour(
            shop_id=shop.id,
            day_of_week=dow,
            open_time=dt_time(10, 0),
            close_time=dt_time(20, 0),
            is_closed=True,
        )
        _db.session.add(bh)
        _db.session.commit()

    date_str = tomorrow.strftime("%Y-%m-%d")
    res = client.get(f"/api/shops/{shop.id}/slots?date={date_str}", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["closed"] is True
    assert data["slots"] == []


def test_slots_with_booking(client, app, shop, menu, customer, customer_headers):
    """Booked slot should show as unavailable."""
    from app import db as _db
    from app.models import Booking

    tomorrow = datetime.utcnow() + timedelta(days=1)
    booking_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

    with app.app_context():
        b = Booking(
            user_id=customer.id,
            shop_id=shop.id,
            menu_id=menu.id,
            booking_time=booking_time,
            status="confirmed",
        )
        _db.session.add(b)
        _db.session.commit()

    date_str = tomorrow.strftime("%Y-%m-%d")
    res = client.get(f"/api/shops/{shop.id}/slots?date={date_str}", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    slot_14 = next(s for s in data["slots"] if s["time"] == "14:00")
    assert slot_14["available"] is False


def test_owner_get_hours_empty(client, shop, owner_headers):
    res = client.get(f"/api/owner/shops/{shop.id}/hours", headers=owner_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["hours"] == []


def test_owner_set_hours(client, shop, owner_headers):
    hours = [
        {"day_of_week": 0, "open_time": "09:00", "close_time": "18:00", "is_closed": False},
        {"day_of_week": 6, "open_time": "10:00", "close_time": "15:00", "is_closed": False},
    ]
    res = client.put(
        f"/api/owner/shops/{shop.id}/hours",
        json={"hours": hours},
        headers=owner_headers,
    )
    assert res.status_code == 200

    res2 = client.get(f"/api/owner/shops/{shop.id}/hours", headers=owner_headers)
    data = res2.get_json()
    assert len(data["hours"]) == 2
    assert data["hours"][0]["day_of_week"] == 0
    assert data["hours"][0]["open_time"] == "09:00"


def test_owner_set_hours_replaces(client, shop, owner_headers):
    """PUT replaces all existing hours."""
    hours1 = [{"day_of_week": i, "open_time": "10:00", "close_time": "20:00"} for i in range(7)]
    client.put(f"/api/owner/shops/{shop.id}/hours", json={"hours": hours1}, headers=owner_headers)

    hours2 = [{"day_of_week": 0, "open_time": "11:00", "close_time": "19:00"}]
    client.put(f"/api/owner/shops/{shop.id}/hours", json={"hours": hours2}, headers=owner_headers)

    res = client.get(f"/api/owner/shops/{shop.id}/hours", headers=owner_headers)
    assert len(res.get_json()["hours"]) == 1


def test_owner_hours_forbidden_for_customer(client, shop, customer_headers):
    res = client.get(f"/api/owner/shops/{shop.id}/hours", headers=customer_headers)
    assert res.status_code == 403
