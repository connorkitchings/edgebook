"""API coverage for ingestion sync, settlement, and conflict resolution."""

from fastapi.testclient import TestClient


def test_sync_games(client: TestClient):
    """Sync games endpoint ingests from fixture feed."""
    response = client.post("/ingestion/sync/games")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["created"] >= 1


def test_sync_games_idempotent(client: TestClient):
    """Second sync of the same fixture feed skips all records."""
    client.post("/ingestion/sync/games")
    response = client.post("/ingestion/sync/games")
    assert response.status_code == 200
    assert response.json()["skipped"] >= 1
    assert response.json()["created"] == 0


def test_sync_quotes(client: TestClient):
    """Sync quotes endpoint ingests odds from fixture feed."""
    client.post("/ingestion/sync/games")
    response = client.post("/ingestion/sync/quotes")
    assert response.status_code == 200
    assert response.json()["created"] >= 1


def test_sync_scores(client: TestClient):
    """Sync scores endpoint ingests scores from fixture feed."""
    client.post("/ingestion/sync/games")
    response = client.post("/ingestion/sync/scores")
    assert response.status_code == 200
    assert response.json()["created"] >= 1


def test_settle_no_confirmed(client: TestClient):
    """Settle endpoint returns zero when no confirmed games exist."""
    response = client.post("/ingestion/settle")
    assert response.status_code == 200
    assert response.json()["settled_count"] == 0


def test_list_runs_empty(client: TestClient):
    """List runs returns empty when no syncs have occurred."""
    response = client.get("/ingestion/runs")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_provider_statuses_hide_credentials(client: TestClient):
    """Provider discovery reports capabilities but never credential values."""
    response = client.get("/ingestion/providers")
    assert response.status_code == 200
    data = response.json()
    assert {item["name"] for item in data} == {
        "the-odds-api",
        "sportsdataio",
        "college-football-data",
    }
    assert all("key" not in item for item in data)


def test_list_runs_after_sync(client: TestClient):
    """List runs shows sync history after a sync."""
    client.post("/ingestion/sync/games")
    response = client.get("/ingestion/runs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["provider"] == "fixture"
    assert data["items"][0]["scope"] == "GAMES"


def test_list_runs_status_filter(client: TestClient):
    """The status query param narrows run history."""
    client.post("/ingestion/sync/games")

    completed = client.get("/ingestion/runs?status=COMPLETED")
    assert completed.status_code == 200
    assert completed.json()["total"] >= 1
    assert all(item["status"] == "COMPLETED" for item in completed.json()["items"])

    failed = client.get("/ingestion/runs?status=FAILED")
    assert failed.status_code == 200
    assert failed.json()["total"] == 0


def test_runs_summary_empty(client: TestClient):
    """Summary reports zero totals before any run exists."""
    response = client.get("/ingestion/runs/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_runs"] == 0
    assert data["status_counts"] == {}
    assert data["last_run_at"] is None


def test_runs_summary_after_sync(client: TestClient):
    """Summary reflects a completed run after a sync."""
    client.post("/ingestion/sync/games")
    response = client.get("/ingestion/runs/summary?window_hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["window_hours"] == 24
    assert data["total_runs"] >= 1
    assert data["status_counts"]["COMPLETED"] >= 1
    assert data["last_run_at"] is not None


def test_list_conflicts_empty(client: TestClient):
    """List conflicts returns empty when none exist."""
    response = client.get("/ingestion/conflicts")
    assert response.status_code == 200
    assert response.json() == []


def test_resolve_conflict_not_found(client: TestClient):
    """Resolve conflict returns 404 for unknown game."""
    response = client.post(
        "/ingestion/conflicts/nonexistent/resolve",
        json={
            "home_score": 21,
            "away_score": 17,
            "reason": "test",
            "resolved_by": "operator",
        },
    )
    assert response.status_code == 404
