"""End-to-end API coverage for the manual simulated wagering flow."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from edgebook.cfb.models import Game, GameStatus, MarketSelection, ScoreCorrection
from edgebook.ledger.models import Account, Transaction, TransactionType
from edgebook.wagering import services as wagering_services
from edgebook.wagering.models import Bet, BetStatus
from edgebook.wagering.services import (
    WagerConflictError,
    place_bet,
    record_game_result,
)


def create_account(client, bankroll: str = "100.00") -> dict:
    response = client.post(
        "/accounts",
        json={"owner_name": "Test Allocator", "starting_bankroll": bankroll},
    )
    assert response.status_code == 201
    return response.json()


def create_open_market(
    client,
    *,
    market_type: str = "SPREAD",
    line: str | None = "-3.500",
    odds: tuple[int, int] = (-110, -110),
) -> tuple[dict, dict]:
    home = client.post("/cfb/teams", json={"name": "Home State"}).json()
    away = client.post("/cfb/teams", json={"name": "Away Tech"}).json()
    game_response = client.post(
        "/cfb/games",
        json={
            "home_team_id": home["id"],
            "away_team_id": away["id"],
            "scheduled_at": "2026-09-05T19:30:00Z",
        },
    )
    assert game_response.status_code == 201
    game = game_response.json()
    market_payload = {"market_type": market_type, "line": line}
    market_response = client.post(
        f"/cfb/games/{game['id']}/markets", json=market_payload
    )
    assert market_response.status_code == 201
    market = market_response.json()
    selections = ("OVER", "UNDER") if market_type == "TOTAL" else ("HOME", "AWAY")
    for selection, american_odds in zip(selections, odds, strict=True):
        assert (
            client.post(
                f"/cfb/markets/{market['id']}/quotes",
                json={"selection": selection, "american_odds": american_odds},
            ).status_code
            == 201
        )
    return game, market


def test_place_bet_snapshots_quote_debits_ledger_and_is_idempotent(client, db_session):
    account = create_account(client)
    _, market = create_open_market(client)
    payload = {
        "market_id": market["id"],
        "selection": "HOME",
        "stake": "10.00",
        "reason": "  Strong line value  ",
    }
    first = client.post(
        f"/accounts/{account['id']}/bets",
        json=payload,
        headers={"Idempotency-Key": "week-1-home"},
    )
    assert first.status_code == 201
    body = first.json()
    assert body["current_balance"] == "90.00"
    assert (
        body["bet"]
        | {
            "status": "PENDING",
            "stake": "10.00",
            "bankroll_before": "100.00",
            "line": "-3.500",
            "american_odds": -110,
            "reason": "Strong line value",
        }
        == body["bet"]
    )

    second = client.post(
        f"/accounts/{account['id']}/bets",
        json=payload,
        headers={"Idempotency-Key": "week-1-home"},
    )
    assert second.status_code == 201
    assert second.json()["bet"]["id"] == body["bet"]["id"]
    assert second.json()["current_balance"] == "90.00"
    mismatched = client.post(
        f"/accounts/{account['id']}/bets",
        json=payload | {"stake": "11.00"},
        headers={"Idempotency-Key": "week-1-home"},
    )
    assert mismatched.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(Bet)) == 1
    wager_postings = db_session.scalars(
        select(Transaction).where(
            Transaction.transaction_type == TransactionType.WAGER_STAKE.value
        )
    ).all()
    assert sorted(posting.amount_cents for posting in wager_postings) == [-1000, 1000]


def test_placement_validation_cutoff_and_account_state(client, db_session):
    account = create_account(client, "5.00")
    game, market = create_open_market(client)
    endpoint = f"/accounts/{account['id']}/bets"
    assert (
        client.post(
            endpoint,
            json={"market_id": market["id"], "selection": "OVER", "stake": "1.00"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            endpoint,
            json={"market_id": market["id"], "selection": "HOME", "stake": "6.00"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/accounts/missing/bets",
            json={"market_id": market["id"], "selection": "HOME", "stake": "1.00"},
        ).status_code
        == 404
    )

    stored_account = db_session.get(Account, account["id"])
    assert stored_account is not None
    stored_account.is_active = False
    db_session.commit()
    assert (
        client.post(
            endpoint,
            json={"market_id": market["id"], "selection": "HOME", "stake": "1.00"},
        ).status_code
        == 409
    )
    stored_account.is_active = True
    db_session.commit()

    with pytest.raises(WagerConflictError, match="30 minutes"):
        place_bet(
            db_session,
            account_id=account["id"],
            market_id=market["id"],
            selection=MarketSelection.HOME,
            stake_cents=100,
            reason=None,
            now=datetime(2026, 9, 5, 19, 0, tzinfo=UTC),
        )
    assert game["scheduled_at"].startswith("2026-09-05T19:30:00")


def test_draft_market_rejects_placement(client):
    account = create_account(client)
    home = client.post("/cfb/teams", json={"name": "Draft Home"}).json()
    away = client.post("/cfb/teams", json={"name": "Draft Away"}).json()
    game = client.post(
        "/cfb/games",
        json={
            "home_team_id": home["id"],
            "away_team_id": away["id"],
            "scheduled_at": "2026-09-05T19:30:00Z",
        },
    ).json()
    market = client.post(
        f"/cfb/games/{game['id']}/markets",
        json={"market_type": "MONEYLINE", "line": None},
    ).json()
    response = client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "HOME", "stake": "1.00"},
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "market_type,line,selection,odds,scores,expected_status,expected_payout",
    [
        ("MONEYLINE", None, "HOME", 150, (21, 17), "WON", "25.00"),
        ("MONEYLINE", None, "AWAY", -110, (21, 17), "LOST", "0.00"),
        ("MONEYLINE", None, "HOME", -110, (17, 17), "PUSH", "10.00"),
        ("SPREAD", "-3.500", "HOME", -110, (24, 20), "WON", "19.09"),
        ("SPREAD", "-3.000", "AWAY", -110, (20, 17), "PUSH", "10.00"),
        ("TOTAL", "41.500", "OVER", -110, (24, 20), "WON", "19.09"),
        ("TOTAL", "44.000", "UNDER", -110, (24, 20), "PUSH", "10.00"),
    ],
)
def test_settlement_rules_and_payouts(
    client,
    market_type,
    line,
    selection,
    odds,
    scores,
    expected_status,
    expected_payout,
):
    account = create_account(client)
    game, market = create_open_market(
        client, market_type=market_type, line=line, odds=(odds, -110)
    )
    placed = client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": selection, "stake": "10.00"},
    )
    assert placed.status_code == 201
    bet_id = placed.json()["bet"]["id"]
    result = client.put(
        f"/cfb/games/{game['id']}/result",
        json={"home_score": scores[0], "away_score": scores[1]},
    )
    assert result.status_code == 200
    assert result.json()["status"] == "FINAL"
    history = client.get(f"/accounts/{account['id']}/bets/{bet_id}").json()
    assert history["status"] == expected_status
    assert history["payout"] == expected_payout
    expected_balance = 9000 + int(Decimal(expected_payout) * 100)
    assert (
        client.get(f"/accounts/{account['id']}").json()["current_balance"]
        == f"{expected_balance / 100:.2f}"
    )


def test_final_score_is_idempotent_and_history_is_paginated_and_isolated(client):
    account = create_account(client)
    other_account = client.post(
        "/accounts", json={"owner_name": "Other", "starting_bankroll": "100.00"}
    ).json()
    game, market = create_open_market(client, market_type="TOTAL", line="40.000")
    bet = client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "OVER", "stake": "5.00"},
    ).json()["bet"]
    score = {"home_score": 21, "away_score": 20}
    assert client.put(f"/cfb/games/{game['id']}/result", json=score).status_code == 200
    assert client.put(f"/cfb/games/{game['id']}/result", json=score).status_code == 200
    assert (
        client.put(
            f"/cfb/games/{game['id']}/result", json={"home_score": 20, "away_score": 20}
        ).status_code
        == 409
    )

    page = client.get(f"/accounts/{account['id']}/bets?limit=1&offset=0").json()
    assert page["total"] == 1 and page["items"][0]["id"] == bet["id"]
    assert (
        client.get(f"/accounts/{other_account['id']}/bets/{bet['id']}").status_code
        == 404
    )
    assert client.get("/accounts/missing/bets").status_code == 404


def test_settlement_failure_rolls_back_score_bet_and_payout(
    client, db_session, monkeypatch
):
    account = create_account(client)
    game, market = create_open_market(client, market_type="MONEYLINE", line=None)
    client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "HOME", "stake": "10.00"},
    )

    def fail_payout(*args, **kwargs):
        raise RuntimeError("forced payout failure")

    monkeypatch.setattr(wagering_services, "post_wager_transaction", fail_payout)
    with pytest.raises(RuntimeError, match="forced payout"):
        record_game_result(db_session, game_id=game["id"], home_score=21, away_score=17)
    db_session.expire_all()
    stored_game = db_session.get(Game, game["id"])
    stored_bet = db_session.scalar(select(Bet).where(Bet.game_id == game["id"]))
    assert stored_game is not None and stored_game.status == GameStatus.SCHEDULED.value
    assert stored_game.home_score is None and stored_game.away_score is None
    assert stored_bet is not None and stored_bet.status == BetStatus.PENDING.value
    assert stored_bet.payout_transaction_id is None


def test_place_bet_with_structured_reasoning_fields(client, db_session):
    """Bets accept rationale_category and notes alongside the legacy reason field."""
    account = create_account(client)
    _, market = create_open_market(client)
    payload = {
        "market_id": market["id"],
        "selection": "HOME",
        "stake": "10.00",
        "rationale_category": "LINE_VALUE",
        "notes": "Spread is 2 points off my model",
    }
    response = client.post(f"/accounts/{account['id']}/bets", json=payload)
    assert response.status_code == 201
    body = response.json()["bet"]
    assert body["rationale_category"] == "LINE_VALUE"
    assert body["notes"] == "Spread is 2 points off my model"
    assert body["reason"] is None

    stored = db_session.scalar(select(Bet).where(Bet.id == body["id"]))
    assert stored is not None
    assert stored.rationale_category == "LINE_VALUE"
    assert stored.notes == "Spread is 2 points off my model"


def test_place_bet_rejects_invalid_rationale_category(client):
    """An invalid rationale category returns a 422."""
    account = create_account(client)
    _, market = create_open_market(client)
    response = client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market["id"],
            "selection": "HOME",
            "stake": "10.00",
            "rationale_category": "GUT_FEELING",
        },
    )
    assert response.status_code == 422


def test_structured_reasoning_idempotency_check(client):
    """Idempotency replay checks notes and rationale_category for conflicts."""
    account = create_account(client)
    _, market = create_open_market(client)
    payload = {
        "market_id": market["id"],
        "selection": "HOME",
        "stake": "10.00",
        "rationale_category": "MATCHUP_ANALYSIS",
        "notes": "Strong defensive edge",
    }
    first = client.post(
        f"/accounts/{account['id']}/bets",
        json=payload,
        headers={"Idempotency-Key": "reasoning-1"},
    )
    assert first.status_code == 201
    replay = client.post(
        f"/accounts/{account['id']}/bets",
        json=payload,
        headers={"Idempotency-Key": "reasoning-1"},
    )
    assert replay.status_code == 201
    assert replay.json()["bet"]["id"] == first.json()["bet"]["id"]

    mismatched = client.post(
        f"/accounts/{account['id']}/bets",
        json=payload | {"rationale_category": "CONTRARIAN"},
        headers={"Idempotency-Key": "reasoning-1"},
    )
    assert mismatched.status_code == 409


def test_score_correction_reverses_and_re_settles_with_audit_trail(client, db_session):
    """Correcting a final score reverses payouts and re-settles atomically."""
    account = create_account(client)
    game, market = create_open_market(
        client, market_type="MONEYLINE", line=None, odds=(-110, 150)
    )
    placed = client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "HOME", "stake": "10.00"},
    )
    assert placed.status_code == 201

    client.put(
        f"/cfb/games/{game['id']}/result",
        json={"home_score": 21, "away_score": 17},
    )

    corrections_before = db_session.scalar(
        select(func.count()).select_from(ScoreCorrection)
    )
    assert corrections_before == 0

    correction = client.put(
        f"/cfb/games/{game['id']}/correction",
        json={
            "home_score": 17,
            "away_score": 21,
            "reason": "Official score correction after review",
        },
    )
    assert correction.status_code == 200
    assert correction.json()["status"] == "FINAL"
    assert correction.json()["home_score"] == 17
    assert correction.json()["away_score"] == 21

    bet_detail = client.get(
        f"/accounts/{account['id']}/bets/{placed.json()['bet']['id']}"
    ).json()
    assert bet_detail["status"] == "LOST"
    assert bet_detail["payout"] == "0.00"

    corrections_after = db_session.scalar(
        select(func.count()).select_from(ScoreCorrection)
    )
    assert corrections_after == 1

    adjustment_postings = db_session.scalars(
        select(Transaction).where(
            Transaction.transaction_type == TransactionType.ADJUSTMENT.value
        )
    ).all()
    assert len(adjustment_postings) == 2
    signed_amounts = sorted(t.amount_cents for t in adjustment_postings)
    assert signed_amounts[0] < 0
    assert signed_amounts[1] > 0
    assert signed_amounts[0] + signed_amounts[1] == 0


def test_score_correction_validates_final_state_and_reason(client):
    """Score correction only works on finalized games and requires a reason."""
    game, market = create_open_market(client, market_type="MONEYLINE", line=None)

    assert (
        client.put(
            f"/cfb/games/{game['id']}/correction",
            json={"home_score": 21, "away_score": 17, "reason": "test"},
        ).status_code
        == 409
    )

    client.put(
        f"/cfb/games/{game['id']}/result",
        json={"home_score": 21, "away_score": 17},
    )

    assert (
        client.put(
            f"/cfb/games/{game['id']}/correction",
            json={"home_score": 21, "away_score": 17, "reason": "no change"},
        ).status_code
        == 422
    )

    assert (
        client.put(
            f"/cfb/games/{game['id']}/correction",
            json={"home_score": 17, "away_score": 21, "reason": "  "},
        ).status_code
        == 422
    )

    assert (
        client.put(
            "/cfb/games/missing/correction",
            json={"home_score": 17, "away_score": 21, "reason": "test"},
        ).status_code
        == 404
    )


def test_score_correction_handles_repeated_changes_for_inactive_accounts(
    client, db_session
):
    """Re-settlement stays balanced through repeated corrections after deactivation."""
    account = create_account(client)
    game, market = create_open_market(
        client, market_type="MONEYLINE", line=None, odds=(-110, 150)
    )
    placed = client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "HOME", "stake": "10.00"},
    )
    assert placed.status_code == 201
    bet_id = placed.json()["bet"]["id"]

    assert (
        client.put(
            f"/cfb/games/{game['id']}/result",
            json={"home_score": 10, "away_score": 21},
        ).status_code
        == 200
    )

    stored_account = db_session.get(Account, account["id"])
    assert stored_account is not None
    stored_account.is_active = False
    db_session.commit()

    first_correction = client.put(
        f"/cfb/games/{game['id']}/correction",
        json={"home_score": 17, "away_score": 17, "reason": "Official tie correction"},
    )
    assert first_correction.status_code == 200
    assert (
        client.get(f"/accounts/{account['id']}/bets/{bet_id}").json()["status"]
        == "PUSH"
    )
    assert (
        client.post(f"/accounts/{account['id']}/reconcile").json()["is_balanced"]
        is True
    )

    second_correction = client.put(
        f"/cfb/games/{game['id']}/correction",
        json={"home_score": 21, "away_score": 17, "reason": "Final score review"},
    )
    assert second_correction.status_code == 200
    corrected_bet = client.get(f"/accounts/{account['id']}/bets/{bet_id}").json()
    assert corrected_bet["status"] == "WON"
    assert corrected_bet["payout"] == "19.09"
    assert (
        client.post(f"/accounts/{account['id']}/reconcile").json()["is_balanced"]
        is True
    )
    assert db_session.scalar(select(func.count()).select_from(ScoreCorrection)) == 2
