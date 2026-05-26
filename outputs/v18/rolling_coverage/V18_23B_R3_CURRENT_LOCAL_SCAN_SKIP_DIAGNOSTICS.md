# V18.23B-R3 Local Scan Skip Diagnostics

Generated: 2026-05-21T14:40:12

## Status
Status: **OK_V18_23B_R3_LOCAL_SCAN_SKIP_DIAGNOSTICS_READY**

Mode: **READ_ONLY_LOCAL_SCAN_SKIP_DIAGNOSTICS**

## Diagnosis
R2 selected 65 tickers and skipped 65. R3 diagnosed 65 skipped tickers without modifying the ledger or source files.

| Category | Count | Interpretation |
| --- | --- | --- |
| MISSING_LOCAL_PRICE | 65 | See repair plan. |

## Success Definition Recommendation
R4 should split local scan success into LOCAL_PRICE_SCAN_SUCCESS and FULL_FACTOR_SCAN_SUCCESS so rolling coverage can track local price coverage separately from full factor-ready coverage.

## Recommended next action
Implement V18.23B-R4 to split LOCAL_PRICE_SCAN_SUCCESS from FULL_FACTOR_SCAN_SUCCESS; use staged backfill later for tickers with no local price evidence.
