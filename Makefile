.PHONY: help install test lint format format-check migrate docs docs-serve clean all dev docker-build docker-up docker-down session-start session-end

help:	## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:	## Install dependencies
	uv sync

test:	## Run tests with coverage
	uv run pytest

lint:	## Run linter
	uv run ruff check .

format:	## Format code
	uv run ruff format .

format-check:	## Check code formatting
	uv run ruff format . --check

migrate:	## Apply database migrations
	uv run alembic upgrade head

docs:	## Build documentation
	uv sync --extra docs
	uv run mkdocs build --strict

docs-serve:	## Serve documentation locally
	uv sync --extra docs
	uv run mkdocs serve

clean:	## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov site

all:	## Run all quality checks (format, lint, test)
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test

dev:	## Start development environment
	@echo "Starting development environment..."
	@echo "Run 'make test' to verify setup"
	@echo "Run 'make migrate' to apply database migrations"
	@echo "Run 'make docs-serve' to preview documentation"

docker-build:	## Build Docker images
	docker compose build

docker-up:	## Start app and Postgres via Docker Compose
	docker compose up -d
	@echo "App running at http://localhost:8000"

docker-down:	## Stop Docker Compose services
	docker compose down

session-start:	## Show session startup checklist
	@echo "=== Session Startup ==="
	@echo "1. Branch:  $$(git branch --show-current)"
	@echo "2. Context: cat .agent/CONTEXT.md"
	@echo "3. Skill:   .agent/skills/session-lifecycle/SKILL.md"
	@echo "4. Recent:  ls -t session_logs/*/"
	@echo ""
	@echo "Recent commits:"
	@git log --oneline -5

session-end:	## Run health checks and show session log checklist
	@echo "=== Session Shutdown ==="
	@echo "Running health checks..."
	@uv run ruff format . && echo "Format: OK" || echo "Format: FAILED"
	@uv run ruff check . && echo "Lint: OK" || echo "Lint: FAILED"
	@uv run pytest -q && echo "Tests: OK" || echo "Tests: FAILED"
	@echo ""
	@echo "Create session log:"
	@echo "  mkdir -p session_logs/$$(date +%m-%d-%Y)"
	@echo "  cp session_logs/TEMPLATE.md session_logs/$$(date +%m-%d-%Y)/N\ -\ Title.md"
	@echo ""
	@echo "Skill: .agent/skills/session-lifecycle/SKILL.md"
