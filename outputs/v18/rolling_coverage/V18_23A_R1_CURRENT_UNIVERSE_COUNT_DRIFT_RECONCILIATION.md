# V18.23A-R1 Universe Count Drift Reconciliation

Generated: 2026-05-21T13:55:50

## Overall reconciliation status
Status: **OK_V18_23A_R1_UNIVERSE_COUNT_DRIFT_RECONCILED**

Result: **EXPLAINED_EXPECTED_324**

## Why this patch exists
V18.23A produced a canonical universe count of 324, while recent research layers often reported around 325 ticker/signal rows. This patch reconciles the difference without modifying universe, ranking, signal, state, price, forward tracker, or trading decision files.

## V18.23A canonical universe summary
Canonical source: `outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv`

Canonical count: 324

## Prior/broader source comparison summary
| Source | Unique tickers | Trust | Role |
| --- | --- | --- | --- |
| outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv | 324 | HIGH | canonical_baseline |
| outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv | 324 | HIGH | selected_source |
| outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv | 324 | HIGH | signal_snapshot_reference |
| outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SNAPSHOT.csv | 324 | MEDIUM | signal_snapshot_reference |
| state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv | 324 | HIGH | state_reference_read_only |
| state/v18/universe/V18_MANUAL_UNIVERSE_ADDITIONS.csv | 275 | MEDIUM | manual_reference_read_only |
| outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | 105 | MEDIUM | ranked_subset |
| outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | 105 | MEDIUM | technical_subset |
| state/v18/raw105_universe_for_factor_lab.csv | 105 | LOW | factor_lab_subset |
| configs/v16/universe/us_full_screened_generated.yaml | 105 | LOW | config_reference |
| outputs/v18/rolling_coverage/V18_23A_CURRENT_TODAY_PLANNED_SCAN_LIST.csv | 65 | MEDIUM | planning_subset |
| outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv | 20 | MEDIUM | ranking_subset |

## 324 vs 325 explanation
Max reference universe count: 324. Sources with 325 or more tickers: 0. Count drift detected: FALSE. Count drift explained: TRUE.

## Missing/dropped ticker table
No valid missing ticker rows were found.

## Duplicate/blank/suspicious ticker analysis
Max duplicate ticker count: 0. Max blank ticker rows: 1. Suspicious ticker rows: 4.

| Source | Raw value | Normalized | Reason |
| --- | --- | --- | --- |
| V18_CURRENT_UNIVERSE_ROLLING_STATE | 105 | 105 | INVALID_OR_SUSPICIOUS_TICKER_FORMAT |
| V18_CURRENT_UNIVERSE_ROLLING_STATE | 325 | 325 | INVALID_OR_SUSPICIOUS_TICKER_FORMAT |
| STATE_V18_UNIVERSE_ROLLING_STATE | 105 | 105 | INVALID_OR_SUSPICIOUS_TICKER_FORMAT |
| STATE_V18_UNIVERSE_ROLLING_STATE | 325 | 325 | INVALID_OR_SUSPICIOUS_TICKER_FORMAT |

## Whether V18.23A stable snapshot is allowed
Allowed. Proceed to V18.23A stable snapshot.

## If not allowed, recommended repair path
Proceed to V18.23A stable snapshot.

## Source provenance and trust notes
The audit preserves source path, detected ticker column, raw row count, nonblank rows, unique normalized ticker count, duplicates, blanks, suspicious rows, role, and trust level for each source. Current files are preferred; this patch does not rewrite source selection.

## Safety invariants
| Invariant | Value |
| --- | --- |
| OFFICIAL_DECISION_IMPACT | NONE |
| BUY_PERMISSION_MODIFIED | FALSE |
| AUTO_TRADE | DISABLED |
| AUTO_SELL | DISABLED |
| CURRENT_DAILY_MODIFIED | FALSE |
| STATE_MODIFIED | FALSE |
| PRICE_CACHE_MODIFIED | FALSE |
| PRICE_HISTORY_WRITTEN | FALSE |
| STAGED_PRICE_HISTORY_WRITTEN | FALSE |
| RANKING_MODIFIED | FALSE |
| SIGNAL_SNAPSHOT_MODIFIED | FALSE |
| EVENT_CALENDAR_MODIFIED | FALSE |
| SIMULATION_POSITION_MODIFIED | FALSE |
| FORWARD_TRACKER_MODIFIED | FALSE |
| PRICE_FACTOR_MODIFIED | FALSE |
| TECHNICAL_TIMING_MODIFIED | FALSE |
| PROMOTION_DEMOTION_MODIFIED | FALSE |
| MANUAL_STATE_MODIFIED | FALSE |
| BROKER_EXECUTION_MODIFIED | FALSE |
| EXTERNAL_DATA_FETCHED | FALSE |
| BACKTEST_EXECUTED | FALSE |
| BACKTEST_RESULTS_APPLIED | FALSE |
| FACTOR_EFFECT_CLAIM_ALLOWED | FALSE |
| WEIGHT_CHANGE_ALLOWED | FALSE |
| PRODUCTION_PROMOTION_ALLOWED | FALSE |
| STAGED_BACKFILL_APPLY_ALLOWED | FALSE |
| DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED | FALSE |
| ROLLING_SCAN_EXECUTED | FALSE |
| ROLLING_SCAN_DATA_FETCHED | FALSE |
| ROLLING_SCAN_PLAN_MODIFIED | FALSE |
