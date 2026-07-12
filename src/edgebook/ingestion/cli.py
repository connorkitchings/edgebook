"""Deployment-neutral commands for sync, settlement, and review scheduling."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

from edgebook.application.operations import (
    claim_pending_reviews,
    settle_confirmed_games,
)
from edgebook.cfb.models import Game, ScoreSyncState
from edgebook.core.config import settings
from edgebook.core.database import SessionLocal
from edgebook.ingestion.adapters import ProviderConfigurationError, load_normalized_feed
from edgebook.ingestion.providers import (
    configured_provider,
    historical_provider,
    provider_statuses,
)
from edgebook.ingestion.services import (
    begin_backfill_checkpoint,
    complete_backfill_checkpoint,
    fail_backfill_checkpoint,
    ingestion_lock,
    sync_games,
    sync_quotes,
    sync_scores,
)

NCAAF_SPORT = "americanfootball_ncaaf"
FEATURED_MARKETS = "h2h,spreads,totals"
BACKFILL_SNAPSHOT_HOUR_UTC = 12


def _snapshot_at(value: str) -> datetime:
    """Parse an ISO date or datetime into the standard daily UTC snapshot time."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(
            hour=BACKFILL_SNAPSHOT_HOUR_UTC,
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=UTC,
        )
    return parsed.astimezone(UTC).replace(
        hour=BACKFILL_SNAPSHOT_HOUR_UTC,
        minute=0,
        second=0,
        microsecond=0,
    )


def run_current_sync(db, provider_name: str) -> dict:
    """Fetch and persist one provider snapshot while holding the scheduler lock."""
    with ingestion_lock(db):
        adapter = configured_provider(provider_name)
        if hasattr(adapter, "fetch_current_sync"):
            adapter.fetch_current_sync()
        games = sync_games(db, adapter)
        quotes = sync_quotes(db, adapter)
        scores = sync_scores(db, adapter)
    return {"games": games, "quotes": quotes, "scores": scores}


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Edgebook ingestion operations")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync = subparsers.add_parser("sync")
    sync.add_argument("--provider", required=True)
    sync.add_argument("--feed", type=Path)
    backfill = subparsers.add_parser("backfill-odds")
    backfill.add_argument("--provider", required=True)
    backfill.add_argument("--from", dest="from_date", required=True)
    backfill.add_argument("--to", dest="to_date", required=True)
    subparsers.add_parser("settle-confirmed")
    reviews = subparsers.add_parser("claim-reviews")
    reviews.add_argument("--limit", type=int, default=50)
    subparsers.add_parser("report")
    subparsers.add_parser("providers")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        if args.command == "sync":
            if args.feed:
                adapter = load_normalized_feed(args.feed, args.provider)
                with ingestion_lock(db):
                    print(sync_games(db, adapter))
                    print(sync_quotes(db, adapter))
                    print(sync_scores(db, adapter))
            else:
                print(run_current_sync(db, args.provider))
        elif args.command == "backfill-odds":
            start = _snapshot_at(args.from_date)
            end = _snapshot_at(args.to_date)
            if end < start:
                raise ProviderConfigurationError("--to must be on or after --from")
            cursor = start
            results = []
            with ingestion_lock(db):
                while cursor <= end:
                    checkpoint = begin_backfill_checkpoint(
                        db,
                        provider=args.provider,
                        sport=NCAAF_SPORT,
                        markets=FEATURED_MARKETS,
                        bookmakers=settings.ODDS_API_BOOKMAKERS,
                        requested_snapshot_at=cursor,
                    )
                    if checkpoint is None:
                        results.append(
                            {"snapshot_at": cursor.isoformat(), "skipped": True}
                        )
                        cursor += timedelta(days=1)
                        continue
                    try:
                        historical_adapter = historical_provider(args.provider, cursor)
                        sync_games(db, historical_adapter, requested_snapshot_at=cursor)
                        quote_result = sync_quotes(
                            db, historical_adapter, requested_snapshot_at=cursor
                        )
                        complete_backfill_checkpoint(
                            db, checkpoint, run_id=quote_result["run_id"]
                        )
                        results.append(quote_result)
                    except Exception as error:
                        fail_backfill_checkpoint(db, checkpoint, error)
                        raise
                    if (
                        historical_adapter.quota_remaining is not None
                        and historical_adapter.quota_remaining
                        < settings.INGESTION_MIN_QUOTA_REMAINING
                    ):
                        raise ProviderConfigurationError(
                            "Stopping backfill before provider quota exhaustion"
                        )
                    cursor += timedelta(days=1)
            print({"snapshots": len(results), "runs": results})
        elif args.command == "settle-confirmed":
            print({"settled": settle_confirmed_games(db)})
        elif args.command == "claim-reviews":
            print(
                {
                    "claimed": [
                        review.bet_id
                        for review in claim_pending_reviews(db, limit=args.limit)
                    ]
                }
            )
        elif args.command == "report":
            print(
                {
                    "conflicted_games": db.scalar(
                        select(func.count())
                        .select_from(Game)
                        .where(Game.score_sync_state == ScoreSyncState.CONFLICTED.value)
                    ),
                }
            )
        else:
            print([status.__dict__ for status in provider_statuses()])
    finally:
        db.close()


if __name__ == "__main__":
    main()
