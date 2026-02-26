import tushare as ts
import pandas as pd
from typing import List, Union, Dict, Callable, Any
from datetime import date as cdate, datetime as cdatetime

from ..core.interfaces import DataProvider
from ..core.models import (
    Bar,
    Tick,
    TradeCalendar,
    Adjustment,
    Fundamental,
    Exchange,
    AdjustmentType,
)
from ..config import settings


class TushareProvider(DataProvider):
    def __init__(self, token: str = None):
        self.token = token or settings.TUSHARE_TOKEN
        if not self.token:
            raise ValueError("Tushare token is required")
        self.pro = ts.pro_api(self.token)

    def get_kline_per_date(
        self,
        date: cdate,
    ) -> pd.DataFrame:
        date_str = date.strftime("%Y%m%d")

        df = self.pro.daily(trade_date=date_str)

        # Rename columns to match Bar model
        # Tushare: trade_date, open, high, low, close, vol, amount
        df = df.rename(
            columns={
                "trade_date": "datetime",
                "vol": "volume",
                "ts_code": "symbol",
            }
        )

        df["datetime"] = pd.to_datetime(df["datetime"])
        df["frequency"] = "1d"
        df["vwap"] = df["amount"] / df["volume"]

        # Select standard columns
        # cols = ["datetime", "open", "high", "low", "close", "vwap", "volume", "amount"]
        # Return all columns to preserve vendor-specific fields
        return df.sort_values("datetime")

    def get_kline_per_symbol(
        self,
        symbol: str,
        start: Union[cdate, cdatetime],
        end: Union[cdate, cdatetime],
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """
        (Not recommended for Tushare) Get daily kline data for a single symbol.

        Args:
            symbol: Stock symbol (e.g., "000001.SZ")
            start: Start date
            end: End date
            frequency: Must be "1d" for daily data

        Returns:
            DataFrame with columns: dt, open, high, low, close, volume, amount
        """

        # Convert symbol (e.g., 000001.SZ)
        # Tushare expects YYYYMMDD
        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")

        if frequency == "1d":
            df = self.pro.daily(ts_code=symbol, start_date=start_str, end_date=end_str)
        else:
            raise NotImplementedError("Only daily data supported for Tushare MVP")

        if df.empty:
            return pd.DataFrame()

        # Rename columns to match Bar model
        # Tushare: trade_date, open, high, low, close, vol, amount
        df = df.rename(
            columns={
                "trade_date": "datetime",
                "vol": "volume",
                "ts_code": "symbol",
            }
        )

        df["datetime"] = pd.to_datetime(df["datetime"])
        df["frequency"] = frequency
        df["vwap"] = df["amount"] / df["volume"]

        # Unit
        df["volume"] *= 100
        df["amount"] *= 1000

        # Select standard columns
        # cols = ["datetime", "open", "high", "low", "close", "vwap", "volume", "amount"]
        # Return all columns to preserve vendor-specific fields
        return df.sort_values("datetime")

    def get_snapshot(self, symbols: List[str]) -> Dict[str, Tick]:
        # Tushare doesn't provide real-time snapshot via standard API easily without credits
        # Using tushare.get_realtime_quotes() (legacy)
        df = ts.get_realtime_quotes(symbols)
        ticks = {}
        for _, row in df.iterrows():
            symbol = row["code"]  # Note: need to handle suffix
            # Simple conversion
            tick = Tick(
                symbol=symbol,
                datetime=cdatetime.now(),  # Approximate
                price=float(row["price"]),
                volume=float(row["volume"]),
                amount=float(row["amount"]),
                bid_price=[float(row["b1_p"])],
                bid_volume=[float(row["b1_v"])],
                ask_price=[float(row["a1_p"])],
                ask_volume=[float(row["a1_v"])],
            )
            ticks[symbol] = tick
        return ticks

    def subscribe(self, symbols: List[str], callback: Callable[[Tick], None]):
        raise NotImplementedError("Tushare does not support real-time subscription")

    def get_calendar(
        self, exchange: str, start: Union[cdate, cdatetime], end: Union[cdate, cdatetime]
    ) -> List[TradeCalendar]:
        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")

        # Tushare exchange mapping
        ex_map = {Exchange.SSE: "SSE", Exchange.SZSE: "SZSE"}
        ts_ex = ex_map.get(exchange, "SSE")

        df = self.pro.trade_cal(exchange=ts_ex, start_date=start_str, end_date=end_str)

        calendars = []
        for _, row in df.iterrows():
            calendars.append(
                TradeCalendar(
                    exchange=Exchange(exchange),
                    date=pd.to_datetime(row["cal_date"]).date(),
                    is_trading=bool(row["is_open"]),
                )
            )
        return calendars

    def get_adjustments(
        self, symbol: str, start: Union[cdate, cdatetime], end: Union[cdate, cdatetime]
    ) -> List[Adjustment]:
        # Tushare adj_factor
        df = self.pro.adj_factor(
            ts_code=symbol,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )
        adjs = []
        for _, row in df.iterrows():
            # This is cumulative factor, might need conversion to split ratio event if needed
            # For MVP, storing raw factor
            adjs.append(
                Adjustment(
                    symbol=symbol,
                    date=pd.to_datetime(row["trade_date"]).date(),
                    type=AdjustmentType.SPLIT,  # Simplified
                    factor=float(row["adj_factor"]),
                )
            )
        return adjs

    def get_fundamentals(
        self, symbol: str, date: Union[cdate, cdatetime]
    ) -> List[Fundamental]:
        date_str = date.strftime("%Y%m%d")
        df = self.pro.daily_basic(ts_code=symbol, trade_date=date_str)

        funds = []
        if not df.empty:
            row = df.iloc[0]
            # Map fields
            fields = {"total_mv": "total_market_cap", "pe": "pe", "pb": "pb"}
            for ts_field, model_field in fields.items():
                if ts_field in row:
                    funds.append(
                        Fundamental(
                            symbol=symbol,
                            date=date,
                            field=model_field,
                            value=float(row[ts_field]),
                        )
                    )
        return funds
    