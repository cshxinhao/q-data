# Quant Data Management System Specification

## 1. Overview
This project is a comprehensive data management system designed for a quantitative hedge fund. It handles the entire lifecycle of financial data, including downloading, processing, persisting, and validating. The system supports both historical data (batch processing) and real-time data (stream processing) across multiple vendors.

## 2. Core Requirements

### 2.1. Use Cases
1.  **Historical Data**:
    *   Download modes: Day-by-day (e.g., for all symbols on a specific date) or Symbol-by-symbol (e.g., full history for a specific stock).
    *   **Data Integrity**: Automated checks for missing data, outliers, and duplicates after download.
2.  **Real-time Data**:
    *   Subscription-based model (pub/sub).
    *   **Hybrid Storage**: High-throughput appending to ClickHouse during the trading day.
    *   **EOD Consolidation**: End-of-day migration from ClickHouse to columnar Parquet files for long-term analytical storage.
3.  **Data Types**:
    *   **Market Data**: OHLCV Bars, Ticks/Snapshots.
    *   **Reference Data**: Trade Calendars, Instrument Definitions.
    *   **Corporate Actions**: Adjustment Factors (Splits, Dividends).
    *   **Fundamental/Basic**: Market Cap, ADV (Average Daily Volume), Financial Ratios (PE, PB).

### 2.2. Supported Vendors
*   **Tushare**: Primary source for Chinese market historical data, reference data, and fundamentals.
*   **Sinolink (XtQuant)**: Chinese market historical and real-time data (A-shares).
*   **Futu**: Hong Kong and US markets.
*   **Interactive Brokers (IB)**: Global markets (TWS API / ib_insync).

## 3. Architecture Design

### 3.1. High-Level Modules
*   **`core`**: Contains abstract base classes and standard data models.
*   **`vendors`**: Vendor-specific implementations adapting to the core interfaces.
*   **`storage`**: Handles data persistence logic.
    *   *Historical*: Parquet (PyArrow) on file system / S3.
    *   *Real-time*: ClickHouse (via `clickhouse-connect` or `clickhouse-driver`).
    *   *Metadata*: SQLite/PostgreSQL.
*   **`checker`**: **(New)** Data integrity validation module.
    *   *Post-Download*: Checks for missing dates against calendar, price anomalies.
    *   *Post-Consolidation*: Verifies row counts and consistency between ClickHouse and Parquet.
*   **`scheduler`**: Manages historical data download jobs and EOD consolidation tasks.
*   **`streamer`**: Manages real-time data subscriptions and writes to ClickHouse.

### 3.2. Data Models
Standardized internal representation to decouple vendors from downstream logic.
*   **`Bar`**: Symbol, dt, open, high, low, close, volume, amount, open_interest.
*   **`Tick`**: Symbol, dt, price, volume, bids, asks.
*   **`Contract`**: Symbol, Exchange, Type, Expiry, Multiplier.
*   **`TradeCalendar`**: Exchange, date, is_trading.
*   **`Adjustment`**: Symbol, date, factor, type (div/split).
*   **`Fundamental`**: Symbol, date, field (e.g., 'pe', 'mkt_cap'), value.

### 3.3. Storage Strategy
*   **Real-time (Intraday)**:
    *   **ClickHouse**: Tables `rt_ticks`, `rt_bars`. Optimized for high-speed inserts.
    *   *Schema*: `(timestamp DateTime64, symbol String, price Float64, ...)` partitioned by date.
*   **Historical (Long-term)**:
    *   **Parquet**: Partitioned by `Frequency` -> `Date` (for whole market) or `Symbol` (for single asset analysis).
    *   *Strategy*: `data/history/daily/YYYY/MM/data.parquet` or `data/history/1min/YYYYMMDD.parquet`.

## 4. Technology Stack
*   **Language**: Python 3.9+
*   **Data Analysis**: Pandas, Numpy
*   **Storage**:
    *   **ClickHouse**: For real-time ingestion.
    *   **Parquet**: For historical archives.
    *   **SQLite**: For light metadata (contracts, download status).
*   **Validation**: `pandera` (optional) or custom validation logic.

## 5. Interface Design

### 5.1. DataProvider Interface
```python
class DataProvider(ABC):
    # Market Data
    @abstractmethod
    def get_history(self, symbol: str, start: datetime, end: datetime, frequency: str) -> pd.DataFrame: ...
    @abstractmethod
    def get_snapshot(self, symbols: List[str]) -> Dict[str, Tick]: ...
    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable): ...
    
    # Reference & Fundamental
    @abstractmethod
    def get_calendar(self, exchange: str, start: datetime, end: datetime) -> List[date]: ...
    @abstractmethod
    def get_adjustments(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame: ...
    @abstractmethod
    def get_fundamentals(self, symbol: str, date: datetime) -> Dict[str, Any]: ...
```

### 5.2. DataChecker Interface
```python
class DataChecker(ABC):
    def check_continuity(self, data: pd.DataFrame, calendar: List[date]) -> List[str]:
        """Check for missing dates."""
        pass

    def check_outliers(self, data: pd.DataFrame, threshold: float = 0.2) -> pd.DataFrame:
        """Check for price jumps > 20%."""
        pass
```

## 6. Directory Structure
```
q-data/
├── config/             # Configuration files (API keys, DB connections)
├── src/
│   ├── core/           # Interfaces and Data Models
│   ├── vendors/        # Vendor implementations
│   ├── storage/        # Parquet and ClickHouse logic
│   ├── checker/        # Data integrity checks
│   ├── jobs/           # EOD consolidation and download scripts
│   └── main.py         # Entry point
├── data/               # Parquet data root
└── requirements.txt
```
