# V18.28A-R2 Remaining UNKNOWN Theme Patch

## Read First

- STATUS: OK_V18_28A_R2_REMAINING_UNKNOWN_THEME_PATCH_READY
- MODE: REMAINING_UNKNOWN_THEME_PATCH
- RUN_ID: 20260523_140813
- THEME_MAP_ROW_COUNT_BEFORE: 252
- THEME_MAP_ROW_COUNT_AFTER: 252
- PATCH_TARGET_COUNT: 15
- PATCHED_ROW_COUNT: 15
- SKIPPED_ALREADY_CLASSIFIED_COUNT: 0
- UNKNOWN_PRIMARY_THEME_COUNT_BEFORE: 15
- UNKNOWN_PRIMARY_THEME_COUNT_AFTER: 0
- DUPLICATE_THEME_TICKER_COUNT_AFTER: 0
- REFRESHED_R28A_STATUS: OK_V18_28A_THEME_CLASSIFICATION_READY
- FORBIDDEN_MODIFIED: FALSE
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED

## Patch Results

| ticker | found_in_theme_map | primary_theme_before | primary_theme_after | manual_review_required_before | manual_review_required_after | patched | skipped_reason | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BLTE | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| TEVA | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| COGT | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| RSP | TRUE | UNKNOWN | OTHER | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. Non-single-stock instrument; exclude or separately bucket in single-stock factor backtests. |
| INSM | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| WVE | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| PSIX | TRUE | UNKNOWN | POWER_INFRASTRUCTURE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| RERE | TRUE | UNKNOWN | ECOMMERCE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| STG | TRUE | UNKNOWN | CONSUMER | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| RBLX | TRUE | UNKNOWN | INTERNET_PLATFORM | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| OLMA | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| ARGT | TRUE | UNKNOWN | OTHER | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. Non-single-stock instrument; exclude or separately bucket in single-stock factor backtests. |
| APG | TRUE | UNKNOWN | INDUSTRIAL | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |
| ALM | TRUE | UNKNOWN | OTHER | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. Consider adding MATERIALS or CRITICAL_MINERALS as a future primary_theme. |
| NAMS | TRUE | UNKNOWN | HEALTHCARE | TRUE | FALSE | TRUE |  | V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch. |

## Primary Theme Counts After

| primary_theme | count |
| --- | --- |
| SOFTWARE | 28 |
| SEMICONDUCTOR | 25 |
| HEALTHCARE | 22 |
| POWER_INFRASTRUCTURE | 19 |
| CONSUMER | 18 |
| SEMICONDUCTOR_EQUIPMENT | 18 |
| FINTECH | 17 |
| INDUSTRIAL | 16 |
| DATA_INFRASTRUCTURE | 13 |
| INTERNET_PLATFORM | 13 |
| AI_INFRASTRUCTURE | 11 |
| ECOMMERCE | 9 |
| CRYPTO_BETA | 8 |
| TRANSPORTATION | 8 |
| ENERGY | 7 |
| ELECTRONICS_SUPPLY_CHAIN | 6 |
| CYBERSECURITY | 5 |
| DEFENSIVE | 5 |
| OTHER | 4 |

## Safety

- No external data fetch was performed.
- Only UNKNOWN or blank rows for the 15 controlled target tickers were eligible for patching.
- Existing non-UNKNOWN classifications were preserved.
- R28A classification audit outputs were refreshed after patching.
