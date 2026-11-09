"""Command line:  python -m dukan_drishti <command>
  brief | forecast | stock | brands | offers | suppliers | khata | search "horlix" | ask "..." | bench | serve --port 8080
Add --size kirana|super|chain."""
from __future__ import annotations

import argparse
import json
import os

from . import api, bench
from .assistant import ask
from .brief import morning_brief
from .forecast import make_forecast
from .insights import demand_leaders, offer_report, supplier_report, brand_reasons, peers_of
from .ledger import khata
from .search import search
from .stock import reorder_plan
from .world import World
from .fmt import inr
from . import cash, finance, history, pricewatch
from .access import ROLES


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dukan_drishti", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["brief", "forecast", "stock", "brands", "offers", "suppliers", "khata", "search", "ask", "profit", "cash", "price", "history", "roles", "bench", "serve"])
    ap.add_argument("text", nargs="*", help="query for search / ask")
    ap.add_argument("--size", default="super", choices=["kirana", "super", "chain"])
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8080)))
    a = ap.parse_args(argv)
    if a.command == "bench":
        print(json.dumps({"forecast_backtest_mape_pct": bench.forecast_bench(), "typo_search": bench.search_bench(), "speed": bench.speed_bench()}, indent=2))
        return 0
    if a.command == "serve":
        srv = api.make_server(a.port)
        print(f"Dukan Drishti API on http://localhost:{a.port}  (Ctrl+C to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    w = World(a.size)
    q = " ".join(a.text)
    if a.command == "brief":
        print(morning_brief(w))
    elif a.command == "forecast":
        print(make_forecast(w).summary())
    elif a.command == "stock":
        for r in reorder_plan(w)[:15]:
            print(f"{r.label:<15} {r.product.name:<32} on hand {r.on_hand:>5}  sells/day {r.daily:>7.1f}  order {r.need:>6} {r.product.unit}")
    elif a.command == "brands":
        top, low = demand_leaders(w)
        for title, ps in (("IN DEMAND", top), ("SLOW SELLERS", low)):
            print(title)
            for p in ps:
                print(f"  {p.name}: {p.units:,.0f} {p.unit}/30d. " + brand_reasons(p, peers_of(w, p))[0])
    elif a.command == "offers":
        for r in offer_report(w):
            print(f"{r.offer['name']:<52} profit change Rs {r.profit_change:>10,.0f}")
    elif a.command == "suppliers":
        for r in supplier_report(w):
            print(f"{r['label']:<13} {r['n']:<28} on time {r['onTime']}%  short {r['short']}%")
    elif a.command == "khata":
        for c in khata(w):
            print(f"{c.name:<20} Rs {c.owed:>7,}  {c.days_late:>3} days  {c.whatsapp_link()[:60]}...")
    elif a.command == "profit":
        p = finance.profit(w)
        print(f"Last 30 days received {inr(p.sales30)}. You really keep about {inr(p.net)}.\nBreak-even sales per day: {inr(p.break_even_per_day)} "
              f"({'today is above it' if p.above_break_even else 'today is BELOW it'}). GST to keep aside (estimate): {inr(p.gst_to_keep_aside)}.")
    elif a.command == "cash":
        for r in cash.rows(w):
            print(f"{r.level:<6} {r.branch:<14} counter {r.counter} {r.cashier:<9} {r.result:<14} cancelled {r.cancelled_bills}  discount {r.discount_pct}%")
    elif a.command == "price":
        for r in pricewatch.rows(w)[:12]:
            print(f"{r.product.name:<32} yours {inr(r.product.price):>7} market {inr(r.market_price):>7}  {r.suggestion}")
    elif a.command == "history":
        for kind in ("weekly", "monthly"):
            print(kind.upper())
            for x in history.periods(w, kind)[-6:]:
                print(f"  {x.label:<10} {inr(x.value):>16}  last year {inr(x.last_year):>16}")
    elif a.command == "roles":
        for r in ROLES.values():
            print(f"{r.title:<28} {r.description}")
    elif a.command == "search":
        for p in search(w, q):
            print(f"{p.name}  ({p.cat}, Rs {p.price})")
    elif a.command == "ask":
        r = ask(w, q)
        print(r.text + "\n  How: " + r.how)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
