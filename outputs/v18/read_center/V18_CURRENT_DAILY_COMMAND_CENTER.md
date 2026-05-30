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
- TOP_5_TICKERS: ACM,CARR,AMZN,AVGO,APH
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
| 2026-05-30 22:13:46 | OFFICIAL_DAILY | SKIPPED | 0 | scripts\v18\run_v18_current_official_daily.ps1 | SKIP_OFFICIAL_DAILY |
| 2026-05-30 22:13:46 | V18_13A | PASS | 0 | D:\us-tech-quant\scripts\v18\run_v18_13A_unified_daily_read_center_link.ps1 | OK |
| 2026-05-30 22:13:47 | V18_13B | PASS | 0 | D:\us-tech-quant\scripts\v18\run_v18_13B_ranked_candidate_read_center.ps1 | OK |
| 2026-05-30 22:13:47 | V18_13C | PASS | 0 | D:\us-tech-quant\scripts\v18\run_v18_13C_ranked_candidate_unified_link.ps1 | OK |

## Top Ranked Candidates
| rank | ticker | composite_candidate_score | final_action | technical_status | latest_price_date | latest_close |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ACM | 37.544190 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_WATCH_POSITIVE | 2026-05-27 | 72.46 |
| 2 | CARR | 35.810984 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 65.595 |
| 3 | AMZN | 33.336889 | WAIT_PULLBACK_REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 267.69 |
| 4 | AVGO | 27.380000 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 423.67 |
| 5 | APH | 19.698222 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 138.95 |
| 6 | CAMT | 18.111111 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 169.075 |
| 7 | ANET | 15.761333 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 154.615 |
| 8 | CEG | 15.570286 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 292.995 |
| 9 | ASML | 15.315556 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 1600.0 |
| 10 | AMKR | 10.417397 | REVIEW_ONLY | TECH_TIMING_NEUTRAL | 2026-05-27 | 71.28 |

## Read Paths
- Main read: outputs/v18/read_center/V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES.md
- Ranked candidates CSV: outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv

## Limitations
- The command center orchestrates local daily read-center refresh steps only.
- Ranked candidates are research priority only and are not official trade actions.
- Official decision logic is owned by the existing official daily chain and is not changed here.
