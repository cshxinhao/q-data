
# A-Share Price Limit Rules

> **Note for Implementation:**  
> 1. **Priority Logic:** When validating data, evaluate rules in order. **IPO-specific rules** take precedence over **Normal Trading rules** if the stock is in its initial listing phase.  
> 2. **Date Format:** `YYYY-MM-DD`.  
> 3. **Price Limit:** Represented as a decimal (e.g., `0.10` = 10%). `None` indicates no hard limit (but temporary suspension mechanisms may apply).  
> 4. **Context:** Current date is assumed to be **2026**. Historical rule changes are reflected accordingly.


| Rule Name | Rule Content (Logic Condition) | Price Limit | Rule Start Date | Rule End Date | Remarks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MAIN_NORMAL_LEGACY** | `board == 'MAIN'` AND `is_st == False` AND `trade_date < 2023-04-10` | 0.10 | 1996-12-16 | 2023-04-09 | Standard main board rule before full registration system. |
| **MAIN_NORMAL_CURRENT** | `board == 'MAIN'` AND `is_st == False` AND `trade_date >= 2023-04-10` | 0.10 | 2023-04-10 | Present | Full registration system implemented. Daily limit unchanged for existing stocks. |
| **MAIN_ST_LEGACY** | `board == 'MAIN'` AND `is_st == True` AND `trade_date < 2025-07-01` | 0.05 | 2012-04-23 | 2025-06-30 | Risk warning stocks historically had tighter limits. |
| **MAIN_ST_CURRENT** | `board == 'MAIN'` AND `is_st == True` AND `trade_date >= 2025-07-01` | 0.10 | 2025-07-01 | Present | Aligned with normal main board stocks per 2025 exchange reform. |
| **MAIN_IPO_LEGACY** | `board == 'MAIN'` AND `ipo_phase == True` AND `ipo_day == 1` AND `trade_date < 2023-04-10` | 0.44 | 2014-01-01 | 2023-04-09 | IPO Day 1 limit was effectively 44% (1.44x issue price). |
| **MAIN_IPO_LEGACY_DAY2** | `board == 'MAIN'` AND `ipo_phase == True` AND `ipo_day > 1` AND `trade_date < 2023-04-10` | 0.10 | 2014-01-01 | 2023-04-09 | IPO Day 2+ reverted to standard 10% limit. |
| **MAIN_IPO_CURRENT** | `board == 'MAIN'` AND `ipo_phase == True` AND `ipo_day <= 5` AND `trade_date >= 2023-04-10` | None | 2023-04-10 | Present | First 5 trading days have no price limit (temporary suspension applies). |
| **MAIN_IPO_CURRENT_POST** | `board == 'MAIN'` AND `ipo_phase == True` AND `ipo_day > 5` AND `trade_date >= 2023-04-10` | 0.10 | 2023-04-10 | Present | From 6th day onwards, standard 10% limit applies. |
| **STAR_NORMAL** | `board == 'STAR'` AND `is_st == False` | 0.20 | 2019-07-22 | Present | STAR Market standard limit. |
| **STAR_ST** | `board == 'STAR'` AND `is_st == True` | 0.20 | 2019-07-22 | Present | STAR Market ST stocks follow same limit as normal stocks. |
| **STAR_IPO** | `board == 'STAR'` AND `ipo_phase == True` AND `ipo_day <= 5` | None | 2019-07-22 | Present | First 5 trading days have no price limit. |
| **STAR_IPO_POST** | `board == 'STAR'` AND `ipo_phase == True` AND `ipo_day > 5` | 0.20 | 2019-07-22 | Present | From 6th day onwards, 20% limit applies. |
| **CHINEXT_NORMAL_LEGACY** | `board == 'CHINEXT'` AND `is_st == False` AND `trade_date < 2020-08-24` | 0.10 | 2009-10-30 | 2020-08-23 | Pre-registration reform limit. |
| **CHINEXT_NORMAL_CURRENT** | `board == 'CHINEXT'` AND `is_st == False` AND `trade_date >= 2020-08-24` | 0.20 | 2020-08-24 | Present | Post-registration reform limit. |
| **CHINEXT_ST_LEGACY** | `board == 'CHINEXT'` AND `is_st == True` AND `trade_date < 2020-08-24` | 0.05 | 2012-04-23 | 2020-08-23 | Pre-reform ST limit was 5%. |
| **CHINEXT_ST_CURRENT** | `board == 'CHINEXT'` AND `is_st == True` AND `trade_date >= 2020-08-24` | 0.20 | 2020-08-24 | Present | Post-reform ST limit aligned with normal stocks (20%). |
| **CHINEXT_IPO** | `board == 'CHINEXT'` AND `ipo_phase == True` AND `ipo_day <= 5` AND `trade_date >= 2020-08-24` | None | 2020-08-24 | Present | First 5 trading days have no price limit (post-reform). |
| **CHINEXT_IPO_LEGACY** | `board == 'CHINEXT'` AND `ipo_phase == True` AND `trade_date < 2020-08-24` | 0.44 | 2014-01-01 | 2020-08-23 | Pre-reform IPO Day 1 limit effectively 44%. |
| **BSE_NORMAL** | `board == 'BSE'` AND `ipo_phase == False` | 0.30 | 2021-11-15 | Present | Beijing Stock Exchange standard limit. |
| **BSE_IPO_DAY1** | `board == 'BSE'` AND `ipo_phase == True` AND `ipo_day == 1` | None | 2021-11-15 | Present | IPO First Day has no price limit. |
| **BSE_IPO_POST** | `board == 'BSE'` AND `ipo_phase == True` AND `ipo_day > 1` | 0.30 | 2021-11-15 | Present | From 2nd day onwards, 30% limit applies. |
| **DELISTING_CONSOLIDATION** | `status == 'DELISTING_CONSOLIDATION'` | 0.10 | 2020-06-12 | Present | Delisting consolidation period generally 10% (check specific board legacy). |
| **SUSPENSION_RESUME** | `is_resume_after_suspend == True` AND `suspend_reason == 'PRICE_VOLATILITY'` | None | 1996-12-16 | Present | Some resumption cases have no limit on first day; verify exchange announcement. |


