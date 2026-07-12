"""API coverage for manual college-football team, game, and odds intake."""

from sqlalchemy import func, select

from edgebook.ledger.models import Transaction


def create_team(client, name: str) -> dict:
    """Create a team and return its response payload."""
    response = client.post("/cfb/teams", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_game(
    client, *, home_name: str = "North State", away_name: str = "South Tech"
) -> dict:
    """Create a reusable scheduled game for market tests."""
    home_team = create_team(client, home_name)
    away_team = create_team(client, away_name)
    response = client.post(
        "/cfb/games",
        json={
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "scheduled_at": "2026-09-05T19:30:00Z",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_manual_game_market_and_quote_flow_stays_outside_ledger(client, db_session):
    """Entered CFB data opens a market but creates no ledger postings."""
    initial_txs = db_session.scalar(select(func.count()).select_from(Transaction))
    game = create_game(client, home_name="East College", away_name="West College")
    market_response = client.post(
        f"/cfb/games/{game['id']}/markets",
        json={"market_type": "SPREAD", "line": "-3.500"},
    )
    assert market_response.status_code == 201
    market = market_response.json()
    assert market["status"] == "DRAFT"
    assert market["line"] == "-3.500"

    invalid_selection = client.post(
        f"/cfb/markets/{market['id']}/quotes",
        json={"selection": "OVER", "american_odds": -110},
    )
    assert invalid_selection.status_code == 422

    assert (
        client.post(
            f"/cfb/markets/{market['id']}/quotes",
            json={"selection": "HOME", "american_odds": -110},
        ).status_code
        == 201
    )
    draft_game = client.get(f"/cfb/games/{game['id']}")
    assert draft_game.json()["markets"][0]["status"] == "DRAFT"

    assert (
        client.post(
            f"/cfb/markets/{market['id']}/quotes",
            json={"selection": "AWAY", "american_odds": -110},
        ).status_code
        == 201
    )
    open_game = client.get(f"/cfb/games/{game['id']}")
    assert open_game.status_code == 200
    assert open_game.json()["markets"][0]["status"] == "OPEN"
    assert len(open_game.json()["markets"][0]["quotes"]) == 2
    current_txs = db_session.scalar(select(func.count()).select_from(Transaction))
    assert current_txs == initial_txs


def test_cfb_intake_validation_and_conflicts(client):
    """Manual intake validates duplicate resources and invalid market data."""
    create_team(client, "  North   State ")
    assert client.post("/cfb/teams", json={"name": "north state"}).status_code == 409
    assert (
        client.post(
            "/cfb/games",
            json={
                "home_team_id": "missing",
                "away_team_id": "also-missing",
                "scheduled_at": "2026-09-05T19:30:00Z",
            },
        ).status_code
        == 404
    )

    game = create_game(client, home_name="East College", away_name="West College")
    assert (
        client.post(
            f"/cfb/games/{game['id']}/markets",
            json={"market_type": "MONEYLINE", "line": "1.000"},
        ).status_code
        == 422
    )
    market = client.post(
        f"/cfb/games/{game['id']}/markets",
        json={"market_type": "TOTAL", "line": "48.500"},
    )
    assert market.status_code == 201
    market_id = market.json()["id"]
    assert (
        client.post(
            f"/cfb/markets/{market_id}/quotes",
            json={"selection": "OVER", "american_odds": 99},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/cfb/markets/{market_id}/quotes",
            json={"selection": "OVER", "american_odds": -110},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/cfb/markets/{market_id}/quotes",
            json={"selection": "OVER", "american_odds": -110},
        ).status_code
        == 409
    )
    alt_line = client.post(
        f"/cfb/games/{game['id']}/markets",
        json={"market_type": "TOTAL", "line": "49.000"},
    )
    assert alt_line.status_code == 201
    assert (
        client.post(
            f"/cfb/games/{game['id']}/markets",
            json={"market_type": "TOTAL", "line": "49.000"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/cfb/games/{game['id']}/markets",
            json={"market_type": "MONEYLINE", "line": None},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/cfb/games/{game['id']}/markets",
            json={"market_type": "MONEYLINE", "line": None},
        ).status_code
        == 409
    )


def test_alternative_lines_allow_multiple_markets_and_bets(client):
    """Multiple spread markets with different lines coexist and accept bets."""
    from tests.api.test_wagering import create_account

    account = create_account(client)
    game = create_game(client, home_name="Alt Home", away_name="Alt Away")

    main_spread = client.post(
        f"/cfb/games/{game['id']}/markets",
        json={"market_type": "SPREAD", "line": "-3.500"},
    ).json()
    alt_spread = client.post(
        f"/cfb/games/{game['id']}/markets",
        json={"market_type": "SPREAD", "line": "-7.000"},
    ).json()
    assert main_spread["id"] != alt_spread["id"]

    for market in (main_spread, alt_spread):
        for selection, odds in (("HOME", -110), ("AWAY", -110)):
            assert (
                client.post(
                    f"/cfb/markets/{market['id']}/quotes",
                    json={"selection": selection, "american_odds": odds},
                ).status_code
                == 201
            )

    bet1 = client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": main_spread["id"],
            "selection": "HOME",
            "stake": "10.00",
        },
    )
    assert bet1.status_code == 201
    assert bet1.json()["bet"]["line"] == "-3.500"

    bet2 = client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": alt_spread["id"],
            "selection": "HOME",
            "stake": "10.00",
        },
    )
    assert bet2.status_code == 201
    assert bet2.json()["bet"]["line"] == "-7.000"
