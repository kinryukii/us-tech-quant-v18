# V18.5B-R1 Validation-Aware Delete Audit

Generated: 2026-05-15 23:44:56

## 1. Status

- STATUS: OK_VALIDATION_AWARE_DELETE_AUDIT_READY
- INPUT: D:\us-tech-quant\outputs\v18\ops\V18_5B_CURRENT_DELETE_CANDIDATE_RUNTIME_AUDIT.csv
- RULE: full-chain validation overrides static zero-runtime graph.
- RESULT: current safe archive/delete candidate count should be zero.

## 2. Summary

| Metric | Value |
|---|---|
| TOTAL_UNIQUE_CANDIDATE_FILES | 12 |
| RUNTIME_OR_DYNAMIC_HIT_COUNT | 12 |
| PROTECTED_DYNAMIC_DEPENDENCY_COUNT | 1 |
| ZERO_RUNTIME_ARCHIVE_CANDIDATE_COUNT_AFTER_VALIDATION | 0 |
| DO_NOT_DELETE_COUNT | 12 |

## 3. Protected Dynamic Runtime Dependencies

| CandidateRel | ExistsNow | RuntimeHit | RuntimeHitMode | DeleteRecommendation | ArchiveRecommendation | Risk | ValidationNote |
|---|---|---|---|---|---|---|---|
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | True | YES_DYNAMIC_PROTECTED | FULL_CHAIN_VALIDATION | DO_NOT_DELETE_PROTECTED_DYNAMIC_RUNTIME_DEPENDENCY | NO_VALIDATION_FAILED_WHEN_ARCHIVED | HIGH | V18.5C archive caused V18.4J-R1 failure through upstream V17.7G-R1; restored and full chain passed. |

## 4. Remaining Archive Candidates

_none_

## 5. Do Not Delete

| CandidateRel | ExistsNow | RuntimeHit | RuntimeHitMode | DeleteRecommendation | ArchiveRecommendation | Risk |
|---|---|---|---|---|---|---|
| scripts\run_v16_11_full_universe_intake.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11b_second_stage_screen.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11c_full_candidate_review.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11d_full_candidate_event_workflow.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | True | YES_DYNAMIC_PROTECTED | FULL_CHAIN_VALIDATION | DO_NOT_DELETE_PROTECTED_DYNAMIC_RUNTIME_DEPENDENCY | NO_VALIDATION_FAILED_WHEN_ARCHIVED | HIGH |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_8A_raw105_full_decision_daily.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |

## 6. Full Result

| CandidateRel | ExistsNow | RuntimeHit | RuntimeHitMode | DeleteRecommendation | ArchiveRecommendation | Risk | ProtectedDynamic |
|---|---|---|---|---|---|---|---|
| scripts\run_v16_11_full_universe_intake.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v16_11b_second_stage_screen.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v16_11c_full_candidate_review.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v16_11d_full_candidate_event_workflow.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | True | YES_DYNAMIC_PROTECTED | FULL_CHAIN_VALIDATION | DO_NOT_DELETE_PROTECTED_DYNAMIC_RUNTIME_DEPENDENCY | NO_VALIDATION_FAILED_WHEN_ARCHIVED | HIGH | True |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |
| scripts\run_v17_8A_raw105_full_decision_daily.py | True | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH | False |

## 7. Next Action

No more archive/delete actions should be performed from this candidate set.
Next safe cleanup direction is generated-output retention, not runtime code deletion.


