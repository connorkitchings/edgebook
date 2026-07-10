.PHONY: help install setup test lint format format-check docs docs-serve validate clean all dev

help:	## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:	## Install dependencies
	uv sync

setup:	## Interactive project setup
	uv run python scripts/setup_project.py

test:	## Run tests with coverage
	uv run pytest tests/test_config.py tests/integration/ --cov=vibe_coding --cov-report=html --cov-report=term-missing

lint:	## Run linter
	uv run ruff check .

format:	## Format code
	uv run ruff format .

format-check:	## Check code formatting
	uv run ruff format . --check

docs:	## Build documentation
	uv run mkdocs build

docs-serve:	## Serve documentation locally
	uv run mkdocs serve

validate:	## Validate template
	uv run python scripts/validate_template.py

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
	@echo "Run 'make docs-serve' to preview documentation"
