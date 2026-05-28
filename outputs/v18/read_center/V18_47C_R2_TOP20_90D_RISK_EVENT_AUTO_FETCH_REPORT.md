# V18.47C-R2 Top20 90-Day Risk Event Auto Fetch Report

V18.47C-R2 identifies upcoming risk events and writes reference-only risk fields. It does not predict event outcomes, earnings results, macro impact, Fed outcomes, or stock direction.

## Sources and Providers
| metric | value |
| --- | --- |
| CURRENT_TOP20_SOURCE | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| TRACKER_SOURCE | D:\us-tech-quant\outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv |
| LOOKAHEAD_DAYS | 90 |
| ALPHAVANTAGE_ENABLED | TRUE |
| YFINANCE_FALLBACK_ENABLED | FALSE |
| FINNHUB_ENABLED | FALSE |
| FMP_ENABLED | FALSE |

## Company Event Coverage
| metric | value |
| --- | --- |
| EARNINGS_DATE_FOUND_COUNT | 18 |
| EARNINGS_DATE_MISSING_COUNT | 2 |
| MULTI_SOURCE_CONFLICT_COUNT | 1 |

## Tickers with earnings dates found
| ticker | rank | days_to_earnings | final_event_risk_level |
| --- | --- | --- | --- |
| KEYS | 1 | 82 | LOW_PASS |
| VRT | 2 | 62 | LOW_PASS |
| ICHR | 3 | 68 | LOW_PASS |
| D | 5 | 63 | LOW_PASS |
| AMKR | 6 | 60 | LOW_PASS |
| GOOGL | 7 | 55 | LOW_PASS |
| FIX | 8 | 56 | LOW_PASS |
| MCHP | 9 | 70 | LOW_PASS |
| LITE | 10 | 76 | LOW_PASS |
| CARR | 11 | 61 | LOW_PASS |
| ENTG | 12 | 63 | LOW_PASS |
| ETR | 14 | 63 | LOW_PASS |
| COHU | 15 | 63 | LOW_PASS |
| GEV | 16 | 62 | LOW_PASS |
| FN | 17 | 81 | LOW_PASS |
| ETN | 18 | 68 | LOW_PASS |
| HUBB | 19 | 61 | LOW_PASS |
| POWL | 20 | 68 | LOW_PASS |

## Tickers still missing earnings dates
| ticker | rank | unknown_reason | recommended_fix |
| --- | --- | --- | --- |
| NVDA | 4 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |
| CRWV | 13 | NO_RELIABLE_EARNINGS_DATE | REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED |

## Risk reference distribution
| risk_level | count |
| --- | --- |
| LOW_PASS | 18 |
| UNKNOWN_REVIEW | 2 |

## Seed proposal rows safe to copy
| ticker | manual_next_earnings_date | manual_event_risk_level | source_note |
| --- | --- | --- | --- |
| KEYS | 2026-08-18 | LOW_PASS | ALPHAVANTAGE_BULK |
| VRT | 2026-07-29 | LOW_PASS | ALPHAVANTAGE_BULK |
| ICHR | 2026-08-04 | LOW_PASS | ALPHAVANTAGE_BULK |
| D | 2026-07-30 | LOW_PASS | ALPHAVANTAGE_BULK |
| AMKR | 2026-07-27 | LOW_PASS | ALPHAVANTAGE_BULK |
| FIX | 2026-07-23 | LOW_PASS | ALPHAVANTAGE_BULK |
| MCHP | 2026-08-06 | LOW_PASS | ALPHAVANTAGE_BULK |
| LITE | 2026-08-12 | LOW_PASS | ALPHAVANTAGE_BULK |
| CARR | 2026-07-28 | LOW_PASS | ALPHAVANTAGE_BULK |
| ENTG | 2026-07-30 | LOW_PASS | ALPHAVANTAGE_BULK |
| ETR | 2026-07-30 | LOW_PASS | ALPHAVANTAGE_BULK |
| COHU | 2026-07-30 | LOW_PASS | ALPHAVANTAGE_BULK |
| GEV | 2026-07-29 | LOW_PASS | ALPHAVANTAGE_BULK |
| FN | 2026-08-17 | LOW_PASS | ALPHAVANTAGE_BULK |
| ETN | 2026-08-04 | LOW_PASS | ALPHAVANTAGE_BULK |
| HUBB | 2026-07-28 | LOW_PASS | ALPHAVANTAGE_BULK |
| POWL | 2026-08-04 | LOW_PASS | ALPHAVANTAGE_BULK |

## Safety statement
Risk scores are reference-only. V18.47C-R2 does not change official ranking, factor weights, official buy permission, official sell permission, broker behavior, order behavior, or trading execution.

## Suggested next step
Rerun V18.47C and check UNKNOWN_REVIEW_COUNT. If coverage remains weak, review the seed proposal; if coverage is usable, proceed to V18.48A Top20 Options Data Collector.
