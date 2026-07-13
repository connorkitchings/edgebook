"""Best-effort webhook notifications for operational events.

Delivery is fire-and-forget: a short bounded timeout is used and any network
error is logged but never raised, so alerting can never break ingestion. There
is no retry queue; configure a dead-letter/retry policy at the webhook target
if guaranteed delivery is required.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from edgebook.core.config import settings

LOGGER = logging.getLogger(__name__)


def notify_ingestion_failure(
    *,
    run_id: str,
    provider: str,
    scope: str,
    error: str,
    started_at: datetime | None,
    quota_remaining: int | None,
) -> None:
    """POST an ingestion-failure alert when ``ALERT_WEBHOOK_URL`` is configured.

    No-op when the webhook URL is empty. Never raises: transport errors are
    logged at WARNING level so ingestion continues unaffected.
    """
    url = settings.ALERT_WEBHOOK_URL
    if not url:
        return

    payload: dict[str, Any] = {
        "event": "ingestion.run_failed",
        "run_id": run_id,
        "provider": provider,
        "scope": scope,
        "error": error[:1000],
        "started_at": started_at.isoformat() if started_at else None,
        "quota_remaining": quota_remaining,
        "notified_at": datetime.now(UTC).isoformat(),
    }

    try:
        httpx.post(url, json=payload, timeout=settings.ALERT_WEBHOOK_TIMEOUT_SECONDS)
    except Exception as exc:
        LOGGER.warning("Alert webhook delivery failed: %s", exc)
