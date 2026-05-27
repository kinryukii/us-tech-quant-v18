# V18.4C Runtime Dependency Audit

生成时间：2026-05-27 17:40:04

## 1. 结论

- ENTRY: `D:\us-tech-quant\scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1`
- UNIQUE_EXISTING_CODE_COUNT: `38`
- MISSING_REFERENCE_COUNT: `0`
- GRAPH_CSV: `D:\us-tech-quant\outputs\v18\ops\V18_4C_runtime_dependency_graph_20260527_174003.csv`

## 2. 按扩展名统计

| ext | count |
|---|---:|
| .ps1 | 27 |
| .py | 11 |

## 3. 参与运行的代码文件

- `D:\us-tech-quant\scripts\run_v16_daily_auto_update.ps1`
- `D:\us-tech-quant\scripts\run_v16_daily_full_universe.ps1`
- `D:\us-tech-quant\scripts\run_v17_6E_screened_universe_latest_price_audit.ps1`
- `D:\us-tech-quant\scripts\run_v17_6E_screened_universe_latest_price_audit.py`
- `D:\us-tech-quant\scripts\run_v17_6F_manual_daily_full_universe_latest_price.ps1`
- `D:\us-tech-quant\scripts\run_v17_6G_B_legacy_health_compat_preflight.ps1`
- `D:\us-tech-quant\scripts\run_v17_7_raw_universe_full_screen_audit.ps1`
- `D:\us-tech-quant\scripts\run_v17_7_raw_universe_full_screen_audit.py`
- `D:\us-tech-quant\scripts\run_v17_7B_universe_semantic_audit.ps1`
- `D:\us-tech-quant\scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1`
- `D:\us-tech-quant\scripts\run_v17_7D_main_compute_delta_audit.ps1`
- `D:\us-tech-quant\scripts\run_v17_7E_removed_main_compute_inspection.ps1`
- `D:\us-tech-quant\scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1`
- `D:\us-tech-quant\scripts\run_v17_7F_raw105_latest_price_refresh.ps1`
- `D:\us-tech-quant\scripts\run_v17_7F_raw105_latest_price_refresh.py`
- `D:\us-tech-quant\scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1`
- `D:\us-tech-quant\scripts\run_v17_8A_raw105_full_decision_daily.ps1`
- `D:\us-tech-quant\scripts\run_v17_8A_raw105_full_decision_daily.py`
- `D:\us-tech-quant\scripts\run_v17_8B_raw105_full_decision_readable_panel.ps1`
- `D:\us-tech-quant\scripts\run_v17_8C_raw105_clean_overwrite_daily.ps1`
- `D:\us-tech-quant\scripts\run_v17_8D_raw105_current_only_daily.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_1B_factor_value_compute.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_3D_R1_official_overlap_fix.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_3D_R2_factor_pack_current_only_daily.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_4A_factor_forward_outcome_tracker.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_4A_R1_daily_integrated_wrapper.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_4B_factor_outcome_summary_promotion_rules.ps1`
- `D:\us-tech-quant\scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1`
- `D:\us-tech-quant\scripts\v18\v18_3D_factor_pack_shadow_extension.py`
- `D:\us-tech-quant\scripts\v18\v18_3D_R1_official_overlap_fix.py`
- `D:\us-tech-quant\scripts\v18\v18_4A_factor_forward_outcome_tracker.py`
- `D:\us-tech-quant\scripts\v18\v18_4B_factor_outcome_summary_promotion_rules.py`
- `D:\us-tech-quant\src\v18\factor_lab\compute_v18_1B_factor_values.py`
- `D:\us-tech-quant\src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py`
- `D:\us-tech-quant\src\v18\factor_lab\run_v18_3B_R2_strict_fallback_compare.py`

## 5. 解释

这个统计是增强静态依赖扫描：会识别显式脚本路径、Join-Path 变量、-File $Variable、python $Variable、以及脚本变量值。动态拼接特别复杂时仍可能低估，但比第一版更接近真实运行链路。
