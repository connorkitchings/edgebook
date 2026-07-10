# Silo Ingestion Architecture

## Overview
For projects ingesting data from multiple external sources (e.g., APIs, scrapers), we use a **Silo Ingestion Pattern**. This ensures that raw data from each source is preserved in isolation before being merged into a production schema. This pattern allows for safe debugging, easy re-ingestion, and clear provenance.

## The Pattern

1.  **Ingest to Silo:** Data is fetched and stored in a source-specific "silo" (schema or table namespace).
    -   *Goal:* Capture the external state faithfully.
    -   *Constraint:* Do not normalize or transform significantly at this stage.
    -   *Example:* `silo_nugsnet.shows`, `silo_setlistfm.shows`

2.  **Normalize & Parse:** Structured data is extracted from the raw silo data.
    -   *Goal:* Convert raw text/JSON into domain objects (e.g., parsing "Notes" into "Guests").
    -   *Ops:* Idempotent transformations.

3.  **Merge to Production:** A priority-based merge script promotes data to the `public` (production) schema.
    -   *Goal:* Create a single "Golden Record".
    -   *Logic:* `Nugs > SetlistFM > Relisten` (Example Priority).
    -   *Provenance:* Track *which* source provided each field.

## Key Principles

-   **Isolation:** A bug in one source's ingestion should not corrupt the others or the production schema.
-   **Idempotence:** You should be able to re-run ingestion and merge scripts without creating duplicates.
-   **Provenance:** Always store *where* a piece of data came from.

## Example Workflow

```bash
# 1. Ingest Nugs.net data to silo_nugsnet
python scripts/ingest_nugs.py --year 2024

# 2. Ingest Setlist.fm data to silo_setlistfm
python scripts/ingest_setlistfm.py --year 2024

# 3. Merge to Production (Public Schema)
python scripts/merge_silos.py --year 2024
```
