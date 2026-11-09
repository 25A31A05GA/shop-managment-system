"""The owner's morning brief: one short text a busy shopkeeper can read (or send to WhatsApp) in 30 seconds."""
from __future__ import annotations

from .fmt import inr, num
from .forecast import make_forecast
from .ledger import khata, khata_ageing
from .stock import reorder_plan
from .world import World, pct


def morning_brief(w: World) -> str:
    chg = pct(w.today_sales, w.yesterday_sales)
    check = [b for b in w.branches if b.status() == "check"]
    watch = [b for b in w.branches if b.status() == "watch"]
    rows = [r for r in reorder_plan(w) if r.status == "check"]
    ks = khata(w)
    late = sum(c.owed for c in ks if c.days_late > 30)
    f = make_forecast(w)
    d = w.days_to("Diwali")
    out = [f"{w.S['name']} · {w.today_date:%A, %d %B %Y}", "",
           f"Sales today: {inr(w.today_sales)} ({chg:+.1f}% vs yesterday)",
           f"Bills: {num(sum(b.bills for b in w.branches))}"]
    if len(w.branches) > 1:
        out.append(f"Branches: {len(check)} need a check, {len(watch)} to keep an eye on, {len(w.branches) - len(check) - len(watch)} going well")
        out += [f"  - {b.name}: sales {pct(b.today, b.yest):+.0f}%, cash gap {inr(b.cash_gap)}" for b in check]
    out.append(f"Reorder now: {len(rows)} products" + (" (most urgent: " + ", ".join(r.product.name for r in rows[:3]) + ")" if rows else ""))
    out.append(f"Customers late over 30 days owe {inr(late)}")
    out.append(f.summary())
    if d is not None and d <= 21:
        when = "is today" if d == 0 else f"in {d} day{'s' if d != 1 else ''}"
        out.append(f"Festival: Diwali {when}. Stock plan includes the festival uplift.")
    out += ["", "A score or verdict is a lead to check, not proof of anything."]
    return "\n".join(out)
