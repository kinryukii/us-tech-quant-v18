# V18.5A Runtime Dependency Decoupling Audit

Generated at: 2026-05-15 18:48:03

## 1. Status

- V18_5A_STATUS: AUDIT_READY
- TOTAL_REFERENCE_COUNT: 1328
- FILES_HIT_COUNT: 45
- LEGACY_RUNTIME_REFERENCE_COUNT: 949
- LEGACY_RUNTIME_FILES_HIT_COUNT: 26
- CURRENT_OUTPUT_REFERENCE_COUNT: 13
- CSV: D:\us-tech-quant\outputs\v18\ops\V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv

## 2. Interpretation

This audit identifies old-looking paths that are still referenced by scripts or state files.
Anything listed under LEGACY_RUNTIME_DEPENDENCY_CANDIDATE must not be deleted before migration.

## 3. Legacy Runtime Dependency Files

- scripts\run_v17_7B_universe_semantic_audit.ps1 : 3 references
- scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 : 5 references
- scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 : 5 references
- scripts\run_v17_7D_main_compute_delta_audit.ps1 : 1 references
- scripts\run_v17_7E_removed_main_compute_inspection.ps1 : 1 references
- scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 : 1 references
- scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 : 1 references
- scripts\run_v17_8A_raw105_full_decision_daily.py : 1 references
- scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1 : 2 references
- scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 : 3 references
- scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1 : 2 references
- scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 : 7 references
- scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1 : 2 references
- scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 : 20 references
- scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 : 7 references
- scripts\v18\run_v18_5A_runtime_decoupling_audit.ps1 : 12 references
- scripts\v18\v18_3D_factor_pack_shadow_extension.py : 10 references
- scripts\v18\v18_3D_R1_official_overlap_fix.py : 9 references
- scripts\v18\v18_4A_factor_forward_outcome_tracker.py : 6 references
- src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py : 9 references
- src\v18\factor_lab\run_v18_3B_R2_strict_fallback_compare.py : 1 references
- src\v18\factor_lab\run_v18_3B_shadow_official_compare.py : 1 references
- state\v18\V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv : 210 references
- state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_155914.csv : 210 references
- state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_183413.csv : 210 references
- state\v18\V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_20260515_184107.csv : 210 references

## 4. Top References

| file | line | pattern | class | text |
|---|---:|---|---|---|
| scripts\run_v16_11_full_universe_intake.py | 494 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_FULL_UNIVERSE_RAW.csv`") |
| scripts\run_v16_11_full_universe_intake.py | 495 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_FULL_UNIVERSE_SCREENED.csv`") |
| scripts\run_v16_11_full_universe_intake.py | 496 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_FULL_UNIVERSE_SELECTED_FOR_EXECUTION.csv`") |
| scripts\run_v16_11_full_universe_intake.py | 497 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_FULL_UNIVERSE_TOP_REVIEW.csv`") |
| scripts\run_v16_11b_second_stage_screen.py | 272 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_FULL_UNIVERSE_SECOND_STAGE.csv`") |
| scripts\run_v16_11b_second_stage_screen.py | 273 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_SECOND_STAGE_TOP_CANDIDATES.csv`") |
| scripts\run_v16_11b_second_stage_screen.py | 274 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\universe\\V16_SECOND_STAGE_WATCHLIST.csv`") |
| scripts\run_v16_11c_full_candidate_review.py | 266 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\review\\V16_FULL_CANDIDATE_REVIEW.csv`") |
| scripts\run_v16_11c_full_candidate_review.py | 267 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\review\\V16_FULL_CANDIDATE_REVIEW.md`") |
| scripts\run_v16_11d_full_candidate_event_workflow.py | 233 | outputs\\v16 | UNKNOWN | lines.append("- `outputs\\v16\\review\\V16_FULL_CANDIDATE_REVIEW.md`") |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | 11 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $OutCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv" |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | 12 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SummaryMd = Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md" |
| scripts\run_v17_7B_universe_semantic_audit.ps1 | 13 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $ReadFirst = Join-Path $OutDir "V17_7B_READ_FIRST.txt" |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 15 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticAudit = Join-Path $Root "scripts\run_v17_7B_universe_semantic_audit.ps1" |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 86 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticExit = Run-Step -Name "V17_7B_UNIVERSE_SEMANTIC_AUDIT" -ScriptPath $SemanticAudit -Required $true |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 91 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticReadFirst = Join-Path $OutDir "V17_7B_READ_FIRST.txt" |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 93 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticSummary = Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md" |
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 94 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv" |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | 17 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticAudit = Join-Path $Root "scripts\run_v17_7B_universe_semantic_audit.ps1" |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | 152 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticExit = Run-NormalStep -Name "V17_7B_UNIVERSE_SEMANTIC_AUDIT" -ScriptPath $SemanticAudit |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | 158 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticReadFirst = Join-Path $OutDir "V17_7B_READ_FIRST.txt" |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | 308 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $Md.Add("- Universe semantic audit: " + (Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md")) |
| scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1 | 342 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $Rf += (Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md") |
| scripts\run_v17_7D_main_compute_delta_audit.ps1 | 12 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $CurrentSemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv" |
| scripts\run_v17_7E_removed_main_compute_inspection.ps1 | 13 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv" |
| scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1 | 13 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $SemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv" |
| scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1 | 25 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $Semantic = Join-Path $AuditDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md" |
| scripts\run_v17_8A_raw105_full_decision_daily.py | 17 | V17_7B | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | SEMANTIC_PATH = ROOT / "outputs" / "v17" / "raw_universe_audit" / "v17_7B_universe_semantic_audit.csv" |
| scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1 | 14 | V18_3A | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $Py3A = "$Root\src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py" |
| scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1 | 39 | V18_3A | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | "$Root\outputs\v18\factor_shadow\V18_3A_READ_FIRST.txt", |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | 17 | V18_3A | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $ShadowCsv = "$OutDir\V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv" |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | 77 | V18_3A | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | "$OutDir\V18_3A_READ_FIRST.txt", |
| scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1 | 131 | V18_3A | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $Py3A = "$Root\src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py" |
| scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1 | 5 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $PyScript = Join-Path $Root "scripts\v18\v18_3D_factor_pack_shadow_extension.py" |
| scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1 | 6 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $ReadFirst = Join-Path $Root "outputs\v18\factor_pack\V18_3D_READ_FIRST.txt" |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 9 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $ReadFirst = "$OutDir\V18_3D_READ_FIRST.txt" |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 11 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $OfficialLog = "$OpsDir\V18_3D_official_v17_8D_$Stamp.log" |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 12 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $ShadowLog = "$OpsDir\V18_3D_shadow_v18_$Stamp.log" |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 24 | V18_3A | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $ShadowCsv = "$Root\outputs\v18\factor_shadow\V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv" |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 98 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | "V18_3D_STATUS: OK_OFFICIAL_PLUS_SHADOW_DAILY_READY", |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 133 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | "powershell -NoProfile -ExecutionPolicy Bypass -File ""D:\us-tech-quant\scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1""", |
| scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1 | 142 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | Write-Host "V18_3D_STATUS: OK_OFFICIAL_PLUS_SHADOW_DAILY_READY" |
| scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1 | 5 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $UpstreamPs = Join-Path $Root "scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1" |
| scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1 | 6 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $FixPy = Join-Path $Root "scripts\v18\v18_3D_R1_official_overlap_fix.py" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 11 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $Upstream = Join-Path $ScriptDir "run_v18_3D_R1_official_overlap_fix.ps1" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 12 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $UpstreamLog = Join-Path $OpsDir "V18_3D_R2_upstream_R1_run.log" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 14 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1Read = Join-Path $OutDir "V18_3D_R1_READ_FIRST.txt" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 15 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1Top30 = Join-Path $OutDir "V18_3D_R1_FACTOR_PACK_TOP30.md" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 16 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1OverlapMd = Join-Path $OutDir "V18_3D_R1_FACTOR_PACK_OFFICIAL_OVERLAP.md" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 17 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1OverlapCsv = Join-Path $OutDir "V18_3D_R1_SHADOW_TOP30_OFFICIAL_OVERLAP.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 18 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1RankingCsv = Join-Path $OutDir "V18_3D_RAW105_FACTOR_PACK_RANKING.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 18 | V18_3D_RAW105_FACTOR_PACK_RANKING | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1RankingCsv = Join-Path $OutDir "V18_3D_RAW105_FACTOR_PACK_RANKING.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 19 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1ValuesCsv = Join-Path $OutDir "V18_3D_RAW105_FACTOR_PACK_VALUES.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 21 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R2Read = Join-Path $OutDir "V18_3D_R2_READ_FIRST.txt" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 22 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R2Top30 = Join-Path $OutDir "V18_3D_R2_CURRENT_FACTOR_PACK_TOP30.md" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 23 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R2OverlapMd = Join-Path $OutDir "V18_3D_R2_CURRENT_FACTOR_PACK_OFFICIAL_OVERLAP.md" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 24 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R2OverlapCsv = Join-Path $OutDir "V18_3D_R2_CURRENT_SHADOW_TOP30_OFFICIAL_OVERLAP.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 25 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R2RankingCsv = Join-Path $OutDir "V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_RANKING.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 26 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R2ValuesCsv = Join-Path $OutDir "V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_VALUES.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 31 | V18_CURRENT_RAW105_FACTOR_PACK_RANKING | UNKNOWN | $GlobalRankingCsv = Join-Path $OutDir "V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 75 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | Write-Host "V18_3D_R2_STATUS: FAIL_UPSTREAM_R1" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 82 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | Write-Host "V18_3D_R2_STATUS: FAIL_MISSING_R1_READ_FIRST" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 89 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $R1Status = Get-LineValue $R1Text "V18_3D_R1_STATUS" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 92 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | Write-Host "V18_3D_R2_STATUS: FAIL_R1_NOT_OK" |
| scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1 | 127 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | "V18_3D_R2_STATUS: OK_FACTOR_PACK_CURRENT_ONLY_READY", |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 73 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | (Join-Path $Root "scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1") |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 78 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $PackLog = Join-Path $OpsDir ("V18_3E_R2_step3_v18_3D_R2_factor_pack_" + $Stamp + ".log") |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 105 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | (Join-Path $Root "outputs\v18\factor_pack\V18_3D_R2_READ_FIRST.txt"), |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 124 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | $PackStatus = GetKey $PackText "V18_3D_R2_STATUS" |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 167 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | ("V18_3D_R2_STATUS: " + $PackStatus), |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 170 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | ("V18_3D_R2_OVERLAP_COUNT: " + $PackOverlapCount), |
| scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1 | 171 | V18_3D | LEGACY_RUNTIME_DEPENDENCY_CANDIDATE | ("V18_3D_R2_OVERLAP_NAMES: " + $PackOverlapNames), |
| scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1 | 89 | V18_CURRENT_FINAL_DAILY | CURRENT_OUTPUT_REFERENCE | $GlobalMd = Join-Path $OutDir "V18_CURRENT_FINAL_DAILY.md" |
| scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1 | 24 | V18_CURRENT_FINAL_DAILY | CURRENT_OUTPUT_REFERENCE | $CurrentFinal = Join-Path $OutDir "V18_CURRENT_FINAL_DAILY.md" |
| scripts\v18\run_v18_4G_R2_stable_snapshot.ps1 | 221 | V18_CURRENT_FINAL_DAILY | CURRENT_OUTPUT_REFERENCE | $ReadFiles += (Join-Path $Root "outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY.md") |
| scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1 | 22 | V18_CURRENT_FINAL_DAILY | CURRENT_OUTPUT_REFERENCE | $IntegratedCurrent = Join-Path $DailyOutDir "V18_CURRENT_FINAL_DAILY_PROMOTION_MERGE.md" |
| scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1 | 17 | V18_CURRENT_READ_FIRST | CURRENT_OUTPUT_REFERENCE | $CurrentReadFirst = Join-Path $ReadCenterDir "V18_CURRENT_READ_FIRST.md" |
| scripts\v18\run_v18_4J_R2_stable_snapshot.ps1 | 187 | V18_CURRENT_READ_FIRST | CURRENT_OUTPUT_REFERENCE | $ReadmeLines += "D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_READ_FIRST.md" |
| scripts\v18\run_v18_4J_read_center_cleanup.ps1 | 15 | V18_CURRENT_READ_FIRST | CURRENT_OUTPUT_REFERENCE | $CurrentReadFirst = Join-Path $ReadCenterDir "V18_CURRENT_READ_FIRST.md" |
| scripts\v18\run_v18_4J_read_center_cleanup.ps1 | 19 | V18_CURRENT_FINAL_DAILY | CURRENT_OUTPUT_REFERENCE | $FinalDailyPromotion = Join-Path $Root "outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY_PROMOTION_MERGE.md" |

## 5. Next Step

If legacy runtime references are found, the next step is V18.5B runtime input migration.
That step should copy required legacy runtime inputs into state\\runtime_inputs and patch readers to prefer canonical inputs.

Do not delete outputs\\v16, outputs\\v17, outputs\\v18\\factor_lab, factor_shadow, factor_validation, data\\prices, or data\\events until this audit shows zero runtime references.
