from typing import List, Union
from datetime import date, datetime
import pandas as pd
import numpy as np
from .base import DataChecker

class SimpleChecker(DataChecker):
    def check_continuity(
        self, 
        data: pd.DataFrame, 
        start: Union[date, datetime], 
        end: Union[date, datetime], 
        calendar: List[date]
    ) -> List[str]:
        if data.empty:
            return [d.isoformat() for d in calendar if start <= d <= end]

        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'dt' in data.columns:
                data = data.set_index('dt')
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

    def check_outliers(
        self, 
        data: pd.DataFrame, 
        threshold: float = 0.2
    ) -> pd.DataFrame:
        if data.empty:
            return pd.DataFrame()
            
        # Check price jumps: abs(close / prev_close - 1) > threshold
        pct_change = data['close'].pct_change().abs()
        outliers = data[pct_change > threshold]
        
        return outliers

    def check_volume(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            return pd.DataFrame()
            
        # Check for zero volume (suspicious for active stocks)
        zero_vol = data[data['volume'] == 0]
        return zero_vol
