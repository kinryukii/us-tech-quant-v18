# V18.16I Rolling Scan Coverage Policy Optimizer

- STATUS: OK_V18_16I_ROLLING_SCAN_COVERAGE_POLICY_OPTIMIZER_READY
- MODE: DRYRUN_POLICY_OPTIMIZER
- TOTAL_UNIVERSE_COUNT: 325
- CURRENT_DAILY_SCAN_COUNT: 45
- REQUIRED_DAILY_SCAN_COUNT: 65
- RECOMMENDED_DAILY_SCAN_COUNT: 65
- TIER_WEIGHTED_FULL_COVERAGE_DAILY_COUNT: 110
- CURRENT_COVERAGE_TARGET_MET: FALSE
- PROJECTED_DAILY_THRESHOLD_MET: TRUE
- PROJECTED_DAILY_THRESHOLD_SHORTFALL_AFTER: 0
- PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET: FALSE
- PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_COUNT: 149
- PROJECTED_TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: 176
- PROJECTED_COVERAGE_TARGET_MET_LEGACY_DAILY_THRESHOLD: TRUE
- COVERAGE_SHORTFALL_BEFORE: 20
- RECOMMENDED_QUOTAS: CORE_DAILY=30, CANDIDATE=14, STRONG_WATCH=5, WATCHLIST=4, RESEARCH=12
- POLICY_APPLIED: FALSE
- VALIDATION_FAIL_COUNT: 0

## Current Problem Summary

The current rolling scan count is 45, below the existing 65 per-day threshold derived from 325 names over 5 trading days. The recent shortfall is 20, with scan limit reason `ESTIMATED_PLAN_COST_LIMIT`.

## Tier Breakdown

| tier | count | current selected | recommended quota | recommended frequency |
| --- | ---: | ---: | ---: | --- |
| CORE_DAILY | 30 | 30 | 30 | EVERY_TRADING_DAY |
| CANDIDATE | 14 | 15 | 14 | EVERY_TRADING_DAY_OR_NEAR_DAILY |
| STRONG_WATCH | 21 | 0 | 5 | EVERY_2_TRADING_DAYS |
| WATCHLIST | 20 | 0 | 4 | EVERY_3_TRADING_DAYS |
| RESEARCH | 240 | 0 | 12 | EVERY_5_TRADING_DAYS_ROTATION |

## Proposed Policy

The advisory next-step policy targets 65 scans/day to close the current daily-threshold shortfall while preserving daily CORE_DAILY and CANDIDATE coverage first. This is not a true full-universe coverage fix. A stricter tier-aware full-coverage policy estimates 110 scans/day, which should be reviewed separately because it may exceed current estimated cost limits.

## 5-Day Plan

| day | total | core | candidate | strong | watchlist | research | cumulative unique | remaining | target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DAY_1 | 65 | 30 | 14 | 5 | 4 | 12 | 65 | 260 | TRUE |
| DAY_2 | 65 | 30 | 14 | 4 | 4 | 13 | 86 | 239 | TRUE |
| DAY_3 | 65 | 30 | 14 | 4 | 4 | 13 | 107 | 218 | TRUE |
| DAY_4 | 65 | 30 | 14 | 4 | 4 | 13 | 128 | 197 | TRUE |
| DAY_5 | 65 | 30 | 14 | 4 | 4 | 13 | 149 | 176 | TRUE |

## Expected Improvement

- PROJECTED_DAILY_THRESHOLD_MET would likely move from FALSE to TRUE if a future scheduler policy can safely run the recommended quota.
- PROJECTED_DAILY_THRESHOLD_SHORTFALL_AFTER would move from 20 to 0.
- PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET remains FALSE with 149/325 unique names covered and 176 uncovered.
- Daily threshold blocker may be reduced if 65/day is applied, but coverage trust should remain WARN/degraded until true five-day unique coverage improves.
- V18.19A should not infer HIGH trust solely from daily-threshold coverage.

## Risks / Unknowns

- Runtime confidence: HIGH. ACTUAL_RUNTIME_SECONDS=9.656; SOFT_STOP_SECONDS=270.0; MAX_RUNTIME_SECONDS=300.0
- Estimated cost confidence: HIGH. Current scheduler estimate is 330 against max 300.
- True full unique five-day coverage remains constrained by high-tier daily repeats unless cost/runtime policy is revised.

## Future APPLY Requirements

- V18.16J may address the conservative daily threshold gap.
- V18.16K is required for true five-day unique coverage scheduling.
- Update the scheduler policy explicitly if adopting the recommended quota.
- Recalculate estimated plan cost before applying any higher scan count.
- Keep yfinance disabled unless a separate approved task changes provider behavior.
- Re-run V18.19A and V18.20K verification after any future policy apply.

## Dryrun Statement

No rolling scan policy was applied. No state file, current daily command center, promotion/demotion engine, ranking output, price update behavior, yfinance behavior, auto trading, auto selling, or official decision logic was modified.

## Validation

- ROLLING_STATE_INPUT_OK: PASS OK
- COVERAGE_INPUT_OK: PASS OK
- SCAN_RESULT_INPUT_OK: PASS OK
- PROMOTION_INPUT_OK: PASS OK
- OUTPUT_POLICY_AUDIT_EXISTS: PASS D:\us-tech-quant\outputs\v18\universe\V18_16I_CURRENT_COVERAGE_POLICY_AUDIT.csv
- OUTPUT_TIER_REQUIREMENTS_EXISTS: PASS D:\us-tech-quant\outputs\v18\universe\V18_16I_CURRENT_TIER_SCAN_REQUIREMENTS.csv
- OUTPUT_RECOMMENDED_PLAN_EXISTS: PASS D:\us-tech-quant\outputs\v18\universe\V18_16I_CURRENT_RECOMMENDED_SCAN_PLAN.csv
- OUTPUT_5DAY_PLAN_EXISTS: PASS D:\us-tech-quant\outputs\v18\universe\V18_16I_CURRENT_5DAY_COVERAGE_PLAN.csv
- TOTAL_UNIVERSE_GT_ZERO: PASS 325
- POLICY_APPLIED_FALSE: PASS 
- STATE_NOT_MODIFIED: PASS 
- CURRENT_DAILY_NOT_MODIFIED: PASS 
- PROMOTION_DEMOTION_NOT_MODIFIED: PASS 
- RANKING_NOT_MODIFIED: PASS 
- PRICE_UPDATE_NOT_MODIFIED: PASS 
- AUTO_TRADE_DISABLED: PASS DISABLED
- AUTO_SELL_DISABLED: PASS DISABLED
- OFFICIAL_DECISION_IMPACT_NONE: PASS NONE
- PYTHON_PARSE_SELF: PASS OK_COMPILE
