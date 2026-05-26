# V18.16K True 5-Day Unique Coverage Scheduler Audit

## Executive summary
- Status: WARN_V18_16K_TRUE_5DAY_UNIQUE_COVERAGE_AUDIT_DEGRADED
- True 5-day unique coverage met: FALSE
- Unique covered tickers: 134 / 324
- Shortfall: 190

## Safety statement
- This module is advisory-only. It writes audit outputs only and does not apply policy.
- Official decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, and auto-sell behavior are unchanged.

## Input files used
- D:\us-tech-quant\outputs\v18\universe\V18_CURRENT_UNIVERSE_ROLLING_STATE.csv
- D:\us-tech-quant\outputs\v18\universe\V18_16A_CURRENT_UNIVERSE_ROLLING_STATE_AUDIT.csv
- D:\us-tech-quant\state\v18\universe\V18_UNIVERSE_ROLLING_STATE.csv
- D:\us-tech-quant\outputs\v18\universe\V18_CURRENT_ROLLING_SCAN_PLAN.csv
- D:\us-tech-quant\outputs\v18\universe\V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv
- D:\us-tech-quant\outputs\v18\universe\V18_CURRENT_ROLLING_SCAN_COVERAGE_AUDIT.csv
- D:\us-tech-quant\outputs\v18\ops\V18_16I_READ_FIRST.txt
- D:\us-tech-quant\outputs\v18\ops\V18_16J_READ_FIRST.txt
- D:\us-tech-quant\outputs\v18\universe\V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv

## Missing/degraded inputs
- None

## Coverage summary
- Coverage evidence status: WARN_FEWER_THAN_5_VALID_SCAN_DAYS
- Scan days used: 2026-05-20;2026-05-19
- Required daily scan count: 65
- Current daily scan count: 65

## Uncovered ticker summary
- Uncovered ticker count: 190
- Full list is in outputs/v18/universe/V18_16K_CURRENT_UNCOVERED_TICKERS.csv

## Duplicate scan summary
- Duplicate scan count: 57
- Duplicate tickers are listed in outputs/v18/universe/V18_16K_CURRENT_DUPLICATE_SCAN_AUDIT.csv

## Recommended next scan plan summary
- Recommended next scan count: 65
- The plan prioritizes uncovered tickers first, then oldest scan evidence. It is not applied.

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- Output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- Validation fail count: 0

## Next-step recommendation
- Review the uncovered ticker CSV and use the advisory next scan plan as the next scheduler input candidate if production policy owners choose to apply a future change.

## R1 Evidence Quality Patch
- Reconciliation status: WARN_SOURCE_COUNTS_DISAGREE
- Selected total universe source: D:\us-tech-quant\outputs\v18\universe\V18_CURRENT_UNIVERSE_ROLLING_STATE.csv
- Scan-day evidence valid/considered: 8 / 9
- Recovery plan ready: TRUE
