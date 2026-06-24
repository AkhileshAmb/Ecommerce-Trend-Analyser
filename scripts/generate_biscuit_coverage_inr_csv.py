"""
Generate biscuit-market test CSV (INR) for TrendScanner AI demos.

Exercises: brand share, pricing stats, comma/pipe/semicolon features,
gap signals, dedup, optional model column — same coverage as phone CSV.
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

random.seed(2026)

# brand, weight, category, (price_lo, price_hi) INR per pack
BRANDS = [
    ("Parle", 24, "Glucose", (10, 120)),
    ("Britannia", 20, "Cream", (25, 280)),
    ("Sunfeast", 16, "Marie", (20, 180)),
    ("Oreo", 14, "Cookies", (30, 350)),
    ("McVitie's", 10, "Digestive", (45, 320)),
    ("Unibic", 9, "Cookies", (35, 250)),
    ("Priyagold", 8, "Cream", (20, 150)),
    ("Patanjali", 7, "Digestive", (25, 200)),
    ("Anmol", 6, "Glucose", (15, 90)),
    ("Cremica", 5, "Wafer", (30, 220)),
    ("Karachi", 5, "Bakery", (40, 180)),
    ("Tasties", 4, "Rusks", (35, 160)),
]

BISCUIT_FEATURES = [
    "Whole Wheat,Glucose Energy,Eggless",
    "Choco Chip,Cocoa Rich,Eggless",
    "Low Sugar,High Fiber,Multigrain",
    "Marie Light,Low Fat,Tea Dip",
    "Milk Cream,Vanilla,Soft Texture",
    "Hazelnut Fill,Premium Cocoa,Crispy Wafer",
    "Oats,Digestive Fiber,No Palm Oil",
    "Butter,Cashew,Pista",
    "Honey,Milk Solids,Crunchy",
    "Jeera,Spiced,Savory Crisp",
]

CREAM_FEATURES = [
    "Milk Cream,Vanilla,Soft Texture",
    "Choco Cream,Double Cocoa,Eggless",
    "Butter,Cashew,Pista",
]

DIGESTIVE_FEATURES = [
    "Oats,Digestive Fiber,No Palm Oil",
    "Whole Wheat,Low Sugar,High Fiber",
    "Multigrain,Bran Rich,Low Fat",
]

WAFEr_FEATURES = [
    "Hazelnut Fill,Premium Cocoa,Crispy Wafer",
    "Vanilla Cream,Layered Wafer,Choco Coated",
]

GAP_RARE = [
    ("Oreo", "Protein Rich,Zero Sugar,Diabetic Friendly"),
    ("Parle", "Keto Friendly,Almond Flour,No Maida"),
    ("Britannia", "Probiotic,Digestive Enzymes,Prebiotic Fiber"),
    ("McVitie's", "Matcha Green Tea,Antioxidant Rich"),
    ("Patanjali", "Hazelnut Fill,Premium Cocoa,Crispy Wafer"),
    ("Unibic", "Whole Wheat,Glucose Energy,Eggless"),
    ("Cremica", "5 Grain,Immunity Boost,Vitamin Fortified"),
    ("Karachi", "Dark Chocolate 70%,Single Origin Cocoa"),
]

DELIMITER_SAMPLES = [
    ("Parle", "Whole Wheat|Glucose Energy|Eggless"),
    ("Britannia", "Milk Cream;Vanilla;Soft Texture"),
    ("Sunfeast", "Marie Light|Low Fat|Tea Dip"),
]

PACK_SUFFIX = ["Family Pack", "Value Pack", "Mini Pack", "Assorted", "Twin Pack"]
VARIANT = ["Classic", "Original", "Lite", "Gold", "Special", "Premium"]


def _price(lo: float, hi: float, *, premium: bool = False) -> float:
    x = random.uniform(lo, hi)
    if premium:
        x *= random.uniform(1.1, 1.4)
    # Typical Indian biscuit MRP endings (₹5 / ₹10 steps)
    x = round(x / 5) * 5
    if x < 10:
        x = 10.0
    return round(x, 2)


def _model(brand: str, category: str) -> str:
    grams = random.choice([75, 100, 137, 200, 400, 600, 800])
    return f"{brand} {category} {random.choice(VARIANT)} {grams}g {random.choice(PACK_SUFFIX)}"


def build_rows() -> list[dict]:
    rows: list[dict] = []

    feature_pool_by_cat = {
        "Glucose": BISCUIT_FEATURES,
        "Cream": CREAM_FEATURES + BISCUIT_FEATURES[:4],
        "Marie": BISCUIT_FEATURES,
        "Cookies": BISCUIT_FEATURES,
        "Digestive": DIGESTIVE_FEATURES + BISCUIT_FEATURES[:3],
        "Wafer": WAFEr_FEATURES + BISCUIT_FEATURES[:2],
        "Bakery": BISCUIT_FEATURES,
        "Rusks": BISCUIT_FEATURES[:5],
    }

    for brand, weight, category, (plo, phi) in BRANDS:
        pool = feature_pool_by_cat.get(category, BISCUIT_FEATURES)
        for _ in range(weight):
            feat = random.choice(pool)
            premium = "Premium" in feat or "Hazelnut" in feat or "Probiotic" in feat
            rows.append(
                {
                    "brand": brand,
                    "price": _price(plo, phi, premium=premium),
                    "feature": feat,
                    "category": category,
                    "model": _model(brand, category),
                }
            )

    for brand, feat in DELIMITER_SAMPLES:
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        rows.append(
            {
                "brand": brand,
                "price": _price(plo, phi),
                "feature": feat,
                "category": cat,
                "model": _model(brand, cat),
            }
        )

    POPULAR_GAP_FEATURE = "Whole Wheat,Low Sugar,High Fiber,Eggless"
    for brand in ("Oreo", "McVitie's", "Cremica", "Karachi"):
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        rows.append(
            {
                "brand": brand,
                "price": _price(plo, phi),
                "feature": POPULAR_GAP_FEATURE,
                "category": cat,
                "model": _model(brand, cat),
            }
        )

    for brand in ("Parle", "Britannia", "Sunfeast", "Priyagold", "Patanjali"):
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        for _ in range(7):
            rows.append(
                {
                    "brand": brand,
                    "price": _price(plo, phi),
                    "feature": POPULAR_GAP_FEATURE,
                    "category": cat,
                    "model": _model(brand, cat),
                }
            )

    for brand, feat in GAP_RARE:
        cat = next((c for b, _, c, _ in BRANDS if b == brand), "Cookies")
        plo, phi = next((p for b, _, _, p in BRANDS if b == brand), (25, 250))
        rows.append(
            {
                "brand": brand,
                "price": _price(phi * 0.8, phi * 1.3, premium=True),
                "feature": feat,
                "category": cat,
                "model": _model(brand, cat),
            }
        )

    outliers = [
        ("Parle", 10.0, "Glucose Energy,Classic Taste", "Glucose"),
        ("Anmol", 15.0, "Whole Wheat,Glucose Energy,Eggless", "Glucose"),
        ("Oreo", 899.0, "Gift Tin,Assorted Flavors,Premium Packaging", "Cookies"),
        ("Britannia", 650.0, "Butter,Cashew,Pista", "Cream"),
        ("McVitie's", 425.0, "Oats,Digestive Fiber,No Palm Oil", "Digestive"),
        ("Unibic", 375.0, "Choco Chip,Cocoa Rich,Eggless", "Cookies"),
    ]
    for brand, price, feat, cat in outliers:
        rows.append(
            {
                "brand": brand,
                "price": price,
                "feature": feat,
                "category": cat,
                "model": _model(brand, cat),
            }
        )

    for brand in ("Parle", "Britannia", "Sunfeast"):
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        rows.append(
            {
                "brand": brand,
                "price": _price(plo, phi),
                "feature": random.choice(BISCUIT_FEATURES),
                "category": "",
                "model": "",
            }
        )

    return rows


def main() -> None:
    import sys

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    rows = build_rows()
    dup_sources = random.sample(rows, min(10, len(rows)))
    rows.extend(dup_sources)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=2026).reset_index(drop=True)

    out = root / "test_trendscanner_biscuits_inr.csv"
    df.to_csv(out, index=False, encoding="utf-8")

    from core.ingestion import read_csv_file
    from core.validator import validate_and_clean
    from core.orchestrator import run_all_agents

    raw = read_csv_file(str(out))
    cleaned = validate_and_clean(raw, cleaning_strategy="drop_rows", remove_dupes=True)
    results = run_all_agents(
        cleaned,
        brand_column="brand",
        price_column="price",
        feature_column="feature",
        top_n_brands=12,
        top_n_features=15,
        gap_threshold=-0.5,
    )

    stats = results["agents"]["pricing"]["results"]["price_statistics"]
    gaps = results["agents"]["gap"]["results"]

    print(f"Wrote: {out}")
    print(f"  Raw rows: {len(df)} | After clean: {len(cleaned)}")
    print(f"  Brands: {results['agents']['brand']['results']['total_unique_brands']}")
    print(f"  Unique feature tokens: {results['agents']['feature']['results']['total_unique_features']}")
    print(f"  Price INR range: {stats['min_price']:,.2f} – {stats['max_price']:,.2f}")
    print(f"  Gap pairs flagged: {gaps['identified_gaps_count']}")


if __name__ == "__main__":
    main()
