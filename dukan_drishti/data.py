"""Constants for the synthetic sample world (mirrors the dashboard's sample settings)."""
TOWNS = ["Guntur", "Hyderabad", "Vijayawada", "Warangal", "Nellore", "Tirupati", "Kurnool", "Rajahmundry", "Karimnagar",
         "Khammam", "Visakhapatnam", "Nizamabad", "Anantapur", "Kakinada", "Eluru", "Ongole", "Mahbubnagar", "Adilabad",
         "Chittoor", "Kadapa", "Nalgonda", "Machilipatnam", "Srikakulam", "Vizianagaram", "Secunderabad"]

SIZES = {
    "kirana": {"count": 1, "regions": ["Home town"], "lo": 7000, "hi": 13000, "name": "Your kirana shop"},
    "super": {"count": 12, "regions": ["Coastal", "Telangana", "Rayalaseema"], "lo": 90000, "hi": 280000, "name": "Sample Supermarkets"},
    "chain": {"count": 100, "regions": ["Coastal", "Telangana", "Rayalaseema", "North Andhra", "Karnataka border", "Tamil border"],
              "lo": 45000, "hi": 210000, "name": "Sample Retail Chain"},
}

# Festival dates move every year, so they are settings. peak = extra demand on the biggest day.
FESTIVALS = [
    {"name": "Diwali", "peak": 0.75, "dates": ["2024-11-01", "2025-10-20", "2026-11-08"]},
    {"name": "Sankranti", "peak": 0.40, "dates": ["2024-01-14", "2025-01-14", "2026-01-14", "2027-01-14"]},
    {"name": "Ugadi", "peak": 0.30, "dates": ["2024-04-09", "2025-03-30", "2026-03-19"]},
    {"name": "Christmas", "peak": 0.15, "dates": ["2024-12-25", "2025-12-25", "2026-12-25"]},
]

# category, brand, name, revenue weight, price, cost, 30-day growth %, stock-out days (of 30), offer days (of 30), unit
# The full 231-product sample catalog lives in catalog.json (exported from the dashboard so both agree exactly).
import json as _json
from pathlib import Path as _Path

PRODUCT_DEFS = [tuple(r) for r in _json.loads((_Path(__file__).with_name("catalog.json")).read_text(encoding="utf-8"))]

SUPPLIERS = [
    {"n": "Sri Venkateswara Traders", "prod": "Rice, pulses", "orders": 22, "onTime": 96, "short": 3, "shortVal": 4200, "ret": 0.6, "owed": 182000},
    {"n": "Annapurna Agro Foods", "prod": "Rice (Telangana)", "orders": 18, "onTime": 78, "short": 17, "shortVal": 38500, "ret": 1.4, "owed": 96000},
    {"n": "Kaveri Distributors", "prod": "Health drinks, tea", "orders": 26, "onTime": 92, "short": 8, "shortVal": 15800, "ret": 0.4, "owed": 241000},
    {"n": "Deccan Oils", "prod": "Cooking oil", "orders": 14, "onTime": 85, "short": 6, "shortVal": 9100, "ret": 0.9, "owed": 64000},
    {"n": "Latur Pulses Mart", "prod": "Toor dal", "orders": 12, "onTime": 71, "short": 22, "shortVal": 41200, "ret": 2.4, "owed": 58000},
    {"n": "Metro Biscuits & Snacks", "prod": "Biscuits", "orders": 20, "onTime": 97, "short": 2, "shortVal": 1200, "ret": 0.2, "owed": 37000},
]

# Two competing sources for the same product. front = front-shelf placement, q = quality score /5.
SOURCES = [
    {"prod": "Sona Masoori rice (loose)", "pid": 4, "src": [
        {"st": "Andhra Pradesh", "dist": "Guntur", "share": .62, "price": 56, "cost": 49, "stockout": 0, "offer": 4, "front": True, "ret": .8, "comp": 3, "q": 4.4, "regions": [.5, .22, .28]},
        {"st": "Telangana", "dist": "Nalgonda", "share": .38, "price": 59, "cost": 51, "stockout": 5, "offer": 0, "front": False, "ret": 1.1, "comp": 4, "q": 4.3, "regions": [.34, .4, .26]}]},
    {"prod": "Toor dal (loose)", "pid": 7, "src": [
        {"st": "Karnataka", "dist": "Kalaburagi", "share": .58, "price": 154, "cost": 129, "stockout": 1, "offer": 0, "front": True, "ret": .6, "comp": 2, "q": 4.5, "regions": [.3, .45, .25]},
        {"st": "Maharashtra", "dist": "Latur", "share": .42, "price": 150, "cost": 127, "stockout": 1, "offer": 0, "front": True, "ret": 2.1, "comp": 7, "q": 3.9, "regions": [.34, .33, .33]}]},
    {"prod": "Basmati rice (loose)", "pid": 5, "src": [
        {"st": "Punjab", "dist": "Amritsar", "share": .55, "price": 118, "cost": 99, "stockout": 0, "offer": 0, "front": True, "ret": .5, "comp": 1, "q": 4.7, "regions": [.4, .35, .25]},
        {"st": "Haryana", "dist": "Karnal", "share": .45, "price": 112, "cost": 95, "stockout": 2, "offer": 0, "front": True, "ret": .7, "comp": 2, "q": 4.5, "regions": [.36, .34, .3]}]},
    {"prod": "Chana dal (loose)", "pid": 8, "src": [
        {"st": "Madhya Pradesh", "dist": "Vidisha", "share": .52, "price": 92, "cost": 80, "stockout": 2, "offer": 6, "front": True, "ret": 1.2, "comp": 3, "q": 4.1, "regions": [.33, .34, .33]},
        {"st": "Rajasthan", "dist": "Bikaner", "share": .48, "price": 92, "cost": 79, "stockout": 2, "offer": 6, "front": True, "ret": 1.3, "comp": 3, "q": 4.1, "regions": [.33, .33, .34]}]},
]

OFFERS = [
    {"id": "D25-1", "name": "Diwali 2025 · Horlicks buy 1 get 1 free", "fest": "Diwali", "year": 2025, "type": "Buy 1 get 1 free", "pid": 0, "len": 7, "lift": 2.6, "free": True, "fast": 62},
    {"id": "D25-2", "name": "Diwali 2025 · Oil 10% off", "fest": "Diwali", "year": 2025, "type": "10% off", "pid": 10, "len": 10, "lift": 1.5, "pct": 10, "fast": 28},
    {"id": "D25-3", "name": "Diwali 2025 · Sona Masoori rice ₹2 off per kg", "fest": "Diwali", "year": 2025, "type": "₹2 off", "pid": 4, "len": 8, "lift": 1.9, "flat": 2, "fast": 41},
    {"id": "D25-4", "name": "Diwali 2025 · Tea ₹5 off", "fest": "Diwali", "year": 2025, "type": "₹5 off", "pid": 14, "len": 7, "lift": 1.25, "flat": 5, "fast": 18},
    {"id": "D24-1", "name": "Diwali 2024 · Good Day biscuits ₹2 off", "fest": "Diwali", "year": 2024, "type": "₹2 off", "pid": 17, "len": 6, "lift": 1.9, "flat": 2, "fast": 55},
    {"id": "D24-2", "name": "Diwali 2024 · Boost 5% off", "fest": "Diwali", "year": 2024, "type": "5% off", "pid": 1, "len": 7, "lift": 1.9, "pct": 5, "fast": 35},
    {"id": "S26-1", "name": "Sankranti 2026 · Rice 8% off", "fest": "Sankranti", "year": 2026, "type": "8% off", "pid": 4, "len": 6, "lift": 1.55, "pct": 8, "fast": 33},
    {"id": "U26-1", "name": "Ugadi 2026 · Chana dal ₹2 off", "fest": "Ugadi", "year": 2026, "type": "₹2 off", "pid": 8, "len": 5, "lift": 1.4, "flat": 2, "fast": 25},
]
