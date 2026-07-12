# API Documentation

This directory contains the generated OpenAPI contract and related documentation for the project's APIs.

## OpenAPI Specification

`openapi.json` is generated from FastAPI's `app.openapi()` schema and is the authoritative
checked-in API contract. Regenerate it with `uv run python scripts/generate_openapi.py`; use
`--check` in automation to detect drift. The live interactive API documentation is available at
`/docs` when the application is running.

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

- **GET /ingestion/providers:** Returns configured provider capabilities without exposing API
  keys or other credentials.
- **POST /ingestion/sync/games**, **/quotes**, and **/scores:** Trigger the local fixture-feed
  synchronization stages independently.
- **POST /ingestion/settle:** Settle games whose provider score observations are confirmed.
- **GET /ingestion/runs:** Read paginated, newest-first ingestion-run history.
- **GET /ingestion/conflicts:** List held score disagreements.
- **POST /ingestion/conflicts/{game_id}/resolve:** Record a local operator score decision and
  make the game eligible for settlement.
- **GET /cfb/games/{game_id}/quote-comparison:** Returns best and worst provider quote IDs for each market selection without creating a canonical line. Place bets with a specific `quote_id` whenever multiple source quotes exist.
- **GET /cfb/games/{game_id}/odds-history:** Returns chronological immutable odds observations for one game. Filter by `source`, `market_type`, `selection`, `start`, `end`, `limit`, and `offset`; each item retains its bookmaker source and provider event ID.
- **PUT /cfb/games/{game_id}/resolve-score-conflict:** Locally resolves a held provider-score conflict, records an audit decision, and settles the game atomically.
- **GET /accounts/{account_id}/bets/{bet_id}/review:** Returns the asynchronous human-review task for a bet.
- **PUT /accounts/{account_id}/bets/{bet_id}/review:** Completes a local human review with summary and cognitive-bias flags.
- **GET /reviews:** Lists local-operator review tasks with wager and source-quote context; supports `status`, `account_id`, `limit`, and `offset`.
- **POST /reviews/{bet_id}/claim:** Atomically claims a pending review for a named local operator.

The scheduler-neutral command surface is `python -m edgebook.ingestion.cli`: use `sync` with a
normalized feed or `--provider the-odds-api`, `backfill-odds` for resumable daily historical snapshots,
`providers`, `settle-confirmed`, `claim-reviews`, and `report`. Production scheduling must invoke
these idempotent commands outside the API process.

## Error Handling

- `404` — The requested account, team dependency, game, or market does not exist.
- `409` — The operation conflicts with current state, such as an overdraft,
  duplicate team, duplicate market, or duplicate quote.
- `422` — The request data is invalid, such as a non-cent amount, invalid odds,
  inappropriate market line, or malformed identifier payload.
