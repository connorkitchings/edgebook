"""Manual college-football intake operations, services package."""

from edgebook.cfb.services.catalog import (
    CfbConflictError,
    CfbError,
    CfbNotFoundError,
    CfbValidationError,
    create_game,
    create_team,
    get_game,
    list_games,
    normalize_team_name,
)
from edgebook.cfb.services.markets import (
    EXPECTED_SELECTIONS,
    create_market,
    create_quote,
    quote_comparison,
)

__all__ = [
    "CfbConflictError",
    "CfbError",
    "CfbNotFoundError",
    "CfbValidationError",
    "create_game",
    "create_team",
    "get_game",
    "list_games",
    "normalize_team_name",
    "EXPECTED_SELECTIONS",
    "create_market",
    "create_quote",
    "quote_comparison",
]
