# V18.23B-R2 Watchdog Force Eligibility Audit

Generated: 2026-05-21T14:33:00

## Status
Status: **WARN_V18_23B_R2_WATCHDOG_FORCE_ELIGIBILITY_READY**

Mode: **LOCAL_ONLY_WATCHDOG_FORCE_ELIGIBILITY_GRACE_WINDOW**

## Policy Fix
Never-success tickers are not force-eligible during the bootstrap grace window. Force sweep remains available after the coverage window matures or when concrete dated overdue evidence exists.

## Metrics
| Metric | Value |
| --- | --- |
| completed_rolling_scan_run_count | 2 |
| coverage_window_matured | FALSE |
| bootstrap_grace_active | TRUE |
| force_stale_sweep_mode | FALSE |
| force_sweep_reason | BOOTSTRAP_GRACE_ACTIVE_NO_CONCRETE_OVERDUE_FORCE_NORMAL_BUDGET |
| selected_scan_count | 65 |
| success_scan_count | 0 |
| skipped_scan_count | 65 |
| true_5day_unique_coverage_met | FALSE |

The date/window logic is a calendar/run-count approximation, not exchange-calendar certified.
