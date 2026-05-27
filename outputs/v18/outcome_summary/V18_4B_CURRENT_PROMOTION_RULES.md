# V18.4B Factor Outcome Summary and Promotion Rules

- V18_4B_STATUS: `OK_PROMOTION_RULES_UPDATED_NO_PROMOTION`
- RUN_TIME: `2026-05-19 10:53:52`
- TRACKER_TOTAL_ROWS: `420`
- SNAPSHOT_DATE_COUNT: `4`
- LATEST_SNAPSHOT_PRICE_DATE: `2026-05-18`

## Current Decision Context

- FINAL_ACTION: `BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION`
- BUY_PERMISSION: `UNKNOWN`
- SELECTED_FACTOR: `F002`
- FACTOR_PACK_OVERLAP_NAMES: `CRWV`

## Completed Forward Observations

| horizon | completed_count |
|---:|---:|
| 1obs | 315 |
| 3obs | 105 |
| 5obs | 0 |
| 10obs | 0 |
| 20obs | 0 |

## Group Outcome Summary

| group | horizon | completed | avg % | median % | win rate % | min n | eval |
|---|---:|---:|---:|---:|---:|---:|---|
| factor_top10 | 1obs | 30 | 0.0936 | -0.3029 | 46.6667 | 20 | NEUTRAL_KEEP_WATCHING |
| factor_top10 | 3obs | 10 | 0.5958 | -1.6422 | 30.0000 | 20 | WATCH_DATA_INSUFFICIENT |
| factor_top10 | 5obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top10 | 10obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top10 | 20obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_top30 | 1obs | 91 | -0.2884 | 0.0617 | 51.6484 | 40 | NEUTRAL_KEEP_WATCHING |
| factor_top30 | 3obs | 30 | -0.1184 | -1.0573 | 40.0000 | 40 | WATCH_DATA_INSUFFICIENT |
| factor_top30 | 5obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| factor_top30 | 10obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| factor_top30 | 20obs | 0 | NA | NA | NA | 40 | NO_COMPLETED_OBS_YET |
| official_review | 1obs | 30 | 0.1999 | 0.3411 | 50.0000 | 20 | KEEP_WATCHING_POSITIVE |
| official_review | 3obs | 10 | 0.5847 | -1.9524 | 40.0000 | 20 | WATCH_DATA_INSUFFICIENT |
| official_review | 5obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| official_review | 10obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| official_review | 20obs | 0 | NA | NA | NA | 20 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 1obs | 13 | -0.8135 | -1.1261 | 46.1538 | 8 | NEUTRAL_KEEP_WATCHING |
| factor_pack_overlap | 3obs | 4 | -3.3579 | -2.5739 | 0.0000 | 8 | WATCH_DATA_INSUFFICIENT |
| factor_pack_overlap | 5obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 10obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| factor_pack_overlap | 20obs | 0 | NA | NA | NA | 8 | NO_COMPLETED_OBS_YET |
| v18_3c_overlap | 1obs | 6 | -0.7812 | 0.0060 | 50.0000 | 6 | NEUTRAL_KEEP_WATCHING |
| v18_3c_overlap | 3obs | 2 | -2.5739 | -2.5739 | 0.0000 | 6 | WATCH_DATA_INSUFFICIENT |
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
