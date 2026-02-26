from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class Exchange(str, Enum):
    SSE = "SSE"  # Shanghai
    SZSE = "SZSE"  # Shenzhen
    HKEX = "HKEX"  # Hong Kong
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    CME = "CME"
    # Add more as needed


class SecurityType(str, Enum):
    STOCK = "STOCK"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    INDEX = "INDEX"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"


class Contract(BaseModel):
    symbol: str
    exchange: Exchange
    sec_type: SecurityType
    name: Optional[str] = None
    expiry: Optional[date] = None
    multiplier: float = 1.0
    strike: Optional[float] = None
    currency: str = "USD"

    model_config = ConfigDict(frozen=True)  # Make it hashable if needed


class Bar(BaseModel):
    symbol: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None  # Turnover
    open_interest: Optional[float] = None
    vwap: Optional[float] = None
    frequency: str = "1d"  # 1d, 1m, 5m, etc.


class Tick(BaseModel):
    symbol: str
    datetime: datetime
    price: float
    volume: float
    amount: Optional[float] = None
    bid_price: List[float] = Field(default_factory=list)
    bid_volume: List[float] = Field(default_factory=list)
    ask_price: List[float] = Field(default_factory=list)
    ask_volume: List[float] = Field(default_factory=list)
    open_interest: Optional[float] = None


class TradeCalendar(BaseModel):
    exchange: Exchange
    date: date
    is_trading: bool
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None


class AdjustmentType(str, Enum):
    SPLIT = "SPLIT"
    DIVIDEND = "DIVIDEND"


class Adjustment(BaseModel):
    symbol: str
    date: date
    type: AdjustmentType
    factor: float  # Split ratio or Dividend amount
    cash_amount: Optional[float] = None  # Explicit cash amount if needed


class Fundamental(BaseModel):
    symbol: str
    date: date
    field: str
    value: float
    period: Optional[str] = None  # e.g., '2023Q1'
