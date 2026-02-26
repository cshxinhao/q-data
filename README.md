# Quant Data Manager

A robust data management system for quantitative trading, supporting multiple vendors (Tushare, Futu, IB, XtQuant) and handling both historical and real-time data.

## Features

- **Multi-Vendor Support**: Unified interface for Tushare, Futu, Interactive Brokers, and Sinolink (XtQuant).
- **Historical Data**: Batch download and efficient storage (Parquet).
- **Real-Time Data**: Event-driven architecture for tick/quote subscriptions.
- **Data Standardization**: Common `Bar` and `Tick` models across all vendors.

## Getting Started

1.  **Configuration**: Set up your API keys in `config.yaml` or `.env`.
2.  **Download History**:
    ```bash
    python src/main.py download --vendor tushare --symbol 000001.SZ --start 2023-01-01
    ```
3.  **Subscribe Real-Time**:
    ```bash
    python src/main.py subscribe --vendor ib --symbol AAPL
    ```

## Structure

- `src/core`: Base classes and data models.
- `src/vendors`: Vendor implementations.
- `src/storage`: Persistence logic.
