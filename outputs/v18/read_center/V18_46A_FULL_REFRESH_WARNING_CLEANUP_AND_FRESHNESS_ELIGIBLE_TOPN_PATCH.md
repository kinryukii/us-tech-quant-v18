# V18.46A Full Refresh Warning Cleanup And Freshness-Eligible TopN Patch

## Summary

V18.46A makes the full refresh operator view use the current authoritative chain:

- V18.35D full universe recompute
- V18.40A top/full canonical sync
- V18.45A ranked candidate freshness audit
- V18.44A operator homepage consolidation

Legacy read-center-only validation and legacy homepage/freshness files are still preserved, but they no longer govern current trust when the authoritative chain is ready.

## Modified Files

- `scripts/v18/run_v18_current_daily_command_center.ps1`
- `scripts/v18/v18_35D_full_universe_factor_technical_recompute.py`
- `scripts/v18/v18_45A_current_ranked_candidate_freshness_audit.py`
- `scripts/v18/v18_44A_daily_operator_homepage_consolidation.py`
- `scripts/v18/v18_19A_daily_readability_refactor.py`
- `outputs/v18/ops/V18_46A_READ_FIRST.txt`
- `outputs/v18/read_center/V18_46A_FULL_REFRESH_WARNING_CLEANUP_AND_FRESHNESS_ELIGIBLE_TOPN_PATCH.md`

## Behavior

- Legacy V18.14A `READ_CENTER_REFRESH_ONLY` plus `OFFICIAL_DAILY_STATUS_SKIPPED` is reclassified as `LEGACY_READ_CENTER_VALIDATION_NONBLOCKING` for full refresh mode.
- Full refresh no longer runs legacy V18.33A/V18.34B by default; opt-in flags are available for backward compatibility.
- V18.44A marks old homepage count mismatch as legacy-only:
  - `OLD_HOMEPAGE_CANDIDATE_COUNT_MISMATCH_LEGACY_ONLY: TRUE`
  - `OLD_HOMEPAGE_CANDIDATE_COUNT_CURRENT_BLOCKING: FALSE`
- V18.35D only reads structured ticker/symbol columns and audits rejected source tokens separately.
- `state/v18/excluded_or_unavailable_tickers.csv` quarantines unavailable Yahoo symbols as `UNAVAILABLE_PRICE_DATA`.
- V18.45A rewrites `V18_CURRENT_TOP_RANKED_CANDIDATES.csv` as the top 20 freshness-eligible rows and preserves `original_full_rank`.
- Stale raw TopN exclusions are audited at `outputs/v18/candidates/V18_46A_STALE_TOPN_EXCLUDED_AUDIT.csv`.

## Validation Results

- Python compile: PASS
  - `python -m py_compile scripts/v18/v18_35D_full_universe_factor_technical_recompute.py`
  - `python -m py_compile scripts/v18/v18_45A_current_ranked_candidate_freshness_audit.py`
  - `python -m py_compile scripts/v18/v18_44A_daily_operator_homepage_consolidation.py`
  - `python -m py_compile scripts/v18/v18_19A_daily_readability_refactor.py`
- PowerShell parse: PASS
  - `PARSE_OK_CURRENT_COMMAND_CENTER`
  - `PARSE_OK_FULL_REFRESH`
- Full refresh command: PASS
  - `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_daily_full_refresh.ps1"`

## Current Results

- `INVALID_PSEUDO_TICKER_COUNT: 0`
- `UNIVERSE_SOURCE_REJECTED_TOKEN_COUNT: 12`
- Rejected source tokens: `0, 105, 11, 20, 250, 252, 303, 318, 325, TICKER, TICKERS, TRUE`
- `PRICE_UNAVAILABLE_EXCLUDED_COUNT: 5`
- Price-unavailable excluded tickers: `CDTX, CFLT, COG, JFROG, MPW`
- `CURRENT_PRICE_REFRESH_BLOCKING_FAILED_TICKER_COUNT: 0`
- `FULL_RANKING_RECOMPUTE_COMPLETE: TRUE`
- `FULL_PRICE_REFRESH_COMPLETE: TRUE`
- `FRESH_TOPN_COUNT: 20`
- `STALE_TOPN_COUNT: 0`
- Stale raw TopN exclusions audited: `VIAV, SITM, TSEM, HUT`
- `TOPN_CURRENT_READY: TRUE`
- `BUY_CANDIDATE_REPORT_TRUST: MEDIUM`
- `DAILY_TRUST_LEVEL: MEDIUM`
- `VALIDATION_FAIL_COUNT: 0`

## Safety Confirmation

- `OFFICIAL_DECISION_IMPACT: NONE`
- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `BROKER_API_USED: FALSE`
- `ORDER_EXECUTION_USED: FALSE`
- `TRADING_EXECUTION_ALLOWED: FALSE`
- `RANKING_LOGIC_CHANGED: FALSE`
- `FACTOR_WEIGHTS_CHANGED: FALSE`
