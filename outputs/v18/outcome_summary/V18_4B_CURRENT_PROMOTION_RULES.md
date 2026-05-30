# V18.4B Factor Outcome Summary and Promotion Rules

- V18_4B_STATUS: `OK_PROMOTION_RULES_UPDATED_NO_PROMOTION`
- RUN_TIME: `2026-05-30 22:36:17`
- TRACKER_TOTAL_ROWS: `630`
- SNAPSHOT_DATE_COUNT: `6`
- LATEST_SNAPSHOT_PRICE_DATE: `2026-05-29`

## Current Decision Context

- FINAL_ACTION: `BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION`
- BUY_PERMISSION: `UNKNOWN`
- SELECTED_FACTOR: `F002`
- FACTOR_PACK_OVERLAP_NAMES: `NONE`

## Completed Forward Observations

| horizon | completed_count |
|---:|---:|
| 1obs | 525 |
| 3obs | 315 |
| 5obs | 105 |
| 10obs | 0 |
| 20obs | 0 |

## Group Outcome Summary

| group | horizon | completed | avg % | median % | win rate % | min n | eval |
|---|---:|---:|---:|---:|---:|---:|---|
| factor_top10 | 1obs | 50 | 2.8749 | 1.7936 | 58.0000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top10 | 3obs | 30 | 11.6499 | 5.6221 | 70.0000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top10 | 5obs | 10 | 15.6540 | 6.9451 | 70.0000 | 20 | WATCH_DATA_INSUFFICIENT |
| factor_top10 | 10obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top10 | 20obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top30 | 1obs | 151 | 2.0007 | 0.6073 | 58.2781 | 40 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top30 | 3obs | 91 | 5.8605 | 3.1421 | 63.7363 | 40 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top30 | 5obs | 30 | 12.9718 | 9.1619 | 70.0000 | 40 | WATCH_DATA_INSUFFICIENT |
| factor_top30 | 10obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| factor_top30 | 20obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| official_review | 1obs | 50 | 4.9162 | 1.8457 | 64.0000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| official_review | 3obs | 30 | 14.3460 | 8.3318 | 73.3333 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| official_review | 5obs | 10 | 26.0713 | 15.5522 | 80.0000 | 20 | WATCH_DATA_INSUFFICIENT |
| official_review | 10obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| official_review | 20obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 1obs | 15 | -0.3396 | 0.7047 | 53.3333 | 8 | NEUTRAL_KEEP_WATCHING |
| factor_pack_overlap | 3obs | 13 | 11.2379 | 3.0116 | 61.5385 | 8 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_pack_overlap | 5obs | 4 | 33.0815 | 30.6645 | 75.0000 | 8 | WATCH_DATA_INSUFFICIENT |
| factor_pack_overlap | 10obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 20obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| v18_3c_overlap | 1obs | 11 | 11.0580 | 2.8495 | 72.7273 | 6 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| v18_3c_overlap | 3obs | 6 | 33.5578 | 31.8242 | 66.6667 | 6 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| v18_3c_overlap | 5obs | 2 | 66.1521 | 66.1521 | 100.0000 | 6 | WATCH_DATA_INSUFFICIENT |
| v18_3c_overlap | 10obs | 0 | NA | NA | NA | 6 | NO_COMPLETED_OBS_YET |
| v18_3c_overlap | 20obs | 0 | NA | NA | NA | 6 | NO_COMPLETED_OBS_YET |

## Promotion Rules

A group can only become a promotion candidate when all of these are true:

1. Completed sample count reaches the group-specific minimum.
2. Average return is at least +1.0%.
3. Median return is at least +0.5%.
4. Win rate is at least 55%.
5. The confirming horizon is 5obs, 10obs, or 20obs.

Current promotion recommendation:

- PROMOTION_RECOMMENDATION: `KEEP_WATCHING`
- PROMOTION_CANDIDATE_COUNT: `0`
- REJECT_CANDIDATE_COUNT: `0`

## Safety

- OFFICIAL_DECISION_IMPACT: `NONE`
- PROMOTION_ACTION: `NONE`

This module is evaluation-only. It does not change official BUY/NO_BUY decisions.
