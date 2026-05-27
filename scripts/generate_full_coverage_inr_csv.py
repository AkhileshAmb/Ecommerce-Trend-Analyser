"""
Generate a full-coverage TrendScanner AI test CSV (INR).

Exercises: ingestion, column mapping, brand share, pricing stats/charts,
comma/pipe/semicolon features, gap signals, dedup, optional model column.
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

random.seed(2026)

# --- Brands & skew (leader + mid + long tail) ---
BRANDS = [
    ("Samsung", 22, "Smartphone", (18999, 134999)),
    ("Xiaomi", 18, "Smartphone", (9999, 69999)),
    ("Realme", 14, "Smartphone", (8999, 45999)),
    ("Apple", 12, "Smartphone", (49900, 159900)),
    ("OnePlus", 10, "Smartphone", (22999, 89999)),
    ("Oppo", 9, "Smartphone", (10999, 54999)),
    ("Vivo", 8, "Smartphone", (9999, 52999)),
    ("Motorola", 6, "Smartphone", (7999, 39999)),
    ("Nokia", 5, "Smartphone", (5999, 24999)),
    ("LG", 5, "Smartphone", (14999, 74999)),
    ("Sony", 6, "Electronics", (2999, 189999)),
    ("Dell", 8, "Laptop", (42999, 175000)),
    ("HP", 8, "Laptop", (38999, 168000)),
    ("Lenovo", 7, "Laptop", (32999, 149000)),
    ("Asus", 7, "Laptop", (45999, 249000)),
    ("Canon", 5, "Camera", (24999, 219000)),
    ("boAt", 6, "Audio", (499, 8999)),
    ("Noise", 5, "Audio", (999, 12999)),
]

# Common multi-feature bundles (comma-separated — feature agent splits these)
PHONE_FEATURES = [
    "5G,OLED,128GB,Wireless Charging",
    "5G,AMOLED,256GB,Fast Charging",
    "4G,LCD,64GB",
    "5G,OLED,512GB,Wireless Charging",
    "5G,IPS,128GB,Fast Charging",
    "4G,AMOLED,128GB",
]

LAPTOP_FEATURES = [
    "WiFi 6,IPS Display,16GB RAM,512GB SSD",
    "WiFi 6,Bluetooth 5.3,RTX Graphics,Thunderbolt 4",
    "WiFi 6,IPS Display,8GB RAM,256GB SSD",
    "144Hz,RTX Graphics,16GB RAM,1TB SSD",
]

CAMERA_FEATURES = [
    "4K UHD,HDR10,Optical Zoom,Dual Camera",
    "4K UHD,Telephoto Lens,Optical Zoom",
    "1080p,HDR10,Dual Camera",
]

AUDIO_FEATURES = [
    "Bluetooth 5.3,Noise Cancelling,IPX4",
    "Bluetooth 5.2,Fast Charging,ENC",
    "Wireless,20hr Battery,Type-C",
]

# Rare full feature strings for gap agent (whole-cell match)
GAP_RARE = [
    ("Apple", "Foldable,1TB,ProMotion"),
    ("Nokia", "5G,OLED,512GB,Wireless Charging"),
    ("Dell", "Foldable,OLED,RTX Graphics"),
    ("boAt", "5G,OLED,512GB"),  # odd category mix on purpose
    ("Canon", "8K Video,Foldable Sensor"),
    ("Noise", "Thunderbolt 4,RTX Graphics"),
    ("Vivo", "Foldable,Under-Display Camera"),
    ("Motorola", "Satellite SOS,1TB"),
]

# Pipe / semicolon delimiter samples (feature agent)
DELIMITER_SAMPLES = [
    ("Samsung", "5G|OLED|256GB|Wireless Charging"),
    ("Xiaomi", "5G;AMOLED;128GB;Fast Charging"),
    ("HP", "WiFi 6|Thunderbolt 4|16GB RAM"),
]

SUFFIX = ["A", "Lite", "Pro", "Max", "Ultra", "FE", "Plus"]


def _price(lo: float, hi: float, *, premium: bool = False) -> float:
    x = random.uniform(lo, hi)
    if premium:
        x *= random.uniform(1.08, 1.35)
    # Round to typical Indian retail (often x99)
    x = round(x / 100) * 100 - random.choice([0, 1, 99])
    if x < 499:
        x = 499.0
    return round(x, 2)


def _model(brand: str) -> str:
    return f"{brand} {random.choice(SUFFIX)}{random.randint(2, 99)}"


def build_rows() -> list[dict]:
    rows: list[dict] = []

    for brand, weight, category, (plo, phi) in BRANDS:
        feature_pool = {
            "Smartphone": PHONE_FEATURES,
            "Laptop": LAPTOP_FEATURES,
            "Camera": CAMERA_FEATURES,
            "Audio": AUDIO_FEATURES,
            "Electronics": PHONE_FEATURES + CAMERA_FEATURES,
        }.get(category, PHONE_FEATURES)

        for _ in range(weight):
            feat = random.choice(feature_pool)
            premium = "512GB" in feat or "RTX" in feat or "1TB" in feat
            rows.append(
                {
                    "brand": brand,
                    "price": _price(plo, phi, premium=premium),
                    "feature": feat,
                    "category": category,
                    "model": _model(brand),
                }
            )

    # Delimiter variety
    for brand, feat in DELIMITER_SAMPLES:
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        rows.append(
            {
                "brand": brand,
                "price": _price(plo, phi),
                "feature": feat,
                "category": cat,
                "model": _model(brand),
            }
        )

    # Gap signals: popular feature string across market, but scarce for specific big brands.
    # (Gap agent keys on the full feature cell, not individual tokens.)
    POPULAR_GAP_FEATURE = "5G,OLED,128GB,Wireless Charging"
    gap_targets = [
        ("Apple", 1),
        ("Sony", 1),
        ("Canon", 1),
        ("Dell", 1),
    ]
    for brand, n in gap_targets:
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        for _ in range(n):
            rows.append(
                {
                    "brand": brand,
                    "price": _price(plo, phi),
                    "feature": POPULAR_GAP_FEATURE,
                    "category": cat,
                    "model": _model(brand),
                }
            )

    # Flood popular feature on high-volume brands (raises expected for that feature string).
    for brand in ("Samsung", "Xiaomi", "Realme", "Oppo", "Vivo"):
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        for _ in range(8):
            rows.append(
                {
                    "brand": brand,
                    "price": _price(plo, phi),
                    "feature": POPULAR_GAP_FEATURE,
                    "category": cat,
                    "model": _model(brand),
                }
            )

    # Other rare full-string pairs (feature tab + edge cases)
    for brand, feat in GAP_RARE:
        cat = next((c for b, _, c, _ in BRANDS if b == brand), "Smartphone")
        plo, phi = next((p for b, _, _, p in BRANDS if b == brand), (10000, 80000))
        rows.append(
            {
                "brand": brand,
                "price": _price(phi * 0.7, phi * 1.2, premium=True),
                "feature": feat,
                "category": cat,
                "model": _model(brand),
            }
        )

    # Pricing spread: budget outliers + premium outliers (histogram / box plot)
    outliers = [
        ("boAt", 499.0, "Bluetooth 5.2,ENC", "Audio"),
        ("Noise", 1299.0, "Wireless,ENC", "Audio"),
        ("Asus", 279999.0, "144Hz,RTX Graphics,32GB RAM,2TB SSD", "Laptop"),
        ("Apple", 159900.0, "5G,OLED,1TB,Wireless Charging", "Smartphone"),
        ("Xiaomi", 8999.0, "4G,LCD,64GB", "Smartphone"),
        ("Canon", 224999.0, "8K Video,Telephoto Lens,Optical Zoom", "Camera"),
    ]
    for brand, price, feat, cat in outliers:
        rows.append(
            {
                "brand": brand,
                "price": price,
                "feature": feat,
                "category": cat,
                "model": _model(brand),
            }
        )

    # Optional columns empty (cleaning keeps row if brand/price/feature present)
    for brand in ("Samsung", "Apple", "Dell"):
        cat = next(c for b, _, c, _ in BRANDS if b == brand)
        plo, phi = next(p for b, _, _, p in BRANDS if b == brand)
        rows.append(
            {
                "brand": brand,
                "price": _price(plo, phi),
                "feature": random.choice(PHONE_FEATURES if cat == "Smartphone" else LAPTOP_FEATURES),
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

    # Exact duplicates (dedup testing — ~12 rows)
    dup_sources = random.sample(rows, min(12, len(rows)))
    rows.extend(dup_sources)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=2026).reset_index(drop=True)

    out = root / "test_trendscanner_full_coverage_inr.csv"
    df.to_csv(out, index=False, encoding="utf-8")

    # Quick validation summary
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
        top_n_brands=15,
        top_n_features=20,
        gap_threshold=-0.5,
    )

    stats = results["agents"]["pricing"]["results"]["price_statistics"]
    gaps = results["agents"]["gap"]["results"]

    print(f"Wrote: {out}")
    print(f"  Raw rows: {len(df)} | After clean: {len(cleaned)} | Dupes removed: {len(df) - len(cleaned)}")
    print(f"  Brands: {results['agents']['brand']['results']['total_unique_brands']}")
    print(f"  Unique feature tokens: {results['agents']['feature']['results']['total_unique_features']}")
    print(f"  Price INR range: {stats['min_price']:,.2f} – {stats['max_price']:,.2f}")
    print(f"  Gap pairs below cutoff: {gaps['identified_gaps_count']}")


if __name__ == "__main__":
    main()
