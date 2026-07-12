#!/usr/bin/env bash
# Back up the Edgebook Postgres database to a timestamped, compressed file.
#
# The dump is written in pg_dump custom format (-Fc, compressed) under the
# configured backup directory. Only the RETENTION most recent backups are kept;
# older files are pruned automatically.
#
# Configuration (environment overrides):
#   COMPOSE_FILE   Compose file with the db service (default: docker-compose.prod.yml)
#   BACKUP_DIR     Where to write dumps (default: ./backups)
#   RETENTION      Number of backups to keep (default: 7)
#   POSTGRES_USER  Postgres user (default: edgebook)
#   POSTGRES_DB    Postgres database (default: edgebook)
#
# Usage:
#   scripts/backup_db.sh
#   COMPOSE_FILE=docker-compose.yml RETENTION=14 scripts/backup_db.sh

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION="${RETENTION:-7}"
PG_USER="${POSTGRES_USER:-edgebook}"
PG_DB="${POSTGRES_DB:-edgebook}"

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="${BACKUP_DIR}/edgebook-${timestamp}.dump"

echo "Backing up '${PG_DB}' (user '${PG_USER}') via ${COMPOSE_FILE}..."
# -T disables TTY allocation so the dump streams cleanly to the redirect.
docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U "$PG_USER" -d "$PG_DB" -Fc >"$backup_file"

echo "Created backup: ${backup_file} ($(du -h "$backup_file" | cut -f1))"

# Prune older backups beyond the retention limit (newest first).
pruned=0
while IFS= read -r old; do
    echo "Pruning old backup: ${old}"
    rm -f "$old"
    pruned=$((pruned + 1))
done < <(ls -1t "${BACKUP_DIR}"/edgebook-*.dump 2>/dev/null | tail -n +$((RETENTION + 1)))

remaining="$(ls -1 "${BACKUP_DIR}"/edgebook-*.dump 2>/dev/null | wc -l | tr -d ' ')"
echo "Done. Kept ${remaining} backup(s) (limit ${RETENTION}); pruned ${pruned}."
