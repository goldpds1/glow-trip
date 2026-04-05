import uuid
from datetime import datetime, timezone

from app import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False)
    menu_id = db.Column(db.UUID, db.ForeignKey("menus.id"), nullable=False)
    booking_time = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending, confirmed, completed, cancelled, noshow
    request_original = db.Column(db.Text, nullable=True)
    request_translated = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="bookings")
    shop = db.relationship("Shop", back_populates="bookings")
    menu = db.relationship("Menu")
    payment = db.relationship("Payment", back_populates="booking", uselist=False)
