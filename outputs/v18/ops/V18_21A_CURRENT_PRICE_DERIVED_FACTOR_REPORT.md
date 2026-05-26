# V18.21A Price-Derived Factor Pack Report

## Executive summary
- Status: WARN_V18_21A_PRICE_DERIVED_FACTOR_PACK_DEGRADED
- Ticker factor rows: 325 / 325
- Market regime: RISK_ON_TREND at coefficient 1.00

## Safety statement
- Advisory-only. No external providers were used and no cache, state, ranking, trading, or command-center files were modified.

## Input discovery summary
- Universe source: outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv
- Price source precedence: data/prices, state/v18/price_cache, data/v16/prices_full, data/v16/prices.

## Ticker-level factor summary
- Insufficient history count: 1
- Data degraded count: 221

## Market regime summary
- QQQ: OK; SPY: OK; VIX: MISSING_LOCAL_PRICE_HISTORY

## Top relative strength tickers
- AEHR;SOXL;INTC;SNDK;MRVL;FLEX;AMD;DELL;VECO;STX

## Top near-buy-zone tickers
- AAPL;ACLS;AEHR;AMAT;AMKR;AMZN;ANET;ARM;ASML;AVGO

## Breakout volume confirmation summary
- 

## Degraded/missing data summary
- Factor fail count: 220; VIX status: MISSING_LOCAL_PRICE_HISTORY

## Validation summary
- PowerShell parse check: OK_PARSE
- Python compile check: OK_COMPILE
- Run check: OK_CURRENT_SCRIPT_EXECUTED
- Output existence check: OK
- Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY
- Validation fail count: 0

## Next-step recommendation
- Review V18.21A as a research input only. Promote nothing into official ranking or trading until a separate policy review is approved.
