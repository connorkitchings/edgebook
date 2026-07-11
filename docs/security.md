# Security & Responsible Use Policy: Edgebook

This document outlines key security guidelines and responsible-use rules for Edgebook.

## Responsible Use: Strictly Simulation-Only
Edgebook is built as a **paper-betting and simulation platform** to test sports analytics, banking ledgers, and allocation strategies.

> [!IMPORTANT]
> **NO REAL MONEY SYSTEM WAGERS:** Edgebook does not handle real currency, does not deposit real money, and must not interface with real sportsbook APIs to place real-money wagers. Any development work that facilitates real-money gambling is strictly out of scope and prohibited.

---

## Security Guidelines

### 1. Secret Management
- **Zero Credentials in Code:** Never commit api keys, database passwords, or environment credentials.
- **Environment Configuration:** Load configurations using environment variables or a `.env` file (which must remain in `.gitignore`).
- **Pydantic Settings:** Let Pydantic Settings handle type conversions and defaults.

### 2. Double-Entry Accounting Validation
To ensure simulation bankroll integrity and protect against data corruption:
- Ledger records are append-only.
- Balance modifications must only occur via ledger transaction entries.
- Validation checks must verify that total assets match total stakes + winnings across the database prior to balance adjustments.

### 3. Database Sanitization
- SQL injection is mitigated by using SQLAlchemy parameters and parameterized queries for all inputs.
- Cross-Site Scripting (XSS) is mitigated by sanitizing game final scores and text reason fields.
