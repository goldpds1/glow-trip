from flask import Blueprint, jsonify, g

from app import db
from app.models import Favorite, Shop
from app.auth.decorators import login_required
from app.utils import shop_avg_rating as _shop_avg_rating, shop_review_count as _shop_review_count, shop_min_price as _shop_min_price

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


# ── 즐겨찾기 토글 (추가/삭제) ───────────────────────────
@favorites_bp.route("/<shop_id>", methods=["POST"])
@login_required
def toggle_favorite(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or not shop.is_active:
        return jsonify(error="Shop not found"), 404

    existing = Favorite.query.filter_by(
        user_id=g.current_user.id, shop_id=shop.id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify(favorited=False), 200

    fav = Favorite(user_id=g.current_user.id, shop_id=shop.id)
    db.session.add(fav)
    db.session.commit()
    return jsonify(favorited=True), 201


# ── 내 즐겨찾기 목록 ───────────────────────────────────
@favorites_bp.route("", methods=["GET"])
@login_required
def list_favorites():
    favs = (
        Favorite.query
        .filter_by(user_id=g.current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    shops = []
    for f in favs:
        s = f.shop
        if not s or not s.is_active:
            continue
        shops.append({
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "address": s.address,
            "image_url": s.image_url,
            "category": s.category,
            "avg_rating": _shop_avg_rating(s.id),
            "review_count": _shop_review_count(s.id),
            "min_price": _shop_min_price(s.id),
        })
    return jsonify(shops=shops), 200


# ── 특정 샵 즐겨찾기 여부 확인 ─────────────────────────
@favorites_bp.route("/check/<shop_id>", methods=["GET"])
@login_required
def check_favorite(shop_id):
    exists = Favorite.query.filter_by(
        user_id=g.current_user.id, shop_id=shop_id
    ).first() is not None
    return jsonify(favorited=exists), 200
