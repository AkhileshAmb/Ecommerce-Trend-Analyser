"""
Price enrichment for analytics: optional USD→INR scaling and optional live retail hints.

All statistics (min, max, quartiles) follow whatever numbers end up in the price column —
ranges adapt to your uploaded product mix; nothing is forced into a fixed band.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

_SERPAPI_URL = "https://serpapi.com/search.json"

# Display/analytics assume amounts are INR in the UI; foreign CSVs often use USD-like magnitudes.
DEFAULT_USD_TO_INR = float(os.environ.get("USD_TO_INR_RATE", "83.0"))


def looks_like_usd_scale(prices: pd.Series) -> bool:
    """Heuristic: many retail exports use sub‑5k numbers as USD, not lakhs of INR."""
    s = pd.to_numeric(prices, errors="coerce").dropna()
    if len(s) == 0:
        return False
    return float(s.max()) <= 8000.0 and float(s.median()) < 5000.0


def scale_usd_to_inr(prices: pd.Series, rate: Optional[float] = None) -> pd.Series:
    """Multiply numeric prices by USD→INR rate (preserves spread within the file)."""
    r = float(rate) if rate is not None else DEFAULT_USD_TO_INR
    s = pd.to_numeric(prices, errors="coerce").astype(float)
    return (s * r).round(2)


def serpapi_google_shopping_first_inr(query: str, api_key: str, timeout: float = 28.0) -> Optional[float]:
    """First Google Shopping India result price, or None. Requires SerpAPI key."""
    params = urllib.parse.urlencode(
        {
            "engine": "google_shopping",
            "q": query + " buy India",
            "gl": "in",
            "hl": "en",
            "api_key": api_key,
        }
    )
    url = f"{_SERPAPI_URL}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrendScannerAI/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None

    if data.get("error"):
        return None

    for item in data.get("shopping_results") or []:
        ep = item.get("extracted_price")
        val = _parse_inr_amount(ep)
        if val is not None:
            return val
        price_str = item.get("price") or ""
        val = _parse_inr_amount(price_str)
        if val is not None:
            return val
    return None


def _parse_inr_amount(raw: Any) -> Optional[float]:
    """Accept a wide INR range — groceries to industrial SKUs."""
    lo, hi = 1.0, 50_000_000.0
    if raw is None:
        return None
    try:
        x = float(raw)
        if lo <= x <= hi:
            return x
    except (TypeError, ValueError):
        pass
    s = str(raw).replace("₹", "").replace(",", "").strip()
    try:
        x = float(s)
        if lo <= x <= hi:
            return x
    except ValueError:
        pass
    m = re.search(r"([\d]{1,9}(?:\.\d+)?)", str(raw).replace(",", ""))
    if m:
        try:
            x = float(m.group(1))
            if lo <= x <= hi:
                return x
        except ValueError:
            pass
    return None


def _build_product_query(
    row: pd.Series,
    brand_col: str,
    feature_col: str,
    model_col: Optional[str],
) -> str:
    brand = str(row.get(brand_col, "")).strip()
    feat = str(row.get(feature_col, "")).strip()[:120]
    model = ""
    if model_col and model_col in row.index:
        model = str(row.get(model_col, "")).strip()
    parts = [p for p in (brand, model, feat) if p]
    q = " ".join(parts).strip()
    if len(q) >= 4:
        return q
    return feat or brand or "product"


def apply_live_serpapi(
    df: pd.DataFrame,
    brand_col: str,
    price_col: str,
    feature_col: str,
    api_key: str,
    model_col: Optional[str] = None,
    max_unique_queries: int = 22,
    cache: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    One SerpAPI call per unique product query (brand + model + feature text).
    Rows without a hit keep their uploaded price — no fixed catalog band.
    """
    msgs: List[str] = []
    cache = cache if cache is not None else {}
    out = df.copy()
    original = pd.to_numeric(df[price_col], errors="coerce")

    idx_to_q = {idx: _build_product_query(row, brand_col, feature_col, model_col) for idx, row in df.iterrows()}
    unique_q: List[str] = []
    seen = set()
    for idx in df.index:
        q = idx_to_q[idx]
        if q not in seen:
            seen.add(q)
            unique_q.append(q)

    live_by_q: Dict[str, float] = {}
    api_calls = 0
    for q in unique_q:
        if q in cache and cache[q] > 0:
            live_by_q[q] = float(cache[q])
            continue
        if api_calls >= max_unique_queries:
            continue
        val = serpapi_google_shopping_first_inr(q, api_key)
        api_calls += 1
        if val is not None:
            cache[q] = val
            live_by_q[q] = val
        else:
            cache[q] = -1.0

    if api_calls >= max_unique_queries and len(unique_q) > max_unique_queries:
        msgs.append(
            f"Live lookup capped at {max_unique_queries} API calls; remaining SKUs keep uploaded prices."
        )

    for idx in df.index:
        q = idx_to_q[idx]
        if q in live_by_q:
            out.at[idx, price_col] = live_by_q[q]
        else:
            out.at[idx, price_col] = original.loc[idx]

    msgs.append(
        f"Live Google Shopping (India): {api_calls} lookup(s); others unchanged from your CSV."
    )
    return out, msgs


def apply_price_enrichment(
    df: pd.DataFrame,
    brand_column: str,
    price_column: str,
    feature_column: str,
    *,
    mode: str,
    model_column: Optional[str] = None,
    serpapi_key: Optional[str] = None,
    cache: Optional[Dict[str, float]] = None,
    usd_to_inr_rate: Optional[float] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    mode:
      - uploaded: use CSV numbers as-is (analytics range follows your data).
      - scale_usd_to_inr: if values look USD-like, multiply by USD_TO_INR_RATE; else unchanged.
      - live_shopping: SerpAPI hints where available; SERPAPI_API_KEY required; else unchanged + note.

    Legacy aliases: csv_auto → scale_usd_to_inr; reference_catalog → uploaded (catalog removed).
    """
    msgs: List[str] = []
    if brand_column not in df.columns or price_column not in df.columns or feature_column not in df.columns:
        msgs.append("Missing mapped columns — skipping price enrichment.")
        return df.copy(), msgs

    rate = usd_to_inr_rate if usd_to_inr_rate is not None else DEFAULT_USD_TO_INR
    key = serpapi_key or os.environ.get("SERPAPI_API_KEY")

    # Backward compatibility with older sidebar keys
    if mode == "csv_auto":
        mode = "scale_usd_to_inr"
    if mode == "reference_catalog":
        msgs.append(
            "Legacy “catalog” mode removed — using uploaded amounts only. "
            "Switch to “Scale USD-like…” if your file uses dollar-scale prices."
        )
        mode = "uploaded"

    out = df.copy()

    if mode == "uploaded":
        msgs.append(
            "Using uploaded prices as-is — min/max bands in reports follow your dataset."
        )
        return out, msgs

    if mode == "scale_usd_to_inr":
        s = pd.to_numeric(out[price_column], errors="coerce")
        if looks_like_usd_scale(s):
            out[price_column] = scale_usd_to_inr(s, rate)
            msgs.append(
                f"Detected USD-like magnitudes — multiplied by ₹{rate:.2f}/USD. "
                "Your reported range now reflects scaled INR."
            )
        else:
            msgs.append(
                "Prices already look INR-scale (or mixed); left unchanged — ranges follow your data."
            )
        return out, msgs

    if mode == "live_shopping":
        if not key:
            msgs.append(
                "SERPAPI_API_KEY not set — keeping uploaded prices (no live lookup)."
            )
            return out, msgs
        out, live_msgs = apply_live_serpapi(
            out,
            brand_column,
            price_column,
            feature_column,
            key,
            model_column=model_column,
            cache=cache,
        )
        msgs.extend(live_msgs)
        return out, msgs

    msgs.append("Unknown price mode — leaving data unchanged.")
    return df.copy(), msgs


# Backward-compatible name used by earlier UI iterations
def apply_mobile_price_mode(*args: Any, **kwargs: Any) -> Tuple[pd.DataFrame, List[str]]:
    return apply_price_enrichment(*args, **kwargs)
