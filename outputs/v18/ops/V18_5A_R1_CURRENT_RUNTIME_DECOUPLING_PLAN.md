# V18.5A-R1 Runtime Decoupling Plan

Generated: 2026-05-15 19:05:15

## 1. Status

- STATUS: OK_DECOUPLING_PLAN_READY
- INPUT: D:\us-tech-quant\outputs\v18\ops\V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv
- TOTAL_ROWS_CLASSIFIED: 1328
- PURPOSE: classify legacy runtime references before delete/archive/patch decisions.

## 2. Action Summary

| Action | Count |
|---|---|
| MANUAL_REVIEW | 1262 |
| TEXT_REFERENCE_REVIEW_LOW_PRIORITY | 66 |

## 3. Family Summary

| Family | Count |
|---|---|
| OTHER | 1262 |
| V16_TEXT_REFERENCE | 45 |
| V17_TEXT_REFERENCE | 21 |

## 4. Source Zone Summary

| SourceZone | Count |
|---|---|
| UNKNOWN | 1328 |

## 5. Top Files By Legacy Reference Count

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

## 6. High Priority: Direct Legacy Script Dependencies

These should be patched before any delete action.

_none_

## 7. Medium Priority: Output/State Abstraction Dependencies

These should move behind V18 current aliases or a single compatibility shim.

_none_

## 8. Wrapper Name Patch Candidates

_none_

## 9. Legacy Root Script Candidates

These are not approved for deletion yet. They become delete/archive candidates only after runtime graph says zero current dependency.

_none_

## 10. Protected Compatibility Bridges

Keep these unless upstream runtime is rewritten.

_none_

## 11. Next Action

Recommended next step:

1. Patch only V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY and PATCH_TO_CURRENT_V18_WRAPPER first.
2. Do not delete protected compatibility bridges.
3. Re-run V18.4J-R1 final daily read center wrapper.
4. Re-run V18.5A audit and this V18.5A-R1 plan.
5. Only then consider archive/delete candidates.


