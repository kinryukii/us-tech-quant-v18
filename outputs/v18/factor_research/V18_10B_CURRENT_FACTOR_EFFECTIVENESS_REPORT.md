# V18.10B Factor Effectiveness Backtest

Generated: `2026-05-18 13:14:33`

## 1. Status

- STATUS: `OK_FACTOR_EFFECTIVENESS_BACKTEST_READY`
- MODE: `SHADOW_ONLY_NO_BLACK_BOX_FACTOR_RESEARCH`
- OFFICIAL_DECISION_IMPACT: `NONE`
- AUTO_WEIGHT_CHANGE: `DISABLED`
- AUTO_PROMOTION: `DISABLED`
- AUTO_TRADE: `DISABLED`

## 2. Source

- SELECTED_SOURCE: `D:\us-tech-quant\state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv`
- SOURCE_ROWS: `93`
- SOURCE_COLUMNS: `57`
- MIN_COUNT_FOR_EVALUATION: `20`
- TOP_FRACTION: `0.3`

## 3. Forward return maturity

| horizon | label_column | nonblank_count |
|---|---|---:|
| 1D | fwd_1d_return | 0 |
| 5D | fwd_5d_return | 0 |
| 10D | fwd_10d_return | 0 |
| 20D | fwd_20d_return | 0 |

## 4. Factor audit

| factor | current_weight | columns_used | method | nonnull |
|---|---:|---|---|---:|
| trend_score | 0.25 |  | NO_CAPTURED_COLUMN | 0 |
| relative_strength_score | 0.2 | relative_strength_score | relative_strength_benchmark | relative_strength_benchmark_return_120d | relative_strength_benchmark_return_20d | relative_strength_benchmark_return_60d | relative_strength_method | relative_strength_raw | relative_strength_return_120d | relative_strength_return_20d | relative_strength_return_60d | relative_strength_status | DIRECT_COLUMN:relative_strength_score | 93 |
| pullback_quality_score | 0.2 |  | NO_CAPTURED_COLUMN | 0 |
| momentum_continuation_score | 0.15 |  | NO_CAPTURED_COLUMN | 0 |
| overheat_penalty | 0.1 |  | NO_CAPTURED_COLUMN | 0 |
| volatility_penalty | 0.05 |  | NO_CAPTURED_COLUMN | 0 |
| execution_fit | 0.05 | execution_fit | execution_fit_score | execution_fit_status | DIRECT_COLUMN:execution_fit | 93 |

## 5. Summary

| factor | evaluated_horizons | avg_top_minus_bottom | avg_spearman | status | action |
|---|---:|---:|---:|---|---|
| trend_score | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |
| relative_strength_score | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |
| pullback_quality_score | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |
| momentum_continuation_score | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |
| overheat_penalty | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |
| volatility_penalty | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |
| execution_fit | 0 |  |  | INSUFFICIENT_MATURE_DATA | HOLD_CURRENT_WEIGHT |

## 6. Interpretation rules

1. `top_minus_bottom_mean > 0` means the favorable factor group outperformed the unfavorable group for that horizon.
2. `spearman_corr > 0` means higher favorable factor score is generally associated with higher forward return.
3. `INSUFFICIENT_SAMPLE` means the factor should not be used for weight changes yet.
4. This report does not change official weights. It only produces evidence.

## 7. Outputs

- EFFECTIVENESS: `D:\us-tech-quant\outputs\v18\factor_research\V18_10B_CURRENT_FACTOR_EFFECTIVENESS.csv`
- SUMMARY: `D:\us-tech-quant\outputs\v18\factor_research\V18_10B_CURRENT_FACTOR_EFFECTIVENESS_SUMMARY.csv`
- FACTOR_AUDIT: `D:\us-tech-quant\outputs\v18\factor_research\V18_10B_CURRENT_FACTOR_EFFECTIVENESS_AUDIT.csv`
- SOURCE_AUDIT: `D:\us-tech-quant\outputs\v18\factor_research\V18_10B_CURRENT_SOURCE_AUDIT.csv`
- REPORT: `D:\us-tech-quant\outputs\v18\factor_research\V18_10B_CURRENT_FACTOR_EFFECTIVENESS_REPORT.md`
- READ_FIRST: `D:\us-tech-quant\outputs\v18\factor_research\V18_10B_READ_FIRST.txt`

## 8. Next step

Forward-return sample is still immature. Keep running daily tracker + forward return filler until enough horizons mature.
