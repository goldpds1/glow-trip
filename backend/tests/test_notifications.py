"""Phase 15 — Notification system tests."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from app import db
from app.models import Booking, Payment
from app.models.notification import Notification
from app.services import notification as notif_service


# ── Unit tests: notification service ───────────────────────

class TestNotifyService:
    """Unit tests for the notification orchestrator."""

    def test_notify_sends_email_when_available(self, app, customer, shop, menu, mock_email):
        """When email is available, notify() creates record with status=sent."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()

            result = notif_service.notify_customer(booking, "booking_confirmed")

            assert result is True
            assert len(mock_email) == 1
            assert mock_email[0]["to"] == customer.email

            notif = Notification.query.filter_by(booking_id=booking.id).first()
            assert notif is not None
            assert notif.status == "sent"
            assert notif.notification_type == "booking_confirmed"

    def test_notify_skips_when_unavailable(self, app, customer, shop, menu):
        """When email service is unavailable, notify() returns False and creates no record."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="pending",
            )
            db.session.add(booking)
            db.session.commit()

            result = notif_service.notify_customer(booking, "booking_created")

            assert result is False
            assert Notification.query.filter_by(booking_id=booking.id).count() == 0

    def test_notify_handles_send_failure(self, app, customer, shop, menu, monkeypatch):
        """When send_email returns False, notification status is 'failed'."""
        monkeypatch.setattr("app.services.email.is_available", lambda: True)
        monkeypatch.setattr("app.services.email.send_email", lambda to, subj, html: False)

        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()

            result = notif_service.notify_customer(booking, "booking_confirmed")

            assert result is False
            notif = Notification.query.filter_by(booking_id=booking.id).first()
            assert notif.status == "failed"

    def test_notify_handles_exception_gracefully(self, app, customer, shop, menu, monkeypatch):
        """When send_email raises, notify() returns False without propagating."""
        monkeypatch.setattr("app.services.email.is_available", lambda: True)
        monkeypatch.setattr("app.services.email.send_email",
                            lambda to, subj, html: (_ for _ in ()).throw(RuntimeError("boom")))

        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()

            result = notif_service.notify_customer(booking, "booking_confirmed")
            assert result is False

    def test_build_context(self, app, customer, shop, menu):
        """_build_context extracts all expected keys."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()

            ctx = notif_service._build_context(booking, customer)
            assert ctx["lang"] == "en"
            assert ctx["shop_name"] == shop.name
            assert ctx["menu_title"] == menu.title
            assert ctx["booking_time"] == "2026-05-01 10:00"


# ── Integration tests: API endpoints + notifications ───────

class TestBookingNotifications:
    """Integration tests verifying notifications are triggered from API endpoints."""

    def test_create_booking_works_without_email(self, client, customer_headers, shop, menu):
        """Booking creation succeeds even without email service (SENDGRID_API_KEY unset)."""
        resp = client.post("/api/bookings", json={
            "shop_id": str(shop.id),
            "menu_id": str(menu.id),
            "booking_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }, headers=customer_headers)
        assert resp.status_code == 201

    def test_owner_confirm_triggers_notification(self, app, client, owner_headers, customer, shop, menu, mock_email):
        """Owner confirming a booking sends notification to customer."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="pending",
            )
            db.session.add(booking)
            db.session.commit()
            bid = str(booking.id)

        resp = client.patch(f"/api/owner/bookings/{bid}/status",
                            json={"status": "confirmed"},
                            headers=owner_headers)
        assert resp.status_code == 200
        assert any(e["to"] == customer.email for e in mock_email)

    def test_customer_cancel_triggers_notification(self, app, client, customer_headers, customer, shop, menu, mock_email):
        """Customer cancelling sends notification to owner."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="pending",
            )
            db.session.add(booking)
            db.session.commit()
            bid = str(booking.id)

        resp = client.post(f"/api/bookings/{bid}/cancel", headers=customer_headers)
        assert resp.status_code == 200
        # Owner should be notified
        with app.app_context():
            from app.models import User
            owner_user = User.query.filter_by(role="owner").first()
            assert any(e["to"] == owner_user.email for e in mock_email)

    def test_admin_cancel_notifies_both(self, app, client, admin_headers, customer, shop, menu, mock_email):
        """Admin cancel sends notifications to both customer and owner."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(days=1),
                status="pending",
            )
            db.session.add(booking)
            db.session.commit()
            bid = str(booking.id)

        resp = client.post(f"/api/admin/bookings/{bid}/cancel", headers=admin_headers)
        assert resp.status_code == 200
        emails_to = [e["to"] for e in mock_email]
        assert customer.email in emails_to
        with app.app_context():
            from app.models import User
            owner_user = User.query.filter_by(role="owner").first()
            assert owner_user.email in emails_to


# ── CLI command tests ──────────────────────────────────────

class TestReminderCLI:
    """Tests for the flask send-reminders CLI command."""

    def test_send_reminders_finds_eligible(self, app, customer, shop, menu, mock_email):
        """Reminder command sends email for confirmed booking within window."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(hours=12),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()

        runner = app.test_cli_runner()
        result = runner.invoke(args=["send-reminders"])
        assert "Sent 1 reminder(s)" in result.output

    def test_send_reminders_skips_already_reminded(self, app, customer, shop, menu, mock_email):
        """Reminder command skips bookings that already have a sent reminder."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) + timedelta(hours=12),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.flush()

            notif = Notification(
                booking_id=booking.id, recipient_id=customer.id,
                channel="email", notification_type="booking_reminder",
                status="sent",
                sent_at=datetime.now(timezone.utc),
            )
            db.session.add(notif)
            db.session.commit()

        runner = app.test_cli_runner()
        result = runner.invoke(args=["send-reminders"])
        assert "Sent 0 reminder(s)" in result.output

    def test_send_reminders_skips_past_bookings(self, app, customer, shop, menu, mock_email):
        """Reminder command ignores bookings in the past."""
        with app.app_context():
            booking = Booking(
                user_id=customer.id, shop_id=shop.id, menu_id=menu.id,
                booking_time=datetime.now(timezone.utc) - timedelta(hours=2),
                status="confirmed",
            )
            db.session.add(booking)
            db.session.commit()

        runner = app.test_cli_runner()
        result = runner.invoke(args=["send-reminders"])
        assert "Sent 0 reminder(s)" in result.output
