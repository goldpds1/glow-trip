"""결제 API — Stripe PaymentIntent 연동

플로우:
1. 고객이 예약 생성 (POST /api/bookings) → Payment(pending) 생성
2. 고객이 결제 시작 (POST /api/payments/:booking_id/checkout) → Stripe PaymentIntent 생성, client_secret 반환
3. 클라이언트에서 Stripe.js로 카드 입력 → 가승인 완료
4. Stripe Webhook → payment_status = authorized
5. 원장이 완료 처리 시 → capture (매입 확정)
6. 취소/노쇼 시 → refund
"""

import logging
from datetime import datetime, timezone

import stripe as stripe_lib
from flask import Blueprint, request, jsonify, g, current_app

from app import db
from app.models import Booking, Payment
from app.auth.decorators import login_required, role_required
from app.services.payment import (
    create_payment_intent,
    capture_payment,
    refund_payment,
)

logger = logging.getLogger(__name__)

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


# ── 결제 시작 (고객) ─────────────────────────────────────
@payments_bp.route("/<booking_id>/checkout", methods=["POST"])
@login_required
def checkout(booking_id):
    """예약에 대한 Stripe PaymentIntent를 생성하고 client_secret을 반환."""
    user = g.current_user
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify(error="Booking not found"), 404
    if str(booking.user_id) != str(user.id):
        return jsonify(error="Forbidden"), 403
    if booking.status != "pending":
        return jsonify(error="Booking is not in pending status"), 400

    payment = booking.payment
    if not payment:
        return jsonify(error="Payment record not found"), 404
    if payment.payment_status not in ("pending", "failed"):
        return jsonify(error=f"Payment already {payment.payment_status}"), 400

    try:
        result = create_payment_intent(
            amount=payment.amount,
            currency=payment.currency,
            metadata={
                "booking_id": str(booking.id),
                "user_id": str(user.id),
                "shop_id": str(booking.shop_id),
            },
        )
    except RuntimeError as e:
        return jsonify(error=str(e)), 503
    except Exception as e:
        logger.exception("Stripe PaymentIntent creation failed")
        return jsonify(error="Payment service unavailable"), 503

    payment.pg_tid = result["payment_intent_id"]
    db.session.commit()

    return jsonify(
        client_secret=result["client_secret"],
        payment_intent_id=result["payment_intent_id"],
        amount=payment.amount,
        currency=payment.currency,
    ), 200


# ── 결제 상태 조회 (고객) ────────────────────────────────
@payments_bp.route("/<booking_id>/status", methods=["GET"])
@login_required
def payment_status(booking_id):
    user = g.current_user
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify(error="Booking not found"), 404
    if str(booking.user_id) != str(user.id) and str(booking.shop.owner_id) != str(user.id):
        return jsonify(error="Forbidden"), 403

    payment = booking.payment
    if not payment:
        return jsonify(error="Payment not found"), 404

    return jsonify(
        booking_id=str(booking.id),
        amount=payment.amount,
        currency=payment.currency,
        payment_status=payment.payment_status,
        pg_tid=payment.pg_tid,
        paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
    ), 200


# ── 환불 요청 (관리자) ──────────────────────────────────
@payments_bp.route("/<booking_id>/refund", methods=["POST"])
@role_required("admin", "owner")
def request_refund(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify(error="Booking not found"), 404

    # 원장은 자기 샵만
    if g.current_user.role == "owner" and str(booking.shop.owner_id) != str(g.current_user.id):
        return jsonify(error="Forbidden"), 403

    payment = booking.payment
    if not payment or not payment.pg_tid:
        return jsonify(error="No payment to refund"), 400
    if payment.payment_status not in ("authorized", "captured"):
        return jsonify(error=f"Cannot refund: status is {payment.payment_status}"), 400

    try:
        result = refund_payment(payment.pg_tid)
    except Exception as e:
        logger.exception("Stripe refund failed")
        return jsonify(error="Refund failed"), 503

    payment.payment_status = "refunded"
    booking.status = "cancelled"
    db.session.commit()

    return jsonify(
        booking_id=str(booking.id),
        refund_id=result["refund_id"],
        refund_amount=result["amount"],
        payment_status=payment.payment_status,
    ), 200


# ── Stripe Webhook ───────────────────────────────────────
@payments_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    """Stripe 이벤트 수신 → 결제 상태 업데이트."""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = current_app.config.get("STRIPE_WEBHOOK_SECRET", "")

    if webhook_secret:
        try:
            event = stripe_lib.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe_lib.error.SignatureVerificationError):
            return jsonify(error="Invalid signature"), 400
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})
    pi_id = data_object.get("id", "")

    if not pi_id:
        return jsonify(received=True), 200

    payment = Payment.query.filter_by(pg_tid=pi_id).first()
    if not payment:
        return jsonify(received=True), 200

    if event_type == "payment_intent.amount_capturable_updated":
        # 가승인 완료
        payment.payment_status = "authorized"
        payment.booking.status = "confirmed"
        db.session.commit()

    elif event_type == "payment_intent.succeeded":
        # 매입 완료
        payment.payment_status = "captured"
        payment.paid_at = datetime.now(timezone.utc)
        db.session.commit()

    elif event_type == "payment_intent.payment_failed":
        payment.payment_status = "failed"
        db.session.commit()

    elif event_type == "charge.refunded":
        payment.payment_status = "refunded"
        payment.booking.status = "cancelled"
        db.session.commit()

    return jsonify(received=True), 200
