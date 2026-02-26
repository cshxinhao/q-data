# Checklist

## Initialization
- [x] Project directory created.
- [x] `spec.md` approved.
- [x] `tasks.md` approved.
- [x] `requirements.txt` includes `clickhouse-driver` or `clickhouse-connect`.

## Core Implementation
- [x] `src/core/models.py` includes `Adjustment`, `Fundamental`.
- [x] `src/core/interfaces.py` updated.

## Storage Implementation
- [ ] **ClickHouse** is running and accessible.
- [ ] `src/storage/clickhouse_store.py` can insert and query data.
- [ ] `src/storage/parquet_store.py` handles partitioning correctly.

## Checker Implementation
- [ ] **Continuity**: Can detect missing trading days.
- [ ] **Outlier**: Can detect abnormal price spikes.
- [ ] **Integration**: Checker runs automatically after download.

## Vendor Adapters
- [ ] **Tushare**: Downloads history, adjustments, and fundamentals.
- [ ] **XtQuant**: Subscribes to ticks and writes to ClickHouse.
- [ ] **IB/Futu**: (Planned) Interfaces ready.

## EOD Process
- [ ] **Consolidation**: Data moves from ClickHouse to Parquet correctly.
- [ ] **Validation**: Consolidated data is verified before finalizing.
