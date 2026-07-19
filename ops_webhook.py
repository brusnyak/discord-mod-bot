import json
import logging
import urllib.request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def send_to_ops_lab(
    webhook_url: str,
    event_id: str,
    author_name: str,
    author_username: str,
    content: str,
):
    """Post a Discord-shaped event to the messaging-bot-ops-lab backend."""
    payload = json.dumps({
        "id": event_id,
        "type": 0,
        "content": content,
        "channel_id": "0",
        "author": {
            "id": "0",
            "username": author_username,
            "global_name": author_name,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }).encode()

    try:
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        logger.warning("ops-lab webhook failed: %s", exc)
