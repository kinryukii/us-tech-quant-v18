# V18.17A Ranking Factor Provenance Audit

## Executive Summary

- STATUS: OK_V18_17A_RANKING_FACTOR_PROVENANCE_AUDIT_READY
- MODE: READ_ONLY_RANKING_PROVENANCE_AUDIT
- RANK_SOURCE_STATUS: FOUND
- RANKED_CANDIDATE_COUNT: 20
- SCORED_TICKER_COUNT: 20
- UNSCORED_TICKER_COUNT: 0
- TOP_5_TICKERS: APH,ACM,CAMT,ASML,CEG
- RANKING_APPEARS_SCORE_BASED: TRUE
- RANKING_APPEARS_FILE_ORDER_ONLY: FALSE
- FACTOR_FAMILY_VERIFIED_USED_COUNT: 7
- FACTOR_FAMILY_PRESENT_NOT_VERIFIED_COUNT: 6
- FACTOR_FAMILY_NOT_FOUND_COUNT: 3
- CANDIDATE_FULLY_EXPLAINED_COUNT: 20
- CANDIDATE_PARTIALLY_EXPLAINED_COUNT: 0
- CANDIDATE_NOT_EXPLAINABLE_COUNT: 0
- SOURCE_FILE_SCANNED_COUNT: 133
- OPTIONAL_SOURCE_MISSING_COUNT: 0
- PRICE_UPDATE_EXECUTED: FALSE
- EVENT_UPDATE_EXECUTED: FALSE
- FULL_DAILY_EXECUTED: FALSE
- YFINANCE_USED: FALSE
- ROLLING_SCAN_EXECUTED: FALSE
- CURRENT_DAILY_MODIFIED: FALSE
- STABLE_SNAPSHOT_MODIFIED: FALSE
- DANGEROUS_TOKEN_FINDING_COUNT: 0
- VALIDATION_FAIL_COUNT: 0
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE

## Current Top 20 Ranked Candidates

APH,ACM,CAMT,ASML,CEG,AMAT,AMKR,ANET,AMZN,CARR,AVGO,ACMR,AAPL,ACLS,BE,AEHR,AMD,BTDR,ALAB,ARM

## Current Top 5 Explanation

- APH: Rank 1 uses score composite_candidate_score=29.788571; source columns=factor_pack_rank;factor_pack_score;overheat_penalty;technical_timing_score;volatility_penalty; rolling scan cross-check tier=CORE_DAILY, trend=WEAK_DOWNTREND.
- ACM: Rank 2 uses score composite_candidate_score=26.558730; source columns=factor_pack_rank;factor_pack_score;overheat_penalty;technical_timing_score;volatility_penalty; rolling scan cross-check tier=CORE_DAILY, trend=WEAK_DOWNTREND.
- CAMT: Rank 3 uses score composite_candidate_score=23.385270; source columns=factor_pack_rank;factor_pack_score;overheat_penalty;technical_timing_score;volatility_penalty; rolling scan cross-check tier=CORE_DAILY, trend=WEAK_DOWNTREND.
- ASML: Rank 4 uses score composite_candidate_score=23.381905; source columns=factor_pack_rank;factor_pack_score;overheat_penalty;technical_timing_score;volatility_penalty; rolling scan cross-check tier=CORE_DAILY, trend=STRONG_UPTREND.
- CEG: Rank 5 uses score composite_candidate_score=20.464444; source columns=factor_pack_rank;factor_pack_score;overheat_penalty;technical_timing_score;volatility_penalty; rolling scan cross-check tier=CORE_DAILY, trend=WEAK_DOWNTREND.

## Verified Factor Families

PULLBACK, TECHNICAL_LIFECYCLE, RISK, OVERHEAT, VOLATILITY, EXECUTION, UNKNOWN_SCORE_FIELD

## Not Verified Factor Families

TREND, MOMENTUM, RELATIVE_STRENGTH, QUALITY, GROWTH, VALUATION, EARNINGS, EVENT_RISK, LIQUIDITY

## Ranking Source Status

Current ranked candidate file: outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv. Ranking appears score-based: TRUE.
Current fast mode appears to read previously computed local score fields from factor pack and technical timing sources; this audit does not recompute formulas.

## V18.17B Gaps

- Persist explicit per-factor contribution columns in ranked candidates.
- Add a machine-readable formula manifest for composite_candidate_score.
- Link every score_source_column to exact source file and row-level value.

## Safety Guardrails

AUTO_TRADE: DISABLED; AUTO_SELL: DISABLED; OFFICIAL_DECISION_IMPACT: NONE.
