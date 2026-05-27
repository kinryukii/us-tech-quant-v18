# V18.45B Full Refresh Wrapper And Ticker Sanitizer Patch

## Status
- STATUS: WARN_V18_45B_FULL_REFRESH_WRAPPER_AND_TICKER_SANITIZER_PATCH_APPLIED
- PATCH_DATE: 2026-05-27
- RANKING_LOGIC_CHANGED: FALSE
- FACTOR_WEIGHTS_CHANGED: FALSE
- CANDIDATE_SCORING_CHANGED: FALSE
- TRADING_EXECUTION_ENABLED: FALSE

## Modified Files
- scripts/v18/run_v18_current_daily_command_center.ps1
- scripts/v18/run_v18_daily_full_refresh.ps1
- scripts/v18/run_v18_daily_rolling_refresh.ps1
- scripts/v18/v18_35D_full_universe_factor_technical_recompute.py
- scripts/v18/v18_45A_current_ranked_candidate_freshness_audit.py

## Validation Commands
- `.venv\Scripts\python.exe -m py_compile scripts\v18\v18_35D_full_universe_factor_technical_recompute.py scripts\v18\v18_45A_current_ranked_candidate_freshness_audit.py scripts\v18\v18_40D_residual_action_warning_resolver.py scripts\v18\v18_41A_daily_clean_operator_pipeline_summary.py scripts\v18\v18_44A_daily_operator_homepage_consolidation.py`
- PowerShell parser validation passed for modified refresh wrappers.
- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_daily_full_refresh.ps1"`
- `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_daily_rolling_refresh.ps1"`

## Validation Results
- Full wrapper reported `REFRESH_MODE: Full`.
- Full wrapper reported `REFRESH_MODE_PRESET_APPLIED: TRUE`.
- Rolling wrapper reported `REFRESH_MODE: Rolling`.
- Rolling wrapper reported `REFRESH_MODE_PRESET_APPLIED: TRUE`.
- Full wrapper no longer enters the legacy V18.15B/V18.14E nested command-center path that printed an inner `RefreshMode Rolling`.
- Known legacy official-daily failure is not allowed to abort later safety/read-center/freshness steps when current usability gates are already true.
- V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt updated.
- V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_V2.md updated.

## Ticker Sanitizer Result
- RAW_UNIVERSE_TOKEN_COUNT: 334
- SANITIZED_UNIVERSE_COUNT: 323
- INVALID_PSEUDO_TICKER_COUNT: 11
- INVALID_PSEUDO_TICKERS: 0, 105, 20, 250, 252, 303, 318, 325, TICKER, TICKERS, TRUE
- YFINANCE_FAILED_TICKER_COUNT: 5
- YFINANCE_FAILED_TICKERS: CDTX, CFLT, COG, JFROG, MPW

## Freshness Result
- Latest validated freshness mode: Rolling
- FULL_PRICE_REFRESH_COMPLETE: FALSE
- FULL_PRICE_REFRESH_INCOMPLETE_REASON: STALE_RANKED_CANDIDATES_REMAIN; MIXED_LATEST_PRICE_DATES; INVALID_PSEUDO_TICKERS_REMOVED; YFINANCE_FAILED_TICKERS_PRESENT
- STALE_TOPN_COUNT: 4
- STALE_TOPN_TICKERS: VIAV, SITM, TSEM, HUT
- Stale TopN rows remain non-actionable with `actionable_allowed_by_freshness=FALSE`.

## Safety Confirmation
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- TRADING_EXECUTION_ALLOWED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE
- RANKING_LOGIC_CHANGED: FALSE
- FACTOR_WEIGHTS_CHANGED: FALSE
- SIGNAL_FREEZE_SEMANTICS_CHANGED: FALSE
