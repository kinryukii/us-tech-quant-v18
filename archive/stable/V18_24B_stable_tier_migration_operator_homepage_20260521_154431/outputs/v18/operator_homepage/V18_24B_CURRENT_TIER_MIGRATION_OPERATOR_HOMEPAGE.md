# V18.24B Tier Migration Operator Homepage

Generated: 2026-05-21T15:32:21

## Overall Status
Status: WARN_V18_24B_TIER_MIGRATION_OPERATOR_HOMEPAGE_BASELINE_READY

## Tier Migration Status
V18.24A source available: TRUE. Current tickers: 324. Score source trust: HIGH.

## Baseline Vs Comparison Mode
Baseline mode: TRUE. If TRUE, upgrade/downgrade counts are expected to be zero until a later run compares against this baseline.

## Current Tier Distribution
| tier | count | operator_note |
| --- | --- | --- |
| TIER_1_CORE_CANDIDATE | 16 | Read-only tier migration category. |
| TIER_2_STRONG_WATCHLIST | 11 | Read-only tier migration category. |
| TIER_3_WATCHLIST | 9 | Read-only tier migration category. |
| TIER_4_REVIEW_ONLY | 16 | Read-only tier migration category. |
| TIER_5_WEAK_OR_BLOCKED | 51 | Read-only tier migration category. |
| TIER_0_DATA_NOT_READY | 221 | Read-only tier migration category. |

## Today's Upgrades
_None currently._

## Today's Downgrades
_None currently._

## Large Score Movers
_None currently._

## Newly Score-Ready / Data-Ready
_None currently._

## Data-Not-Ready Or Blocked Summary
Data-not-ready/blocked count: 221.
| summary_type | ticker | current_tier | data_readiness_status | held_out_status |
| --- | --- | --- | --- | --- |
| TOTAL_DATA_NOT_READY_OR_BLOCKED |  |  |  |  |
| SAMPLE | AA | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | AAL | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | ABR | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | ADBE | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | ADMA | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | ADSK | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | AEIS | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | AEVA | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | AFRM | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | AGX | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |
| SAMPLE | ALM | TIER_0_DATA_NOT_READY | DATA_NOT_READY |  |

## Top Tier 1 / Tier 2 Candidates
| ticker | current_tier | current_score | current_rank | latest_success_scan_date |
| --- | --- | --- | --- | --- |
| FORM | TIER_1_CORE_CANDIDATE | 100.000000 | 1 | 2026-05-21 |
| LITE | TIER_1_CORE_CANDIDATE | 99.050000 | 2 | 2026-05-21 |
| POWL | TIER_1_CORE_CANDIDATE | 98.100000 | 3 | 2026-05-21 |
| MU | TIER_1_CORE_CANDIDATE | 97.140000 | 4 | 2026-05-21 |
| SOXL | TIER_1_CORE_CANDIDATE | 96.190000 | 5 | 2026-05-21 |
| GLW | TIER_1_CORE_CANDIDATE | 95.240000 | 6 | 2026-05-21 |
| AEHR | TIER_1_CORE_CANDIDATE | 94.290000 | 7 | 2026-05-21 |
| ICHR | TIER_1_CORE_CANDIDATE | 93.330000 | 8 | 2026-05-21 |
| MOD | TIER_1_CORE_CANDIDATE | 92.380000 | 9 | 2026-05-21 |
| SNDK | TIER_1_CORE_CANDIDATE | 91.430000 | 10 | 2026-05-21 |
| INTC | TIER_1_CORE_CANDIDATE | 90.480000 | 11 | 2026-05-21 |
| WDC | TIER_1_CORE_CANDIDATE | 89.520000 | 12 | 2026-05-21 |
| AMKR | TIER_1_CORE_CANDIDATE | 88.570000 | 13 | 2026-05-21 |
| STX | TIER_1_CORE_CANDIDATE | 87.620000 | 14 | 2026-05-21 |
| FIX | TIER_1_CORE_CANDIDATE | 86.670000 | 15 | 2026-05-21 |
| COHU | TIER_1_CORE_CANDIDATE | 85.710000 | 16 | 2026-05-21 |
| KEYS | TIER_2_STRONG_WATCHLIST | 84.760000 | 17 | 2026-05-21 |
| CIEN | TIER_2_STRONG_WATCHLIST | 83.810000 | 18 | 2026-05-21 |
| CAMT | TIER_2_STRONG_WATCHLIST | 82.860000 | 19 | 2026-05-21 |
| FLEX | TIER_2_STRONG_WATCHLIST | 81.900000 | 20 | 2026-05-21 |

## Movement Reason Summary
| reason | count |
| --- | --- |
| NO_PRIOR_BASELINE | 324 |

## Coverage / Trust Notes
TRUE_5DAY_UNIQUE_COVERAGE_MET remains FALSE: FALSE_PARTIAL_LEDGER_COVERAGE_AFTER_R3.

## What Remains Blocked
Official ranking changes, factor effect claims, weight changes, production promotion, daily command center integration, backtests, auto-trade, and auto-sell remain blocked.

## Exact Files To Read Next
- D:\us-tech-quant\outputs\v18\operator_homepage\V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE.md
- D:\us-tech-quant\outputs\v18\tier_migration\V18_24B_CURRENT_OPERATOR_TIER_SUMMARY.csv
- D:\us-tech-quant\outputs\v18\tier_migration\V18_24B_CURRENT_OPERATOR_MOVEMENT_HIGHLIGHTS.csv
- D:\us-tech-quant\outputs\v18\tier_migration\V18_24B_CURRENT_OPERATOR_TOP_TIER_CANDIDATES.csv
- D:\us-tech-quant\outputs\v18\tier_migration\V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv

## Safety Invariants
Official decision impact: NONE. Ranking, factor pack, technical timing, signal snapshot, ledger, price cache, backtest, and trading state were not modified.

## Recommended Next Action
Read the V18.24B homepage first each day; rerun V18.24A after score/readiness changes to produce real upgrade/downgrade movement against this baseline.
