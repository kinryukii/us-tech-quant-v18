# V18.4J Current Read Center

Generated at: 2026-05-30 22:37:25

## 1. Today Action

- FINAL_ACTION: BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION
- TODAY_SAFE: UNKNOWN
- BUY_PERMISSION: UNKNOWN
- ACTIONABLE_BUY_COUNT_TODAY: 20
- WORTH_REVIEW_BUT_LOCKED_COUNT: 0

Interpretation:

Today remains no new buy unless the official daily decision changes.

## 2. Factor Pack

- SELECTED_FACTOR: F002
- FACTOR_TOP10_NAMES: ORCL,DDOG,SNOW,SMCI,IYW,SNDK,QCOM,FLEX,NOW,NET
- OFFICIAL_REVIEW_NAMES: DELL,ARM,QCOM,SNOW,CRWV,NET,ANET,VST,FLR,ZS
- FACTOR_PACK_OVERLAP_NAMES: NONE

## 3. Forward Tracker

- TRACKER_TOTAL_ROWS: 630
- SNAPSHOT_DATE_COUNT: 6
- LATEST_SNAPSHOT_PRICE_DATE: 2026-05-29
- COMPLETED_1OBS_COUNT: 525
- COMPLETED_3OBS_COUNT: 315
- COMPLETED_5OBS_COUNT: 105
- COMPLETED_10OBS_COUNT: 0
- COMPLETED_20OBS_COUNT: 0

## 4. Promotion Status

- PROMOTION_RECOMMENDATION: KEEP_WATCHING
- PROMOTION_CANDIDATE_COUNT: 0
- REJECT_CANDIDATE_COUNT: 0
- GLOBAL_FORWARD_GATE: FORWARD_KEEP_WATCHING_NO_PROMOTION
- DIRECT_PROMOTION: NO
- OFFICIAL_DECISION_IMPACT: NONE
- PROMOTION_ACTION: NONE

## 5. Backtest Forward Promotion Cluster

- CORE_ALPHA_WATCH: F007_PULLBACK_IN_UPTREND
- PRIMARY_CONFIRMATION_WATCH: F009_VOLUME_PRICE_CONFIRM

Current interpretation:

- F007 is core alpha watch, but not promoted.
- F009 is primary confirmation watch, but not promoted.
- F010, F011, F008 and F006 remain auxiliary evidence only.
- Official decision impact remains NONE.

## 6. Factor Audit Health

- RUNTIME_CODE_COUNT: 38
- MISSING_REFERENCE_COUNT: 0
- WORLDQUANT_STYLE_FACTOR_FOUND_COUNT: 6
- OUTPUT_COLUMN_FOUND_COUNT: 6
- FORWARD_COVERED_COUNT: 6
- FORWARD_MISSING_COUNT: 0

## 7. Final Daily Command

powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"

## 8. Read Files

- V18.4I-R1 read first: D:\us-tech-quant\outputs\v18\daily_integrated\V18_4I_R1_READ_FIRST.txt
- Final daily promotion merge: D:\us-tech-quant\outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY_PROMOTION_MERGE.md
- Official daily read first: D:\us-tech-quant\outputs\v18\daily_integrated\V18_4B_R1_READ_FIRST.txt
- Factor audit read first: D:\us-tech-quant\outputs\v18\daily_integrated\V18_4G_R1_READ_FIRST.txt
- Promotion merge read first: D:\us-tech-quant\outputs\v18\promotion_merge\V18_4I_READ_FIRST.txt
- Promotion current: D:\us-tech-quant\outputs\v18\promotion_merge\V18_CURRENT_BACKTEST_FORWARD_PROMOTION.md
- Factor robustness interpretation: D:\us-tech-quant\outputs\v18\factor_backtest\V18_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md
- Forward summary: D:\us-tech-quant\outputs\v18\forward_outcome\V18_CURRENT_FORWARD_OUTCOME_SUMMARY.md
- Promotion rules: D:\us-tech-quant\outputs\v18\outcome_summary\V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md

## 9. Safety Guard

No factor research layer can bypass:

- event gate
- budget lock
- behavior guard
- official daily decision
- position cap

Therefore the current factor research layer remains evidence-only.
