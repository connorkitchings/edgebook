"""Generate or verify Edgebook's checked-in FastAPI OpenAPI contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from edgebook.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "docs" / "api" / "openapi.json"


def render_openapi() -> str:
    """Return a deterministic representation of the application's API contract."""
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the checked-in contract differs from FastAPI's schema",
    )
    args = parser.parse_args()
    rendered = render_openapi()

    if args.check:
        if not CONTRACT_PATH.exists() or CONTRACT_PATH.read_text() != rendered:
            print(
                "OpenAPI contract is out of date. "
                "Run: uv run python scripts/generate_openapi.py",
                file=sys.stderr,
            )
            raise SystemExit(1)
        return

    CONTRACT_PATH.write_text(rendered)


if __name__ == "__main__":
    main()
