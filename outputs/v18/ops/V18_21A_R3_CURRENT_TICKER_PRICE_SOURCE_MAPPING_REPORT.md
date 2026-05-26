# V18.21A-R3 Ticker Price Source Mapping Report

## Executive summary
- Status: WARN_V18_21A_R3_TICKER_PRICE_SOURCE_MAPPING_RECONCILIATION_DEGRADED
- Local price data available: 105 / 325
- No candidate source found: 220

## Safety statement
- Advisory-only. No history backfill, external fetch, price cache writes, state writes, ranking changes, broker execution, auto-trade, or auto-sell changes were made.

## Current universe source summary
- Current universe source is the V18 current rolling universe state.

## Source-to-ticker mapping summary
- Full history mapped: 104; partial: 0; latest-only: 1.

## Why discovered source count differs from ticker-level availability
- Source discovery counts files, including duplicate cache locations, historical copies, summary files, and sources for symbols outside the current universe. Ticker availability requires a usable per-ticker source selected for a current universe ticker.

## No-local-data detail summary
- No local price data count: 220. See R3 no-local detail CSV.

## Mapping failure categories
- Candidate sources rejected: 0; no candidate source found: 220.

## Market regime proxy status
- QQQ: OK; SPY: OK; VIX: MISSING_LOCAL_PRICE_HISTORY; coefficient: 0.95.

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check V18.21A-R2: OK_COMPILE
- Python compile check V18.21A-R3: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- R3 output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- HISTORY_BACKFILL_APPLIED: FALSE
- EXTERNAL_DATA_FETCHED: FALSE
- Validation fail count: 0

## Recommended next step
- Missing tickers mostly need an advisory full-history backfill plan. Do not apply backfill in this module.
