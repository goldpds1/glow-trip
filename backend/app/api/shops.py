import math

from flask import Blueprint, request, jsonify, g

from app import db
from app.models import Shop, Menu, Review
from app.auth.decorators import login_required, role_required


def _shop_avg_rating(shop_id):
    result = db.session.query(db.func.avg(Review.rating)).filter_by(shop_id=shop_id).scalar()
    return round(float(result), 1) if result else 0


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two GPS coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

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

    # 거리순 정렬
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    sort = request.args.get("sort", "").strip()

    if sort == "distance" and user_lat is not None and user_lng is not None:
        all_shops = q.all()
        shop_list = []
        for s in all_shops:
            dist = None
            if s.latitude and s.longitude:
                dist = round(_haversine(user_lat, user_lng, s.latitude, s.longitude), 2)
            shop_list.append((s, dist))
        shop_list.sort(key=lambda x: (x[1] is None, x[1] or 0))
        total = len(shop_list)
        start = (page - 1) * per_page
        page_items = shop_list[start:start + per_page]
        shops = [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "address": s.address,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "image_url": s.image_url,
                "avg_rating": _shop_avg_rating(s.id),
                "distance_km": dist,
            }
            for s, dist in page_items
        ]
        return jsonify(
            shops=shops,
            total=total,
            page=page,
            pages=math.ceil(total / per_page) if total else 1,
        ), 200

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
            "avg_rating": _shop_avg_rating(s.id),
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
            "image_url": m.image_url,
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
            "image_url": m.image_url,
        }
        for m in shop.menus.filter_by(is_active=True).order_by(Menu.price.asc())
    ]

    return jsonify(menus=menus), 200
