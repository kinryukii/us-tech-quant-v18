# V18.22D Daily Research Operator Homepage

Generated: 2026-05-21T13:35:32

## Overall operator status
Status: **WARN_V18_22D_DAILY_RESEARCH_OPERATOR_HOMEPAGE_READY**

Mode: **READ_ONLY_DAILY_RESEARCH_OPERATOR_HOMEPAGE**

This homepage is read-only. It summarizes current V18 research readiness after V18.22C and does not change trading decisions, rankings, factor weights, price history, state, event calendars, simulations, forward trackers, broker/manual execution state, or existing stable snapshots.

## Read-first file list with exact relative paths
- outputs/v18/ops/V18_22D_READ_FIRST.txt
- outputs/v18/operator_homepage/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md
- outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_GATE_SUMMARY.csv
- outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_SOURCE_AUDIT.csv
- outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_VALIDATION.csv
- outputs/v18/ops/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE_REPORT.md

## Current system readiness summary
- Stable layers: 9/9 OK
- Score-ready ratio: 0.320000
- Full-history factor-ready count: 104
- Missing history ticker count: 221
- Forward return filled: 0
- Forward return pending: 525
- High-confidence forward match count: 0
- Multi-horizon readiness: NOT_READY_MULTI_HORIZON
- Backtest execution readiness: BLOCKED_DESIGN_ONLY_FORWARD_RETURNS_PENDING

## Key metrics table
| Metric | Value |
| --- | --- |
| stable layer count | 9 |
| stable layer OK count | 9 |
| score-ready ratio | 0.320000 |
| full-history factor-ready count | 104 |
| missing history ticker count | 221 |
| forward tracker shadow rows | 525 |
| forward return filled | 0 |
| forward return pending | 525 |
| high-confidence forward match count | 0 |
| multi-horizon readiness | NOT_READY_MULTI_HORIZON |
| signal snapshot rows | 325 |
| signal snapshot history count | 1 |
| event final advisory market coefficient | 0.300000 |
| event risk coefficient applied to official decision | FALSE |
| backtest execution readiness | BLOCKED_DESIGN_ONLY_FORWARD_RETURNS_PENDING |

## Research gates table
| Gate | Allowed | Status | Operator instruction |
| --- | --- | --- | --- |
| factor_effect_claim_allowed | FALSE | BLOCKED | Do not claim factor effectiveness today. |
| weight_change_allowed | FALSE | BLOCKED | Do not change factor weights today. |
| production_promotion_allowed | FALSE | BLOCKED | Do not promote to production today. |
| backtest_execution_allowed | FALSE | BLOCKED | Do not execute backtests today. |
| staged_backfill_apply_allowed | FALSE | REQUIRES_EXPLICIT_APPROVAL | Do not run staged backfill apply today without explicit approval. |
| daily_command_center_integration_allowed | FALSE | BLOCKED | Do not integrate V18.22D into the daily command center today. |

## Blocked reasons table
| Blocked gate | Why blocked | Unlock condition |
| --- | --- | --- |
| factor_effect_claim_allowed | Requires forward return filled count > 0, high-confidence forward match count > 0, and multi-horizon readiness not NOT_READY_MULTI_HORIZON. | Filled forward returns, high-confidence matches, and multi-horizon readiness. |
| weight_change_allowed | Requires factor effect claim gate and non-blocked backtest execution readiness. | Validated factor effect evidence plus unblocked backtest readiness. |
| production_promotion_allowed | Requires weight-change gate plus explicit production integration that is present and safe. | Weight-change allowed and explicit production integration approval/presence. |
| backtest_execution_allowed | Forward returns are pending or readiness contains BLOCKED. | No pending forward returns and readiness not blocked. |
| staged_backfill_apply_allowed | Disabled by default for V18.22D; explicit approval required before staged fetch/import/apply. | Explicit operator approval for staged backfill apply. |
| daily_command_center_integration_allowed | Disabled by default for this read-only operator homepage step. | Separate approved integration step. |

## What is allowed today
- Read the V18.22D READ_FIRST file and homepage.
- Review V18.22C research packets and current/stable source files listed in the source audit.
- Preserve the current research state and wait for approved future steps.
- Discuss or plan staged backfill, forward return filling, or integration work without running it.

## What is not allowed yet
- Do not claim factor effectiveness.
- Do not change factor weights.
- Do not promote to production.
- Do not run backtests.
- Do not apply staged backfill or fetch/import external data without explicit approval.
- Do not integrate this homepage into the daily command center in this step.
- Do not modify price cache, price history, rankings, signal snapshots, event calendars, simulation positions, forward trackers, price factors, technical timing, promotion/demotion files, manual state, or broker execution state.

## Recommended next action
Read outputs/v18/ops/V18_22D_READ_FIRST.txt first; keep research gates blocked; do not run staged backfill, backtests, production promotion, or daily command center integration without a separate approved step.

## Source provenance and trust notes
Current source available: TRUE. Stable source available: TRUE. Missing source candidate count: 0.

Missing source candidates: None

| Source | Selected path | Role | Parse status |
| --- | --- | --- | --- |
| V18_22C_READ_FIRST | outputs/v18/ops/V18_22C_READ_FIRST.txt | current | TEXT_READ;KEYS=68 |
| V18_22C_REPORT | outputs/v18/ops/V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md | current | TEXT_READ;KEYS=4 |
| V18_22C_EXECUTIVE_BRIEF | outputs/v18/research_packets/V18_22C_CURRENT_EXECUTIVE_RESEARCH_BRIEF.md | current | TEXT_READ;KEYS=6 |
| V18_22C_DETAILED_PACKET | outputs/v18/research_packets/V18_22C_CURRENT_DETAILED_RESEARCH_PACKET.md | current | TEXT_READ;KEYS=6 |
| V18_22C_BLOCKED_GATE_EXPLANATION | outputs/v18/research_packets/V18_22C_CURRENT_BLOCKED_GATE_EXPLANATION.md | current | TEXT_READ;KEYS=5 |
| V18_22C_NEXT_ACTION_CHECKLIST | outputs/v18/research_packets/V18_22C_CURRENT_NEXT_ACTION_CHECKLIST.csv | current | CSV_ROWS=6;FIELDS=12 |
| V18_22C_DO_NOT_DO_YET_CHECKLIST | outputs/v18/research_packets/V18_22C_CURRENT_DO_NOT_DO_YET_CHECKLIST.csv | current | CSV_ROWS=10;FIELDS=7 |
| V18_22C_SOURCE_AUDIT | outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_SOURCE_AUDIT.csv | current | CSV_ROWS=16;FIELDS=8 |
| V18_22C_VALIDATION | outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_VALIDATION.csv | current | CSV_ROWS=28;FIELDS=4 |
| V18_22B_READ_FIRST | outputs/v18/ops/V18_22B_READ_FIRST.txt | current | TEXT_READ;KEYS=66 |
| V18_22B_GATE_SUMMARY | outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv | current | CSV_ROWS=8;FIELDS=6 |
| V18_22A_READ_FIRST | outputs/v18/ops/V18_22A_READ_FIRST.txt | current | TEXT_READ;KEYS=53 |

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
