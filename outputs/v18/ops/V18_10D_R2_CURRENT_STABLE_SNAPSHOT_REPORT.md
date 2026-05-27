# V18.10D-R2 Stable Snapshot

Generated: `2026-05-17 02:05:55`

## 1. Status

- STATUS: `OK_STABLE_SNAPSHOT_READY`
- MODE: `STABLE_RESTORE_POINT_FOR_CURRENT_SHADOW_RESEARCH_DAILY_ENTRY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- AUTO_WEIGHT_CHANGE: `DISABLED`
- AUTO_PROMOTION: `DISABLED`
- AUTO_TRADE: `DISABLED`

## 2. Snapshot

- SNAPSHOT: `D:\us-tech-quant\archive\stable\V18_10D_R2_stable_current_shadow_research_daily_20260517_020553`
- COPIED_FILE_COUNT: `665`
- MISSING_LAYER_COUNT: `0`
- COPY_FAIL_COUNT: `0`
- MISSING_CRITICAL_COUNT: `0`
- PARSE_FAIL_COUNT: `0`
- PY_COMPILE_FAIL_COUNT: `0`

## 3. Critical validation

| type | rel_path | status |
|---|---|---|
| ps1_parse | scripts/v18/run_v18_current_official_daily.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_current_shadow_research_daily.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_9C_official_daily_with_sim_validation.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10D_official_daily_with_factor_weight_research.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10C_R1_factor_weight_research_daily_chain.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10C_weight_research_engine.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10A_R2_factor_daily_capture_patch.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10A_factor_registry_coverage_audit.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10B_factor_effectiveness_backtest.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_10B_R1_forward_return_maturity_monitor.ps1 | OK_PARSE |
| ps1_parse | scripts/v18/run_v18_9B_forward_return_filler.ps1 | OK_PARSE |
| py_compile | scripts/v18/v18_10D_R2_stable_snapshot.py | OK_PY_COMPILE |
| py_compile | scripts/v18/v18_10C_weight_research_engine.py | OK_PY_COMPILE |
| py_compile | scripts/v18/v18_10A_R2_factor_daily_capture_patch.py | OK_PY_COMPILE |
| py_compile | scripts/v18/v18_10A_factor_registry_coverage_audit.py | OK_PY_COMPILE |
| py_compile | scripts/v18/v18_10B_factor_effectiveness_backtest.py | OK_PY_COMPILE |
| py_compile | scripts/v18/v18_10B_R1_forward_return_maturity_monitor.py | OK_PY_COMPILE |
| py_compile | scripts/v18/v18_9B_forward_return_filler.py | OK_PY_COMPILE |

## 4. Outputs

- README: `D:\us-tech-quant\archive\stable\V18_10D_R2_stable_current_shadow_research_daily_20260517_020553\V18_10D_R2_STABLE_SNAPSHOT_README.txt`
- MANIFEST: `D:\us-tech-quant\archive\stable\V18_10D_R2_stable_current_shadow_research_daily_20260517_020553\V18_10D_R2_STABLE_MANIFEST.csv`
- VALIDATION_CHECKS: `D:\us-tech-quant\archive\stable\V18_10D_R2_stable_current_shadow_research_daily_20260517_020553\V18_10D_R2_STABLE_VALIDATION_CHECKS.csv`
- RESTORE_SCRIPT: `D:\us-tech-quant\archive\stable\V18_10D_R2_stable_current_shadow_research_daily_20260517_020553\restore_v18_10D_R2_stable_snapshot.ps1`
- COMBINED_READ_FIRST: `D:\us-tech-quant\archive\stable\V18_10D_R2_stable_current_shadow_research_daily_20260517_020553\V18_10D_R2_COMBINED_READ_FIRST_CAPTURE.txt`
- REPORT: `D:\us-tech-quant\outputs\v18\ops\V18_10D_R2_CURRENT_STABLE_SNAPSHOT_REPORT.md`
- READ_FIRST: `D:\us-tech-quant\outputs\v18\ops\V18_10D_R2_READ_FIRST.txt`
