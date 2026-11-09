"""Cash and cashier checks. A flag means 'look at the records', never proof that someone did something wrong."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .fmt import inr, js_round
from .rng import rng
from .world import World

CASHIERS = ("Anil", "Divya", "Mahesh", "Swathi", "Prasad", "Rekha", "Kishore", "Lavanya")


@dataclass(frozen=True)
class CashRow:
    branch: str
    counter: int
    cashier: str
    bills_say: int
    counted: int
    difference: int
    cancelled_bills: int
    discount_pct: float
    level: str
    result: str
    may_mean: str


def cash_level(diff: int) -> str:
    """A cash difference of 120 or more is worth a recount; 300 or more needs a look."""
    return "check" if abs(diff) >= 300 else "watch" if abs(diff) >= 120 else "good"


def cashier_level(diff: int, cancelled: int, discount_pct: float) -> str:
    """Cashier flag from cash difference, cancelled bills and discount given."""
    if abs(diff) >= 300 or cancelled >= 6 or discount_pct >= 4.5:
        return "check"
    if abs(diff) >= 120 or cancelled >= 4 or discount_pct >= 3.5:
        return "watch"
    return "good"


def result_for(d: int) -> Tuple[str, str, str]:
    """d = counted cash minus what the bills say, in rupees."""
    if d <= -120:
        return "check", f"Short {inr(-d)}", "Customer may have got too much change, or a bill was cancelled after cash was taken."
    if d >= 120:
        return "watch", f"Extra {inr(d)}", "Change may not have been given back, or a cash payment was recorded as UPI."
    return "good", "Matches", "Nothing to do."


def rows(w: World) -> List[CashRow]:
    r = rng(3 + w.S["count"] * 7)
    one = w.S["count"] == 1
    bs = sorted(w.branches, key=lambda b: b.cash_gap)[:6]
    out: List[CashRow] = []
    for i, b in enumerate(bs):
        for c in ((1,) if one else (1, 2)):
            sh = 1.0 if one else (.6 if c == 1 else .4)
            exp = js_round(b.today * .35 * sh / 10) * 10
            d = js_round(b.cash_gap * sh / 10) * 10
            vo = js_round(r() * r() * 10)
            dc = js_round(r() * 6 * 10) / 10.0
            lv, res, mean = result_for(d)
            out.append(CashRow(b.name, c, CASHIERS[(i * 2 + c) % 8], exp, exp + d, d, vo, dc, lv, res, mean))
    out.sort(key=lambda x: x.difference)
    return out
