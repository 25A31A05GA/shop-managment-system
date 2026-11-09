"""Zero-dependency tests:  python -m unittest discover -s tests -v
The 'parity' tests compare Python against numbers computed by the dashboard's own JavaScript
(tests/fixtures/dashboard_parity.json), so the two implementations cannot drift apart unnoticed."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from dukan_drishti import World, api, bench, cash, finance, history, pricewatch
from dukan_drishti.access import ROLES, blocked_answer, can_approve, can_see, get_role
from dukan_drishti.fmt import group, inr, num, sgn
from dukan_drishti.assistant import QUESTIONS, ask
from dukan_drishti.brief import morning_brief
from dukan_drishti.data import SOURCES
from dukan_drishti.forecast import make_forecast, weekday_index
from dukan_drishti.insights import (brand_verdict, compare_sources, evaluate_offer, offer_report, peers_of, source_verdict, supplier_report)
from dukan_drishti.ledger import Credit, expiry_risk, khata, khata_ageing
from dukan_drishti.rng import rng
from dukan_drishti.search import levenshtein, search, skeleton
from dukan_drishti.stock import reorder_plan
from dukan_drishti.world import Branch, Product, _round, pct

FIX = json.loads((Path(__file__).parent / "fixtures" / "dashboard_parity.json").read_text(encoding="utf-8"))
STOCK_FIX = json.loads((Path(__file__).parent / "fixtures" / "dashboard_stock_rows.json").read_text(encoding="utf-8"))
D = date(2026, 11, 8)
W = World("super", D)


def rel(a, b):
    return abs(a - b) / abs(b)


def product(**kw):
    base = dict(id=0, cat="X", brand="B", name="B 1", price=100, cost=90, g=0, stockout=0, offer=0, unit="kg", units=300, prev_units=300, rev=30000, margin=.1, profit=3000)
    base.update(kw)
    return Product(**base)


class Parity(unittest.TestCase):
    def test_sales_today_and_yesterday(self):
        self.assertAlmostEqual(W.today_sales, FIX["today"], places=6)
        self.assertAlmostEqual(W.yesterday_sales, FIX["yest"], places=6)

    def test_bills(self):
        self.assertEqual(sum(b.bills for b in W.branches), FIX["bills"])

    def test_branch_status_cash_and_low_stock(self):
        self.assertEqual([b.status() for b in W.branches], FIX["status"])
        self.assertEqual([b.cash_gap for b in W.branches], FIX["cash"])
        self.assertEqual([b.low_stock for b in W.branches], FIX["lowStock"])

    def test_history(self):
        self.assertEqual(len(W.history), 3 * 365 + 40)
        for a, b in zip(W.history[:5], FIX["hist_first"]):
            self.assertLess(rel(a, b), 1e-12)
        for a, b in zip(W.history[-5:], FIX["hist_last"]):
            self.assertLess(rel(a, b), 1e-12)

    def test_product_catalog(self):
        self.assertEqual(len(W.products), FIX["n_products"])
        self.assertLess(max(rel(p.units, u) for p, u in zip(W.products, FIX["units"])), 1e-12)
        self.assertLess(max(rel(p.rev, u) for p, u in zip(W.products, FIX["rev"])), 1e-12)

    def test_weekday_pattern(self):
        for a, b in zip(weekday_index(W), FIX["wd"]):
            self.assertAlmostEqual(a, b, places=12)

    def test_forecast_and_backtest(self):
        f = make_forecast(W)
        self.assertLess(max(rel(a, b) for a, b in zip(f.values, FIX["fc"])), 1e-12)
        self.assertAlmostEqual(f.mape, FIX["mape"], places=9)

    def test_offer_profit(self):
        got = {r.offer["id"]: r for r in offer_report(W)}
        for o in FIX["offers"]:
            self.assertLess(rel(got[o["id"]].profit_change, o["profitChange"]), 1e-9)
            self.assertLess(rel(got[o["id"]].discount_cost, o["discountCost"]), 1e-9)

    def test_brand_verdicts_for_all_products(self):
        self.assertEqual([brand_verdict(p, peers_of(W, p))[0] for p in W.products], FIX["brand_verdicts"])

    def test_source_verdicts(self):
        for i, s in enumerate(FIX["source_verdicts"]):
            v = compare_sources(W, i)
            self.assertEqual(v.label, s["verdict"])
            self.assertAlmostEqual(v.ratio, s["ratio"], places=9)

    def test_reorder_plan_rows_match_dashboard(self):
        rows = reorder_plan(W)
        self.assertEqual(sum(r.status == "check" for r in rows), 154)
        for r, d in zip(rows[:40], STOCK_FIX[:40]):
            self.assertEqual(r.product.name, d[0])
            self.assertEqual(r.label, d[1])
            self.assertEqual(f"{r.need:,}", d[5].split()[0].replace("—", "0") if r.need else "0")


class Basics(unittest.TestCase):
    def test_rng_is_deterministic_and_in_range(self):
        a, b = rng(42), rng(42)
        xs = [a() for _ in range(1000)]
        self.assertEqual(xs, [b() for _ in range(1000)])
        self.assertTrue(all(0 <= x < 1 for x in xs))

    def test_rng_different_seeds_differ(self):
        self.assertNotEqual(rng(1)(), rng(2)())

    def test_js_style_rounding(self):
        self.assertEqual(_round(2.5), 3)
        self.assertEqual(_round(-0.5), 0)  # Python's round(-0.5) is -0 and round(2.5) is 2: this keeps JavaScript behaviour

    def test_same_date_same_world(self):
        self.assertEqual(World("kirana", D).history[:10], World("kirana", D).history[:10])

    def test_bad_size_rejected(self):
        with self.assertRaises(ValueError):
            World("mall", D)

    def test_sizes(self):
        self.assertEqual([len(World(s, D).branches) for s in ("kirana", "super", "chain")], [1, 12, 100])

    def test_status_thresholds(self):
        mk = lambda today, yest, cash=0, low=0: Branch(1, "t", "r", [], today, yest, 10, .1, cash, low, 1)
        self.assertEqual(mk(100, 100).status(), "good")
        self.assertEqual(mk(88, 100).status(), "watch")      # -12% drop
        self.assertEqual(mk(77, 100).status(), "check")      # -23% drop
        self.assertEqual(mk(100, 100, cash=-300).status(), "check")
        self.assertEqual(mk(100, 100, cash=150).status(), "watch")
        self.assertEqual(mk(100, 100, low=9).status(), "watch")

    def test_pct_zero_base_is_safe(self):
        self.assertEqual(pct(5, 0), 0.0)

    def test_days_to_festival(self):
        self.assertEqual(W.days_to("Diwali"), 0)
        self.assertEqual(World("super", date(2026, 11, 1)).days_to("Diwali"), 7)


class Forecast(unittest.TestCase):
    def test_range_and_reliability(self):
        f = make_forecast(W)
        self.assertEqual(len(f.values), 14)
        self.assertLess(f.low, f.total)
        self.assertGreater(f.high, f.total)
        self.assertTrue(f.reliable)  # 4.9% back-test miss
        self.assertGreaterEqual(f.band, 0.05)

    def test_summary_mentions_diwali_today(self):
        self.assertIn("Diwali is today", make_forecast(W).summary())

    def test_festival_raises_the_forecast(self):
        before = make_forecast(World("super", date(2026, 10, 30)))
        quiet = make_forecast(World("super", date(2026, 6, 1)))
        self.assertGreater((before.total - before.last14) / before.last14, (quiet.total - quiet.last14) / quiet.last14)

    def test_backtest_is_worse_in_festival_fortnights_known_limitation(self):
        """Documented in docs/case-studies/05: the back-test ignores festivals, so it reads 'rough guide' when one falls inside it."""
        from dukan_drishti.forecast import backtest_mape
        w_fest, w_quiet = World("super", date(2026, 11, 20)), World("super", date(2026, 7, 10))
        self.assertGreater(backtest_mape(w_fest, weekday_index(w_fest)), backtest_mape(w_quiet, weekday_index(w_quiet)))


class Stock(unittest.TestCase):
    def test_need_formula(self):
        for r in reorder_plan(W, cover=7)[:50]:
            self.assertEqual(r.need, max(0, __import__("math").ceil(r.daily * (r.lead + 7) - r.on_hand)))

    def test_longer_cover_orders_more(self):
        a, b = {r.product.id: r.need for r in reorder_plan(W, 3)}, {r.product.id: r.need for r in reorder_plan(W, 14)}
        self.assertTrue(all(b[k] >= a[k] for k in a))

    def test_festival_uplift_off_lowers_daily_sales(self):
        on = {r.product.id: r.daily for r in reorder_plan(W, 7, True)}
        off = {r.product.id: r.daily for r in reorder_plan(W, 7, False)}
        self.assertTrue(all(on[k] > off[k] for k in on))

    def test_out_of_stock_is_flagged(self):
        self.assertTrue(all(r.status == "check" for r in reorder_plan(W) if r.on_hand == 0))

    def test_sorted_most_urgent_first(self):
        left = [r.days_left for r in reorder_plan(W)]
        self.assertEqual(left, sorted(left))


class Insights(unittest.TestCase):
    def test_brand_verdict_high_and_slow(self):
        peers = [product(units=900, rev=90000), product(units=100, rev=10000), product(units=500, rev=50000)]
        self.assertEqual(brand_verdict(peers[0], peers)[0], "good")
        self.assertEqual(brand_verdict(peers[1], peers)[0], "check")
        self.assertEqual(brand_verdict(peers[2], peers)[0], "watch")

    def test_single_product_group_is_never_flagged(self):
        p = product()
        self.assertEqual(brand_verdict(p, [p])[0], "watch")

    def _src(self, **kw):
        base = dict(st="S", dist="d", units=100, price=100, cost=80, stockout=0, offer=0, front=False, ret=1, comp=3, q=4.0)
        base.update(kw)
        return base

    def test_similar_sources_are_no_clear_difference(self):
        self.assertEqual(source_verdict(self._src(units=105), self._src()).label, "No clear difference")

    def test_better_quality_wins_trust(self):
        a = self._src(units=150, q=4.6, ret=.3, comp=1)
        self.assertEqual(source_verdict(a, self._src()).level, "good")

    def test_cheaper_and_better_shelf_is_not_proof_of_quality(self):
        a = self._src(units=150, price=90, front=True)
        v = source_verdict(a, self._src())
        self.assertEqual(v.level, "check")
        self.assertIn("NOT proof", v.advice)

    def test_offer_math_percent_flat_and_bogo(self):
        w = World("super", D)
        pct10 = evaluate_offer(w, {"pid": 10, "len": 10, "lift": 1.5, "pct": 10})
        flat = evaluate_offer(w, {"pid": 4, "len": 8, "lift": 1.9, "flat": 2})
        bogo = evaluate_offer(w, {"pid": 0, "len": 7, "lift": 2.6, "free": True})
        p = w.products[10]
        self.assertAlmostEqual(pct10.discount_cost, p.units / 30 * 1.5 * 10 * p.price * .10)
        self.assertGreater(flat.extra_units, 0)
        self.assertAlmostEqual(bogo.discount_cost, w.products[0].units / 30 * 2.6 * 7 / 2 * w.products[0].cost)

    def test_a_fast_selling_offer_can_still_lose_money(self):
        """The Horlicks 1+1 sold 62% in two days, yet the free goods cost more than the extra sales earned."""
        bogo = next(r for r in offer_report(W) if r.offer["id"] == "D25-1")
        self.assertGreater(bogo.extra_units, 0)
        self.assertLess(bogo.profit_change, 0)

    def test_supplier_levels(self):
        by = {r["n"]: r for r in supplier_report(W)}
        self.assertEqual(by["Latur Pulses Mart"]["level"], "check")
        self.assertEqual(by["Metro Biscuits & Snacks"]["level"], "good")
        self.assertEqual(supplier_report(W)[0]["n"], "Latur Pulses Mart")  # most short deliveries first

    def test_supplier_values_scale_with_business_size(self):
        small, big = supplier_report(World("kirana", D)), supplier_report(World("chain", D))
        self.assertGreater(sum(r["owed"] for r in big), sum(r["owed"] for r in small))


class Ledger(unittest.TestCase):
    def test_ageing_adds_up_to_total(self):
        rows = khata(W)
        self.assertEqual(sum(khata_ageing(rows).values()), sum(c.owed for c in rows))

    def test_oldest_credit_first(self):
        d = [c.days_late for c in khata(W)]
        self.assertEqual(d, sorted(d, reverse=True))

    def test_whatsapp_link_is_encoded(self):
        link = Credit("Ramesh Babu", 1200, 40).whatsapp_link("Sri Stores")
        self.assertTrue(link.startswith("https://wa.me/?text="))
        self.assertIn("Ramesh%20Babu", link)
        self.assertNotIn(" ", link)

    def test_expiry_actions_follow_days_left(self):
        for r in expiry_risk(W):
            if r.days <= 3:
                self.assertIn("30%", r.action)
            elif r.days > 14:
                self.assertEqual(r.action, "Fine")

    def test_expiry_sorted_soonest_first(self):
        d = [r.days for r in expiry_risk(W)]
        self.assertEqual(d, sorted(d))


class Search(unittest.TestCase):
    def test_edit_distance_and_skeleton(self):
        self.assertEqual(levenshtein("horlicks", "horlix"), 3)
        self.assertEqual(skeleton("masoori"), skeleton("masuri"))

    def test_typos_find_the_product(self):
        for q, word in [("horlix", "horlicks"), ("sona masuri", "sona"), ("fortun oil", "fortune"), ("basmti", "basmati")]:
            top = search(W, q, 3)
            self.assertTrue(any(word in f"{p.brand} {p.name}".lower() for p in top), q)

    def test_regression_hyphenated_query_used_to_return_nothing(self):
        self.assertTrue(search(W, "vi-john"))

    def test_empty_and_nonsense_queries(self):
        self.assertEqual(search(W, ""), [])
        self.assertEqual(search(W, "   "), [])
        self.assertEqual(search(W, "qzxwvkj"), [])

    def test_limit(self):
        self.assertLessEqual(len(search(W, "rice", 3)), 3)

    def test_prefix_typo_rule_fixes_half_typed_words_without_adding_junk(self):
        self.assertTrue(search(W, "horlix", 3, prefix_typos=True))
        self.assertFalse(any("Horlicks" in p.name for p in search(W, "horlix", 3, prefix_typos=False)))
        self.assertLess(bench._junk(W), 0.03)

    def test_prefix_rule_never_lowers_an_existing_better_match(self):
        for q in ("sona masuri", "fortun oil", "basmti", "parle", "tata tea"):
            self.assertEqual([p.id for p in search(W, q, 5, prefix_typos=True)][:1], [p.id for p in search(W, q, 5, prefix_typos=False)][:1], q)

    def test_typo_search_benchmark_floor(self):
        r = bench.search_bench(seed=1, n=200)
        self.assertGreater(r["top3"], 0.9)
        self.assertGreater(r["clean_top1"], 0.95)


class Assistant(unittest.TestCase):
    def test_every_suggested_question_gets_a_real_answer_with_how(self):
        for q in QUESTIONS:
            a = ask(W, q)
            self.assertTrue(a.text and a.how, q)
            self.assertNotIn("No matching question", a.how, q)

    def test_unknown_question_is_honest(self):
        self.assertIn("records only", ask(W, "what is the meaning of life").text)

    def test_today_answer_uses_real_total(self):
        self.assertIn(inr(W.today_sales), ask(W, "total sales today").text)


class Brief(unittest.TestCase):
    def test_brief_has_the_essentials(self):
        b = morning_brief(W)
        for s in ("Sales today", "Reorder now", "Next 14 days", "Diwali is today", "not proof"):
            self.assertIn(s, b)

    def test_kirana_brief_has_no_branch_line(self):
        self.assertNotIn("Branches:", morning_brief(World("kirana", D)))


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = api.make_server(0, "127.0.0.1")
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def get(self, path, accept="application/json"):
        req = urllib.request.Request(self.base + path, headers={"Accept": accept})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.headers["Content-Type"], r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.headers["Content-Type"], e.read().decode()

    def test_health(self):
        code, _, body = self.get("/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["status"], "ok")

    def test_every_endpoint_returns_json(self):
        for path in ["/api/summary", "/api/branches", "/api/forecast", "/api/stock", "/api/brands", "/api/sources?i=1", "/api/offers",
                     "/api/suppliers", "/api/khata", "/api/expiry", "/api/search?q=horlix", "/api/ask?q=today", "/api/brief"]:
            code, ctype, body = self.get(path)
            self.assertEqual(code, 200, path)
            self.assertTrue(ctype.startswith("application/json"), path)
            json.loads(body)

    def test_sizes(self):
        for size, n in (("kirana", 1), ("chain", 100)):
            self.assertEqual(len(json.loads(self.get(f"/api/branches?size={size}")[2])), n)

    def test_bad_inputs(self):
        self.assertEqual(self.get("/api/sources?i=99")[0], 400)
        self.assertEqual(self.get("/api/ask")[0], 400)
        self.assertEqual(self.get("/api/nope")[0], 404)

    def test_browser_gets_styled_home_and_404(self):
        code, ctype, body = self.get("/", "text/html")
        self.assertTrue(code == 200 and ctype.startswith("text/html") and "API is running" in body)
        code, ctype, body = self.get("/nope", "text/html")
        self.assertTrue(code == 404 and "but the API is up" in body)

    def test_program_gets_json_at_root(self):
        self.assertEqual(json.loads(self.get("/")[2])["status"], "running")

    def test_search_via_api_finds_product_with_typo(self):
        names = [p["name"] for p in json.loads(self.get("/api/search?q=horlix")[2])]
        self.assertTrue(any("Horlicks" in n for n in names))


TABS = json.loads((Path(__file__).parent / "fixtures" / "dashboard_tabs.json").read_text(encoding="utf-8"))


class DashboardTextParity(unittest.TestCase):
    """Each assertion looks for a number Python computed inside the text the dashboard itself rendered for that screen."""

    def test_profit_screen(self):
        p, t = finance.profit(W), TABS["profit"]
        for v in (p.net, p.break_even_per_day, p.gst_to_keep_aside, p.gross_profit, p.running_costs, p.sales30):
            self.assertIn(inr(v), t)
        self.assertTrue(p.above_break_even and "above it" in t)

    def test_cash_screen(self):
        rows, t = cash.rows(W), TABS["staff"]
        for r in rows[:6]:
            self.assertIn(r.branch, t)
            self.assertIn(r.cashier, t)
        self.assertIn(f"Short {inr(330)}", t)
        self.assertEqual((rows[0].branch, rows[0].cashier, rows[0].difference), ("Kurnool", "Divya", -330))

    def test_price_watch_screen(self):
        rows, t = pricewatch.rows(W), TABS["price"]
        for r in rows[:5]:
            self.assertIn(r.product.name, t)
            self.assertIn(inr(r.market_price), t)
            self.assertIn(inr(r.extra_profit_per_month), t)

    def test_khata_screen(self):
        rows, t = khata(W), TABS["khata"]
        for label, v in khata_ageing(rows).items():
            self.assertIn(inr(v), t, label)
        for c in rows[:5]:
            self.assertIn(c.name, t)
            self.assertIn(inr(c.owed), t)
        self.assertIn(inr(sum(c.owed for c in rows if c.days_late > 30)), t)

    def test_expiry_screen(self):
        rows, t = expiry_risk(W), TABS["expiry"]
        for r in rows[:6]:
            self.assertIn(r.name, t)
            self.assertIn(inr(r.value), t)
        self.assertIn(inr(sum(r.value for r in rows if r.days <= 14)), t)

    def test_history_screen(self):
        m, t = history.month_to_date(W), TABS["history"]
        self.assertIn(inr(m["month_to_date"]), t)
        self.assertIn(f"{abs(m['mtd_change_pct']):.1f}%", t)
        self.assertIn(inr(m["last_12_months"]), t)

    def test_supplier_screen(self):
        t = TABS["suppliers"]
        for r in supplier_report(W):
            self.assertIn(r["n"], t)
            self.assertIn(inr(r["shortVal"]), t)


class Extras(unittest.TestCase):
    def test_indian_digit_grouping(self):
        self.assertEqual(group(1234567), "12,34,567")
        self.assertEqual(group(999), "999")
        self.assertEqual(group(100000), "1,00,000")
        self.assertEqual(inr(-1500), "-₹1,500")
        self.assertEqual(num(2443310.4), "24,43,310")
        self.assertEqual(sgn(-3.84, 1), "-3.8%")

    def test_cash_levels(self):
        self.assertEqual(cash.cash_level(-300), "check")
        self.assertEqual(cash.cash_level(150), "watch")
        self.assertEqual(cash.cash_level(40), "good")
        self.assertEqual(cash.cashier_level(0, 6, 0), "check")
        self.assertEqual(cash.cashier_level(0, 4, 0), "watch")
        self.assertEqual(cash.cashier_level(0, 0, 4.5), "check")
        self.assertEqual(cash.cashier_level(0, 0, 1), "good")

    def test_a_cash_flag_is_a_lead_not_blame(self):
        self.assertTrue(all("never" not in r.may_mean.lower() for r in cash.rows(W)))
        self.assertIn("Nothing to do", cash.result_for(10)[2])

    def test_break_even_formula(self):
        p = finance.profit(W)
        self.assertAlmostEqual(p.break_even_per_day, p.running_costs / W.gross_margin / 30, places=6)

    def test_price_suggestion_only_when_clearly_cheaper_and_margin_ok(self):
        for r in pricewatch.rows(W):
            if r.suggestion.startswith("Room"):
                self.assertTrue(r.diff_pct <= -3 and r.product.margin > .08)
            if r.level == "check":
                self.assertGreaterEqual(r.diff_pct, 4)

    def test_history_kinds_and_year_ago_values(self):
        for kind, n in (("daily", 30), ("weekly", 26), ("monthly", 12), ("yearly", 3)):
            ps = history.periods(W, kind)
            self.assertEqual(len(ps), n, kind)
            self.assertTrue(ps[-1].current and not any(p.current for p in ps[:-1]))
        with self.assertRaises(ValueError):
            history.periods(W, "hourly")

    def test_roles(self):
        self.assertEqual(len(ROLES), 7)
        self.assertTrue(can_see("chairman", "profit"))
        self.assertFalse(can_see("cashier", "profit"))
        self.assertFalse(can_see("branch", "suppliers"))   # branch managers see no supplier dues
        self.assertFalse(can_see("purchase", "khata"))      # purchase team sees no customer credit
        self.assertTrue(can_approve("chairman") and not can_approve("finance"))
        with self.assertRaises(ValueError):
            get_role("intern")

    def test_assistant_refuses_questions_about_screens_a_role_cannot_open(self):
        self.assertIsNotNone(blocked_answer("cashier", "how much profit did we make"))
        self.assertIsNotNone(blocked_answer("branch", "which supplier is late"))
        self.assertIsNone(blocked_answer("chairman", "how much profit did we make"))
        self.assertIsNone(blocked_answer("branch", "what is selling today"))

    def test_extra_api_endpoints(self):
        for path in ("/api/profit", "/api/cash", "/api/price", "/api/history", "/api/roles"):
            self.assertEqual(api.handle(path, {})[0], 200, path)
        self.assertEqual(api.handle("/api/history", {"kind": "hourly"})[0], 400)


class Bench(unittest.TestCase):
    def test_forecast_bench_shape(self):
        r = bench.forecast_bench(sizes=("super",), n_dates=5)
        self.assertIn("median", r["super"])
        self.assertGreater(r["super"]["worst"], 0)


if __name__ == "__main__":
    unittest.main()
