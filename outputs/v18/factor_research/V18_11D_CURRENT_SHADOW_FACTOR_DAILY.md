# V18.11D Shadow Factor Daily

- STATUS: $Status
- MODE: $Mode
- USE_YFINANCE: $UseYFinance
- OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact
- AUTO_WEIGHT_CHANGE: $AutoWeightChange
- AUTO_PROMOTION: $AutoPromotion
- AUTO_TRADE: $AutoTrade
- STATE_REGISTRY_MODIFIED: $StateRegistryModified
- CANDIDATE_TRACKER_STATE_MODIFIED: $CandidateTrackerStateModified
- FACTOR_COUNT: $FactorCount
- COMPUTABLE_COUNT: $ComputableCount
- PROXY_ONLY_COUNT: $ProxyOnlyCount
- DATA_UNAVAILABLE_COUNT: $DataUnavailableCount
- CANDIDATE_ROW_COUNT: $CandidateRowCount
- YFINANCE_STATUS: $YFinanceStatus
- TOTAL_SECONDS: $TotalSeconds
- FAIL_COUNT: $FailCount

## Outputs

- V18.11A_READ_FIRST: $V11ARead
- V18.11B_READ_FIRST: $V11BRead
- V18.11C_READ_FIRST: $V11CRead
- STEPS_CSV: $StepsCsv

## Safety

This wrapper runs only scripts\v18\run_v18_11_calendar_vwap_rv_shadow_factors.ps1.
It does not run official daily, shadow research daily, V18.10D, or cleanup delete tools.
