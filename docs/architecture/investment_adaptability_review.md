# Investment Adaptability Review

## Outcome

Edgebook is ready to preserve, rather than implement, a future paper-investing option. The generic
ledger and account primitives can support another allocation domain without changing the current
CFB product model.

## Boundary Findings

| Area | Current role | Phase 6 decision |
| --- | --- | --- |
| Ledger | Append-only, double-entry simulation credits | Keep generic and unaware of sports or investments. |
| CFB | Teams, games, markets, odds, and scores | Keep sport-specific; do not generalize prematurely. |
| Wagering | Bet lifecycle and ledger postings | Keep as the sports coordination boundary. |
| Ingestion | Provider data and score confidence | Restrict to provider/CFB synchronization. |
| Application | Cross-domain operational workflows | Own settlement, conflict resolution, and review scheduling. |
| Analytics | Read-side performance composition | May read domains but must not be imported by them. |
| Future identity | User/profile ownership | Remain separate from fictional ledger accounts until authentication. |

## Future Investing Seam

A later `investing` domain may model instruments and paper positions, while an application workflow
coordinates it with the existing ledger. It must not reuse CFB games, markets, bets, or ingestion
types as generic financial abstractions. Introduce that domain only after a product decision defines
its user flows and accounting semantics.

## Guardrails

- Domain import rules are enforced by `tests/architecture/test_import_boundaries.py`.
- No investment schema, API, credential, or market-data integration is part of Phase 6.
- Authentication and authorization remain prerequisites for exposing operator workflows publicly.

