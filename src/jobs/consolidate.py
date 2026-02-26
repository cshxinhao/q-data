import pandas as pd
from datetime import date, datetime, timedelta
import logging

from ..storage.clickhouse_store import ClickHouseStorage
from ..storage.parquet_store import ParquetStorage
from ..checker.validators import SimpleChecker
from ..config import settings

logger = logging.getLogger(__name__)

def consolidate_daily(target_date: date):
    """
    Consolidate real-time bars from ClickHouse to Parquet.
    Validate data before saving.
    """
    logger.info(f"Starting consolidation for {target_date}")
    
    ch_store = ClickHouseStorage()
    pq_store = ParquetStorage()
    checker = SimpleChecker()
    
    # 1. Get list of symbols traded today (from CH)
    # This query assumes we have data in rt_bars
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    query = f"""
        SELECT DISTINCT symbol FROM rt_bars 
        WHERE timestamp >= '{start_dt}' AND timestamp <= '{end_dt}'
    """
    symbols = [row[0] for row in ch_store.client.execute(query)]
    
    logger.info(f"Found {len(symbols)} symbols to consolidate")
    
    for symbol in symbols:
        try:
            # 2. Load bars from CH
            df = ch_store.load_bars(symbol, start_dt, end_dt, frequency='1m')
            
            if df.empty:
                continue
                
            # 3. Validate
            # Check for outliers
            outliers = checker.check_outliers(df)
            if not outliers.empty:
                logger.warning(f"Outliers detected for {symbol} on {target_date}: {len(outliers)}")
                # Depending on policy, we might filter them or just log
                
            # 4. Resample to Daily (if needed) or keep 1m
            # Here we save the 1m bars to parquet
            pq_store.save_bars(df, symbol, frequency='1m')
            
            # Also aggregate to 1d and save
            daily_df = df.resample('1D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'amount': 'sum'
            }).dropna()
            
            if not daily_df.empty:
                pq_store.save_bars(daily_df, symbol, frequency='1d')
                
        except Exception as e:
            logger.error(f"Failed to consolidate {symbol}: {e}")
            
    logger.info("Consolidation complete")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        d = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    else:
        d = date.today()
    consolidate_daily(d)
