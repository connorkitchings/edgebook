# API Documentation

This directory contains the OpenAPI specification and related documentation for the project's APIs.

## OpenAPI Specification

The `openapi.yaml` file defines the RESTful API for this project. You can use tools like [Swagger UI](https://swagger.io/tools/swagger-ui/) or [Redoc](https://github.com/Redocly/redoc) to generate interactive documentation from this file.

## Simulation-Only Policy

All balances and odds in this API are fictional simulation data. Edgebook has no
real-money payment, wagering, or sportsbook integration.

## Endpoints

### Health

- **GET /health:** Verifies that the API and configured database are reachable.

### Generic Ledger Accounts

- **POST /accounts:** Create a fictional account with `owner_name` and optional
  two-decimal `starting_bankroll` simulation credits.
- **GET /accounts/{account_id}:** Retrieve account status, opening bankroll, and
  current balance.
- **POST /accounts/{account_id}/transactions:** Record a `DEPOSIT` or
  `WITHDRAWAL` in positive two-decimal simulation credits.
- **GET /accounts/{account_id}/transactions:** Read a newest-first statement;
  supports `limit` (1–100) and `offset` pagination.

Ledger statements are append-only, and every balance change is represented by
balanced signed postings to the fictional account and the internal simulation-capital
counterparty. `WAGER_STAKE`, `WAGER_PAYOUT`, and `ADJUSTMENT` are reserved for
later phases and cannot be submitted to the manual transaction API.

### Manual College Football Intake

- **POST /cfb/teams:** Add a reusable team catalog entry.
- **POST /cfb/games:** Create a scheduled game between distinct team IDs.
- **GET /cfb/games/{game_id}:** Retrieve the game, markets, and quotes.
- **POST /cfb/games/{game_id}/markets:** Create a draft `SPREAD`, `MONEYLINE`,
  or `TOTAL` market.
- **POST /cfb/markets/{market_id}/quotes:** Add a selection and signed American
  odds quote. A market opens after it has its required pair of quotes.

CFB intake is separate from the ledger: creating teams, games, markets, and odds
does not change any balance.

## Error Handling

- `404` — The requested account, team dependency, game, or market does not exist.
- `409` — The operation conflicts with current state, such as an overdraft,
  duplicate team, duplicate market, or duplicate quote.
- `422` — The request data is invalid, such as a non-cent amount, invalid odds,
  inappropriate market line, or malformed identifier payload.
