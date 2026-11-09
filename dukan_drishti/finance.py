"""What the owner really keeps: sales minus goods, wastage and running costs, plus the daily break-even line."""
from __future__ import annotations

from dataclasses import dataclass

from .fmt import js_round
from .world import HISTORY_DAYS as N, World


@dataclass(frozen=True)
class Costs:
    rent: float
    salaries: float
    electricity: float
    other: float

    @property
    def total(self) -> float:
        return self.rent + self.salaries + self.electricity + self.other


@dataclass(frozen=True)
class Profit:
    sales30: float
    gross_profit: float
    wastage: float
    running_costs: float
    net: float
    break_even_per_day: float
    sales_today: float
    above_break_even: bool
    gst_to_keep_aside: float
    margin_pct: float


def default_costs(sales30: float) -> Costs:
    """Default monthly costs as a share of 30-day sales, rounded to the nearest thousand (sample settings)."""
    r = lambda share: js_round(sales30 * share / 1000) * 1000.0  # noqa: E731
    return Costs(r(.03), r(.065), r(.012), r(.01))


def profit(w: World, costs: Costs | None = None) -> Profit:
    m = w.sum_range(N - 30, N - 1)
    costs = costs or default_costs(m)
    g = w.gross_margin
    gross, waste, fixed = m * g, m * .009, costs.total
    net = gross - waste - fixed
    be = (fixed + waste) / g / 30
    today = w.today_sales
    return Profit(m, gross, waste, fixed + waste, net, be, today, today >= be, m * .045, g * 100)
