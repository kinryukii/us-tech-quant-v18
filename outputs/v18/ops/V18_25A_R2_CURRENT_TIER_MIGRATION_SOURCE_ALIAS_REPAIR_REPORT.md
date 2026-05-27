# V18.25A R2 Tier Migration CSV Alias Repair

- STATUS: OK_V18_25A_R2_TIER_MIGRATION_SOURCE_ALIAS_REPAIR_READY
- MODE: READ_ONLY_TIER_MIGRATION_SOURCE_ALIAS_REPAIR
- GENERATED_AT: 2026-05-21T21:53:43
- ALIAS_CREATED: TRUE
- SOURCE_PATH: D:\us-tech-quant\outputs\v18\tier_migration\V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv
- ALIAS_PATH: outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.csv
- SELECTED_SOURCE_KIND: V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv
- WARNING_COUNT: 0
- REQUIRED_FIELD_MISSING_COUNT: 0

## Source Selection

| candidate_name | exists | row_count | selected | selection_score | selection_reason |
| --- | --- | ---: | --- | ---: | --- |
| V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv | TRUE | 324 | TRUE | 39 | selected:ticker_level_csv |
| V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv | TRUE | 324 | FALSE | 29 | ticker_level_csv |
| V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.md | TRUE | 27 | FALSE | 0 | ticker_level_csv |
| V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE.md | TRUE | 82 | FALSE | 0 | ticker_level_csv |

## Safety

- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- No forbidden official files were modified by this repair.

## Warnings
- NONE
