# Data Dictionary

Definitions for key data elements used across Edgebook. All monetary values are fictional
simulation credits.

## Terms

### Account Kind

**Definition:** Classifies a ledger account without coupling it to a product domain.

**Data Type:** enum (string)

**Allowed values:** `USER_ASSET`, `EQUITY`

**Source:** `src/edgebook/ledger/models.py` (`AccountKind`)

**Usage:** `USER_ASSET` is the user's fictional bankroll account; `EQUITY` is the internal
simulation-capital counterparty used to balance every posting.

---

### Transaction Type

**Definition:** The economic event category recorded by a ledger posting.

**Data Type:** enum (string)

**Allowed values:** `DEPOSIT`, `WITHDRAWAL`, `WAGER_STAKE`, `WAGER_PAYOUT`, `ADJUSTMENT`

**Source:** `src/edgebook/ledger/models.py` (`TransactionType`)

**Usage:** The manual transaction API accepts only `DEPOSIT` and `WITHDRAWAL`.
`WAGER_STAKE` and `WAGER_PAYOUT` are emitted by wagering placement and settlement.

---

### Amount (cents)

**Definition:** A signed, non-zero integer amount in cents representing a ledger posting.

**Data Type:** integer

**Format/Constraints:** Non-zero; positive credits, negative debits; the API accepts
two-decimal floats which are converted to cents internally.

**Source:** `ledger_transactions.amount_cents`

**Usage:** Stored as cents to avoid floating-point rounding across balances and statements.

---

### American Odds

**Definition:** Signed integer American-odds quote for a CFB market selection.

**Data Type:** integer

**Format/Constraints:** Non-zero; positive for underdogs (+), negative for favorites (-).

**Source:** `cfb_market_quotes.american_odds`

**Usage:** Captured during manual CFB intake and locked onto each bet for settlement.

---

### Bet Status

**Definition:** Lifecycle result of a durable simulated bet.

**Allowed values:** `PENDING`, `WON`, `LOST`, `PUSH`

**Source:** `src/edgebook/wagering/models.py` (`BetStatus`)

**Usage:** Pending after placement and finalized atomically when the game score is recorded.

---

### Market Type

**Definition:** The category of a CFB betting market.

**Data Type:** enum (string)

**Allowed values:** `SPREAD`, `MONEYLINE`, `TOTAL`

**Source:** `src/edgebook/cfb/models.py` (`MarketType`)

**Usage:** One market type per game; combined with `MarketSelection` defines a wagerable
outcome.

---

### Market Selection

**Definition:** The outcome side being quoted within a market.

**Data Type:** enum (string)

**Allowed values:** `HOME`, `AWAY`, `OVER`, `UNDER`

**Source:** `src/edgebook/cfb/models.py` (`MarketSelection`)

**Usage:** Paired with a market to form a quote; a market opens once it has its required
pair of quotes.
