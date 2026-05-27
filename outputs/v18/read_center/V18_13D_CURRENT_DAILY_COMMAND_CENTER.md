# V18.13D Daily Command Center

## Status

- STATUS: OK_V18_13D_READ_CENTER_REFRESH_READY
- RUN_MODE: READ_CENTER_REFRESH_ONLY
- OFFICIAL_DAILY_STATUS: SKIPPED
- V18_13A_STATUS: OK_V18_13A_UNIFIED_DAILY_READ_CENTER_READY
- V18_13B_STATUS: OK_V18_13B_RANKED_CANDIDATE_READ_CENTER_READY
- V18_13C_STATUS: OK_V18_13C_UNIFIED_DAILY_WITH_RANKED_CANDIDATES_READY
- RANK_SOURCE_STATUS: OK_SCORE_SOURCE_FOUND
- SECOND_STAGE_COUNT: 20
- SCORED_TICKER_COUNT: 20
- UNSCORED_TICKER_COUNT: 0
- TOP_5_TICKERS: APH,ACM,CAMT,ASML,CEG
- TODAY_MAIN_READ: outputs/v18/read_center/V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES.md
- TODAY_RANKED_CANDIDATES_CSV: outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- READ_ONLY: TRUE
- COMMAND_CENTER_ONLY: TRUE

## Run Log
| timestamp | step | status | exit_code | script | note |
| --- | --- | --- | --- | --- | --- |
| 2026-05-27 14:29:52 | OFFICIAL_DAILY | SKIPPED | 0 | scripts\v18\run_v18_current_official_daily.ps1 | SKIP_OFFICIAL_DAILY |
| 2026-05-27 14:29:53 | V18_13A | PASS | 0 | D:\us-tech-quant\scripts\v18\run_v18_13A_unified_daily_read_center_link.ps1 | OK |
| 2026-05-27 14:29:53 | V18_13B | PASS | 0 | D:\us-tech-quant\scripts\v18\run_v18_13B_ranked_candidate_read_center.ps1 | OK |
| 2026-05-27 14:29:54 | V18_13C | PASS | 0 | D:\us-tech-quant\scripts\v18\run_v18_13C_ranked_candidate_unified_link.ps1 | OK |

## Top Ranked Candidates
| rank | ticker | composite_candidate_score | final_action | technical_status | latest_price_date | latest_close |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | APH | 29.788571 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_WATCH_POSITIVE | 2026-05-18 | 121.72 |
| 2 | ACM | 26.558730 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_WATCH_POSITIVE | 2026-05-18 | 71.49 |
| 3 | CAMT | 23.385270 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_WATCH_POSITIVE | 2026-05-18 | 155.74 |
| 4 | ASML | 23.381905 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-18 | 1472.39 |
| 5 | CEG | 20.464444 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_WATCH_POSITIVE | 2026-05-18 | 262.0 |
| 6 | AMAT | 17.866286 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-18 | 413.57 |
| 7 | AMKR | 13.462921 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-18 | 66.04 |
| 8 | ANET | 9.155175 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_WATCH_POSITIVE | 2026-05-18 | 141.71 |
| 9 | AMZN | 6.746984 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-18 | 264.86 |
| 10 | CARR | 6.112825 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-18 | 64.51 |

## Read Paths
- Main read: outputs/v18/read_center/V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES.md
- Ranked candidates CSV: outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv

## Limitations
- The command center orchestrates local daily read-center refresh steps only.
- Ranked candidates are research priority only and are not official trade actions.
- Official decision logic is owned by the existing official daily chain and is not changed here.
