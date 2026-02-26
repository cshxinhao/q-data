import pandas as pd
import numpy as np
from datetime import datetime
import warnings


def get_board_type(symbol: str) -> str:
    """
    Infers board type from stock symbol.

    Args:
        symbol (str): Stock symbol (e.g., '600000.SH', '300001').

    Returns:
        str: 'STAR', 'CHINEXT', 'BSE', or 'MAIN'.
    """
    # Remove suffix if present
    code = symbol.split(".")[0]

    if code.startswith("688"):
        return "STAR"
    elif code.startswith("300"):
        return "CHINEXT"
    elif code.startswith(("8", "4", "920")):
        return "BSE"
    else:
        return "MAIN"


def calculate_price_limit(df: pd.DataFrame) -> pd.Series:
    """
    Calculates the price limit for each row in the DataFrame based on China A-share rules.

    Args:
        df (pd.DataFrame): DataFrame containing at least 'datetime' and 'symbol'.
                           Optional columns: 'list_date', 'is_st'.

    Returns:
        pd.Series: Series of price limit (float). e.g., 0.10 for 10%.
                   Returns np.inf for unlimited (no price limit).
    """
    # Create a copy to avoid modifying original
    data = df.copy()

    # Check columns
    if "datetime" not in data.columns:
        raise ValueError("DataFrame must have 'datetime' column")
    if "symbol" not in data.columns:
        raise ValueError("DataFrame must have 'symbol' column")

    data["datetime"] = pd.to_datetime(data["datetime"])
    symbol_col = "symbol"

    # Determine Board if not provided
    if "board" not in data.columns:
        warnings.warn("'board' column not found. Inferring board types from symbol.")
        data["board"] = data[symbol_col].astype(str).apply(get_board_type)

    # Initialize limit with default 0.10 (Main Board standard), will be overridden by rules later
    data["limit"] = 0.10

    # Handle IS_ST
    if "is_st" not in data.columns:
        warnings.warn("'is_st' column not found. Defaulting to False.")
        data["is_st"] = False  # Default to False if unknown

    # -------------------------------------------------------------------------
    # Rule Implementation
    # -------------------------------------------------------------------------

    # Dates for logic
    REG_MAIN_DATE = pd.Timestamp("2023-04-10")
    REG_CHINEXT_DATE = pd.Timestamp("2020-08-24")
    ST_REFORM_DATE = pd.Timestamp("2025-07-01")

    # 1. STAR Market (Always 20%, IPO first 5 days unlimited)
    # -------------------------------------------------------
    mask_star = data["board"] == "STAR"
    data.loc[mask_star, "limit"] = 0.20

    # 2. ChiNext
    # -------------------------------------------------------
    # Before 2020-08-24: 10% (ST 5%)
    # After 2020-08-24: 20% (ST 20%)
    mask_chinext = data["board"] == "CHINEXT"
    mask_chinext_pre = mask_chinext & (data["datetime"] < REG_CHINEXT_DATE)
    mask_chinext_post = mask_chinext & (data["datetime"] >= REG_CHINEXT_DATE)

    data.loc[mask_chinext_pre, "limit"] = 0.10
    data.loc[mask_chinext_pre & data["is_st"], "limit"] = 0.05
    data.loc[mask_chinext_post, "limit"] = 0.20

    # 3. BSE (Beijing Stock Exchange)
    # -------------------------------------------------------
    # Always 30% (IPO Day 1 unlimited)
    mask_bse = data["board"] == "BSE"
    data.loc[mask_bse, "limit"] = 0.30

    # 4. Main Board
    # -------------------------------------------------------
    mask_main = data["board"] == "MAIN"

    # ST Rules
    # Before 2025-07-01: ST is 5%
    # After 2025-07-01: ST is 10% (Same as normal)
    mask_main_st_legacy = (
        mask_main & data["is_st"] & (data["datetime"] < ST_REFORM_DATE)
    )
    data.loc[mask_main_st_legacy, "limit"] = 0.05

    # Normal Main Board is 10% (already default)

    # 5. IPO Rules (Unlimited Price Limits)
    # -------------------------------------------------------
    # If list_date is available, we can check for IPO phases
    if "list_date" in data.columns:
        data["list_date"] = pd.to_datetime(data["list_date"])

        # Calculate days difference (approximate trading days)
        # Note: This is calendar days difference.
        # For strict 5 trading days, usually within 7-10 calendar days.
        # We will strictly check Day 0 (Launch day) and loosen for Day 1-5 if we can't be sure.
        # Ideally, we need 'ipo_day' column.

        # IPO Day 1 (Launch Day)
        # STAR: Unlimited
        # ChiNext (Post-Reg): Unlimited
        # Main (Post-Reg): Unlimited
        # BSE: Unlimited
        # Main/ChiNext (Pre-Reg): 44% effectively (but usually handled as special case, let's say 0.44)

        mask_ipo_day1 = data["datetime"] == data["list_date"]

        # STAR Day 1
        data.loc[mask_star & mask_ipo_day1, "limit"] = np.inf

        # BSE Day 1
        data.loc[mask_bse & mask_ipo_day1, "limit"] = np.inf

        # ChiNext Day 1
        # Pre-Reg: 44%
        data.loc[mask_chinext_pre & mask_ipo_day1, "limit"] = 0.44
        # Post-Reg: Unlimited
        data.loc[mask_chinext_post & mask_ipo_day1, "limit"] = np.inf

        # Main Day 1
        # Pre-Reg: 44%
        mask_main_pre = mask_main & (data["datetime"] < REG_MAIN_DATE)
        data.loc[mask_main_pre & mask_ipo_day1, "limit"] = 0.44
        # Post-Reg: Unlimited
        mask_main_post = mask_main & (data["datetime"] >= REG_MAIN_DATE)
        data.loc[mask_main_post & mask_ipo_day1, "limit"] = np.inf

        # First 5 Days Unlimited (STAR, ChiNext Post, Main Post)
        # We need to know if it's day 2-5.
        # Without trading calendar, we can't be 100% sure.
        # However, if 'ipo_day' column exists, use it.
        if "ipo_day" in data.columns:
            mask_first_5 = data["ipo_day"] <= 5

            # STAR: First 5 days unlimited
            data.loc[mask_star & mask_first_5, "limit"] = np.inf

            # ChiNext Post: First 5 days unlimited
            data.loc[mask_chinext_post & mask_first_5, "limit"] = np.inf

            # Main Post: First 5 days unlimited
            data.loc[mask_main_post & mask_first_5, "limit"] = np.inf

            # BSE: Only Day 1 unlimited, Day 2+ 30% (already set to 30, Day 1 set to inf above)

    return data["limit"]
