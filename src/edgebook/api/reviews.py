"""Local-operator queue endpoints for human wager-rationale reviews."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from edgebook.core.database import get_db
from edgebook.core.templates import templates
from edgebook.wagering.models import ReviewStatus
from edgebook.wagering.reviews import (
    ReviewConflictError,
    ReviewNotFoundError,
    ReviewQueueItem,
    claim_review,
    get_review_queue_item,
    list_reviews,
)

router = APIRouter(prefix="/reviews", tags=["review-operations"])


class ReviewQueueResponse(BaseModel):
    bet_id: str
    account_id: str
    status: ReviewStatus
    reviewer_label: str | None
    rationale_category: str | None
    reason: str | None
    notes: str | None
    quote_source: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ReviewQueuePage(BaseModel):
    items: list[ReviewQueueResponse]
    total: int
    limit: int
    offset: int


class ReviewClaim(BaseModel):
    reviewer_label: str = Field(min_length=1, max_length=200)


def _response(item: ReviewQueueItem) -> ReviewQueueResponse:
    return ReviewQueueResponse(**item.__dict__)


@router.get("", response_model=None, responses={200: {"model": ReviewQueuePage}})
def list_reviews_endpoint(
    request: Request,
    status: ReviewStatus | None = None,
    account_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ReviewQueuePage | HTMLResponse:
    """List review tasks as JSON, or render the local operator queue for browsers."""
    items, total = list_reviews(
        db, status=status, account_id=account_id, limit=limit, offset=offset
    )
    page = ReviewQueuePage(
        items=[_response(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
    if "text/html" in request.headers.get("accept", ""):
        status_counts = {
            review_status.value: list_reviews(db, status=review_status, limit=1)[1]
            for review_status in ReviewStatus
        }
        return templates.TemplateResponse(
            request,
            "reviews.html",
            {
                "active_page": "reviews",
                "reviews": items,
                "total": total,
                "selected_status": status.value if status else "",
                "statuses": list(ReviewStatus),
                "status_counts": status_counts,
            },
        )
    return page


@router.post("/{bet_id}/claim", response_model=ReviewQueueResponse)
def claim_review_endpoint(
    bet_id: str, payload: ReviewClaim, db: Session = Depends(get_db)
) -> ReviewQueueResponse:
    """Claim a pending review for the named local operator."""
    try:
        review = claim_review(db, bet_id=bet_id, reviewer_label=payload.reviewer_label)
        return _response(get_review_queue_item(db, review.bet_id))
    except ReviewNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReviewConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
