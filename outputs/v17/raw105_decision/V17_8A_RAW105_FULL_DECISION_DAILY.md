# V17.8A RAW105 Full Decision Daily

Generated: 2026-05-30 22:36:07

## 1. Main Conclusion

RAW105_FULL_DECISION_STATUS: OK
FINAL_ACTION: BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION

**今天存在买入候选，但仍需要人工确认触发价、仓位和事件风险。**

## 2. Gate Status

| item | value |
|---|---|
| MANUAL_DAILY_STATUS | WARN_READOUT_PARTIAL |
| TODAY_SAFE | UNKNOWN |
| OFFICIAL_ACTION | UNKNOWN |
| BUDGET_ACTION | UNKNOWN |
| BUY_PERMISSION | UNKNOWN |
| GLOBAL_MODE | UNKNOWN |
| PRICE_AUDIT_STATUS | OK |

## 3. RAW105 Full Decision Counts

| item | count |
|---|---:|
| RAW_UNIVERSE_DECISION_COUNT | 105 |
| MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC | 105 |
| SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC | 20 |
| RAW105_PRICE_OK_COUNT | 105 |
| RAW105_PRICE_FAIL_COUNT | 0 |
| ACTIONABLE_BUY_COUNT_TODAY | 20 |
| WORTH_REVIEW_BUT_LOCKED_COUNT | 0 |
| MAIN_COMPUTE_WATCH_COUNT | 85 |

## 4. 今日值得复核但不能买的候选

| ticker | latest_price_date | latest_close | decision | reason |
|---|---:|---:|---|---|

## 5. 如果今天门控打开，优先复核层

优先级不是直接买入顺序，而是人工复核顺序：

1. second stage candidate
2. main compute but not second stage
3. classified only

## 6. Output Files

- Full RAW105 decision CSV: D:\us-tech-quant\outputs\v17\raw105_decision\v17_8A_raw105_full_decision_daily.csv
- Actionable buy candidates CSV: D:\us-tech-quant\outputs\v17\raw105_decision\v17_8A_today_buy_candidates.csv
- Worth-review watch CSV: D:\us-tech-quant\outputs\v17\raw105_decision\v17_8A_today_watch_candidates.csv
- Summary: D:\us-tech-quant\outputs\v17\raw105_decision\V17_8A_RAW105_FULL_DECISION_DAILY.md
- Read first: D:\us-tech-quant\outputs\v17\raw105_decision\V17_8A_READ_FIRST.txt
- Latest manual daily source: D:\us-tech-quant\outputs\v17\manual_daily\V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_20260530_223458.txt
