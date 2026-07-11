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
- **POST /accounts/{account_id}/reconcile:** Verify that the stored balance equals the
  sum of its append-only postings.

Ledger statements are append-only, and every balance change is represented by
balanced signed postings to the fictional account and the internal simulation-capital
counterparty. `WAGER_STAKE` and `WAGER_PAYOUT` are created only by the wagering lifecycle;
they cannot be submitted to the manual transaction API.

### Manual College Football Intake

- **POST /cfb/teams:** Add a reusable team catalog entry.
- **POST /cfb/games:** Create a scheduled game between distinct team IDs.
- **GET /cfb/games/{game_id}:** Retrieve the game, markets, and quotes.
- **POST /cfb/games/{game_id}/markets:** Create a draft `SPREAD`, `MONEYLINE`,
  or `TOTAL` market.
- **POST /cfb/markets/{market_id}/quotes:** Add a selection and signed American
  odds quote. A market opens after it has its required pair of quotes.
- **PUT /cfb/games/{game_id}/result:** Finalize a score and atomically settle pending bets.

CFB intake is separate from the ledger: creating teams, games, markets, and odds
does not change any balance.

### Simulated Wagers

- **POST /accounts/{account_id}/bets:** Place a straight simulated bet against an open
  quote. Optional `Idempotency-Key` retries return the original bet without another debit.
- **GET /accounts/{account_id}/bets:** Read newest-first paginated bet history.
- **GET /accounts/{account_id}/bets/{bet_id}:** Read one owned bet and its settlement.

Placement locks the odds and line, snapshots the pre-bet bankroll, debits the stake, and
closes automatically 30 minutes before kickoff. Rationale is optional; conviction is later
derived from stake divided by the placement bankroll rather than a subjective score.

### Analytics and Score Corrections

- **GET /accounts/{account_id}/analytics:** Returns lifetime or date-range performance
  metrics, breakdowns, allocation calibration, and ledger-replayed balance/drawdown series.
  `from` and `to` must include timezone offsets, `from` cannot be after `to`, and `buckets`
  must be positive, strictly increasing comma-separated percentage boundaries.
- **PUT /cfb/games/{game_id}/correction:** Records an audit trail, offsets prior payouts, and
  re-settles a finalized game. It is intentionally unauthenticated only for the current local,
  simulation-only workflow; authorization is required before external exposure.

### Multi-Source Ingestion and Reviews

- **GET /cfb/games/{game_id}/quote-comparison:** Returns best and worst provider quote IDs for each market selection without creating a canonical line. Place bets with a specific `quote_id` whenever multiple source quotes exist.
- **PUT /cfb/games/{game_id}/resolve-score-conflict:** Locally resolves a held provider-score conflict, records an audit decision, and settles the game atomically.
- **GET /accounts/{account_id}/bets/{bet_id}/review:** Returns the asynchronous human-review task for a bet.
- **PUT /accounts/{account_id}/bets/{bet_id}/review:** Completes a local human review with summary and cognitive-bias flags.

The scheduler-neutral command surface is `python -m edgebook.ingestion.cli`: use `sync` with a normalized provider feed, `settle-confirmed`, `claim-reviews`, and `report`. Production scheduling must invoke these idempotent commands outside the API process.

## Error Handling

- `404` — The requested account, team dependency, game, or market does not exist.
- `409` — The operation conflicts with current state, such as an overdraft,
  duplicate team, duplicate market, or duplicate quote.
- `422` — The request data is invalid, such as a non-cent amount, invalid odds,
  inappropriate market line, or malformed identifier payload.
