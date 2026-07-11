# Project Charter: Edgebook

This document is the single source of truth for Edgebook's goals, scope, and technical context.

> 📚 For a high-level entry point and links to all documentation, see `README.md`.

## Project Overview

**Project Name:** Edgebook

**Project Vision:** Deliver a simulation-only college football paper-betting platform that allows users to manage a fictional bankroll, record simulated bets, track results, and analyze whether their allocation choices are profitable over time. The platform's core architecture will cleanly separate ledger-accounting concepts from college football specific concepts to ensure future adaptability for a paper-investing system.

**Technical Goal:** Build a FastAPI-based modular monolith backend running on PostgreSQL, with a modern frontend, validated by automated CI checks, and governed by strict double-entry ledger controls.

**Responsible Use Policy:** Edgebook is exclusively for paper trading and simulation. Under no circumstances will it process real money or integrate with real-money wagering interfaces.

---

## Users & User Stories

### Primary Persona

**Target User:** Dana the Disciplined Allocator
- **Description:** An enthusiast who wants to test college football betting strategies, record fictional stake allocations and reasoning, and mathematically analyze profit-and-loss performance without putting actual capital at risk.
- **Pain Points:** Hard to track bankroll history across spreadsheet tools, lack of post-settlement analytics on allocation discipline, and absence of an audit-proof transaction ledger.
- **Goals:** Accurately log simulated bets, evaluate ROI, filter performance by market type and stake allocation, and review cognitive biases.

### Core User Stories

**Story 1:** As Dana, I want to create a fictional account with a starting bankroll so that I can track my simulation starting point. (Priority: Must-have, Phase 1)
**Story 2:** As Dana, I want to enter a game, record a bet (stake, odds, optional reasoning), and later update the game's final score to settle the bet. (Priority: Must-have, Phase 1)
**Story 3:** As Dana, I want my bankroll balance to update automatically when a bet is settled, with an immutable audit trail showing the transaction log. (Priority: Must-have, Phase 1)
**Story 4:** As Dana, I want to see basic performance stats like ROI, net units won/lost, and performance split by fictional stake allocation. (Priority: Should-have, Phase 3)

---

## Technical Stack

| Category | Technology | Version | Notes |
|----------|------------|---------|-------|
| Environment Manager | uv | >=0.4.x | Python environment resolver and runner |
| Programming Language | Python | 3.11.x | Backend engine and analytics calculation |
| Web Framework | FastAPI | 0.116+ | REST API engine |
| Database | PostgreSQL | 15+ | System of record for ledger and sportsman data |
| ORM | SQLAlchemy | 2.0+ | Database abstraction layer |
| Linting & Formatting | Ruff | 0.14+ | Standard linting and formatting tool |
| Testing | Pytest | 8.x | Test framework |

---

## Risks & Assumptions

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ledger discrepancies or double-spending simulation credits | Low | High | Enforce database-level constraint checks and transactional double-entry verification |
| CFB schema changes complicate future paper-investing adaptations | Medium | Medium | Maintain strict separation between the reusable `ledger`, sports-specific `cfb`, and coordinating `wagering` modules |
| External odds APIs rate-limiting ingestion | High | Low | Cache historical queries and implement manual entry fallbacks for all workflows |

---

## Decision Log

| Date | Decision | Context / Drivers | Impact / Follow-up |
|------|----------|-------------------|-------------------|
| 2026-07-10 | Adopt Modular Monolith architecture | Avoid microservices complexity while maintaining code separation | Maintain `ledger`, `cfb`, and cross-domain `wagering` boundaries inside `src/edgebook` |
| 2026-07-11 | Derive conviction from allocation | A separate confidence score duplicates actual fictional stake behavior | Snapshot pre-bet bankroll and calculate conviction from stake percentage in analytics |
| 2026-07-10 | Pin Python environment to 3.11 | Resolve compilation issues with Pydantic core under Python 3.14 | Created `.python-version` pinning the workspace to 3.11 |
