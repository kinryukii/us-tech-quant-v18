# V18.4B Factor Outcome Summary and Promotion Rules

- V18_4B_STATUS: `OK_PROMOTION_RULES_UPDATED_NO_PROMOTION`
- RUN_TIME: `2026-05-27 22:23:08`
- TRACKER_TOTAL_ROWS: `525`
- SNAPSHOT_DATE_COUNT: `5`
- LATEST_SNAPSHOT_PRICE_DATE: `2026-05-26`

## Current Decision Context

- FINAL_ACTION: `BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION`
- BUY_PERMISSION: `UNKNOWN`
- SELECTED_FACTOR: `F002`
- FACTOR_PACK_OVERLAP_NAMES: `CRWV`

## Completed Forward Observations

| horizon | completed_count |
|---:|---:|
| 1obs | 420 |
| 3obs | 210 |
| 5obs | 0 |
| 10obs | 0 |
| 20obs | 0 |

## Group Outcome Summary

| group | horizon | completed | avg % | median % | win rate % | min n | eval |
|---|---:|---:|---:|---:|---:|---:|---|
| factor_top10 | 1obs | 40 | 3.2124 | 1.8987 | 57.5000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top10 | 3obs | 20 | 4.8425 | 2.4923 | 55.0000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top10 | 5obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top10 | 10obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top10 | 20obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top30 | 1obs | 121 | 1.7006 | 0.5668 | 57.8512 | 40 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top30 | 3obs | 61 | 2.3301 | 1.7035 | 55.7377 | 40 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| factor_top30 | 5obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| factor_top30 | 10obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| factor_top30 | 20obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| official_review | 1obs | 40 | 4.1712 | 1.8457 | 62.5000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| official_review | 3obs | 20 | 7.9614 | 5.8203 | 65.0000 | 20 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| official_review | 5obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| official_review | 10obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| official_review | 20obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 1obs | 14 | -0.6094 | -0.2107 | 50.0000 | 8 | NEUTRAL_KEEP_WATCHING |
| factor_pack_overlap | 3obs | 10 | 4.5496 | 0.7508 | 50.0000 | 8 | KEEP_WATCHING_POSITIVE |
| factor_pack_overlap | 5obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 10obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 20obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| v18_3c_overlap | 1obs | 8 | 9.1004 | 2.2489 | 62.5000 | 6 | POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET |
| v18_3c_overlap | 3obs | 4 | 14.6252 | 10.3380 | 50.0000 | 6 | WATCH_DATA_INSUFFICIENT |
| v18_3c_overlap | 5obs | 0 | NA | NA | NA | 6 | NO_COMPLETED_OBS_YET |
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
