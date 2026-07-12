"""Asynchronous human-review workflow for placed bet rationales."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from edgebook.wagering.models import Bet, BetReview, ReviewStatus


class ReviewError(Exception):
    """Base exception for human-review workflow failures."""


class ReviewNotFoundError(ReviewError):
    pass


class ReviewConflictError(ReviewError):
    pass


@dataclass(frozen=True)
class ReviewQueueItem:
    """Operator-facing review task enriched with immutable bet context."""

    bet_id: str
    account_id: str
    status: str
    reviewer_label: str | None
    rationale_category: str | None
    reason: str | None
    notes: str | None
    quote_source: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


def get_review(db: Session, bet_id: str) -> BetReview:
    review = db.scalar(select(BetReview).where(BetReview.bet_id == bet_id))
    if review is None:
        raise ReviewNotFoundError(f"Review for bet {bet_id} was not found")
    return review


def claim_pending_reviews(db: Session, *, limit: int = 50) -> list[BetReview]:
    """Mark a bounded batch as in review without doing model execution."""
    reviews = list(
        db.scalars(
            select(BetReview)
            .where(BetReview.status == ReviewStatus.PENDING.value)
            .order_by(BetReview.created_at.asc())
            .limit(limit)
        )
    )
    now = datetime.now(UTC)
    for review in reviews:
        review.status = ReviewStatus.IN_REVIEW.value
        review.started_at = now
    db.commit()
    return reviews


def claim_review(db: Session, *, bet_id: str, reviewer_label: str) -> BetReview:
    """Atomically claim a pending review for one named local operator."""
    label = reviewer_label.strip()
    if not label:
        raise ReviewConflictError("Reviewer label is required")
    claimed = db.execute(
        update(BetReview)
        .where(
            BetReview.bet_id == bet_id,
            BetReview.status == ReviewStatus.PENDING.value,
        )
        .values(
            status=ReviewStatus.IN_REVIEW.value,
            reviewer_label=label,
            started_at=datetime.now(UTC),
        )
    )
    if claimed.rowcount != 1:
        db.rollback()
        raise ReviewConflictError("Only pending reviews can be claimed")
    db.commit()
    return get_review(db, bet_id)


def list_reviews(
    db: Session,
    *,
    status: ReviewStatus | None = None,
    account_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ReviewQueueItem], int]:
    """List review tasks with their wager context, newest actionable tasks first."""
    filters = []
    if status is not None:
        filters.append(BetReview.status == status.value)
    if account_id is not None:
        filters.append(Bet.account_id == account_id)
    query = (
        select(BetReview, Bet)
        .join(Bet, BetReview.bet_id == Bet.id)
        .where(*filters)
        .order_by(BetReview.created_at.asc(), BetReview.id.asc())
        .limit(limit)
        .offset(offset)
    )
    total = int(
        db.scalar(
            select(func.count())
            .select_from(BetReview)
            .join(Bet, BetReview.bet_id == Bet.id)
            .where(*filters)
        )
        or 0
    )
    return (
        [
            ReviewQueueItem(
                bet_id=review.bet_id,
                account_id=bet.account_id,
                status=review.status,
                reviewer_label=review.reviewer_label,
                rationale_category=bet.rationale_category,
                reason=bet.reason,
                notes=bet.notes,
                quote_source=bet.quote_source,
                created_at=review.created_at,
                started_at=review.started_at,
                completed_at=review.completed_at,
            )
            for review, bet in db.execute(query).all()
        ],
        total,
    )


def get_review_queue_item(db: Session, bet_id: str) -> ReviewQueueItem:
    """Return one operator-facing review task or raise the standard not-found error."""
    query = (
        select(BetReview, Bet)
        .join(Bet, BetReview.bet_id == Bet.id)
        .where(BetReview.bet_id == bet_id)
    )
    row = db.execute(query).one_or_none()
    if row is None:
        raise ReviewNotFoundError(f"Review for bet {bet_id} was not found")
    review, bet = row
    return ReviewQueueItem(
        bet_id=review.bet_id,
        account_id=bet.account_id,
        status=review.status,
        reviewer_label=review.reviewer_label,
        rationale_category=bet.rationale_category,
        reason=bet.reason,
        notes=bet.notes,
        quote_source=bet.quote_source,
        created_at=review.created_at,
        started_at=review.started_at,
        completed_at=review.completed_at,
    )


def complete_review(
    db: Session,
    *,
    bet_id: str,
    reviewer_label: str,
    summary: str,
    bias_flags: list[str],
    assessment_notes: str | None,
    review_version: str = "human-v1",
) -> BetReview:
    review = get_review(db, bet_id)
    if review.status in {
        ReviewStatus.COMPLETED.value,
        ReviewStatus.NOT_APPLICABLE.value,
    }:
        raise ReviewConflictError("Review is already terminal")
    if not reviewer_label.strip() or not summary.strip():
        raise ReviewConflictError("Reviewer label and summary are required")
    if review.reviewer_label and review.reviewer_label != reviewer_label.strip():
        raise ReviewConflictError("Only the claiming reviewer can complete this review")
    review.status = ReviewStatus.COMPLETED.value
    review.reviewer_label = reviewer_label.strip()
    review.summary = summary.strip()
    review.bias_flags = json.dumps(sorted(set(bias_flags)))
    review.assessment_notes = assessment_notes.strip() if assessment_notes else None
    review.review_version = review_version
    review.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(review)
    return review
