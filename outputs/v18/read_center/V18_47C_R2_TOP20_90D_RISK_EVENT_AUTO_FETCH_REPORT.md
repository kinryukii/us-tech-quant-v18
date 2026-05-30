# V18.47C-R2 Top20 90-Day Risk Event Auto Fetch Report

V18.47C-R2 identifies upcoming risk events and writes reference-only risk fields. It does not predict event outcomes, earnings results, macro impact, Fed outcomes, or stock direction.

## Sources and Providers
| metric | value |
| --- | --- |
| CURRENT_TOP20_SOURCE | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| TRACKER_SOURCE | D:\us-tech-quant\outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv |
| LOOKAHEAD_DAYS | 90 |
| ALPHAVANTAGE_ENABLED | FALSE |
| YFINANCE_FALLBACK_ENABLED | FALSE |
| FINNHUB_ENABLED | FALSE |
| FMP_ENABLED | FALSE |

## Company Event Coverage
| metric | value |
| --- | --- |
| EARNINGS_DATE_FOUND_COUNT | 1 |
| EARNINGS_DATE_MISSING_COUNT | 19 |
| MULTI_SOURCE_CONFLICT_COUNT | 0 |

## Tickers with earnings dates found
| ticker | rank | days_to_earnings | final_event_risk_level |
| --- | --- | --- | --- |
| GOOGL | 7 | 53 | LOW_PASS |

## Tickers still missing earnings dates
| ticker | rank | unknown_reason | recommended_fix |
| --- | --- | --- | --- |
| KEYS | 1 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| VRT | 2 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| ICHR | 3 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| NVDA | 4 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| D | 5 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| AMKR | 6 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| FIX | 8 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| MCHP | 9 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| LITE | 10 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| CARR | 11 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| ENTG | 12 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| CRWV | 13 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| ETR | 14 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| COHU | 15 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| GEV | 16 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| FN | 17 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| ETN | 18 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| HUBB | 19 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| POWL | 20 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |

## Risk reference distribution
| risk_level | count |
| --- | --- |
| LOW_PASS | 1 |
| UNKNOWN_REVIEW | 19 |

## Seed proposal rows safe to copy
| ticker | manual_next_earnings_date | manual_event_risk_level | source_note |
| --- | --- | --- | --- |
| GOOGL | 2026-07-22 | LOW_PASS | cloud_earnings_event_calendar.csv |

## Safety statement
Risk scores are reference-only. V18.47C-R2 does not change official ranking, factor weights, official buy permission, official sell permission, broker behavior, order behavior, or trading execution.

## Suggested next step
Rerun V18.47C and check UNKNOWN_REVIEW_COUNT. If coverage remains weak, review the seed proposal; if coverage is usable, proceed to V18.48A Top20 Options Data Collector.
