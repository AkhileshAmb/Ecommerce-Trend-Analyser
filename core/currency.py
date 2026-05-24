"""Indian Rupee display helpers — numeric columns are shown as INR everywhere."""

from __future__ import annotations

from typing import Union

INR_SYMBOL = "₹"


def format_inr(amount: Union[float, int], *, decimals: int = 2) -> str:
    """Format a numeric amount as INR for dashboards, charts, and exports."""
    return f"{INR_SYMBOL}{float(amount):,.{decimals}f}"
