# V18.5A-R2 Runtime Decoupling Classifier

Generated: 2026-05-15 19:08:07

## 1. Status

- STATUS: OK_SCHEMA_AWARE_CLASSIFIER_READY
- INPUT: D:\us-tech-quant\outputs\v18\ops\V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv
- TOTAL_ROWS_CLASSIFIED: 1328
- PURPOSE: classify runtime references using relative-path-aware source zones.

## 2. Action Summary

| Action | Count |
|---|---|
| IGNORE_STATE_DATA_REFERENCE | 1155 |
| MANUAL_REVIEW | 113 |
| IGNORE_SELF_AUDIT_DEFINITION | 32 |
| LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | 28 |

## 3. Family Summary

| Family | Count |
|---|---|
| V18_GENERATED_FACTOR_FORWARD_STATE | 1155 |
| OTHER | 113 |
| SELF_AUDIT_SCRIPT | 32 |
| V17_ROOT_SCRIPT | 18 |
| V16_ROOT_SCRIPT | 10 |

## 4. Source Zone Summary

| SourceZone | Count |
|---|---|
| STATE_FILE | 1155 |
| CURRENT_V18_CODE | 123 |
| CURRENT_QUTUMN_CODE | 22 |
| LEGACY_V17_ROOT_SCRIPT | 18 |
| LEGACY_V16_ROOT_SCRIPT | 10 |

## 5. Top Files

| SourceRel | Count |
|---|---|
| state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_155914.csv | 210 |
| state\v18\V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv | 210 |
| state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_184107.csv | 210 |
| state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_183413.csv | 210 |
| state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260514_225509.csv | 105 |
| state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_155119.csv | 105 |
| state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_143526.csv | 105 |
| scripts\v18\run_v18_5A_runtime_decoupling_audit.ps1 | 32 |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 21 |
| src\qutumn\cli\run_daily.py | 11 |
| src\qutumn\cli\run_stable_candidate.py | 10 |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | 10 |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | 9 |
| src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py | 9 |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 7 |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 7 |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | 7 |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 5 |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | 5 |
| scripts\run_v16_11_full_universe_intake.py | 4 |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | 3 |
| scripts\run_v16_11b_second_stage_screen.py | 3 |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | 3 |
| scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1 | 2 |
| scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1 | 2 |
| scripts\v18\run_v18_4J_read_center_cleanup.ps1 | 2 |
| scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1 | 2 |
| scripts\run_v16_11c_full_candidate_review.py | 2 |
| src\v18\factor_lab\run_v18_3B_shadow_official_compare.py | 1 |
| src\v18\factor_lab\run_v18_3B_R2_strict_fallback_compare.py | 1 |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | 1 |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | 1 |
| scripts\run_v16_11d_full_candidate_event_workflow.py | 1 |
| scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1 | 1 |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | 1 |
| scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1 | 1 |
| scripts\v18\run_v18_4J_R2_stable_snapshot.ps1 | 1 |
| scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1 | 1 |
| scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1 | 1 |
| scripts\v18\run_v18_4G_R2_stable_snapshot.ps1 | 1 |

## 6. Direct Legacy Script Dependencies

_none_

## 7. Output Or State Abstraction Dependencies

_none_

## 8. Old Wrapper Patch Candidates

_none_

## 9. Legacy Root Script Candidates After Runtime Audit

| SourceRel | SourceZone | Line | Family | Action | DeletePermission | ReferenceText |
|---|---|---|---|---|---|---|
| scripts\run_v16_11_full_universe_intake.py | LEGACY_V16_ROOT_SCRIPT | 494 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11_full_universe_intake.py | LEGACY_V16_ROOT_SCRIPT | 495 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11_full_universe_intake.py | LEGACY_V16_ROOT_SCRIPT | 496 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11_full_universe_intake.py | LEGACY_V16_ROOT_SCRIPT | 497 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11b_second_stage_screen.py | LEGACY_V16_ROOT_SCRIPT | 272 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11b_second_stage_screen.py | LEGACY_V16_ROOT_SCRIPT | 273 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11b_second_stage_screen.py | LEGACY_V16_ROOT_SCRIPT | 274 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11c_full_candidate_review.py | LEGACY_V16_ROOT_SCRIPT | 266 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11c_full_candidate_review.py | LEGACY_V16_ROOT_SCRIPT | 267 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v16_11d_full_candidate_event_workflow.py | LEGACY_V16_ROOT_SCRIPT | 233 | V16_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | outputs\\v16 |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 11 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 12 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 13 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 15 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 86 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 91 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 93 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 94 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 17 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 152 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 158 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 308 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 342 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | LEGACY_V17_ROOT_SCRIPT | 12 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | LEGACY_V17_ROOT_SCRIPT | 13 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | LEGACY_V17_ROOT_SCRIPT | 13 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 | LEGACY_V17_ROOT_SCRIPT | 25 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |
| scripts\run_v17_8A_raw105_full_decision_daily.py | LEGACY_V17_ROOT_SCRIPT | 17 | V17_ROOT_SCRIPT | LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT | MAYBE_AFTER_ZERO_RUNTIME_HIT | V17_7B |

## 10. Manual Review Samples

| SourceRel | SourceZone | Line | Family | Action | ReferenceText |
|---|---|---|---|---|---|
| scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1 | CURRENT_V18_CODE | 14 | OTHER | MANUAL_REVIEW | V18_3A |
| scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1 | CURRENT_V18_CODE | 39 | OTHER | MANUAL_REVIEW | V18_3A |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | CURRENT_V18_CODE | 17 | OTHER | MANUAL_REVIEW | V18_3A |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | CURRENT_V18_CODE | 77 | OTHER | MANUAL_REVIEW | V18_3A |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | CURRENT_V18_CODE | 131 | OTHER | MANUAL_REVIEW | V18_3A |
| scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1 | CURRENT_V18_CODE | 5 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1 | CURRENT_V18_CODE | 6 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 9 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 11 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 12 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 24 | OTHER | MANUAL_REVIEW | V18_3A |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 98 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 133 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | CURRENT_V18_CODE | 142 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1 | CURRENT_V18_CODE | 5 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1 | CURRENT_V18_CODE | 6 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 11 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 12 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 14 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 15 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 16 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 17 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 18 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 18 | OTHER | MANUAL_REVIEW | V18_3D_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 19 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 21 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 22 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 23 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 24 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 25 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 26 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 31 | OTHER | MANUAL_REVIEW | V18_CURRENT_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 75 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 82 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 89 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 92 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | CURRENT_V18_CODE | 127 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 73 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 78 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 105 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 124 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 167 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 170 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | CURRENT_V18_CODE | 171 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1 | CURRENT_V18_CODE | 89 | OTHER | MANUAL_REVIEW | V18_CURRENT_FINAL_DAILY |
| scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1 | CURRENT_V18_CODE | 24 | OTHER | MANUAL_REVIEW | V18_CURRENT_FINAL_DAILY |
| scripts\v18\run_v18_4G_R2_stable_snapshot.ps1 | CURRENT_V18_CODE | 221 | OTHER | MANUAL_REVIEW | V18_CURRENT_FINAL_DAILY |
| scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1 | CURRENT_V18_CODE | 22 | OTHER | MANUAL_REVIEW | V18_CURRENT_FINAL_DAILY |
| scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1 | CURRENT_V18_CODE | 17 | OTHER | MANUAL_REVIEW | V18_CURRENT_READ_FIRST |
| scripts\v18\run_v18_4J_R2_stable_snapshot.ps1 | CURRENT_V18_CODE | 187 | OTHER | MANUAL_REVIEW | V18_CURRENT_READ_FIRST |
| scripts\v18\run_v18_4J_read_center_cleanup.ps1 | CURRENT_V18_CODE | 15 | OTHER | MANUAL_REVIEW | V18_CURRENT_READ_FIRST |
| scripts\v18\run_v18_4J_read_center_cleanup.ps1 | CURRENT_V18_CODE | 19 | OTHER | MANUAL_REVIEW | V18_CURRENT_FINAL_DAILY |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 31 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 32 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 33 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 33 | OTHER | MANUAL_REVIEW | V18_3D_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 34 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 35 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 521 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 557 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 581 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_factor_pack_shadow_extension.py | CURRENT_V18_CODE | 632 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 88 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 88 | OTHER | MANUAL_REVIEW | V18_3D_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 412 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 413 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 414 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 415 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 467 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 499 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_3D_R1_official_overlap_fix.py | CURRENT_V18_CODE | 507 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 24 | OTHER | MANUAL_REVIEW | V18_CURRENT_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 25 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 26 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 26 | OTHER | MANUAL_REVIEW | V18_3D_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 31 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 32 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_4A_factor_forward_outcome_tracker.py | CURRENT_V18_CODE | 351 | OTHER | MANUAL_REVIEW | V18_3D |
| scripts\v18\v18_4H_factor_rolling_backtest.py | CURRENT_V18_CODE | 57 | OTHER | MANUAL_REVIEW | V18_CURRENT_RAW105_FACTOR_PACK_RANKING |
| scripts\v18\v18_4I_backtest_forward_promotion_merge.py | CURRENT_V18_CODE | 97 | OTHER | MANUAL_REVIEW | V18_CURRENT_FINAL_DAILY |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 266 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 267 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 268 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 269 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 270 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 271 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 272 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 273 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 274 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 275 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_daily.py | CURRENT_QUTUMN_CODE | 276 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_price_refresh.py | CURRENT_QUTUMN_CODE | 15 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 110 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 111 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 112 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 113 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 114 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 224 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 225 | OTHER | MANUAL_REVIEW | outputs\\v16 |
| src\qutumn\cli\run_stable_candidate.py | CURRENT_QUTUMN_CODE | 226 | OTHER | MANUAL_REVIEW | outputs\\v16 |

## 11. Next Action

If Direct Legacy Script Dependencies or Old Wrapper Patch Candidates are non-zero, patch those first.
If they are zero, proceed to V18.5B delete-candidate audit based on runtime graph, not raw text references.
State snapshot rows and generated output rows are ignored for code deletion decisions.


