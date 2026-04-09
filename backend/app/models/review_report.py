import uuid
from datetime import datetime, timezone

from app import db


class ReviewReport(db.Model):
    __tablename__ = "review_reports"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    review_id = db.Column(db.UUID, db.ForeignKey("reviews.id"), nullable=False, index=True)
    reporter_id = db.Column(db.UUID, db.ForeignKey("users.id"), nullable=False, index=True)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("review_id", "reporter_id", name="uq_review_report_once"),
    )

