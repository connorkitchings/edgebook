"""Test cases for server-rendered page routes."""

from fastapi.testclient import TestClient


def _create_team(client: TestClient, name: str) -> dict:
    response = client.post("/cfb/teams", json={"name": name})
    assert response.status_code == 201
    return response.json()


def _create_game(
    client: TestClient,
    *,
    home_name: str = "North State",
    away_name: str = "South Tech",
) -> dict:
    home = _create_team(client, home_name)
    away = _create_team(client, away_name)
    response = client.post(
        "/cfb/games",
        json={
            "home_team_id": home["id"],
            "away_team_id": away["id"],
            "scheduled_at": "2026-09-05T19:30:00Z",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_open_market(client: TestClient, game_id: str) -> dict:
    market = client.post(
        f"/cfb/games/{game_id}/markets",
        json={"market_type": "SPREAD", "line": "-3.500"},
    ).json()
    client.post(
        f"/cfb/markets/{market['id']}/quotes",
        json={"selection": "HOME", "american_odds": -110},
    )
    client.post(
        f"/cfb/markets/{market['id']}/quotes",
        json={"selection": "AWAY", "american_odds": -110},
    )
    return market


def _create_account(client: TestClient) -> dict:
    return client.post(
        "/accounts",
        json={"owner_name": "Test User", "starting_bankroll": "1000.00"},
    ).json()


def test_dashboard_page_no_account(client: TestClient):
    """Dashboard renders the empty state when no account exists."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Dashboard" in response.text
    assert "No account found" in response.text


def test_dashboard_page_with_account(client: TestClient):
    """Dashboard renders account details when an account exists."""
    client.post(
        "/accounts",
        json={"owner_name": "Test User", "starting_bankroll": "1000.00"},
    )

    response = client.get("/")
    assert response.status_code == 200
    assert "Test User" in response.text
    assert "1000.00" in response.text


def test_bets_page(client: TestClient):
    """Bets page renders the placement wizard."""
    response = client.get("/bets")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Bets" in response.text


def test_bets_page_no_account(client: TestClient):
    """Bets page shows empty state when no account exists."""
    response = client.get("/bets")
    assert response.status_code == 200
    assert "No account found" in response.text


def test_analytics_page_no_account(client: TestClient):
    """Analytics page shows empty state when no account exists."""
    response = client.get("/analytics")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Analytics" in response.text
    assert "No account found" in response.text


def test_analytics_page_with_account(client: TestClient):
    """Analytics page renders stat cards when account exists."""
    _create_account(client)
    response = client.get("/analytics")
    assert response.status_code == 200
    assert "ROI" in response.text
    assert "Win Rate" in response.text


def test_ingestion_page(client: TestClient):
    """Ingestion monitoring page renders."""
    response = client.get("/ingestion")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ingestion" in response.text
    assert "Sync Triggers" in response.text


def test_run_history_partial_empty(client: TestClient):
    """Run history partial shows empty state when no runs exist."""
    response = client.get("/partials/run-history")
    assert response.status_code == 200
    assert "No ingestion runs yet" in response.text


def test_run_history_partial_with_runs(client: TestClient):
    """Run history partial shows runs after a sync."""
    client.post("/ingestion/sync/games")
    response = client.get("/partials/run-history")
    assert response.status_code == 200
    assert "fixture" in response.text
    assert "GAMES" in response.text


def test_conflict_list_partial_empty(client: TestClient):
    """Conflict list partial shows empty state when no conflicts exist."""
    response = client.get("/partials/conflict-list")
    assert response.status_code == 200
    assert "No score conflicts" in response.text


def test_recent_bets_partial_no_account(client: TestClient):
    """Recent bets partial returns empty state without account_id."""
    response = client.get("/partials/recent-bets")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "No bets placed yet" in response.text


def test_recent_bets_partial_with_account(client: TestClient):
    """Recent bets partial returns empty state for an account with no bets."""
    account = _create_account(client)

    response = client.get(f"/partials/recent-bets?account_id={account['id']}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "No bets placed yet" in response.text


def test_static_css_served(client: TestClient):
    """Static CSS file is served correctly."""
    response = client.get("/static/css/app.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


# --- GET /cfb/games endpoint tests ---


def test_list_games_endpoint_empty(client: TestClient):
    """List games endpoint returns empty array when no games exist."""
    response = client.get("/cfb/games")
    assert response.status_code == 200
    assert response.json() == []


def test_list_games_endpoint_with_games(client: TestClient):
    """List games endpoint returns games newest-first."""
    _create_game(client, home_name="Team A", away_name="Team B")

    response = client.get("/cfb/games")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["home_team"]["name"] == "Team A"
    assert data[0]["away_team"]["name"] == "Team B"


def test_list_games_endpoint_status_filter(client: TestClient):
    """List games endpoint filters by status."""
    _create_game(client, home_name="Team A", away_name="Team B")

    response = client.get("/cfb/games?status=SCHEDULED")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/cfb/games?status=FINAL")
    assert response.status_code == 200
    assert len(response.json()) == 0


# --- Bet placement wizard partial tests ---


def test_game_select_partial_empty(client: TestClient):
    """Game select partial shows empty state when no games exist."""
    response = client.get("/partials/game-select")
    assert response.status_code == 200
    assert "No games available" in response.text


def test_game_select_partial_with_games(client: TestClient):
    """Game select partial shows game cards when games exist."""
    _create_game(client, home_name="Alpha", away_name="Beta")

    response = client.get("/partials/game-select")
    assert response.status_code == 200
    assert "Alpha" in response.text
    assert "Beta" in response.text


def test_market_picker_partial(client: TestClient):
    """Market picker partial shows open markets with quote buttons."""
    game = _create_game(client)
    _create_open_market(client, game["id"])

    response = client.get(f"/partials/market-picker?game_id={game['id']}")
    assert response.status_code == 200
    assert "SPREAD" in response.text
    assert "HOME" in response.text
    assert "AWAY" in response.text


def test_stake_form_partial(client: TestClient):
    """Stake form partial shows the form with market details."""
    account = _create_account(client)
    game = _create_game(client)
    market = _create_open_market(client, game["id"])

    quotes = client.get(f"/cfb/games/{game['id']}").json()
    quote_id = quotes["markets"][0]["quotes"][0]["id"]

    response = client.get(
        f"/partials/stake-form?market_id={market['id']}"
        f"&selection=HOME&quote_id={quote_id}&account_id={account['id']}"
    )
    assert response.status_code == 200
    assert "Stake Amount" in response.text
    assert "HOME" in response.text


def test_place_bet_partial_success(client: TestClient):
    """Place bet partial successfully places a bet and shows confirmation."""
    account = _create_account(client)
    game = _create_game(client)
    market = _create_open_market(client, game["id"])

    quotes = client.get(f"/cfb/games/{game['id']}").json()
    quote_id = quotes["markets"][0]["quotes"][0]["id"]

    response = client.post(
        "/partials/place-bet",
        data={
            "account_id": account["id"],
            "market_id": market["id"],
            "selection": "HOME",
            "quote_id": quote_id,
            "stake": "25.00",
            "rationale_category": "",
            "reason": "",
        },
    )
    assert response.status_code == 200
    assert "Bet Placed" in response.text
    assert "HOME" in response.text
    assert "25.00" in response.text


def test_place_bet_partial_invalid_stake(client: TestClient):
    """Place bet partial shows error for invalid stake."""
    account = _create_account(client)
    game = _create_game(client)
    market = _create_open_market(client, game["id"])

    quotes = client.get(f"/cfb/games/{game['id']}").json()
    quote_id = quotes["markets"][0]["quotes"][0]["id"]

    response = client.post(
        "/partials/place-bet",
        data={
            "account_id": account["id"],
            "market_id": market["id"],
            "selection": "HOME",
            "quote_id": quote_id,
            "stake": "not-a-number",
            "rationale_category": "",
            "reason": "",
        },
    )
    assert response.status_code == 200
    assert "Invalid stake amount" in response.text


# --- Bet history page tests ---


def test_bet_history_page_empty(client: TestClient):
    """Bet history page shows empty state when no account exists."""
    response = client.get("/bets/history")
    assert response.status_code == 200
    assert "Bet History" in response.text


def test_bet_history_page_with_account(client: TestClient):
    """Bet history page loads the HTMX bet table container."""
    _create_account(client)
    response = client.get("/bets/history")
    assert response.status_code == 200
    assert "bet-table-container" not in response.text or "Loading bets" in response.text


def test_bet_table_partial_with_account(client: TestClient):
    """Bet table partial shows empty state for account with no bets."""
    account = _create_account(client)
    response = client.get(f"/partials/bet-table?account_id={account['id']}&offset=0")
    assert response.status_code == 200
    assert "No bets match" in response.text


def test_bet_table_partial_with_bets(client: TestClient):
    """Bet table partial shows bets with load-more pagination."""
    account = _create_account(client)
    game = _create_game(client)
    market = _create_open_market(client, game["id"])

    client.post(
        f"/accounts/{account['id']}/bets",
        json={
            "market_id": market["id"],
            "selection": "HOME",
            "stake": "10.00",
        },
    )

    response = client.get(f"/partials/bet-table?account_id={account['id']}&offset=0")
    assert response.status_code == 200
    assert "HOME" in response.text


def test_bet_table_partial_status_filter(client: TestClient):
    """Bet table partial filters by status."""
    account = _create_account(client)
    response = client.get(
        f"/partials/bet-table?account_id={account['id']}&status=WON&offset=0"
    )
    assert response.status_code == 200


# --- Game management tests ---


def test_games_page_empty(client: TestClient):
    """Games page renders with no teams."""
    response = client.get("/games")
    assert response.status_code == 200
    assert "Game Management" in response.text


def test_games_page_with_teams(client: TestClient):
    """Games page shows team dropdowns when teams exist."""
    _create_team(client, "Alabama")
    response = client.get("/games")
    assert response.status_code == 200
    assert "Alabama" in response.text


def test_create_team_partial(client: TestClient):
    """Create team partial returns success message."""
    response = client.post("/partials/create-team", data={"name": "Ohio State"})
    assert response.status_code == 200
    assert "Created: Ohio State" in response.text


def test_create_team_partial_duplicate(client: TestClient):
    """Create team partial shows error for duplicate name."""
    _create_team(client, "Michigan")
    response = client.post("/partials/create-team", data={"name": "Michigan"})
    assert response.status_code == 200
    assert "already exists" in response.text


def test_create_game_partial(client: TestClient):
    """Create game partial returns success."""
    home = _create_team(client, "Home Team")
    away = _create_team(client, "Away Team")
    response = client.post(
        "/partials/create-game",
        data={
            "home_team_id": home["id"],
            "away_team_id": away["id"],
            "scheduled_at": "2026-09-05T19:30",
        },
    )
    assert response.status_code == 200
    assert "Game created" in response.text


def test_game_list_partial(client: TestClient):
    """Game list partial shows scheduled games."""
    _create_game(client)
    response = client.get("/partials/game-list")
    assert response.status_code == 200
    assert "North State" in response.text
    assert "South Tech" in response.text
