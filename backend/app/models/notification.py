import uuid
from datetime import datetime, timezone

from app import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(db.UUID, db.ForeignKey("bookings.id"), nullable=False)
    recipient_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False)
    channel = db.Column(db.String(20), nullable=False)  # "email", "push"
    notification_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    booking = db.relationship("Booking")
    recipient = db.relationship("User")
