"""Compare your shelf price with the next market (sample market prices). Suggest a small rise where you are clearly cheaper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .fmt import inr, js_round, pct
from .rng import rng
from .world import Product, World


@dataclass(frozen=True)
class PriceRow:
    product: Product
    market_price: int
    diff_pct: float
    level: str
    suggestion: str
    extra_profit_per_month: float


def rows(w: World) -> List[PriceRow]:
    r = rng(17 * 131 + w.S["count"])
    out = []
    for p in w.products:
        c = js_round(p.price * (.93 + r() * .14))
        d = pct(p.price, c)
        lv, a, gain = "good", "Price is fine", 0.0
        if d >= 4:
            lv, a = "check", f"Market is cheaper by {inr(p.price - c)}"
        elif d <= -3 and p.margin > .08:
            lv, a, gain = "watch", f"Room to raise to {inr(c - 1)}", p.units * (c - 1 - p.price)
        out.append(PriceRow(p, c, d, lv, a, gain))
    out.sort(key=lambda x: -x.extra_profit_per_month)
    return out
