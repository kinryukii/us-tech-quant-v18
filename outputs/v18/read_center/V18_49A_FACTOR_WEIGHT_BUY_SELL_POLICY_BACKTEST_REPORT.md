# V18.49A Factor Weight Buy/Sell Policy Backtest

V18.49A is a read-only research sidecar that compares a small policy grid for simulation-cabin evidence.

## Safety Statement
No official ranking weights, buy/sell permissions, real positions, broker APIs, orders, or trading execution are changed.

## Source Availability
| source_name | found | usable | row_count | source_path |
| --- | --- | --- | --- | --- |
| current_top20 | TRUE | TRUE | 20 | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| ranked_candidates | TRUE | TRUE | 317 | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv |
| candidate_forward_tracker | TRUE | TRUE | 57 | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv |
| factor_forward_tracker | TRUE | TRUE | 525 | D:\us-tech-quant\state\v18\forward_outcome\V18_4A_FACTOR_FORWARD_TRACKER.csv |
| factor_pack | TRUE | TRUE | 317 | D:\us-tech-quant\outputs\v18\factor_pack\V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv |
| technical_timing | TRUE | TRUE | 317 | D:\us-tech-quant\outputs\v18\technical_timing\V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv |
| event_risk | TRUE | TRUE | 20 | D:\us-tech-quant\outputs\v18\event_risk\V18_47C_TOP20_EVENT_EARNINGS_RISK.csv |
| options_risk | TRUE | TRUE | 20 | D:\us-tech-quant\outputs\v18\options\V18_48B_TOP20_OPTIONS_RISK_RADAR.csv |
| priority_tracker | TRUE | TRUE | 20 | D:\us-tech-quant\outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv |
| factor_shadow_outcome | TRUE | TRUE | 1510 | D:\us-tech-quant\state\v18\factor_shadow_outcome_tracker.csv |

## Policy Grid
| policy_id | entry_rule | exit_rule | position_size_rule |
| --- | --- | --- | --- |
| BASELINE_TOP20 | Official Top20/current ranking order | FIXED_HOLD_20D_PLUS_RANK_DETERIORATION_IF_AVAILABLE | EQUAL_WEIGHT |
| FACTOR_HEAVY | Prefer factor_pack_score/factor_score | RANK_DETERIORATION_EXIT_PLUS_FIXED_HOLD_20D | EQUAL_WEIGHT |
| TECHNICAL_HEAVY | Prefer technical_timing_score/positive labels | TECHNICAL_DETERIORATION_EXIT_PLUS_FIXED_HOLD_10D | EQUAL_WEIGHT |
| PULLBACK_ENTRY | Prefer BB_BELOW_LOWER/BB_LOWER_HALF/pullback labels | OVERHEAT_EXIT_PLUS_FIXED_HOLD_20D | EQUAL_WEIGHT |
| EVENT_FILTERED | Penalize or skip HIGH/EXTREME/UNKNOWN event risk | EVENT_RISK_WORSEN_EXIT_PLUS_FIXED_HOLD_20D | SMALL_SIZE_ONLY |
| OPTIONS_RISK_FILTERED | Penalize or skip HIGH/EXTREME options risk | OPTIONS_RISK_WORSEN_EXIT_PLUS_FIXED_HOLD_20D | SMALL_SIZE_ONLY |
| DEFENSIVE | Fewer names with stricter event/options/technical filters | EARLY_DETERIORATION_EXIT_PLUS_FIXED_HOLD_10D | DEFENSIVE_HALF_SIZE |
| AGGRESSIVE_TEST | More names with looser filters | LATE_RISK_WORSEN_EXIT_PLUS_FIXED_HOLD_20D | AGGRESSIVE_TEST_SIZE |

## Performance Summary
| policy_id | selected_trade_count | completed_trade_count | avg_return_5d | avg_return_20d | evidence_quality | comparison_basis_status | recommendation_label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE_TOP20 | 121 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| FACTOR_HEAVY | 91 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| TECHNICAL_HEAVY | 91 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| PULLBACK_ENTRY | 0 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| EVENT_FILTERED | 0 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| OPTIONS_RISK_FILTERED | 0 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| DEFENSIVE | 0 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |
| AGGRESSIVE_TEST | 146 | 0 | UNKNOWN | UNKNOWN | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE |

## Best Policy / Simulation Style
| recommended_for_simulation | recommended_policy_id | recommended_sim_style | confidence_level | evidence_quality | reason |
| --- | --- | --- | --- | --- | --- |
| FALSE | NONE | SIM_EXIT_VALIDATION | LOW | INSUFFICIENT | Insufficient completed local forward-return evidence. |

## Evidence Limitations
Missing or limited sources: NONE. Forward returns use local cached forward tracker data when available; missing forward prices are not fabricated.

## Why Official Ranking Is Unchanged
The policy scores are local research attribution only. They are written to factor_backtest outputs and are not fed into official ranking, candidate scoring, buy permission, sell permission, final_action, broker, or order code.

## Next Step
V18.49B Simulation Policy Weight Engine.

