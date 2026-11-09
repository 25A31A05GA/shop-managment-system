"""Small REST API (standard library only). Browsers get a styled page, programs get JSON.

GET /api/health | summary | branches | forecast | stock | brands | sources | offers | suppliers | khata | expiry
GET /api/search?q=horlix      GET /api/ask?q=which brand sells least      GET /api/brief
Optional ?size=kirana|super|chain on every call."""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__
from .assistant import ask
from .brief import morning_brief
from .data import SIZES, SOURCES
from .forecast import make_forecast
from .insights import brand_reasons, brand_verdict, compare_sources, demand_leaders, offer_report, peers_of, supplier_report
from .ledger import expiry_risk, khata, khata_ageing
from . import cash, finance, history, pricewatch
from .access import ROLES, can_see
from .search import search
from .stock import reorder_plan
from .world import World, pct


@lru_cache(maxsize=8)
def _world(size: str, day: str) -> World:
    return World(size, date.fromisoformat(day))


def world_for(size: str) -> World:
    return _world(size if size in SIZES else "super", date.today().isoformat())


def _plain(o):
    if is_dataclass(o) and not isinstance(o, type):
        return {k: _plain(v) for k, v in asdict(o).items() if not k.startswith("_")}
    if isinstance(o, dict):
        return {k: _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if isinstance(o, date):
        return o.isoformat()
    return o


def _prod(p):
    return {"id": p.id, "name": p.name, "category": p.cat, "unit": p.unit, "price": p.price, "unitsLast30Days": round(p.units),
            "moneyReceived": round(p.rev), "growthPct": p.g}


def handle(path: str, q: dict[str, str]):
    """Return (status, payload). Pure function so it is easy to test without a socket."""
    w = world_for(q.get("size", "super"))
    if path in ("/", "/api"):
        return 200, {"name": "Dukan Drishti API", "status": "running", "version": __version__, "endpoints": [
            "/api/health", "/api/summary", "/api/branches", "/api/forecast", "/api/stock?cover=7", "/api/brands", "/api/sources?i=0",
            "/api/offers", "/api/suppliers", "/api/khata", "/api/expiry", "/api/profit", "/api/cash", "/api/price", "/api/history?kind=weekly", "/api/roles", "/api/search?q=horlix", "/api/ask?q=...", "/api/brief"]}
    if path == "/api/health":
        return 200, {"status": "ok", "version": __version__, "size": w.size, "products": len(w.products)}
    if path == "/api/summary":
        return 200, {"size": w.size, "salesToday": round(w.today_sales), "salesYesterday": round(w.yesterday_sales),
                     "changePct": round(pct(w.today_sales, w.yesterday_sales), 2), "bills": sum(b.bills for b in w.branches),
                     "branches": len(w.branches), "needCheck": sum(b.status() == "check" for b in w.branches),
                     "dataIs": "synthetic sample data"}
    if path == "/api/branches":
        return 200, [{"id": b.id, "name": b.name, "region": b.region, "today": round(b.today), "changePct": round(pct(b.today, b.yest), 1),
                      "cashGap": b.cash_gap, "lowStock": b.low_stock, "status": b.status()} for b in w.branches]
    if path == "/api/forecast":
        f = make_forecast(w)
        return 200, {"summary": f.summary(), "total": round(f.total), "low": round(f.low), "high": round(f.high), "backtestMapePct": round(f.mape, 2),
                     "reliable": f.reliable, "days": [{"date": d.isoformat(), "expected": round(v)} for d, v in zip(f.days, f.values)]}
    if path == "/api/stock":
        cover = int(q.get("cover", "7"))
        return 200, [{"product": r.product.name, "status": r.label, "onHand": r.on_hand, "sellsPerDay": round(r.daily, 1), "daysLeft": round(r.days_left, 1),
                      "deliveryDays": r.lead, "orderQty": r.need, "unit": r.product.unit} for r in reorder_plan(w, cover, q.get("uplift", "1") != "0")]
    if path == "/api/brands":
        top, low = demand_leaders(w)
        return 200, {"inDemand": [{**_prod(p), "why": brand_reasons(p, peers_of(w, p))} for p in top],
                     "slow": [{**_prod(p), "why": brand_reasons(p, peers_of(w, p))} for p in low]}
    if path == "/api/sources":
        i = int(q.get("i", "0"))
        if not 0 <= i < len(SOURCES):
            return 400, {"error": f"i must be 0 to {len(SOURCES) - 1}"}
        return 200, {"product": SOURCES[i]["prod"], **_plain(compare_sources(w, i))}
    if path == "/api/offers":
        return 200, [{"offer": r.offer["name"], "type": r.offer["type"], "extraUnits": round(r.extra_units), "extraRevenue": round(r.extra_revenue),
                      "discountCost": round(r.discount_cost), "profitChange": round(r.profit_change)} for r in offer_report(w)]
    if path == "/api/suppliers":
        return 200, supplier_report(w)
    if path == "/api/khata":
        rows = khata(w)
        return 200, {"customers": _plain(rows), "ageing": khata_ageing(rows)}
    if path == "/api/expiry":
        return 200, _plain(expiry_risk(w)[:15])
    if path == "/api/search":
        return 200, [_prod(p) for p in search(w, q.get("q", ""), 10)]
    if path == "/api/ask":
        if not q.get("q", "").strip():
            return 400, {"error": "add ?q=your question"}
        return 200, _plain(ask(w, q["q"]))
    if path == "/api/profit":
        return 200, _plain(finance.profit(w))
    if path == "/api/cash":
        return 200, _plain(cash.rows(w))
    if path == "/api/price":
        return 200, [{"product": r.product.name, "yourPrice": r.product.price, "marketPrice": r.market_price, "diffPct": round(r.diff_pct, 1),
                      "level": r.level, "suggestion": r.suggestion, "extraProfitPerMonth": round(r.extra_profit_per_month)} for r in pricewatch.rows(w)[:20]]
    if path == "/api/history":
        kind = q.get("kind", "weekly")
        if kind not in ("daily", "weekly", "monthly", "yearly"):
            return 400, {"error": "kind must be daily, weekly, monthly or yearly"}
        return 200, {"kind": kind, "periods": _plain(history.periods(w, kind)), "summary": history.month_to_date(w)}
    if path == "/api/roles":
        return 200, [{"id": r.id, "title": r.title, "description": r.description, "everything": r.everything, "tabs": list(r.tabs)} for r in ROLES.values()]
    if path == "/api/brief":
        return 200, {"brief": morning_brief(w)}
    return 404, {"error": "not found"}


_CSS = ("<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#11151c;"
        "color:#eef1f6;font:16px/1.6 'Noto Sans',system-ui,sans-serif;padding:20px}.c{max-width:760px;width:100%;border:1px solid #333d4c;border-radius:14px;"
        "background:#1a2029;padding:28px}h1{margin:6px 0}h1 span{color:#ff8a2b}p{color:#a9b2c0}.ok{display:inline-block;width:9px;height:9px;border-radius:50%;"
        "background:#7ee2a1;margin-right:8px}table{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}td{border-top:1px solid #333d4c;padding:8px 6px}"
        "td:first-child{font-family:ui-monospace,Menlo,monospace;color:#ff8a2b;white-space:nowrap}a{color:#ff8a2b}</style>")

_DOC = [("/api/summary", "Today's sales, bills, branches needing a check"), ("/api/branches", "Every branch with a traffic-light status"),
        ("/api/forecast", "14-day forecast with a back-tested range"), ("/api/stock?cover=7", "What to reorder and how much"),
        ("/api/brands", "Brands in demand and slow sellers, with reasons"), ("/api/sources?i=0", "Fair test of two supply sources"),
        ("/api/offers", "Did each festival offer earn more than it cost?"), ("/api/suppliers", "Supplier reliability"),
        ("/api/khata", "Credit owed and ageing"), ("/api/profit", "What the owner really keeps, break-even per day"), ("/api/cash", "Cash drawer and cashier checks"), ("/api/price", "Your prices against the market"), ("/api/history?kind=weekly", "Sales history, each period next to a year earlier"), ("/api/roles", "Who may see what"), ("/api/expiry", "Stock about to expire"), ("/api/search?q=horlix", "Typo-tolerant product search"),
        ("/api/ask?q=which brand sells least", "Ask in plain English"), ("/api/brief", "The owner's morning brief")]


def _html(code: int, body: str) -> bytes:
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Dukan Drishti API</title>{_CSS}</head><body><div class='c'>{body}</div></body></html>").encode()


_HOME = ("<h1><span class='ok'></span>Dukan <span>Drishti</span> API is running</h1><p>Owner's control room for Indian retail. All data is synthetic.</p><table>"
         + "".join(f"<tr><td><a href='{a}'>{a}</a></td><td>{b}</td></tr>" for a, b in _DOC) + "</table>")
_404 = "<h1>Nothing here, <span>but the API is up</span></h1><p>Try the <a href='/'>endpoint list</a> or <a href='/api/health'>/api/health</a>.</p>"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            code, payload = handle(u.path.rstrip("/") or "/", q)
        except Exception as e:  # never leak a stack trace to a caller
            code, payload = 500, {"error": str(e)}
        wants_html = "text/html" in self.headers.get("Accept", "")
        if wants_html and u.path in ("/", "/api"):
            body, ctype = _html(200, _HOME), "text/html; charset=utf-8"
        elif wants_html and code == 404 and not u.path.startswith("/api/"):
            body, ctype = _html(404, _404), "text/html; charset=utf-8"
        else:
            body, ctype = json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # quiet by default
        pass


def make_server(port: int = 8080, host: str = "0.0.0.0") -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)
