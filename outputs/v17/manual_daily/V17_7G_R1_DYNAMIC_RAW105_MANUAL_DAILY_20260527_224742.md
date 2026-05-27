# V17.7G-R1 Dynamic RAW105 Manual Daily

Generated: 2026-05-27 22:47:42

## 1. Status

| item | value |
|---|---|
| V17_7G_R1_STATUS | FAIL_OR_REVIEW_REQUIRED |
| UPSTREAM_V17_7C_R1_STATUS | FAIL_OR_REVIEW_REQUIRED |
| BASE_DAILY_STATUS | SOFT_OK_OUTPUTS_VALID |
| MANUAL_DAILY_STATUS |  |

## 2. Today Operation Advice

| item | value |
|---|---|
| TODAY_SAFE |  |
| OFFICIAL_ACTION |  |
| BUDGET_ACTION |  |
| BUY_PERMISSION |  |
| GLOBAL_MODE |  |
| CRITICAL_UNKNOWN_COUNT |  |

Conclusion: 今日操作需要人工复核。

## 3. Correct Universe Hierarchy

| layer | count |
|---|---:|
| RAW_UNIVERSE_COUNT | 105 |
| CLASSIFIED_UNIVERSE_COUNT | 105 |
| MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC | 105 |
| SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC | 20 |

MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC is not hardcoded. It can change day by day.

## 4. RAW105 Price Refresh

| item | value |
|---|---:|
| RAW105_PRICE_REFRESH_STATUS | OK |
| PRICE_REFRESH_OK_COUNT | 105 |
| PRICE_REFRESH_FAIL_COUNT | 0 |
| MAX_LATEST_PRICE_DATE | 2026-05-27 |
| LATEST_DATE_COUNT | 104 |
| OK_BUT_NOT_MAX_DATE_COUNT | 1 |
| PRICE_FRESHNESS_ACCEPTANCE_STATUS | WARN_REVIEW_OR_REJECT_PRESENT |

## 5. Main Compute Price Audit

| item | value |
|---|---:|
| PRICE_AUDIT_STATUS |  |
| PRICE_ROW_COUNT |  |
| PRICE_OK_COUNT |  |
| PRICE_FAIL_COUNT |  |
| PRICE_STALE_COUNT |  |
| MIN_LATEST_PRICE_DATE |  |
| MAX_LATEST_PRICE_DATE |  |

## 6. Read Files

- TXT report: D:\us-tech-quant\outputs\v17\manual_daily\V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_20260527_224742.txt
- MD report: D:\us-tech-quant\outputs\v17\manual_daily\V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_20260527_224742.md
- Read first: D:\us-tech-quant\outputs\v17\manual_daily\V17_7G_R1_READ_FIRST.txt
- Latest base manual daily: 
- Upstream summary: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7C_R1_MANUAL_DAILY_WITH_RAW105_AUDIT_SUMMARY.md
- RAW105 refresh: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7F_RAW105_LATEST_PRICE_REFRESH.md
- Freshness acceptance: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md
- Universe semantic audit: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7B_UNIVERSE_SEMANTIC_AUDIT.md
- Delta audit: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7D_MAIN_COMPUTE_DELTA_AUDIT.md
- Removed inspection: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md

## 7. Next Normal Command

Set-Location "D:\us-tech-quant"

powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1"

