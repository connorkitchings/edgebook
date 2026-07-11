.PHONY: help install test lint format format-check migrate docs docs-serve clean all dev

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
