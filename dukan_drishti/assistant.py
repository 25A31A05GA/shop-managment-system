"""'Ask the assistant': answers only from the records, and always says how it worked the answer out."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .fmt import inr, num
from .forecast import make_forecast
from .insights import (brand_reasons, brand_verdict, compare_sources, demand_leaders, offer_report, peers_of, supplier_report)
from .stock import reorder_plan
from .world import HISTORY_DAYS as N, World, pct

QUESTIONS = ["What are today's total sales?", "Which brand is in most demand?", "Which brand sells least?",
             "Which rice source sells more, and why?", "Which Diwali offer worked best?", "Which products should I reorder?",
             "Which supplier has the most short deliveries?", "Compare this month with last month",
             "What will sales be in the next 14 days?"]


@dataclass
class Answer:
    text: str
    how: str


_inr = inr


def ask(w: World, q: str) -> Answer:
    s = q.lower()
    has = lambda pat: re.search(pat, s) is not None
    if has(r"today|total sales|how much money"):
        return Answer(f"Today's sales are {_inr(w.today_sales)} from {num(sum(b.bills for b in w.branches))} bills "
                      f"({pct(w.today_sales, w.yesterday_sales):+.1f}% vs yesterday).", "Added up every bill made today across all branches.")
    if has(r"least|lowest|slow|worst|weak") and has(r"brand|product|sell"):
        low = demand_leaders(w, 1)[1]
        if not low:
            return Answer("No product stands out as slow compared with its own group.", "Compared each product's share with an equal split inside its group.")
        x = low[0]
        return Answer(f"{x.name} is the slowest compared with others in its group: {num(x.units)} {x.unit} in 30 days, "
                      f"{x.g:+.0f}% vs the month before. Possible reason: {brand_reasons(x, peers_of(w, x))[0]}",
                      "Compared each product's unit and money share with an equal split inside its own group.")
    if has(r"most|best|top|demand|popular") and has(r"brand|product|sell|demand") and not has(r"offer|rice|source"):
        top = sorted(w.products, key=lambda p: -p.rev)[:3]
        return Answer("Top sellers by money received: " + ", ".join(f"{p.name} ({_inr(p.rev)})" for p in top) + ".",
                      "Ranked all products by money received over the last 30 days.")
    if has(r"rice|source|state|dal"):
        v = compare_sources(w, 0)
        return Answer(f"{v.winner} sells {(v.ratio - 1) * 100:.0f}% more than {v.loser}. Verdict: {v.label}. {v.advice}",
                      "Compared the two sources on price, stock-outs, offers, shelf position, returns, complaints and quality score.")
    if has(r"offer|diwali|festival"):
        best = [r for r in offer_report(w) if r.offer["fest"] == "Diwali"]
        b = best[0]
        return Answer(f"The Diwali offer that earned the most extra profit was {b.offer['name']} ({_inr(b.profit_change)}).",
                      "Compared each offer's extra sales against the discount it gave away.")
    if has(r"reorder|order|stock|buy"):
        rows = [r for r in reorder_plan(w) if r.status == "check"]
        return Answer(f"{len(rows)} products should be ordered now, most urgent: " + ", ".join(r.product.name for r in rows[:3]) + ".",
                      "Expected daily sales x (delivery days + days to cover) - stock on hand.")
    if has(r"supplier|short|delivery"):
        r = supplier_report(w)[0]
        return Answer(f"{r['n']} has the most short deliveries: {r['short']}% of items, about {_inr(r['shortVal'])}. "
                      "A short delivery is a reason to check the slip, not proof of anything dishonest.",
                      "Ranked suppliers by the share of items delivered short over the last 90 days.")
    if has(r"month|compare"):
        a, b = w.sum_range(N - 30, N - 1), w.sum_range(N - 60, N - 31)
        return Answer(f"The last 30 days brought {_inr(a)} against {_inr(b)} in the 30 days before ({pct(a, b):+.1f}%).",
                      "Added daily money received for each 30-day period.")
    if has(r"forecast|next|will|predict|tomorrow"):
        f = make_forecast(w)
        return Answer(f.summary(), "Recent level x weekday pattern x festival effect, with a back-test of the same method on the last 14 days.")
    return Answer("I can answer from the records only. Try: " + " / ".join(QUESTIONS[:4]), "No matching question found.")
