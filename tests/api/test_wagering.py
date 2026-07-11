"""End-to-end API coverage for the manual simulated wagering flow."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from edgebook.cfb.models import Game, GameStatus, MarketSelection
from edgebook.ledger.models import Account, Transaction, TransactionType
from edgebook.wagering import services as wagering_services
from edgebook.wagering.models import Bet, BetStatus
from edgebook.wagering.services import WagerConflictError, place_bet, record_game_result


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
