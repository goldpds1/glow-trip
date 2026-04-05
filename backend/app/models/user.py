import uuid
from datetime import datetime, timezone

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    auth_provider = db.Column(db.String(50), nullable=False, default="email")
    provider_id = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    language = db.Column(db.String(10), nullable=False, default="en")
    role = db.Column(db.String(20), nullable=False, default="customer")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    shops = db.relationship("Shop", back_populates="owner", lazy="dynamic")
    bookings = db.relationship("Booking", back_populates="user", lazy="dynamic")
