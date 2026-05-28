# V18.47B Top20 Priority Tracker Report

V18.47B is a read-only Top20 tracking layer. It does not change official ranking logic, factor weights, candidate scoring, Top20 selection, freshness eligibility, trading execution, broker/order behavior, signal freeze ledgers, or V18.47A governance outputs.

## Current source and counts
| metric | value |
| --- | --- |
| CURRENT_TOP20_SOURCE | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| CURRENT_TOP20_SNAPSHOT_COUNT | 20 |
| TIER_1_CORE_COUNT | 0 |
| TIER_2_IMPORTANT_COUNT | 10 |
| TIER_3_OCCASIONAL_COUNT | 10 |
| TIER_4_CACHE_ONLY_COUNT | 0 |

## TIER_1_CORE tickers
| ticker | latest_rank | top20_entry_count_60d | consecutive_top20_days | tracking_tier_reason |
| --- | --- | --- | --- | --- |

## TIER_2_IMPORTANT tickers
| ticker | latest_rank | top20_entry_count_60d | tracking_tier_reason |
| --- | --- | --- | --- |
| KEYS | 1 | 1 | CURRENT_LATEST_RANK_LE_10 |
| VRT | 2 | 1 | CURRENT_LATEST_RANK_LE_10 |
| ICHR | 3 | 1 | CURRENT_LATEST_RANK_LE_10 |
| NVDA | 4 | 1 | CURRENT_LATEST_RANK_LE_10 |
| D | 5 | 1 | CURRENT_LATEST_RANK_LE_10 |
| AMKR | 6 | 1 | CURRENT_LATEST_RANK_LE_10 |
| GOOGL | 7 | 1 | CURRENT_LATEST_RANK_LE_10 |
| FIX | 8 | 1 | CURRENT_LATEST_RANK_LE_10 |
| MCHP | 9 | 1 | CURRENT_LATEST_RANK_LE_10 |
| LITE | 10 | 1 | CURRENT_LATEST_RANK_LE_10 |

## High-priority event tracking tickers
| ticker | latest_rank | tracking_tier | event_tracking_priority |
| --- | --- | --- | --- |

## High-priority options tracking tickers
| ticker | latest_rank | tracking_tier | options_tracking_priority |
| --- | --- | --- | --- |

## Safety statement
OFFICIAL_RANKING_CHANGED is FALSE and FACTOR_WEIGHTS_CHANGED is FALSE. V18.47B only records Top20 history and computes tracking tiers.

## Suggested next step
V18.47C Top20 Event / Earnings Risk Layer.
