"""Notification orchestrator — ties together templates, email service, and DB logging."""

import logging
from datetime import datetime, timezone

from flask import render_template

from app import db
from app.models.notification import Notification
from app.services import email as email_service

logger = logging.getLogger(__name__)

SUBJECTS = {
    "booking_created": {
        "ko": "새 예약이 접수되었습니다",
        "en": "New Booking Received",
        "ja": "新しい予約が届きました",
        "zh": "收到新预约",
    },
    "booking_confirmed": {
        "ko": "예약이 확정되었습니다",
        "en": "Booking Confirmed",
        "ja": "予約が確定しました",
        "zh": "预约已确认",
    },
    "booking_cancelled": {
        "ko": "예약이 취소되었습니다",
        "en": "Booking Cancelled",
        "ja": "予約がキャンセルされました",
        "zh": "预约已取消",
    },
    "booking_completed": {
        "ko": "시술이 완료되었습니다",
        "en": "Service Completed",
        "ja": "施術が完了しました",
        "zh": "服务已完成",
    },
    "booking_noshow": {
        "ko": "노쇼 처리되었습니다",
        "en": "Marked as No-Show",
        "ja": "ノーショー処理されました",
        "zh": "已标记为未到店",
    },
    "payment_failed": {
        "ko": "결제에 실패했습니다",
        "en": "Payment Failed",
        "ja": "決済に失敗しました",
        "zh": "支付失败",
    },
    "payment_refunded": {
        "ko": "환불 처리되었습니다",
        "en": "Refund Processed",
        "ja": "返金処理されました",
        "zh": "退款已处理",
    },
    "booking_reminder": {
        "ko": "예약 리마인더",
        "en": "Booking Reminder",
        "ja": "予約リマインダー",
        "zh": "预约提醒",
    },
}


def _build_context(booking, recipient):
    """Build template context dict from booking and recipient."""
    return {
        "lang": recipient.language or "en",
        "recipient_name": recipient.name or recipient.email,
        "shop_name": booking.shop.name,
        "shop_address": booking.shop.address or "",
        "shop_phone": booking.shop.phone or "",
        "menu_title": booking.menu.title,
        "menu_price": booking.menu.price,
        "menu_duration": booking.menu.duration,
        "booking_time": booking.booking_time.strftime("%Y-%m-%d %H:%M"),
        "booking_status": booking.status,
        "amount": booking.payment.amount if booking.payment else booking.menu.price,
        "currency": booking.payment.currency if booking.payment else "KRW",
    }


def notify(booking, recipient, notification_type: str) -> bool:
    """Send a notification for a booking event.

    This function NEVER raises. If email service is unavailable or sending fails,
    it logs the error and returns False.
    """
    try:
        if not email_service.is_available():
            logger.info("Email service unavailable, skipping %s", notification_type)
            return False

        lang = recipient.language or "en"
        context = _build_context(booking, recipient)
        html_content = render_template(f"email/{notification_type}.html", **context)

        subject_map = SUBJECTS.get(notification_type, {})
        subject = subject_map.get(lang, subject_map.get("en", "Glow Trip"))

        notif = Notification(
            booking_id=booking.id,
            recipient_id=recipient.id,
            channel="email",
            notification_type=notification_type,
            status="pending",
        )
        db.session.add(notif)
        db.session.flush()

        success = email_service.send_email(recipient.email, subject, html_content)

        notif.status = "sent" if success else "failed"
        if not success:
            notif.error_message = "Email send returned failure"
        notif.sent_at = datetime.now(timezone.utc) if success else None
        db.session.commit()

        return success

    except Exception:
        logger.exception("notify() failed for booking=%s type=%s", booking.id, notification_type)
        try:
            db.session.rollback()
        except Exception:
            pass
        return False


def notify_owner(booking, notification_type: str) -> bool:
    """Send notification to shop owner."""
    return notify(booking, booking.shop.owner, notification_type)


def notify_customer(booking, notification_type: str) -> bool:
    """Send notification to booking customer."""
    return notify(booking, booking.user, notification_type)
