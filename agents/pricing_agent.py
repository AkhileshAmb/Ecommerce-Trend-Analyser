"""Pricing Analysis Agent.

Deterministic agent that analyzes numeric pricing data for any product category.
Computes min, max, quartiles, and statistics from the uploaded price column — ranges always follow the dataset.
UI formats amounts as INR; optional enrichment may scale USD-like CSV magnitudes.
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


def extract_price_column(df: pd.DataFrame, price_column: str) -> pd.Series:
    """
    Extract and clean price data from DataFrame.
    
    Args:
        df: Pandas DataFrame with pricing data
        price_column: Name of the column containing prices
    
    Returns:
        Series with numeric price values
    """
    if price_column not in df.columns:
        raise ValueError(f"Column '{price_column}' not found in DataFrame")
    
    # Convert to numeric, handling any non-numeric values
    prices = pd.to_numeric(df[price_column], errors='coerce')
    
    # Remove NaN values
    prices = prices.dropna()
    
    if len(prices) == 0:
        raise ValueError(f"No valid price data found in column '{price_column}'")
    
    return prices


def calculate_price_statistics(prices: pd.Series) -> Dict:
    """
    Calculate basic price statistics.
    
    Args:
        prices: Series with numeric price values
    
    Returns:
        Dictionary with price statistics
    """
    return {
        "min_price": float(prices.min()),
        "max_price": float(prices.max()),
        "mean_price": float(prices.mean()),
        "median_price": float(prices.median()),
        "std_price": float(prices.std())
    }


def calculate_optimal_price_range(prices: pd.Series) -> Dict:
    """
    Calculate optimal price range using quartiles.
    
    Args:
        prices: Series with numeric price values
    
    Returns:
        Dictionary with optimal price range (Q1 to Q3)
    """
    q1 = float(prices.quantile(0.25))
    q2 = float(prices.quantile(0.50))  # Median
    q3 = float(prices.quantile(0.75))
    
    return {
        "q1_price": q1,
        "median_price": q2,
        "q3_price": q3,
        "optimal_range_min": q1,
        "optimal_range_max": q3,
        "optimal_range_span": q3 - q1
    }


def analyze_pricing(df: pd.DataFrame, price_column: str = "price") -> Dict:
    """
    Main analysis function for pricing agent.
    
    Args:
        df: Pandas DataFrame with market data
        price_column: Name of the column containing prices
    
    Returns:
        Structured JSON output with pricing analysis results
    """
    total_records = len(df)
    
    # Extract and clean prices
    prices = extract_price_column(df, price_column)
    valid_price_count = len(prices)
    
    # Calculate statistics
    stats = calculate_price_statistics(prices)
    optimal_range = calculate_optimal_price_range(prices)
    
    # Calculate confidence: ratio of valid prices to total records
    confidence = valid_price_count / total_records if total_records > 0 else 0.0
    
    results = {
        "total_records": total_records,
        "valid_price_records": valid_price_count,
        "price_statistics": stats,
        "optimal_price_range": optimal_range
    }
    
    return {
        "agent_name": "pricing_agent",
        "results": results,
        "confidence": round(confidence, 4),
        "timestamp": datetime.now().isoformat()
    }

