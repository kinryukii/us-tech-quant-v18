# V18.18E Technical Timing Backtest Current Alias Externalization Audit

## Summary

- STATUS: OK_V18_18E_TECHNICAL_TIMING_ALIAS_EXTERNALIZATION_AUDIT_READY
- MODE: DRYRUN
- TOTAL_BACKTEST_DIR_SIZE_MB: 252.881
- TOTAL_BACKTEST_FILE_COUNT: 13
- CURRENT_FILE_COUNT: 11
- CURRENT_FILE_MB: 252.880
- HISTORICAL_FILE_COUNT: 2
- HISTORICAL_FILE_MB: 0.001
- ARCHIVEABLE_AFTER_EXTERNALIZATION_COUNT: 2
- ARCHIVEABLE_AFTER_EXTERNALIZATION_MB: 0.001
- EXTERNALIZATION_NEEDED: TRUE
- APPLY: FALSE
- DELETED_COUNT: 0
- MOVED_COUNT: 0
- COPIED_COUNT: 0
- VALIDATION_FAIL_COUNT: 0
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE

## Current Files Protecting Directory

- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_SIGNAL_FORWARD_SUMMARY.csv: 0.001 MB
- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_DETAIL.csv: 85.358 MB
- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_REPORT.md: 0.006 MB
- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TOPN_BACKTEST_MATRIX.csv: 1.317 MB
- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TOPN_STRATEGY_SUMMARY.csv: 0.001 MB
- outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_SIGNAL_EXCESS_SUMMARY.csv: 0.003 MB
- outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv: 166.158 MB
- outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_REPORT.md: 0.014 MB
- outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_TOPN_EXCESS_STRATEGY_SUMMARY.csv: 0.001 MB
- outputs/v18/technical_timing_backtest/V18_CURRENT_TECHNICAL_TIMING_BACKTEST.md: 0.006 MB
- outputs/v18/technical_timing_backtest/V18_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC.md: 0.014 MB

## Archiveable After Externalization

- outputs/v18/technical_timing_backtest/V18_6B_R1_READ_FIRST.txt: 0.001 MB, class=LATEST_READ_FIRST_OR_RUN_SUMMARY
- outputs/v18/technical_timing_backtest/V18_6B_READ_FIRST.txt: 0.000 MB, class=LATEST_READ_FIRST_OR_RUN_SUMMARY

## Proposed Externalization Target

- outputs/v18/technical_timing_backtest_current/

## Notes

- DRYRUN only; no files were copied, moved, archived, or deleted.
- The externalization plan mirrors CURRENT aliases to a dedicated current folder before any later archive cleanup.

## Guardrails

AUTO_TRADE: DISABLED; AUTO_SELL: DISABLED; OFFICIAL_DECISION_IMPACT: NONE.
