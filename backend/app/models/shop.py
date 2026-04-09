import uuid
from datetime import datetime, timezone

from app import db


class Shop(db.Model):
    __tablename__ = "shops"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    owner_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    region = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    owner = db.relationship("User", back_populates="shops")
    menus = db.relationship("Menu", back_populates="shop", lazy="dynamic")
    bookings = db.relationship("Booking", back_populates="shop", lazy="dynamic")
