# V18.25A-R5 Targeted Technical Timing Refresh Dry Run

- Status: WARN_V18_25A_R5_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN_READY
- Mode: READ_ONLY_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN
- Target tickers: 52
- Technical refresh success: 52
- Technical refresh fail: 0
- Formula compatibility status: PARTIAL_COMPATIBLE
- Exact V18.6A formula reused: FALSE
- Partial compatible count: 52
- Full compatible count: 0
- Insufficient history count: 0
- Staged technical output path: D:\us-tech-quant\outputs\v18\technical_timing\V18_25A_R5_TARGETED_TECHNICAL_TIMING_DRYRUN.csv
- Current technical file modified: FALSE

## Summary

| Metric | Count | Notes |
| --- | ---: | --- |
| TARGET_TICKER_COUNT | 52 | Target tickers selected from R4 dry-run readiness source. |
| TECHNICAL_REFRESH_ATTEMPT_COUNT | 52 | One dry-run refresh attempt per target ticker. |
| TECHNICAL_REFRESH_SUCCESS_COUNT | 52 | Rows with no technical refresh blocker. |
| TECHNICAL_REFRESH_FAIL_COUNT | 0 | Rows that carried a blocker or missing-data condition. |
| FULL_COMPATIBLE_COUNT | 0 | Rows using the exact current V18.6A formula set, including external overlay. Expected zero in local-only dry-run. |
| PARTIAL_COMPATIBLE_COUNT | 52 | Rows using local V18.6A-compatible indicator logic without the external VIX overlay. |
| INSUFFICIENT_HISTORY_COUNT | 0 | Rows with missing required price history or columns. |
| OUTPUT_ROW_COUNT | 52 | Rows written to the staged dry-run technical output. |
| FORMULA_COMPATIBILITY_STATUS | PARTIAL_COMPATIBLE | Local-only compatibility assessment for the staged dry-run. |
| EXACT_V18_6A_FORMULA_REUSED | FALSE | False because the external VIX overlay was not fetched. |

## Notes

- The dry run reuses the local V18.6A-compatible BB, RSI, KDJ, and volume-ratio logic.
- The external VIX overlay is intentionally omitted because this task forbids external data fetches.
- `formula_compatibility` is therefore `PARTIAL_COMPATIBLE` for every staged row.
- No official technical timing file was overwritten.
