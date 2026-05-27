# V18.10A Factor Registry + Coverage Audit

Generated: `2026-05-18 13:14:23`

## 1. Status

- STATUS: `OK_FACTOR_REGISTRY_COVERAGE_AUDIT_READY`
- MODE: `NO_BLACK_BOX_FACTOR_GOVERNANCE`
- OFFICIAL_DECISION_IMPACT: `NONE`
- AUTO_WEIGHT_CHANGE: `DISABLED`
- AUTO_PROMOTION: `DISABLED`
- AUTO_TRADE: `DISABLED`

## 2. Summary

- TOTAL_FACTOR_COUNT: `30`
- CAPTURED_FACTOR_OR_LABEL_COUNT: `22`
- OFFICIAL_CANDIDATE_COUNT: `7`
- OFFICIAL_CANDIDATE_CAPTURED_COUNT: `7`
- GATE_FACTOR_COUNT: `6`
- GATE_SOURCE_CAPTURED_COUNT: `3`
- VALIDATION_LABEL_COUNT: `4`
- VALIDATION_LABEL_CAPTURED_COUNT: `4`
- CSV_FILES_SCANNED: `50`

## 3. No-black-box rules

1. Hard gates are not weights.
2. Forward returns are validation labels, never decision-time inputs.
3. Every official candidate factor needs explicit name, direction, weight range, source, and principle.
4. Missing factor fields are not silently inferred.
5. This module cannot change official decisions.

## 4. Official candidate factor coverage

| factor_name | current_weight | range | coverage_status | matched_columns |
|---|---:|---:|---|---|
| trend_score | 0.25 | 0.15 - 0.35 | OFFICIAL_CANDIDATE_CAPTURED | F007_PULLBACK_IN_UPTREND | pullback_uptrend_raw | trend_ok_60_120 |
| relative_strength_score | 0.2 | 0.1 - 0.3 | OFFICIAL_CANDIDATE_CAPTURED | relative_strength_benchmark | relative_strength_benchmark_return_120d | relative_strength_benchmark_return_20d | relative_strength_benchmark_return_60d | relative_strength_method | relative_strength_raw | relative_strength_return_120d | relative_strength_return_20d | relative_strength_return_60d | relative_strength_score | relative_strength_status |
| pullback_quality_score | 0.2 | 0.1 - 0.3 | OFFICIAL_CANDIDATE_CAPTURED | signal_pullback_watch |
| momentum_continuation_score | 0.15 | 0.05 - 0.25 | OFFICIAL_CANDIDATE_CAPTURED | F011_TS_MOMENTUM_60_120 | signal_breakout_continuation | ts_momentum_raw |
| overheat_penalty | 0.1 | 0.05 - 0.2 | OFFICIAL_CANDIDATE_CAPTURED | overheat_penalty | signal_exhaustion_risk | signal_overheat_old | signal_overheat_unclassified |
| volatility_penalty | 0.05 | 0.0 - 0.15 | OFFICIAL_CANDIDATE_CAPTURED | ann_volatility_20d | volatility_penalty |
| execution_fit | 0.05 | 0.0 - 0.1 | OFFICIAL_CANDIDATE_CAPTURED | execution_fit | execution_fit_score | execution_fit_status |

## 5. Hard gates

| factor_name | role | coverage_status | matched_columns |
|---|---|---|---|
| data_freshness | hard_gate | GATE_SOURCE_CAPTURED | fwd_10d_price_date | fwd_1d_price_date | fwd_20d_price_date | fwd_5d_price_date | latest_price_date | obs_price_date_1 | obs_price_date_10 | obs_price_date_20 | obs_price_date_3 | obs_price_date_5 | price_date | snapshot_price_date |
| event_risk | hard_gate_or_downgrade_gate | GATE_DECLARED_SOURCE_NOT_FOUND |  |
| behavior_guard | hard_gate | GATE_DECLARED_SOURCE_NOT_FOUND |  |
| budget_constraint | hard_gate | GATE_SOURCE_CAPTURED | buy_permission | cash_usd | execution_cash_usd | execution_required_cash_usd | official_permission |
| position_cap | risk_constraint | GATE_SOURCE_CAPTURED | position_count |
| leveraged_etf_constraint | risk_constraint | GATE_DECLARED_SOURCE_NOT_FOUND |  |

## 6. Validation labels

| label | coverage_status | matched_columns |
|---|---|---|
| forward_return_1d | VALIDATION_LABEL_CAPTURED | fwd_1d_fill_method | fwd_1d_price_date | fwd_1d_price_usd | fwd_1d_return |
| forward_return_5d | VALIDATION_LABEL_CAPTURED | fwd_5d_fill_method | fwd_5d_price_date | fwd_5d_price_usd | fwd_5d_return |
| forward_return_10d | VALIDATION_LABEL_CAPTURED | fwd_10d_fill_method | fwd_10d_price_date | fwd_10d_price_usd | fwd_10d_return |
| forward_return_20d | VALIDATION_LABEL_CAPTURED | fwd_20d_fill_method | fwd_20d_price_date | fwd_20d_price_usd | fwd_20d_return | relative_strength_benchmark_return_20d | relative_strength_return_20d |

## 7. Missing official candidate fields

- None.

## 8. Files scanned

| rel_path | rows | columns |
|---|---:|---:|
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv | 93 | 57 |
| outputs\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv | 93 | 57 |
| outputs\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv | 31 | 44 |
| state\v18\V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_TRACKER.csv | 105 | 52 |
| outputs\v18\technical_timing_forward\V18_6C_R1_CURRENT_STALE_PRICE_AUDIT.csv | 0 | 32 |
| outputs\v18\simulation\V18_9B_CURRENT_FORWARD_RETURN_FILLER_AUDIT.csv | 93 | 8 |
| outputs\v18\ops\V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION_PROFILE.csv | 1 | 15 |
| outputs\v18\ops\V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION_STEPS.csv | 3 | 6 |
| state\v18\simulation\V18_CURRENT_PAPER_POSITIONS.csv | 0 | 10 |
| state\v18\simulation\V18_CURRENT_PAPER_TRADE_LOG.csv | 4 | 10 |
| state\v18\simulation\V18_CURRENT_SIM_ACCOUNT.csv | 1 | 5 |
| outputs\v18\simulation\V18_CURRENT_PAPER_PNL.csv | 3 | 11 |
| outputs\v18\simulation\V18_CURRENT_PAPER_POSITIONS.csv | 0 | 10 |
| outputs\v18\simulation\V18_CURRENT_PAPER_TRADE_LOG.csv | 4 | 10 |
| outputs\v18\technical_timing\V18_6A_CURRENT_TECHNICAL_TIMING.csv | 105 | 33 |
| outputs\v18\technical_timing\V18_6A_TECHNICAL_TIMING_20260518_130842.csv | 105 | 33 |
| outputs\v18\technical_timing\V18_6A_TECHNICAL_TIMING_20260518_131309.csv | 105 | 33 |
| outputs\v18\technical_timing_forward\V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv | 35 | 8 |
| outputs\v18\technical_timing_forward\V18_6C_R1_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv | 35 | 8 |
| outputs\v18\technical_timing_forward\V18_6C_R1_LOW_COVERAGE_SNAPSHOT_QUARANTINE.csv | 0 | 52 |
| outputs\v18\technical_timing_forward\V18_6C_R1_SNAPSHOT_DATE_DISTRIBUTION.csv | 1 | 4 |
| outputs\v18\factor_audit\V18_4D_CURRENT_FACTOR_PACK_AUDIT.csv | 8 | 14 |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260518_130616.csv | 8 | 14 |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260518_131117.csv | 8 | 14 |
| outputs\v18\factor_audit\V18_4E_CURRENT_FACTOR_OUTPUT_FORWARD_AUDIT.csv | 6 | 19 |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_130825.csv | 6 | 19 |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_131254.csv | 6 | 19 |
| outputs\v18\factor_audit\V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.csv | 6 | 8 |
| outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260518_130834.csv | 6 | 8 |
| outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260518_131302.csv | 6 | 8 |
| outputs\v18\factor_pack\V18_3D_R1_SHADOW_TOP30_OFFICIAL_OVERLAP.csv | 37 | 5 |
| outputs\v18\factor_pack\V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | 105 | 20 |
| outputs\v18\factor_pack\V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_VALUES.csv | 105 | 35 |
| outputs\v18\factor_pack\V18_3D_R2_CURRENT_SHADOW_TOP30_OFFICIAL_OVERLAP.csv | 37 | 5 |
| outputs\v18\factor_pack\V18_3D_RAW105_FACTOR_PACK_RANKING.csv | 105 | 20 |
| outputs\v18\factor_pack\V18_3D_RAW105_FACTOR_PACK_VALUES.csv | 105 | 35 |
| outputs\v18\factor_pack\V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | 105 | 20 |
| outputs\v18\factor_pack\V18_CURRENT_RAW105_FACTOR_PACK_VALUES.csv | 105 | 35 |
| outputs\v18\factor_pack\V18_CURRENT_SHADOW_TOP30_OFFICIAL_OVERLAP.csv | 37 | 5 |
| outputs\v18\promotion_merge\V18_4I_CURRENT_BACKTEST_FORWARD_PROMOTION_MERGE.csv | 6 | 27 |
| outputs\v18\promotion_merge\V18_4I_CURRENT_PROMOTION_CLUSTER.csv | 6 | 27 |
| outputs\v18\ops\V18_10D_CURRENT_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH_PROFILE.csv | 13 | 2 |
| outputs\v18\ops\V18_7A_CURRENT_FULL_SPEED_PROFILE.csv | 3 | 10 |
| outputs\v18\ops\V18_7B_CURRENT_MAIN_CHAIN_LINEAR_PROFILE.csv | 9 | 10 |
| outputs\v18\ops\V18_7D_CURRENT_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_PROFILE.csv | 6 | 10 |
| outputs\v18\ops\V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION_PROFILE.csv | 1 | 12 |
| outputs\v18\ops\V18_10D_CURRENT_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH_STEPS.csv | 2 | 4 |
| outputs\v18\ops\V18_11D_CURRENT_SHADOW_FACTOR_DAILY_STEPS.csv | 1 | 5 |
| outputs\v18\ops\V18_11F_CURRENT_SHADOW_FACTOR_RESEARCH_CHAIN_STEPS.csv | 2 | 5 |
| outputs\v18\ops\V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION_STEPS.csv | 2 | 6 |

## 9. Outputs

- FACTOR_REGISTRY: `D:\us-tech-quant\state\v18\factor_registry\V18_CURRENT_FACTOR_REGISTRY.csv`
- COVERAGE_AUDIT: `D:\us-tech-quant\outputs\v18\factor_registry\V18_10A_CURRENT_FACTOR_COVERAGE_AUDIT.csv`
- REPORT: `D:\us-tech-quant\outputs\v18\factor_registry\V18_10A_CURRENT_FACTOR_REGISTRY_REPORT.md`
- READ_FIRST: `D:\us-tech-quant\outputs\v18\factor_registry\V18_10A_READ_FIRST.txt`

## 10. Next step

Next recommended module: `V18.10B Factor Effectiveness Backtest`.

V18.10B should only start after confirming that the required factor columns and forward-return labels are being captured.
