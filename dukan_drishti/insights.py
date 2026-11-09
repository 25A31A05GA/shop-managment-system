"""Brand demand, regional-source fairness test, offer profit and supplier reliability.
Every verdict says WHY and says what it is NOT (a signal, not proof)."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .data import OFFERS, SOURCES, SUPPLIERS
from .world import Product, World, pct


def peers_of(w: World, p: Product) -> list[Product]:
    return [x for x in w.products if x.cat == p.cat]


def brand_verdict(p: Product, peers: list[Product]) -> tuple[str, str]:
    share = (p.units / sum(x.units for x in peers) + p.rev / sum(x.rev for x in peers)) / 2
    even = 1 / len(peers)
    if len(peers) > 1 and share >= even * 1.3:
        return "good", "Very high demand"
    if len(peers) > 1 and share <= even * 0.55:
        return "check", "Slow seller"
    return "watch", "Steady"


def brand_reasons(p: Product, peers: list[Product]) -> list[str]:
    avg_p, r, gap = mean(x.price for x in peers), [], pct(p.price, mean(x.price for x in peers))
    if len(peers) > 1 and gap <= -5:
        r.append(f"Priced {abs(gap):.0f}% below the average of its group, which may help sales.")
    if len(peers) > 1 and gap >= 5:
        r.append(f"Priced {gap:.0f}% above the average of its group, so fewer shoppers may choose it.")
    if p.stockout >= 3:
        r.append(f"Was out of stock on {p.stockout} of the last 30 days. Some sales were probably lost, not refused.")
    if p.offer >= 5:
        r.append(f"Had an offer on {p.offer} days. Offers lift sales for a while, so check offers before trusting the number.")
    if p.g >= 8:
        r.append(f"Sales are rising ({p.g:+.0f}% against the previous 30 days).")
    if p.g <= -8:
        r.append(f"Sales are falling ({p.g:+.0f}% against the previous 30 days).")
    if p.margin >= 0.15:
        r.append(f"Good earning per sale ({p.margin * 100:.0f}% margin), so it is worth keeping in stock.")
    if p.margin <= 0.07:
        r.append(f"Thin margin ({p.margin * 100:.0f}%). Selling more of it earns little.")
    return r or ["No unusual price, stock or offer effect found in the sample records."]


def demand_leaders(w: World, n: int = 3) -> tuple[list[Product], list[Product]]:
    top = sorted((p for p in w.products if brand_verdict(p, peers_of(w, p))[0] == "good"), key=lambda p: -p.rev)[:n]
    low = sorted((p for p in w.products if brand_verdict(p, peers_of(w, p))[0] == "check"), key=lambda p: p.rev)[:n]
    return top, low


# ---- regional source: does one source sell more because customers prefer it, or for other reasons? ---------
@dataclass
class SourceVerdict:
    ratio: float
    confounders: list[str]
    quality_signals: list[str]
    level: str
    label: str
    advice: str
    winner: str
    loser: str


def _source_rows(w: World, s: dict) -> list[dict]:
    weekly = w.products[s["pid"]].units / 30 * 7
    return [{**x, "units": weekly * x["share"], "margin": (x["price"] - x["cost"]) / x["price"]} for x in s["src"]]


def source_verdict(a: dict, b: dict) -> SourceVerdict:
    ratio, conf, qual = a["units"] / b["units"], [], []
    if pct(a["price"], b["price"]) <= -4:
        conf.append(f"cheaper by {abs(pct(a['price'], b['price'])):.0f}%")
    if b["stockout"] - a["stockout"] >= 3:
        conf.append(f"the other was out of stock {b['stockout'] - a['stockout']} more days")
    if a["offer"] - b["offer"] >= 5:
        conf.append(f"on offer {a['offer'] - b['offer']} more days")
    if a["front"] and not b["front"]:
        conf.append("kept on the front shelf")
    if a["q"] - b["q"] >= 0.3:
        qual.append(f"better quality check score ({a['q']} vs {b['q']})")
    if b["ret"] - a["ret"] >= 0.5:
        qual.append(f"fewer returns ({a['ret']}% vs {b['ret']}%)")
    if b["comp"] - a["comp"] >= 2:
        qual.append(f"fewer customer complaints ({a['comp']} vs {b['comp']})")
    if ratio < 1.15:
        v = ("watch", "No clear difference", "Both sources sell at a similar pace. Keep buying from both and keep recording.")
    elif len(qual) >= 2 and len(conf) <= 1:
        v = ("good", "Customers seem to prefer it", "It sells more AND has better quality signals, and price, stock or shelf do not explain the gap. This is fairly strong evidence.")
    elif len(conf) >= 2 and len(qual) <= 1:
        v = ("check", "Sold more mostly for other reasons", "The gap is largely explained by price, availability, offers or shelf position. This is NOT proof that it is better quality.")
    else:
        v = ("watch", "Mixed evidence", "Some signals point each way. Run a fair test before changing your supplier.")
    return SourceVerdict(ratio, conf, qual, v[0], v[1], v[2], a["st"], b["st"])


def compare_sources(w: World, index: int = 0) -> SourceVerdict:
    rows = _source_rows(w, SOURCES[index])
    a, b = (rows[0], rows[1]) if rows[0]["units"] >= rows[1]["units"] else (rows[1], rows[0])
    return source_verdict(a, b)


# ---- offers: did the discount earn more than it cost? ----------------------------------------------------
@dataclass
class OfferResult:
    offer: dict
    product: Product
    extra_units: float
    extra_revenue: float
    discount_cost: float
    profit_change: float


def evaluate_offer(w: World, o: dict) -> OfferResult:
    p = w.products[o["pid"]]
    base = p.units / 30
    normal_units, offer_units = base * o["len"], base * o["lift"] * o["len"]
    if o.get("free"):
        disc, revenue = offer_units / 2 * p.cost, offer_units * p.price * .5
        offer_profit = offer_units * (.5 * p.price) - offer_units * p.cost
    else:
        disc = offer_units * p.price * o["pct"] / 100 if o.get("pct") else offer_units * o.get("flat", 0)
        revenue = offer_units * p.price - disc
        offer_profit = revenue - offer_units * p.cost
    normal_profit = normal_units * (p.price - p.cost)
    return OfferResult(o, p, offer_units - normal_units, revenue - normal_units * p.price, disc, offer_profit - normal_profit)


def offer_report(w: World) -> list[OfferResult]:
    return sorted((evaluate_offer(w, o) for o in OFFERS), key=lambda r: -r.profit_change)


# ---- suppliers ----------------------------------------------------------------------------------------------
def supplier_report(w: World) -> list[dict]:
    k, rows = max(1, w.S["count"] / 12), []
    for s in SUPPLIERS:
        if s["short"] >= 15 or s["onTime"] < 75:
            st = ("check", "Please review")
        elif s["short"] >= 6 or s["onTime"] < 90:
            st = ("watch", "Keep an eye")
        else:
            st = ("good", "Reliable")
        rows.append({**s, "orders": round(s["orders"] * k), "shortVal": s["shortVal"] * k, "owed": s["owed"] * k, "level": st[0], "label": st[1]})
    return sorted(rows, key=lambda r: -r["short"])
