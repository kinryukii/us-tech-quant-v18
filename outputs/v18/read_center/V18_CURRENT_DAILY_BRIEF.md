# Qutumn Daily Brief

## 1. Today's Decision
- Today Action: Read-only daily refresh; coverage is acceptable but other warnings remain.
- Trade Permission: DISABLED / DISABLED
- Daily Trust Level: LOW
- Main Reason: Validation failures or missing ranking source were detected. True 5-day unique universe coverage remains unresolved; trust level is capped below HIGH.

## 2. Top Candidates

| Rank | Ticker | Tier | Score | Key Reason | Data Status |
| --- | --- | --- | --- | --- | --- |
| 1 | APH | CORE_DAILY | 29.788571 | Rank 1 uses score composite_candidate_score=29.788571; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 2 | ACM | CORE_DAILY | 26.558730 | Rank 2 uses score composite_candidate_score=26.558730; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 3 | CAMT | CORE_DAILY | 23.385270 | Rank 3 uses score composite_candidate_score=23.385270; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 4 | ASML | CORE_DAILY | 23.381905 | Rank 4 uses score composite_candidate_score=23.381905; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 5 | CEG | CORE_DAILY | 20.464444 | Rank 5 uses score composite_candidate_score=20.464444; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 6 | AMAT | CORE_DAILY | 17.866286 | Rank 6 uses score composite_candidate_score=17.866286; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 7 | AMKR | CANDIDATE | 13.462921 | Rank 7 uses score composite_candidate_score=13.462921; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |
| 8 | ANET | STRONG_WATCH | 9.155175 | Rank 8 uses score composite_candidate_score=9.155175; source columns=factor_pack_rank;factor_pack_score;ove... | FULL_HISTORY_AVAILABLE |
| 9 | AMZN | CANDIDATE | 6.746984 | Rank 9 uses score composite_candidate_score=6.746984; source columns=factor_pack_rank;factor_pack_score;ove... | FULL_HISTORY_AVAILABLE |
| 10 | CARR | CORE_DAILY | 6.112825 | Rank 10 uses score composite_candidate_score=6.112825; source columns=factor_pack_rank;factor_pack_score;ov... | FULL_HISTORY_AVAILABLE |

## 3. Risk Dashboard
- Data Freshness: Current data is cache-backed and safe-mode oriented; yfinance preflight did not present a clean pass.
- Event Risk: Primary event audit was found at outputs/v18/risk/V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv.
- Command Center Source: outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt (OK)
- Current Mode Source: outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt (OK)
- Coverage Risk: Daily threshold coverage target was met from fresh rolling scan evidence.
- Same-Day Promotion Guard: TRUE
- Validation Status: 1
- Auto Trade / Auto Sell Status: DISABLED / DISABLED

## 4. Universe Changes
- Promotions: 0
- Demotions: 128
- Core Daily count: 40
- Candidate count: 150
- Watchlist count: 0
- Research count: 16

## 5. What Changed Today
0 promotion(s), 128 demotion(s), 92 unchanged row(s).

## 6. What To Read Next
- [V18_CURRENT_TOP_RANKED_CANDIDATES.md](daily_packet/V18_CURRENT_TOP_RANKED_CANDIDATES.md)
- [V18_CURRENT_UNIVERSE_CHANGES.md](daily_packet/V18_CURRENT_UNIVERSE_CHANGES.md)
- [V18_CURRENT_RISK_DASHBOARD.md](daily_packet/V18_CURRENT_RISK_DASHBOARD.md)
- [V18_CURRENT_COVERAGE_STATUS.md](daily_packet/V18_CURRENT_COVERAGE_STATUS.md)
- [V18_CURRENT_DATA_FRESHNESS.md](daily_packet/V18_CURRENT_DATA_FRESHNESS.md)

## 7. Machine Status
```text
AUTO_TRADE: DISABLED
AUTO_SELL: DISABLED
OFFICIAL_DECISION_IMPACT: NONE
VALIDATION_FAIL_COUNT: 1
COVERAGE_TARGET_MET: TRUE
DAILY_THRESHOLD_COVERAGE_SOURCE: outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt
DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS: OK_FRESH_DAILY_SCAN_SOURCE
DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME: 2026-05-27T12:59:02
DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON: Valid current-run read-first daily threshold evidence.
DAILY_THRESHOLD_TARGET_MET: TRUE
DAILY_THRESHOLD_SHORTFALL_COUNT: 0
TRUE_5DAY_UNIQUE_COVERAGE_MET: FALSE
TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: 176
TODAY_ROLLING_SCAN_COUNT: 318
DAILY_MIN_SCAN_COUNT: 67
COVERAGE_SHORTFALL_COUNT: 0
SAME_DAY_PROMOTION_GUARD: TRUE
RANK_SOURCE_STATUS: OK_SCORE_SOURCE_FOUND
```
