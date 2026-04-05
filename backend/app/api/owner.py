from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g

from app import db
from app.models import Booking, Shop, Menu, Payment
from app.auth.decorators import role_required

owner_bp = Blueprint("owner", __name__, url_prefix="/api/owner")


def _booking_detail(b):
    return {
        "id": str(b.id),
        "user_name": b.user.name,
        "user_email": b.user.email,
        "menu_title": b.menu.title,
        "menu_price": b.menu.price,
        "booking_time": b.booking_time.isoformat(),
        "status": b.status,
        "request_original": b.request_original,
        "request_translated": b.request_translated,
        "payment_status": b.payment.payment_status if b.payment else None,
        "created_at": b.created_at.isoformat(),
    }


# ── 내 샵 목록 ──────────────────────────────────────────
@owner_bp.route("/shops", methods=["GET"])
@role_required("owner")
def my_shops():
    shops = Shop.query.filter_by(owner_id=g.current_user.id).all()
    return jsonify(
        shops=[
            {"id": str(s.id), "name": s.name, "is_active": s.is_active}
            for s in shops
        ]
    ), 200


# ── 샵 정보 수정 ───────────────────────────────────────
@owner_bp.route("/shops/<shop_id>", methods=["PATCH"])
@role_required("owner")
def update_shop(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Shop not found or not yours"), 404

    data = request.get_json() or {}
    allowed = ("name", "description", "address", "phone", "image_url")
    for key in allowed:
        if key in data:
            setattr(shop, key, data[key])

    db.session.commit()

    return jsonify(
        id=str(shop.id),
        name=shop.name,
        description=shop.description,
        address=shop.address,
        phone=shop.phone,
        image_url=shop.image_url,
    ), 200


# ── 메뉴 추가 ─────────────────────────────────────────
@owner_bp.route("/shops/<shop_id>/menus", methods=["POST"])
@role_required("owner")
def create_menu(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Shop not found or not yours"), 404

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    price = data.get("price")
    duration = data.get("duration")

    if not title or price is None or duration is None:
        return jsonify(error="title, price, duration are required"), 400

    menu = Menu(
        shop_id=shop.id,
        title=title,
        description=data.get("description", ""),
        price=int(price),
        duration=int(duration),
        image_url=data.get("image_url"),
        is_active=True,
    )
    db.session.add(menu)
    db.session.commit()

    return jsonify(
        id=str(menu.id),
        title=menu.title,
        description=menu.description,
        price=menu.price,
        duration=menu.duration,
        image_url=menu.image_url,
        is_active=menu.is_active,
    ), 201


# ── 메뉴 수정 ─────────────────────────────────────────
@owner_bp.route("/menus/<menu_id>", methods=["PATCH"])
@role_required("owner")
def update_menu(menu_id):
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify(error="Menu not found"), 404

    shop = Shop.query.get(menu.shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Not your menu"), 403

    data = request.get_json() or {}
    allowed = ("title", "description", "price", "duration", "is_active", "image_url")
    for key in allowed:
        if key in data:
            val = data[key]
            if key in ("price", "duration"):
                val = int(val)
            setattr(menu, key, val)

    db.session.commit()

    return jsonify(
        id=str(menu.id),
        title=menu.title,
        description=menu.description,
        price=menu.price,
        duration=menu.duration,
        image_url=menu.image_url,
        is_active=menu.is_active,
    ), 200


# ── 메뉴 삭제 ─────────────────────────────────────────
@owner_bp.route("/menus/<menu_id>", methods=["DELETE"])
@role_required("owner")
def delete_menu(menu_id):
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify(error="Menu not found"), 404

    shop = Shop.query.get(menu.shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Not your menu"), 403

    db.session.delete(menu)
    db.session.commit()

    return jsonify(message="Menu deleted"), 200


# ── 샵 예약 캘린더 (날짜별 조회) ─────────────────────────
@owner_bp.route("/shops/<shop_id>/bookings", methods=["GET"])
@role_required("owner")
def shop_bookings(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Shop not found or not yours"), 404

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    status = request.args.get("status")
    date_str = request.args.get("date")  # YYYY-MM-DD

    q = Booking.query.filter_by(shop_id=shop.id)

    if status:
        q = q.filter_by(status=status)

    if date_str:
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            next_day = target.replace(hour=0, minute=0, second=0)
            from datetime import timedelta
            q = q.filter(
                Booking.booking_time >= target,
                Booking.booking_time < target + timedelta(days=1),
            )
        except ValueError:
            return jsonify(error="Invalid date format (YYYY-MM-DD)"), 400

    pagination = q.order_by(Booking.booking_time.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        bookings=[_booking_detail(b) for b in pagination.items],
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


# ── 예약 상태 변경 (확정/완료/노쇼) ──────────────────────
@owner_bp.route("/bookings/<booking_id>/status", methods=["PATCH"])
@role_required("owner")
def update_booking_status(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify(error="Booking not found"), 404

    shop = Shop.query.get(booking.shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Not your booking"), 403

    data = request.get_json() or {}
    new_status = data.get("status")

    valid_transitions = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["completed", "noshow", "cancelled"],
    }

    allowed = valid_transitions.get(booking.status, [])
    if new_status not in allowed:
        return jsonify(
            error=f"Cannot change from '{booking.status}' to '{new_status}'",
            allowed=allowed,
        ), 400

    booking.status = new_status

    # 노쇼/취소 시 결제 상태 업데이트
    if new_status in ("cancelled", "noshow") and booking.payment:
        if booking.payment.payment_status in ("authorized", "captured"):
            booking.payment.payment_status = "refunded"

    # 완료 시 결제 확정
    if new_status == "completed" and booking.payment:
        if booking.payment.payment_status == "authorized":
            booking.payment.payment_status = "captured"
            booking.payment.paid_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify(
        id=str(booking.id),
        status=booking.status,
        payment_status=booking.payment.payment_status if booking.payment else None,
    ), 200


# ── 정산 조회 ────────────────────────────────────────────
@owner_bp.route("/shops/<shop_id>/settlements", methods=["GET"])
@role_required("owner")
def shop_settlements(shop_id):
    """샵의 완료된 결제 내역 및 정산 합계 조회."""
    shop = Shop.query.get(shop_id)
    if not shop or str(shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Shop not found or not yours"), 404

    from flask import current_app
    fee_rate = current_app.config.get("PLATFORM_FEE_RATE", 0.1)

    # captured 상태인 결제만 정산 대상
    payments = (
        db.session.query(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .filter(Booking.shop_id == shop.id, Payment.payment_status == "captured")
        .order_by(Payment.paid_at.desc())
        .all()
    )

    total_sales = sum(p.amount for p in payments)
    total_fee = int(total_sales * fee_rate)
    total_settlement = total_sales - total_fee

    items = [
        {
            "booking_id": str(p.booking_id),
            "amount": p.amount,
            "fee": int(p.amount * fee_rate),
            "settlement": p.amount - int(p.amount * fee_rate),
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        }
        for p in payments
    ]

    return jsonify(
        shop_id=str(shop.id),
        shop_name=shop.name,
        fee_rate=fee_rate,
        total_sales=total_sales,
        total_fee=total_fee,
        total_settlement=total_settlement,
        count=len(items),
        items=items,
    ), 200
