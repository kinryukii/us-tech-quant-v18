# V18.23A Rolling Research Coverage Controller

Generated: 2026-05-21T13:48:33

## Overall status
Status: **WARN_V18_23A_ROLLING_COVERAGE_CONTROLLER_READY**

Mode: **READ_ONLY_ROLLING_RESEARCH_COVERAGE_PLANNING**

## Purpose of this step
Create a read-only planning/read-center layer for rolling research coverage. It plans roughly full-universe coverage over 5 planning buckets without fetching data, scanning tickers, updating caches, running backtests, or changing trading decisions.

## Canonical universe source
outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv

## Key coverage metrics
| Metric | Value |
| --- | --- |
| total_universe_count | 324 |
| recommended_daily_scan_count | 65 |
| planned_scan_count_today | 65 |
| planned_bucket_index | 3 |
| estimated_full_cycle_coverage_count | 324 |
| estimated_full_cycle_coverage_ratio | 1.000000 |
| true_5day_unique_coverage_met | FALSE |
| true_5day_unique_coverage_status | UNPROVEN_PLANNING_ONLY;PARTIAL_LOCAL_SCAN_HISTORY |
| coverage_trust_level | MEDIUM |

## 5-day rolling bucket plan
| Bucket | Ticker count | Planned today | Coverage ratio |
| --- | --- | --- | --- |
| bucket_1 | 65 | FALSE | 0.200617 |
| bucket_2 | 65 | FALSE | 0.200617 |
| bucket_3 | 65 | TRUE | 0.200617 |
| bucket_4 | 65 | FALSE | 0.200617 |
| bucket_5 | 64 | FALSE | 0.197531 |

## Today planned scan list summary
Today is planning bucket 3 with 65 planned tickers. This is a deterministic planning index based on local date modulo 5, not an exchange-calendar guarantee.

## Coverage trust explanation
Coverage trust level: MEDIUM. Universe count is not suspiciously low.

## TRUE_5DAY_UNIQUE_COVERAGE status
UNPROVEN_PLANNING_ONLY;PARTIAL_LOCAL_SCAN_HISTORY. TRUE is only allowed when local scan-history evidence proves all canonical tickers were scanned within the target window.

## Source provenance
| Source | Exists | Ticker count | Selected | Notes |
| --- | --- | --- | --- | --- |
| outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv | TRUE | 324 | TRUE | Selected canonical universe source. |
| state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv | TRUE | 324 | FALSE | Usable fallback source. |
| outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | TRUE | 105 | FALSE | Usable fallback source. |
| outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv | TRUE | 20 | FALSE | Usable fallback source. |
| state/v18/raw105_universe_for_factor_lab.csv | TRUE | 105 | FALSE | Usable fallback source. |
| outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv | TRUE | 324 | FALSE | Usable fallback source. |
| outputs/v18/ops/V18_22D_STABLE_READ_FIRST.txt | TRUE |  | FALSE | Context/provenance source. |
| outputs/v18/operator_homepage/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md | TRUE |  | FALSE | Context/provenance source. |
| outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt | TRUE |  | FALSE | Context/provenance source. |
| outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt | TRUE |  | FALSE | Context/provenance source. |
| outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt | TRUE |  | FALSE | Context/provenance source. |
| state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json | TRUE |  | FALSE | Context/provenance source. |
| outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv | TRUE |  | FALSE | Context/provenance source. |
| outputs/v18/universe/V18_16I_CURRENT_RECOMMENDED_SCAN_PLAN.csv | TRUE |  | FALSE | Context/provenance source. |

## Missing/weak sources
Missing source count: 0. Missing: None.

## Allowed today
- Read this controller and V18.23A READ_FIRST.
- Review the deterministic rolling coverage plan.
- Use the plan as planning input for a later approved scanner.

## Not allowed yet
- Do not fetch external data.
- Do not execute rolling scans.
- Do not modify price cache, price history, rankings, signals, event calendars, state, simulations, forward trackers, broker/manual execution, or production decisions.
- Do not run backtests or apply factor effect, weight, promotion, staged backfill, or daily command center integration changes.

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

## Recommended next action
Review outputs/v18/ops/V18_23A_READ_FIRST.txt and the rolling coverage plan; do not execute scans or fetch data until a separate approved execution layer exists.
