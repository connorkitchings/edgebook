"""Asynchronous human-review workflow for placed bet rationales."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from edgebook.wagering.models import BetReview, ReviewStatus


class ReviewError(Exception):
    """Base exception for human-review workflow failures."""


class ReviewNotFoundError(ReviewError):
    pass


class ReviewConflictError(ReviewError):
    pass


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
