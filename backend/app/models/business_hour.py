import uuid

from app import db


class BusinessHour(db.Model):
    __tablename__ = "business_hours"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon .. 6=Sun
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)

    shop = db.relationship("Shop", backref=db.backref("business_hours", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("shop_id", "day_of_week", name="uq_shop_day"),
    )
