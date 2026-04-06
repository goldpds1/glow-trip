import math

from flask import Blueprint, request, jsonify, g

from datetime import datetime, timedelta, time as dt_time

from app import db
from app.models import Shop, Menu, Review, Booking, BusinessHour
from app.auth.decorators import login_required, role_required


def _shop_avg_rating(shop_id):
    result = db.session.query(db.func.avg(Review.rating)).filter_by(shop_id=shop_id).scalar()
    return round(float(result), 1) if result else 0


def _shop_review_count(shop_id):
    return Review.query.filter_by(shop_id=shop_id).count()


def _shop_min_price(shop_id):
    result = db.session.query(db.func.min(Menu.price)).filter_by(
        shop_id=shop_id, is_active=True
    ).scalar()
    return result


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

    # 카테고리 필터
    category = request.args.get("category", "").strip()
    if category:
        q = q.filter(Shop.category == category)

    # 거리순 정렬
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    sort = request.args.get("sort", "").strip()

    def _serialize_shop(s, distance_km=None):
        d = {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "address": s.address,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "image_url": s.image_url,
            "category": s.category,
            "avg_rating": _shop_avg_rating(s.id),
            "review_count": _shop_review_count(s.id),
            "min_price": _shop_min_price(s.id),
        }
        if distance_km is not None:
            d["distance_km"] = distance_km
        return d

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
        shops = [_serialize_shop(s, dist) for s, dist in page_items]
        return jsonify(
            shops=shops,
            total=total,
            page=page,
            pages=math.ceil(total / per_page) if total else 1,
        ), 200

    # 인기순 정렬 (예약 수 기준)
    if sort == "popular":
        booking_count = (
            db.session.query(
                Booking.shop_id,
                db.func.count(Booking.id).label("cnt"),
            )
            .group_by(Booking.shop_id)
            .subquery()
        )
        q = q.outerjoin(booking_count, Shop.id == booking_count.c.shop_id).order_by(
            db.desc(db.func.coalesce(booking_count.c.cnt, 0))
        )
    else:
        q = q.order_by(Shop.created_at.desc())

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    shops = [_serialize_shop(s) for s in pagination.items]

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
        category=shop.category,
        image_url=shop.image_url,
        avg_rating=_shop_avg_rating(shop.id),
        review_count=_shop_review_count(shop.id),
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


# ── 예약 가능 타임슬롯 조회 ──────────────────────────────
@shops_bp.route("/<shop_id>/slots", methods=["GET"])
def list_slots(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or not shop.is_active:
        return jsonify(error="Shop not found"), 404

    date_str = request.args.get("date", "")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify(error="date parameter required (YYYY-MM-DD)"), 400

    dow = date.weekday()  # 0=Mon
    bh = BusinessHour.query.filter_by(shop_id=shop.id, day_of_week=dow).first()

    # Default: 10:00~20:00 if no business hours set
    if bh and bh.is_closed:
        return jsonify(slots=[], date=date_str, closed=True), 200

    open_t = bh.open_time if bh else dt_time(10, 0)
    close_t = bh.close_time if bh else dt_time(20, 0)

    # Existing bookings on this date
    day_start = datetime.combine(date, dt_time(0, 0))
    day_end = day_start + timedelta(days=1)
    booked_times = set()
    bookings = Booking.query.filter(
        Booking.shop_id == shop.id,
        Booking.booking_time >= day_start,
        Booking.booking_time < day_end,
        Booking.status.in_(["pending", "confirmed"]),
    ).all()
    for b in bookings:
        booked_times.add(b.booking_time.strftime("%H:%M"))

    # Generate 30-minute slots
    slots = []
    current = datetime.combine(date, open_t)
    end = datetime.combine(date, close_t)
    now = datetime.utcnow()

    while current < end:
        time_str = current.strftime("%H:%M")
        available = time_str not in booked_times
        # Past slots are unavailable
        if datetime.combine(date, current.time()) < now:
            available = False
        slots.append({"time": time_str, "available": available})
        current += timedelta(minutes=30)

    return jsonify(slots=slots, date=date_str, closed=False), 200
