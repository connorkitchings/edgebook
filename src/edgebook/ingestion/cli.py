"""Deployment-neutral commands for sync, settlement, and review scheduling."""

from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import func, select

from edgebook.cfb.models import Game, ScoreSyncState
from edgebook.core.database import SessionLocal
from edgebook.ingestion.adapters import load_normalized_feed
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
    sync.add_argument("--feed", type=Path, required=True)
    subparsers.add_parser("settle-confirmed")
    reviews = subparsers.add_parser("claim-reviews")
    reviews.add_argument("--limit", type=int, default=50)
    subparsers.add_parser("report")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        if args.command == "sync":
            adapter = load_normalized_feed(args.feed, args.provider)
            print(sync_games(db, adapter))
            print(sync_quotes(db, adapter))
            print(sync_scores(db, adapter))
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
        else:
            print(
                {
                    "conflicted_games": db.scalar(
                        select(func.count())
                        .select_from(Game)
                        .where(Game.score_sync_state == ScoreSyncState.CONFLICTED.value)
                    ),
                }
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
