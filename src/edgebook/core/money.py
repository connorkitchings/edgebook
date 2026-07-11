"""Shared money utilities for decimal-to-cents conversion and validation."""

from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def validate_credit_amount(value: Decimal, *, allow_zero: bool = False) -> Decimal:
    """Validate a two-decimal simulation-credit amount without using floats."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Amount must be a decimal value") from error
    if not amount.is_finite():
        raise ValueError("Amount must be finite")
    if amount != amount.quantize(CENT):
        raise ValueError("Amount cannot have more than two decimal places")
    if amount < 0 or (amount == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"Amount must be {qualifier}")
    return amount


def decimal_to_cents(value: Decimal) -> int:
    """Convert a validated decimal simulation-credit amount to integer cents."""
    return int(value * 100)


def cents_to_string(value: int) -> str:
    """Render integer cents as an exact two-decimal string."""
    return f"{Decimal(value) / 100:.2f}"
