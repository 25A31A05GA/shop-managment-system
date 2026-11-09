"""Small formatting helpers: Indian digit grouping (1,23,456), signs and JavaScript-style rounding."""
import math


def js_round(x: float) -> int:
    """JavaScript Math.round: halves go up. Python's round() uses banker's rounding, which would not match the dashboard."""
    return int(math.floor(x + 0.5))


def pct(a: float, b: float) -> float:
    """Percentage change from b to a (0 when b is 0)."""
    return (a - b) / b * 100 if b != 0 else 0.0


def group(n: int) -> str:
    neg, s = n < 0, str(abs(int(n)))
    if len(s) <= 3:
        return ("-" if neg else "") + s
    last3, rest = s[-3:], s[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return ("-" if neg else "") + ",".join(parts) + "," + last3


def num(n: float) -> str:
    return group(js_round(n))


def inr(n: float) -> str:
    r = js_round(n)
    return ("-" if r < 0 else "") + "₹" + group(abs(r))


def sgn(v: float, digits: int = 0) -> str:
    s = "+" if v > 0 else "-" if v < 0 else ""
    return f"{s}{abs(v):.{digits}f}%"
