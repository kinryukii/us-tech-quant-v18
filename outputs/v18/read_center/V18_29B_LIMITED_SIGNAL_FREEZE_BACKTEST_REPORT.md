# V18.29B Limited Historical Signal-Freeze Backtest

## Read First
```text
STATUS: WARN_V18_29B_LIMITED_SIGNAL_FREEZE_BACKTEST_REVIEW_NEEDED
MODE: LIMITED_HISTORICAL_SIGNAL_FREEZE_BACKTEST
RUN_ID: V18_29B_20260523_163216
SIGNAL_FREEZE_LEDGER_AVAILABLE: TRUE
HISTORICAL_SIGNAL_FREEZE_RUN_COUNT: 6
TOTAL_FROZEN_ROWS: 1122
UNIQUE_TICKER_COUNT: 252
PRICE_CACHE_COVERAGE_COUNT: 252
RUNS_WITH_1D_FILLABLE: 0
RUNS_WITH_3D_FILLABLE: 0
RUNS_WITH_5D_FILLABLE: 0
RUNS_WITH_10D_FILLABLE: 0
RUNS_WITH_20D_FILLABLE: 0
TOTAL_1D_FILLABLE_ROWS: 0
TOTAL_3D_FILLABLE_ROWS: 0
TOTAL_5D_FILLABLE_ROWS: 0
TOTAL_10D_FILLABLE_ROWS: 0
TOTAL_20D_FILLABLE_ROWS: 0
LATEST_FREEZE_RUN_ID: V18_25A_R21_20260523_022643
LATEST_FREEZE_SIGNAL_DATE: 2026-05-23
LATEST_FREEZE_INCLUDED_IN_METRICS: FALSE
CURRENT_RECOMMENDATION_TIERS_USED_HISTORICALLY: FALSE
FULL_RECOMMENDATION_TIER_BACKTEST_READY: FALSE
SURVIVORSHIP_BIAS_RISK: MEDIUM
LOOKAHEAD_BIAS_RISK: LOW
DATE_ALIGNMENT_RISK: HIGH
TRANSACTION_COST_MODEL_READY: FALSE
OFFICIAL_DECISION_IMPACT: NONE
AUTO_TRADE: DISABLED
AUTO_SELL: DISABLED
FORBIDDEN_MODIFIED: FALSE
```

## Scope Limitations
- This is a limited signal-freeze backtest, not a full recommendation-tier backtest.
- Current recommendation_tier labels are not used historically.
- Entry convention: close on the first cached trading date on or after signal_date.
- Exit convention: close after N cached trading bars from entry; prices before or on signal_date are not used as forward endpoints.
- Latest freezes with no future prices are included in coverage diagnostics and excluded from filled return metrics.

## Historical Signal Freeze Run Coverage
| run_id | signal_date | frozen_row_count | unique_ticker_count | forward_1d_fillable_count | forward_3d_fillable_count | forward_5d_fillable_count | forward_10d_fillable_count | forward_20d_fillable_count | included_in_metrics | run_warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V18_25A_R21_20260522_140438 | 2026-05-22 | 20 | 20 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260522_184530 | 2026-05-22 | 250 | 250 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260522_191554 | 2026-05-22 | 250 | 250 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260522_191703 | 2026-05-22 | 250 | 250 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260523_022515 | 2026-05-23 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260523_022643 | 2026-05-23 | 252 | 252 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS;LATEST_FREEZE_EXCLUDED_FROM_FILLED_METRICS |

## Forward Return Fillability By Run
| run_id | signal_date | frozen_row_count | unique_ticker_count | forward_1d_fillable_count | forward_3d_fillable_count | forward_5d_fillable_count | forward_10d_fillable_count | forward_20d_fillable_count | included_in_metrics | run_warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V18_25A_R21_20260522_140438 | 2026-05-22 | 20 | 20 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260522_184530 | 2026-05-22 | 250 | 250 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260522_191554 | 2026-05-22 | 250 | 250 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260522_191703 | 2026-05-22 | 250 | 250 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260523_022515 | 2026-05-23 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS |
| V18_25A_R21_20260523_022643 | 2026-05-23 | 252 | 252 | 0 | 0 | 0 | 0 | 0 | FALSE | NO_FILLABLE_FORWARD_RETURNS;LATEST_FREEZE_EXCLUDED_FROM_FILLED_METRICS |

## Rank Bucket Performance By Horizon
| horizon | bucket_type | bucket_name | observation_count | fillable_count | avg_forward_return | median_forward_return | win_rate | loss_rate | best_return | worst_return | standard_deviation | spread_vs_rest | spread_vs_lowest_bucket |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1D | rank_bucket | TOP_10 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | rank_bucket | TOP_20 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | rank_bucket | TOP_30 | 50 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | rank_bucket | TOP_50 | 100 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | rank_bucket | TOP_100 | 250 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | rank_bucket | REST | 602 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | rank_bucket | TOP_10 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | rank_bucket | TOP_20 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | rank_bucket | TOP_30 | 50 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | rank_bucket | TOP_50 | 100 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | rank_bucket | TOP_100 | 250 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | rank_bucket | REST | 602 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | rank_bucket | TOP_10 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | rank_bucket | TOP_20 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | rank_bucket | TOP_30 | 50 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | rank_bucket | TOP_50 | 100 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | rank_bucket | TOP_100 | 250 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | rank_bucket | REST | 602 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | rank_bucket | TOP_10 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | rank_bucket | TOP_20 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | rank_bucket | TOP_30 | 50 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | rank_bucket | TOP_50 | 100 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | rank_bucket | TOP_100 | 250 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | rank_bucket | REST | 602 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | rank_bucket | TOP_10 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | rank_bucket | TOP_20 | 60 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | rank_bucket | TOP_30 | 50 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | rank_bucket | TOP_50 | 100 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | rank_bucket | TOP_100 | 250 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | rank_bucket | REST | 602 | 0 |  |  |  |  |  |  |  |  |  |

## Score Bucket Performance By Horizon
| horizon | bucket_type | bucket_name | observation_count | fillable_count | avg_forward_return | median_forward_return | win_rate | loss_rate | best_return | worst_return | standard_deviation | spread_vs_rest | spread_vs_lowest_bucket |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1D | score_bucket | score_quantile_1_highest | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | score_bucket | score_quantile_2 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | score_bucket | score_quantile_3 | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | score_bucket | score_quantile_4 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 1D | score_bucket | score_quantile_5_lowest | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | score_bucket | score_quantile_1_highest | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | score_bucket | score_quantile_2 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | score_bucket | score_quantile_3 | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | score_bucket | score_quantile_4 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 3D | score_bucket | score_quantile_5_lowest | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | score_bucket | score_quantile_1_highest | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | score_bucket | score_quantile_2 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | score_bucket | score_quantile_3 | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | score_bucket | score_quantile_4 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 5D | score_bucket | score_quantile_5_lowest | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | score_bucket | score_quantile_1_highest | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | score_bucket | score_quantile_2 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | score_bucket | score_quantile_3 | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | score_bucket | score_quantile_4 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 10D | score_bucket | score_quantile_5_lowest | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | score_bucket | score_quantile_1_highest | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | score_bucket | score_quantile_2 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | score_bucket | score_quantile_3 | 225 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | score_bucket | score_quantile_4 | 224 | 0 |  |  |  |  |  |  |  |  |  |
| 20D | score_bucket | score_quantile_5_lowest | 224 | 0 |  |  |  |  |  |  |  |  |  |

## Top-Minus-Rest Spread
_None._

## Top-Minus-Bottom Score Bucket Spread
_None._

## Data Quality And Bias Warnings
- SURVIVORSHIP_BIAS_RISK: MEDIUM
- LOOKAHEAD_BIAS_RISK: LOW
- DATE_ALIGNMENT_RISK: HIGH
- TRANSACTION_COST_MODEL_READY: FALSE
- ETF/macro instruments are flagged with current metadata when available, but are not silently removed.

## Not A Full Recommendation-Tier Backtest
Historical recommendation-tier snapshots do not exist, so this report only evaluates frozen rank and frozen score buckets from the signal freeze ledger.

## Next-Step Recommendation
- Wait for post-freeze local price bars before relying on forward-return metrics for the 2026-05-23 run.
- Build dated recommendation-tier snapshots before attempting a full historical recommendation-tier backtest.
- Add an explicit transaction-cost/slippage model before using results for production-like performance claims.
