import uuid
from datetime import datetime, timezone

from app import db


class UserDevice(db.Model):
    __tablename__ = "user_devices"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False, index=True)
    device_token = db.Column(db.String(300), nullable=False, unique=True)
    platform = db.Column(db.String(20), nullable=False, default="unknown")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

