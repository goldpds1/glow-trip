import uuid
from datetime import datetime, timezone

from app import db


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "shop_id", name="uq_user_shop_favorite"),
    )

    user = db.relationship("User", backref=db.backref("favorites", lazy="dynamic"))
    shop = db.relationship("Shop", backref=db.backref("favorited_by", lazy="dynamic"))
