# V18.21A-R2 Price History Source Coverage Report

## Executive summary
- Status: WARN_V18_21A_R2_PRICE_HISTORY_SOURCE_COVERAGE_PATCH_DEGRADED
- Full-history ready: 104 / 325
- No local price data: 220

## Safety statement
- Advisory-only. No production wrappers, official decisions, ranking, promotion/demotion, technical timing, state, price cache, broker execution, auto-trade, or auto-sell behavior were modified.

## Price history source discovery summary
- Candidate sources: 350
- Full-history usable sources: 220
- Light-factor usable sources: 222

## Factor scope classification summary
- Full: 104; partial light: 0; latest-only: 1; none: 220

## Fatal vs latest-only vs partial-history explanation
- Fatal now means no usable local latest close/date. Latest-only and partial-history rows are separated from full-history factor-ready rows.

## Full-score vs light-score readiness summary
- Full score ready: 104; light score ready: 0

## Top list eligibility summary
- RS eligible: 104; buy-zone eligible: 76; breakout-volume eligible: 0

## Market regime and VIX missing cap summary
- VIX status: MISSING_LOCAL_PRICE_HISTORY; cap applied: TRUE; coefficient: 0.95

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check V18.21A: OK_COMPILE
- Python compile check V18.21A-R1: OK_COMPILE
- Python compile check V18.21A-R2: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- R2 output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- Validation fail count: 0

## Next-step recommendation
- Treat R2 as a source-coverage audit. Backfill or validate local history coverage before any stable snapshot or policy integration.
