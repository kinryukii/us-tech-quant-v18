# V18.20B Deep Cleanup Triage Report

- Mode: DRYRUN
- Review-required input count: 1984
- Review-required input MB: 93.47
- SAFE_TO_DELETE_LATER count: 267
- SAFE_TO_DELETE_LATER MB: 24.78
- ARCHIVE_THEN_DELETE_LATER count: 479
- ARCHIVE_THEN_DELETE_LATER MB: 7.07
- KEEP_PROTECTED count: 894
- KEEP_PROTECTED MB: 56.48
- NEEDS_HUMAN_REVIEW count: 344
- NEEDS_HUMAN_REVIEW MB: 5.14
- Estimated safe direct-delete MB: 24.78
- Estimated archive-then-delete MB: 7.07
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- DELETED_COUNT: 0
- MOVED_COUNT: 0
- ARCHIVED_COUNT: 0
- CURRENT_DAILY_MODIFIED: FALSE
- STABLE_SNAPSHOT_MODIFIED: FALSE
- MANUAL_STATE_MODIFIED: FALSE
- PRICE_CACHE_MODIFIED: FALSE
- VALIDATION_FAIL_COUNT: 0

## Category Summary

| triage_category | count | mb |
| --- | ---: | ---: |
| SAFE_TO_DELETE_LATER | 267 | 24.78 |
| ARCHIVE_THEN_DELETE_LATER | 479 | 7.07 |
| KEEP_PROTECTED | 894 | 56.48 |
| NEEDS_HUMAN_REVIEW | 344 | 5.14 |

## Top 30 SAFE_TO_DELETE_LATER

| path | size_mb | reason | ref_count | confidence |
| --- | ---: | --- | ---: | --- |
| data/v16/prices/NVDA.csv | 0.1892 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/NVDA.csv | 0.1892 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/TQQQ.csv | 0.1877 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/TQQQ.csv | 0.1877 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/HPE.csv | 0.1869 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/FLEX.csv | 0.1867 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/SOXL.csv | 0.1865 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/SOXL.csv | 0.1865 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/WDC.csv | 0.1859 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/AAPL.csv | 0.1857 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/AVGO.csv | 0.1853 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/AVGO.csv | 0.1852 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/SOXX.csv | 0.1852 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/SOXX.csv | 0.1852 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/GOOGL.csv | 0.1851 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/SMCI.csv | 0.1850 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/INTC.csv | 0.1847 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/XLK.csv | 0.1845 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/TSLA.csv | 0.1844 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/XLK.csv | 0.1844 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/AMZN.csv | 0.1843 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/CSCO.csv | 0.1843 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/LRCX.csv | 0.1842 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/TXN.csv | 0.1842 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/QQQ.csv | 0.1839 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/DELL.csv | 0.1839 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/QCOM.csv | 0.1839 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/QQQ.csv | 0.1839 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices/AMD.csv | 0.1838 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |
| data/v16/prices_full/AMD.csv | 0.1838 | Unreferenced generated clutter with low operational risk. | 0 | MEDIUM |

## Top 30 ARCHIVE_THEN_DELETE_LATER

| path | size_mb | reason | ref_count | confidence |
| --- | ---: | --- | ---: | --- |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v18/factor_validation/V18_2A_FACTOR_VALIDATION_DETAIL.csv | 0.6057 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260519_105611.csv | 0.0617 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/outputs/v17/raw105_decision/v17_8A_raw105_full_decision_daily.csv | 0.0599 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_213854.csv | 0.0591 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_212518.csv | 0.0568 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_164754.csv | 0.0543 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_131254.csv | 0.0519 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_130825.csv | 0.0501 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| outputs/v18/factor_audit/V18_4D_FACTOR_PACK_AUDIT_20260519_105352.csv | 0.0500 | Historical generated report contains operational tokens and should be archived first. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/HPE.csv | 0.0466 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/AMKR.csv | 0.0465 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/TXN.csv | 0.0464 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/AMAT.csv | 0.0463 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/NVDA.csv | 0.0463 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/QCOM.csv | 0.0463 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/TQQQ.csv | 0.0463 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/VRT.csv | 0.0463 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/VST.csv | 0.0463 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/AAPL.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/CRM.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/DELL.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/ECL.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/IRDM.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/MKSI.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/NXPI.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/SOXL.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/SOXX.csv | 0.0462 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/ENTG.csv | 0.0461 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/GLW.csv | 0.0461 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |
| archive/deprecated/v18_4K_workspace_cleanup_20260515_172036/data/prices/GOOGL.csv | 0.0461 | Versioned historical generated output is likely useful for debugging. | 0 | MEDIUM |

## Top 30 KEEP_PROTECTED

| path | size_mb | reason | ref_count | confidence |
| --- | ---: | --- | ---: | --- |
| outputs/v18/ops/V18_18A_CURRENT_STORAGE_AUDIT.csv | 3.0940 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_CURRENT_STORAGE_AUDIT.csv | 3.0940 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_CLEANUP_DELETE_PLAN_CURRENT.csv | 2.5786 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_CLEANUP_QUARANTINE_PLAN_CURRENT.csv | 2.5527 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_BACKTEST_HOLDINGS.csv | 2.4040 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_CLEANUP_AUDIT_CURRENT.csv | 1.4934 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_18A_CURRENT_KEEP_PROTECTED_FILES.csv | 1.4532 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TOPN_BACKTEST_MATRIX.csv | 1.3173 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_5A_R1_CURRENT_RUNTIME_DECOUPLING_PLAN.csv | 0.5053 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| outputs/v18/ops/V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv | 0.3906 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| state/v17_factor_effectiveness_tracking.csv | 0.3882 | State/config/cache/manual-related content must be retained. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/NVDA.csv | 0.2553 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/TSLA.csv | 0.2537 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AAPL.csv | 0.2535 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/GOOGL.csv | 0.2535 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AMZN.csv | 0.2534 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/SOXL.csv | 0.2534 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AVGO.csv | 0.2532 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/AMD.csv | 0.2530 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/HPE.csv | 0.2530 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/NOW.csv | 0.2530 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/FLEX.csv | 0.2529 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/INTC.csv | 0.2529 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/SMCI.csv | 0.2529 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/QCOM.csv | 0.2528 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/SOXX.csv | 0.2527 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/WDC.csv | 0.2527 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/CSCO.csv | 0.2526 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/LRCX.csv | 0.2526 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |
| archive/stable/V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357/state/v18/price_cache/MSFT.csv | 0.2524 | Active CURRENT alias or stable-line artifact. | 0 | HIGH |

## Top 30 NEEDS_HUMAN_REVIEW

| path | size_mb | reason | ref_count | confidence |
| --- | ---: | --- | ---: | --- |
| scripts/v18/__pycache__/v18_19A_daily_readability_refactor.cpython-314.pyc | 0.0753 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/__pycache__/run_v17_1_1_factor_effectiveness_tracker.cpython-314.pyc | 0.0596 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/v18_16C_scan_scoped_data_update.py | 0.0566 | Source code contains risky operational tokens and is unreferenced. | 0 | LOW |
| scripts/v18/__pycache__/v18_13B_ranked_candidate_read_center.cpython-314.pyc | 0.0515 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_16E_promotion_demotion_engine.cpython-314.pyc | 0.0449 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_20A_deep_legacy_cleanup_audit.cpython-314.pyc | 0.0432 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_10B_factor_effectiveness_backtest.cpython-314.pyc | 0.0425 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_13C_R1_stable_snapshot.cpython-314.pyc | 0.0403 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_12A_sell_timing_shadow_engine.cpython-314.pyc | 0.0395 | Operational filename is ambiguous. | 0 | LOW |
| scripts/v18/v18_15C_predevelopment_program_audit.py | 0.0391 | Source code contains risky operational tokens and is unreferenced. | 0 | LOW |
| scripts/v18/__pycache__/v18_13B_R1_stable_snapshot.cpython-314.pyc | 0.0388 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_13D_R1_stable_snapshot.cpython-314.pyc | 0.0384 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/v18_10A_factor_registry_coverage_audit.py | 0.0383 | Source code contains risky operational tokens and is unreferenced. | 0 | LOW |
| scripts/v18/__pycache__/v18_10C_weight_research_engine.cpython-314.pyc | 0.0380 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_10A_factor_registry_coverage_audit.cpython-314.pyc | 0.0376 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/run_v17_1_1_factor_effectiveness_tracker.py | 0.0374 | Source code contains risky operational tokens and is unreferenced. | 0 | LOW |
| scripts/v18/__pycache__/v18_16B_rolling_scan_scheduler.cpython-314.pyc | 0.0372 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/v18_13B_ranked_candidate_read_center.py | 0.0366 | Source code contains risky operational tokens and is unreferenced. | 0 | LOW |
| scripts/v18/__pycache__/v18_12C_position_lifecycle_review.cpython-314.pyc | 0.0362 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_12D_exit_signal_forward_validation.cpython-314.pyc | 0.0361 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_14D_ranked_candidate_forward_price_filler.cpython-314.pyc | 0.0360 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_14C_ranked_candidate_forward_tracker.cpython-314.pyc | 0.0354 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_10A_R2_factor_daily_capture_patch.cpython-314.pyc | 0.0346 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_14E_R1_stable_snapshot.cpython-314.pyc | 0.0344 | Unclear cleanup status requires human review. | 0 | LOW |
| src/qutumn/execution/__pycache__/execution_plan.cpython-314.pyc | 0.0344 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/v18_16A_universe_rolling_state_builder.py | 0.0332 | Source code contains risky operational tokens and is unreferenced. | 0 | LOW |
| scripts/v18/__pycache__/v18_4H_factor_rolling_backtest.cpython-314.pyc | 0.0329 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_14D_R1_stable_snapshot.cpython-314.pyc | 0.0326 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_11_calendar_vwap_rv_shadow_factors.cpython-314.pyc | 0.0325 | Unclear cleanup status requires human review. | 0 | LOW |
| scripts/v18/__pycache__/v18_12B_sell_timing_technical_label_integration.cpython-314.pyc | 0.0324 | Operational filename is ambiguous. | 0 | LOW |

## Validation

- MODE_DRYRUN: PASS
- TRIAGE_OUTPUTS_EXIST: PASS
- DELETED_COUNT_ZERO: PASS
- MOVED_COUNT_ZERO: PASS
- ARCHIVED_COUNT_ZERO: PASS
- CURRENT_DAILY_MODIFIED_FALSE: PASS
- STABLE_SNAPSHOT_MODIFIED_FALSE: PASS
- MANUAL_STATE_MODIFIED_FALSE: PASS
- PRICE_CACHE_MODIFIED_FALSE: PASS
- AUTO_TRADE_DISABLED: PASS
- AUTO_SELL_DISABLED: PASS
- OFFICIAL_DECISION_NONE: PASS
- TRIAGE_NONEMPTY: PASS

- READ_FIRST: outputs\v18\ops\V18_20B_READ_FIRST.txt
- TRIAGE_REPORT: outputs\v18\ops\V18_20B_CURRENT_DEEP_CLEANUP_TRIAGE_REPORT.md
- TRIAGE_CSV: outputs\v18\ops\V18_20B_CURRENT_REVIEW_REQUIRED_TRIAGE.csv
- SAFE_CSV: outputs\v18\ops\V18_20B_CURRENT_SAFE_DELETE_LATER.csv
- ARCHIVE_CSV: outputs\v18\ops\V18_20B_CURRENT_ARCHIVE_THEN_DELETE_LATER.csv
- KEEP_CSV: outputs\v18\ops\V18_20B_CURRENT_KEEP_PROTECTED_AFTER_TRIAGE.csv
- HUMAN_CSV: outputs\v18\ops\V18_20B_CURRENT_NEEDS_HUMAN_REVIEW.csv
