"""Tests for metrics, health probes, and HTTP instrumentation."""

from prometheus_client import generate_latest

from edgebook.ingestion.models import IngestionRun
from edgebook.ingestion.services import _fail, _finish


def test_healthz_reports_liveness(client):
    """/healthz is an unauthenticated liveness probe that always returns 200."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readyz_reports_database_status(client):
    """/readyz reflects database reachability."""
    response = client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_backward_compatible(client):
    """The legacy /health endpoint remains available for existing healthchecks."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint_exposes_counters(client):
    """/metrics exposes Prometheus-format text including our base metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    body = response.text
    assert "edgebook_http_requests_total" in body
    assert "edgebook_db_up" in body


def test_http_middleware_counts_requests(client):
    """Hitting an endpoint increments the request counter for that route."""
    client.get("/healthz")
    body = client.get("/metrics").text
    assert "edgebook_http_requests_total" in body
    assert 'path_template="/healthz"' in body
    assert 'method="GET"' in body


def test_finish_instruments_ingestion_counter(db_session):
    """_finish bumps the ingestion-runs counter for the completed outcome."""
    run = IngestionRun(provider="test-finish", scope="games", status="RUNNING")
    db_session.add(run)
    db_session.flush()

    _finish(db_session, run, status="COMPLETED")

    body = generate_latest().decode()
    assert "edgebook_ingestion_runs_total" in body
    assert 'provider="test-finish"' in body
    assert 'status="COMPLETED"' in body


def test_fail_instruments_ingestion_counter(db_session):
    """_fail bumps the ingestion-runs counter for the failed outcome."""
    run = IngestionRun(provider="test-fail", scope="quotes", status="RUNNING")
    db_session.add(run)
    db_session.flush()

    _fail(db_session, run, ValueError("boom"))

    body = generate_latest().decode()
    assert "edgebook_ingestion_runs_total" in body
    assert 'provider="test-fail"' in body
    assert 'status="FAILED"' in body
