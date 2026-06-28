"""
WhatsApp share helpers for TrendScanner AI.

Uses click-to-chat (wa.me) — opens WhatsApp with a pre-filled report summary.
The user taps Send in WhatsApp; PDF/files can be attached manually after download.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from typing import Any, Dict, Tuple

from ui.email_utils import _report_summary_lines

_DIGITS_RE = re.compile(r"\D")
_DEFAULT_COUNTRY = os.environ.get("WHATSAPP_DEFAULT_COUNTRY_CODE", "91").strip() or "91"
_MAX_WA_URL_CHARS = 1800


def normalize_whatsapp_phone(country_code: str, local_number: str) -> Tuple[bool, str, str]:
    """
    Combine country code + local number into wa.me digits (no + prefix).

    Returns (ok, e164_digits_without_plus, error_message).
    """
    cc = _DIGITS_RE.sub("", country_code or "")
    local = _DIGITS_RE.sub("", local_number or "").lstrip("0")
    digits = f"{cc}{local}"

    if not cc:
        return False, digits, "Enter a country code (e.g. 91 for India)."
    if not local:
        return False, digits, "Enter the recipient phone number."
    if len(digits) < 10 or len(digits) > 15:
        return False, digits, "Phone number must be 10–15 digits including country code."
    return True, digits, ""


def build_whatsapp_message(
    results: Dict[str, Any],
    *,
    include_llm: bool = True,
    max_chars: int = _MAX_WA_URL_CHARS,
) -> str:
    """Plain-text report summary formatted for WhatsApp."""
    lines = [
        "TrendScanner AI — Market Report",
        "",
        "Key highlights:",
        *[_wa_bullet(line) for line in _report_summary_lines(results)],
    ]

    if include_llm:
        llm = results.get("llm_summary") or {}
        if llm.get("status") == "success" and llm.get("summary"):
            summary = llm["summary"].strip()
            if len(summary) > 700:
                summary = summary[:697] + "..."
            lines.extend(["", "AI summary:", summary])

    lines.extend(
        [
            "",
            "Download the full PDF/Excel from TrendScanner Export tab and attach here if needed.",
            "",
            "— TrendScanner AI",
        ]
    )

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."
    return text


def build_wa_me_url(phone_digits: str, message: str) -> str:
    """Build https://wa.me/<digits>?text=... for click-to-chat."""
    digits = _DIGITS_RE.sub("", phone_digits or "")
    encoded = urllib.parse.quote(message, safe="")
    return f"https://wa.me/{digits}?text={encoded}"


def default_country_code() -> str:
    return _DEFAULT_COUNTRY


def _wa_bullet(line: str) -> str:
    """Turn 'Label: value' lines into WhatsApp-friendly bullets."""
    if ":" in line:
        label, _, value = line.partition(":")
        return f"• {label.strip()}: {value.strip()}"
    return f"• {line.strip()}"
