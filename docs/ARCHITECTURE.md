# Architecture

```
            ┌──────────────┐    seeded sample data (same random numbers as the dashboard)
            │   world.py   │──► branches · 3+ years of daily sales · 231 products
            └──────┬───────┘
   ┌───────────────┼──────────────────────────────────────────────┐
   ▼               ▼                ▼               ▼             ▼
forecast.py     stock.py       insights.py      ledger.py     cash / finance /
(14-day +       (reorder)      (brands, sources, (khata,       pricewatch / history
 back-test)                     offers, suppliers) expiry)     / access
   └───────────────┴────────┬───────┴───────────────┴─────────────┘
                            ▼
              assistant.py · search.py · brief.py
                            ▼
              api.py (REST)  ·  __main__.py (CLI)  ·  docs/dashboard.html
```

## Rules of the design
1. **One random-number generator** (`rng.py`, mulberry32) shared with the dashboard, so Python and the browser agree.
2. **Every verdict has a reason** and a sentence on what it does not prove.
3. **JavaScript rounding** (`Math.round`) is reproduced, because Python's `round()` rounds halves to even and would drift from the dashboard.
4. **No dependencies.** The API uses `http.server`; tests use `unittest`.
5. **Parity tests** compare against numbers produced by the dashboard itself (`tests/fixtures/`).
