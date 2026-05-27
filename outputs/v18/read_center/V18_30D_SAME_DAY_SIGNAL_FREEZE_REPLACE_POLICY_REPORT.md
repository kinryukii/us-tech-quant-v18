# V18.30D Same-Day Signal Freeze Replace Policy

## Read First
```text
STATUS: OK_V18_30D_SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY_READY
MODE: SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY
RUN_ID: V18_30D_20260523_172209
FREEZE_LEDGER_PATH: D:\us-tech-quant\state\v18\forward_test\V18_DAILY_SIGNAL_FREEZE_LEDGER.csv
PRE_LEDGER_ROWS: 1374
SIGNAL_DATE_COUNT: 2
DUPLICATE_SIGNAL_DATE_TICKER_COUNT_BEFORE: 502
DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER: 0
R21_PATCH_APPLIED: TRUE
R21_WRAPPER_PATCH_APPLIED: TRUE
R30A_PATCH_APPLIED: TRUE
R30B_PATCH_APPLIED: TRUE
APPLY_CLEANUP: TRUE
CLEANUP_APPLIED: TRUE
BACKUP_PATH: D:\us-tech-quant\archive\v18\signal_freeze_same_day_replace_backups\V18_30D_20260523_172209\V18_DAILY_SIGNAL_FREEZE_LEDGER_PRE_CLEANUP.csv
LATEST_SIGNAL_DATE: 2026-05-23
LATEST_SIGNAL_DATE_ROW_COUNT: 252
LATEST_SIGNAL_DATE_UNIQUE_TICKER_COUNT: 252
OFFICIAL_DECISION_IMPACT: NONE
AUTO_TRADE: DISABLED
AUTO_SELL: DISABLED
FORBIDDEN_MODIFIED: FALSE
```

## Policy Summary
R21 default mode is same-day replace by signal_date+ticker. Use -AllowSameDayAppend only for intentional intraday archival appends.

## Checks
| category | item | status | value | details |
| --- | --- | --- | --- | --- |
| check | r21_patch_applied | PASS | TRUE | scripts/v18/v18_25A_R21_daily_signal_freeze_forward_test_ledger.py |
| check | r21_wrapper_patch_applied | PASS | TRUE | scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1 |
| check | r30a_patch_applied | PASS | TRUE | scripts/v18/v18_30A_daily_operator_control_center.py |
| check | r30b_patch_applied | PASS | TRUE | scripts/v18/v18_30B_daily_command_compatibility_guard.py |
| ledger | duplicate_signal_date_ticker_before | WARN | 502 | Apply cleanup if nonzero |
| ledger | duplicate_signal_date_ticker_after | PASS | 0 | Post-cleanup duplicate count |
| ledger | latest_signal_date_row_count | PASS | 252 | 2026-05-23 |
| ledger | latest_signal_date_unique_ticker_count | PASS | 252 | 2026-05-23 |

