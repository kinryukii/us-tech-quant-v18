# V18.24A Dynamic Score Tier Migration Audit

Generated: 2026-05-21T16:20:36

## Purpose
Create a read-only score tier snapshot, compare it with the prior tier snapshot when available, and produce a separate movement/change audit. This step does not modify official ranking, factor pack, technical timing, signal snapshot, price cache, ledger, backtest, or trading state.

## Source Summary
Current ticker count: 324.
Score source: D:\us-tech-quant\outputs\v18\factor_pack\V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv (HIGH).
Previous snapshot found: TRUE.
Baseline mode: FALSE.

## Tier Policy
Default thresholds: score >= 85 Tier 1; 75-84.99 Tier 2; 65-74.99 Tier 3; 50-64.99 Tier 4; below 50 Tier 5. Missing score or missing local price evidence is Tier 0. Held-out/review tickers are capped at Tier 4. Full-history gaps are capped at Tier 4 when a usable score exists.

## Current Tier Distribution
- TIER_1_CORE_CANDIDATE: 16
- TIER_2_STRONG_WATCHLIST: 11
- TIER_3_WATCHLIST: 9
- TIER_4_REVIEW_ONLY: 16
- TIER_5_WEAK_OR_BLOCKED: 51
- TIER_0_DATA_NOT_READY: 221

## Movement Summary
- SAME_TIER_SCORE_DOWN: 310
- HELD_OUT_OR_REVIEW_BLOCKED: 14

## Top Reasons
- NO_MATERIAL_CHANGE: 324
- HELD_OUT_BY_BACKFILL_QUALITY: 14

## Limits And Trust Notes
Score coverage is limited to available local score/rank sources. Tier output is an audit/read-center artifact only and is not an official ranking change.

## Recommended Next Action
Use this read-only tier/movement report for operator review; do not modify official rankings or weights until score coverage, ledger coverage, and forward-return gates are ready.
