# V18.5B Delete Candidate Runtime Graph Audit

Generated: 2026-05-15 19:15:26

## 1. Status

- STATUS: OK_DELETE_CANDIDATE_RUNTIME_AUDIT_READY
- CLASSIFIER_INPUT: D:\us-tech-quant\outputs\v18\ops\V18_5A_R2_CURRENT_RUNTIME_DECOUPLING_CLASSIFIER.csv
- RUNTIME_GRAPH_INPUT: D:\us-tech-quant\outputs\v18\ops\V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv
- RULE: archive only files with zero runtime graph hit; do not permanently delete here.

## 2. Summary

| Metric | Value |
|---|---|
| TOTAL_UNIQUE_CANDIDATE_FILES | 12 |
| RUNTIME_HIT_COUNT | 11 |
| ZERO_RUNTIME_HIT_ARCHIVE_CANDIDATE_COUNT | 1 |
| ALREADY_MISSING_OR_ARCHIVED_COUNT | 0 |

## 3. Archive Candidates With Zero Runtime Hit

| CandidateRel | ExistsNow | ClassifierHitCount | RuntimeHit | RuntimeHitMode | DeleteRecommendation | ArchiveRecommendation | Risk |
|---|---|---|---|---|---|---|---|
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | True | 5 | NO | NONE | ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT | YES_ARCHIVE_FIRST_NOT_PERMANENT_DELETE | MEDIUM |

## 4. Runtime Hits - Do Not Delete

| CandidateRel | ExistsNow | ClassifierHitCount | RuntimeHit | RuntimeHitMode | DeleteRecommendation | ArchiveRecommendation | Risk |
|---|---|---|---|---|---|---|---|
| scripts\run_v16_11_full_universe_intake.py | True | 4 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11b_second_stage_screen.py | True | 3 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11c_full_candidate_review.py | True | 2 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11d_full_candidate_event_workflow.py | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | True | 3 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | True | 5 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_8A_raw105_full_decision_daily.py | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |

## 5. Already Missing Or Archived

_none_

## 6. Full Result

| CandidateRel | ExistsNow | ClassifierHitCount | RuntimeHit | RuntimeHitMode | DeleteRecommendation | ArchiveRecommendation | Risk |
|---|---|---|---|---|---|---|---|
| scripts\run_v16_11_full_universe_intake.py | True | 4 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11b_second_stage_screen.py | True | 3 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11c_full_candidate_review.py | True | 2 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v16_11d_full_candidate_event_workflow.py | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | True | 3 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | True | 5 | NO | NONE | ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT | YES_ARCHIVE_FIRST_NOT_PERMANENT_DELETE | MEDIUM |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | True | 5 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |
| scripts\run_v17_8A_raw105_full_decision_daily.py | True | 1 | YES | CODE_SET | DO_NOT_DELETE_RUNTIME_HIT | NO | HIGH |

## 7. Next Action

If ZERO_RUNTIME_HIT_ARCHIVE_CANDIDATE_COUNT is greater than zero, next step is V18.5C archive-only move with restore manifest.
After archive-only move, run V18.4J-R1 final daily read center wrapper again.
Only after a successful full-chain validation should permanent deletion be considered.


