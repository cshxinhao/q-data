import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CONFIG_DIR: Path = BASE_DIR / "config"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Database & Storage
    METADATA_DB_URL: str = f"sqlite:///{DATA_DIR}/metadata.db"
    PARQUET_ROOT: Path = DATA_DIR / "history"
    
    # ClickHouse (Real-time)
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DB: str = "quant_data"

    # Vendor: Tushare
    TUSHARE_TOKEN: str = ""

    # Vendor: Interactive Brokers
    IB_HOST: str = "127.0.0.1"
    IB_PORT: int = 7497  # Paper trading default
    IB_CLIENT_ID: int = 1

    # Vendor: Futu
    FUTU_HOST: str = "127.0.0.1"
    FUTU_PORT: int = 11111

    # Vendor: XtQuant
    XT_PATH: str = ""  # Path to XtQuant installation if needed
    XT_ACCOUNT_ID: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def create_dirs(self):
        """Ensure critical directories exist."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.PARQUET_ROOT.mkdir(exist_ok=True, parents=True)
        self.LOG_DIR.mkdir(exist_ok=True)

settings = Settings()
settings.create_dirs()
