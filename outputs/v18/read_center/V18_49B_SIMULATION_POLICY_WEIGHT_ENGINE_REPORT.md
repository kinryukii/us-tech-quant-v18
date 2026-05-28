# V18.49B-R1 Simulation Policy Weight Engine

V18.49B-R1 reads V18.49A-R1 evidence and converts it into simulation-cabin policy settings only.

## Source V18.49A-R1 Evidence
| policy_id | evidence_quality | comparison_basis_status | recommendation_label | avg_return_5d |
| --- | --- | --- | --- | --- |
| BASELINE_TOP20 | LOW | COMPARISON_BASIS_LIMITED | SIMULATION_CANDIDATE_BALANCED_LOW_EVIDENCE | 0.070176 |
| FACTOR_HEAVY | LOW | COMPARISON_BASIS_LIMITED | SIMULATION_CANDIDATE_BALANCED_LOW_EVIDENCE | 0.049191 |
| TECHNICAL_HEAVY | LOW | COMPARISON_BASIS_LIMITED | SIMULATION_CANDIDATE_BALANCED_LOW_EVIDENCE | 0.049191 |
| PULLBACK_ENTRY | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| EVENT_FILTERED | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| OPTIONS_RISK_FILTERED | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| DEFENSIVE | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| AGGRESSIVE_TEST | LOW | COMPARISON_BASIS_LIMITED | SIMULATION_CANDIDATE_BALANCED_LOW_EVIDENCE | 0.038750 |

## Simulation Policy Decision
| simulation_policy_style | primary_policy_id | secondary_policy_id | policy_confidence | policy_reason |
| --- | --- | --- | --- | --- |
| SIM_BALANCED | BASELINE_TOP20 | NONE | LOW | LOW_EVIDENCE_NOT_READY_FOR_POLICY_WEIGHTING;LOW_EVIDENCE_BASELINE_ONLY;COMPARISON_BASIS_LIMITED_NOT_READY_FOR_POLICY_WEIGHTING;OPTIONS_RISK_FILTERED_NOT_PROMOTED_LIMITED_HISTORY |

## Entry / Exit Aggressiveness
| entry_aggressiveness | exit_aggressiveness | max_paper_buy_count | max_paper_add_count | max_paper_reduce_count |
| --- | --- | --- | --- | --- |
| LIMITED_NORMAL | ACTIVE_REVIEW | 3 | 1 | 1 |

## Risk Filter Modes
| options_risk_filter_mode | event_risk_filter_mode | technical_exit_validation_mode | pullback_entry_mode |
| --- | --- | --- | --- |
| LIMITED_HISTORY_NOT_PROMOTED | CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY | DISABLED | REFERENCE_ONLY |

## Simulation Only
This output is not real trade advice and creates no executable orders. It is only eligible for cautious simulation-cabin testing.

## Official Ranking And Weights
V18.49B-R1 does not change official ranking, factor weights, Top20 selection, buy/sell permissions, final_action, real positions, broker behavior, or order execution.

## Next Step
V18.49C Dual-Book Action Planner.

