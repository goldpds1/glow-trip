from flask import Blueprint, request, jsonify, g

from app import db
from app.models import Shop, Menu
from app.auth.decorators import login_required, role_required

shops_bp = Blueprint("shops", __name__, url_prefix="/api/shops")


# ── 샵 목록 조회 (공개) ──────────────────────────────────
@shops_bp.route("", methods=["GET"])
def list_shops():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    q = Shop.query.filter_by(is_active=True)

    # 키워드 검색
    keyword = request.args.get("keyword", "").strip()
    if keyword:
        q = q.filter(
            db.or_(
                Shop.name.ilike(f"%{keyword}%"),
                Shop.description.ilike(f"%{keyword}%"),
                Shop.address.ilike(f"%{keyword}%"),
            )
        )

    pagination = q.order_by(Shop.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    shops = [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "address": s.address,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "image_url": s.image_url,
        }
        for s in pagination.items
    ]

    return jsonify(
        shops=shops,
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


# ── 샵 상세 조회 (공개) ──────────────────────────────────
@shops_bp.route("/<shop_id>", methods=["GET"])
def get_shop(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or not shop.is_active:
        return jsonify(error="Shop not found"), 404

    menus = [
        {
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "price": m.price,
            "duration": m.duration,
        }
        for m in shop.menus.filter_by(is_active=True).order_by(Menu.price.asc())
    ]

    return jsonify(
        id=str(shop.id),
        name=shop.name,
        description=shop.description,
        address=shop.address,
        latitude=shop.latitude,
        longitude=shop.longitude,
        phone=shop.phone,
        image_url=shop.image_url,
        menus=menus,
    ), 200


# ── 샵의 메뉴 목록 (공개) ────────────────────────────────
@shops_bp.route("/<shop_id>/menus", methods=["GET"])
def list_menus(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or not shop.is_active:
        return jsonify(error="Shop not found"), 404

    menus = [
        {
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "price": m.price,
            "duration": m.duration,
        }
        for m in shop.menus.filter_by(is_active=True).order_by(Menu.price.asc())
    ]

    return jsonify(menus=menus), 200
