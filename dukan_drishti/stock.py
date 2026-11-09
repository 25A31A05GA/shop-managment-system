"""Stock and reorder: expected daily sales x (delivery days + days to cover) - stock on hand.
Stock on hand is sample data here; in a real shop it comes from bills, deliveries, returns and counts."""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean

from .forecast import lift_table
from .rng import rng
from .world import Product, World


@dataclass
class StockRow:
    product: Product
    daily: float
    on_hand: int
    lead: int
    days_left: float
    need: int
    status: str  # good / watch / check
    label: str


def festival_uplift(w: World, enabled: bool = True) -> float:
    d = w.days_to("Diwali")
    if not enabled or d is None or d > 21:
        return 1.0
    L = lift_table(w)
    return mean(L.lift(o) for o in range(-6, 1))


def reorder_plan(w: World, cover: int = 7, uplift: bool = True) -> list[StockRow]:
    upl, rnd, rows = festival_uplift(w, uplift), rng(77 + w.S["count"]), []
    for p in w.products:
        daily = p.units / 30
        eff = daily * upl
        lead = 3 + math.floor(rnd() * 4)
        on_hand = 1 if p.id == 0 else max(0, math.floor(daily * (rnd() * 14 - 1) + 0.5))
        left = on_hand / eff if eff > 0 else 99
        need = max(0, math.ceil(eff * (lead + cover) - on_hand))
        if on_hand == 0:
            st = ("check", "Out of stock")
        elif left < lead:
            st = ("check", "Order now")
        elif left < lead + 3:
            st = ("watch", "Order soon")
        elif left > 60:
            st = ("watch", "Too much stock")
        else:
            st = ("good", "Enough")
        rows.append(StockRow(p, eff, on_hand, lead, left, need, st[0], st[1]))
    return sorted(rows, key=lambda r: r.days_left)
