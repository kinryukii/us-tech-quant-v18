# V18.4H-R1 因子稳健性审计报告

## 1. 结论

本报告自动测试当前 F006-F011 因子在不同参数组合下的稳健性。
它是历史回测证据层，不直接改变 official daily decision。

## 2. 参数矩阵

- LOOKBACK_DAYS_LIST: `756,1260`
- TOP_N_LIST: `5,10,15,20`
- HOLD_DAYS_LIST: `3,5,10,20`
- COST_BPS_LIST: `10,25,50`
- MATRIX_ROWS: `576`
- CONFIG_COUNT: `96`

## 3. 因子稳健性排名

| rank | factor | recommendation | role | avg rank | top1 | top3 rate | avg Sharpe | avg CAGR | worst MaxDD |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | F007_PULLBACK_IN_UPTREND | WATCH | CORE_PULLBACK_UPTREND_CANDIDATE | 1.86 | 52 | 91.67% | 2.015 | 139.51% | -58.32% |
| 2 | F009_VOLUME_PRICE_CONFIRM | STRONG_WATCH | VOLUME_PRICE_CONFIRMATION | 2.84 | 24 | 60.42% | 1.887 | 118.44% | -54.00% |
| 3 | F010_XSEC_COMPOSITE_RANK | WATCH | COMPOSITE_RANK_STABILIZER | 3.48 | 0 | 54.17% | 1.831 | 107.39% | -65.63% |
| 4 | F011_TS_MOMENTUM_60_120 | SECONDARY_EVIDENCE | TREND_CONFIRMATION_ONLY | 3.84 | 5 | 40.62% | 1.790 | 114.40% | -51.53% |
| 5 | F008_VOLUME_ABNORMAL_5_20 | SECONDARY_EVIDENCE | VOLUME_ABNORMALITY_SECONDARY | 4.23 | 9 | 31.25% | 1.680 | 80.20% | -47.85% |
| 6 | F006_SHORT_REV_5D | SECONDARY_EVIDENCE | SHORT_REVERSAL_CONFIRMATION | 4.74 | 6 | 21.88% | 1.545 | 81.93% | -56.31% |

## 4. 解释规则

- STRONG_WATCH：多数参数下进入前三，平均排名靠前，Sharpe 较高，且最差回撤没有严重失控。
- WATCH：整体表现良好，但仍存在参数敏感性。
- SECONDARY_EVIDENCE：可作为确认层，不适合作为单独主信号。
- WEAK_OR_SENSITIVE：参数敏感或排序不稳定。

## 5. 当前系统建议

当前不做直接 promotion。
下一步应把本历史稳健性审计结果与 V18.4A forward tracker 合并，形成 V18.4I backtest-forward promotion evidence。

建议的候选结构不是单因子，而是：

```text
F007_PULLBACK_IN_UPTREND
+ F010_XSEC_COMPOSITE_RANK
+ F006_SHORT_REV_5D or F009_VOLUME_PRICE_CONFIRM
```

F011_TS_MOMENTUM_60_120 只作为趋势确认层，不作为单独 promotion 主因子。

## 6. 输出文件

- `V18_4H_R1_CURRENT_ROBUSTNESS_MATRIX.csv`
- `V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_SUMMARY.csv`
- `V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_REPORT.md`
- `V18_CURRENT_FACTOR_ROBUSTNESS.md`