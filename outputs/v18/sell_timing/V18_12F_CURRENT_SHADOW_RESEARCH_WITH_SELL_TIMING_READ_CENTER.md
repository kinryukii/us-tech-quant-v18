# V18.12F Shadow Research Daily With Sell Timing Read Center

## Status

- STATUS: OK_V18_12F_SHADOW_RESEARCH_DAILY_WITH_SELL_TIMING_READY
- MODE: SHADOW_ONLY
- SHADOW_RESEARCH_STATUS: SKIPPED_USE_EXISTING_OUTPUTS
- SELL_TIMING_STATUS: OK_V18_12E_SELL_TIMING_DAILY_WRAPPER_READY
- POSITION_COUNT: 0
- ACTIONABLE_EXIT_COUNT: 0
- TECHNICAL_LABEL_SOURCE_COUNT: 17
- LIFECYCLE_STAGE_COUNT: 1
- TRACKER_ROWS: 1
- FORWARD_COMPLETE_ROWS: 0
- PENDING_FORWARD_ROWS: 0
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_SELL: DISABLED
- AUTO_TRADE: DISABLED

## Guardrails

- This is shadow-only research integration, not an official sell decision.
- Fast safe mode may reuse existing shadow research outputs without rerunning the full shadow research chain.
- It does not replace the official daily entry and does not affect official decisions.
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_SELL: DISABLED
- AUTO_TRADE: DISABLED

## Inputs

- SHADOW_RESEARCH_READ_FIRST: D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST.txt
- SELL_TIMING_READ_FIRST: D:\us-tech-quant\outputs\v18\sell_timing\V18_12E_READ_FIRST.txt
- SUMMARY_CSV: D:\us-tech-quant\outputs\v18\sell_timing\V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_SUMMARY.csv
- INPUT_AUDIT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_INPUT_AUDIT.csv
