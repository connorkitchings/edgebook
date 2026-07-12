"""Deployment-neutral commands for sync, settlement, and review scheduling."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

from edgebook.cfb.models import Game, ScoreSyncState
from edgebook.core.database import SessionLocal
from edgebook.ingestion.adapters import ProviderConfigurationError, load_normalized_feed
from edgebook.ingestion.providers import (
    configured_provider,
    historical_provider,
    provider_statuses,
)
from edgebook.ingestion.services import (
    settle_confirmed_games,
    sync_games,
    sync_quotes,
    sync_scores,
)
from edgebook.wagering.reviews import claim_pending_reviews


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
            adapter = (
                load_normalized_feed(args.feed, args.provider)
                if args.feed
                else configured_provider(args.provider)
            )
            if not args.feed and hasattr(adapter, "fetch_current_sync"):
                adapter.fetch_current_sync()
            print(sync_games(db, adapter))
            print(sync_quotes(db, adapter))
            print(sync_scores(db, adapter))
        elif args.command == "backfill-odds":
            start = datetime.fromisoformat(args.from_date).replace(tzinfo=UTC)
            end = datetime.fromisoformat(args.to_date).replace(tzinfo=UTC)
            if end < start:
                raise ProviderConfigurationError("--to must be on or after --from")
            cursor = start
            results = []
            while cursor <= end:
                adapter = historical_provider(args.provider, cursor)
                sync_games(db, adapter)
                results.append(sync_quotes(db, adapter))
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
