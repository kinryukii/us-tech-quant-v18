# V18.47C-R1 Event Source Coverage Repair Report

V18.47C-R1 is a local-only coverage audit and seed repair layer. It does not predict event outcomes and does not change official ranking, factor weights, candidate scoring, Top20 selection, freshness eligibility, trading execution, broker/order behavior, or signal freeze ledgers.

## Sources
| metric | value |
| --- | --- |
| CURRENT_TOP20_SOURCE | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| V18_47B_TRACKER_SOURCE | D:\us-tech-quant\outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv |
| USABLE_EVENT_SOURCE_COUNT | 3 |
| EVENT_SOURCES_WITH_TOP20_MATCHES | 3 |
| UNKNOWN_BEFORE | 19 |
| UNKNOWN_AFTER | 19 |

## Event Source Audit
| source_path | source_exists | row_count | parseable_date_count | current_top20_ticker_match_count | source_usable | source_issue_reason |
| --- | --- | --- | --- | --- | --- | --- |
| D:\us-tech-quant\state\v18\cloud_earnings_event_calendar.csv | TRUE | 5 | 5 | 1 | TRUE | OK |
| D:\us-tech-quant\state\v16\event_calendar.csv | TRUE | 5 | 5 | 1 | TRUE | OK |
| D:\us-tech-quant\data\events\v16_macro_events.csv | TRUE | 2 | 2 | 0 | TRUE | OK |
| D:\us-tech-quant\data\events\v16_earnings_overrides.csv | TRUE | 0 | 0 | 0 | FALSE | NO_ROWS |
| D:\us-tech-quant\state\v18\manual_event_overrides.csv | FALSE | 0 | 0 | 0 | FALSE | SOURCE_MISSING |
| D:\us-tech-quant\state\v18\V18_47C_MANUAL_EVENT_OVERRIDES.csv | FALSE | 0 | 0 | 0 | FALSE | SOURCE_MISSING |
| D:\us-tech-quant\state\v18\V18_47C_TOP20_EVENT_EARNINGS_SEED.csv | TRUE | 20 | 0 | 20 | FALSE | EVENT_SOURCE_DATE_PARSE_FAILED |

## Why UNKNOWN_REVIEW Was High
The available local earnings calendars cover only a small subset of current Top20 tickers. Macro data is market-wide and cannot replace ticker-level earnings coverage. Blank or missing manual seed rows keep tickers in UNKNOWN_REVIEW by design.

## Remaining UNKNOWN_REVIEW Fixes
| ticker | rank | match_status | unknown_reason | recommended_fix |
| --- | --- | --- | --- | --- |
| KEYS | 1 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| VRT | 2 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| ICHR | 3 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| NVDA | 4 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| D | 5 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| AMKR | 6 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| FIX | 8 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| MCHP | 9 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| LITE | 10 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| CARR | 11 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| ENTG | 12 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| CRWV | 13 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| ETR | 14 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| COHU | 15 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| GEV | 16 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| FN | 17 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| ETN | 18 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| HUBB | 19 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |
| POWL | 20 | UNKNOWN_REVIEW_REQUIRED | MANUAL_SEED_BLANK | CHECK_TICKER_ALIAS |

## Manual Seed File
Fill `D:\us-tech-quant\state\v18\V18_47C_TOP20_EVENT_EARNINGS_SEED.csv` with reviewed local earnings/event dates, set `active` to TRUE for reviewed rows, rerun V18.47C-R1, then rerun V18.47C.

## Suggested Next Step
fill manual seed file, rerun V18.47C-R1, then rerun V18.47C.
