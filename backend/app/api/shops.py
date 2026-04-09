import math

from flask import Blueprint, request, jsonify, g

from datetime import datetime, timedelta, time as dt_time

from app import db
from app.models import Shop, Menu, Review, Booking, BusinessHour, SlotHold, SpecialSchedule
from app.auth.decorators import login_required
from app.utils import shop_avg_rating as _shop_avg_rating, shop_review_count as _shop_review_count, shop_min_price as _shop_min_price


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

    # 지역 필터
    region = request.args.get("region", "").strip()
    if region:
        q = q.filter(Shop.region == region)

    # 카테고리 필터
    category = request.args.get("category", "").strip()
    if category:
        q = q.filter(Shop.category == category)

    # 가격대 필터 (최저 메뉴 가격 기준)
    price_min = request.args.get("price_min", type=int)
    price_max = request.args.get("price_max", type=int)
    if price_min is not None or price_max is not None:
        min_price_sub = (
            db.session.query(
                Menu.shop_id,
                db.func.min(Menu.price).label("mp"),
            )
            .filter(Menu.is_active.is_(True))
            .group_by(Menu.shop_id)
            .subquery()
        )
        q = q.join(min_price_sub, Shop.id == min_price_sub.c.shop_id)
        if price_min is not None:
            q = q.filter(min_price_sub.c.mp >= price_min)
        if price_max is not None:
            q = q.filter(min_price_sub.c.mp <= price_max)

    # 최소 평점 필터
    min_rating = request.args.get("min_rating", type=float)
    if min_rating is not None:
        avg_sub = (
            db.session.query(
                Review.shop_id,
                db.func.avg(Review.rating).label("ar"),
            )
            .group_by(Review.shop_id)
            .subquery()
        )
        q = q.join(avg_sub, Shop.id == avg_sub.c.shop_id).filter(avg_sub.c.ar >= min_rating)

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
            "region": s.region,
            "avg_rating": _shop_avg_rating(s.id),
            "review_count": _shop_review_count(s.id),
            "min_price": _shop_min_price(s.id),
        }
        if distance_km is not None:
            d["distance_km"] = distance_km
        return d

    # In-memory sort modes (distance, rating, price)
    if sort in ("distance", "rating", "price"):
        all_shops = q.all()
        shop_list = []
        for s in all_shops:
            dist = None
            if sort == "distance" and user_lat is not None and user_lng is not None:
                if s.latitude and s.longitude:
                    dist = round(_haversine(user_lat, user_lng, s.latitude, s.longitude), 2)
            shop_list.append((s, dist))

        if sort == "distance" and user_lat is not None and user_lng is not None:
            shop_list.sort(key=lambda x: (x[1] is None, x[1] or 0))
        elif sort == "rating":
            shop_list.sort(key=lambda x: _shop_avg_rating(x[0].id), reverse=True)
        elif sort == "price":
            shop_list.sort(key=lambda x: (_shop_min_price(x[0].id) is None, _shop_min_price(x[0].id) or 0))

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

    # Business hours
    hours = BusinessHour.query.filter_by(shop_id=shop.id).order_by(BusinessHour.day_of_week).all()
    business_hours = [
        {
            "day_of_week": h.day_of_week,
            "open_time": h.open_time.strftime("%H:%M") if h.open_time else "10:00",
            "close_time": h.close_time.strftime("%H:%M") if h.close_time else "20:00",
            "is_closed": h.is_closed,
        }
        for h in hours
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
        region=shop.region,
        image_url=shop.image_url,
        avg_rating=_shop_avg_rating(shop.id),
        review_count=_shop_review_count(shop.id),
        menus=menus,
        business_hours=business_hours,
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
    special = SpecialSchedule.query.filter_by(shop_id=shop.id, date=date).first()

    # Special schedule overrides weekly business hours
    if special and special.is_closed:
        return jsonify(slots=[], date=date_str, closed=True), 200
    if bh and bh.is_closed and not special:
        return jsonify(slots=[], date=date_str, closed=True), 200

    open_t = special.open_time if (special and special.open_time) else (bh.open_time if bh else dt_time(10, 0))
    close_t = special.close_time if (special and special.close_time) else (bh.close_time if bh else dt_time(20, 0))

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

    # Active slot holds by other users (public endpoint => all holds block)
    now = datetime.utcnow()
    active_holds = SlotHold.query.filter(
        SlotHold.shop_id == shop.id,
        SlotHold.slot_time >= day_start,
        SlotHold.slot_time < day_end,
        SlotHold.expires_at > now,
    ).all()
    held_times = {h.slot_time.strftime("%H:%M") for h in active_holds}

    # Generate 30-minute slots
    slots = []
    current = datetime.combine(date, open_t)
    end = datetime.combine(date, close_t)
    while current < end:
        time_str = current.strftime("%H:%M")
        available = time_str not in booked_times
        if time_str in held_times:
            available = False
        # Past slots are unavailable
        if datetime.combine(date, current.time()) < now:
            available = False
        slots.append({"time": time_str, "available": available})
        current += timedelta(minutes=30)

    return jsonify(slots=slots, date=date_str, closed=False), 200


@shops_bp.route("/<shop_id>/slots/hold", methods=["POST"])
@login_required
def hold_slot(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or not shop.is_active:
        return jsonify(error="Shop not found"), 404

    data = request.get_json() or {}
    date_str = data.get("date")
    time_str = data.get("time")
    if not date_str or not time_str:
        return jsonify(error="date and time are required"), 400

    try:
        slot_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify(error="Invalid date/time format"), 400

    if slot_time <= datetime.utcnow():
        return jsonify(error="Cannot hold past slot"), 400

    existing_booking = Booking.query.filter(
        Booking.shop_id == shop.id,
        Booking.booking_time == slot_time,
        Booking.status.in_(["pending", "confirmed"]),
    ).first()
    if existing_booking:
        return jsonify(error="Slot already booked"), 409

    # Clean up expired holds first
    SlotHold.query.filter(SlotHold.expires_at <= datetime.utcnow()).delete()
    db.session.flush()

    hold = SlotHold.query.filter_by(shop_id=shop.id, slot_time=slot_time).first()
    if hold and str(hold.user_id) != str(g.current_user.id) and hold.expires_at > datetime.utcnow():
        return jsonify(error="Slot currently held"), 409

    expires_at = datetime.utcnow() + timedelta(minutes=10)
    if hold:
        hold.user_id = g.current_user.id
        hold.expires_at = expires_at
    else:
        hold = SlotHold(
            shop_id=shop.id,
            user_id=g.current_user.id,
            slot_time=slot_time,
            expires_at=expires_at,
        )
        db.session.add(hold)
    db.session.commit()

    return jsonify(
        held=True,
        shop_id=str(shop.id),
        date=date_str,
        time=time_str,
        expires_at=expires_at.isoformat(),
    ), 200
