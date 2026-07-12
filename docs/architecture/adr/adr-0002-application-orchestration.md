# ADR-0002: Application Orchestration Boundary

## Status

Accepted (2026-07-12)

## Context

Provider ingestion persists CFB observations, while settlement and review scheduling mutate
wagering state. Keeping those workflows in `ingestion` coupled an adapter-oriented domain to the
wagering boundary and weakened the module rules established by ADR-0001.

## Decision

Create `src/edgebook/application/` for workflows that compose domains:

- `ingestion` owns provider adapters, immutable observations, checkpoints, and CFB synchronization.
- `application` owns confirmed-score settlement, operator conflict resolution, and scheduled review claims.
- `wagering` continues to coordinate bet placement and ledger postings.
- API routes and CLI command adapters may invoke `application`; domains may not import it.

The legacy `edgebook.ingestion.cli` path remains supported as a command adapter and is the sole
documented ingestion-package exception permitted to import `application`.

## Consequences

- The ledger remains reusable for a future paper-investing domain without importing sports code.
- CFB remains intentionally sport-specific; this decision does not add generic instruments,
  portfolios, positions, or event abstractions.
- AST-based tests enforce the allowed import graph and prevent a future `ingestion -> wagering`
  dependency.

