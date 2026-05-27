# V18 Current Position Sizing Policy

STATUS: WARN_V18_31B_MANUAL_POSITION_SIZING_POLICY_REVIEW_NEEDED
RUN_ID: V18_31B_20260524_182840
GENERATED_AT: 2026-05-24T18:28:40

## Account-Size Assumptions
- Account size USD: `2000.00`
- Cash reserve pct: `15.00`
- Max active positions: `8`
- Max speculative positions: `2`

## Position Status Counts
| position_policy_status | count |
| --- | --- |
| POSITION_OPERATOR_BLOCKED | 252 |

## Top POSITION_ALLOWED
_None._

## Top POSITION_SMALL_ONLY
_None._

## WATCH_ONLY / WAIT_PULLBACK Summary
_None._

## Risk Budget Policy Table
| recommendation_tier | risk_budget_pct | stop_review_pct | take_profit_review_pct | initial_cap_pct | max_cap_pct |
| --- | --- | --- | --- | --- | --- |
| CORE_CANDIDATE | 0.75 | -7.00 | 15.00 | 6.00 | 12.00 |
| WATCHLIST_STRONG | 0.50 | -6.00 | 10.00 | 4.00 | 8.00 |
| TACTICAL_ENTRY | 0.40 | -5.00 | 8.00 | 3.00 | 6.00 |
| SPECULATIVE_SATELLITE | 0.25 | -10.00 | 15.00 | 1.50 | 3.00 |
| DEFENSIVE_HEDGE | 0.50 | -6.00 | 8.00 | 4.00 | 10.00 |
| ETF_OR_MACRO_EXPOSURE | 0.40 | -5.00 | 7.00 | 3.00 | 8.00 |
| OVERHEATED_WAIT | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| DO_NOT_PRIORITIZE | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Safety
- Manual research guidance only.
- No broker connection.
- No order placement.
- Does not override operator judgment.
- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `OFFICIAL_DECISION_IMPACT: NONE`

## Warnings
- `FORWARD_RETURN_NOT_READY_STATIC_POLICY_ONLY`
- `R30A_R30E_OR_R31A_WARN_REVIEW_NEEDED`

## Next Step Recommendation
- R31C Moomoo cost/slippage model.
- R31D account-aware manual plan later.
