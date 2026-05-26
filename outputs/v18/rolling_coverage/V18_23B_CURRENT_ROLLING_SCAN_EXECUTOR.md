# V18.23B Rolling Scan Executor

Generated: 2026-05-21T14:09:31

## Status
Status: **WARN_V18_23B_ROLLING_SCAN_EXECUTOR_READY**

Mode: **LOCAL_ONLY_ROLLING_SCAN_EXECUTION**

## Local-only execution
V18.23B executes a local-only rolling scan over selected tickers and updates only the dedicated ledger `D:\us-tech-quant\state\v18\rolling_coverage\V18_23B_ROLLING_SCAN_LEDGER.csv` plus V18.23B output files. It does not fetch data, modify price cache, rewrite rankings, rewrite factor packs, rewrite technical timing, run backtests, or affect trading decisions.

## Run summary
| Metric | Value |
| --- | --- |
| total_universe_count | 324 |
| target_scan_count_per_run | 65 |
| selected_scan_count | 65 |
| success_scan_count | 23 |
| skipped_scan_count | 42 |
| failed_scan_count | 0 |
| unique_success_scanned_within_window_count | 23 |
| true_5day_unique_coverage_met | FALSE |
| coverage_trust_level | MEDIUM |

## Coverage window note
The 5-day coverage audit uses local ledger dates and a simple calendar approximation. It is not exchange-calendar certified.

## Source audit
| Source | Exists | Ticker count | Selected | Notes |
| --- | --- | --- | --- | --- |
| outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv | TRUE | 324 | TRUE | ticker_column=ticker |
| outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv | TRUE | 324 | FALSE | ticker_column=ticker |
| outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | TRUE | 105 | FALSE | Read-only local factor availability source. |
| outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | TRUE | 105 | FALSE | Read-only local technical timing availability source. |

## Safety invariants
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
Run V18.23B again on later cycles to scan the next least-recently-successful tickers; do not fetch data or modify official ranking/price/trading files.
