"""Sales history screen: daily, weekly, monthly and yearly totals, each next to the same period a year earlier."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

from .fmt import pct
from .world import HISTORY_DAYS as N, World


@dataclass(frozen=True)
class Period:
    label: str
    value: float
    last_year: float
    current: bool


def periods(w: World, kind: str) -> List[Period]:
    today, last = w.today_date, N - 1
    out: List[Period] = []
    if kind == "daily":
        for k in range(29, -1, -1):
            i = last - k
            d = w.date_at(i)
            out.append(Period(f"{d.day}/{d.month}", w.history[i], w.history[i - 364], k == 0))
    elif kind == "weekly":
        for k in range(25, -1, -1):
            end = last - k * 7
            s = end - 6
            out.append(Period(w.date_at(s).strftime("%d %b"), w.sum_range(s, end), w.sum_range(s - 364, end - 364), k == 0))
    elif kind == "monthly":
        def idx(d: date) -> int:
            return N - 1 - (today - d).days

        def first_of(year: int, month: int) -> date:
            year, month = year + (month - 1) // 12, (month - 1) % 12 + 1
            return date(year, month, 1)
        for k in range(11, -1, -1):
            m = first_of(today.year, today.month - k)
            nm = first_of(m.year, m.month + 1)
            s, e_ = idx(m), min(last, idx(nm) - 1)
            rs = idx(date(m.year - 1, m.month, 1))
            ref = w.sum_range(rs, rs + (e_ - s)) if s - 365 >= 0 else 0.0
            out.append(Period(m.strftime("%b") + (" " + str(m.year)[2:] if m.month == 1 else ""), w.sum_range(s, e_), ref, k == 0))
    elif kind == "yearly":
        for k in range(2, -1, -1):
            end = last - k * 365
            s = end - 364
            label = "Last 12 months" if k == 0 else "12 months before" if k == 1 else "12 before that"
            out.append(Period(label, w.sum_range(s, end), w.sum_range(s - 365, end - 365), k == 0))
    else:
        raise ValueError("kind must be daily, weekly, monthly or yearly")
    return out


def month_to_date(w: World) -> dict:
    """This month so far, against the same days last month, and the last 12 months against the 12 before."""
    last, d = N - 1, w.today_date.day
    prev_month_days = (w.today_date.replace(day=1) - timedelta(days=1)).day
    mtd = w.sum_range(last - d + 1, last)
    ps = last - d - prev_month_days + 1
    pm = w.sum_range(ps, ps + d - 1)
    l12, p12 = w.sum_range(last - 364, last), w.sum_range(last - 729, last - 365)
    return {"month_to_date": mtd, "same_days_last_month": pm, "mtd_change_pct": pct(mtd, pm),
            "last_12_months": l12, "previous_12_months": p12, "l12_change_pct": pct(l12, p12)}
