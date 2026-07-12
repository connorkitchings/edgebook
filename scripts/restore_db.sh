#!/usr/bin/env bash
# Restore the Edgebook Postgres database from a backup file produced by
# backup_db.sh.
#
# This OVERWRITES the target database: the public schema is dropped and
# recreated, then the backup is loaded. A confirmation prompt requires typing
# the database name to guard against accidental production restores.
#
# Configuration (environment overrides):
#   COMPOSE_FILE   Compose file with the db service (default: docker-compose.prod.yml)
#   POSTGRES_USER  Postgres user (default: edgebook)
#   POSTGRES_DB    Postgres database (default: edgebook)
#
# Usage:
#   scripts/restore_db.sh <backup-file>

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <backup-file>" >&2
    exit 1
fi

backup_file="$1"
if [ ! -f "$backup_file" ]; then
    echo "Error: backup file not found: ${backup_file}" >&2
    exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
PG_USER="${POSTGRES_USER:-edgebook}"
PG_DB="${POSTGRES_DB:-edgebook}"

echo "WARNING: this will DROP and REPLACE the '${PG_DB}' database."
echo "  source: ${backup_file}"
echo "  target: ${PG_DB} (user ${PG_USER}) via ${COMPOSE_FILE}"
read -r -p "Type the database name (${PG_DB}) to confirm restore: " confirm
if [ "$confirm" != "$PG_DB" ]; then
    echo "Aborted: confirmation did not match '${PG_DB}'." >&2
    exit 1
fi

echo "Dropping and recreating 'public' schema in '${PG_DB}'..."
# Connect to the target database to reset its schema before loading the dump.
docker compose -f "$COMPOSE_FILE" exec -T db \
    psql -U "$PG_USER" -d "$PG_DB" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null

echo "Restoring ${backup_file} into '${PG_DB}'..."
docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_restore -U "$PG_USER" -d "$PG_DB" --no-owner --no-acl <"$backup_file"

echo "Restore complete."
echo "Run 'alembic upgrade head' if the restored schema needs re-stamping."
