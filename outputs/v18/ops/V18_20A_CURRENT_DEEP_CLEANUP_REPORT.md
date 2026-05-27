# V18.20A Deep Legacy Cleanup Audit

- Mode: DRYRUN
- Total scanned files: 2485
- Total repository size MB: 577.02
- Protected file count: 251
- Delete candidate count: 76
- Archive-before-delete candidate count: 174
- Review-required count: 1984
- Dangerous token candidate count: 1021
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- DELETED_COUNT: 0
- MOVED_COUNT: 0
- ARCHIVED_COUNT: 0
- CURRENT_DAILY_MODIFIED: FALSE
- STABLE_SNAPSHOT_MODIFIED: FALSE
- MANUAL_STATE_MODIFIED: FALSE
- PRICE_CACHE_MODIFIED: FALSE
- VALIDATION_FAIL_COUNT: 0

## Category Summary

| cleanup_action | count | size_mb |
| --- | ---: | ---: |
| PROTECT | 251 | 481.63 |
| DELETE_CANDIDATE_DRYRUN | 76 | 1.15 |
| ARCHIVE_BEFORE_DELETE_DRYRUN | 174 | 0.77 |
| REVIEW_REQUIRED | 1984 | 93.47 |

## Top 20 Largest Candidates

| path | size_mb | action | reason |
| --- | ---: | --- | --- |
| outputs/v18/ops/V18_18A_CURRENT_STORAGE_AUDIT.csv | 3.0940 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/ops/V18_CURRENT_STORAGE_AUDIT.csv | 3.0940 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/ops/V18_CLEANUP_DELETE_PLAN_CURRENT.csv | 2.5786 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/ops/V18_CLEANUP_QUARANTINE_PLAN_CURRENT.csv | 2.5527 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_BACKTEST_HOLDINGS.csv | 2.4040 | REVIEW_REQUIRED | Unclear cleanup status; keep for manual review. |
| outputs/v18/ops/V18_CLEANUP_AUDIT_CURRENT.csv | 1.4934 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/ops/V18_18A_CURRENT_KEEP_PROTECTED_FILES.csv | 1.4532 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TOPN_BACKTEST_MATRIX.csv | 1.3173 | REVIEW_REQUIRED | Unclear cleanup status; keep for manual review. |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v18/factor_validation/V18_2A_FACTOR_VALIDATION_DETAIL.csv | 0.6057 | REVIEW_REQUIRED | Unclear cleanup status; keep for manual review. |
| outputs/v18/factor_validation/V18_2A_FACTOR_VALIDATION_DETAIL.csv | 0.6057 | DELETE_CANDIDATE_DRYRUN | Superseded generated output with versioned name. |
| outputs/v18/ops/V18_5A_R1_CURRENT_RUNTIME_DECOUPLING_PLAN.csv | 0.5053 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| outputs/v18/ops/V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv | 0.3906 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| state/v17_factor_effectiveness_tracking.csv | 0.3882 | REVIEW_REQUIRED | Candidate contains risky operational tokens. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/NVDA.csv | 0.2553 | REVIEW_REQUIRED | Name suggests operational or stateful content. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/TSLA.csv | 0.2537 | REVIEW_REQUIRED | Name suggests operational or stateful content. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AAPL.csv | 0.2535 | REVIEW_REQUIRED | Name suggests operational or stateful content. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/GOOGL.csv | 0.2535 | REVIEW_REQUIRED | Name suggests operational or stateful content. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AMZN.csv | 0.2534 | REVIEW_REQUIRED | Name suggests operational or stateful content. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/SOXL.csv | 0.2534 | REVIEW_REQUIRED | Name suggests operational or stateful content. |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AVGO.csv | 0.2532 | REVIEW_REQUIRED | Name suggests operational or stateful content. |

## Validation

- MODE_DRYRUN: PASS
- DELETED_COUNT_ZERO: PASS
- MOVED_COUNT_ZERO: PASS
- ARCHIVED_COUNT_ZERO: PASS
- CURRENT_DAILY_MODIFIED_FALSE: PASS
- STABLE_SNAPSHOT_MODIFIED_FALSE: PASS
- MANUAL_STATE_MODIFIED_FALSE: PASS
- PRICE_CACHE_MODIFIED_FALSE: PASS
- AUTO_TRADE_DISABLED: PASS
- AUTO_SELL_DISABLED: PASS
- OFFICIAL_DECISION_NONE: PASS
- READ_FIRST_EXISTS: PASS
- AUDIT_EXISTS: PASS
- CANDIDATES_EXISTS: PASS
- PROTECTED_EXISTS: PASS
- REPORT_EXISTS: PASS
- DEPENDENCY_EXISTS: PASS

- READ_FIRST: outputs\v18\ops\V18_20A_READ_FIRST.txt
- REPORT: outputs\v18\ops\V18_20A_CURRENT_DEEP_CLEANUP_REPORT.md
- AUDIT: outputs\v18\ops\V18_20A_CURRENT_DEEP_CLEANUP_AUDIT.csv
- CANDIDATES: outputs\v18\ops\V18_20A_CURRENT_DEEP_CLEANUP_CANDIDATES.csv
- PROTECTED: outputs\v18\ops\V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv
- DEPENDENCY_REFERENCE_AUDIT: outputs\v18\ops\V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv
