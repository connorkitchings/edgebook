"""Provider registry and safe runtime configuration for ingestion jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from edgebook.core.config import settings
from edgebook.ingestion.adapters import (
    ProviderAdapter,
    ProviderConfigurationError,
    TheOddsApiAdapter,
)


@dataclass(frozen=True)
class ProviderStatus:
    """Public, credential-free provider capability report."""

    name: str
    configured: bool
    live_enabled: bool
    supports_historical: bool


def provider_statuses() -> list[ProviderStatus]:
    """Return supported providers without ever exposing credential values."""
    return [
        ProviderStatus("the-odds-api", bool(settings.ODDS_API_KEY), True, True),
        ProviderStatus(
            "sportsdataio", bool(settings.SPORTSDATAIO_API_KEY), False, True
        ),
        ProviderStatus(
            "college-football-data",
            bool(settings.COLLEGE_FOOTBALL_DATA_API_KEY),
            False,
            True,
        ),
    ]


def configured_provider(name: str) -> ProviderAdapter:
    """Construct the requested live provider, or reject disabled providers safely."""
    if name != "the-odds-api":
        raise ProviderConfigurationError(
            f"{name} is fixture-ready only and has no live implementation enabled"
        )
    return TheOddsApiAdapter(
        settings.ODDS_API_KEY,
        regions=settings.ODDS_API_REGIONS,
        bookmakers=settings.ODDS_API_BOOKMAKERS,
        timeout_seconds=settings.INGESTION_HTTP_TIMEOUT_SECONDS,
        max_retries=settings.INGESTION_HTTP_MAX_RETRIES,
    )


def historical_provider(name: str, snapshot_at: datetime) -> TheOddsApiAdapter:
    """Fetch one historical snapshot from a provider with entitlement validation."""
    adapter = configured_provider(name)
    if not isinstance(adapter, TheOddsApiAdapter):  # defensive future extension
        raise ProviderConfigurationError(
            f"{name} does not support historical snapshots"
        )
    adapter.fetch_historical_sync(snapshot_at)
    return adapter
