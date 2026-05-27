# V18.16K-R1 Coverage Evidence Quality Report

## Executive summary
- Status: WARN_V18_16K_R1_COVERAGE_EVIDENCE_QUALITY_PATCH_DEGRADED
- True 5-day unique coverage met: FALSE
- Unique coverage: 134 / 324
- Evidence status: WARN_FEWER_THAN_5_VALID_SCAN_DAYS;UNIVERSE_COUNT_SOURCE_DISAGREEMENT

## Safety statement
- Advisory-only patch. It writes R1 audit outputs and does not apply the recovery plan.
- Current daily behavior, decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, and auto-sell are unchanged.

## Universe count reconciliation
- Status: WARN_SOURCE_COUNTS_DISAGREE
- Selected source: D:\us-tech-quant\outputs\v18\universe\V18_CURRENT_UNIVERSE_ROLLING_STATE.csv
- Min/max parsed source counts: 324 / 325
- Source disagreement: TRUE
- Count evidence: 324 from D:\us-tech-quant\outputs\v18\universe\V18_CURRENT_UNIVERSE_ROLLING_STATE.csv; 324 from D:\us-tech-quant\state\v18\universe\V18_UNIVERSE_ROLLING_STATE.csv; 325 from D:\us-tech-quant\outputs\v18\universe\V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv; 325 from D:\us-tech-quant\outputs\v18\ops\V18_16F_READ_FIRST.txt; 325 from D:\us-tech-quant\outputs\v18\ops\V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt; 325 from D:\us-tech-quant\outputs\v18\ops\V18_16J_READ_FIRST.txt; 324 from D:\us-tech-quant\outputs\v18\ops\V18_16K_READ_FIRST.txt

## Evidence quality
- Valid scan-day evidence points: 8 / 9
- Scan days used: 2026-05-20;2026-05-19

## Duplicate scan detail
- Duplicate scan count: 57
- Detail output: outputs/v18/universe/V18_16K_R1_CURRENT_DUPLICATE_SCAN_DETAIL.csv

## 5-day recovery plan
- Plan ready: TRUE
- Day count: 5
- Expected unique coverage after plan: 324
- Expected shortfall after plan: 0
- The plan is advisory and was not applied.

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check V18.16K: OK_COMPILE
- Python compile check V18.16K-R1: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- R1 output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- Validation fail count: 0

## Next-step recommendation
- Treat the 324 vs 325 disagreement as an input governance item before stable snapshot. The R1 reconciliation CSV identifies which current rolling-state sources expose 324 and which READ_FIRST/policy context still reports or implies 325.
