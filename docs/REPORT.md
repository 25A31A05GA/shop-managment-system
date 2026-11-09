# Dukan Drishti: Project Report

## 1. The problem
A shop owner with one kirana, a dozen supermarkets or a hundred chain stores cannot watch every bill. Numbers arrive late, in a form that needs an expert, and without a reason. The owner needs short answers: *what is going wrong today, what should I order, did my offer work, whose drawer is short.*

## 2. The approach
- **Plain language first.** Each verdict (Good, Watch, Check) carries its reason and says what it is *not*.
- **Honest numbers.** The forecast is back-tested on the last 14 days and shows its own miss. With under 8 weeks of history it shows nothing.
- **Same logic everywhere.** The dashboard (browser) and the engine (Python) share one random-number generator and one rule set, so tests compare them directly.

## 3. How it is built
`world` builds 3+ years of daily sales (level x growth x weekday x month x festival ramp x noise). `forecast`, `stock`, `insights`, `ledger`, `cash`, `finance`, `pricewatch`, `history` and `access` are rule modules. `assistant`, `search`, `brief` make it easy to ask. `api` serves everything as JSON, with styled pages for browsers. Standard library only.

## 4. Results (synthetic data; reproduce with `python -m dukan_drishti bench`)

**Forecast back-test** (predict the last 14 days using only what was known 14 days earlier, 60 dates)

| Size | Median miss | Share of dates under 8% |
|---|---|---|
| Single kirana | 12.3% | 0% |
| 12 supermarkets | 6.2% | 80% outside festival fortnights, 53% inside |
| 100-store chain | 6.0% | 80% outside, 53% inside |

**Typo search** (400 queries): right product in top 3: **95.3%**; top 1: 86.5%; exact word: 97.5%; random letters wrongly returning something: 1.25%. Half-typed words with a slip ("horlix"): 78.3% with the new rule, 75.8% without.

**Matching the dashboard:** sales, 231 products, weekday pattern, forecast, back-test, offer profit, brand and source verdicts, and the full reorder plan match to 12 decimals. Text-parity tests compare profit, cash, price, credit, expiry, history and supplier screens with what the dashboard itself prints.

**Tests:** 80, all passing, about 10 seconds, no dependencies.

## 5. Attempts and failures
Eight logged problems, each with the cause and the fix, are in [JOURNEY.md](JOURNEY.md). The two that mattered most: the dashboard secretly has 231 products, not 18; and my first search fix lowered accuracy until I re-ran the benchmark.

## 6. Cases
Seven worked cases in [case-studies/](case-studies/README.md), including a Diwali stock-out, an offer that lost money, a supplier fairness test and a drawer that is short.

## 7. Limitations
- Synthetic data; never tested on a real shop.
- The forecast learns festival effects from only a few past years and ignores one-off events.
- A single kirana's forecast is rough by nature.
- No database, login or sending yet.
- Search is typo-tolerant, not meaning-aware ("sugar" will not find "chini").

## 8. What I would do next
Real CSV import, SQLite, Telugu and Hindi questions, scheduled WhatsApp brief, a measured test on a real shop with the owner's permission.

## 9. Responsible use
These are leads for a human to check. A short drawer is not theft, a short delivery is not dishonesty, and a slow brand is not a bad brand. Always say why.
