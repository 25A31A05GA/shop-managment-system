"""Seeded random numbers (mulberry32). Same algorithm as the dashboard, so Python and the
browser produce the same sample data for the same seed."""
M = 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    return (a * b) & M


def rng(seed: int):
    a = seed & M

    def nxt() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & M
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & M) ^ t
        return ((t ^ (t >> 14)) & M) / 4294967296

    return nxt
