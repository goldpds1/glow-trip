from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g

from app import db
from app.models import Booking, Shop, Menu, Payment, Review
from app.auth.decorators import login_required
from app.services.translator import translate_to_korean
from app.services import notification as notif_service

bookings_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")


def _booking_to_dict(b, include_translation=False):
    d = {
        "id": str(b.id),
        "shop_id": str(b.shop_id),
        "shop_name": b.shop.name,
        "menu_id": str(b.menu_id),
        "menu_title": b.menu.title,
        "booking_time": b.booking_time.isoformat(),
        "status": b.status,
        "request_original": b.request_original,
        "created_at": b.created_at.isoformat(),
    }
    if include_translation:
        d["request_translated"] = b.request_translated
    if b.payment:
        d["payment_status"] = b.payment.payment_status
        d["amount"] = b.payment.amount
    d["has_review"] = Review.query.filter_by(booking_id=b.id).first() is not None
    return d


# ── 예약 생성 (고객) ─────────────────────────────────────
@bookings_bp.route("", methods=["POST"])
@login_required
def create_booking():
    data = request.get_json() or {}
    user = g.current_user

    shop_id = data.get("shop_id")
    menu_id = data.get("menu_id")
    booking_time_str = data.get("booking_time")
    request_text = data.get("request_original", "").strip()

    if not shop_id or not menu_id or not booking_time_str:
        return jsonify(error="shop_id, menu_id, booking_time are required"), 400

    shop = Shop.query.get(shop_id)
    if not shop or not shop.is_active:
        return jsonify(error="Shop not found"), 404

    menu = Menu.query.get(menu_id)
    if not menu or not menu.is_active or str(menu.shop_id) != str(shop.id):
        return jsonify(error="Menu not found in this shop"), 404

    try:
        booking_time = datetime.fromisoformat(booking_time_str)
    except ValueError:
        return jsonify(error="Invalid booking_time format (ISO 8601)"), 400

    if booking_time < datetime.now(timezone.utc):
        return jsonify(error="Cannot book in the past"), 400

    # AI 번역 (요청사항이 있을 때만)
    translated = None
    if request_text:
        translated = translate_to_korean(request_text)

    booking = Booking(
        user_id=user.id,
        shop_id=shop.id,
        menu_id=menu.id,
        booking_time=booking_time,
        status="pending",
        request_original=request_text or None,
        request_translated=translated,
    )
    db.session.add(booking)
    db.session.flush()

    # 결제 레코드 생성 (pending 상태)
    payment = Payment(
        booking_id=booking.id,
        amount=menu.price,
        currency="KRW",
        payment_status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    notif_service.notify_owner(booking, "booking_created")

    return jsonify(
        id=str(booking.id),
        status=booking.status,
        payment_status=payment.payment_status,
        amount=payment.amount,
    ), 201


# ── 내 예약 목록 (고객) ──────────────────────────────────
@bookings_bp.route("", methods=["GET"])
@login_required
def list_my_bookings():
    user = g.current_user
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    status = request.args.get("status")

    q = Booking.query.filter_by(user_id=user.id)
    if status:
        q = q.filter_by(status=status)

    pagination = q.order_by(Booking.booking_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        bookings=[_booking_to_dict(b) for b in pagination.items],
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


# ── 예약 상세 (고객) ─────────────────────────────────────
@bookings_bp.route("/<booking_id>", methods=["GET"])
@login_required
def get_booking(booking_id):
    user = g.current_user
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify(error="Booking not found"), 404

    # 고객 본인 또는 해당 샵 원장만 조회 가능
    if str(booking.user_id) != str(user.id) and str(booking.shop.owner_id) != str(user.id):
        return jsonify(error="Forbidden"), 403

    include_translation = str(booking.shop.owner_id) == str(user.id)
    return jsonify(_booking_to_dict(booking, include_translation=include_translation)), 200


# ── 예약 취소 (고객) ─────────────────────────────────────
@bookings_bp.route("/<booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    user = g.current_user
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify(error="Booking not found"), 404
    if str(booking.user_id) != str(user.id):
        return jsonify(error="Forbidden"), 403
    if booking.status not in ("pending", "confirmed"):
        return jsonify(error="Cannot cancel this booking"), 400

    booking.status = "cancelled"
    if booking.payment and booking.payment.payment_status in ("authorized", "captured"):
        booking.payment.payment_status = "refunded"
    db.session.commit()

    notif_service.notify_owner(booking, "booking_cancelled")

    return jsonify(id=str(booking.id), status=booking.status), 200
