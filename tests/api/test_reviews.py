"""API coverage for source-specific placement and human rationale review."""

from datetime import UTC, datetime

from edgebook.cfb.models import MarketQuote
from edgebook.wagering.reviews import claim_pending_reviews
from tests.api.test_wagering import create_account, create_open_market


def test_source_specific_bet_and_human_review_flow(client, db_session):
    """A selected provider quote is snapshotted and reviewed asynchronously."""
    account = create_account(client)
    game, market = create_open_market(client, market_type="MONEYLINE", line=None)
    manual_quote = next(
        quote
        for quote in client.get(f"/cfb/games/{game['id']}").json()["markets"][0][
            "quotes"
        ]
        if quote["selection"] == "HOME"
    )
    external_quote = MarketQuote(
        market_id=market["id"],
        selection="HOME",
        american_odds=125,
        source="source-a",
        source_quote_id="source-a-home-1",
        observed_at=datetime.now(UTC),
    )
    db_session.add(external_quote)
    db_session.commit()

    ambiguous = client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "HOME", "stake": "10.00"},
    )
    assert ambiguous.status_code == 422

    placed = client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market["id"],
            "quote_id": external_quote.id,
            "selection": "HOME",
            "stake": "10.00",
            "reason": "Provider-specific value",
        },
    )
    assert placed.status_code == 201
    bet = placed.json()["bet"]
    assert bet["quote_id"] == external_quote.id
    assert bet["quote_source"] == "source-a"
    assert bet["quote_source_id"] == "source-a-home-1"
    assert manual_quote["source"] == "MANUAL"

    pending = client.get(f"/accounts/{account['id']}/bets/{bet['id']}/review")
    assert pending.status_code == 200
    assert pending.json()["status"] == "PENDING"
    assert [review.bet_id for review in claim_pending_reviews(db_session)] == [
        bet["id"]
    ]

    completed = client.put(
        f"/accounts/{account['id']}/bets/{bet['id']}/review",
        json={
            "reviewer_label": "Dana",
            "summary": "Evidence is specific and testable.",
            "bias_flags": ["RECENCY_BIAS"],
            "assessment_notes": "Track result after settlement.",
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"
    assert completed.json()["bias_flags"] == ["RECENCY_BIAS"]

    reviews = client.get(f"/accounts/{account['id']}/analytics").json()[
        "review_summary"
    ]
    assert reviews["eligible"] == 1
    assert reviews["completed"] == 1
    assert reviews["coverage"] == 1.0
    assert reviews["bias_flags"] == [{"flag": "RECENCY_BIAS", "count": 1}]


def test_operator_queue_claims_reviews_and_enforces_claiming_reviewer(client):
    """Local operators can claim only pending tasks and must complete their own work."""
    account = create_account(client)
    _, market = create_open_market(client, market_type="MONEYLINE", line=None)
    placed = client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market["id"],
            "selection": "HOME",
            "stake": "10.00",
            "reason": "Review queue coverage",
        },
    )
    assert placed.status_code == 201
    bet_id = placed.json()["bet"]["id"]

    queue = client.get("/reviews?status=PENDING")
    assert queue.status_code == 200
    assert queue.json()["total"] == 1
    assert queue.json()["items"][0]["bet_id"] == bet_id

    claim = client.post(f"/reviews/{bet_id}/claim", json={"reviewer_label": "Dana"})
    assert claim.status_code == 200
    assert claim.json()["status"] == "IN_REVIEW"
    assert claim.json()["reviewer_label"] == "Dana"
    assert (
        client.post(
            f"/reviews/{bet_id}/claim", json={"reviewer_label": "Alex"}
        ).status_code
        == 409
    )

    wrong_operator = client.put(
        f"/accounts/{account['id']}/bets/{bet_id}/review",
        json={"reviewer_label": "Alex", "summary": "Cannot complete another claim."},
    )
    assert wrong_operator.status_code == 409
    completed = client.put(
        f"/accounts/{account['id']}/bets/{bet_id}/review",
        json={"reviewer_label": "Dana", "summary": "Evidence is testable."},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"
    assert (
        client.post(
            f"/reviews/{bet_id}/claim", json={"reviewer_label": "Dana"}
        ).status_code
        == 409
    )
