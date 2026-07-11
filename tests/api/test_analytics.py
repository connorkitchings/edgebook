"""End-to-end API coverage for the analytics endpoint."""

import uuid

from tests.api.test_wagering import create_account


def _create_open_market(
    client,
    *,
    market_type: str = "SPREAD",
    line: str | None = "-3.500",
    odds: tuple[int, int] = (-110, -110),
) -> tuple[dict, dict]:
    """Create a game with an open market using unique team names."""
    suffix = uuid.uuid4().hex[:8]
    home = client.post("/cfb/teams", json={"name": f"Home {suffix}"}).json()
    away = client.post("/cfb/teams", json={"name": f"Away {suffix}"}).json()
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


def _setup_account_with_settled_bets(client):
    """Create an account with a mix of settled bets across market types."""
    account = create_account(client, "200.00")

    game1, market1 = _create_open_market(
        client, market_type="SPREAD", line="-3.500", odds=(-110, -110)
    )
    client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market1["id"],
            "selection": "HOME",
            "stake": "20.00",
            "rationale_category": "MATCHUP_ANALYSIS",
            "notes": "Strong defensive edge",
        },
    )
    client.put(
        f"/cfb/games/{game1['id']}/result",
        json={"home_score": 24, "away_score": 17},
    )

    game2, market2 = _create_open_market(
        client, market_type="MONEYLINE", line=None, odds=(150, -170)
    )
    client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market2["id"],
            "selection": "AWAY",
            "stake": "10.00",
            "rationale_category": "LINE_VALUE",
            "notes": "Underdog value",
        },
    )
    client.put(
        f"/cfb/games/{game2['id']}/result",
        json={"home_score": 14, "away_score": 28},
    )

    game3, market3 = _create_open_market(
        client, market_type="TOTAL", line="45.500", odds=(-110, -110)
    )
    client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market3["id"],
            "selection": "UNDER",
            "stake": "5.00",
        },
    )
    client.put(
        f"/cfb/games/{game3['id']}/result",
        json={"home_score": 10, "away_score": 7},
    )

    return account


def test_analytics_summary_with_settled_bets(client):
    """Analytics returns correct summary metrics for an account with bets."""
    account = _setup_account_with_settled_bets(client)
    response = client.get(f"/accounts/{account['id']}/analytics")
    assert response.status_code == 200
    body = response.json()

    assert body["account_id"] == account["id"]
    summary = body["summary"]
    assert summary["total_bets"] == 3
    assert summary["wins"] == 3
    assert summary["losses"] == 0
    assert summary["pushes"] == 0
    assert summary["win_rate"] == 1.0
    assert summary["total_staked"] == "35.00"
    assert float(summary["total_payout"]) > 35.0
    assert float(summary["net_profit"]) > 0
    assert summary["roi"] > 0
    assert summary["sharpe_ratio"] is not None
    assert float(summary["max_drawdown"]) <= 0


def test_analytics_by_sport(client):
    """Analytics groups performance by sport."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    assert len(body["by_sport"]) == 1
    assert body["by_sport"][0]["sport"] == "CFB"
    assert body["by_sport"][0]["bets"] == 3


def test_analytics_by_market_type(client):
    """Analytics groups performance by market type."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    market_types = {row["market_type"] for row in body["by_market_type"]}
    assert market_types == {"SPREAD", "MONEYLINE", "TOTAL"}


def test_analytics_by_rationale_category(client):
    """Analytics groups performance by rationale category."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    categories = {row["category"] for row in body["by_rationale_category"]}
    assert "MATCHUP_ANALYSIS" in categories
    assert "LINE_VALUE" in categories
    assert None in categories


def test_analytics_allocation_calibration(client):
    """Analytics buckets bets by conviction percentage."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    calibration = body["allocation_calibration"]
    assert len(calibration) == 6
    total_bets = sum(b["bets"] for b in calibration)
    assert total_bets == 3


def test_analytics_allocation_calibration_custom_buckets(client):
    """Custom bucket boundaries are respected."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics?buckets=5,15").json()
    calibration = body["allocation_calibration"]
    assert len(calibration) == 3
    assert calibration[0]["bucket"] == "<5%"
    assert calibration[1]["bucket"] == "5-15%"
    assert calibration[2]["bucket"] == "15%+"


def test_analytics_drawdown_series(client):
    """Drawdown series contains per-transaction points."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    series = body["drawdown_series"]
    assert len(series) >= 3
    for point in series:
        assert "timestamp" in point
        assert "balance" in point
        assert "peak" in point
        assert "drawdown_pct" in point
        assert "event" in point


def test_analytics_balance_series(client):
    """Balance series contains daily points."""
    account = _setup_account_with_settled_bets(client)
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    series = body["balance_series"]
    assert len(series) >= 1
    for point in series:
        assert "date" in point
        assert "balance" in point


def test_analytics_no_settled_bets(client):
    """Account with no settled bets returns zeroes, not errors."""
    account = create_account(client, "100.00")
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    summary = body["summary"]
    assert summary["total_bets"] == 0
    assert summary["wins"] == 0
    assert summary["losses"] == 0
    assert summary["roi"] == 0.0
    assert summary["sharpe_ratio"] is None
    assert summary["max_drawdown"] == "0.00"
    assert body["by_sport"] == []
    assert body["by_market_type"] == []
    assert body["by_rationale_category"] == []


def test_analytics_missing_account_returns_404(client):
    """A non-existent account returns 404."""
    response = client.get("/accounts/missing/analytics")
    assert response.status_code == 404


def test_analytics_with_losses(client):
    """Analytics correctly counts losses and negative ROI."""
    account = create_account(client, "100.00")
    game, market = _create_open_market(
        client, market_type="MONEYLINE", line=None, odds=(-110, -110)
    )
    client.post(
        f"/accounts/{account['id']}/bets",
        json={"market_id": market["id"], "selection": "HOME", "stake": "10.00"},
    )
    client.put(
        f"/cfb/games/{game['id']}/result",
        json={"home_score": 10, "away_score": 21},
    )
    body = client.get(f"/accounts/{account['id']}/analytics").json()
    summary = body["summary"]
    assert summary["total_bets"] == 1
    assert summary["wins"] == 0
    assert summary["losses"] == 1
    assert summary["win_rate"] == 0.0
    assert summary["net_profit"] == "-10.00"
    assert summary["roi"] == -1.0
    assert summary["sharpe_ratio"] is None
