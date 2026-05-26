# V18.12A Sell Timing Shadow Engine

## Status

- STATUS: OK_SELL_TIMING_SHADOW_READY
- SNAPSHOT_DATE: 2026-05-18
- MODE: SHADOW_ONLY
- POSITION_COUNT: 0
- ACTIONABLE_EXIT_COUNT: 0
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_SELL: DISABLED
- AUTO_TRADE: DISABLED

## Purpose

- V18.12A is a shadow-only sell/trim/hold review layer for current positions.
- It is designed to make exit timing inputs visible without changing official decisions.
- The logic is intentionally simple, transparent, and CSV/Markdown based.

## Safety Guardrails

- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_SELL: DISABLED
- AUTO_TRADE: DISABLED
- This is shadow-only review output. It is not a sell order and does not modify official daily decisions.
- Official daily runners and pointers are not modified by this module.

## Input Discovery

- Search roots: state/v18/simulation, outputs/v18/simulation, state/v18, outputs/v18.
- Candidate names include positions, current_positions, paper_positions, account, paper_pnl, sim_cabin, and candidate_tracker.
- Position-like sources are audited first, then the highest-priority open-position source is selected for review.
- Missing or non-position files are recorded in the audit CSV and do not fail the shadow run.

## No-Position Behavior

- If no open positions are found, the run still exits OK with POSITION_COUNT 0.
- The shadow CSV contains a NO_POSITION row and ACTIONABLE_EXIT_COUNT remains 0.

## Action Vocabulary

- HOLD: no current exit review signal.
- WATCH_EXIT: soft risk review.
- TRIM_REVIEW: partial trim review candidate.
- TAKE_PROFIT_REVIEW: profit-taking review candidate.
- STOP_LOSS_REVIEW: stop-loss review candidate.
- EXIT_REVIEW: highest-severity shadow exit review.
- NO_POSITION: no open position was available for review.
- SELL_NOW is intentionally not part of V18.12A output vocabulary.

## Output Files

- REPORT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_SHADOW_REPORT.md
- CSV: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_SHADOW.csv
- INPUT_AUDIT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_INPUT_AUDIT.csv

## Input Source Summary

- AVAILABLE_SOURCE_COUNT: 9
- SELECTED_POSITION_SOURCE_COUNT: 0
- SELECTED: NONE

## Position Summary

- POSITION_COUNT: 0
- OUTPUT_CSV: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_SHADOW.csv
- INPUT_AUDIT_CSV: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_INPUT_AUDIT.csv

## Exit Action Counts

- EXIT_REVIEW: 0
- STOP_LOSS_REVIEW: 0
- TAKE_PROFIT_REVIEW: 0
- TRIM_REVIEW: 0
- WATCH_EXIT: 0
- HOLD: 0
- NO_POSITION: 1

## Top Exit Review Rows

No actionable exit review rows.

## Notes

- V18.12A only creates CSV/MD review artifacts for sell, trim, watch, and hold review.
- It does not output SELL_NOW.
- It does not auto-sell, auto-trade, auto-promote, change weights, or modify official daily decision files.
- All rows keep OFFICIAL_DECISION_IMPACT as NONE, AUTO_SELL as DISABLED, and AUTO_TRADE as DISABLED.
- REPORT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_SHADOW_REPORT.md
