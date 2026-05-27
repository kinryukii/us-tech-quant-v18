# V18.34B Daily Output Freshness Guard

- STATUS: `WARN_V18_34B_DAILY_OUTPUT_FRESHNESS_REVIEW_NEEDED`
- GENERATED_AT: `2026-05-25T13:51:26`
- FRESHNESS_ROUND_CONSISTENT: `TRUE`
- MAX_KEY_FILE_GAP_HOURS: `13.95`

## Required Files
| file | exists | modified | age_hours |
| --- | --- | --- | ---: |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md` | TRUE | 2026-05-25T13:51:25 | 0.00 |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md` | TRUE | 2026-05-25T00:27:29 | 13.40 |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_CONTEXT_CONSISTENCY.md` | TRUE | 2026-05-24T23:54:21 | 13.95 |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_DAILY_TRADE_READINESS.md` | TRUE | 2026-05-25T13:51:25 | 0.00 |
| `D:\us-tech-quant\outputs\v18\ops\V18_PROJECT_CONTEXT_COMPACT.md` | TRUE | 2026-05-24T23:54:21 | 13.95 |

## Optional Files
| file | exists | modified | age_hours |
| --- | --- | --- | ---: |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_STORAGE_CLEANUP.md` | TRUE | 2026-05-25T00:50:54 | 13.01 |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_FREEZE_COVERAGE_REPAIR.md` | TRUE | 2026-05-24T23:54:13 | 13.95 |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md` | TRUE | 2026-05-24T18:28:41 | 19.38 |
| `D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md` | TRUE | 2026-05-24T18:28:38 | 19.38 |

## Extracted Fields
- candidate_count: `252`
- expected_candidate_count: `252`
- freeze_ticker_count: `252`
- freeze_coverage_status: `FULL_MATCH`
- latest_signal_date: `2026-05-22`
- allowed_trade_candidate_count: `0`
- account_state_quality: `WARN_TEMPLATE_EMPTY_ACCOUNT`
- `AUTO_TRADE`: `DISABLED`
- `AUTO_SELL`: `DISABLED`
- `OFFICIAL_DECISION_IMPACT`: `NONE`
- `FORBIDDEN_MODIFIED`: `FALSE`
- `DAILY_TRUST_LEVEL`: `LOW`
- `V18_33A_RUN_ID`: `V18_33A_20260525_135125`
- `V18_33B_RUN_ID`: `UNKNOWN`
- storage_repo_size_mb: `845.20`

## Consistency Check
- homepage vs context candidate/freeze: OK
- runbook vs homepage freshness: OK
- compact vs context consistency: OK
- daily readiness vs homepage/context: OK
- storage state: OK

## Warnings
- WARN: account state is template/manual
- WARN: allowed trade candidates are 0

## Notes
- This guard is audit-only and does not modify ledgers or trading logic.
- `WARN` is expected for template account state, zero allowed candidates, and medium daily trust level.
