# V18.45A Operator Refresh Mode And Freshness Gate Patch

## Status
- STATUS: WARN_V18_45A_OPERATOR_REFRESH_MODE_AND_FRESHNESS_GATE_PATCH_APPLIED
- PATCH_DATE: 2026-05-27
- RANKING_LOGIC_CHANGED: FALSE
- FACTOR_WEIGHTS_CHANGED: FALSE
- CANDIDATE_SCORING_CHANGED: FALSE
- TRADING_EXECUTION_ENABLED: FALSE

## Modified Files
- scripts/v18/v18_40D_residual_action_warning_resolver.py
- scripts/v18/v18_41A_daily_clean_operator_pipeline_summary.py
- scripts/v18/v18_44A_daily_operator_homepage_consolidation.py
- scripts/v18/v18_45A_current_ranked_candidate_freshness_audit.py
- scripts/v18/run_v18_45A_current_ranked_candidate_freshness_audit.ps1
- scripts/v18/run_v18_current_daily_command_center.ps1
- scripts/v18/run_v18_41A_daily_clean_operator_pipeline.ps1
- scripts/v18/run_v18_daily_rolling_refresh.ps1
- scripts/v18/run_v18_daily_full_refresh.ps1

## New Outputs
- outputs/v18/ops/V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_AUDIT.csv
- outputs/v18/read_center/V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_AUDIT.md
- outputs/v18/ops/V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt

## Validation Commands
- `.venv\Scripts\python.exe -m py_compile scripts\v18\v18_40D_residual_action_warning_resolver.py scripts\v18\v18_41A_daily_clean_operator_pipeline_summary.py scripts\v18\v18_44A_daily_operator_homepage_consolidation.py scripts\v18\v18_45A_current_ranked_candidate_freshness_audit.py`
- PowerShell parser validation passed for modified ps1 wrappers.
- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_40D_residual_action_warning_resolver.ps1" -Root "D:\us-tech-quant" -ApplyResidualActionWarningResolver`
- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" -RefreshMode Rolling`
- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" -RefreshMode Full`

## Operator Commands
- Rolling refresh: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" -RefreshMode Rolling`
- Full refresh: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" -RefreshMode Full`
- Convenience rolling wrapper: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_daily_rolling_refresh.ps1"`
- Convenience full wrapper: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_daily_full_refresh.ps1"`

## Validation Results
- V18.40D classified `V18_19A_READ_FIRST.txt / WARN_V18_19A_DAILY_READABILITY_READY` as `READABILITY_TRUST_WARNING_NONBLOCKING`.
- UNKNOWN_REVIEW_REQUIRED_COUNT: 0
- EXPECTED_REMAINING_ACTION_REQUIRED_COUNT: 0
- READABILITY_TRUST_WARNING_NONBLOCKING_COUNT: 1
- DAILY_RUN_USABLE: TRUE
- BUY_CANDIDATE_REPORT_USABLE: TRUE
- TRADING_EXECUTION_ALLOWED: FALSE
- V18.41A status after refresh: WARN_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_REVIEW_NEEDED, not FAIL.
- Homepage current aliases written with `CURRENT_HOMEPAGE_WRITE_SKIPPED_REASON: NONE`.

## Latest Freshness Audit
- REFRESH_MODE: Full
- RANKED_CANDIDATE_COUNT: 318
- LATEST_PRICE_DATE_DISTRIBUTION: 2026-05-20=103; 2026-05-21=93; 2026-05-22=17; 2026-05-26=105
- FULL_RANKING_RECOMPUTE_COMPLETE: TRUE
- FULL_PRICE_REFRESH_COMPLETE: FALSE
- STALE_TOPN_COUNT: 4
- STALE_TOPN_TICKERS: VIAV, SITM, TSEM, HUT
- BUY_CANDIDATE_REPORT_TRUST: MEDIUM
- BUY_CANDIDATE_REPORT_USABLE: TRUE

## Operator Rule
If TopN contains stale price rows, do not use those stale rows for buy timing.

## Safety Confirmation
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- TRADING_EXECUTION_ALLOWED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE
- RANKING_LOGIC_CHANGED: FALSE
- FACTOR_WEIGHTS_CHANGED: FALSE
- REAL_TRADING_INTEGRATION_CHANGED: FALSE
