# V17.7C-R1 Manual Daily With RAW105 Audit

Generated: 2026-05-30 22:36:06

## 1. Main Conclusion

V17_7C_R1_STATUS: OK_DYNAMIC_COUNTS_WITH_RAW105_REFRESH

本 wrapper 修正 V17.7C 的状态语义：base daily 若非零退出，但关键输出有效，则标记为 SOFT_OK_OUTPUTS_VALID，而不是误报 failed。

## 2. Correct Current Universe Hierarchy

| item | value |
|---|---:|
| RAW_UNIVERSE_COUNT | 105 |
| CLASSIFIED_UNIVERSE_COUNT | 105 |
| MAIN_COMPUTE_UNIVERSE_COUNT | 105 |
| SECOND_STAGE_CANDIDATE_COUNT | 20 |
| RAW_PRICE_OK_COUNT | 105 |
| RAW_PRICE_FAIL_COUNT | 0 |

## 3. RAW105 Latest Price Refresh

| item | value |
|---|---:|
| RAW105_PRICE_REFRESH_STATUS | OK |
| PRICE_REFRESH_OK_COUNT | 105 |
| PRICE_REFRESH_FAIL_COUNT | 0 |
| MAX_LATEST_PRICE_DATE | 2026-05-29 |
| LATEST_DATE_COUNT | 105 |
| OK_BUT_NOT_MAX_DATE_COUNT | 0 |

## 4. Freshness Acceptance

| item | value |
|---|---:|
| PRICE_FRESHNESS_ACCEPTANCE_STATUS | OK_ACCEPT_DYNAMIC_NON_MAX |
| NON_MAX_ACCEPT_COUNT | 0 |
| REVIEW_COUNT | 0 |
| REJECT_COUNT | 0 |

## 5. Main Compute Delta

| item | value |
|---|---:|
| DELTA_AUDIT_STATUS | OK_RAW_PRICE_WITH_DYNAMIC_MAIN_COUNT |
| MAIN_COMPUTE_REMOVED_COUNT | 0 |
| MAIN_COMPUTE_ADDED_COUNT | 105 |
| REMOVED_INSPECTION_STATUS | WARN_CHECK_REMOVED_NAMES |

## 6. Step Results

| step | status | exit_code | note |
|---|---|---:|---|
| V17_6F_MANUAL_DAILY_BASE | OK | 0 | base daily completed |
| V17_7F_RAW105_LATEST_PRICE_REFRESH | OK | 0 | completed |
| V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE | OK | 0 | completed |
| V17_7_RAW_UNIVERSE_FULL_AUDIT | OK | 0 | completed |
| V17_7B_UNIVERSE_SEMANTIC_AUDIT | OK | 0 | completed |
| V17_7D_MAIN_COMPUTE_DELTA_AUDIT | OK | 0 | completed |
| V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION | OK | 0 | completed |

## 7. Interpretation

当前正式口径：RAW 原始池 105 个全部刷新与审计；105 个全部 classified；当前 main compute 动态层为 56；second stage 候选为 10。

PSTG 是唯一 non-max-date ticker，日期为 2026-05-11，但它不在 main compute 56，也不在 second stage 10，因此不阻断今日候选/操作建议。

## 8. Output Files

- V17.7C-R1 summary: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7C_R1_MANUAL_DAILY_WITH_RAW105_AUDIT_SUMMARY.md
- V17.7C-R1 read first: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7C_R1_READ_FIRST.txt
- V17.7C-R1 steps CSV: D:\us-tech-quant\outputs\v17\raw_universe_audit\v17_7C_R1_manual_daily_steps.csv
- RAW105 refresh: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7F_RAW105_LATEST_PRICE_REFRESH.md
- Freshness acceptance: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md
- Universe semantic audit: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7B_UNIVERSE_SEMANTIC_AUDIT.md
- Delta audit: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7D_MAIN_COMPUTE_DELTA_AUDIT.md
- Removed inspection: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md

