# V18.21E-R1 Hard-Lock Overlay Semantics Report

## Executive Summary
Status: WARN_V18_21E_R1_HARD_LOCK_OVERLAY_SEMANTICS_READY. V18.21E-R1 separates calendar-derived event coefficients from existing hard-lock overlay context.

## Safety Statement
This patch is advisory-only. It does not modify official decisions, buy permission, current daily wrappers, rankings, signal snapshots, event calendars, simulation positions, forward tracker state, price cache, manual state, broker execution, auto-trade, or auto-sell behavior.

## Calendar-Derived Coefficient Summary
Calendar market coefficient: 1.000000. Calendar market level: NORMAL. Normalized events: 10.

## Hard-Lock Overlay Attribution Summary
Hard-lock overlay detected: TRUE. Dominant overlay type: OFFICIAL_NO_TRADE. Detected attribution rows: 12.

## Final Advisory Coefficient Semantics
Final advisory market coefficient: 0.300000. Final advisory level: HARD_LOCK_SOURCE_DETECTED. The overlay coefficient is not applied to official decisions.

## Ticker-Level Event Semantics Summary
Ticker rows: 325. Calendar high-risk tickers: 0. Calendar extreme-caution tickers: 0. Overlay affected tickers: 325.

## Event-Adjusted Candidate Semantics
Candidate rows: 325. Score-available rows: 105. Ranks are reported separately for calendar-only and advisory-overlay scores.

## Top List Sorting Explanation
Top event-risk tickers are sorted by lowest calendar ticker coefficient, then nearest calendar event, then ticker. If values are tied, alphabetical order is only a final tie-breaker and the audit states the sort metric.

## Validation Summary
Validation fail count: 0. Validation rows: 17.

## Next-Step Recommendation
Use R1 outputs for review and stable snapshot only. Any future integration into official daily behavior requires explicit approval.
