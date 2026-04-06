"""Push notification service — FCM (deferred until Phase 17 native app)."""

import logging
import os

logger = logging.getLogger(__name__)


def is_available() -> bool:
    return bool(os.environ.get("FCM_SERVER_KEY"))


def send_push(device_token: str, title: str, body: str, data: dict = None) -> bool:
    """Send a push notification via FCM. Currently a stub — returns False."""
    if not is_available():
        return False
    logger.info("FCM push stub called: token=%s title=%s", device_token[:20], title)
    return False
