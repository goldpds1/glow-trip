import uuid
from datetime import datetime, timezone

from app import db


class SpecialSchedule(db.Model):
    __tablename__ = "special_schedules"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    open_time = db.Column(db.Time, nullable=True)
    close_time = db.Column(db.Time, nullable=True)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("shop_id", "date", name="uq_special_schedule_shop_date"),
    )

