from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional, Any, Union
from datetime import date, datetime
import pandas as pd

from .models import Tick, Bar, Contract, TradeCalendar, Adjustment, Fundamental


class DataProvider(ABC):
    """
    Abstract Base Class for Data Vendors (Tushare, IB, etc.)
    """

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        start: Union[date, datetime],
        end: Union[date, datetime],
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """
        Download historical bars.
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
        self, exchange: str, start: Union[date, datetime], end: Union[date, datetime]
    ) -> List[TradeCalendar]:
        """
        Get trading calendar.
        """
        pass

    @abstractmethod
    def get_adjustments(
        self, symbol: str, start: Union[date, datetime], end: Union[date, datetime]
    ) -> List[Adjustment]:
        """
        Get splits and dividends.
        """
        pass

    @abstractmethod
    def get_fundamentals(
        self, symbol: str, date: Union[date, datetime]
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
    def save_bars(self, data: pd.DataFrame, symbol: str, frequency: str):
        """
        Save bars to storage.
        """
        pass

    @abstractmethod
    def load_bars(
        self,
        symbol: str,
        start: Union[date, datetime],
        end: Union[date, datetime],
        frequency: str,
    ) -> pd.DataFrame:
        """
        Load bars from storage.
        """
        pass

    @abstractmethod
    def save_ticks(self, ticks: List[Tick]):
        """
        Save ticks (likely to real-time DB).
        """
        pass
