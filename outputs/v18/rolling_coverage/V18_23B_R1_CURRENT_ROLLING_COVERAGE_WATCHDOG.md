# V18.23B-R1 Rolling Coverage Watchdog

Generated: 2026-05-21T14:17:00

## Status
Status: **WARN_V18_23B_R1_ROLLING_COVERAGE_WATCHDOG_READY**

Mode: **LOCAL_ONLY_ROLLING_COVERAGE_WATCHDOG_FORCE_SWEEP**

## Watchdog policy
Normal target scan count is 65. FORCE_STALE_SWEEP_MODE is TRUE because: STALE_OR_NEVER_SUCCESS_TICKERS_PRESENT_FORCE_ATTEMPT_REQUIRED.

Force sweep means force attempt, not guaranteed success. Local-only missing inputs remain skipped/stale until successful local scan evidence exists.

## Run metrics
| Metric | Value |
| --- | --- |
| total_universe_count | 324 |
| stale_or_overdue_ticker_count | 301 |
| selected_scan_count | 301 |
| success_scan_count | 80 |
| skipped_scan_count | 221 |
| force_still_stale_count | 221 |
| true_5day_unique_coverage_met | FALSE |
| coverage_trust_level | MEDIUM |

## Calendar note
The window is a calendar/run-count approximation from the local ledger, not exchange-calendar certified.

## Safety
| Invariant | Value |
| --- | --- |
| OFFICIAL_DECISION_IMPACT | NONE |
| BUY_PERMISSION_MODIFIED | FALSE |
| AUTO_TRADE | DISABLED |
| AUTO_SELL | DISABLED |
| EXTERNAL_DATA_FETCHED | FALSE |
| ROLLING_SCAN_DATA_FETCHED | FALSE |
| PRICE_CACHE_MODIFIED | FALSE |
| PRICE_HISTORY_WRITTEN | FALSE |
| STAGED_PRICE_HISTORY_WRITTEN | FALSE |
| RANKING_MODIFIED | FALSE |
| SIGNAL_SNAPSHOT_MODIFIED | FALSE |
| FACTOR_PACK_MODIFIED | FALSE |
| TECHNICAL_TIMING_MODIFIED | FALSE |
| BACKTEST_EXECUTED | FALSE |
| BACKTEST_RESULTS_APPLIED | FALSE |
| FACTOR_EFFECT_CLAIM_ALLOWED | FALSE |
| WEIGHT_CHANGE_ALLOWED | FALSE |
| PRODUCTION_PROMOTION_ALLOWED | FALSE |
| DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED | FALSE |

## Recommended next action
Continue local-only watchdog runs; stale tickers with missing local inputs remain priority until local data exists and a successful scan is recorded.
