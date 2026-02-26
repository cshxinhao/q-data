import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.checker.validators import SimpleChecker
from src.checker.china_rules import get_board_type, calculate_price_limit

def test_logic_consistency():
    print("Testing Logic Consistency...")
    checker = SimpleChecker()
    
    # Create sample data
    data = pd.DataFrame({
        'open': [10.0, 10.0, 10.0],
        'high': [9.0, 12.0, 12.0],   # Row 0: High(9) < Open(10) -> Error
        'low':  [9.0, 13.0, 9.0],    # Row 1: Low(13) > High(12) -> Error
        'close': [9.0, 11.0, 11.0],
        'volume': [100, 100, -10],   # Row 2: Volume < 0 -> Error
        'vwap': [9.0, 11.5, 10.0]    
    })
    # Add dummy index
    data.index = pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
    
    res = checker.check_logic_consistency(data)
    print("Found inconsistencies:", len(res))
    print(res[['reason']])
    
    # We expect errors in all 3 rows
    # Row 0: High < Open
    # Row 1: Low > High (High < Low)
    # Row 2: Volume < 0
    assert len(res) >= 3

def test_price_limits():
    print("\nTesting Price Limits...")
    checker = SimpleChecker()
    
    # Test cases
    # 1. Main Board Normal (10%) - 2024 (Post-Reg)
    # 2. STAR (20%)
    # 3. ChiNext (20% after 2020)
    
    dates = pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
    data = pd.DataFrame({
        'trade_date': dates,
        'ts_code': ['600000.SH', '688001.SH', '300001.SZ'],
        'pre_close': [10.0, 10.0, 10.0],
        'close': [11.15, 12.15, 12.15], # 11.5% (>10%), 21.5% (>20%), 21.5% (>20%)
        'is_st': [False, False, False]
    })
    
    # Calculate limits manually to verify
    limits = calculate_price_limit(data)
    print("Limits:\n", limits)
    
    res = checker.check_price_limit(data)
    print("Violations:\n", res[['ts_code', 'limit_val', 'pct_change', 'reason']])
    
    # Expect all 3 to be violations
    assert len(res) == 3

    # Test IPO Day 1 (Unlimited)
    print("\nTesting IPO Rules...")
    data_ipo = pd.DataFrame({
        'trade_date': pd.to_datetime(['2024-01-01']),
        'ts_code': ['600000.SH'],
        'list_date': pd.to_datetime(['2024-01-01']),
        'pre_close': [10.0],
        'close': [20.0], # 100% change
        'is_st': [False]
    })
    
    res_ipo = checker.check_price_limit(data_ipo)
    print("IPO Violations (Should be empty):", res_ipo)
    assert res_ipo.empty

if __name__ == "__main__":
    test_logic_consistency()
    test_price_limits()
    print("\nAll tests passed!")
