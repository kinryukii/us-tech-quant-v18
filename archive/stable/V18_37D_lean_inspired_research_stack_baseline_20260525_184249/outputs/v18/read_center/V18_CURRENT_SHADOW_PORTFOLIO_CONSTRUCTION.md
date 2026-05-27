# V18.37B Shadow Portfolio Construction Comparison

生成时间：2026-05-25T18:28:59

本报告是受 LEAN/QuantConnect 组合构建思想启发的研究层，用当前 V18 候选排名和 V18.37A strategy motif 影子候选构造透明的影子组合。这里没有复制 LEAN 策略代码，也没有 broker、API、订单、账户或执行逻辑。

明确边界：官方排名、因子权重、候选冻结、纸交易账本、账户状态和交易决策均未改变。本层只服务研究比较和未来纸交易归因观察。

## 安全状态

- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- FORBIDDEN_MODIFIED: FALSE

## 总览

| 指标 | 数值 |
| --- | --- |
| 组合数量 | 10 |
| Ready 组合数量 | 10 |
| 警告数量 | 0 |
| 候选宇宙数量 | 318 |
| 持仓行数 | 744 |

## 组合说明

等权组合让每只股票权重相同，便于作为最朴素的基线。分数加权组合优先使用 composite_candidate_score，缺失时回退等权并标记 fallback。低波动调整组合只在存在 volatility_penalty、overheat_penalty 或技术风险代理时生成。Motif blend 只使用 V18.37A 中 READY/READY_REAL_EVIDENCE 的 motif，代理和缺失因子 motif 只进入诊断排除计数。

| Portfolio | 中文名 | 方法 | 状态 | 持仓数 | 备注 |
| --- | --- | --- | --- | --- | --- |
| TOP20_EQUAL_WEIGHT | Top20 等权篮子 | TOP_N_EQUAL_WEIGHT | READY | 20 | 当前排名前 20 的等权研究篮子。 |
| TOP50_EQUAL_WEIGHT | Top50 等权篮子 | TOP_N_EQUAL_WEIGHT | READY | 50 | 当前排名前 50 的等权研究篮子。 |
| TOP100_EQUAL_WEIGHT | Top100 等权篮子 | TOP_N_EQUAL_WEIGHT | READY | 100 | 当前排名前 100 的等权研究篮子。 |
| FULL318_EQUAL_WEIGHT | 全当前候选等权篮子 | FULL_CURRENT_EQUAL_WEIGHT | READY | 318 | 当前可用完整候选宇宙的等权研究篮子。 |
| TOP20_SCORE_WEIGHTED | Top20 分数加权篮子 | TOP_N_SCORE_WEIGHTED | READY | 20 | 优先使用 composite_candidate_score 的分数加权研究篮子。 |
| TOP50_SCORE_WEIGHTED | Top50 分数加权篮子 | TOP_N_SCORE_WEIGHTED | READY | 50 | 优先使用 composite_candidate_score 的分数加权研究篮子。 |
| TOP100_SCORE_WEIGHTED | Top100 分数加权篮子 | TOP_N_SCORE_WEIGHTED | READY | 100 | 优先使用 composite_candidate_score 的分数加权研究篮子。 |
| LOW_VOL_ADJUSTED_TOP50 | 低波动调整 Top50 | LOW_VOL_ADJUSTED_TOP_N | READY | 50 | 仅在存在可用波动或风险代理字段时生成权重。 |
| MOTIF_READY_EQUAL_WEIGHT | Ready Motif 等权篮子 | READY_MOTIF_EQUAL_WEIGHT | READY | 18 | 只使用 V18.37A 标记为 READY/READY_REAL_EVIDENCE 的 motif 候选。 |
| MOTIF_READY_TOPN_BLEND | Ready Motif TopN 混合篮子 | READY_MOTIF_TOPN_BLEND | READY | 18 | 每个 ready motif 先等权，再聚合到股票层面。 |

## Ready 组合 Top Holdings

### TOP20_EQUAL_WEIGHT
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.05 | 1 |  |
| AEIS | 0.05 | 2 |  |
| AGX | 0.05 | 3 |  |
| BLTE | 0.05 | 4 |  |
| LITE | 0.05 | 5 |  |
| ALM | 0.05 | 6 |  |
| POWL | 0.05 | 7 |  |
| MTZ | 0.05 | 8 |  |

### TOP50_EQUAL_WEIGHT
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.02 | 1 |  |
| AEIS | 0.02 | 2 |  |
| AGX | 0.02 | 3 |  |
| BLTE | 0.02 | 4 |  |
| LITE | 0.02 | 5 |  |
| ALM | 0.02 | 6 |  |
| POWL | 0.02 | 7 |  |
| MTZ | 0.02 | 8 |  |

### TOP100_EQUAL_WEIGHT
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.01 | 1 |  |
| AEIS | 0.01 | 2 |  |
| AGX | 0.01 | 3 |  |
| BLTE | 0.01 | 4 |  |
| LITE | 0.01 | 5 |  |
| ALM | 0.01 | 6 |  |
| POWL | 0.01 | 7 |  |
| MTZ | 0.01 | 8 |  |

### FULL318_EQUAL_WEIGHT
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.0031446541 | 1 |  |
| AEIS | 0.0031446541 | 2 |  |
| AGX | 0.0031446541 | 3 |  |
| BLTE | 0.0031446541 | 4 |  |
| LITE | 0.0031446541 | 5 |  |
| ALM | 0.0031446541 | 6 |  |
| POWL | 0.0031446541 | 7 |  |
| MTZ | 0.0031446541 | 8 |  |

### TOP20_SCORE_WEIGHTED
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.0540729856 | 1 |  |
| AEIS | 0.0537624313 | 2 |  |
| AGX | 0.0524288745 | 3 |  |
| BLTE | 0.0523594565 | 4 |  |
| LITE | 0.0520817844 | 5 |  |
| ALM | 0.0519648699 | 6 |  |
| POWL | 0.0517346943 | 7 |  |
| MTZ | 0.0517273871 | 8 |  |

### TOP50_SCORE_WEIGHTED
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.0230241175 | 1 |  |
| AEIS | 0.0228918844 | 2 |  |
| AGX | 0.0223240599 | 3 |  |
| BLTE | 0.0222945019 | 4 |  |
| LITE | 0.0221762699 | 5 |  |
| ALM | 0.0221264881 | 6 |  |
| POWL | 0.02202848 | 7 |  |
| MTZ | 0.0220253686 | 8 |  |

### TOP100_SCORE_WEIGHTED
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| FORM | 0.0128123248 | 1 |  |
| AEIS | 0.0127387405 | 2 |  |
| AGX | 0.0124227608 | 3 |  |
| BLTE | 0.0124063126 | 4 |  |
| LITE | 0.0123405196 | 5 |  |
| ALM | 0.0123128172 | 6 |  |
| POWL | 0.0122582783 | 7 |  |
| MTZ | 0.0122565469 | 8 |  |

### LOW_VOL_ADJUSTED_TOP50
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| ALM | 0.0352465137 | 6 |  |
| SOXL | 0.0341272473 | 13 |  |
| INTC | 0.0320413845 | 25 |  |
| AEHR | 0.0313405169 | 17 |  |
| LITE | 0.0307906525 | 5 |  |
| FLEX | 0.0307724888 | 43 |  |
| SNDK | 0.0297475248 | 22 |  |
| BE | 0.0294658178 | 47 |  |

### MOTIF_READY_EQUAL_WEIGHT
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| AEIS | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| BLTE | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| MU | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| CAMT | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| KEYS | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| VIAV | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| SITM | 0.0555555556 |  | BREAKOUT_CONTINUATION |
| TSEM | 0.0555555556 |  | BREAKOUT_CONTINUATION |

### MOTIF_READY_TOPN_BLEND
| Ticker | Weight | Rank | Motif |
| --- | --- | --- | --- |
| AEIS | 0.1 |  | BREAKOUT_CONTINUATION;EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| BLTE | 0.1 |  | BREAKOUT_CONTINUATION;EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| AGX | 0.0833333333 |  | EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| ALM | 0.0833333333 |  | EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| FORM | 0.0833333333 |  | EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| LITE | 0.0833333333 |  | EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| MOD | 0.0833333333 |  | EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |
| MTZ | 0.0833333333 |  | EQUAL_WEIGHT_TOP_N_BASELINE;MEAN_REVERSION_CANDIDATE;RISK_ADJUSTED_TOP_RANK;SCORE_WEIGHTED_TOP_N_BASELINE;TECHNICAL_OVERHEAT_AVOIDANCE |

## 操作员结论

这些组合都是影子组合，不是订单建议，不会改变官方候选、权重、冻结、纸交易或账户记录。可用于后续研究比较：等权 vs 分数加权 vs 风险代理调整 vs ready motif 混合。
