# V18.21A-R1 Data Coverage + Scoring Semantics Report

## Executive summary
- Status: WARN_V18_21A_R1_DATA_COVERAGE_SCORING_PATCH_DEGRADED
- Score-ready tickers: 105 / 325
- Fatal failures: 220; partial degraded: 1

## Safety statement
- Advisory-only. No production wrapper, official decision, ranking, promotion/demotion, technical timing, state, cache, broker execution, auto-trade, or auto-sell behavior was modified.

## Data coverage summary
- Volume missing: 221
- 200DMA missing: 221
- 52W high missing: 221

## Fatal vs partial degradation explanation
- Fatal means no usable local close/date data. Missing long history, volume, 52W high, or proxy-dependent fields are partial degradation when basic scoring remains possible.

## Top list sorting explanation
- Near-buy-zone tickers are sorted by absolute nearest_buy_zone_distance ascending among valid buy-zone candidates.

## Market regime and VIX missing cap explanation
- VIX missing cap applied: TRUE; coefficient: 0.95

## Scoring coverage summary
- Score ready ratio: 0.323077

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check V18.21A: OK_COMPILE
- Python compile check V18.21A-R1: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- R1 output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- Validation fail count: 0

## Next-step recommendation
- Use R1 outputs to decide whether local price coverage should be backfilled before any later policy or ranking integration.
