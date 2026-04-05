import uuid
from datetime import datetime, timezone

from app import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(
        db.UUID, db.ForeignKey("bookings.id"), unique=True, nullable=False
    )
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="KRW")
    pg_tid = db.Column(db.String(200), nullable=True)
    payment_status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending, authorized, captured, refunded, failed
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    booking = db.relationship("Booking", back_populates="payment")
