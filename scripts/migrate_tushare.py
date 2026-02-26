# One-time script to migrate tushare data to parquet format
import logging
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from src.core.models import Bar
from src.vendors.tushare_provider import TushareProvider
from src.storage.parquet_store import ParquetStorage
from src.config import settings

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def migrate_kline_by_date(
    start_date: str,
    end_date: str,
):
    """Migrate tushare data from previous path to new parquet path and format."""
    store = ParquetStorage(vendor="tushare", frequency="1d", replace_existing=True)

    # Get all dates to process
    for date in pd.date_range(start=start_date, end=end_date, freq="B").date:
        old_path = (
            Path(r"D:\source_data\tushare\bar_price\1day")
            / f"{date.isoformat()}.parquet"
        )
        df = pd.read_parquet(old_path)

        # Preprocess
        df = df.rename(
            columns={
                "trade_date": "datetime",
                "vol": "volume",
                "ts_code": "symbol",
            }
        )

        # Unit
        df["volume"] *= 100
        df["amount"] *= 1000

        # Add columns
        df["datetime"] = pd.to_datetime(df["datetime"])
        df["frequency"] = "1d"
        df["vwap"] = df["amount"] / df["volume"]

        # Save
        store.save_kline_for_date(df, date)


if __name__ == "__main__":
    migrate_kline_by_date(
        start_date="2012-01-01",
        end_date="2026-02-26",
    )
