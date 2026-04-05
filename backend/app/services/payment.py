"""결제 서비스 — Stripe PaymentIntent 기반 Auth & Capture"""

import logging

import stripe
from flask import current_app

logger = logging.getLogger(__name__)


def _init_stripe():
    key = current_app.config.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    stripe.api_key = key


def create_payment_intent(amount: int, currency: str = "krw", metadata: dict = None) -> dict:
    """PaymentIntent 생성 (가승인 — capture_method=manual).

    Returns:
        {"client_secret": str, "payment_intent_id": str}
    """
    _init_stripe()
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency.lower(),
        capture_method="manual",
        metadata=metadata or {},
    )
    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
    }


def capture_payment(payment_intent_id: str) -> dict:
    """가승인된 PaymentIntent를 매입(확정)."""
    _init_stripe()
    intent = stripe.PaymentIntent.capture(payment_intent_id)
    return {
        "payment_intent_id": intent.id,
        "status": intent.status,
        "amount_captured": intent.amount_received,
    }


def refund_payment(payment_intent_id: str, amount: int = None) -> dict:
    """결제 환불. amount 미지정 시 전액 환불."""
    _init_stripe()
    params = {"payment_intent": payment_intent_id}
    if amount:
        params["amount"] = amount
    refund = stripe.Refund.create(**params)
    return {
        "refund_id": refund.id,
        "status": refund.status,
        "amount": refund.amount,
    }


def retrieve_payment_intent(payment_intent_id: str) -> dict:
    """PaymentIntent 상태 조회."""
    _init_stripe()
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    return {
        "payment_intent_id": intent.id,
        "status": intent.status,
        "amount": intent.amount,
        "amount_received": intent.amount_received,
    }
