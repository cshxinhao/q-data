import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, date
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.models import Bar, Tick
from src.vendors.tushare_provider import TushareProvider
from src.vendors.xt_provider import XtProvider

class TestStandardization(unittest.TestCase):
    def test_models_have_datetime(self):
        """Verify Bar and Tick models use datetime instead of dt"""
        bar = Bar(
            symbol="000001.SZ",
            datetime=datetime.now(),
            open=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=1000,
            amount=10500,
            vwap=10.5
        )
        self.assertEqual(bar.symbol, "000001.SZ")
        self.assertTrue(hasattr(bar, "datetime"))
        self.assertFalse(hasattr(bar, "dt"))

        tick = Tick(
            symbol="000001.SZ",
            datetime=datetime.now(),
            price=10.5,
            volume=100
        )
        self.assertTrue(hasattr(tick, "datetime"))
        self.assertFalse(hasattr(tick, "dt"))

    @patch("src.vendors.tushare_provider.ts")
    def test_tushare_kline_standardization(self, mock_ts):
        """Verify Tushare provider standardizes columns and preserves extra ones"""
        # Mock pro API
        mock_pro = MagicMock()
        mock_ts.pro_api.return_value = mock_pro
        
        # Mock return data
        data = {
            "trade_date": ["20230101"],
            "ts_code": ["000001.SZ"],
            "open": [10.0],
            "high": [11.0],
            "low": [9.0],
            "close": [10.5],
            "vol": [1000],
            "amount": [10500.0],
            "pre_close": [9.8],  # Extra column
            "pct_chg": [7.14]    # Extra column
        }
        df_mock = pd.DataFrame(data)
        mock_pro.daily.return_value = df_mock
        
        provider = TushareProvider(token="mock_token")
        
        # Test get_kline_per_day
        df = provider.get_kline_per_day(date(2023, 1, 1))
        
        # Check standard columns
        self.assertIn("datetime", df.columns)
        self.assertIn("symbol", df.columns)
        self.assertIn("volume", df.columns)
        self.assertIn("vwap", df.columns)
        
        # Check values
        self.assertEqual(df.iloc[0]["symbol"], "000001.SZ")
        self.assertEqual(df.iloc[0]["volume"], 1000)
        self.assertEqual(df.iloc[0]["vwap"], 10.5)
        
        # Check extra columns preserved
        self.assertIn("pre_close", df.columns)
        self.assertIn("pct_chg", df.columns)
        self.assertEqual(df.iloc[0]["pre_close"], 9.8)

    @patch("src.vendors.xt_provider.xtdata")
    def test_xt_kline_standardization(self, mock_xtdata):
        """Verify Xt provider standardizes columns and preserves extra ones"""
        # Mock xtdata
        # get_market_data returns dict of {symbol: data}
        # data can be list of records or dict of arrays
        
        data_mock = {
            "time": [1672531200000], # 2023-01-01
            "open": [10.0],
            "high": [11.0],
            "low": [9.0],
            "close": [10.5],
            "volume": [1000],
            "amount": [10500.0],
            "extra_field": [123] # Extra field
        }
        
        mock_xtdata.get_market_data.return_value = {"000001.SZ": data_mock}
        
        provider = XtProvider()
        
        df = provider.get_kline_per_symbol(
            "000001.SZ", 
            date(2023, 1, 1), 
            date(2023, 1, 2)
        )
        
        # Check standard columns
        self.assertIn("datetime", df.columns)
        self.assertIn("symbol", df.columns)
        self.assertIn("vwap", df.columns)
        
        # Check values
        self.assertEqual(df.iloc[0]["symbol"], "000001.SZ")
        self.assertEqual(df.iloc[0]["vwap"], 10.5)
        
        # Check extra columns preserved
        self.assertIn("extra_field", df.columns)
        self.assertEqual(df.iloc[0]["extra_field"], 123)

    @patch("src.vendors.tushare_provider.ts")
    def test_tushare_fundamentals_mapping(self, mock_ts):
        """Verify Tushare fundamentals map total_mv to total_market_cap"""
        mock_pro = MagicMock()
        mock_ts.pro_api.return_value = mock_pro
        
        data = {
            "ts_code": ["000001.SZ"],
            "trade_date": ["20230101"],
            "total_mv": [100000.0],
            "pe": [10.5]
        }
        df_mock = pd.DataFrame(data)
        mock_pro.daily_basic.return_value = df_mock
        
        provider = TushareProvider(token="mock_token")
        funds = provider.get_fundamentals("000001.SZ", date(2023, 1, 1))
        
        # Check if one of the fundamentals is total_market_cap
        fields = [f.field for f in funds]
        self.assertIn("total_market_cap", fields)
        self.assertNotIn("mkt_cap", fields)
        
        # Check value
        for f in funds:
            if f.field == "total_market_cap":
                self.assertEqual(f.value, 100000.0)

if __name__ == "__main__":
    unittest.main()
