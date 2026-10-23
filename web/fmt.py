"""Number formats for pages and charts. Each refuses NaN and infinity rather than print them."""

import math


def _finite(value) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"refusing to format a non-finite number: {value}")
    return value


def _signed(value: float, body: str) -> str:
    return f"-{body}" if value < 0 and body.strip("$0.,%") else body


def money(value) -> str:
    """$1,234 with no cents."""
    value = _finite(value)
    return _signed(value, f"${abs(value):,.0f}")


def money_cents(value) -> str:
    """$1,234.56"""
    value = _finite(value)
    return _signed(value, f"${abs(value):,.2f}")


def signed_money(value) -> str:
    """+$1,234 or -$1,234, for amounts that add to or take from a total."""
    text = money(value)
    return text if text.startswith("-") or text == "$0" else f"+{text}"


def money_short(value) -> str:
    """$950, $12K, $1.2M: for axis ticks."""
    value = _finite(value)
    size = abs(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if size >= limit:
            body = f"{size / limit:.1f}".removesuffix(".0")
            return _signed(value, f"${body}{suffix}")
    return _signed(value, f"${size:,.0f}")


def percent(fraction, digits: int = 2) -> str:
    """0.0525 -> 5.25%, trimming trailing zeros."""
    value = _finite(fraction) * 100
    body = f"{abs(value):.{digits}f}".rstrip("0").rstrip(".") if digits else f"{abs(value):.0f}"
    return _signed(value, f"{body}%")


def rate(value, digits: int = 2) -> str:
    """A rate FRED already gives in percent: 6.3 -> 6.30%."""
    value = _finite(value)
    return _signed(value, f"{abs(value):.{digits}f}%")


def number(value, digits: int = 1) -> str:
    value = _finite(value)
    return _signed(value, f"{abs(value):,.{digits}f}")
