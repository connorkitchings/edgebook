"""Migration lifecycle coverage for the initial Edgebook schema."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_initial_migration_upgrades_downgrades_and_reupgrades(tmp_path: Path):
    """The initial schema is reversible on the SQLite development database."""
    database_path = tmp_path / "migration-test.db"
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        assert {
            "ledger_accounts",
            "ledger_transactions",
            "cfb_games",
            "cfb_market_quotes",
        }.issubset(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    command.downgrade(config, "base")
    command.upgrade(config, "head")
