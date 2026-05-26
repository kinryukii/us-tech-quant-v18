# V18.12B Sell Timing Technical Label Integration

## Status

- STATUS: OK_SELL_TIMING_TECHNICAL_LABEL_READY
- MODE: SHADOW_ONLY
- POSITION_COUNT: 0
- ACTIONABLE_EXIT_COUNT: 0
- TECHNICAL_LABEL_SOURCE_COUNT: 17
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_SELL: DISABLED
- AUTO_TRADE: DISABLED

## Safety Guardrails

- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_SELL: DISABLED
- AUTO_TRADE: DISABLED
- SHADOW_ONLY: technical labels create review context only.
- This is not a sell order and does not affect official decisions, trading logic, or factor weights.

## Input Source Summary

- V18_12A_INPUT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12A_CURRENT_SELL_TIMING_SHADOW.csv
- INPUT_AUDIT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12B_CURRENT_TECHNICAL_LABEL_INPUT_AUDIT.csv

## Technical Label Source Summary

- AVAILABLE_SOURCE_COUNT: 76
- USED_LABEL_SOURCE_COUNT: 17
- USED: D:\us-tech-quant\outputs\v18\technical_timing\V18_6A_CURRENT_TECHNICAL_TIMING.csv (label_hits=14)
- USED: D:\us-tech-quant\outputs\v18\technical_timing\V18_6A_CURRENT_TECHNICAL_TIMING_REPORT.md (label_hits=2)
- USED: D:\us-tech-quant\outputs\v18\technical_timing\V18_6A_TECHNICAL_TIMING_20260518_130842.csv (label_hits=14)
- USED: D:\us-tech-quant\outputs\v18\technical_timing\V18_6A_TECHNICAL_TIMING_20260518_131309.csv (label_hits=14)
- USED: D:\us-tech-quant\outputs\v18\technical_timing\V18_CURRENT_TECHNICAL_TIMING.md (label_hits=2)
- USED: D:\us-tech-quant\outputs\v18\factor_research\V18_11C_CURRENT_CALENDAR_VWAP_RV_SHADOW_FACTORS.csv (label_hits=204)
- USED: D:\us-tech-quant\outputs\v18\factor_research\V18_11E_CURRENT_SHADOW_FACTOR_SUMMARY.csv (label_hits=21)
- USED: D:\us-tech-quant\outputs\v18\factor_research\V18_11E_CURRENT_SHADOW_FACTOR_SUMMARY.md (label_hits=4)
- USED: D:\us-tech-quant\outputs\v18\factor_research\V18_11E_READ_FIRST.txt (label_hits=5)
- USED: D:\us-tech-quant\outputs\v18\factor_research\V18_11F_CURRENT_SHADOW_FACTOR_RESEARCH_CHAIN.md (label_hits=5)
- USED: D:\us-tech-quant\outputs\v18\factor_research\V18_11F_READ_FIRST.txt (label_hits=5)
- USED: D:\us-tech-quant\state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv (label_hits=210)
- USED: D:\us-tech-quant\outputs\v18\simulation\V18_9A_CURRENT_SIM_CANDIDATE_TRACKER.md (label_hits=4)
- USED: D:\us-tech-quant\outputs\v18\simulation\V18_9B_CURRENT_FORWARD_RETURN_FILLER.md (label_hits=4)
- USED: D:\us-tech-quant\outputs\v18\simulation\V18_9B_CURRENT_FORWARD_RETURN_FILLER_AUDIT.csv (label_hits=93)

## Position Summary

- POSITION_COUNT: 0
- OUTPUT_CSV: D:\us-tech-quant\outputs\v18\sell_timing\V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL.csv

## Exit Action Counts

- EXIT_REVIEW: 0
- STOP_LOSS_REVIEW: 0
- TAKE_PROFIT_REVIEW: 0
- TRIM_REVIEW: 0
- WATCH_EXIT: 0
- HOLD: 0
- NO_POSITION: 1

## Top Technical Exit Review Rows

No actionable technical exit review rows.

## Notes

- V18.12B is additive to V18.12A and preserves V18.12A stable files.
- Combined action uses the stronger of V18.12A shadow_exit_action and V18.12B technical_exit_action.
- Immediate sell action vocabulary is intentionally excluded.
- Outputs are review-only shadow artifacts.
- REPORT: D:\us-tech-quant\outputs\v18\sell_timing\V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL_REPORT.md
