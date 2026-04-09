"""Push notification service — FCM legacy HTTP API."""

import logging
import os
import requests

logger = logging.getLogger(__name__)


def is_available() -> bool:
    return bool(os.environ.get("FCM_SERVER_KEY"))


def send_push(device_token: str, title: str, body: str, data: dict = None) -> bool:
    """Send a push notification via FCM legacy API."""
    if not is_available():
        return False
    try:
        payload = {
            "to": device_token,
            "priority": "high",
            "notification": {"title": title, "body": body},
            "data": data or {},
        }
        headers = {
            "Authorization": f"key={os.environ.get('FCM_SERVER_KEY')}",
            "Content-Type": "application/json",
        }
        res = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            json=payload,
            headers=headers,
            timeout=5,
        )
        if res.status_code != 200:
            logger.warning("FCM push failed: status=%s body=%s", res.status_code, res.text[:200])
            return False
        body_json = res.json()
        return body_json.get("success", 0) >= 1
    except Exception:
        logger.exception("send_push failed")
        return False
