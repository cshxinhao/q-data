import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import date as cdate, datetime as cdatetime
from typing import Union, List, Optional
import os
import warnings
import logging


from ..core.models import Tick, Bar
from ..core.interfaces import DataStorage
from ..config import settings


# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ParquetStorage(DataStorage):
    def __init__(
        self,
        vendor: str,
        frequency: str,
        root_dir: Optional[Path] = None,
        replace_existing: bool = False,
    ):
        self.root_dir = root_dir or settings.PARQUET_ROOT / frequency / vendor
        self.replace_existing = replace_existing
        warnings.warn("!! Replace existing files if they exist.")

    def _get_path_by_symbol(self, symbol: str) -> Path:
        """
        Partition strategy: frequency / symbol.parquet
        Example: data/history/1d/000001.SZ.parquet
        """
        return self.root_dir / "by_symbol" / f"{symbol}.parquet"

    def _get_path_by_date(self, date: cdate) -> Path:
        """
        Partition strategy: frequency / date.parquet
        Example: data/history/1d/2023-01-01.parquet
        """
        return self.root_dir / "by_date" / f"{date.isoformat()}.parquet"

    def save_kline_for_date(self, data: pd.DataFrame, date: cdate):
        path = self._get_path_by_date(date)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists() and not self.replace_existing:
            warnings.warn(f"File {path} already exists. Skip.")
        else:
            data.to_parquet(path)
            logger.info(f"{date}: Saved {len(data)} records to Parquet.")

    def load_kline_for_date(self, date: cdate) -> pd.DataFrame:
        path = self._get_path_by_date(date)
        if not path.exists():
            return pd.DataFrame()

        # Read parquet
        df = pd.read_parquet(path)

        return df

    def save_kline_for_symbol(self, data: pd.DataFrame, symbol: str):
        path = self._get_path_by_symbol(symbol)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to parquet
        # If file exists, we might want to append or overwrite.
        # For simplicity in MVP, we overwrite or merge.
        # Here we implement a merge strategy: load existing, combine, dedup, save.

        if path.exists() and not self.replace_existing:
            existing_df = pd.read_parquet(path)
            combined = pd.concat([existing_df, data])
            # Drop duplicates based on index (dt)
            combined = combined[~combined.index.duplicated(keep="last")]
            combined.sort_index(inplace=True)
            combined.to_parquet(path)
        else:
            data.sort_index(inplace=True)
            data.to_parquet(path)

    def load_kline_for_symbol(
        self,
        symbol: str,
        start: Union[cdate, cdatetime],
        end: Union[cdate, cdatetime],
    ) -> pd.DataFrame:
        path = self._get_path_by_symbol(symbol)
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
