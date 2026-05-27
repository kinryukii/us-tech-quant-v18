# V18.30A Daily Operator Control Center

## Read First
```text
STATUS: WARN_V18_30A_DAILY_OPERATOR_CONTROL_CENTER_REVIEW_NEEDED
MODE: READ_ONLY_DAILY_OPERATOR_CONTROL_CENTER
RUN_ID: V18_30A_20260524_172032
CURRENT_RECOMMENDATION_ROW_COUNT: 252
CURRENT_RANKED_CANDIDATE_ROW_COUNT: 252
THEME_CLASSIFICATION_ROW_COUNT: 252
UNKNOWN_PRIMARY_THEME_COUNT: 0
LATEST_SIGNAL_FREEZE_RUN_ID: V18_25A_R21_20260524_170725
LATEST_SIGNAL_FREEZE_DATE: 2026-05-24
LATEST_SIGNAL_FREEZE_TICKER_COUNT: 252
LATEST_FULL_SIGNAL_FREEZE_RUN_ID: V18_25A_R21_20260524_170725
LATEST_FULL_SIGNAL_FREEZE_DATE: 2026-05-24
LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT: 252
PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID: V18_25A_R21_20260523_235020
SAME_DAY_FULL_FREEZE_RUN_COUNT: 1
SAME_DAY_MULTIPLE_FREEZE_WARNING: FALSE
LATEST_RECOMMENDATION_SNAPSHOT_DATE: 2026-05-24
LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT: 252
SNAPSHOT_MATCHES_LATEST_FREEZE_DATE: TRUE
FORWARD_1D_FILLABLE_COUNT: 0
FORWARD_3D_FILLABLE_COUNT: 0
FORWARD_5D_FILLABLE_COUNT: 0
FORWARD_10D_FILLABLE_COUNT: 0
FORWARD_20D_FILLABLE_COUNT: 0
FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW: TRUE
CURRENT_OPERATOR_ACTION: WAIT_FOR_FUTURE_PRICE_DATA;READY_FOR_MANUAL_REVIEW;DO_NOT_AUTO_TRADE
MANUAL_REVIEW_READY: TRUE
AUTO_TRADE: DISABLED
AUTO_SELL: DISABLED
OFFICIAL_DECISION_IMPACT: NONE
FORBIDDEN_MODIFIED: FALSE
```

## Today's Operator Action
- `WAIT_FOR_FUTURE_PRICE_DATA;READY_FOR_MANUAL_REVIEW;DO_NOT_AUTO_TRADE`
- `MANUAL_REVIEW_READY: TRUE`
- `AUTO_TRADE: DISABLED`

## Current Recommendation Tier Counts
| recommendation_tier | count |
| --- | --- |
| DO_NOT_PRIORITIZE | 104 |
| SPECULATIVE_SATELLITE | 38 |
| WATCHLIST_STRONG | 38 |
| OVERHEATED_WAIT | 27 |
| TACTICAL_ENTRY | 24 |
| DEFENSIVE_HEDGE | 13 |
| CORE_CANDIDATE | 6 |
| ETF_OR_MACRO_EXPOSURE | 2 |

## Top CORE_CANDIDATE Names
- VIAV - Viavi Solutions Inc.
- TSEM - Tower Semiconductor Ltd.
- STM - STMicroelectronics N.V.
- TTMI - TTM Technologies Inc.
- SMTC - Semtech Corporation

## Top WATCHLIST_STRONG Names
- PUMP - ProPetro Holding Corp.
- QSR - Restaurant Brands International Inc.
- VIST - Vista Energy S.A.B. de C.V.
- WLK - Westlake Corporation
- USFD - US Foods Holding Corp.

## Top OVERHEATED_WAIT Names
- IGV - iShares Expanded Tech-Software Sector ETF
- AMAT - Applied Materials Inc.
- AAPL - Apple Inc.
- NTAP - NetApp Inc.
- NVDA - NVIDIA Corporation

## Top SPECULATIVE_SATELLITE Names
- SITM - SiTime Corporation
- BW - Babcock & Wilcox Enterprises Inc.
- PLUG - Plug Power Inc.
- TWLO - Twilio Inc.
- HTZ - Hertz Global Holdings Inc.

## Signal Freeze And Snapshot Alignment
| category | check_name | status | value | detail |
| --- | --- | --- | --- | --- |
| alignment | latest_recommendation_snapshot_date | PASS | 2026-05-24 | Latest snapshot from recommendation snapshot ledger |
| alignment | snapshot_matches_latest_freeze_date | PASS | TRUE | snapshot=2026-05-24 freeze=2026-05-24 |
| alignment | latest_freeze_run_id | PASS | V18_25A_R21_20260524_170725 | from R29A/R29B if available |
| alignment | latest_full_freeze_run_id | PASS | V18_25A_R21_20260524_170725 | directly selected from signal freeze ledger |
| alignment | same_day_multiple_freeze_warning | PASS | FALSE | multiple full freezes on the same signal date |

## Forward-Return And Backtest Readiness
| category | check_name | status | value | detail |
| --- | --- | --- | --- | --- |
| backtest | forward_fillable_total | WARN | 0 | R29A/R29B forward-return fillability |
| backtest | full_recommendation_tier_backtest_ready_now | PASS | TRUE | current system readiness |
| forward | forward_1d_fillable_count | WARN | 0 | R29A |
| forward | forward_3d_fillable_count | WARN | 0 | R29A |
| forward | forward_5d_fillable_count | WARN | 0 | R29A |
| forward | forward_10d_fillable_count | WARN | 0 | R29A |
| forward | forward_20d_fillable_count | WARN | 0 | R29A |

## Safety Status
| category | check_name | status | value | detail |
| --- | --- | --- | --- | --- |
| safety | auto_trade | PASS | DISABLED | No trading actions are enabled. |
| safety | auto_sell | PASS | DISABLED | No trading actions are enabled. |
| safety | official_decision_impact | PASS | NONE | Read-only control center. |

## Exact Next Commands To Run
- `./scripts/v18/run_v18_29C_daily_recommendation_tier_snapshot_ledger.ps1 -Root D:\us-tech-quant`
- `./scripts/v18/run_v18_29B_limited_signal_freeze_backtest.ps1 -Root D:\us-tech-quant`
- Re-run the control center after any new daily snapshot or price-data update.
