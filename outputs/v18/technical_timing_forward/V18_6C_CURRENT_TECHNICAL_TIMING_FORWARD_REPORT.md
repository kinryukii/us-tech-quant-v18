# V18.6C Technical Timing Forward Tracker

## 1. Status

- V18_6C_STATUS: `OK_TECHNICAL_TIMING_FORWARD_TRACKER_READY`
- CURRENT_SNAPSHOT_ROWS: `105`
- NEW_TRACKER_ROWS_ADDED_OR_REFRESHED: `105`
- TRACKER_TOTAL_ROWS: `105`
- SNAPSHOT_DATE_COUNT: `2`
- LATEST_SNAPSHOT_PRICE_DATE: `2026-05-15`
- COMPLETED_1D_COUNT: `0`
- COMPLETED_3D_COUNT: `0`
- COMPLETED_5D_COUNT: `0`
- COMPLETED_10D_COUNT: `0`
- COMPLETED_20D_COUNT: `0`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. Purpose

This module tracks V18.6A technical timing signals forward.
It records the daily technical timing snapshot and later updates 1/3/5/10/20-day outcomes.

## 3. Signal Outcome Summary

| signal                |   horizon_days |   completed_obs |   avg_ret |   median_ret |   win_rate |   avg_win |   avg_loss |
|:----------------------|---------------:|----------------:|----------:|-------------:|-----------:|----------:|-----------:|
| WATCH_POSITIVE        |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| WATCH_POSITIVE        |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| WATCH_POSITIVE        |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| WATCH_POSITIVE        |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| WATCH_POSITIVE        |             20 |               0 |       nan |          nan |        nan |       nan |        nan |
| PULLBACK_WATCH        |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| PULLBACK_WATCH        |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| PULLBACK_WATCH        |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| PULLBACK_WATCH        |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| PULLBACK_WATCH        |             20 |               0 |       nan |          nan |        nan |       nan |        nan |
| BB_SQUEEZE            |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| BB_SQUEEZE            |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| BB_SQUEEZE            |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| BB_SQUEEZE            |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| BB_SQUEEZE            |             20 |               0 |       nan |          nan |        nan |       nan |        nan |
| BREAKOUT_CONTINUATION |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| BREAKOUT_CONTINUATION |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| BREAKOUT_CONTINUATION |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| BREAKOUT_CONTINUATION |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| BREAKOUT_CONTINUATION |             20 |               0 |       nan |          nan |        nan |       nan |        nan |
| EXHAUSTION_RISK       |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| EXHAUSTION_RISK       |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| EXHAUSTION_RISK       |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| EXHAUSTION_RISK       |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| EXHAUSTION_RISK       |             20 |               0 |       nan |          nan |        nan |       nan |        nan |
| OVERHEAT_UNCLASSIFIED |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| OVERHEAT_UNCLASSIFIED |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| OVERHEAT_UNCLASSIFIED |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| OVERHEAT_UNCLASSIFIED |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| OVERHEAT_UNCLASSIFIED |             20 |               0 |       nan |          nan |        nan |       nan |        nan |
| OLD_OVERHEAT          |              1 |               0 |       nan |          nan |        nan |       nan |        nan |
| OLD_OVERHEAT          |              3 |               0 |       nan |          nan |        nan |       nan |        nan |
| OLD_OVERHEAT          |              5 |               0 |       nan |          nan |        nan |       nan |        nan |
| OLD_OVERHEAT          |             10 |               0 |       nan |          nan |        nan |       nan |        nan |
| OLD_OVERHEAT          |             20 |               0 |       nan |          nan |        nan |       nan |        nan |

## 4. Output Files

- TRACKER: `D:\us-tech-quant\state\v18\V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_TRACKER.csv`
- SUMMARY: `D:\us-tech-quant\outputs\v18\technical_timing_forward\V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv`

## 5. Interpretation

- Completed counts will be low at the beginning.
- Promotion is not allowed from this module until enough forward observations mature.
- `OFFICIAL_DECISION_IMPACT` remains `NONE`.
