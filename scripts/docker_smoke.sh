#!/usr/bin/env bash

set -euo pipefail

cleanup() {
  docker compose down -v --remove-orphans
}

trap cleanup EXIT

export PORT="$(python3 -c 'import socket; sock = socket.socket(); sock.bind(("127.0.0.1", 0)); print(sock.getsockname()[1]); sock.close()')"

docker compose down -v --remove-orphans
docker compose up --build --wait --wait-timeout 90

expected_revision="$(uv run alembic heads | awk '{print $1}')"
actual_revision="$(docker compose exec -T db psql -U edgebook -d edgebook -tAc 'SELECT version_num FROM alembic_version')"

test "$actual_revision" = "$expected_revision"
curl --fail --silent --show-error "http://localhost:${PORT}/health" | \
  grep -q '"status":"ok"'
