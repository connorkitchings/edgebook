# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v2.0.0] - 2026-02-11

### Added
- **Interactive Setup Script** (`scripts/setup_project.py`)
  - Automated project initialization with prompts for project details
  - Automatic replacement of template variables across all files
  - Git repository initialization and feature branch creation
  - Creates .gitignore with standard patterns

- **Git Integration for Commit Messages** (`vibe_sync suggest`)
  - Analyzes latest session log to generate conventional commit messages
  - Detects commit type (feat, fix, docs, test, refactor) from session content
  - Lists changed files from git status
  - Provides suggested git commit commands

- **Integration Tests** (`tests/integration/`)
  - `test_config_integration.py` - Tests config module with actual files
  - `test_logging_integration.py` - Tests logging with file output
  - `test_workflow_integration.py` - Tests CLI tools and workflows

- **Test Coverage Reporting**
  - Configured pytest-cov with 75% coverage target
  - HTML and terminal coverage reports
  - Coverage configuration in pyproject.toml

- **Test Fixtures** (`tests/fixtures/`)
  - `sample_config.env` - Example configuration values
  - `sample_logging_config.json` - Example logging configuration
  - `sample_session_log.md` - Example session log format

- **Template Versioning**
  - `TEMPLATE_VERSION` file for tracking template version (v2.0.0)
  - Version checking in `validate_template.py`
  - Major version numbering scheme

- **Makefile** with convenient commands
  - `make setup` - Interactive project setup
  - `make test` - Run tests with coverage
  - `make lint` / `make format` - Code quality
  - `make docs` / `make docs-serve` - Documentation
  - `make validate` - Template validation
  - `make all` - Run all quality checks

- **VS Code Snippets** (`.vscode/vibe-coding.code-snippets`)
  - Config import pattern
  - Logging setup pattern
  - Pytest fixture template
  - Session log section template

- **Editor Configuration** (`.editorconfig`)
  - Consistent formatting across editors
  - 4-space indentation for Python/Markdown
  - UTF-8 encoding, LF line endings

- **Enhanced Documentation**
  - Quick Start section in getting_started.md
  - Template Migration Guide (new file)
  - Troubleshooting guide expanded
  - Pre-commit hooks documentation

### Changed
- Updated implementation schedule to reflect template improvements
- Enhanced session log template alignment with CLI output
- Improved documentation structure with better navigation
- Fixed all health-check path references (.sh → .md)
- Consolidated duplicate AGENTS.md files
- Aligned version references (3.11+ → 3.10+)

### Fixed
- Resolved template variable placeholders with dual approach
- Fixed broken documentation links
- Standardized session log format across templates

### Changed

### Deprecated

### Removed

### Fixed

### Security
