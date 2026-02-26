# Tasks

## Phase 1: Foundation & Core Interfaces
- [x] Create project structure and virtual environment setup.
- [x] Define configuration management (API keys, ClickHouse URI).
- [x] **Core Models**: Implement `Bar`, `Tick`, `Contract`, `TradeCalendar`, `Adjustment`, `Fundamental` in `src/core/models.py`.
- [x] **Core Interfaces**: Update `DataProvider` with new methods (calendar, fundamentals) in `src/core/interfaces.py`.
- [x] **Checker Interface**: Define `DataChecker` in `src/checker/base.py`.

## Phase 2: Storage Layer (Hybrid)
- [x] **Parquet**: Implement `src/storage/parquet_store.py` for reading/writing historical data.
- [x] **ClickHouse**: Implement `src/storage/clickhouse_store.py` using `clickhouse-driver`.
    - [x] Create tables for ticks and bars.
    - [x] Implement bulk insert method.
- [x] **Metadata**: Implement `src/storage/meta_store.py` (SQLite) for contracts and calendars.

## Phase 3: Checker Module
- [x] Implement `src/checker/validators.py`:
    - [x] Continuity check (compare data index vs trade calendar).
    - [x] Price outlier check (e.g., price change > limit).
    - [x] Volume check (e.g., zero volume on active day).
- [ ] Implement `src/checker/report.py`: Generate a simple validation report/log.

## Phase 4: Vendor Implementation - Tushare (History & Ref)
- [x] Implement `src/vendors/tushare_provider.py`.
- [x] Implement `get_history` (Bars).
- [x] Implement `get_calendar`, `get_adjustments`, `get_fundamentals` (Cap, ADV, PE).
- [ ] **Download Job**: Create script to download history + run `Checker`.

## Phase 5: Vendor Implementation - Sinolink/XtQuant (Real-time)
- [x] Implement `src/vendors/xt_provider.py`.
- [x] Implement real-time subscription pushing to `ClickHouse`.
- [x] Implement `get_snapshot`.

## Phase 6: EOD Consolidation & Operations
- [x] **Consolidation Job**: Create `src/jobs/consolidate.py`:
    - [x] Query ClickHouse for the day's data.
    - [x] Run `Checker` on the dataset.
    - [x] Write to Parquet (History).
    - [ ] Clean up/Archive ClickHouse data.
- [x] **CLI**: Update `main.py` with commands:
    - [x] `check-data`: Run integrity checks manually.
    - [x] `consolidate`: Run EOD process.
