"""
Test Script for Analytical Agents

Simple test script to verify all agents work correctly with sample data.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.ingestion import read_csv_file
from core.validator import validate_and_clean
from agents.brand_agent import analyze_brands
from agents.pricing_agent import analyze_pricing
from agents.feature_agent import analyze_features
from agents.gap_agent import analyze_gaps


def print_json_pretty(data: dict, title: str = ""):
    """Print JSON data in a readable format."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_ingestion():
    """Test CSV file ingestion."""
    print("\n[TEST 1] Testing CSV Ingestion...")
    try:
        df = read_csv_file("test_data.csv")
        print(f"[PASS] Successfully loaded CSV: {len(df)} rows, {len(df.columns)} columns")
        print(f"  Columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        return None


def test_validation(df):
    """Test data validation and cleaning."""
    print("\n[TEST 2] Testing Data Validation...")
    try:
        cleaned_df = validate_and_clean(
            df, 
            cleaning_strategy="drop_rows",
            remove_dupes=True
        )
        print(f"[PASS] Validation successful: {len(cleaned_df)} rows after cleaning")
        return cleaned_df
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        return None


def test_brand_agent(df):
    """Test brand agent."""
    print("\n[TEST 3] Testing Brand Agent...")
    try:
        result = analyze_brands(df, brand_column="brand", top_n=5)
        print(f"[PASS] Brand agent executed successfully")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Top brands found: {len(result['results']['top_brands'])}")
        print_json_pretty(result, "Brand Agent Output")
        return result
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pricing_agent(df):
    """Test pricing agent."""
    print("\n[TEST 4] Testing Pricing Agent...")
    try:
        result = analyze_pricing(df, price_column="price")
        print(f"[PASS] Pricing agent executed successfully")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Min Price: ${result['results']['price_statistics']['min_price']:.2f}")
        print(f"  Max Price: ${result['results']['price_statistics']['max_price']:.2f}")
        print_json_pretty(result, "Pricing Agent Output")
        return result
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_feature_agent(df):
    """Test feature agent."""
    print("\n[TEST 5] Testing Feature Agent...")
    try:
        result = analyze_features(df, feature_column="feature", top_n=10)
        print(f"[PASS] Feature agent executed successfully")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Top features found: {len(result['results']['top_features'])}")
        print_json_pretty(result, "Feature Agent Output")
        return result
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_gap_agent(df):
    """Test gap agent."""
    print("\n[TEST 6] Testing Gap Agent...")
    try:
        result = analyze_gaps(
            df, 
            brand_column="brand",
            feature_column="feature",
            gap_threshold=-0.5,
            top_n=5
        )
        print(f"[PASS] Gap agent executed successfully")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Gaps identified: {result['results']['identified_gaps_count']}")
        print_json_pretty(result, "Gap Agent Output")
        return result
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all agent tests."""
    print("="*60)
    print("  TrendScanner AI - Agent Testing")
    print("="*60)
    
    # Test 1: Ingestion
    df = test_ingestion()
    if df is None:
        print("\n✗ Cannot proceed without data. Exiting.")
        return
    
    # Test 2: Validation
    cleaned_df = test_validation(df)
    if cleaned_df is None:
        print("\n✗ Validation failed. Exiting.")
        return
    
    # Test 3-6: Agents
    brand_result = test_brand_agent(cleaned_df)
    pricing_result = test_pricing_agent(cleaned_df)
    feature_result = test_feature_agent(cleaned_df)
    gap_result = test_gap_agent(cleaned_df)
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"Ingestion:      {'[PASS]' if df is not None else '[FAIL]'}")
    print(f"Validation:     {'[PASS]' if cleaned_df is not None else '[FAIL]'}")
    print(f"Brand Agent:    {'[PASS]' if brand_result is not None else '[FAIL]'}")
    print(f"Pricing Agent:  {'[PASS]' if pricing_result is not None else '[FAIL]'}")
    print(f"Feature Agent:  {'[PASS]' if feature_result is not None else '[FAIL]'}")
    print(f"Gap Agent:      {'[PASS]' if gap_result is not None else '[FAIL]'}")
    
    all_passed = all([
        df is not None,
        cleaned_df is not None,
        brand_result is not None,
        pricing_result is not None,
        feature_result is not None,
        gap_result is not None
    ])
    
    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED!")
    else:
        print("\n[ERROR] SOME TESTS FAILED")
    
    print("="*60)


if __name__ == "__main__":
    main()

