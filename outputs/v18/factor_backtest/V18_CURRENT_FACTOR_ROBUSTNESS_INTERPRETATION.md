# V18.4H-R1A 因子稳健性解释修正报告

## 1. 结论

本报告不重新回测，只对 V18.4H-R1 的稳健性审计结果做解释层修正。

核心修正：

```text
不要把 REC 字段直接理解为因子强弱。
必须拆成：alpha_strength / drawdown_risk / promotion_status。
```

## 2. 输入状态

- MATRIX_ROWS: `576`
- CONFIG_COUNT: `96`
- INPUT_SUMMARY: `D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_SUMMARY.csv`
- INPUT_MATRIX: `D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_R1_CURRENT_ROBUSTNESS_MATRIX.csv`

## 3. 修正后因子解释

| rank | factor | alpha_strength | drawdown_risk | promotion_status | avg_rank | top1 | top3_rate | avg_sharpe | avg_cagr | worst_dd | final_role |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | F007_PULLBACK_IN_UPTREND | STRONG_ALPHA | VERY_HIGH_DRAWDOWN_RISK | CORE_WATCH_NOT_PROMOTED_DD_BLOCKED | 1.86 | 52 | 91.67% | 2.015 | 139.51% | -58.32% | CORE_PULLBACK_UPTREND_ALPHA |
| 2 | F009_VOLUME_PRICE_CONFIRM | HIGH_ALPHA | HIGH_DRAWDOWN_RISK | STRONG_CONFIRMATION_WATCH_DD_BLOCKED | 2.84 | 24 | 60.42% | 1.887 | 118.44% | -54.00% | PRIMARY_VOLUME_PRICE_CONFIRMATION |
| 3 | F011_TS_MOMENTUM_60_120 | MODERATE_ALPHA | HIGH_DRAWDOWN_RISK | SECONDARY_EVIDENCE_ONLY | 3.84 | 5 | 40.62% | 1.790 | 114.40% | -51.53% | TREND_CONFIRMATION_ONLY |
| 4 | F008_VOLUME_ABNORMAL_5_20 | MODERATE_ALPHA | ELEVATED_DRAWDOWN_RISK | SECONDARY_EVIDENCE_ONLY | 4.23 | 9 | 31.25% | 1.680 | 80.20% | -47.85% | VOLUME_ABNORMALITY_AUXILIARY |
| 5 | F010_XSEC_COMPOSITE_RANK | SECONDARY_ALPHA | EXTREME_DRAWDOWN_RISK | AUXILIARY_EVIDENCE_ONLY | 3.48 | 0 | 54.17% | 1.831 | 107.39% | -65.63% | COMPOSITE_RANK_STABILIZER |
| 6 | F006_SHORT_REV_5D | SECONDARY_ALPHA | VERY_HIGH_DRAWDOWN_RISK | AUXILIARY_EVIDENCE_ONLY | 4.74 | 6 | 21.88% | 1.545 | 81.93% | -56.31% | SHORT_REVERSAL_AUXILIARY |

## 4. 当前 promotion 结论

当前不做 official promotion。

原因：

```text
F007 historical alpha is strong, but drawdown risk is too high.
F009 is a strong confirmation factor, but still lacks merged forward proof.
F010 is useful as stabilizer, not standalone trigger.
Forward tracker evidence has not yet been merged into promotion rules.
```

## 5. 推荐候选结构

```text
CORE:        F007_PULLBACK_IN_UPTREND
CONFIRM:     F009_VOLUME_PRICE_CONFIRM
STABILIZER:  F010_XSEC_COMPOSITE_RANK
AUXILIARY:   F011 / F008 / F006
```

## 6. 下一步

进入 V18.4I：把 V18.4H-R1A 历史稳健性解释结果与 V18.4A/V18.4B forward tracker 合并。

V18.4I 的目标不是直接买入，而是生成：

```text
BACKTEST_FORWARD_PROMOTION_EVIDENCE
PROMOTION_CANDIDATE_CLUSTER
OFFICIAL_DECISION_IMPACT = NONE unless future rules explicitly promote
```