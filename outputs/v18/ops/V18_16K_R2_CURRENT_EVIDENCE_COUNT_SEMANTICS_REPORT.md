# V18.16K-R2 Evidence Count Semantics Report

## Executive summary
- Status: WARN_V18_16K_R2_EVIDENCE_COUNT_SEMANTICS_PATCH_DEGRADED
- Current true 5-day unique coverage met: FALSE
- Distinct valid scan days: 2 / 5
- Universe source counts: 324 to 325

## Safety statement
- Advisory-only patch. It creates R2 audit outputs and does not apply any recovery plan.
- Current daily behavior, official decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, and auto-sell remain unchanged.

## Evidence count semantics explanation
- Evidence file counts measure how many source artifacts were considered and how many contained valid dated ticker evidence.
- Distinct scan-day counts measure unique scan dates with valid ticker evidence after de-duplicating multiple files for the same date.

## Evidence file count vs distinct scan-day count
- Evidence files valid/considered: 6 / 7
- Distinct scan days valid/considered: 2 / 2
- Valid scan days used: 2026-05-20;2026-05-19

## Current true 5-day coverage status
- Coverage window complete: FALSE
- Unique coverage count: 134
- Shortfall: 190

## Universe count reconciliation
- Source disagreement: TRUE
- Review required: TRUE
- Selected/max counts: 324 / 325

## Conservative recovery plan summary
- Plan ready: TRUE
- Selected universe outcome: coverage 324, shortfall 0, solves TRUE
- Max-source universe outcome: coverage 324, shortfall 1, solves FALSE

## Why current status remains WARN
- The current evidence has fewer than five distinct valid scan days.
- Universe count sources still disagree, so max-source coverage is reported conservatively.

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check V18.16K: OK_COMPILE
- Python compile check V18.16K-R1: OK_COMPILE
- Python compile check V18.16K-R2: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- R2 output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- Validation fail count: 0

## Next-step recommendation
- Resolve the 324 vs 325 source-count discrepancy before treating any recovery plan as complete coverage proof.
