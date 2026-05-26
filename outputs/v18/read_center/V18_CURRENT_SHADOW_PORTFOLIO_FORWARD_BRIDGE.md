# V18.37C Shadow Portfolio Forward Bridge

生成时间：2026-05-25T18:48:10
RUN_ID：V18_37C_20260525_184809
状态：OK
信号日期：2026-05-25
日期来源：V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv:signal_date
ApplySnapshot：TRUE
Backup：D:\us-tech-quant\archive\v18\shadow_portfolio_snapshot_backups\V18_37C_20260525_184809

本层是 V18.37B 影子组合的研究快照与未来归因桥。它只冻结影子组合持仓和权重到专用 research ledger，用于未来 1D/3D/5D/10D/20D 组合级 forward return 比较。

它不是实盘交易，不是官方决策逻辑，也不修改官方排名、因子权重、候选别名、官方 signal freeze ledger、纸交易账本、账户状态、broker/API 或订单逻辑。

## 总览

| 指标 | 数值 |
| --- | --- |
| Portfolio 数 | 10 |
| Snapshot 行数 | 744 |
| Entry price 可用 | 744 |
| Entry price 缺失 | 0 |

## Forward Readiness

| Portfolio | 持仓数 | 权重和 | Entry 可用 | 1D | 3D | 5D | 10D | 20D |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FULL318_EQUAL_WEIGHT | 318 | 1.0 | 318 | 0 | 0 | 0 | 0 | 0 |
| LOW_VOL_ADJUSTED_TOP50 | 50 | 1.0 | 50 | 0 | 0 | 0 | 0 | 0 |
| MOTIF_READY_EQUAL_WEIGHT | 18 | 1.0 | 18 | 0 | 0 | 0 | 0 | 0 |
| MOTIF_READY_TOPN_BLEND | 18 | 1.0 | 18 | 0 | 0 | 0 | 0 | 0 |
| TOP100_EQUAL_WEIGHT | 100 | 1.0 | 100 | 0 | 0 | 0 | 0 | 0 |
| TOP100_SCORE_WEIGHTED | 100 | 1.0 | 100 | 0 | 0 | 0 | 0 | 0 |
| TOP20_EQUAL_WEIGHT | 20 | 1.0 | 20 | 0 | 0 | 0 | 0 | 0 |
| TOP20_SCORE_WEIGHTED | 20 | 1.0 | 20 | 0 | 0 | 0 | 0 | 0 |
| TOP50_EQUAL_WEIGHT | 50 | 1.0 | 50 | 0 | 0 | 0 | 0 | 0 |
| TOP50_SCORE_WEIGHTED | 50 | 1.0 | 50 | 0 | 0 | 0 | 0 | 0 |

## 安全状态

- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- FORBIDDEN_MODIFIED: FALSE
