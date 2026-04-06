from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify

from app import db
from app.models import User, Shop, Menu, Booking, Payment, Review
from app.auth.decorators import role_required
from app.services import notification as notif_service

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── 사용자 관리 ────────────��────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    role = request.args.get("role")
    keyword = request.args.get("keyword", "").strip()

    q = User.query
    if role:
        q = q.filter_by(role=role)
    if keyword:
        q = q.filter(
            db.or_(
                User.name.ilike(f"%{keyword}%"),
                User.email.ilike(f"%{keyword}%"),
            )
        )

    pagination = q.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        users=[
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "language": u.language,
                "auth_provider": u.auth_provider,
                "created_at": u.created_at.isoformat(),
            }
            for u in pagination.items
        ],
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


@admin_bp.route("/users/<user_id>", methods=["PATCH"])
@role_required("admin")
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(error="User not found"), 404

    data = request.get_json() or {}

    if "role" in data:
        if data["role"] not in ("customer", "owner", "admin"):
            return jsonify(error="Invalid role"), 400
        user.role = data["role"]

    db.session.commit()

    return jsonify(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
    ), 200


# ── 샵 관리 ───────────────────────────────────────────

@admin_bp.route("/shops", methods=["GET"])
@role_required("admin")
def list_shops():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    keyword = request.args.get("keyword", "").strip()
    active = request.args.get("active")

    q = Shop.query
    if keyword:
        q = q.filter(
            db.or_(
                Shop.name.ilike(f"%{keyword}%"),
                Shop.address.ilike(f"%{keyword}%"),
            )
        )
    if active is not None:
        q = q.filter_by(is_active=active.lower() == "true")

    pagination = q.order_by(Shop.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        shops=[
            {
                "id": str(s.id),
                "name": s.name,
                "owner_email": s.owner.email,
                "owner_name": s.owner.name,
                "address": s.address,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
            }
            for s in pagination.items
        ],
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


@admin_bp.route("/shops/<shop_id>", methods=["PATCH"])
@role_required("admin")
def update_shop(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop:
        return jsonify(error="Shop not found"), 404

    data = request.get_json() or {}

    if "is_active" in data:
        shop.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify(
        id=str(shop.id),
        name=shop.name,
        is_active=shop.is_active,
    ), 200


# ── 예약 관리 ──────���───────────────────────────────────

@admin_bp.route("/bookings", methods=["GET"])
@role_required("admin")
def list_bookings():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    status = request.args.get("status")

    q = Booking.query
    if status:
        q = q.filter_by(status=status)

    pagination = q.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        bookings=[
            {
                "id": str(b.id),
                "user_name": b.user.name,
                "user_email": b.user.email,
                "shop_name": b.shop.name,
                "menu_title": b.menu.title,
                "booking_time": b.booking_time.isoformat(),
                "status": b.status,
                "payment_status": b.payment.payment_status if b.payment else None,
                "amount": b.payment.amount if b.payment else None,
                "created_at": b.created_at.isoformat(),
            }
            for b in pagination.items
        ],
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


@admin_bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
@role_required("admin")
def cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify(error="Booking not found"), 404

    if booking.status in ("cancelled", "completed"):
        return jsonify(error=f"Cannot cancel a {booking.status} booking"), 400

    booking.status = "cancelled"
    if booking.payment and booking.payment.payment_status in ("authorized", "captured"):
        booking.payment.payment_status = "refunded"

    db.session.commit()

    notif_service.notify_customer(booking, "booking_cancelled")
    notif_service.notify_owner(booking, "booking_cancelled")

    return jsonify(
        id=str(booking.id),
        status=booking.status,
        payment_status=booking.payment.payment_status if booking.payment else None,
    ), 200


# ── 정산 관리 ─────���─────────────────────────────────���──

@admin_bp.route("/settlements", methods=["GET"])
@role_required("admin")
def all_settlements():
    from flask import current_app
    fee_rate = current_app.config.get("PLATFORM_FEE_RATE", 0.1)

    shops = Shop.query.all()
    result = []
    grand_total_sales = 0
    grand_total_fee = 0

    for shop in shops:
        payments = (
            db.session.query(Payment)
            .join(Booking, Payment.booking_id == Booking.id)
            .filter(Booking.shop_id == shop.id, Payment.payment_status == "captured")
            .all()
        )
        total_sales = sum(p.amount for p in payments)
        total_fee = int(total_sales * fee_rate)
        total_settlement = total_sales - total_fee
        grand_total_sales += total_sales
        grand_total_fee += total_fee

        if total_sales > 0:
            result.append({
                "shop_id": str(shop.id),
                "shop_name": shop.name,
                "owner_name": shop.owner.name,
                "total_sales": total_sales,
                "total_fee": total_fee,
                "total_settlement": total_settlement,
                "payment_count": len(payments),
            })

    return jsonify(
        fee_rate=fee_rate,
        grand_total_sales=grand_total_sales,
        grand_total_fee=grand_total_fee,
        grand_total_settlement=grand_total_sales - grand_total_fee,
        shops=result,
    ), 200


# ── 통계 대시보드 ──────────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
@role_required("admin")
def dashboard_stats():
    total_users = User.query.count()
    total_shops = Shop.query.count()
    total_bookings = Booking.query.count()
    total_reviews = Review.query.count()

    # 매출 총계
    total_revenue = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(Payment.payment_status == "captured").scalar()

    # 상태별 예약 수
    status_counts = {}
    for status in ("pending", "confirmed", "completed", "cancelled", "noshow"):
        status_counts[status] = Booking.query.filter_by(status=status).count()

    # 최근 7일 예약 추이
    now = datetime.now(timezone.utc)
    daily_bookings = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = Booking.query.filter(
            db.func.date(Booking.created_at) == day
        ).count()
        daily_bookings.append({"date": day.isoformat(), "count": count})

    # 인기 샵 (예약 수 기준 Top 5)
    popular_shops = (
        db.session.query(
            Shop.id, Shop.name,
            db.func.count(Booking.id).label("booking_count")
        )
        .join(Booking, Shop.id == Booking.shop_id)
        .group_by(Shop.id, Shop.name)
        .order_by(db.desc("booking_count"))
        .limit(5)
        .all()
    )

    return jsonify(
        total_users=total_users,
        total_shops=total_shops,
        total_bookings=total_bookings,
        total_reviews=total_reviews,
        total_revenue=int(total_revenue),
        status_counts=status_counts,
        daily_bookings=daily_bookings,
        popular_shops=[
            {"shop_id": str(s.id), "name": s.name, "booking_count": s.booking_count}
            for s in popular_shops
        ],
    ), 200
