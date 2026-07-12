"""Provider-neutral normalized feed contracts and deterministic fixture adapters."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from asyncio import run
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

import httpx

from edgebook.cfb.models import MarketSelection, MarketType


@dataclass(frozen=True)
class ExternalGame:
    external_id: str
    home_team: str
    away_team: str
    scheduled_at: datetime


@dataclass(frozen=True)
class ExternalQuote:
    external_id: str
    game_external_id: str
    market_type: MarketType
    line_millipoints: int | None
    selection: MarketSelection
    american_odds: int
    observed_at: datetime
    source: str | None = None


@dataclass(frozen=True)
class ExternalScore:
    external_id: str
    game_external_id: str
    home_score: int
    away_score: int
    observed_at: datetime


class ProviderAdapter(Protocol):
    """Normalized provider contract; concrete vendors map their feeds here."""

    name: str

    def games(self) -> list[ExternalGame]: ...

    def quotes(self) -> list[ExternalQuote]: ...

    def scores(self) -> list[ExternalScore]: ...


class ProviderConfigurationError(ValueError):
    """Raised when a provider is requested without its required configuration."""


class ProviderRequestError(RuntimeError):
    """Raised for sanitized provider transport or response failures."""


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _millipoints(value: object | None) -> int | None:
    if value is None:
        return None
    return int(Decimal(str(value)) * 1000)


class RemoteProviderAdapter(ABC):
    """Shared bounded-retry async transport for concrete provider adapters."""

    name: str

    def __init__(self, *, timeout_seconds: float = 10, max_retries: int = 2) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.quota_remaining: str | None = None

    async def _get_json(
        self, url: str, *, params: dict[str, str], headers: dict[str, str]
    ) -> Any:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.get(url, params=params, headers=headers)
                    self.quota_remaining = response.headers.get(
                        "x-requests-remaining", self.quota_remaining
                    )
                    if response.status_code == 429 and attempt < self.max_retries:
                        continue
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError) as error:
                    if attempt == self.max_retries:
                        raise ProviderRequestError(
                            f"{self.name} request failed ({type(error).__name__})"
                        ) from error
        raise AssertionError("retry loop must return or raise")

    @abstractmethod
    async def fetch_current(self) -> None: ...

    def fetch_current_sync(self) -> None:
        """Bridge the scheduler's synchronous interface to async HTTP safely."""
        run(self.fetch_current())


class TheOddsApiAdapter(RemoteProviderAdapter):
    """Maps The Odds API NCAAF featured markets into normalized observations."""

    name = "the-odds-api"
    _url = "https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds"
    _historical_url = (
        "https://api.the-odds-api.com/v4/historical/sports/americanfootball_ncaaf/odds"
    )

    def __init__(
        self,
        api_key: str,
        *,
        regions: str = "us",
        bookmakers: str = "",
        timeout_seconds: float = 10,
        max_retries: int = 2,
        payload: list[dict[str, Any]] | None = None,
        snapshot_at: datetime | None = None,
    ) -> None:
        super().__init__(timeout_seconds=timeout_seconds, max_retries=max_retries)
        if not api_key and payload is None:
            raise ProviderConfigurationError("ODDS_API_KEY is required")
        self.api_key = api_key
        self.regions = regions
        self.bookmakers = bookmakers
        self.payload = payload or []
        self.snapshot_at = snapshot_at

    async def fetch_current(self) -> None:
        params = {
            "apiKey": self.api_key,
            "regions": self.regions,
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
        }
        if self.bookmakers:
            params["bookmakers"] = self.bookmakers
        payload = await self._get_json(self._url, params=params, headers={})
        if not isinstance(payload, list):
            raise ProviderRequestError(
                "the-odds-api returned an invalid current payload"
            )
        self.payload = payload
        self.snapshot_at = datetime.now(UTC)

    async def fetch_historical(self, snapshot_at: datetime) -> None:
        params = {
            "apiKey": self.api_key,
            "regions": self.regions,
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
            "date": snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        }
        payload = await self._get_json(self._historical_url, params=params, headers={})
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ProviderRequestError(
                "the-odds-api returned an invalid historical payload"
            )
        self.payload = payload["data"]
        self.snapshot_at = _parse_datetime(
            payload.get("timestamp", snapshot_at.isoformat())
        )

    def fetch_historical_sync(self, snapshot_at: datetime) -> None:
        run(self.fetch_historical(snapshot_at))

    def games(self) -> list[ExternalGame]:
        return [
            ExternalGame(
                external_id=event["id"],
                home_team=event["home_team"],
                away_team=event["away_team"],
                scheduled_at=_parse_datetime(event["commence_time"]),
            )
            for event in self.payload
        ]

    def quotes(self) -> list[ExternalQuote]:
        market_types = {
            "h2h": MarketType.MONEYLINE,
            "spreads": MarketType.SPREAD,
            "totals": MarketType.TOTAL,
        }
        records: list[ExternalQuote] = []
        for event in self.payload:
            for bookmaker in event.get("bookmakers", []):
                source = f"{self.name}:{bookmaker['key']}"
                for market in bookmaker.get("markets", []):
                    market_type = market_types.get(market.get("key"))
                    if market_type is None:
                        continue
                    observed_at = _parse_datetime(
                        market.get("last_update")
                        or bookmaker.get("last_update")
                        or (self.snapshot_at or datetime.now(UTC)).isoformat()
                    )
                    for outcome in market.get("outcomes", []):
                        selection = self._selection(event, market_type, outcome["name"])
                        if selection is None:
                            continue
                        point = outcome.get("point")
                        records.append(
                            ExternalQuote(
                                external_id=(
                                    f"{event['id']}:{bookmaker['key']}:{market['key']}:"
                                    f"{outcome['name']}:{point}:{observed_at.isoformat()}"
                                ),
                                game_external_id=event["id"],
                                market_type=market_type,
                                line_millipoints=_millipoints(point),
                                selection=selection,
                                american_odds=int(outcome["price"]),
                                observed_at=observed_at,
                                source=source,
                            )
                        )
        return records

    @staticmethod
    def _selection(
        event: dict[str, Any], market_type: MarketType, outcome_name: str
    ) -> MarketSelection | None:
        if market_type == MarketType.TOTAL:
            return {"Over": MarketSelection.OVER, "Under": MarketSelection.UNDER}.get(
                outcome_name
            )
        if outcome_name == event["home_team"]:
            return MarketSelection.HOME
        if outcome_name == event["away_team"]:
            return MarketSelection.AWAY
        return None

    def scores(self) -> list[ExternalScore]:
        return []


@dataclass
class FixtureProviderAdapter:
    """In-memory adapter used for contract tests and scheduler dry runs."""

    name: str
    game_records: list[ExternalGame]
    quote_records: list[ExternalQuote]
    score_records: list[ExternalScore]

    def games(self) -> list[ExternalGame]:
        return self.game_records

    def quotes(self) -> list[ExternalQuote]:
        return self.quote_records

    def scores(self) -> list[ExternalScore]:
        return self.score_records


class SportsDataIoAdapter(FixtureProviderAdapter):
    """Fixture-backed mapping boundary for SportsDataIO's CFB game-line feeds."""

    name = "sportsdataio"

    @classmethod
    def from_payload(
        cls,
        games_payload: list[dict[str, Any]],
        lines_payload: list[dict[str, Any]] | None = None,
    ) -> "SportsDataIoAdapter":
        games: list[ExternalGame] = []
        quotes: list[ExternalQuote] = []
        scores: list[ExternalScore] = []
        for game in games_payload:
            game_id = str(game["GameID"])
            scheduled_at = _parse_datetime(game["DateTime"])
            games.append(
                ExternalGame(
                    game_id, game["HomeTeamName"], game["AwayTeamName"], scheduled_at
                )
            )
            if game.get("HomeScore") is not None and game.get("AwayScore") is not None:
                scores.append(
                    ExternalScore(
                        game_id,
                        game_id,
                        game["HomeScore"],
                        game["AwayScore"],
                        scheduled_at,
                    )
                )
        game_by_id = {game.external_id: game for game in games}
        for line in lines_payload or []:
            game_id = str(line["GameID"])
            external_game = game_by_id.get(game_id)
            if external_game is None:
                continue
            bookmaker = line.get("Sportsbook", line.get("SportsbookID", "unknown"))
            source = f"{cls.name}:{bookmaker}"
            observed_value = (
                line.get("LastUpdated") or external_game.scheduled_at.isoformat()
            )
            observed_at = _parse_datetime(str(observed_value))
            point_spread = line.get("PointSpread")
            for selection, odds, point, market_type in (
                (
                    MarketSelection.HOME,
                    line.get("HomeMoneyLine"),
                    None,
                    MarketType.MONEYLINE,
                ),
                (
                    MarketSelection.AWAY,
                    line.get("AwayMoneyLine"),
                    None,
                    MarketType.MONEYLINE,
                ),
                (
                    MarketSelection.HOME,
                    line.get("HomePointSpreadPayout"),
                    point_spread,
                    MarketType.SPREAD,
                ),
                (
                    MarketSelection.AWAY,
                    line.get("AwayPointSpreadPayout"),
                    -Decimal(str(point_spread)) if point_spread is not None else None,
                    MarketType.SPREAD,
                ),
                (
                    MarketSelection.OVER,
                    line.get("OverPayout"),
                    line.get("OverUnder"),
                    MarketType.TOTAL,
                ),
                (
                    MarketSelection.UNDER,
                    line.get("UnderPayout"),
                    line.get("OverUnder"),
                    MarketType.TOTAL,
                ),
            ):
                if odds is None:
                    continue
                quotes.append(
                    ExternalQuote(
                        external_id=(
                            f"{game_id}:{source}:{market_type}:{selection}:"
                            f"{point}:{observed_at.isoformat()}"
                        ),
                        game_external_id=game_id,
                        market_type=market_type,
                        line_millipoints=_millipoints(point),
                        selection=selection,
                        american_odds=int(odds),
                        observed_at=observed_at,
                        source=source,
                    )
                )
        return cls(cls.name, games, quotes, scores)


class CollegeFootballDataAdapter(FixtureProviderAdapter):
    """Fixture-backed mapping boundary for CollegeFootballData games and lines."""

    name = "college-football-data"

    @classmethod
    def from_payload(
        cls, games_payload: list[dict[str, Any]], lines_payload: list[dict[str, Any]]
    ) -> "CollegeFootballDataAdapter":
        games = [
            ExternalGame(
                str(game["id"]),
                game["home_team"],
                game["away_team"],
                _parse_datetime(game["start_date"]),
            )
            for game in games_payload
        ]
        game_by_id = {game.external_id: game for game in games}
        quotes: list[ExternalQuote] = []
        for line in lines_payload:
            game = game_by_id.get(str(line["id"]))
            if game is None:
                continue
            source = f"{cls.name}:{line.get('provider', 'unknown').lower()}"
            observed_at = _parse_datetime(
                line.get("start_date", game.scheduled_at.isoformat())
            )
            for selection, odds, point, market_type in (
                (
                    MarketSelection.HOME,
                    line.get("home_moneyline"),
                    None,
                    MarketType.MONEYLINE,
                ),
                (
                    MarketSelection.AWAY,
                    line.get("away_moneyline"),
                    None,
                    MarketType.MONEYLINE,
                ),
                (
                    MarketSelection.HOME,
                    line.get("home_spread"),
                    line.get("spread"),
                    MarketType.SPREAD,
                ),
                (
                    MarketSelection.AWAY,
                    line.get("away_spread"),
                    -Decimal(str(line["spread"]))
                    if line.get("spread") is not None
                    else None,
                    MarketType.SPREAD,
                ),
            ):
                if odds is None:
                    continue
                quotes.append(
                    ExternalQuote(
                        f"{game.external_id}:{source}:{market_type}:{selection}",
                        game.external_id,
                        market_type,
                        _millipoints(point),
                        selection,
                        int(odds),
                        observed_at,
                        source,
                    )
                )
        return cls(cls.name, games, quotes, [])


def load_normalized_feed(path: Path, provider: str) -> FixtureProviderAdapter:
    """Load a normalized provider feed for local syncs and scheduler hooks."""
    payload = json.loads(path.read_text())
    return FixtureProviderAdapter(
        name=provider,
        game_records=[
            ExternalGame(
                external_id=record["external_id"],
                home_team=record["home_team"],
                away_team=record["away_team"],
                scheduled_at=datetime.fromisoformat(record["scheduled_at"]),
            )
            for record in payload.get("games", [])
        ],
        quote_records=[
            ExternalQuote(
                external_id=record["external_id"],
                game_external_id=record["game_external_id"],
                market_type=MarketType(record["market_type"]),
                line_millipoints=record.get("line_millipoints"),
                selection=MarketSelection(record["selection"]),
                american_odds=record["american_odds"],
                observed_at=datetime.fromisoformat(record["observed_at"]),
                source=record.get("source"),
            )
            for record in payload.get("quotes", [])
        ],
        score_records=[
            ExternalScore(
                external_id=record["external_id"],
                game_external_id=record["game_external_id"],
                home_score=record["home_score"],
                away_score=record["away_score"],
                observed_at=datetime.fromisoformat(record["observed_at"]),
            )
            for record in payload.get("scores", [])
        ],
    )
