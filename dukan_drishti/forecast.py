"""14-day sales forecast: recent level x weekday pattern x festival effect learned from your own past festivals,
with an honest back-test (MAPE) and a likely range. Shows 'not enough data' rather than a made-up number."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean

from .data import FESTIVALS
from .fmt import inr
from .world import HISTORY_DAYS as N, World, _round


def weekday_index(w: World) -> list[float]:
    xs: list[list[float]] = [[] for _ in range(7)]
    for i in range(N - 120, N - 30):
        xs[w.dow(i)].append(w.history[i])
    m = [mean(x) for x in xs]
    allm = mean(m)
    return [v / allm for v in m]


@dataclass
class LiftTable:
    w: World
    wd: list[float]
    prev: list[int]

    @property
    def prev_count(self) -> int:
        return len(self.prev)

    def n2(self, i: int) -> float:
        return self.w.history[i] / self.wd[self.w.dow(i)]

    def lift(self, offset: int) -> float:
        """Average demand multiplier `offset` days from Diwali, learned from earlier Diwalis."""
        def one(f: int) -> float:
            i = f + offset
            return self.n2(i) / mean(self.n2(i - 42 + k) for k in range(28))
        return mean(one(f) for f in self.prev)


def lift_table(w: World, wd: list[float] | None = None) -> LiftTable:
    wd = wd or weekday_index(w)
    def idx_of(k: str) -> int:
        return N - 1 - _round((w.today_date - date.fromisoformat(k)).days)
    prev = [i for i in map(idx_of, FESTIVALS[0]["dates"]) if i - 42 >= 0 and i + 3 < N - 1 and i < N - 14]
    return LiftTable(w, wd, prev)


@dataclass
class Forecast:
    days: list[date]
    values: list[float]
    total: float
    low: float
    high: float
    last14: float
    mape: float
    band: float
    festival_in_days: int | None
    reliable: bool
    enough_history: bool

    def summary(self) -> str:
        if not self.enough_history:
            return "Not enough history yet: at least 8 weeks of sales are needed before a forecast is shown."
        change = (self.total - self.last14) / self.last14 * 100
        s = (f"Next 14 days: about {inr(self.total)} expected (likely {inr(self.low)} to {inr(self.high)}), "
             f"{change:+.1f}% vs the last 14 days. Back-test miss: {self.mape:.1f}% ({'fairly reliable' if self.reliable else 'rough guide'}).")
        if self.festival_in_days is not None and 1 <= self.festival_in_days <= 14:
            s += f" Part of the rise comes from Diwali in {self.festival_in_days} days."
        elif self.festival_in_days == 0:
            s += " Diwali is today, so sales are expected to stay high for the next few days."
        return s


def forecast_day(w: World, offset: int, L: LiftTable, wd: list[float], level: float) -> float:
    dt = w.today_date + timedelta(days=offset)
    lift = 1.0
    cutoff = w.today_date + timedelta(days=offset - 3)
    nxt = next((d for d in map(date.fromisoformat, FESTIVALS[0]["dates"]) if d >= cutoff), None)
    if nxt is not None:
        o = (dt - nxt).days
        if -10 <= o <= 3 and L.prev_count > 0:
            lift = L.lift(o)
    return level * wd[(dt.weekday() + 1) % 7] * lift * math.pow(1.16, offset / 365)


def backtest_mape(w: World, wd: list[float]) -> float:
    """Predict the last 14 days using only what was known 14 days earlier."""
    n2 = lambda i: w.history[i] / wd[w.dow(i)]
    lvl0 = mean(n2(N - 14 - 42 + k) for k in range(28))
    errs = []
    for k in range(14):
        i = N - 14 + k
        f = lvl0 * wd[w.dow(i)] * math.pow(1.16, (k + 14) / 365)
        errs.append(abs(w.history[i] - f) / w.history[i])
    return mean(errs) * 100


def make_forecast(w: World) -> Forecast:
    wd, enough = weekday_index(w), N >= 8 * 7
    L = lift_table(w, wd)
    level = mean(w.history[N - 42 + k] / wd[w.dow(N - 42 + k)] for k in range(28))
    vals = [forecast_day(w, k + 1, L, wd, level) for k in range(14)]
    mape = backtest_mape(w, wd)
    band = max(mape * 1.5, 5) / 100
    tot = sum(vals)
    return Forecast([w.today_date + timedelta(days=k + 1) for k in range(14)], vals, tot, tot * (1 - band), tot * (1 + band),
                    w.sum_range(N - 14, N - 1), mape, band, w.days_to("Diwali"), mape < 8, enough)
