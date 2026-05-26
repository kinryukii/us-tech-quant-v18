# V18.38B Research Experiment Registry / Qlib-Style Experiment Tracking Layer

## 1. 今日结论
- STATUS: OK_V18_38B_RESEARCH_EXPERIMENT_REGISTRY_READY
- RUN_ID: V18_38B_RESEARCH_EXPERIMENT_REGISTRY_20260526_235406
- 结论: 实验总账已生成；当前主要状态是等待 forward outcome 成熟。
- TOTAL_EXPERIMENT_COUNT: 29
- ANY_FORWARD_OUTCOME_AVAILABLE: FALSE
- READY_FOR_FACTOR_FORWARD_ATTRIBUTION: FALSE
- READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE: FALSE

## 2. 实验总览
| total_experiment_count | paper_experiment_count | shadow_portfolio_experiment_count | motif_experiment_count | benchmark_experiment_count | pending_research_experiment_count | ready_experiment_count | partial_ready_experiment_count | pending_forward_outcome_count | missing_input_experiment_count | any_forward_outcome_available | ready_for_factor_forward_attribution | ready_for_shadow_portfolio_league_table | recommended_next_development_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 29 | 4 | 10 | 10 | 2 | 3 | 0 | 0 | 18 | 3 | FALSE | FALSE | FALSE | Wait for forward outcome maturity, then rerun V18.38A and V18.38B. |

## 3. Paper trading 实验
| experiment_id | experiment_type | entry_count | matured_horizon_count | readiness_status | downstream_recommended_next_step |
| --- | --- | --- | --- | --- | --- |
| PAPER_TOP20 | PAPER_TRADING | 20 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| PAPER_TOP50 | PAPER_TRADING | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| PAPER_TOP100 | PAPER_TRADING | 100 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| PAPER_FULL318 | PAPER_TRADING | 318 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |

## 4. Shadow portfolio 实验
| experiment_id | experiment_type | entry_count | matured_horizon_count | readiness_status | downstream_recommended_next_step |
| --- | --- | --- | --- | --- | --- |
| SHADOW_PORTFOLIO_TOP20_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 20 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP50_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP100_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 100 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_FULL318_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 318 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP20_SCORE_WEIGHTED | SHADOW_PORTFOLIO | 20 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP50_SCORE_WEIGHTED | SHADOW_PORTFOLIO | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP100_SCORE_WEIGHTED | SHADOW_PORTFOLIO | 100 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_LOW_VOL_ADJUSTED_TOP50 | SHADOW_PORTFOLIO | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_MOTIF_READY_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 18 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_MOTIF_READY_TOPN_BLEND | SHADOW_PORTFOLIO | 18 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |

## 5. LEAN-inspired motif 实验
| experiment_id | experiment_name | entry_count | current_forward_readiness | readiness_status | notes |
| --- | --- | --- | --- | --- | --- |
| LEAN_MOTIF_VALUE_MOMENTUM | 价值动量 | 10 | NOT_READY | MISSING_INPUT | evidence_status=MISSING_REQUIRED_FACTOR; research_readiness=NOT_READY |
| LEAN_MOTIF_QUALITY_MOMENTUM | 质量动量 | 10 | NOT_READY | MISSING_INPUT | evidence_status=MISSING_REQUIRED_FACTOR; research_readiness=NOT_READY |
| LEAN_MOTIF_LOW_VOL_MOMENTUM | 低波动动量 | 10 | PROXY_ONLY | REGISTERED_NOT_YET_MEASURABLE | evidence_status=PROXY_RESEARCH_ONLY; research_readiness=PROXY_ONLY |
| LEAN_MOTIF_BREAKOUT_CONTINUATION | 突破延续 | 10 | READY_FOR_PAPER_OBSERVATION | REGISTERED_NOT_YET_MEASURABLE | evidence_status=READY_REAL_EVIDENCE; research_readiness=READY_FOR_PAPER_OBSERVATION |
| LEAN_MOTIF_MEAN_REVERSION_CANDIDATE | 均值回归候选 | 10 | READY_FOR_PAPER_OBSERVATION | REGISTERED_NOT_YET_MEASURABLE | evidence_status=READY_REAL_EVIDENCE; research_readiness=READY_FOR_PAPER_OBSERVATION |
| LEAN_MOTIF_TECHNICAL_OVERHEAT_AVOIDANCE | 技术过热回避 | 10 | READY_FOR_PAPER_OBSERVATION | REGISTERED_NOT_YET_MEASURABLE | evidence_status=READY_REAL_EVIDENCE; research_readiness=READY_FOR_PAPER_OBSERVATION |
| LEAN_MOTIF_RISK_ADJUSTED_TOP_RANK | 风险调整高排名 | 10 | READY_FOR_PAPER_OBSERVATION | REGISTERED_NOT_YET_MEASURABLE | evidence_status=READY_REAL_EVIDENCE; research_readiness=READY_FOR_PAPER_OBSERVATION |
| LEAN_MOTIF_SECTOR_BALANCED_TOP_RANK | 行业均衡高排名 | 10 | NOT_READY | MISSING_INPUT | evidence_status=MISSING_REQUIRED_FACTOR; research_readiness=NOT_READY |
| LEAN_MOTIF_EQUAL_WEIGHT_TOP_N_BASELINE | 等权 Top N 基线 | 10 | READY_FOR_PAPER_OBSERVATION | REGISTERED_NOT_YET_MEASURABLE | evidence_status=READY_REAL_EVIDENCE; research_readiness=READY_FOR_PAPER_OBSERVATION |
| LEAN_MOTIF_SCORE_WEIGHTED_TOP_N_BASELINE | 分数加权 Top N 基线 | 10 | READY_FOR_PAPER_OBSERVATION | REGISTERED_NOT_YET_MEASURABLE | evidence_status=READY_REAL_EVIDENCE; research_readiness=READY_FOR_PAPER_OBSERVATION |

## 6. Benchmark 实验
| experiment_id | experiment_type | entry_count | matured_horizon_count | readiness_status | downstream_recommended_next_step |
| --- | --- | --- | --- | --- | --- |
| BENCHMARK_SPY | BENCHMARK | 1 | 0 | PENDING_FORWARD_OUTCOME | Use only as reference once benchmark forward returns are filled. |
| BENCHMARK_QQQ | BENCHMARK | 1 | 0 | PENDING_FORWARD_OUTCOME | Use only as reference once benchmark forward returns are filled. |

## 7. 当前 pending 的研究任务
| experiment_id | experiment_type | readiness_status | upstream_files | downstream_recommended_next_step |
| --- | --- | --- | --- | --- |
| FACTOR_FORWARD_ATTRIBUTION_PENDING | FACTOR_RESEARCH_PENDING | PENDING_FORWARD_OUTCOME | outputs/v18/ops/V18_38A_READ_FIRST.txt;outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv | Run factor attribution only after forward outcomes exist. |
| SHADOW_PORTFOLIO_LEAGUE_TABLE_PENDING | FACTOR_RESEARCH_PENDING | PENDING_FORWARD_OUTCOME | outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv;outputs/v18/ops/V18_38A_READ_FIRST.txt | Build league table only after shadow portfolio horizons mature. |
| TURNOVER_COST_SIMULATION_PENDING | COST_RESEARCH_PENDING | REGISTERED_NOT_YET_MEASURABLE | state/v18/paper_trading/V18_PAPER_TRADING_LEDGER.csv;state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv | Define cost model after enough forward snapshots and turnover events exist. |

## 8. 哪些实验已经可以比较
_无可用记录。_

## 9. 哪些实验还需要等待 forward outcome
| experiment_id | experiment_type | entry_count | matured_horizon_count | readiness_status | downstream_recommended_next_step |
| --- | --- | --- | --- | --- | --- |
| PAPER_TOP20 | PAPER_TRADING | 20 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| PAPER_TOP50 | PAPER_TRADING | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| PAPER_TOP100 | PAPER_TRADING | 100 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| PAPER_FULL318 | PAPER_TRADING | 318 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward returns to mature, then compare net return and benchmark excess return. |
| SHADOW_PORTFOLIO_TOP20_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 20 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP50_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP100_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 100 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_FULL318_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 318 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP20_SCORE_WEIGHTED | SHADOW_PORTFOLIO | 20 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP50_SCORE_WEIGHTED | SHADOW_PORTFOLIO | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_TOP100_SCORE_WEIGHTED | SHADOW_PORTFOLIO | 100 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_LOW_VOL_ADJUSTED_TOP50 | SHADOW_PORTFOLIO | 50 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_MOTIF_READY_EQUAL_WEIGHT | SHADOW_PORTFOLIO | 18 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| SHADOW_PORTFOLIO_MOTIF_READY_TOPN_BLEND | SHADOW_PORTFOLIO | 18 | 0 | PENDING_FORWARD_OUTCOME | Wait for forward outcomes before shadow portfolio league table. |
| BENCHMARK_SPY | BENCHMARK | 1 | 0 | PENDING_FORWARD_OUTCOME | Use only as reference once benchmark forward returns are filled. |
| BENCHMARK_QQQ | BENCHMARK | 1 | 0 | PENDING_FORWARD_OUTCOME | Use only as reference once benchmark forward returns are filled. |
| FACTOR_FORWARD_ATTRIBUTION_PENDING | FACTOR_RESEARCH_PENDING |  |  | PENDING_FORWARD_OUTCOME | Run factor attribution only after forward outcomes exist. |
| SHADOW_PORTFOLIO_LEAGUE_TABLE_PENDING | FACTOR_RESEARCH_PENDING |  |  | PENDING_FORWARD_OUTCOME | Build league table only after shadow portfolio horizons mature. |

## 10. 下一步建议
- Wait for forward outcome maturity, then rerun V18.38A and V18.38B.

## 11. Safety / no-impact confirmation
- MODE: READ_ONLY_RESEARCH_EXPERIMENT_REGISTRY
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE

### Dependency Snapshot
| dependency_name | exists | row_count | dependency_status | modified_time | notes |
| --- | --- | --- | --- | --- | --- |
| V18.38A READ_FIRST | TRUE |  | OK_USABLE | 2026-05-26T23:54:05 | usable dependency |
| V18.38A forward evidence summary | TRUE | 1 | OK_USABLE | 2026-05-26T23:54:05 | usable dependency |
| V18.38A forward evidence detail | TRUE | 31 | OK_USABLE | 2026-05-26T23:54:05 | usable dependency |
| V18.38A forward evidence readiness | TRUE | 5 | OK_USABLE | 2026-05-26T23:54:05 | usable dependency |
| V18.36A READ_FIRST | TRUE |  | OK_USABLE | 2026-05-26T16:51:40 | usable dependency |
| current paper trading forward attribution report | TRUE |  | OK_USABLE | 2026-05-26T16:51:40 | usable dependency |
| V18.37A LEAN motif summary | TRUE | 10 | OK_USABLE | 2026-05-26T17:12:09 | usable dependency |
| V18.37A strategy motif registry | TRUE | 10 | OK_USABLE | 2026-05-26T17:12:09 | usable dependency |
| V18.37B shadow portfolio registry | TRUE | 10 | OK_USABLE | 2026-05-26T17:12:10 | usable dependency |
| V18.37B shadow portfolio holdings | TRUE | 744 | OK_USABLE | 2026-05-26T17:12:10 | usable dependency |
| V18.37B shadow portfolio diagnostics | TRUE | 10 | OK_USABLE | 2026-05-26T17:12:10 | usable dependency |
| V18.37C shadow snapshot summary | TRUE | 1 | OK_USABLE | 2026-05-26T17:12:11 | usable dependency |
| V18.37C shadow forward readiness | TRUE | 6 | OK_USABLE | 2026-05-26T17:12:11 | usable dependency |
| current Full318 candidates | TRUE | 318 | OK_USABLE | 2026-05-25T18:48:08 | usable dependency |
| current top candidates | TRUE | 20 | OK_USABLE | 2026-05-26T23:54:03 | usable dependency |
| signal freeze ledger | TRUE | 570 | OK_USABLE | 2026-05-25T13:48:02 | usable dependency |
| paper trading ledger | TRUE | 488 | OK_USABLE | 2026-05-25T15:16:37 | usable dependency |
| paper positions | TRUE | 488 | OK_USABLE | 2026-05-25T15:16:37 | usable dependency |
| paper portfolio state | TRUE | 20 | OK_USABLE | 2026-05-25T15:16:37 | usable dependency |
| shadow portfolio snapshot ledger | TRUE | 744 | OK_USABLE | 2026-05-25T18:48:10 | usable dependency |
