"""Dedicated daily pregame scheduler, intentionally outside FastAPI."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from edgebook.core.database import SessionLocal
from edgebook.ingestion.cli import run_current_sync

LOGGER = logging.getLogger(__name__)
NEW_YORK = ZoneInfo("America/New_York")


def next_run_at(now: datetime | None = None) -> datetime:
    """Return the next 08:00 America/New_York scheduler instant."""
    current = (now or datetime.now(NEW_YORK)).astimezone(NEW_YORK)
    target = current.replace(hour=8, minute=0, second=0, microsecond=0)
    if target <= current:
        target += timedelta(days=1)
    return target


def run_once() -> dict:
    """Run one safe current-odds collection cycle."""
    db = SessionLocal()
    try:
        return run_current_sync(db, "the-odds-api")
    finally:
        db.close()


def main() -> None:  # pragma: no cover - long-running deployment process
    logging.basicConfig(level=logging.INFO)
    while True:
        target = next_run_at()
        delay = max((target - datetime.now(NEW_YORK)).total_seconds(), 0)
        LOGGER.info("Next pregame odds sync at %s", target.isoformat())
        time.sleep(delay)
        try:
            LOGGER.info("Completed pregame odds sync: %s", run_once())
        except Exception:
            LOGGER.exception("Pregame odds sync failed; retrying at the next schedule")


if __name__ == "__main__":  # pragma: no cover
    main()
