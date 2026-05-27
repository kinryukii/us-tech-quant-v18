# V18.4I Backtest-Forward Promotion Merge

生成时间：2026-05-19 10:56:32

## 1. 结论

- V18_4I_STATUS: `OK_BACKTEST_FORWARD_PROMOTION_MERGE_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- PROMOTION_ACTION: `NONE`
- DIRECT_PROMOTION: `NO`
- GLOBAL_FORWARD_GATE: `FORWARD_KEEP_WATCHING_NO_PROMOTION`
- CORE_ALPHA_WATCH: `F007_PULLBACK_IN_UPTREND`
- PRIMARY_CONFIRMATION_WATCH: `F009_VOLUME_PRICE_CONFIRM`

当前结论：

```text
F007 是历史强 alpha，但被回撤和 forward 成熟度阻挡。
F009 是主要确认因子，但同样不能单独 promotion。
F010/F011/F008/F006 只作为辅助证据，不直接触发 official decision。
```

## 2. 输入来源

- BACKTEST_INTERPRETATION: `D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_R1A_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.csv`
- FORWARD_SOURCE_USED: `D:\us-tech-quant\outputs\v18\outcome_summary\V18_4B_CURRENT_FACTOR_OUTCOME_SUMMARY.csv`

文本上下文来源：

- `D:\us-tech-quant\outputs\v18\outcome_summary\V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md`
- `D:\us-tech-quant\outputs\v18\outcome_summary\V18_4B_CURRENT_PROMOTION_RULES.md`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY.md`
- `D:\us-tech-quant\outputs\v18\daily_integrated\V18_4B_R1_READ_FIRST.txt`
- `D:\us-tech-quant\outputs\v18\factor_backtest\V18_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md`

## 3. 全局 promotion context

- PROMOTION_RECOMMENDATION: `KEEP_WATCHING`
- PROMOTION_ACTION: `NONE`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 4. 合并后因子状态

| rank | factor | cluster_role | alpha | drawdown | merged_status | avg_rank | top3_rate | avg_sharpe | avg_cagr | worst_dd | official_impact |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | F007_PULLBACK_IN_UPTREND | CORE_ALPHA_WATCH | STRONG_ALPHA | VERY_HIGH_DRAWDOWN_RISK | CORE_WATCH_NOT_PROMOTED_DD_AND_FORWARD_BLOCKED | 1.86 | 91.67% | 2.015 | 139.51% | -58.32% | NONE |
| 2 | F009_VOLUME_PRICE_CONFIRM | PRIMARY_CONFIRMATION_WATCH | HIGH_ALPHA | HIGH_DRAWDOWN_RISK | PRIMARY_CONFIRMATION_WATCH_NOT_PROMOTED_DD_AND_FORWARD_BLOCKED | 2.84 | 60.42% | 1.887 | 118.44% | -54.00% | NONE |
| 3 | F010_XSEC_COMPOSITE_RANK | AUXILIARY_STABILIZER_ONLY | SECONDARY_ALPHA | EXTREME_DRAWDOWN_RISK | AUXILIARY_EVIDENCE_ONLY | 3.48 | 54.17% | 1.831 | 107.39% | -65.63% | NONE |
| 4 | F011_TS_MOMENTUM_60_120 | AUXILIARY_TREND_CONFIRMATION | MODERATE_ALPHA | HIGH_DRAWDOWN_RISK | AUXILIARY_EVIDENCE_ONLY | 3.84 | 40.62% | 1.790 | 114.40% | -51.53% | NONE |
| 5 | F008_VOLUME_ABNORMAL_5_20 | AUXILIARY_VOLUME_ABNORMALITY | MODERATE_ALPHA | ELEVATED_DRAWDOWN_RISK | AUXILIARY_EVIDENCE_ONLY | 4.23 | 31.25% | 1.680 | 80.20% | -47.85% | NONE |
| 6 | F006_SHORT_REV_5D | AUXILIARY_SHORT_REVERSAL | SECONDARY_ALPHA | VERY_HIGH_DRAWDOWN_RISK | AUXILIARY_EVIDENCE_ONLY | 4.74 | 21.88% | 1.545 | 81.93% | -56.31% | NONE |

## 5. Promotion cluster

```text
CORE:        F007_PULLBACK_IN_UPTREND
CONFIRM:     F009_VOLUME_PRICE_CONFIRM
AUXILIARY:   F010 / F011 / F008 / F006
ACTION:      WATCH_NOT_PROMOTED
IMPACT:      OFFICIAL_DECISION_IMPACT = NONE
```

## 6. 下一步

下一步不是直接 promotion，而是做 V18.4I-R1：把本 merge 报告接入 final daily wrapper，使每天自动刷新 promotion evidence。
接入后仍然不允许绕过 event gate、budget lock、behavior guard 和 official daily decision。