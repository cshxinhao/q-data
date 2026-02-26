import click
import time
from datetime import date as cdate, datetime as cdatetime
import logging
from typing import List
import pandas as pd

from .config import settings
from .vendors.tushare_provider import TushareProvider
from .vendors.xt_provider import XtProvider
from .storage.parquet_store import ParquetStorage
from .storage.clickhouse_store import ClickHouseStorage
from .jobs.consolidate import consolidate_daily
from .checker.validators import SimpleChecker

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("q-data")


@click.group()
def cli():
    pass


def try_n_times(task: callable, n: int = 3, seconds: int = 5, **kwargs) -> any:
    """Try a task n times with delay between each try."""
    for i in range(n):
        try:
            result = task(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Attempt {i + 1} failed: {e}")
            if i < n - 1:
                time.sleep(seconds)
    return None


@cli.command()
@click.option(
    "--vendor", type=click.Choice(["tushare", "xt", "ib", "futu"]), required=True
)
@click.option("--start", required=True, help="YYYY-MM-DD")
@click.option("--end", required=True, help="YYYY-MM-DD")
@click.option("--frequency", default="1d", help="1d, 1m, 1h")
def download_cs_range(vendor, start, end, frequency):
    """Download historical data: cross-sectionally for a range of dates."""
    start_dt = cdatetime.strptime(start, "%Y-%m-%d")
    end_dt = cdatetime.strptime(end, "%Y-%m-%d")

    if vendor == "tushare":
        provider = TushareProvider()
    elif vendor == "xt":
        provider = XtProvider()
    else:
        click.echo("Vendor not implemented yet")
        return

    if frequency != "1d":
        raise NotImplementedError(
            "Only daily frequency supported for cross-section download"
        )

    logger.info(f"Downloading {vendor} {frequency} from {start} to {end}...")

    # Check data integrity after downloading for all days?
    # Or check data integrity for each day?
    # If check for each day, we can save the data for each day to Parquet.
    # If check after downloading for all days, we can save the data for all days to Parquet.
    # Let's check & save for each day first

    checker = SimpleChecker()
    store = ParquetStorage(vendor=vendor, frequency=frequency)
    for date in reversed(pd.date_range(start_dt, end_dt, freq="B").date):
        path = store._get_path_by_date(date)
        if path.exists():
            logger.warning(f"File {path} already exists. Skip.")
            continue

        df = try_n_times(
            task=provider.get_kline_per_date,
            n=5,
            seconds=10,
            date=date,
        )

        if df is None:
            logger.warning(f"Failed downloading {frequency} kline for {date}")
            continue

        zero_volume_records = checker.check_volume(df)
        if not zero_volume_records.empty:
            logger.warning(f"Found {len(zero_volume_records)} zero volume records.")

        # Save
        store.save_kline_for_date(df, date)

        time.sleep(1)  # prevent from downloading too fast


@cli.command()
@click.option("--vendor", type=click.Choice(["xt", "ib", "futu"]), required=True)
@click.option("--symbols", required=True, help="Comma separated symbols")
def subscribe(vendor, symbols):
    """Subscribe to real-time ticks."""
    symbol_list = symbols.split(",")

    if vendor == "xt":
        provider = XtProvider()
    else:
        click.echo("Only XtQuant supported for real-time in MVP")
        return

    ch_store = ClickHouseStorage()

    def on_tick(tick):
        # Print to console
        click.echo(f"{tick.dt} {tick.symbol} {tick.price}")
        # Save to ClickHouse
        ch_store.save_ticks([tick])

    logger.info(f"Subscribing to {symbol_list}...")
    provider.subscribe(symbol_list, on_tick)

    # Keep alive
    import time

    while True:
        time.sleep(1)


@cli.command()
@click.option("--date", required=True, help="YYYY-MM-DD")
def consolidate(date):
    """Run EOD consolidation."""
    target_date = cdatetime.strptime(date, "%Y-%m-%d").date()
    consolidate_daily(target_date)


if __name__ == "__main__":
    cli()
