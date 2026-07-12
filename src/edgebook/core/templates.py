"""Jinja2 template configuration and custom filters."""

from pathlib import Path

from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from edgebook.core.money import cents_to_string

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def format_cents(value: int | str | None) -> str:
    if value is None:
        return "$0.00"
    if isinstance(value, str):
        value = int(float(value) * 100)
    return f"${cents_to_string(value)}"


def format_pct(value: float | None) -> str:
    if value is None:
        return "0.0%"
    return f"{value:.1f}%"


def format_datetime(value: str | None) -> str:
    if not value:
        return ""
    from datetime import datetime

    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value)
    return dt.strftime("%b %d, %Y %I:%M %p")


def pluralize(value: int) -> str:
    return "s" if value != 1 else ""


def status_label(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("_", " ").title()


templates.env.filters["format_cents"] = format_cents
templates.env.filters["format_pct"] = format_pct
templates.env.filters["format_datetime"] = format_datetime
templates.env.filters["pluralize"] = pluralize
templates.env.filters["status_label"] = status_label


def get_templates(request: Request) -> Jinja2Templates:
    return templates
