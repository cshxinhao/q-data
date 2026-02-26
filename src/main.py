import click
from datetime import datetime, date
import logging
from typing import List

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


@cli.command()
@click.option(
    "--vendor", type=click.Choice(["tushare", "xt", "ib", "futu"]), required=True
)
@click.option("--symbol", required=True, help="Symbol (e.g., 000001.SZ)")
@click.option("--start", required=True, help="YYYY-MM-DD")
@click.option("--end", required=True, help="YYYY-MM-DD")
@click.option("--frequency", default="1d", help="1d, 1m")
def download(vendor, symbol, start, end, frequency):
    """Download historical data."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    if vendor == "tushare":
        provider = TushareProvider()
    elif vendor == "xt":
        provider = XtProvider()
    else:
        click.echo("Vendor not implemented yet")
        return

    logger.info(f"Downloading {symbol} from {start} to {end}...")
    df = provider.get_history(symbol, start_dt, end_dt, frequency)

    if df.empty:
        logger.warning("No data found.")
        return

    # Check data integrity
    checker = SimpleChecker()
    # Assume we have a calendar available (stub for now)
    # missing = checker.check_continuity(df, start_dt, end_dt, calendar=[])
    # if missing:
    #     logger.warning(f"Missing dates: {len(missing)}")

    outliers = checker.check_outliers(df)
    if not outliers.empty:
        logger.warning(f"Found {len(outliers)} outliers.")

    # Save
    store = ParquetStorage()
    store.save_bars(df, symbol, frequency)
    logger.info(f"Saved {len(df)} records to Parquet.")


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
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    consolidate_daily(target_date)


if __name__ == "__main__":
    cli()
