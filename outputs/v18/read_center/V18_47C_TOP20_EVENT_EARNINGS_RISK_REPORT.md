# V18.47C Top20 Event / Earnings Risk Report

V18.47C is a read-only event risk layer. It does not predict event outcomes and does not change official ranking logic, factor weights, candidate scoring, Top20 selection, freshness eligibility, trading execution, broker/order behavior, signal freeze ledgers, or V18.47A/V18.47B outputs.

## Source coverage and distribution
| metric | value |
| --- | --- |
| CURRENT_TOP20_SOURCE | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| V18_47B_TRACKER_SOURCE | D:\us-tech-quant\outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv |
| EVENT_SOURCE_COUNT_FOUND | 6 |
| EVENT_SOURCES_FOUND | D:\us-tech-quant\state\v18\V18_47C_TOP20_EVENT_EARNINGS_SEED.csv;D:\us-tech-quant\state\v18\V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv;D:\us-tech-quant\state\v18\cloud_earnings_event_calendar.csv;D:\us-tech-quant\state\v16\event_calendar.csv;D:\us-tech-quant\data\events\v16_macro_events.csv;D:\us-tech-quant\data\events\v16_earnings_overrides.csv |
| EVENT_SOURCES_MISSING | D:\us-tech-quant\state\v18\manual_event_overrides.csv;D:\us-tech-quant\state\v18\V18_47C_MANUAL_EVENT_OVERRIDES.csv |
| LOW_PASS | 18 |
| MEDIUM_REDUCE_SIZE | 0 |
| HIGH_HOLD_REVIEW | 0 |
| EXTREME_NO_NEW_BUYS | 0 |
| UNKNOWN_REVIEW | 2 |

## EXTREME_NO_NEW_BUYS
| ticker | rank | final_event_risk_reason | buy_permission_after_event_gate |
| --- | --- | --- | --- |

## HIGH_HOLD_REVIEW
| ticker | rank | final_event_risk_reason | sell_review_after_event_gate |
| --- | --- | --- | --- |

## MEDIUM_REDUCE_SIZE
| ticker | rank | final_event_risk_reason | buy_permission_after_event_gate |
| --- | --- | --- | --- |

## UNKNOWN_REVIEW
| ticker | rank | event_data_quality | final_event_risk_reason |
| --- | --- | --- | --- |
| NVDA | 4 | UNKNOWN_REVIEW_REQUIRED | Known event risks are low, but missing source data prevents confident pass: No local earnings date found for ticker. |
| CRWV | 13 | UNKNOWN_REVIEW_REQUIRED | Known event risks are low, but missing source data prevents confident pass: No local earnings date found for ticker. |

## Upcoming earnings windows
| ticker | next_earnings_date | days_to_earnings | earnings_risk_level | earnings_risk_reason |
| --- | --- | --- | --- | --- |

## Upcoming macro event windows
| ticker | macro_event_date | macro_event_type | days_to_macro_event | macro_risk_level |
| --- | --- | --- | --- | --- |

## Manual override events
| ticker | manual_event_date | manual_event_type | manual_event_risk_level | manual_event_reason |
| --- | --- | --- | --- | --- |

## Suggested next step
V18.48A Top20 Options Data Collector if options data readiness is the priority, or V18.49B Entry/Exit Plan Generator if action planning is the priority.
