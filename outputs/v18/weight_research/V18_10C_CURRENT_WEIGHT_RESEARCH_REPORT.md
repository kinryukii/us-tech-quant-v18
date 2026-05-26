# V18.10C Weight Research Engine

Generated: `2026-05-18 13:14:33`

## 1. Status

- STATUS: `OK_WEIGHT_RESEARCH_ENGINE_READY`
- MODE: `SHADOW_ONLY_NO_BLACK_BOX_WEIGHT_RESEARCH`
- OFFICIAL_DECISION_IMPACT: `NONE`
- AUTO_WEIGHT_CHANGE: `DISABLED`
- AUTO_PROMOTION: `DISABLED`
- AUTO_TRADE: `DISABLED`

## 2. Source

- SELECTED_SOURCE: `D:\us-tech-quant\state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv`
- SOURCE_ROWS: `93`
- OFFICIAL_FACTOR_COUNT: `7`
- WEIGHT_CANDIDATE_COUNT: `7`
- MIN_COUNT_REQUIRED: `20`
- TOP_FRACTION: `0.3`

## 3. Forward label maturity

| horizon | label_column | nonblank_count |
|---|---|---:|
| 1D | fwd_1d_return | 0 |
| 5D | fwd_5d_return | 0 |
| 10D | fwd_10d_return | 0 |
| 20D | fwd_20d_return | 0 |

## 4. Weight candidates

| weight_set | trend | rs | pullback | momentum | overheat | volatility | execution |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASELINE_CURRENT | 0.250000 | 0.200000 | 0.200000 | 0.150000 | 0.100000 | 0.050000 | 0.050000 |
| EQUAL_WEIGHT | 0.142857 | 0.142857 | 0.142857 | 0.142857 | 0.142857 | 0.142857 | 0.142857 |
| DEFENSIVE_CAUTION | 0.200000 | 0.180000 | 0.240000 | 0.080000 | 0.180000 | 0.080000 | 0.040000 |
| MOMENTUM_NORMAL | 0.260000 | 0.240000 | 0.140000 | 0.220000 | 0.060000 | 0.040000 | 0.040000 |
| PULLBACK_QUALITY | 0.200000 | 0.180000 | 0.320000 | 0.080000 | 0.140000 | 0.050000 | 0.030000 |
| LOW_VOL_DEFENSE | 0.200000 | 0.180000 | 0.200000 | 0.080000 | 0.140000 | 0.160000 | 0.040000 |
| EXECUTION_AWARE_SMALL_ACCOUNT | 0.200000 | 0.180000 | 0.200000 | 0.100000 | 0.100000 | 0.070000 | 0.150000 |

## 5. Guardrail conclusion

- READY_HORIZON_COUNT: `0`
- OK_EVALUATED_ROWS: `0`
- INSUFFICIENT_SAMPLE_ROWS: `0`
- NO_DATA_ROWS: `28`
- PROMOTION_PERMISSION: `HOLD_NO_WEIGHT_ACTION`

No automatic weight changes are allowed. If forward labels are immature, the only valid action is HOLD_NO_WEIGHT_ACTION.

## 6. Outputs

- WEIGHT_CANDIDATES: `D:\us-tech-quant\outputs\v18\weight_research\V18_10C_CURRENT_WEIGHT_CANDIDATES.csv`
- EVALUATION: `D:\us-tech-quant\outputs\v18\weight_research\V18_10C_CURRENT_WEIGHT_RESEARCH_EVALUATION.csv`
- FACTOR_AUDIT: `D:\us-tech-quant\outputs\v18\weight_research\V18_10C_CURRENT_WEIGHT_RESEARCH_FACTOR_AUDIT.csv`
- SOURCE_AUDIT: `D:\us-tech-quant\outputs\v18\weight_research\V18_10C_CURRENT_WEIGHT_RESEARCH_SOURCE_AUDIT.csv`
- REPORT: `D:\us-tech-quant\outputs\v18\weight_research\V18_10C_CURRENT_WEIGHT_RESEARCH_REPORT.md`
- READ_FIRST: `D:\us-tech-quant\outputs\v18\weight_research\V18_10C_READ_FIRST.txt`
