"""Honest self-checks: forecast back-test over many dates, and typo-search accuracy.
Both use the synthetic world, so read them as 'works as designed', not 'works on real shops'."""
from __future__ import annotations

import random
import time
from datetime import date, timedelta
from statistics import mean, median

from .forecast import backtest_mape, weekday_index
from .search import search
from .world import World


def forecast_bench(sizes=("kirana", "super", "chain"), n_dates: int = 40, start: date = date(2026, 1, 1)) -> dict:
    out, rows = {}, []
    for size in sizes:
        mapes = []
        for k in range(n_dates):
            w = World(size, start + timedelta(days=k * 9))
            mapes.append(backtest_mape(w, weekday_index(w)))
        out[size] = {"median": median(mapes), "mean": mean(mapes), "worst": max(mapes), "share_under_8": sum(m < 8 for m in mapes) / len(mapes)}
        rows += mapes
    out["all"] = {"median": median(rows), "mean": mean(rows), "worst": max(rows), "share_under_8": sum(m < 8 for m in rows) / len(rows)}
    return out


def _typo(word: str, rnd: random.Random) -> str:
    if len(word) < 4:
        return word
    i, kind = rnd.randrange(1, len(word) - 1), rnd.choice(["drop", "swap", "sub", "double"])
    if kind == "drop":
        return word[:i] + word[i + 1:]
    if kind == "swap":
        return word[:i] + word[i + 1] + word[i] + word[i + 2:]
    if kind == "sub":
        return word[:i] + rnd.choice("abcdefghijklmnopqrstuvwxyz") + word[i + 1:]
    return word[:i] + word[i] + word[i:]


def search_bench(seed: int = 1, n: int = 400) -> dict:
    """Pick a product, mangle the first word of its brand with one typo, check a product containing the real
    word comes back in the top 1 / top 3. (v1 compared brand names and under-counted: 'Paper Boat' found for
    'boat' was scored as a miss. See docs/JOURNEY.md.)"""
    w, rnd = World("super", date(2026, 11, 8)), random.Random(seed)
    contains = lambda g, word: word in f"{g.brand} {g.name} {g.cat}".lower()
    hit1 = hit3 = clean1 = 0
    for _ in range(n):
        p = rnd.choice(w.products)
        first = [t for t in p.brand.lower().replace("-", " ").split() if t][0]
        got = search(w, _typo(first, rnd), 3)
        hit1 += bool(got) and contains(got[0], first)
        hit3 += any(contains(g, first) for g in got)
        clean = search(w, first, 1)
        clean1 += bool(clean) and contains(clean[0], first)
    return {"queries": n, "top1": hit1 / n, "top3": hit3 / n, "clean_top1": clean1 / n, **_prefix_bench(w, seed, n), "junk_returning_results": _junk(w)}


def _prefix_bench(w: World, seed: int, n: int) -> dict:
    """Half-typed brand names, half of them with one slip ('horlix'): measured with and without the prefix-typo rule."""
    rnd, contains = random.Random(seed + 1), lambda g, word: word in f"{g.brand} {g.name} {g.cat}".lower()
    cases = []
    for _ in range(n):
        p = rnd.choice(w.products)
        first = [t for t in p.brand.lower().replace("-", " ").split() if t][0]
        if len(first) >= 7:
            cut = first[: rnd.randint(6, len(first) - 1)]
            cases.append((first, _typo(cut, rnd) if rnd.random() < .5 else cut))
    on = sum(any(contains(g, f) for g in search(w, q, 3, prefix_typos=True)) for f, q in cases) / len(cases)
    off = sum(any(contains(g, f) for g in search(w, q, 3, prefix_typos=False)) for f, q in cases) / len(cases)
    return {"prefix_typo_cases": len(cases), "prefix_typo_top3_with_rule": on, "prefix_typo_top3_without_rule": off}


def _junk(w: World, n: int = 400, seed: int = 3) -> float:
    """Random letters should find nothing. Share that wrongly returned something (lower is better)."""
    r = random.Random(seed)
    return sum(bool(search(w, "".join(r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(r.choice([5, 6, 7]))), 1)) for _ in range(n)) / n


def speed_bench() -> dict:
    t = time.perf_counter()
    w = World("chain", date(2026, 11, 8))
    build = time.perf_counter() - t
    t = time.perf_counter()
    for q in ("horlix", "sona masuri", "fortun oil", "parle", "tata tea"):
        for _ in range(200):
            search(w, q)
    return {"chain_world_build_s": build, "searches_per_s": 1000 / (time.perf_counter() - t), "products": len(w.products)}
