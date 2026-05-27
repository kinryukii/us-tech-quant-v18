# V18.11F Shadow Factor Research Chain

- STATUS: $Status
- MODE: $Mode
- TOTAL_SECONDS: $TotalSeconds
- FAIL_COUNT: $FailCount
- OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact
- AUTO_WEIGHT_CHANGE: $AutoWeightChange
- AUTO_PROMOTION: $AutoPromotion
- AUTO_TRADE: $AutoTrade
- OFFICIAL_TRADING_IMPACT: $OfficialTradingImpact
- STATE_REGISTRY_MODIFIED: $StateRegistryModified
- CANDIDATE_TRACKER_STATE_MODIFIED: $CandidateTrackerStateModified
- FACTOR_WEIGHTS_MODIFIED: $FactorWeightsModified
- V18_11D_STATUS: $Status11D
- V18_11E_STATUS: $Status11E
- FACTOR_COUNT: $FactorCount
- COMPUTABLE_COUNT: $ComputableCount
- PROXY_ONLY_COUNT: $ProxyOnlyCount
- DATA_UNAVAILABLE_COUNT: $DataUnavailableCount
- CANDIDATE_ROW_COUNT: $CandidateRowCount
- UNIQUE_TICKER_COUNT: $UniqueTickerCount
- UNIQUE_TICKER_BASE_DATE_COUNT: $UniqueTickerBaseDateCount
- YFINANCE_STATUS: $YFinanceStatus

## Research Highlights

- TOP_HIGH_RV_TICKERS: $TopHighRvTickers
- TOP_POSITIVE_VWAP_PROXY_DEVIATION_TICKERS: $TopPositiveVwapTickers
- TOP_NEGATIVE_VWAP_PROXY_DEVIATION_TICKERS: $TopNegativeVwapTickers
- VWAP_RECLAIM_CANDIDATES: $VwapReclaimCandidates

## OPEX Warning Summary

- OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT: $OpexRaw
- OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT: $OpexUnique
- MONTH_END_ACTIVE_COUNT: $MonthEndActive
- QUARTER_END_ACTIVE_COUNT: $QuarterEndActive
- POST_OPEX_RELIEF_ACTIVE_COUNT: $PostOpexReliefActive
- OPEX_METHOD: CALENDAR_PROXY_ONLY; No options chain / OI / IV used
- VWAP_METHOD: PROXY_ONLY_DAILY_OHLCV; Not true intraday VWAP

## Outputs

- V18.11D_READ_FIRST: $Read11D
- V18.11E_READ_FIRST: $Read11E
- STEPS_CSV: $StepsCsv

## Safety

This wrapper runs only V18.11D and V18.11E. It does not run official daily, current shadow research daily, V18.10D, or cleanup delete tools.
