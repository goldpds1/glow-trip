"""Shared utility functions."""

from app import db
from app.models import Review, Menu


def shop_avg_rating(shop_id):
    result = db.session.query(db.func.avg(Review.rating)).filter_by(shop_id=shop_id).scalar()
    return round(float(result), 1) if result else 0


def shop_review_count(shop_id):
    return Review.query.filter_by(shop_id=shop_id).count()


def shop_min_price(shop_id):
    return db.session.query(db.func.min(Menu.price)).filter_by(
        shop_id=shop_id, is_active=True
    ).scalar()
