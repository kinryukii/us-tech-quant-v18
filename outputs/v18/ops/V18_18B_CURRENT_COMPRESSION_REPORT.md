# V18.18B Stable Snapshot Compression and Large Output Archive Audit

## Summary

- STATUS: OK_V18_18B_COMPRESSION_APPLIED
- MODE: APPLY
- APPLY: TRUE
- KEEP_LATEST_STABLE_SNAPSHOTS: 5
- DELETE_ORIGINAL_AFTER_VERIFIED_ZIP: FALSE
- ARCHIVE_LARGE_OUTPUTS: FALSE
- TOTAL_SIZE_MB_BEFORE: 1623.089
- ARCHIVE_STABLE_SIZE_MB: 848.028
- STABLE_SNAPSHOT_FOLDER_COUNT: 44
- STABLE_COMPRESSION_CANDIDATE_COUNT: 39
- STABLE_COMPRESSION_CANDIDATE_MB: 820.848
- ESTIMATED_STABLE_ZIP_SIZE_MB: 279.164
- ESTIMATED_STABLE_SAVINGS_MB: 541.684
- STABLE_ZIP_CREATED_COUNT: 39
- STABLE_ZIP_CREATED_MB: 279.164
- STABLE_ORIGINAL_DELETED_COUNT: 0
- STABLE_ORIGINAL_DELETED_MB: 0.000
- LARGE_OUTPUT_CANDIDATE_COUNT: 4
- LARGE_OUTPUT_CANDIDATE_MB: 529.905
- OUTPUT_ZIP_CREATED_COUNT: 0
- OUTPUT_ZIP_CREATED_MB: 0.000
- OUTPUT_ORIGINAL_DELETED_COUNT: 0
- OUTPUT_ORIGINAL_DELETED_MB: 0.000
- SOURCE_CODE_DELETED_COUNT: 0
- CURRENT_ALIAS_DELETED_COUNT: 0
- MANUAL_STATE_DELETED_COUNT: 0
- PRICE_CACHE_DELETED_COUNT: 0
- LATEST_STABLE_SNAPSHOT_PROTECTED: TRUE
- V18_16G_R1_PROTECTED: TRUE
- CURRENT_DAILY_MODIFIED: FALSE
- STABLE_SNAPSHOT_MODIFIED: FALSE
- VALIDATION_FAIL_COUNT: 0
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE

## Stable Snapshot Candidates

- V18_8E_R3_stable_current_official_daily_with_simulation_20260516_191846: 262.987 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_7D_R2_stable_fast_official_daily_with_technical_20260516_174922: 262.775 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_6F_R2_stable_official_daily_with_technical_20260516_025712: 257.072 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357: 25.556 MB, candidate=FALSE, action=KEEP_UNCOMPRESSED
- V18_4J_R2_stable_final_daily_read_center_20260515_164730: 8.380 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_10D_R2_stable_current_shadow_research_daily_20260517_020553: 5.836 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_10D_R1_stable_official_daily_with_factor_weight_research_20260517_015842: 5.599 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_10C_R2_stable_factor_weight_research_chain_20260517_012209: 5.026 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_10B_R3_stable_factor_research_chain_20260517_010140: 4.878 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_11F_R1_stable_shadow_factor_research_chain_20260518_000500: 3.882 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_3E_R4_stable_cockpit_after_legacy_cleanup_20260514_153532: 1.341 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V17_6H_stable_manual_run_full_universe_latest_price_20260512_165345: 0.549 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V17_6H_R2_stable_repair_health_compat_manual_daily_20260512_214624: 0.525 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_15B_R1_stable_current_daily_forward_tracker_manual_feedback_predev_audited_20260519_110537: 0.407 MB, candidate=FALSE, action=KEEP_UNCOMPRESSED
- V18_15B_R1_stable_current_daily_forward_tracker_manual_feedback_predev_audited_20260519_110402: 0.407 MB, candidate=FALSE, action=KEEP_UNCOMPRESSED
- V18_15B_R1_stable_current_daily_forward_tracker_manual_feedback_predev_audited_20260519_110803: 0.405 MB, candidate=FALSE, action=KEEP_UNCOMPRESSED
- V18_15B_R1_stable_current_daily_forward_tracker_manual_feedback_predev_audited_20260519_110651: 0.405 MB, candidate=FALSE, action=KEEP_UNCOMPRESSED
- V18_14D_R1_stable_ranked_candidate_forward_price_filler_20260518_233007: 0.176 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_14D_R1_stable_ranked_candidate_forward_price_filler_20260518_233032: 0.175 MB, candidate=TRUE, action=COMPRESS_TO_ZIP
- V18_14E_R1_stable_current_daily_with_forward_tracker_20260518_234221: 0.151 MB, candidate=TRUE, action=COMPRESS_TO_ZIP

## Large Output Candidates

- outputs/v18/technical_timing_backtest: 252.881 MB, protected=PROTECTED_CURRENT_ALIAS_PRESENT
- outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv: 166.158 MB, protected=PROTECTED_CURRENT_ALIAS
- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_DETAIL.csv: 85.358 MB, protected=PROTECTED_CURRENT_ALIAS
- outputs/v18/ops: 25.508 MB, protected=PROTECTED_CURRENT_ALIAS_PRESENT

## Safety Notes

- DRYRUN creates no zip files and deletes nothing.
- Stable snapshot originals are never deleted unless both -Apply and -DeleteOriginalAfterVerifiedZip are passed.
- Output originals are not deleted by this first V18.18B version.

## Apply Commands

- Compression only: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_18B_stable_snapshot_compression_audit.ps1" -Apply
- Compression with old stable original deletion after verified zip: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_18B_stable_snapshot_compression_audit.ps1" -Apply -DeleteOriginalAfterVerifiedZip

## Guardrails

AUTO_TRADE: DISABLED; AUTO_SELL: DISABLED; OFFICIAL_DECISION_IMPACT: NONE.
