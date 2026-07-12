"""Regression coverage for the generated FastAPI OpenAPI contract."""

import json
from pathlib import Path

from edgebook.main import app


def test_checked_in_openapi_matches_fastapi_schema():
    """The checked-in contract remains a faithful rendering of the running API."""
    contract_path = (
        Path(__file__).resolve().parents[1] / "docs" / "api" / "openapi.json"
    )
    assert json.loads(contract_path.read_text()) == app.openapi()


def test_openapi_contract_includes_all_ingestion_routes():
    """The ingestion surface stays documented as part of the public API contract."""
    paths = app.openapi()["paths"]
    assert {
        "/ingestion/sync/games",
        "/ingestion/sync/quotes",
        "/ingestion/sync/scores",
        "/ingestion/settle",
        "/ingestion/runs",
        "/ingestion/conflicts",
        "/ingestion/conflicts/{game_id}/resolve",
    }.issubset(paths)
