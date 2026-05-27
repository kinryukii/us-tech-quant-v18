# V18.35B 当前候选池文件口径规范化

- STATUS: `WARN_V18_35B_CANDIDATE_SOURCE_NORMALIZATION_REVIEW_NEEDED`
- RUN_ID: `V18_35B_20260527_125904`
- GENERATED_AT: `2026-05-27T12:59:04`

## 为什么 V18.35A 出现 WARN
V18.35A 发现 `V18_CURRENT_RANKED_CANDIDATES.csv` 的行数与 current context / latest freeze 的 252 口径不一致。
这个任务把 full current candidates、top display candidates 和 legacy/current alias 状态拆开，避免后续脚本误读。

## 当前口径
- 修复前 `V18_CURRENT_RANKED_CANDIDATES.csv`: `318`
- 修复后 `V18_CURRENT_RANKED_CANDIDATES.csv`: `318`
- Full current candidates: `318`
- Top display candidates: `20`
- Latest signal freeze: `318`
- Full candidate matches freeze: `TRUE`
- Top is subset of full: `TRUE`

## 是否执行 canonical alias repair
- Apply requested: `FALSE`
- Canonical alias repaired: `FALSE`
- Backup path: `NONE`

## Source Map
| source | rows | unique_tickers | matches_latest_freeze | role | selected_full | selected_top |
| --- | ---: | ---: | --- | --- | --- | --- |
| `outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv` | 318 | 318 | TRUE | `FULL_CURRENT_CANDIDATE_SOURCE` | TRUE | FALSE |
| `outputs/v18/candidates/V18_RESTORED_RANKED_CANDIDATES_FROM_R29C_SNAPSHOT.csv` | 252 | 252 | FALSE | `OTHER_CANDIDATE_EVIDENCE` | FALSE | FALSE |
| `outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv` | 318 | 318 | TRUE | `FREEZE_MATCHED_CANDIDATE_EVIDENCE` | FALSE | FALSE |
| `outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv` | 20 | 20 | FALSE | `TOP_DISPLAY_CANDIDATE_SOURCE` | FALSE | TRUE |
| `outputs/v18/candidates/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW.csv` | 252 | 252 | FALSE | `OTHER_CANDIDATE_EVIDENCE` | FALSE | FALSE |
| `outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv` | 250 | 250 | FALSE | `OTHER_CANDIDATE_EVIDENCE` | FALSE | FALSE |
| `outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv` | 252 | 252 | FALSE | `FACTOR_PACK_EVIDENCE` | FALSE | FALSE |
| `outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv` | 252 | 252 | FALSE | `TECHNICAL_TIMING_EVIDENCE` | FALSE | FALSE |

## Dependency Scan
- Reference count: `63`
- Ambiguous reference count: `36`

| file | role guess | notes |
| --- | --- | --- |
| `scripts/v18/v18_14C_R1_stable_snapshot.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_14C_ranked_candidate_forward_tracker.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_14D_R1_stable_snapshot.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_15A_manual_position_trade_feedback.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_15A_R1_stable_snapshot.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_15B_R1_stable_snapshot.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_15C_predevelopment_program_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_16A_universe_rolling_state_builder.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_16J_conservative_daily_threshold_patch.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_17A_ranking_factor_provenance_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_19A_daily_readability_refactor.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_21A_R4_advisory_full_history_backfill_plan.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R21_daily_signal_freeze_forward_test_ledger.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R22_rolling_multi_run_continuation_scheduler.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R24_factor_technical_tier_refresh_readiness_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R25F_safe_downstream_refresh_ranked_candidate_regeneration.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R25G_promote_ranked_candidates_preview_to_current.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R26B_forward_return_filler_readiness_audit.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_25A_R27E_post_integration_downstream_readiness_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R27F_build_staged_factor_technical_rows_tln_rddt.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R27G_validate_staged_factor_technical_merge_plan.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R27I_post_merge_candidate_readiness_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R27J_ranked_candidates_preview_refresh_tln_rddt.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R27K_promote_ranked_candidates_preview_to_current.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_25A_R27L_post_promotion_validation_signal_freeze_readiness.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_28A_R1_theme_map_bootstrap_coverage_upgrade.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_28A_R2_remaining_unknown_theme_patch.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_28A_sector_theme_classification_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_28B_recommendation_tier_action_layer.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_28C_recommendation_tier_calibration_audit.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_28D_recommendation_tier_rule_calibration_patch.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_29A_historical_backtest_readiness_audit.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_29B_limited_signal_freeze_backtest.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_29C_daily_recommendation_tier_snapshot_ledger.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_30B_daily_command_compatibility_guard.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_30C_operator_control_center_latest_freeze_patch.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_30D_same_day_signal_freeze_replace_policy.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_30E_safe_daily_operator_sequence.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_31A_static_buyability_gate.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_31B_manual_position_sizing_policy_layer.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_31C_moomoo_cost_slippage_constraint_layer.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_31D_account_aware_manual_trade_plan.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_31E_daily_trade_plan_snapshot_ledger.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_31G_R1_unsupported_signal_date_ledger_review_cleanup.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_31G_trading_day_signal_date_guard.py` | `FULL_SET_EXPECTED` | Context contains full/freeze/candidate-count language. |
| `scripts/v18/v18_32A_manual_account_state_validator.py` | `UNKNOWN_SCRIPT_REFERENCE` | Script reference needs manual review before patching. |
| `scripts/v18/v18_35B_current_candidate_source_normalization.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_35C_candidate_source_dependency_role_review.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_35D_full_universe_factor_technical_recompute.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_35F_next_signal_freeze_expansion.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_35G_universe_invalid_ticker_prune.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_35H_stable_snapshot_318_aligned_baseline.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_36A_paper_trading_forward_attribution.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_36C_factor_implementation_audit.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_36C_R1_strict_evidence_classification_patch.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_37A_lean_inspired_strategy_motif_lab.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_37B_shadow_portfolio_construction_comparison.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `scripts/v18/v18_37D_stable_snapshot_research_stack_baseline.py` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `outputs/v18/read_center/V18_35B_CANDIDATE_SOURCE_NORMALIZATION_REPORT.md` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `outputs/v18/read_center/V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_REPORT.md` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `outputs/v18/read_center/V18_CURRENT_CANDIDATE_SOURCE_DEPENDENCY_REVIEW.md` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |
| `outputs/v18/read_center/V18_CURRENT_CANDIDATE_SOURCE_NORMALIZATION.md` | `TOP_DISPLAY_EXPECTED` | Context contains display/top/second-stage language. |

## Warnings
- WARN: dependency scan found ambiguous references: 36

## Fail Reasons
- NONE

## Operator Next Action
- 日常读完整候选池时优先使用 `outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv`。
- 日常展示 top candidates 时使用 `outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv`。
- 只有在确认需要恢复 canonical alias 为 full set 时，才运行 `-ApplyCanonicalAliasRepair`。
- 若 command center 重新生成 20 行 alias，可再次运行 apply repair，或后续单独修复生成链路的 alias 语义。

## Final Conclusion
This is candidate source normalization only.
No ranking/factor/freeze/trading/account logic was changed.
`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.
