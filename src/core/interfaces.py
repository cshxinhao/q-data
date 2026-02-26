from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional, Any, Union
from datetime import date as cdate, datetime as cdatetime
import pandas as pd

from .models import Tick, Bar, Contract, TradeCalendar, Adjustment, Fundamental


class DataProvider(ABC):
    """
    Abstract Base Class for Data Vendors (Tushare, IB, etc.)
    """

    @abstractmethod
    def get_kline_per_date(
        self,
        date: cdate,
    ) -> pd.DataFrame:
        """
        Download historical kline bars for a specific day.
        Returns a DataFrame with columns matching Bar fields.
        """
        pass

    @abstractmethod
    def get_kline_per_symbol(
        self,
        symbol: str,
        start: Union[cdate, cdatetime],
        end: Union[cdate, cdatetime],
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """
        Download historical kline bars for a specific symbol.
        Returns a DataFrame with columns matching Bar fields.
        """
        pass

    @abstractmethod
    def get_snapshot(self, symbols: List[str]) -> Dict[str, Tick]:
        """
        Get latest tick/quote for symbols.
        """
        pass

    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable[[Tick], None]):
        """
        Subscribe to real-time tick data.
        Callback is called with each new Tick.
        """
        pass

    # Reference Data
    @abstractmethod
    def get_calendar(
        self,
        exchange: str,
        start: Union[cdate, cdatetime],
        end: Union[cdate, cdatetime],
    ) -> List[TradeCalendar]:
        """
        Get trading calendar.
        """
        pass

    @abstractmethod
    def get_adjustments(
        self,
        symbol: str,
        start: Union[cdate, cdatetime],
        end: Union[cdate, cdatetime],
    ) -> List[Adjustment]:
        """
        Get splits and dividends.
        """
        pass

    @abstractmethod
    def get_fundamentals(
        self, symbol: str, date: Union[cdate, cdatetime]
    ) -> List[Fundamental]:
        """
        Get fundamental data for a specific date (or period).
        """
        pass


class DataStorage(ABC):
    """
    Abstract Base Class for Data Persistence (Parquet, DB, etc.)
    """

    @abstractmethod
    def save_kline_for_date(
        self, data: pd.DataFrame, date: cdate, frequency: str
    ):
        """
        Save kline bars for a specific date to storage.
        """
        pass

    @abstractmethod
    def load_kline_for_date(self, date: cdate, frequency: str) -> pd.DataFrame:
        """
        Load kline bars for a specific date from storage.
        """
        pass

    @abstractmethod
    def save_kline_for_symbol(self, data: pd.DataFrame, symbol: str, frequency: str):
        """
        Save kline bars for a specific symbol to storage.
        """
        pass

    @abstractmethod
    def load_kline_for_symbol(
        self,
        symbol: str,
        start: Union[cdate, cdatetime],
        end: Union[cdate, cdatetime],
        frequency: str,
    ) -> pd.DataFrame:
        """
        Load kline bars from storage.
        """
        pass

    @abstractmethod
    def save_ticks(self, ticks: List[Tick]):
        """
        Save ticks (likely to real-time DB).
        """
        pass
