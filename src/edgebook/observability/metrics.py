"""Prometheus metrics for Edgebook.

Metric naming follows the ``edgebook_<subsystem>_<name>`` convention so the
exported series are easy to filter on in dashboards and alert rules. The
default ``prometheus_client`` registry also exports standard process and
Python runtime metrics (gc, memory, info) for free.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge

HTTP_REQUESTS = Counter(
    "edgebook_http_requests_total",
    "Total HTTP requests handled by the application.",
    ["method", "path_template", "status"],
)

INGESTION_RUNS = Counter(
    "edgebook_ingestion_runs_total",
    "Total ingestion runs finalized, by provider/scope/outcome.",
    ["provider", "scope", "status"],
)

INGESTION_QUOTA_REMAINING = Gauge(
    "edgebook_ingestion_quota_remaining",
    "Remaining provider API quota after the most recent ingestion run.",
    ["provider"],
)

DB_UP = Gauge(
    "edgebook_db_up",
    "1 if the application database is reachable on the last readiness check, "
    "0 otherwise.",
)
