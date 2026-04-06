"""Email service — SendGrid HTTP API (synchronous)."""

import logging
import os

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from sendgrid import SendGridAPIClient

        api_key = os.environ.get("SENDGRID_API_KEY", "")
        if not api_key:
            raise RuntimeError("SENDGRID_API_KEY is not set")
        _client = SendGridAPIClient(api_key)
    return _client


def is_available() -> bool:
    return bool(os.environ.get("SENDGRID_API_KEY"))


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send a single email. Returns True on success, False on failure."""
    try:
        from sendgrid.helpers.mail import Mail

        client = _get_client()
        from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@glowtrip.com")
        from_name = os.environ.get("SENDGRID_FROM_NAME", "Glow Trip")
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        response = client.send(message)
        logger.info("Email sent to %s, status=%s", to_email, response.status_code)
        return 200 <= response.status_code < 300
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
