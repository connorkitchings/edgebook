# ADR-0001: Modular Monolith Architecture

## Status
Accepted (2026-07-10)

## Context
Edgebook requires a clean separation between generic ledger-accounting concepts and college-football-specific concepts to support future adaptability for paper-investing use cases. The system must remain simple to operate and deploy while maintaining strict domain boundaries.

## Decision
Adopt a **modular monolith** architecture within a single FastAPI application. The codebase is partitioned into three domain boundaries plus supporting layers:

| Boundary | Location | Responsibility | Import Rules |
|----------|----------|----------------|--------------|
| **Ledger** | `src/edgebook/ledger/` | Generic double-entry accounting | Imports only `core/` |
| **CFB** | `src/edgebook/cfb/` | College-football domain (teams, games, markets, quotes) | Imports only `core/` |
| **Wagering** | `src/edgebook/wagering/` | Coordinates CFB events into ledger postings | Imports `core/`, `cfb/`, `ledger/` |
| **API** | `src/edgebook/api/` | REST routes delegating to domain modules | Imports domain modules and `core/` |
| **Core** | `src/edgebook/core/` | Config, database session, shared utilities | No domain imports |

### Key Constraints
- `ledger` and `cfb` **never import from each other**
- `wagering` is the only boundary that composes across `ledger` and `cfb`
- All monetary amounts stored as integer cents to avoid floating-point
- All ledger postings are append-only and immutable (enforced by DB triggers)
- Every journal entry must balance to zero (validated in service layer)

## Consequences
- **Positive**: Ledger is reusable for non-sports paper-investing scenarios; CFB module can evolve independently; single deployable artifact simplifies operations
- **Negative**: Cross-boundary coordination (wagering) requires careful transaction management; no independent scaling of boundaries
- **Risk**: Boundary violations must be caught in code review; no compile-time enforcement of import rules

## Alternatives Considered
- **Microservices**: Rejected — premature complexity for a simulation platform with a small user base
- **Single-module monolith**: Rejected — would couple ledger and CFB concepts, blocking future adaptability
