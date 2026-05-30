# V18.49B-R1 Simulation Policy Weight Engine

V18.49B-R1 reads V18.49A-R1 evidence and converts it into simulation-cabin policy settings only.

## Source V18.49A-R1 Evidence
| policy_id | evidence_quality | comparison_basis_status | recommendation_label | avg_return_5d |
| --- | --- | --- | --- | --- |
| BASELINE_TOP20 | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| FACTOR_HEAVY | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| TECHNICAL_HEAVY | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| PULLBACK_ENTRY | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| EVENT_FILTERED | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| OPTIONS_RISK_FILTERED | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| DEFENSIVE | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |
| AGGRESSIVE_TEST | INSUFFICIENT | INSUFFICIENT_MATCHED_EVIDENCE | INSUFFICIENT_EVIDENCE | UNKNOWN |

## Simulation Policy Decision
| simulation_policy_style | primary_policy_id | secondary_policy_id | policy_confidence | policy_reason |
| --- | --- | --- | --- | --- |
| SIM_EXIT_VALIDATION | NONE | NONE | LOW | OPTIONS_RISK_FILTERED_NOT_PROMOTED_LIMITED_HISTORY |

## Entry / Exit Aggressiveness
| entry_aggressiveness | exit_aggressiveness | max_paper_buy_count | max_paper_add_count | max_paper_reduce_count |
| --- | --- | --- | --- | --- |
| LIMITED | EXIT_VALIDATION_ONLY | 1 | 0 | 1 |

## Risk Filter Modes
| options_risk_filter_mode | event_risk_filter_mode | technical_exit_validation_mode | pullback_entry_mode |
| --- | --- | --- | --- |
| CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY | CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY | DISABLED | REFERENCE_ONLY |

## Simulation Only
This output is not real trade advice and creates no executable orders. It is only eligible for cautious simulation-cabin testing.

## Official Ranking And Weights
V18.49B-R1 does not change official ranking, factor weights, Top20 selection, buy/sell permissions, final_action, real positions, broker behavior, or order execution.

## Next Step
V18.49C Dual-Book Action Planner.

