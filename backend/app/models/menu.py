import uuid
from datetime import datetime, timezone

from app import db


class Menu(db.Model):
    __tablename__ = "menus"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    shop = db.relationship("Shop", back_populates="menus")
