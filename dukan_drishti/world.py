"""Builds the synthetic world: branches, 3+ years of daily sales history, and the product table."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean

from .data import FESTIVALS, PRODUCT_DEFS, SIZES, TOWNS
from .rng import rng

HISTORY_DAYS = 3 * 365 + 40


def _round(x: float) -> int:  # JavaScript Math.round (halves go up), not Python's banker's rounding
    return math.floor(x + 0.5)


def pct(a: float, b: float) -> float:
    return (a - b) / b * 100 if b else 0.0


@dataclass
class Branch:
    id: int
    name: str
    region: str
    days: list[float]
    today: float
    yest: float
    bills: int
    margin: float
    cash_gap: int
    low_stock: int
    base: float

    def status(self) -> str:
        drop = pct(self.today, self.yest)
        if abs(self.cash_gap) >= 300 or drop <= -22:
            return "check"
        if abs(self.cash_gap) >= 120 or drop <= -10 or self.low_stock >= 9:
            return "watch"
        return "good"


@dataclass
class Product:
    id: int
    cat: str
    brand: str
    name: str
    price: float
    cost: float
    g: float
    stockout: int
    offer: int
    unit: str
    units: float
    prev_units: float
    rev: float
    margin: float
    profit: float


@dataclass
class World:
    size: str = "super"
    today_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if self.size not in SIZES:
            raise ValueError(f"size must be one of {list(SIZES)}")
        self.S = SIZES[self.size]
        self.branches = self._build_branches()
        self.trend = [sum(b.days[i] for b in self.branches) for i in range(14)]
        self.history = self._build_history()
        self.products = self._build_products()

    # -- branches (same random-number order as the dashboard) -------------------------------------
    def _build_branches(self) -> list[Branch]:
        S, r, out = self.S, rng(len(self.size) * 7919 + SIZES[self.size]["count"]), []
        for i in range(S["count"]):
            base = S["lo"] + r() * (S["hi"] - S["lo"])
            days = []
            for d in range(13, -1, -1):
                dt = self.today_date - timedelta(days=d)
                weekend = dt.weekday() in (5, 6)  # Saturday, Sunday
                days.append(base * (0.82 + r() * 0.36) * (1.15 if weekend else 1))
            today, yest = days[13], days[12]
            bills = max(8, _round(today / (140 if self.size == "kirana" else 310 + r() * 80)))
            margin = 0.11 + r() * 0.09
            if r() < 0.18:
                cash_gap = -_round(120 + r() * 480)
            elif r() < 0.08:
                cash_gap = _round(80 + r() * 150)
            else:
                cash_gap = _round((r() - .5) * 60)
            low = math.floor(r() * r() * (6 if self.size == "kirana" else 14))
            town = TOWNS[i % len(TOWNS)] + (f" {i // len(TOWNS) + 1}" if i >= len(TOWNS) else "")
            out.append(Branch(i + 1, S["name"] if self.size == "kirana" else town, S["regions"][i % len(S["regions"])],
                              days, today, yest, bills, margin, cash_gap, low, base))
        return out

    # -- 3+ years of daily sales: level x growth x weekday x month x festival ramp x noise ------------
    def date_at(self, i: int) -> date:
        return self.today_date - timedelta(days=HISTORY_DAYS - 1 - i)

    def _build_history(self) -> list[float]:
        N = HISTORY_DAYS
        r, level, out = rng(4242 + self.S["count"]), mean(self.trend), [0.0] * N
        wd = [1.13, 0.93, 0.92, 0.94, 0.97, 1.04, 1.14]  # index 0 = Sunday (JS getDay)
        mo = [1.05, .95, 1, 1, .97, .93, .94, 1, 1, 1.07, 1.1, 1.1]
        fest = [(date.fromisoformat(d), f["peak"]) for f in FESTIVALS for d in f["dates"]]
        for i in range(N):
            d, ago = self.date_at(i), N - 1 - i
            js_dow = (d.weekday() + 1) % 7
            v = level * math.pow(1.16, -ago / 365) * wd[js_dow] * mo[d.month - 1] * (0.94 + r() * 0.12)
            for fd, peak in fest:
                o = (d - fd).days
                if -10 <= o <= 3:
                    v *= 1 + peak * math.exp(-math.pow(o + 1.5, 2) / 18)
            out[i] = v
        for k in range(14):  # last two weeks equal the Today numbers
            out[N - 14 + k] = self.trend[k]
        return out

    def sum_range(self, a: int, b: int) -> float:
        return sum(self.history[max(0, a): max(0, b + 1)])

    def dow(self, i: int) -> int:  # 0 = Sunday, like JavaScript
        return (self.date_at(i).weekday() + 1) % 7

    def days_to(self, festival: str) -> int | None:
        f = next(x for x in FESTIVALS if x["name"] == festival)
        for d in sorted(date.fromisoformat(x) for x in f["dates"]):
            if d >= self.today_date:
                return (d - self.today_date).days
        return None

    def _build_products(self) -> list[Product]:
        last30 = self.sum_range(HISTORY_DAYS - 30, HISTORY_DAYS - 1)
        total_w, pool, out = sum(p[3] for p in PRODUCT_DEFS), last30 * 0.6, []
        for i, p in enumerate(PRODUCT_DEFS):
            rev = pool * p[3] / total_w
            units = rev / p[4]
            out.append(Product(i, p[0], p[1], p[2], p[4], p[5], p[6], p[7], p[8], p[9], units, units / (1 + p[6] / 100),
                               rev, (p[4] - p[5]) / p[4], units * (p[4] - p[5])))
        return out

    # -- convenient totals ----------------------------------------------------------------------------
    @property
    def today_sales(self) -> float:
        return sum(b.today for b in self.branches)

    @property
    def yesterday_sales(self) -> float:
        return sum(b.yest for b in self.branches)

    @property
    def gross_margin(self) -> float:
        """Share of each rupee of sales that is left after the cost of goods (weighted by branch sales today)."""
        return sum(b.today * b.margin for b in self.branches) / self.today_sales
