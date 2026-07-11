"""Migration lifecycle coverage for the initial Edgebook schema."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def _assert_phase_one_to_three_schema(engine) -> None:
    """Assert the tables and columns introduced through the stabilization scope."""
    inspector = inspect(engine)
    assert {
        "ledger_accounts",
        "ledger_transactions",
        "cfb_games",
        "cfb_markets",
        "cfb_market_quotes",
        "cfb_score_corrections",
        "cfb_score_observations",
        "cfb_score_resolutions",
        "ingestion_runs",
        "ingestion_provider_observations",
        "wagering_bets",
        "wagering_bet_reviews",
    }.issubset(inspector.get_table_names())
    assert {column["name"] for column in inspector.get_columns("cfb_games")} >= {
        "sport",
        "home_score",
        "away_score",
        "score_sync_state",
    }
    assert {column["name"] for column in inspector.get_columns("wagering_bets")} >= {
        "rationale_category",
        "notes",
        "bankroll_before_cents",
        "quote_source",
    }


def test_initial_migration_upgrades_downgrades_and_reupgrades(tmp_path: Path):
    """The initial schema is reversible on the SQLite development database."""
    database_path = tmp_path / "migration-test.db"
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        _assert_phase_one_to_three_schema(engine)
    finally:
        engine.dispose()

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        _assert_phase_one_to_three_schema(engine)
    finally:
        engine.dispose()
