# V17.7 RAW Universe Full Screen Audit

Generated: `2026-05-27 22:48:34`

## 1. Main Conclusion

**RAW_FULL_AUDIT_STATUS: `OK`**

This audit checks every ticker in the raw universe before the system narrows the list to screened universe and second-stage candidates.

## 2. Count Summary

| item | count |
|---|---:|
| RAW_UNIVERSE_COUNT | 105 |
| SCREENED_UNIVERSE_COUNT | 105 |
| EXCLUDED_BEFORE_SCREENED_COUNT | 0 |
| SELECTED_FOR_EXECUTION_COUNT | 105 |
| SECOND_STAGE_COUNT | 20 |
| RAW_PRICE_OK_COUNT | 105 |
| RAW_PRICE_FAIL_COUNT | 0 |

## 3. Pipeline Status Counts

| status | count |
|---|---:|
| SELECTED_FOR_EXECUTION_REVIEW | 85 |
| SECOND_STAGE_CANDIDATE | 20 |

## 4. Price Status Counts

| price_status | count |
|---|---:|
| OK_EXISTING_LOCAL_PRICE | 105 |

## 5. Important Output Files

- Full audit CSV: `D:\us-tech-quant\outputs\v17\raw_universe_audit\v17_7_raw_universe_full_screen_audit.csv`
- Summary: `D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7_RAW_UNIVERSE_FULL_SCREEN_AUDIT.md`
- Read first: `D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7_READ_FIRST.txt`

## 6. Interpretation

- `RAW_UNIVERSE_COUNT` is the original pool size.
- `SCREENED_UNIVERSE_COUNT` is the number that survives the basic screen.
- `SECOND_STAGE_COUNT` is the number promoted to the focused candidate layer.
- `RAW_ONLY_EXCLUDED_BEFORE_SCREENED` means the ticker existed in the raw list but did not survive to the screened universe.
- `price_status` confirms whether the ticker had usable local or yfinance price data.
