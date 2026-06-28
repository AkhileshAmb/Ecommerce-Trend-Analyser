"""
LLM Summarization Module

Summarizes pre-computed analytical agent results into natural language.
Uses Groq (Llama) by default, with a deterministic local fallback when unavailable.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv

    _env_file = Path("!.env")
    if _env_file.exists():
        load_dotenv("!.env")
    else:
        load_dotenv()
except ImportError:
    pass

_PLACEHOLDER_KEYS = frozenset({"your_groq_api_key_here", "your_api_key_here", ""})
_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Cloudflare blocks Python urllib's default User-Agent (HTTP 403, error 1010).
_GROQ_HTTP_HEADERS_BASE = {
    "Content-Type": "application/json",
    "User-Agent": "TrendScannerAI/1.0",
    "Accept": "application/json",
}


def is_groq_configured(api_key: Optional[str] = None) -> bool:
    """True when a non-placeholder Groq API key is available."""
    key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
    return bool(key and key not in _PLACEHOLDER_KEYS)


def load_prompt_template() -> str:
    """Load the fixed prompt template from prompt.txt."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _condense_results(agent_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only the fields needed for a summary — smaller prompts, faster calls."""
    if agent_name == "brand_agent":
        return {
            "total_unique_brands": results.get("total_unique_brands"),
            "total_records": results.get("total_records"),
            "top_brands": (results.get("top_brands") or [])[:8],
        }
    if agent_name == "pricing_agent":
        stats = results.get("price_statistics") or {}
        optimal = results.get("optimal_price_range") or {}
        return {
            "valid_price_records": results.get("valid_price_records"),
            "price_statistics": {
                k: round(float(v), 2) if isinstance(v, (int, float)) else v
                for k, v in stats.items()
            },
            "optimal_price_range": {
                k: round(float(v), 2) if isinstance(v, (int, float)) else v
                for k, v in optimal.items()
            },
        }
    if agent_name == "feature_agent":
        return {
            "total_unique_features": results.get("total_unique_features"),
            "total_records": results.get("total_records"),
            "top_features": (results.get("top_features") or [])[:12],
        }
    if agent_name == "gap_agent":
        return {
            "identified_gaps_count": results.get("identified_gaps_count"),
            "total_combinations": results.get("total_combinations"),
            "gap_threshold": results.get("gap_threshold"),
            "top_gaps": (results.get("top_gaps") or [])[:8],
        }
    return results


def format_agent_results(agent_outputs: List[Dict]) -> str:
    """Format condensed agent outputs for the LLM prompt."""
    formatted_results = []
    for agent_output in agent_outputs:
        agent_name = agent_output.get("agent_name", "unknown")
        results = agent_output.get("results", {})
        confidence = agent_output.get("confidence", 0.0)
        condensed = _condense_results(agent_name, results)
        formatted_results.append(f"\n[{agent_name.upper()}]")
        formatted_results.append(f"Confidence: {confidence:.4f}")
        formatted_results.append(f"Results: {json.dumps(condensed, indent=2)}")
    return "\n".join(formatted_results)


def build_full_prompt(agent_outputs: List[Dict]) -> str:
    """Assemble the final prompt sent to Groq."""
    prompt_template = load_prompt_template()
    return prompt_template.format(agent_results=format_agent_results(agent_outputs))


def _parse_groq_error(exc: Exception) -> Tuple[str, str]:
    """Return (category, user_message) from a Groq API exception."""
    text = str(exc)
    lower = text.lower()
    if "403" in text and "1010" in text:
        return (
            "blocked",
            "Groq request was blocked by Cloudflare (error 1010). "
            "Restart the app after updating — this is fixed in the latest summarizer.",
        )
    if "401" in text or ("invalid" in lower and "api key" in lower):
        return (
            "auth",
            "Invalid Groq API key. Get a free key at https://console.groq.com "
            "and set GROQ_API_KEY in .env, then restart the app.",
        )
    if "429" in text or "rate limit" in lower or "quota" in lower:
        return (
            "quota",
            "Groq rate limit reached. Wait a minute and retry, or use the offline "
            "template fallback (LLM_ALLOW_LOCAL_FALLBACK=true).",
        )
    if "404" in text and "model" in lower:
        return (
            "model",
            f"Groq model not found. Set GROQ_MODEL to a supported model "
            f"(default: {_DEFAULT_GROQ_MODEL}). Details: {text[:160]}",
        )
    return ("unknown", text[:320])


def summarize_locally(agent_outputs: List[Dict]) -> Dict:
    """Deterministic narrative when Groq is unavailable."""
    by_name = {a.get("agent_name"): a for a in agent_outputs}
    brand = (by_name.get("brand_agent") or {}).get("results", {})
    pricing = (by_name.get("pricing_agent") or {}).get("results", {})
    feature = (by_name.get("feature_agent") or {}).get("results", {})
    gap = (by_name.get("gap_agent") or {}).get("results", {})

    stats = pricing.get("price_statistics") or {}
    optimal = pricing.get("optimal_price_range") or {}
    top_brands = brand.get("top_brands") or []
    top_features = feature.get("top_features") or []
    top_gaps = gap.get("top_gaps") or []

    brand_bits = ", ".join(
        f"{b.get('brand', '?')} ({b.get('count', 0)} listings)"
        for b in top_brands[:4]
    ) or "no dominant brands identified"
    feature_bits = ", ".join(
        f"{f.get('feature', '?')} ({f.get('count', 0)})" for f in top_features[:4]
    ) or "no standout features"
    gap_bits = ", ".join(
        f"{g.get('brand', '?')} × {g.get('feature', '?')}" for g in top_gaps[:3]
    ) or "no major underrepresented pairs at the chosen threshold"

    mean_p = stats.get("mean_price")
    min_p = stats.get("min_price")
    max_p = stats.get("max_price")
    opt_min = optimal.get("optimal_range_min")
    opt_max = optimal.get("optimal_range_max")

    def _inr(v: Any) -> str:
        if v is None:
            return "N/A"
        try:
            return f"₹{float(v):,.0f}"
        except (TypeError, ValueError):
            return str(v)

    p1 = (
        f"The dataset covers {brand.get('total_records', '—')} product records across "
        f"{brand.get('total_unique_brands', '—')} brands. "
        f"Market concentration is led by {brand_bits}. "
        f"Feature prevalence highlights {feature_bits}, suggesting where assortment overlaps most."
    )
    p2 = (
        f"Pricing spans {_inr(min_p)} to {_inr(max_p)} with a mean of {_inr(mean_p)}. "
        f"The inter-quartile band suggests a competitive sweet spot between "
        f"{_inr(opt_min)} and {_inr(opt_max)} for positioning new or revised SKUs."
    )
    p3 = (
        f"Gap analysis flagged {gap.get('identified_gaps_count', 0)} underrepresented "
        f"brand–feature pairs (threshold {gap.get('gap_threshold', '—')}). "
        f"Notable opportunities include {gap_bits}. "
        f"These gaps may indicate whitespace for differentiation or data-collection blind spots."
    )

    return {
        "summary": "\n\n".join([p1, p2, p3]),
        "model": "local-template",
        "temperature": 0.0,
        "num_agents_summarized": len(agent_outputs),
        "status": "success",
        "provider": "local",
    }


def summarize_with_groq(
    agent_outputs: List[Dict],
    api_key: Optional[str] = None,
    temperature: float = 0.3,
) -> Dict:
    """Summarize via Groq (OpenAI-compatible chat completions API)."""
    api_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
    if not is_groq_configured(api_key):
        raise ValueError(
            "Groq API key required. Set GROQ_API_KEY in .env "
            "(free at https://console.groq.com) and restart the app."
        )

    if temperature > 0.3:
        temperature = 0.3

    model = (os.getenv("GROQ_MODEL") or _DEFAULT_GROQ_MODEL).strip()
    full_prompt = build_full_prompt(agent_outputs)
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": temperature,
            "max_tokens": 768,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        _GROQ_API_URL,
        data=payload,
        headers={
            **_GROQ_HTTP_HEADERS_BASE,
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        summary_text = body["choices"][0]["message"]["content"].strip()
        return {
            "summary": summary_text,
            "model": body.get("model", model),
            "temperature": temperature,
            "num_agents_summarized": len(agent_outputs),
            "status": "success",
            "provider": "groq",
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:320]
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail}") from exc


def summarize_agent_results(
    agent_outputs: List[Dict],
    api_key: Optional[str] = None,
) -> Dict:
    """
    Main entry: Groq (single API call) → optional local template fallback.
    """
    errors: List[str] = []
    allow_local = os.getenv("LLM_ALLOW_LOCAL_FALLBACK", "true").lower() in (
        "1",
        "true",
        "yes",
    )

    groq_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
    if is_groq_configured(groq_key):
        try:
            return summarize_with_groq(agent_outputs, api_key=groq_key, temperature=0.3)
        except Exception as exc:
            _, msg = _parse_groq_error(exc)
            errors.append(msg)
    else:
        errors.append(
            "GROQ_API_KEY not set. Add a free key from https://console.groq.com to .env."
        )

    if allow_local:
        local = summarize_locally(agent_outputs)
        if errors:
            local["warning"] = " ".join(errors) + " Used offline template summary instead."
        return local

    return {
        "summary": None,
        "error": " | ".join(errors) or "Groq API key not configured.",
        "model": None,
        "temperature": 0.3,
        "num_agents_summarized": len(agent_outputs),
        "status": "error",
    }
