# V18.30B Daily Command Compatibility Guard

## Read First
```text
STATUS: WARN_V18_30B_DAILY_COMMAND_COMPATIBILITY_GUARD_REVIEW_NEEDED
MODE: DAILY_COMMAND_COMPATIBILITY_GUARD
RUN_ID: V18_30B_20260524_182840
CURRENT_RANKED_CANDIDATE_ROW_COUNT: 252
CURRENT_THEME_CLASSIFICATION_ROW_COUNT: 252
CURRENT_RECOMMENDATION_ROW_COUNT: 252
CURRENT_RANKED_RDDT_COUNT: 1
CURRENT_RANKED_TLN_COUNT: 1
LATEST_RECOMMENDATION_SNAPSHOT_DATE: 
LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT: 0
LATEST_SIGNAL_FREEZE_RUN_ID: V18_25A_R21_20260522_191703
LATEST_SIGNAL_FREEZE_DATE: 2026-05-22
LATEST_SIGNAL_FREEZE_TICKER_COUNT: 250
LEGACY_DAILY_OVERWRITE_DETECTED: FALSE
CURRENT_RECOMMENDATION_CORRUPTED_BY_LEGACY_CHAIN: FALSE
RECOVERY_CANDIDATE_COUNT: 0
BEST_RECOVERY_SOURCE_TYPE: 
BEST_RECOVERY_CANDIDATE_PATH_OR_GROUP: 
APPLY_RESTORE: FALSE
RESTORE_APPLIED: FALSE
R28A_RERUN: FALSE
R28B_RERUN: FALSE
R29C_RERUN_BLOCKED_TO_AVOID_DUPLICATE_SNAPSHOT: FALSE
CORRECT_R21_WRAPPER_FOUND: TRUE
CORRECT_R21_WRAPPER_PATH: scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1
SAFE_DAILY_COMMAND_RECOMMENDATION: Use scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1; do not run scripts/v18/run_v18_current_daily_command_center.ps1 before V18.28+ compatibility is fixed.
OFFICIAL_DECISION_IMPACT: NONE
AUTO_TRADE: DISABLED
AUTO_SELL: DISABLED
FORBIDDEN_MODIFIED: FALSE
```

## Compatibility Warning
Do not run `scripts/v18/run_v18_current_daily_command_center.ps1` before the V18.28+ layer until compatibility is fixed. Use the R21 wrapper recorded below for the 252-row flow.

## Recovery Candidate List
_None._

## Anchor Checks
| category | item | status | value | details |
| --- | --- | --- | --- | --- |
| check | current_ranked_candidate_row_count | PASS | 252 | expected 252 |
| check | current_theme_classification_row_count | PASS | 252 | expected 252 |
| check | current_recommendation_row_count | PASS | 252 | expected 252 |
| check | rddt_present | PASS | 1 | RDDT should be present once in ranked candidates |
| check | tln_present | PASS | 1 | TLN should be present once in ranked candidates |
| check | latest_snapshot_row_count | WARN | 0 |  |
| check | latest_signal_freeze_ticker_count | WARN | 250 | V18_25A_R21_20260522_191703 |
| check | duplicate_signal_date_ticker_count_in_freeze_ledger | PASS | 0 | Run V18.30D cleanup if nonzero |
| check | legacy_daily_overwrite_detected | PASS | FALSE | 20-row current files with 252-row snapshot available |
| check | correct_r21_wrapper_found | PASS | TRUE | scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1 |

## Safe Daily Command Recommendation
`Use scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1; do not run scripts/v18/run_v18_current_daily_command_center.ps1 before V18.28+ compatibility is fixed.`
