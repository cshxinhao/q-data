from typing import List, Union
from datetime import date, datetime
import pandas as pd
import numpy as np
from .base import DataChecker
from .china_rules import calculate_price_limit


class SimpleChecker(DataChecker):
    def check_continuity(
        self,
        data: pd.DataFrame,
        start: Union[date, datetime],
        end: Union[date, datetime],
        calendar: List[date],
    ) -> List[str]:
        if data.empty:
            return [d.isoformat() for d in calendar if start <= d <= end]

        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            if "dt" in data.columns:
                data = data.set_index("dt")
            else:
                raise ValueError("Data must have datetime index or 'dt' column")

        # Get unique dates from data
        data_dates = set(data.index.normalize().date)

        # Filter calendar for range
        start_date = start.date() if isinstance(start, datetime) else start
        end_date = end.date() if isinstance(end, datetime) else end

        expected_dates = [d for d in calendar if start_date <= d <= end_date]

        missing = []
        for d in expected_dates:
            if d not in data_dates:
                missing.append(d.isoformat())

        return missing

    def check_outliers_for_single_stock(
        self, data: pd.DataFrame, threshold: float = 0.2
    ) -> pd.DataFrame:
        if data.empty:
            return pd.DataFrame()

        # Check price jumps: abs(close / prev_close - 1) > threshold
        pct_change = data["close"].pct_change().abs()
        outliers = data[pct_change > threshold]

        return outliers

    def check_volume(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            return pd.DataFrame()

        # Check for zero volume (suspicious for active stocks)
        zero_vol = data[data["volume"] == 0]
        return zero_vol

    def check_logic_consistency(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            return pd.DataFrame()

        required = ["open", "high", "low", "close", "volume"]
        # Relax requirement: only check what is present?
        # But 'high >= low' requires both.
        # Let's check essential OHLC.
        if not all(col in data.columns for col in required):
            # Try to check partial?
            # For now, return empty if essential columns missing to avoid crash
            return pd.DataFrame()

        inconsistencies = []

        # High >= Open, High >= Close, High >= Low
        mask_high = (
            (data["high"] < data["open"])
            | (data["high"] < data["close"])
            | (data["high"] < data["low"])
        )

        if mask_high.any():
            inv_high = data[mask_high].copy()
            inv_high["reason"] = "High < Open/Close/Low"
            inconsistencies.append(inv_high)

        # Low <= Open, Low <= Close
        mask_low = (data["low"] > data["open"]) | (data["low"] > data["close"])

        if mask_low.any():
            inv_low = data[mask_low].copy()
            inv_low["reason"] = "Low > Open/Close"
            inconsistencies.append(inv_low)

        # Volume >= 0
        mask_vol = data["volume"] < 0
        if mask_vol.any():
            inv_vol = data[mask_vol].copy()
            inv_vol["reason"] = "Volume < 0"
            inconsistencies.append(inv_vol)

        # Amount >= 0
        if "amount" in data.columns:
            mask_amt = data["amount"] < 0
            if mask_amt.any():
                inv_amt = data[mask_amt].copy()
                inv_amt["reason"] = "Amount < 0"
                inconsistencies.append(inv_amt)

        # VWAP Logic
        if "vwap" in data.columns:
            tolerance = 1e-4
            mask_vwap = (data["vwap"] < data["low"] * (1 - tolerance)) | (
                data["vwap"] > data["high"] * (1 + tolerance)
            )

            if mask_vwap.any():
                inv_vwap = data[mask_vwap].copy()
                inv_vwap["reason"] = "VWAP out of [Low, High]"
                inconsistencies.append(inv_vwap)

        if inconsistencies:
            return pd.concat(inconsistencies)

        return pd.DataFrame()

    def check_price_limit(self, data: pd.DataFrame, market: str) -> pd.DataFrame:

        if market == "China":
            if data.empty:
                return pd.DataFrame()

            try:
                limits = calculate_price_limit(data)
            except ValueError:
                return pd.DataFrame()

            # Calculate percentage change
            if "pre_close" in data.columns:
                pct_change = (data["close"] / data["pre_close"] - 1).abs()
            else:
                pct_change = data["close"].pct_change().abs()

            # Check against limit
            tolerance = 0.001

            # Identify violations
            mask_violation = (pct_change > limits + tolerance) & (limits != np.inf)

            if mask_violation.any():
                result = data[mask_violation].copy()
                result["limit_val"] = limits[mask_violation]
                result["pct_change"] = pct_change[mask_violation]
                result["reason"] = "Price limit exceeded"
                return result

            return pd.DataFrame()
