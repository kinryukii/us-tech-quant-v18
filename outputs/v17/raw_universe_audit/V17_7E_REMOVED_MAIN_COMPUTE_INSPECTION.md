# V17.7E Removed Main Compute Inspection

Generated: 2026-05-30 22:36:06

## 1. Main Conclusion

REMOVED_INSPECTION_STATUS: WARN_CHECK_REMOVED_NAMES

本报告检查从旧 stable 主计算层 66 中被移出、当前不在 main compute 56 里的标的。

## 2. Count Summary

| item | count |
|---|---:|
| MAIN_COMPUTE_REMOVED_COUNT | 0 |
| MAIN_COMPUTE_ADDED_COUNT | 105 |
| REMOVED_PRICE_OK_COUNT | 0 |
| REMOVED_STILL_RAW_COUNT | 0 |
| REMOVED_STILL_CLASSIFIED_COUNT | 0 |
| REMOVED_STILL_SECOND_STAGE_COUNT | 0 |

## 3. Removed Tickers

| ticker | current_semantic_layer | price_status | latest_price_date | latest_close | interpretation |
|---|---|---|---:|---:|---|

## 4. Interpretation

如果 REMOVED_PRICE_OK_COUNT 等于 MAIN_COMPUTE_REMOVED_COUNT，说明这 10 个不是因为价格失败被移出。

如果 REMOVED_STILL_RAW_COUNT 和 REMOVED_STILL_CLASSIFIED_COUNT 都等于 10，说明它们仍在 105 原始池和 105 分类池中，只是没有进入当前 main compute 56。

## 5. Output Files

- Inspection CSV: D:\us-tech-quant\outputs\v17\raw_universe_audit\v17_7E_removed_main_compute_inspection.csv
- Summary: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md
- Read first: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7E_READ_FIRST.txt

