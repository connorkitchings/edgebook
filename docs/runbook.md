# Runbook

This runbook documents how to operate and troubleshoot the **Vibe Coding Data Science Template** in its default state. When the template becomes a named project, extend each section with environment-specific details per the [Template Kickoff Guide](./template_starting_guide.md).

## Table of Contents

- [Monitoring](#monitoring)
- [Common Issues & Troubleshooting](#common-issues--troubleshooting)
- [Deployment & Rollback](#deployment--rollback)
- [Contact & Escalation](#contact--escalation)

## Monitoring

- **CI Pipeline:** GitHub Actions workflow `.github/workflows/ci.yml` runs linting, security scans, and tests on every push/PR. Treat red builds as the primary health signal while the template is being tailored.
- **Prefect Flows (local):** When running `prefect server start`, use Prefect Orion UI (default `http://127.0.0.1:4200`) to inspect flow runs from `src/vibe_coding/flows/`.
- **Structured Logs:** Application scripts use `vibe_coding.utils.logging` which logs to stdout with timestamps and module names. Redirect output to files during longer runs for later analysis.

## Common Issues & Troubleshooting

### Issue: `uv sync` fails or dependencies missing

**Symptoms:**
- `uv sync` exits with resolution errors or missing interpreter messages.

**Troubleshooting Steps:**
1. Verify Python 3.10+ is installed: `python3 --version`.
2. Clear the `.venv` (if created) and rerun `uv sync`.
3. On macOS/Linux, ensure `uv` binary is on the PATH (`which uv`).

**Resolution:**
Re-run `uv sync` after environment correction. Consult `pyproject.toml` to confirm dependency pins remain intact.

### Issue: Prefect example flow fails to start

**Symptoms:**
- CLI prints connection errors (e.g., `Failed to connect to Orion API`).

**Troubleshooting Steps:**
1. Ensure `prefect server start` is running in a separate terminal.
2. Export `PREFECT_API_URL=http://127.0.0.1:4200/api`.
3. Rerun `python src/vibe_coding/flows/example_flow.py`.

**Resolution:**
Restart the Prefect server and flow once configuration variables are set. Document any persistent errors in `docs/knowledge_base.md`.

### Issue: CI pipeline red due to lint/test failure

**Symptoms:**
- GitHub Actions job fails on `ruff` or `pytest`.

**Troubleshooting Steps:**
1. Reproduce locally with `uv run ruff format . && uv run ruff check .` and `uv run pytest -vv`.
2. Apply fixes or update tests to meet expectations.
3. Push changes; confirm pipeline passes.

**Resolution:**
Keep local checks green before pushing to avoid repeated CI failures.

## Deployment & Rollback

The template does not ship production deployments. When converting to a real project:

- Document deployment targets (staging/prod) and release commands here.
- Record rollback steps (e.g., revert tags, redeploy previous container).
- Link to automation scripts or external runbooks once created.

## Contact & Escalation

- **Primary Maintainer:** Connor Kitchings (`connorkitchings` on GitHub).
- **Escalation Path:** If adoption teams encounter issues beyond the template scope, open an issue in the repository and notify the DevEx Guild for triage.
