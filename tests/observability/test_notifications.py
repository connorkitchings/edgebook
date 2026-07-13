"""Tests for the best-effort webhook notifier."""

import httpx

from edgebook.core.config import settings
from edgebook.observability.notifications import notify_ingestion_failure


def test_notify_noop_when_url_unset(monkeypatch):
    """No webhook call is made when ALERT_WEBHOOK_URL is empty."""
    monkeypatch.setattr(settings, "ALERT_WEBHOOK_URL", "")
    calls: list = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append((a, k)))

    notify_ingestion_failure(
        run_id="r1",
        provider="p",
        scope="games",
        error="boom",
        started_at=None,
        quota_remaining=None,
    )

    assert calls == []


def test_notify_posts_payload_when_configured(monkeypatch):
    """A configured URL receives a JSON alert with the run details."""
    monkeypatch.setattr(
        settings, "ALERT_WEBHOOK_URL", "https://hooks.example.com/alert"
    )

    captured: dict = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs

        class _Response:
            status_code = 200

        return _Response()

    monkeypatch.setattr(httpx, "post", fake_post)

    notify_ingestion_failure(
        run_id="r1",
        provider="the-odds-api",
        scope="games",
        error="ValueError: boom",
        started_at=None,
        quota_remaining=42,
    )

    assert captured["url"] == "https://hooks.example.com/alert"
    payload = captured["kwargs"]["json"]
    assert payload["event"] == "ingestion.run_failed"
    assert payload["provider"] == "the-odds-api"
    assert payload["quota_remaining"] == 42
    assert payload["error"].startswith("ValueError")
    assert captured["kwargs"]["timeout"] == settings.ALERT_WEBHOOK_TIMEOUT_SECONDS


def test_notify_swallows_transport_errors(monkeypatch):
    """A failing webhook must never raise into the caller (ingestion)."""
    monkeypatch.setattr(
        settings, "ALERT_WEBHOOK_URL", "https://hooks.example.com/alert"
    )

    def boom(*args, **kwargs):
        raise httpx.ConnectError("unreachable")

    monkeypatch.setattr(httpx, "post", boom)

    # Must not raise.
    notify_ingestion_failure(
        run_id="r1",
        provider="p",
        scope="s",
        error="x",
        started_at=None,
        quota_remaining=None,
    )
