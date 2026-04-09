import uuid
from datetime import datetime, timezone

from app import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False)
    booking_id = db.Column(db.UUID, db.ForeignKey("bookings.id"), unique=True, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User")
    shop = db.relationship("Shop")
    booking = db.relationship("Booking")
