"""Khata (credit owed by customers) and expiry risk. Both are sample data here, deterministic per seed."""
from __future__ import annotations

import math
from dataclasses import dataclass
from urllib.parse import quote

from .fmt import inr
from .rng import rng
from .world import World, _round

NAMES = ["Ramesh Babu", "Lakshmi Devi", "Venkat Rao", "Sita Mahalakshmi", "Srinivas Reddy", "Padma", "Kiran Kumar",
         "Anitha", "Ravi Teja", "Suresh", "Bhavani", "Murali Krishna", "Saroja", "Naga Raju"]


@dataclass
class Credit:
    name: str
    owed: int
    days_late: int

    def reminder(self, shop: str = "our shop") -> str:
        return (f"Namaste {self.name}, your balance at {shop} is {inr(self.owed)}. "
                "Please pay when you can. Thank you.")

    def whatsapp_link(self, shop: str = "our shop") -> str:
        return "https://wa.me/?text=" + quote(self.reminder(shop))


def khata(w: World) -> list[Credit]:
    r, K = rng(9 * 131 + w.S["count"]), max(1.0, math.sqrt(w.S["count"]))
    rows = [Credit(n, _round((800 + r() * 9000) * K / 10) * 10, _round(r() * 75)) for n in NAMES]
    return sorted(rows, key=lambda c: -c.days_late)


def khata_ageing(rows: list[Credit]) -> dict[str, int]:
    buckets = {"0-15 days": (0, 15), "16-30 days": (16, 30), "31-60 days": (31, 60), "Over 60 days": (61, 10**6)}
    return {k: sum(c.owed for c in rows if lo <= c.days_late <= hi) for k, (lo, hi) in buckets.items()}


@dataclass
class ExpiryRow:
    name: str
    stock: int
    days: int
    value: float
    action: str
    level: str


def expiry_risk(w: World) -> list[ExpiryRow]:
    r, rows = rng(5 * 131 + w.S["count"]), []
    for p in w.products:
        s, d = _round(p.units / 30 * (4 + r() * 16)), _round(r() * r() * 40) + 1
        if d <= 3:
            act = ("check", "Markdown 30% today")
        elif d <= 7:
            act = ("check", "Markdown 15%, front shelf")
        elif d <= 14:
            act = ("watch", "Put in front, sell first")
        else:
            act = ("good", "Fine")
        rows.append(ExpiryRow(p.name, s, d, s * p.cost, act[1], act[0]))
    return sorted(rows, key=lambda x: x.days)
