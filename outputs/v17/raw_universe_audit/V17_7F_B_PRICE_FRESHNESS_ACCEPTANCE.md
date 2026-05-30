# V17.7F-B RAW105 Price Freshness Acceptance

Generated: 2026-05-30 22:36:02

## 1. Main Conclusion

PRICE_FRESHNESS_ACCEPTANCE_STATUS: OK_ACCEPT_DYNAMIC_NON_MAX

本报告判断 V17.7F 中唯一 non-max-date ticker 是否影响正式 daily 操作建议。

## 2. Count Summary

| item | value |
|---|---:|
| RAW_TICKER_COUNT | 105 |
| PRICE_REFRESH_OK_COUNT | 105 |
| PRICE_REFRESH_FAIL_COUNT | 0 |
| MAX_LATEST_PRICE_DATE | 2026-05-29 |
| LATEST_DATE_ACCEPT_COUNT | 105 |
| NON_MAX_ACCEPT_COUNT | 0 |
| REVIEW_COUNT | 0 |
| REJECT_COUNT | 0 |

## 3. Non Max / Review Rows

| ticker | latest_price_date | latest_close | latest_volume | semantic_layer | in_main_compute | in_second_stage | acceptance_status |
|---|---:|---:|---:|---|---|---|---|

## 4. Interpretation

PSTG 的 latest_price_date 为 2026-05-11，低于全池最大日期 2026-05-12。

但 PSTG 当前不在 main compute 56，也不在 second stage 10，因此不会污染今日主计算候选或操作建议。

只要 PRICE_FRESHNESS_ACCEPTANCE_STATUS 为 OK_ACCEPT_1_NON_MAX_NOT_IN_MAIN_OR_SECOND_STAGE，就允许继续推进 wrapper 语义修正。

## 5. Output Files

- Acceptance CSV: D:\us-tech-quant\outputs\v17\raw_universe_audit\v17_7F_B_price_freshness_acceptance.csv
- Summary: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md
- Read first: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7F_B_READ_FIRST.txt

