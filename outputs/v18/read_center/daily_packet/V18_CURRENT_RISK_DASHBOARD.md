# V18_CURRENT_RISK_DASHBOARD

| Field | Raw | Meaning | Impact |
| --- | --- | --- | --- |
| AUTO_TRADE | DISABLED | Live trading remains disabled. | No execution path changes. |
| AUTO_SELL | DISABLED | Auto-selling remains disabled. | No automatic exit behavior is enabled. |
| OFFICIAL_DECISION_IMPACT | NONE | This layer does not alter official decisions. | Official daily logic is unchanged. |
| VALIDATION_FAIL_COUNT | 0 | Validation errors in current daily chain. | Zero is preferred; non-zero would lower trust. |
| SAME_DAY_PROMOTION_GUARD | TRUE | Same-day core promotion protection is active when TRUE/ENABLED/ON. | FALSE/DISABLED/OFF is unsafe; UNKNOWN is degraded. |
| CORE_PROMOTION_ALLOWED_THIS_RUN | TRUE | Whether core promotion may proceed under the guard. | TRUE means the guard did not block the run. |
| RANK_SOURCE_STATUS | OK_SCORE_SOURCE_FOUND | Ranking input was found and read. | Missing ranking source would lower trust. |
| COVERAGE_TARGET_MET | TRUE | Rolling scan coverage target status. | FALSE means the scan did not reach the theoretical target. |
| COVERAGE_SHORTFALL_COUNT | 0 | How many names were not scanned versus target. | A shortfall leaves some names less recently refreshed. |
| DAILY_THRESHOLD_COVERAGE_SOURCE | outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt | Source used for daily threshold coverage. | Fresh V18.16J/V18.16F evidence is preferred over stale V18.16H audits. |
| DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS | OK_FRESH_DAILY_SCAN_SOURCE | Freshness/provenance for daily threshold source. | Fallback or stale sources are reported explicitly. |
| DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME | 2026-05-27T22:48:39 | Filesystem modified time for selected coverage source. | Newest valid daily-threshold evidence is selected. |
| DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON | Valid current-run read-first daily threshold evidence. | Why this daily-threshold source was selected. | Malformed newer candidates are skipped. |
| TRUE_5DAY_UNIQUE_COVERAGE_MET | FALSE | Separate true five-day unique universe coverage status. | FALSE caps trust below HIGH even if daily threshold is met. |
| PRICE_FRESHNESS_MODE | LOCAL_CACHE_ONLY_SAFE_MODE | Current price refresh used cache-only or cache-backed mode. | Cache-only mode is usable but not ideal for freshness. |
| PRICE_PREFLIGHT | PASS | Historical yfinance/caching preflight result. | FAIL indicates provider or cache repair issues were seen. |
| EVENT_AUDIT_AVAILABLE | TRUE | Whether event-risk freshness could be verified from an event audit. | Missing audit degrades freshness confidence. |
| EVENT_AUDIT_SENTENCE | Primary event audit was found at outputs/v18/risk/V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv. | Human-readable event-risk summary. | Derived from loaded audit state. |
| COMMAND_CENTER_SOURCE | outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt | Current command-center alias source used for operator fields. | The human-facing status source is visible. |
| COMMAND_CENTER_SOURCE_STATUS | OK | Parse status for the selected command-center alias. | Missing or malformed aliases are visible. |
| CURRENT_MODE_SOURCE | outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt | Current mode alias source used for freshness reporting. | The selected mode source is visible. |
| CURRENT_MODE_SOURCE_STATUS | OK | Parse status for the selected mode alias. | Missing or malformed aliases are visible. |

## Warnings

- Event provider statuses: NOT_UPDATED_NO_PROVIDER_IN_SAFE_MODE=318
- Current data freshness mode: READ_CENTER_REFRESH_ONLY
- Current cache-backed price mode: LOCAL_CACHE_ONLY_SAFE_MODE
- Coverage target met: TRUE
