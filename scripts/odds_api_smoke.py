"""Credential-gated live smoke check for The Odds API NCAAF feed."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from edgebook.core.config import settings
from edgebook.ingestion.adapters import TheOddsApiAdapter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate The Odds API without logging keys"
    )
    parser.add_argument(
        "--historical-date",
        help="Optional ISO-8601 snapshot date; requires a historical-data entitlement",
    )
    args = parser.parse_args()
    if not settings.ODDS_API_KEY:
        print({"status": "skipped", "reason": "ODDS_API_KEY is not configured"})
        return

    adapter = TheOddsApiAdapter(
        settings.ODDS_API_KEY,
        regions=settings.ODDS_API_REGIONS,
        bookmakers=settings.ODDS_API_BOOKMAKERS,
        timeout_seconds=settings.INGESTION_HTTP_TIMEOUT_SECONDS,
        max_retries=settings.INGESTION_HTTP_MAX_RETRIES,
    )
    if args.historical_date:
        snapshot_at = datetime.fromisoformat(args.historical_date).replace(tzinfo=UTC)
        adapter.fetch_historical_sync(snapshot_at)
    else:
        adapter.fetch_current_sync()
    print(
        {
            "status": "ok",
            "events": len(adapter.games()),
            "quotes": len(adapter.quotes()),
            "quota_remaining": adapter.quota_remaining,
        }
    )


if __name__ == "__main__":
    main()
