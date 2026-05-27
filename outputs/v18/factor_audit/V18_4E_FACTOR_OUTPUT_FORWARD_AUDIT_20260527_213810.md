# V18.4E Factor Output + Forward Tracking Audit

Generated: `20260527_213810`

## 1. Status

- V18_4E_STATUS: `OK_FACTOR_OUTPUT_FORWARD_AUDIT_READY`
- AUDIT_ENGINE: `V18.7C_FAST_TARGETED`
- RUNTIME_CODE_COUNT: `38`
- MISSING_REFERENCE_COUNT: `0`
- WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED: `6`
- OUTPUT_COLUMN_FOUND_COUNT: `6`
- NON_NULL_VALUE_FACTOR_COUNT: `6`
- TOP_OR_RANK_OUTPUT_FOUND_COUNT: `6`
- FORWARD_TRACKING_FOUND_COUNT: `6`
- CURRENT_SELECTED_FACTOR: `F002`
- TARGET_CSV_FILE_COUNT: `675`
- TARGET_TEXT_FILE_COUNT: `675`

## 2. Factor Output / Forward Coverage

| factor | name | output column | non-null | top/rank output | forward tracking | matched cols | non-null values |
|---|---|---|---|---|---|---:|---:|
| F006 | SHORT_REV_5D | OUTPUT_COLUMN_FOUND | HAS_NON_NULL_VALUES | FOUND_IN_TOP_OR_RANK_OUTPUTS | FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES | 36 | 4153 |
| F007 | PULLBACK_IN_UPTREND | OUTPUT_COLUMN_FOUND | HAS_NON_NULL_VALUES | FOUND_IN_TOP_OR_RANK_OUTPUTS | FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES | 110 | 11990 |
| F008 | VOLUME_ABNORMAL_5_20 | OUTPUT_COLUMN_FOUND | HAS_NON_NULL_VALUES | FOUND_IN_TOP_OR_RANK_OUTPUTS | FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES | 33 | 3838 |
| F009 | VOLUME_PRICE_CONFIRM | OUTPUT_COLUMN_FOUND | HAS_NON_NULL_VALUES | FOUND_IN_TOP_OR_RANK_OUTPUTS | FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES | 36 | 4153 |
| F010 | XSEC_COMPOSITE_RANK | OUTPUT_COLUMN_FOUND | HAS_NON_NULL_VALUES | FOUND_IN_TOP_OR_RANK_OUTPUTS | FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES | 36 | 4153 |
| F011 | TS_MOMENTUM_60_120 | OUTPUT_COLUMN_FOUND | HAS_NON_NULL_VALUES | FOUND_IN_TOP_OR_RANK_OUTPUTS | FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES | 36 | 4153 |

## 3. Interpretation

- V18.7C uses targeted current output/state directories instead of scanning the entire outputs/state tree.
- This is intended to preserve the audit contract while reducing repeated filesystem and CSV IO.
- OFFICIAL_DECISION_IMPACT remains NONE.

## 4. Selected Factor Sources

- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4A_R1_CURRENT_DAILY_INTEGRATED.md`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4A_R1_CURRENT_DAILY_INTEGRATED.txt`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4A_R1_READ_FIRST.txt`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4B_R1_CURRENT_FINAL_DAILY.md`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4B_R1_CURRENT_FINAL_DAILY.txt`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4B_R1_READ_FIRST.txt`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4G_R1_READ_FIRST.txt`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_CURRENT_DAILY_INTEGRATED.md`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY.md`
- `D:\us-tech-quant\outputs\v18\factor_shadow\V18_3A_FACTOR_SHADOW_AUDIT.csv`
- `D:\us-tech-quant\outputs\v18\factor_shadow\V18_3A_READ_FIRST.txt`
- `D:\us-tech-quant\outputs\v18\outcome_summary\V18_4B_CURRENT_PROMOTION_RULES.md`
- `D:\us-tech-quant\outputs\v18\outcome_summary\V18_4B_READ_FIRST.txt`
- `D:\us-tech-quant\outputs\v18\outcome_summary\V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md`
