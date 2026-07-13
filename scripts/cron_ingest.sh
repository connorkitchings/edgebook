#!/usr/bin/env bash
# Daily ingestion one-shot, intended to be run by host cron.
#
# Replaces the long-running ingestion-worker container. Invokes the existing
# CLI sync command in a throwaway app container that shares the production
# stack network (so it can reach the db) and environment (ODDS_API_KEY, etc.).
#
# Install from cron at 08:00 America/New_York (see docs/deployment.md):
#   CRON_TZ=America/New_York
#   0 8 * * *  cd /opt/edgebook && ./scripts/cron_ingest.sh >> logs/ingest.log 2>&1

set -euo pipefail

cd "$(dirname "$0")/.."

# --no-deps: db and app are already running; we only need a one-shot container.
docker compose -f docker-compose.prod.yml run --rm --no-deps app \
    python -m edgebook.ingestion.cli sync --provider the-odds-api
