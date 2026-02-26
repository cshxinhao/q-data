import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import date, datetime
from typing import Union, List, Optional
import os

from ..core.models import Tick, Bar
from ..core.interfaces import DataStorage
from ..config import settings


class ParquetStorage(DataStorage):
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def _get_path_by_symbol(self, symbol: str, frequency: str) -> Path:
        """
        Partition strategy: frequency / symbol.parquet
        Example: data/history/1d/000001.SZ.parquet
        """
        return self.root_dir / frequency / f"{symbol}.parquet"

    def _get_path_by_date(self, date: date, frequency: str) -> Path:
        """
        Partition strategy: frequency / date.parquet
        Example: data/history/1d/2023-01-01.parquet
        """
        return self.root_dir / frequency / f"{date.isoformat()}.parquet"

    def save_kline_for_day(self, data: pd.DataFrame, frequency: str):
        if data.empty:
            return

        path = self._get_path_by_symbol("dummy", frequency)

    def save_kline_for_symbol(self, data: pd.DataFrame, symbol: str, frequency: str):
        if data.empty:
            return

        path = self._get_path_by_symbol(symbol, frequency)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure 'dt' is datetime and set as index if not already
        if "dt" in data.columns:
            data = data.set_index("dt")

        # Write to parquet
        # If file exists, we might want to append or overwrite.
        # For simplicity in MVP, we overwrite or merge.
        # Here we implement a merge strategy: load existing, combine, dedup, save.

        if path.exists():
            existing_df = pd.read_parquet(path)
            combined = pd.concat([existing_df, data])
            # Drop duplicates based on index (dt)
            combined = combined[~combined.index.duplicated(keep="last")]
            combined.sort_index(inplace=True)
            combined.to_parquet(path)
        else:
            data.sort_index(inplace=True)
            data.to_parquet(path)

    def load_bars(
        self,
        symbol: str,
        start: Union[date, datetime],
        end: Union[date, datetime],
        frequency: str,
    ) -> pd.DataFrame:
        path = self._get_path_by_symbol(symbol, frequency)
        if not path.exists():
            return pd.DataFrame()

        # Read parquet with filters
        # PyArrow dataset filtering is more efficient, but for single file pandas read is okay
        # To optimize, we can use filters in read_parquet if we partition by date.
        # Since we partition by symbol, we load the file and filter in memory.
        # For very large files, we should partition by Year/Month.

        df = pd.read_parquet(path)

        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Filter by date range
        mask = (df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))
        return df.loc[mask]

    def save_ticks(self, ticks: List[Tick]):
        # Parquet is not ideal for real-time tick writing.
        # This method is reserved for EOD consolidation.
        pass
