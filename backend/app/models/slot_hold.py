import uuid
from datetime import datetime, timezone

from app import db


class SlotHold(db.Model):
    __tablename__ = "slot_holds"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False, index=True)
    user_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False, index=True)
    slot_time = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("shop_id", "slot_time", name="uq_slot_hold_shop_time"),
    )

