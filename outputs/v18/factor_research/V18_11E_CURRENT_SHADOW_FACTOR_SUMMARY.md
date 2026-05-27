# V18.11E Shadow Factor Summary

## 1. Status And Safety Guards

- STATUS: `OK_V18_11E_SHADOW_FACTOR_SUMMARY_READY`
- MODE: `SHADOW_ONLY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- AUTO_WEIGHT_CHANGE: `DISABLED`
- AUTO_PROMOTION: `DISABLED`
- AUTO_TRADE: `DISABLED`
- OFFICIAL_TRADING_IMPACT: `NONE`
- CANDIDATE_TRACKER_STATE_MODIFIED: `False`
- FACTOR_WEIGHTS_MODIFIED: `False`

## 2. Candidate Row Count

- RAW_CANDIDATE_ROW_COUNT: `93`

## 3. Unique Ticker Count

- UNIQUE_TICKER_COUNT: `31`

## 4. Unique Ticker + Base Date Count

- UNIQUE_TICKER_BASE_DATE_COUNT: `31`

## 5. Calendar/OPEX Warnings

- OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT: `93`
- OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT: `31`
- MONTH_END_ACTIVE_COUNT: `0`
- QUARTER_END_ACTIVE_COUNT: `0`
- POST_OPEX_RELIEF_ACTIVE_COUNT: `0`
- OPEX_METHOD: `CALENDAR_PROXY_ONLY. No options chain / OI / IV used.`

## 6. Top 10 Realized Volatility

| rank | ticker | base_date | metric | value | status |
|---:|---|---|---|---:|---|
| 1 | FLEX | 2026-05-15 | realized_volatility_factor | 1.450080 | COMPUTABLE_NOW |
| 2 | DDOG | 2026-05-15 | realized_volatility_factor | 1.142391 | COMPUTABLE_NOW |
| 3 | AEHR | 2026-05-15 | realized_volatility_factor | 0.981241 | COMPUTABLE_NOW |
| 4 | CRDO | 2026-05-15 | realized_volatility_factor | 0.934447 | COMPUTABLE_NOW |
| 5 | CRWV | 2026-05-15 | realized_volatility_factor | 0.902017 | COMPUTABLE_NOW |
| 6 | CAMT | 2026-05-15 | realized_volatility_factor | 0.855501 | COMPUTABLE_NOW |
| 7 | FLR | 2026-05-15 | realized_volatility_factor | 0.695077 | COMPUTABLE_NOW |
| 8 | ANET | 2026-05-15 | realized_volatility_factor | 0.672539 | COMPUTABLE_NOW |
| 9 | AMKR | 2026-05-15 | realized_volatility_factor | 0.628585 | COMPUTABLE_NOW |
| 10 | ICHR | 2026-05-15 | realized_volatility_factor | 0.618708 | COMPUTABLE_NOW |

## 7. Top 10 Positive VWAP Proxy Deviation

`PROXY_ONLY_DAILY_OHLCV. Not true intraday VWAP.`

| rank | ticker | base_date | metric | value | status |
|---:|---|---|---|---:|---|
| 1 | DDOG | 2026-05-15 | vwap_deviation_factor | 0.258517 | PROXY_ONLY_DAILY_OHLCV |
| 2 | PANW | 2026-05-15 | vwap_deviation_factor | 0.228775 | PROXY_ONLY_DAILY_OHLCV |
| 3 | CRWD | 2026-05-15 | vwap_deviation_factor | 0.209784 | PROXY_ONLY_DAILY_OHLCV |
| 4 | CSCO | 2026-05-15 | vwap_deviation_factor | 0.201870 | PROXY_ONLY_DAILY_OHLCV |
| 5 | FLEX | 2026-05-15 | vwap_deviation_factor | 0.167888 | PROXY_ONLY_DAILY_OHLCV |
| 6 | ZS | 2026-05-15 | vwap_deviation_factor | 0.121579 | PROXY_ONLY_DAILY_OHLCV |
| 7 | AEHR | 2026-05-15 | vwap_deviation_factor | 0.067651 | PROXY_ONLY_DAILY_OHLCV |
| 8 | AAPL | 2026-05-15 | vwap_deviation_factor | 0.066110 | PROXY_ONLY_DAILY_OHLCV |
| 9 | ICHR | 2026-05-15 | vwap_deviation_factor | 0.065429 | PROXY_ONLY_DAILY_OHLCV |
| 10 | NTAP | 2026-05-15 | vwap_deviation_factor | 0.058400 | PROXY_ONLY_DAILY_OHLCV |

## 8. Top 10 Negative VWAP Proxy Deviation

`PROXY_ONLY_DAILY_OHLCV. Not true intraday VWAP.`

| rank | ticker | base_date | metric | value | status |
|---:|---|---|---|---:|---|
| 1 | CEG | 2026-05-15 | vwap_deviation_factor | -0.101860 | PROXY_ONLY_DAILY_OHLCV |
| 2 | CAMT | 2026-05-15 | vwap_deviation_factor | -0.097523 | PROXY_ONLY_DAILY_OHLCV |
| 3 | ACM | 2026-05-15 | vwap_deviation_factor | -0.096543 | PROXY_ONLY_DAILY_OHLCV |
| 4 | VST | 2026-05-15 | vwap_deviation_factor | -0.093436 | PROXY_ONLY_DAILY_OHLCV |
| 5 | ENTG | 2026-05-15 | vwap_deviation_factor | -0.091451 | PROXY_ONLY_DAILY_OHLCV |
| 6 | APH | 2026-05-15 | vwap_deviation_factor | -0.090046 | PROXY_ONLY_DAILY_OHLCV |
| 7 | CRWV | 2026-05-15 | vwap_deviation_factor | -0.083370 | PROXY_ONLY_DAILY_OHLCV |
| 8 | ANET | 2026-05-15 | vwap_deviation_factor | -0.082146 | PROXY_ONLY_DAILY_OHLCV |
| 9 | FLR | 2026-05-15 | vwap_deviation_factor | -0.075635 | PROXY_ONLY_DAILY_OHLCV |
| 10 | CRDO | 2026-05-15 | vwap_deviation_factor | -0.071044 | PROXY_ONLY_DAILY_OHLCV |

## 9. VWAP Reclaim Support Candidates

`PROXY_ONLY_DAILY_OHLCV. Not true intraday VWAP.`

| rank | ticker | base_date | metric | value | status |
|---:|---|---|---|---:|---|
| 1 | ICHR | 2026-05-15 | vwap_reclaim_support_factor | 1.000000 | PROXY_ONLY_DAILY_OHLCV |

## 10. Duplicate Snapshot/Base Date Warning

- DUPLICATE_WARNING: `DUPLICATES_FOUND`
- DUPLICATE_TICKER_BASE_DATE_COUNT: `62`

## 11. Official Impact Statement

This report is SHADOW_ONLY and has no official trading impact. It does not change official decisions, buy/sell logic, factor weights, or candidate tracker state.
