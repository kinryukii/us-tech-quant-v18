# V18.28C Recommendation Tier Calibration Audit

## Read First

- STATUS: WARN_V18_28C_RECOMMENDATION_TIER_CALIBRATION_REVIEW_NEEDED
- MODE: READ_ONLY_RECOMMENDATION_TIER_CALIBRATION_AUDIT
- RUN_ID: 20260523_143444
- INPUT_RECOMMENDATION_ROW_COUNT: 252
- CURRENT_RANKED_CANDIDATE_ROW_COUNT: 252
- MISSING_RECOMMENDATION_TIER_COUNT: 0
- MISSING_RECOMMENDATION_ACTION_COUNT: 0
- UNKNOWN_PRIMARY_THEME_COUNT: 0
- DUPLICATE_TICKER_COUNT: 0
- CORE_CANDIDATE_COUNT: 6
- WATCHLIST_STRONG_COUNT: 38
- TACTICAL_ENTRY_COUNT: 24
- OVERHEATED_WAIT_COUNT: 27
- SPECULATIVE_SATELLITE_COUNT: 38
- DEFENSIVE_HEDGE_COUNT: 13
- ETF_OR_MACRO_EXPOSURE_COUNT: 2
- DO_NOT_PRIORITIZE_COUNT: 104
- TOP_30_SPECULATIVE_SATELLITE_COUNT: 19
- TOP_30_OVERHEATED_WAIT_COUNT: 0
- TOP_30_CORE_CANDIDATE_COUNT: 6
- POSSIBLE_CORE_REVIEW_COUNT: 0
- POSSIBLE_WATCHLIST_REVIEW_COUNT: 12
- OVERHEAT_RULE_REVIEW_COUNT: 0
- VOLATILITY_RULE_REVIEW_COUNT: 7
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- FORBIDDEN_MODIFIED: FALSE

## Current Recommendation Tier Counts

| key | count |
| --- | --- |
| DO_NOT_PRIORITIZE | 104 |
| SPECULATIVE_SATELLITE | 38 |
| WATCHLIST_STRONG | 38 |
| OVERHEATED_WAIT | 27 |
| TACTICAL_ENTRY | 24 |
| DEFENSIVE_HEDGE | 13 |
| CORE_CANDIDATE | 6 |
| ETF_OR_MACRO_EXPOSURE | 2 |

## Top 30 Tier Distribution

| tier | count |
| --- | --- |
| SPECULATIVE_SATELLITE | 19 |
| CORE_CANDIDATE | 6 |
| WATCHLIST_STRONG | 4 |
| DEFENSIVE_HEDGE | 1 |

## Top 75 Tier Distribution

| tier | count |
| --- | --- |
| SPECULATIVE_SATELLITE | 36 |
| WATCHLIST_STRONG | 29 |
| CORE_CANDIDATE | 6 |
| DEFENSIVE_HEDGE | 3 |
| ETF_OR_MACRO_EXPOSURE | 1 |

## Tier by Primary Theme

| primary_theme | CORE_CANDIDATE | WATCHLIST_STRONG | TACTICAL_ENTRY | OVERHEATED_WAIT | SPECULATIVE_SATELLITE | DEFENSIVE_HEDGE | ETF_OR_MACRO_EXPOSURE | DO_NOT_PRIORITIZE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI_INFRASTRUCTURE |  |  |  | 4 | 2 |  |  | 5 |
| CONSUMER |  | 5 | 5 | 1 | 4 | 1 |  | 2 |
| CRYPTO_BETA |  |  |  | 2 | 3 |  |  | 3 |
| CYBERSECURITY |  | 2 |  | 3 |  |  |  |  |
| DATA_INFRASTRUCTURE | 1 |  |  | 2 | 1 | 1 |  | 8 |
| DEFENSIVE |  |  |  |  |  | 5 |  |  |
| ECOMMERCE |  | 2 |  |  | 2 |  |  | 5 |
| ELECTRONICS_SUPPLY_CHAIN | 1 | 2 |  | 1 |  |  |  | 2 |
| ENERGY |  | 3 |  |  | 3 | 1 |  |  |
| FINTECH |  | 5 | 2 |  | 3 |  |  | 7 |
| HEALTHCARE |  |  | 1 |  | 9 | 4 |  | 8 |
| INDUSTRIAL |  | 5 | 2 |  | 1 | 1 |  | 7 |
| INTERNET_PLATFORM |  | 3 | 3 | 1 | 2 |  |  | 4 |
| OTHER |  | 1 |  |  |  |  | 2 | 1 |
| POWER_INFRASTRUCTURE |  | 2 | 4 |  | 1 |  |  | 12 |
| SEMICONDUCTOR | 3 |  |  | 3 | 2 |  |  | 17 |
| SEMICONDUCTOR_EQUIPMENT |  | 3 |  | 5 |  |  |  | 10 |
| SOFTWARE |  | 3 | 6 | 5 | 4 |  |  | 10 |
| TRANSPORTATION | 1 | 2 | 1 |  | 1 |  |  | 3 |

## Tier by Volatility Bucket

| group | CORE_CANDIDATE | WATCHLIST_STRONG | TACTICAL_ENTRY | OVERHEATED_WAIT | SPECULATIVE_SATELLITE | DEFENSIVE_HEDGE | ETF_OR_MACRO_EXPOSURE | DO_NOT_PRIORITIZE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXTREME |  |  |  | 5 | 26 |  |  | 16 |
| HIGH | 5 | 15 | 8 | 13 | 12 |  | 1 | 54 |
| LOW |  | 3 | 1 |  |  | 8 |  | 1 |
| MEDIUM | 1 | 20 | 15 | 9 |  | 5 | 1 | 33 |

## Tier by Role Bucket

| group | CORE_CANDIDATE | WATCHLIST_STRONG | TACTICAL_ENTRY | OVERHEATED_WAIT | SPECULATIVE_SATELLITE | DEFENSIVE_HEDGE | ETF_OR_MACRO_EXPOSURE | DO_NOT_PRIORITIZE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CORE_GROWTH |  | 14 | 11 | 13 |  |  |  | 25 |
| CYCLICAL_GROWTH | 6 | 8 | 3 | 8 |  |  |  | 36 |
| DEFENSIVE_HEDGE |  |  |  |  |  | 13 |  |  |
| NON_CORE |  | 4 | 1 |  |  |  | 1 | 2 |
| SPECULATIVE_SATELLITE |  |  |  | 5 | 37 |  |  | 26 |
| TACTICAL_BETA |  | 12 | 9 | 1 | 1 |  | 1 | 15 |

## Possible CORE Review Candidates

_None._

## Possible WATCHLIST Review Candidates

| rank | ticker | primary_theme | role_bucket | volatility_bucket | recommendation_tier | reason_codes | audit_comment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | SITM | SEMICONDUCTOR | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 2, tier SPECULATIVE_SATELLITE, theme SEMICONDUCTOR, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 8 | TWLO | SOFTWARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 8, tier SPECULATIVE_SATELLITE, theme SOFTWARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 11 | OLPX | CONSUMER | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 11, tier SPECULATIVE_SATELLITE, theme CONSUMER, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 13 | U | SOFTWARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 13, tier SPECULATIVE_SATELLITE, theme SOFTWARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 16 | SATS | DATA_INFRASTRUCTURE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 16, tier SPECULATIVE_SATELLITE, theme DATA_INFRASTRUCTURE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 18 | XYZ | FINTECH | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 18, tier SPECULATIVE_SATELLITE, theme FINTECH, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 24 | ROKU | INTERNET_PLATFORM | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 24, tier SPECULATIVE_SATELLITE, theme INTERNET_PLATFORM, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 36 | RNG | SOFTWARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW: rank 36, tier SPECULATIVE_SATELLITE, theme SOFTWARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. |
| 45 | RDDT | INTERNET_PLATFORM | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW: rank 45, tier SPECULATIVE_SATELLITE, theme INTERNET_PLATFORM, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. |
| 54 | PCOR | SOFTWARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_75_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW: rank 54, tier SPECULATIVE_SATELLITE, theme SOFTWARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. |
| 56 | PI | SEMICONDUCTOR | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_75_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW: rank 56, tier SPECULATIVE_SATELLITE, theme SEMICONDUCTOR, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. |
| 71 | INSM | HEALTHCARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_75_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW: rank 71, tier SPECULATIVE_SATELLITE, theme HEALTHCARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. |

## Overheated Wait Review Candidates

_None._

## Volatility Rule Review Candidates

| rank | ticker | primary_theme | role_bucket | volatility_bucket | recommendation_tier | reason_codes | audit_comment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | SITM | SEMICONDUCTOR | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 2, tier SPECULATIVE_SATELLITE, theme SEMICONDUCTOR, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 8 | TWLO | SOFTWARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 8, tier SPECULATIVE_SATELLITE, theme SOFTWARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 11 | OLPX | CONSUMER | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 11, tier SPECULATIVE_SATELLITE, theme CONSUMER, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 13 | U | SOFTWARE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 13, tier SPECULATIVE_SATELLITE, theme SOFTWARE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 16 | SATS | DATA_INFRASTRUCTURE | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 16, tier SPECULATIVE_SATELLITE, theme DATA_INFRASTRUCTURE, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 18 | XYZ | FINTECH | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 18, tier SPECULATIVE_SATELLITE, theme FINTECH, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |
| 24 | ROKU | INTERNET_PLATFORM | SPECULATIVE_SATELLITE | HIGH | SPECULATIVE_SATELLITE | TOP_30_RANK;TOP_75_RANK;TOP_3_THEME_RANK;SPECULATIVE_ROLE;HIGH_VOLATILITY;HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE;TECHNICAL_CAUTION | POSSIBLE_WATCHLIST_REVIEW;VOLATILITY_RULE_REVIEW: rank 24, tier SPECULATIVE_SATELLITE, theme INTERNET_PLATFORM, volatility HIGH. Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag. Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate. |

## Calibration Recommendations

- `POSSIBLE_CORE_REVIEW` count is 0; this suggests the current priority order may be over-penalizing top-30 cyclical growth names with only high volatility.
- `POSSIBLE_WATCHLIST_REVIEW` count is 12; consider whether top-75 / top-theme speculative names should be WATCHLIST_STRONG instead of SPECULATIVE_SATELLITE when technicals are not overheated.
- `OVERHEAT_RULE_REVIEW` count is 0; review whether `OVERHEATED_WAIT` should require stronger evidence than staging labels or high-volatility inference alone.
- `VOLATILITY_RULE_REVIEW` count is 7; review whether the volatility fallback is too aggressive for top-ranked candidates.

## Next-Step Recommendation For R29A / R29B

- `R29A`: calibrate rule priority and volatility thresholds on a copy of the advisory layer, focusing on top-30 and top-75 names that are currently speculative or waiting on pullbacks.
- `R29B`: if the calibration is accepted, rerun the tier layer with revised thresholds before any historical backtest or recommendation-policy promotion.

## Audit Details

- Rows with any audit flag: 12
- Strongly reviewed top-30 names: 0
