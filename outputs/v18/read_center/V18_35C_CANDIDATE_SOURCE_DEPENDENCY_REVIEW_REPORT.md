# V18.35C 候选池引用依赖角色审计与安全补丁

- STATUS: `WARN_V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_NEEDED`
- RUN_ID: `V18_35C_20260525_135127`
- GENERATED_AT: `2026-05-25T13:51:27`

## 为什么需要 V18.35C
`V18_CURRENT_RANKED_CANDIDATES.csv` 已被 V18.35B 修复为 full 252-row alias，但代码和报告中仍有旧引用。
本步骤逐行判断引用语义，把明确 full/top 的引用改到更明确的新文件名；不确定的脚本引用只报告，不强改。

## 当前候选源状态
- Current canonical alias rows: `318`
- Full candidate alias rows: `318`
- Top display alias rows: `20`

## Role Count
| role | count |
| --- | ---: |
| `UNKNOWN_SCRIPT_REFERENCE` | 56 |
| `DO_NOT_PATCH` | 11 |
| `TEXT_ONLY_REPORT_REFERENCE` | 10 |
| `FULL_SET_EXPECTED` | 1 |

## Patch Summary
- Apply requested: `FALSE`
- Patch recommended: `1`
- Patch applied: `0`
- Backup path: `NONE`

| file | line | role | replacement |
| --- | ---: | --- | --- |
| NONE |  |  |  |

## Remaining Unknown References Sample
| file | line | reason |
| --- | ---: | --- |
| `scripts/v18/v18_14C_R1_stable_snapshot.py` | 42 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_14C_R1_stable_snapshot.py` | 466 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_14C_ranked_candidate_forward_tracker.py` | 215 | script reference could not be confidently classified |
| `scripts/v18/v18_14C_ranked_candidate_forward_tracker.py` | 372 | script reference could not be confidently classified |
| `scripts/v18/v18_14C_ranked_candidate_forward_tracker.py` | 375 | script reference could not be confidently classified |
| `scripts/v18/v18_14D_R1_stable_snapshot.py` | 49 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_14D_R1_stable_snapshot.py` | 484 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_15A_manual_position_trade_feedback.py` | 287 | script reference could not be confidently classified |
| `scripts/v18/v18_15A_R1_stable_snapshot.py` | 44 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_15B_R1_stable_snapshot.py` | 49 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_15B_R1_stable_snapshot.py` | 442 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_15C_predevelopment_program_audit.py` | 43 | script reference could not be confidently classified |
| `scripts/v18/v18_15C_predevelopment_program_audit.py` | 440 | script reference could not be confidently classified |
| `scripts/v18/v18_15C_predevelopment_program_audit.py` | 579 | script reference could not be confidently classified |
| `scripts/v18/v18_15C_predevelopment_program_audit.py` | 729 | script reference could not be confidently classified |
| `scripts/v18/v18_16A_universe_rolling_state_builder.py` | 80 | script reference could not be confidently classified |
| `scripts/v18/v18_16A_universe_rolling_state_builder.py` | 498 | script reference could not be confidently classified |
| `scripts/v18/v18_16J_conservative_daily_threshold_patch.py` | 155 | script reference could not be confidently classified |
| `scripts/v18/v18_17A_ranking_factor_provenance_audit.py` | 243 | script reference could not be confidently classified |
| `scripts/v18/v18_19A_daily_readability_refactor.py` | 232 | script reference could not be confidently classified |
| `scripts/v18/v18_21A_R4_advisory_full_history_backfill_plan.py` | 149 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R21_daily_signal_freeze_forward_test_ledger.py` | 35 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R22_rolling_multi_run_continuation_scheduler.py` | 27 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R24_factor_technical_tier_refresh_readiness_audit.py` | 30 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R25F_safe_downstream_refresh_ranked_candidate_regeneration.py` | 28 | candidate generation/promotion context; not safe to patch automatically |
| `scripts/v18/v18_25A_R25G_promote_ranked_candidates_preview_to_current.py` | 29 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_25A_R26B_forward_return_filler_readiness_audit.py` | 21 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R27E_post_integration_downstream_readiness_audit.py` | 25 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R27F_build_staged_factor_technical_rows_tln_rddt.py` | 24 | script reference could not be confidently classified |
| `scripts/v18/v18_25A_R27G_validate_staged_factor_technical_merge_plan.py` | 27 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_25A_R27I_post_merge_candidate_readiness_audit.py` | 23 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_25A_R27J_ranked_candidates_preview_refresh_tln_rddt.py` | 26 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_25A_R27K_promote_ranked_candidates_preview_to_current.py` | 28 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_25A_R27K_promote_ranked_candidates_preview_to_current.py` | 326 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_25A_R27L_post_promotion_validation_signal_freeze_readiness.py` | 21 | historical/promotion/generation script context needs manual review |
| `scripts/v18/v18_28A_R1_theme_map_bootstrap_coverage_upgrade.py` | 18 | script reference could not be confidently classified |
| `scripts/v18/v18_28A_R2_remaining_unknown_theme_patch.py` | 19 | script reference could not be confidently classified |
| `scripts/v18/v18_28A_sector_theme_classification_audit.py` | 18 | script reference could not be confidently classified |
| `scripts/v18/v18_28B_recommendation_tier_action_layer.py` | 17 | script reference could not be confidently classified |
| `scripts/v18/v18_28C_recommendation_tier_calibration_audit.py` | 17 | script reference could not be confidently classified |
| `scripts/v18/v18_28D_recommendation_tier_rule_calibration_patch.py` | 26 | script reference could not be confidently classified |
| `scripts/v18/v18_29A_historical_backtest_readiness_audit.py` | 19 | script reference could not be confidently classified |
| `scripts/v18/v18_29B_limited_signal_freeze_backtest.py` | 23 | script reference could not be confidently classified |
| `scripts/v18/v18_29C_daily_recommendation_tier_snapshot_ledger.py` | 30 | script reference could not be confidently classified |
| `scripts/v18/v18_30B_daily_command_compatibility_guard.py` | 23 | script reference could not be confidently classified |
| `scripts/v18/v18_30C_operator_control_center_latest_freeze_patch.py` | 21 | script reference could not be confidently classified |
| `scripts/v18/v18_30D_same_day_signal_freeze_replace_policy.py` | 97 | script reference could not be confidently classified |
| `scripts/v18/v18_30E_safe_daily_operator_sequence.py` | 44 | script reference could not be confidently classified |
| `scripts/v18/v18_31A_static_buyability_gate.py` | 21 | script reference could not be confidently classified |
| `scripts/v18/v18_31B_manual_position_sizing_policy_layer.py` | 23 | script reference could not be confidently classified |
| `scripts/v18/v18_31C_moomoo_cost_slippage_constraint_layer.py` | 27 | script reference could not be confidently classified |
| `scripts/v18/v18_31D_account_aware_manual_trade_plan.py` | 25 | script reference could not be confidently classified |
| `scripts/v18/v18_31E_daily_trade_plan_snapshot_ledger.py` | 26 | script reference could not be confidently classified |
| `scripts/v18/v18_31G_R1_unsupported_signal_date_ledger_review_cleanup.py` | 30 | script reference could not be confidently classified |
| `scripts/v18/v18_31G_trading_day_signal_date_guard.py` | 41 | script reference could not be confidently classified |
| `scripts/v18/v18_32A_manual_account_state_validator.py` | 25 | script reference could not be confidently classified |

## Warnings
- WARN: audit-only mode used and safe patches are available but not applied
- WARN: unknown script references remain: 56

## Failures
- NONE

## Operator Next Action
- 对 `UNKNOWN_SCRIPT_REFERENCE` 保持人工复核，不要批量替换。
- 如果 command center 后续仍会重写 top display alias 到 canonical alias，应优先修复对应 read-center alias 生成语义。
- 日常 full candidate 消费优先使用 `V18_CURRENT_FULL_RANKED_CANDIDATES.csv`。
- 日常 top display 消费优先使用 `V18_CURRENT_TOP_RANKED_CANDIDATES.csv`。

## Final Conclusion
This is dependency source normalization only.
No ranking/factor/freeze/trading/account logic was changed.
`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.
