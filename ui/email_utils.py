"""
Report email delivery for TrendScanner AI.

Providers:
  - smtp  — Gmail or any SMTP server (easy setup; often lands in spam)
  - brevo — Brevo transactional API (recommended for inbox delivery)

Configure via environment variables (see .env.example).
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
import smtplib
import urllib.error
import urllib.request
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from typing import Any, Dict, Optional, Tuple

from core.currency import format_inr

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def is_valid_email(address: str) -> bool:
    """Basic recipient validation."""
    return bool(_EMAIL_RE.match((address or "").strip()))


def _strip_secret(value: str) -> str:
    """Remove spaces from pasted app passwords / API keys."""
    return (value or "").strip().replace(" ", "")


def _sender_from_env() -> Tuple[str, str]:
    from_addr = os.environ.get("SMTP_FROM", "").strip() or os.environ.get("SMTP_USER", "").strip()
    from_name = os.environ.get("SMTP_FROM_NAME", "TrendScanner AI").strip() or "TrendScanner AI"
    return from_name, from_addr


def get_smtp_config() -> Optional[Dict[str, Any]]:
    """Read SMTP settings from environment."""
    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = _strip_secret(os.environ.get("SMTP_PASSWORD", ""))
    if not host or not user or not password:
        return None

    port_raw = os.environ.get("SMTP_PORT", "587").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    use_tls = os.environ.get("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes")
    from_name, from_addr = _sender_from_env()
    if not from_addr:
        from_addr = user

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_addr": from_addr,
        "from_name": from_name,
        "use_tls": use_tls,
    }


def get_brevo_config() -> Optional[Dict[str, Any]]:
    """Read Brevo API settings (verified sender required at brevo.com)."""
    api_key = _strip_secret(os.environ.get("BREVO_API_KEY", ""))
    from_name, from_addr = _sender_from_env()
    if not api_key or not from_addr:
        return None
    return {
        "api_key": api_key,
        "from_addr": from_addr,
        "from_name": from_name,
    }


def resolve_email_provider() -> Optional[str]:
    """Return active provider id: 'brevo' or 'smtp'."""
    preferred = os.environ.get("EMAIL_PROVIDER", "").strip().lower()
    brevo = get_brevo_config()
    smtp = get_smtp_config()

    if preferred == "brevo":
        return "brevo" if brevo else None
    if preferred == "smtp":
        return "smtp" if smtp else None

    if brevo:
        return "brevo"
    if smtp:
        return "smtp"
    return None


def resolve_smtp_config() -> Optional[Dict[str, Any]]:
    """Environment first, then optional Streamlit secrets."""
    cfg = get_smtp_config()
    if cfg:
        return cfg
    try:
        import streamlit as st

        s = st.secrets
        host = str(s.get("SMTP_HOST", "")).strip()
        user = str(s.get("SMTP_USER", "")).strip()
        password = _strip_secret(str(s.get("SMTP_PASSWORD", "")))
        if host and user and password:
            port = int(str(s.get("SMTP_PORT", "587")))
            use_tls = str(s.get("SMTP_USE_TLS", "true")).lower() in ("1", "true", "yes")
            from_addr = str(s.get("SMTP_FROM", user)).strip() or user
            from_name = str(s.get("SMTP_FROM_NAME", "TrendScanner AI")).strip() or "TrendScanner AI"
            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "from_addr": from_addr,
                "from_name": from_name,
                "use_tls": use_tls,
            }
    except Exception:
        pass
    return None


def resolve_brevo_config() -> Optional[Dict[str, Any]]:
    cfg = get_brevo_config()
    if cfg:
        return cfg
    try:
        import streamlit as st

        s = st.secrets
        api_key = _strip_secret(str(s.get("BREVO_API_KEY", "")))
        from_addr = str(s.get("SMTP_FROM", "")).strip()
        from_name = str(s.get("SMTP_FROM_NAME", "TrendScanner AI")).strip() or "TrendScanner AI"
        if api_key and from_addr:
            return {"api_key": api_key, "from_addr": from_addr, "from_name": from_name}
    except Exception:
        pass
    return None


def email_configured() -> bool:
    return resolve_email_provider() is not None


def smtp_configured() -> bool:
    """Backward-compatible alias."""
    return email_configured()


def email_provider_label() -> str:
    provider = resolve_email_provider()
    if provider == "brevo":
        return "Brevo (transactional — inbox delivery)"
    if provider == "smtp":
        return "SMTP (Gmail — may land in spam)"
    return "not configured"


def _report_summary_lines(results: Dict[str, Any]) -> list[str]:
    brand = results["agents"]["brand"]["results"]
    pricing = results["agents"]["pricing"]["results"]["price_statistics"]
    feature = results["agents"]["feature"]["results"]
    gap = results["agents"]["gap"]["results"]
    top_brand = brand["top_brands"][0]["brand"] if brand.get("top_brands") else "N/A"
    return [
        f"Rows analyzed: {results.get('total_records', 0):,}",
        f"Top brand: {top_brand}",
        f"Average price: {format_inr(pricing.get('mean_price', 0))}",
        f"Unique brands: {brand.get('total_unique_brands', '—')}",
        f"Unique features: {feature.get('total_unique_features', '—')}",
        f"Market gaps flagged: {gap.get('identified_gaps_count', 0)}",
        f"Run timestamp: {results.get('timestamp', '—')}",
    ]


def build_report_email_subject(results: Dict[str, Any]) -> str:
    """Human-readable subject line (avoids attachment-style filenames)."""
    ts = str(results.get("timestamp", "")).strip()
    date_part = ts[:10] if len(ts) >= 10 else ""
    if date_part:
        return f"Your market analysis report ({date_part})"
    return "Your market analysis report"


def build_report_email_body(results: Dict[str, Any], *, include_llm: bool = False) -> str:
    """Plain-text summary for the email body."""
    lines = [
        "Hello,",
        "",
        "Thank you for using TrendScanner AI.",
        "",
        "Your market analysis report is attached. Key highlights from this run:",
        "",
        *[_bullet(line) for line in _report_summary_lines(results)],
        "",
    ]

    if include_llm:
        llm = results.get("llm_summary") or {}
        if llm.get("status") == "success" and llm.get("summary"):
            lines.extend(["AI executive summary", "—" * 24, llm["summary"].strip(), ""])

    lines.extend(
        [
            "The attachment contains the full export you selected (charts and tables where applicable).",
            "If you have any questions, reply to this email.",
            "",
            "Best regards,",
            "TrendScanner AI",
        ]
    )
    return "\n".join(lines)


def build_report_email_html(results: Dict[str, Any], *, include_llm: bool = False) -> str:
    """HTML alternative body — improves deliverability vs plain-text-only."""
    summary_rows = "".join(
        f"<tr><td style='padding:4px 12px 4px 0;color:#444;'>{html.escape(label)}</td>"
        f"<td style='padding:4px 0;font-weight:600;'>{html.escape(value)}</td></tr>"
        for label, value in (_split_summary_line(line) for line in _report_summary_lines(results))
    )

    llm_block = ""
    if include_llm:
        llm = results.get("llm_summary") or {}
        if llm.get("status") == "success" and llm.get("summary"):
            llm_block = (
                "<h3 style='margin:24px 0 8px;font-size:16px;'>AI executive summary</h3>"
                f"<p style='margin:0;line-height:1.5;'>{html.escape(llm['summary'].strip()).replace(chr(10), '<br>')}</p>"
            )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>TrendScanner AI report</title></head>
<body style="font-family:Segoe UI,Arial,sans-serif;font-size:15px;color:#222;line-height:1.5;margin:0;padding:24px;">
  <p>Hello,</p>
  <p>Thank you for using <strong>TrendScanner AI</strong>.</p>
  <p>Your market analysis report is attached. Key highlights from this run:</p>
  <table style="border-collapse:collapse;">{summary_rows}</table>
  {llm_block}
  <p style="margin-top:24px;">The attachment contains the full export you selected. If you have any questions, reply to this email.</p>
  <p style="margin-top:24px;">Best regards,<br><strong>TrendScanner AI</strong></p>
</body>
</html>"""


def friendly_attachment_name(filename: str) -> str:
    """Use a clean attachment name (filenames with underscores can hurt spam scores)."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "TrendScanner-Market-Analysis-Report.pdf"
    if lower.endswith(".xlsx"):
        return "TrendScanner-Market-Analysis-Report.xlsx"
    if lower.endswith(".csv"):
        return "TrendScanner-Market-Analysis-Report.csv"
    if lower.endswith(".json"):
        return "TrendScanner-Market-Analysis-Report.json"
    return filename


def _bullet(line: str) -> str:
    return f"- {line}"


def _split_summary_line(line: str) -> Tuple[str, str]:
    if ": " in line:
        label, value = line.split(": ", 1)
        return label, value
    return line, ""


def _attachment_subtype(mime_type: str, filename: str) -> str:
    if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return "pdf"
    if mime_type == "application/json" or filename.lower().endswith(".json"):
        return "json"
    if mime_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ) or filename.lower().endswith((".xlsx", ".xls")):
        return "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if mime_type == "text/csv" or filename.lower().endswith(".csv"):
        return "csv"
    return "octet-stream"


def _build_mime_message(
    *,
    from_name: str,
    from_addr: str,
    recipient: str,
    subject: str,
    body: str,
    html_body: Optional[str],
    attachment_bytes: bytes,
    filename: str,
    mime_type: str,
) -> MIMEMultipart:
    from_header = formataddr((from_name, from_addr))
    domain = from_addr.split("@")[-1] if "@" in from_addr else None

    msg = MIMEMultipart("mixed")
    msg["From"] = from_header
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=domain)
    msg["Reply-To"] = from_header
    msg["MIME-Version"] = "1.0"

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body, "plain", "utf-8"))
    alt.attach(MIMEText(html_body or body, "html", "utf-8"))
    msg.attach(alt)

    subtype = _attachment_subtype(mime_type, filename)
    part = MIMEApplication(attachment_bytes, _subtype=subtype)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)
    return msg


def _send_via_smtp(
    recipient: str,
    *,
    subject: str,
    body: str,
    html_body: Optional[str],
    attachment_bytes: bytes,
    filename: str,
    mime_type: str,
    cfg: Dict[str, Any],
) -> Tuple[bool, str]:
    msg = _build_mime_message(
        from_name=cfg["from_name"],
        from_addr=cfg["from_addr"],
        recipient=recipient,
        subject=subject,
        body=body,
        html_body=html_body,
        attachment_bytes=attachment_bytes,
        filename=filename,
        mime_type=mime_type,
    )
    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as server:
            if cfg["use_tls"]:
                server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg, from_addr=cfg["from_addr"], to_addrs=[recipient])
        return True, f"Report emailed to {recipient}."
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP login failed — check SMTP_USER and SMTP_PASSWORD (use an app password for Gmail)."
    except smtplib.SMTPException as exc:
        return False, f"SMTP error: {exc}"
    except OSError as exc:
        return False, f"Could not reach mail server: {exc}"


def _send_via_brevo(
    recipient: str,
    *,
    subject: str,
    body: str,
    html_body: Optional[str],
    attachment_bytes: bytes,
    filename: str,
    cfg: Dict[str, Any],
) -> Tuple[bool, str]:
    payload = {
        "sender": {"name": cfg["from_name"], "email": cfg["from_addr"]},
        "to": [{"email": recipient}],
        "subject": subject,
        "htmlContent": html_body or body,
        "textContent": body,
        "attachment": [
            {
                "content": base64.b64encode(attachment_bytes).decode("ascii"),
                "name": filename,
            }
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        _BREVO_API_URL,
        data=data,
        headers={
            "api-key": cfg["api_key"],
            "Content-Type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if 200 <= response.status < 300:
                return True, f"Report emailed to {recipient} via Brevo."
            return False, f"Brevo API returned status {response.status}."
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401:
            return False, "Brevo API key is invalid — check BREVO_API_KEY in .env."
        if "not verified" in detail.lower() or exc.code == 400:
            return (
                False,
                "Brevo rejected the sender — verify SMTP_FROM at brevo.com → Senders & IP → Senders.",
            )
        return False, f"Brevo API error ({exc.code}): {detail[:200]}"
    except urllib.error.URLError as exc:
        return False, f"Could not reach Brevo API: {exc.reason}"
    except Exception as exc:
        return False, f"Brevo send failed: {exc}"
    return False, "Brevo API returned an unexpected response."


def send_report_email(
    to_email: str,
    *,
    subject: str,
    body: str,
    attachment_bytes: bytes,
    filename: str,
    mime_type: str = "application/octet-stream",
    html_body: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Send one email with a single attachment.

    Uses Brevo API when EMAIL_PROVIDER=brevo (recommended), otherwise SMTP.
    Returns (success, message).
    """
    recipient = to_email.strip()
    if not is_valid_email(recipient):
        return False, "Enter a valid recipient email address."

    filename = friendly_attachment_name(filename)
    provider = resolve_email_provider()
    if not provider:
        return (
            False,
            "Email is not configured. Set BREVO_API_KEY (recommended) or SMTP_* in .env.",
        )

    if provider == "brevo":
        brevo_cfg = resolve_brevo_config()
        if not brevo_cfg:
            return False, "Brevo is selected but BREVO_API_KEY or SMTP_FROM is missing."
        return _send_via_brevo(
            recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            attachment_bytes=attachment_bytes,
            filename=filename,
            mime_type=mime_type,
            cfg=brevo_cfg,
        )

    smtp_cfg = config or resolve_smtp_config()
    if not smtp_cfg:
        return False, "SMTP is not configured. Set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD in .env."
    return _send_via_smtp(
        recipient,
        subject=subject,
        body=body,
        html_body=html_body,
        attachment_bytes=attachment_bytes,
        filename=filename,
        mime_type=mime_type,
        cfg=smtp_cfg,
    )
