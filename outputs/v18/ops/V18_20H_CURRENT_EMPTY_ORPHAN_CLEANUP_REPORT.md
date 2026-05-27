# V18.20H Empty Folder and Orphan Output Cleanup Report

- STATUS: OK_V18_20H_EMPTY_ORPHAN_CLEANUP_READY
- MODE: DRYRUN
- ROOT: D:\us-tech-quant
- ARCHIVE_ROOT: D:\us-tech-quant
- EMPTY_DIR_COUNT: 45
- EMPTY_DIR_DELETE_CANDIDATE_COUNT: 4
- EMPTY_DIR_PROTECTED_COUNT: 41
- EMPTY_DIR_REVIEW_REQUIRED_COUNT: 0
- ORPHAN_OUTPUT_COUNT: 602
- ORPHAN_OUTPUT_MB: 14.426
- VERIFIED_ARCHIVED_ORIGINAL_DELETE_CANDIDATE_COUNT: 268
- VERIFIED_ARCHIVED_ORIGINAL_DELETE_CANDIDATE_MB: 2.242
- PROTECTED_EXCLUSION_COUNT: 475
- PROTECTED_EXCLUSION_MB: 488.266
- DELETED_FILE_COUNT: 0
- DELETED_DIR_COUNT: 0
- MOVED_COUNT: 0
- ARCHIVED_COUNT: 0
- ZIP_CREATED_COUNT: 0
- VALIDATION_FAIL_COUNT: 0
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- CURRENT_DAILY_MODIFIED: FALSE
- STABLE_SNAPSHOT_MODIFIED: FALSE
- MANUAL_STATE_MODIFIED: FALSE
- PRICE_CACHE_MODIFIED: FALSE
- LATEST_STABLE_SNAPSHOT_NAME: V18_19A_R1_stable_daily_readability_refactor_20260519_171556

## Empty Directories By Category
- EMPTY_DIR_DELETE_CANDIDATE: 4
- EMPTY_DIR_PROTECTED: 41
- EMPTY_DIR_REVIEW_REQUIRED: 0

## Orphan Output Categories
- OLD_TIMESTAMPED_OUTPUT: 0 / 0.000 MB
- OLD_LOG: 0 / 0.000 MB
- OLD_DEPRECATED_ARCHIVE_OUTPUT: 108 / 4.575 MB
- OLD_V17_OUTPUT: 4 / 0.020 MB
- OLD_V18_SUPERSEDED_OUTPUT: 28 / 0.900 MB
- VERIFIED_ARCHIVED_ORIGINAL: 272 / 2.257 MB
- PROTECTED_CURRENT_ALIAS: 186 / 6.667 MB
- REVIEW_REQUIRED: 4 / 0.007 MB

## Recommendation

- Empty directory deletion looks worthwhile for leaf folders outside protected active paths.
- Later delete only verified OLD_GENERATED_REPORTS originals after a separate approval step.
- Keep source scripts and wrappers archive-only unless they are separately reviewed.

## Top 30 Largest Orphan Outputs
- outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_BACKTEST_HOLDINGS.csv | 2.404 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TOPN_BACKTEST_MATRIX.csv | 1.317 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v18/factor_validation/V18_2A_FACTOR_VALIDATION_DETAIL.csv | 0.606 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_validation/V18_2A_FACTOR_VALIDATION_DETAIL.csv | 0.606 MB | OLD_V18_SUPERSEDED_OUTPUT | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_BACKTEST_DAILY_RETURNS.csv | 0.209 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_backtest/V18_4H_R1_CURRENT_ROBUSTNESS_MATRIX.csv | 0.206 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260518_130936.bak | 0.112 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260518_131419.bak | 0.112 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv | 0.108 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_210713.bak | 0.097 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_212019.bak | 0.097 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_014422.bak | 0.074 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_014958.bak | 0.074 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_020200.bak | 0.074 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_220436.bak | 0.074 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_lab/V18_1B_FACTOR_VALUES_CURRENT.csv | 0.072 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v18/factor_lab/V18_1B_FACTOR_VALUES_CURRENT.csv | 0.071 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_research/V18_10B_R1_CURRENT_FORWARD_RETURN_PENDING_ROWS.csv | 0.063 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_audit/V18_4E_CURRENT_FACTOR_OUTPUT_FORWARD_AUDIT.csv | 0.062 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260519_105611.csv | 0.062 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw105_decision/v17_8A_raw105_full_decision_daily.csv | 0.060 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw105_decision/v17_8C_current_raw105_full_decision.csv | 0.060 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_213854.csv | 0.059 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_212518.csv | 0.057 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_audit/V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.csv | 0.056 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_audit/V18_4F_FORWARD_FACTOR_COVERAGE_20260519_105624.csv | 0.056 MB | OLD_V18_SUPERSEDED_OUTPUT | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_164754.csv | 0.054 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_131254.csv | 0.052 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION
- outputs/v18/factor_audit/V18_4D_CURRENT_FACTOR_PACK_AUDIT.csv | 0.050 MB | PROTECTED_CURRENT_ALIAS | KEEP_PROTECTED
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260519_105352.csv | 0.050 MB | VERIFIED_ARCHIVED_ORIGINAL | DELETE_AFTER_ARCHIVE_VERIFICATION

## Top 30 Verified Archived-Original Candidates
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v18/factor_validation/V18_2A_FACTOR_VALIDATION_DETAIL.csv | 0.606 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260519_105611.csv | 0.062 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw105_decision/v17_8A_raw105_full_decision_daily.csv | 0.060 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_213854.csv | 0.059 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_212518.csv | 0.057 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_164754.csv | 0.054 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_131254.csv | 0.052 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260519_105352.csv | 0.050 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_130825.csv | 0.050 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260518_213632.csv | 0.045 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v17/raw105_decision/v17_8A_raw105_full_decision_daily.csv | 0.043 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260518_212255.csv | 0.042 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260518_164556.csv | 0.038 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v16/universe/V16_FULL_UNIVERSE_SECOND_STAGE.csv | 0.034 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260518_131117.csv | 0.034 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260518_130616.csv | 0.031 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/technical_timing/V18_6A_TECHNICAL_TIMING_20260518_130842.csv | 0.031 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/technical_timing/V18_6A_TECHNICAL_TIMING_20260518_131309.csv | 0.031 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/technical_timing/V18_6A_TECHNICAL_TIMING_20260518_164814.csv | 0.031 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/technical_timing/V18_6A_TECHNICAL_TIMING_20260518_212536.csv | 0.031 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/technical_timing/V18_6A_TECHNICAL_TIMING_20260518_213915.csv | 0.031 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v18/technical_timing/V18_6A_TECHNICAL_TIMING_20260519_105633.csv | 0.030 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw105_decision/v17_8B_raw105_decision_readable_panel.csv | 0.028 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v17/raw105_decision/v17_8B_raw105_decision_readable_panel.csv | 0.027 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v16/universe/V16_SECOND_STAGE_WATCHLIST.csv | 0.026 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v17/raw_universe_audit/v17_7_raw_universe_full_screen_audit.csv | 0.026 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw_universe_audit/v17_7B_universe_semantic_audit.csv | 0.024 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- outputs/v17/raw_universe_audit/v17_7B_universe_semantic_audit.csv | 0.024 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v16/universe/V16_FULL_UNIVERSE_SCREENED.csv | 0.023 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.
- archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw_universe_audit/v17_7_raw_universe_full_screen_audit.csv | 0.021 MB | DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE | Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step.

- READ_FIRST: outputs/v18/ops/V18_20H_READ_FIRST.txt
- REPORT: outputs/v18/ops/V18_20H_CURRENT_EMPTY_ORPHAN_CLEANUP_REPORT.md
