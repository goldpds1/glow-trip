"""Flask CLI commands for scheduled tasks."""

import logging
from datetime import datetime, timezone, timedelta

import click
from flask import current_app
from flask.cli import with_appcontext

from app import db
from app.models import Booking
from app.models.notification import Notification
from app.services import notification as notif_service

logger = logging.getLogger(__name__)


@click.command("send-reminders")
@with_appcontext
def send_reminders_command():
    """Send reminder emails for bookings in the next N hours."""
    hours = current_app.config.get("NOTIFICATION_REMINDER_HOURS", 24)
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=hours)

    already_reminded = (
        db.session.query(Notification.booking_id)
        .filter(
            Notification.notification_type == "booking_reminder",
            Notification.status == "sent",
        )
        .subquery()
    )

    bookings = (
        Booking.query.filter(
            Booking.status == "confirmed",
            Booking.booking_time >= now,
            Booking.booking_time <= window_end,
            ~Booking.id.in_(db.session.query(already_reminded.c.booking_id)),
        )
        .all()
    )

    sent = 0
    for booking in bookings:
        if notif_service.notify_customer(booking, "booking_reminder"):
            sent += 1

    click.echo(f"Sent {sent} reminder(s) out of {len(bookings)} eligible booking(s).")
