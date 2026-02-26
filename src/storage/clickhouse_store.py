import clickhouse_driver
from clickhouse_driver import Client
from typing import List, Dict, Any, Union
from datetime import date, datetime
import pandas as pd

from ..core.models import Tick, Bar
from ..core.interfaces import DataStorage
from ..config import settings

class ClickHouseStorage(DataStorage):
    def __init__(self, host=settings.CLICKHOUSE_HOST, port=settings.CLICKHOUSE_PORT):
        self.client = Client(host=host, port=port, user=settings.CLICKHOUSE_USER, password=settings.CLICKHOUSE_PASSWORD, database=settings.CLICKHOUSE_DB)
        self._ensure_schema()

    def _ensure_schema(self):
        """Create necessary tables if they don't exist."""
        # Ticks table: Optimized for high write throughput
        self.client.execute("""
            CREATE TABLE IF NOT EXISTS rt_ticks (
                timestamp DateTime64(3),
                symbol String,
                price Float64,
                volume Float64,
                amount Float64,
                bid_price Array(Float64),
                bid_volume Array(Float64),
                ask_price Array(Float64),
                ask_volume Array(Float64)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMMDD(timestamp)
            ORDER BY (symbol, timestamp)
        """)

        # Bars table: For intraday bars
        self.client.execute("""
            CREATE TABLE IF NOT EXISTS rt_bars (
                timestamp DateTime64(0),
                symbol String,
                open Float64,
                high Float64,
                low Float64,
                close Float64,
                volume Float64,
                amount Float64,
                frequency String
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMMDD(timestamp)
            ORDER BY (symbol, frequency, timestamp)
        """)

    def save_ticks(self, ticks: List[Tick]):
        if not ticks:
            return
        
        # Convert Pydantic models to dicts for insertion
        data = [
            {
                'timestamp': t.dt,
                'symbol': t.symbol,
                'price': t.price,
                'volume': t.volume,
                'amount': t.amount or 0.0,
                'bid_price': t.bid_price,
                'bid_volume': t.bid_volume,
                'ask_price': t.ask_price,
                'ask_volume': t.ask_volume
            }
            for t in ticks
        ]
        
        self.client.execute('INSERT INTO rt_ticks VALUES', data)

    def save_bars(self, data: pd.DataFrame, symbol: str, frequency: str):
        # Convert DataFrame to list of dicts
        # Ensure 'dt' is a column
        if 'dt' not in data.columns and isinstance(data.index, pd.DatetimeIndex):
            data = data.reset_index()
            
        rows = []
        for _, row in data.iterrows():
            rows.append({
                'timestamp': row['dt'],
                'symbol': symbol,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'amount': row.get('amount', 0.0),
                'frequency': frequency
            })
            
        self.client.execute('INSERT INTO rt_bars VALUES', rows)

    def load_bars(self, symbol: str, start: Union[date, datetime], end: Union[date, datetime], frequency: str) -> pd.DataFrame:
        query = f"""
            SELECT timestamp, open, high, low, close, volume, amount 
            FROM rt_bars 
            WHERE symbol = '{symbol}' 
              AND frequency = '{frequency}'
              AND timestamp >= '{start}' 
              AND timestamp <= '{end}'
            ORDER BY timestamp
        """
        result = self.client.execute(query)
        df = pd.DataFrame(result, columns=['dt', 'open', 'high', 'low', 'close', 'volume', 'amount'])
        df.set_index('dt', inplace=True)
        return df
