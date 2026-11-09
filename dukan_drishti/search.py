"""Typo-tolerant product search (edit distance + a vowel-less 'skeleton' match).
Helps shopkeepers who type fast or spell brand names by sound: 'horlix', 'sona masuri', 'fortun oil'."""
from __future__ import annotations

import re
from functools import lru_cache

from .world import Product, World

_TOKEN = re.compile(r"[^a-z0-9]+")


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@lru_cache(maxsize=4096)
def skeleton(s: str) -> str:
    return re.sub(r"(.)\1+", r"\1", re.sub(r"[aeiouh]", "", s))


def _tokens(p: Product) -> list[str]:
    cached = getattr(p, "_tok", None)
    if cached is None:
        toks = [t for t in _TOKEN.split(f"{p.brand} {p.name} {p.cat}".lower()) if t]
        cached = toks + ["".join(toks)]
        object.__setattr__(p, "_tok", cached)
    return cached


def _distance(word: str, k: str, limit: int, prefix_typos: bool = True) -> float:
    if k.startswith(word) or (len(k) > 2 and word.startswith(k)):
        return 0.0
    if len(word) > 2 and word in k:
        return 0.5
    if len(word) > 3 and skeleton(word) == skeleton(k):
        return 1.0
    d = 9.0 if abs(len(word) - len(k)) > limit else float(levenshtein(word, k))  # skip the slow part when it cannot match
    if prefix_typos and len(word) >= 6 and len(k) >= len(word):
        # a typed-so-far word with one slip: 'horlix' ~ start of 'horlicks'. Not in the dashboard; added after the
        # benchmark showed such queries returned nothing (docs/JOURNEY.md). Only ever improves a worse distance.
        dp = levenshtein(word, k[:len(word)])
        if dp <= 1:
            d = min(d, dp + 0.5)
    return d


def search(w: World, query: str, limit: int = 10, prefix_typos: bool = True) -> list[Product]:
    words = [t for t in _TOKEN.split(query.lower().strip()) if t]  # 'vi-john' -> ['vi', 'john'] (was returning nothing)
    if not words:
        return []
    scored = []
    for p in w.products:
        toks, score = _tokens(p), 0.0
        for word in words:
            allowed = max(1, len(word) // 3)
            best = min(_distance(word, k, allowed, prefix_typos) for k in toks)
            if best <= allowed:
                score += 3 - best
            else:
                score = -99
                break
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], -x[1].rev))
    return [p for _, p in scored[:limit]]
