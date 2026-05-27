# V18.10A-R2 Factor Daily Capture Patch

Generated: `2026-05-18 13:14:22`

## 1. Status

- STATUS: `OK_FACTOR_DAILY_CAPTURE_PATCH_READY`
- MODE: `NO_BLACK_BOX_FACTOR_CAPTURE`
- OFFICIAL_DECISION_IMPACT: `NONE`
- AUTO_WEIGHT_CHANGE: `DISABLED`
- AUTO_TRADE: `DISABLED`

## 2. Formula disclosure

### relative_strength_score

- Benchmark: `QQQ`
- Raw score formula when yfinance is enabled:

```text
relative_strength_raw =
  0.50 * (ticker_return_20d - benchmark_return_20d)
+ 0.30 * (ticker_return_60d - benchmark_return_60d)
+ 0.20 * (ticker_return_120d - benchmark_return_120d)

relative_strength_score = cross-sectional percentile of relative_strength_raw among current candidates
```

If yfinance is not used and explicit asset/benchmark return columns are missing, the field is created but marked `MISSING_INPUT`.

### execution_fit

```text
required_cash_usd = latest_close * (1 + price_buffer_pct)
concentration_pct = required_cash_usd / cash_usd

if required_cash_usd > cash_usd: execution_fit = 0
elif concentration_pct <= 20%: execution_fit = 100
elif concentration_pct <= 30%: execution_fit = 80
elif concentration_pct <= max_single_order_cash_pct: execution_fit = 60
elif concentration_pct <= 50%: execution_fit = 40
elif concentration_pct <= 75%: execution_fit = 20
else: execution_fit = 10
```

## 3. Summary

- FILES_FOUND: `3`
- FILES_PATCHED: `3`
- RELATIVE_STRENGTH_POPULATED_TOTAL: `217`
- EXECUTION_FIT_POPULATED_TOTAL: `217`
- USE_YFINANCE: `True`
- CASH_USD: `2000.0000`
- CASH_SOURCE: `D:\us-tech-quant\state\v18\simulation\V18_CURRENT_SIM_ACCOUNT.csv`
- PRICE_BUFFER_PCT: `0.02`
- MAX_SINGLE_ORDER_CASH_PCT: `0.4`

## 4. Patched files

| path | rows | status | relative_strength_populated | execution_fit_populated |
|---|---:|---|---:|---:|
| D:\us-tech-quant\state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv | 93 | OK_PATCHED | 93 | 93 |
| D:\us-tech-quant\outputs\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv | 93 | OK_PATCHED | 93 | 93 |
| D:\us-tech-quant\outputs\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv | 31 | OK_PATCHED | 31 | 31 |

## 5. Outputs

- AUDIT: `D:\us-tech-quant\outputs\v18\factor_registry\V18_10A_R2_CURRENT_FACTOR_DAILY_CAPTURE_PATCH_AUDIT.csv`
- REPORT: `D:\us-tech-quant\outputs\v18\factor_registry\V18_10A_R2_CURRENT_FACTOR_DAILY_CAPTURE_PATCH_REPORT.md`
- READ_FIRST: `D:\us-tech-quant\outputs\v18\factor_registry\V18_10A_R2_READ_FIRST.txt`

## 6. Next step

Run V18.10A coverage audit again. Expected improvement: official candidate captured count should become `7 / 7` if headers are now present.
