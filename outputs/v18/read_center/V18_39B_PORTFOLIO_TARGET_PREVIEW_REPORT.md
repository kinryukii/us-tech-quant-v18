# V18.39B Portfolio Target Preview 报告

## 1. 今日结论
- 状态: OK_V18_39B_PORTFOLIO_TARGET_PREVIEW_READY
- Alpha signal input count: 318
- Scenario count: 5
- Capital level count: 4
- Total preview rows: 1832

## 2. Portfolio Target Preview 是什么
- 这是把 V18.39A alpha signal objects 转换成模拟资金规模下的 target weight / target notional / feasibility preview。
- 它不是交易建议，不是订单列表，不使用真实账户现金或持仓。

## 3. 使用的模拟资金规模
- 1000
- 2000
- 5000
- 10000

## 4. Top20 Equal Weight 预览
- 10000 USD included tickers: 20
- Weight sum: 1.0000000000
- Whole-share feasible: 16

## 5. Top20 Confidence Weighted 预览
- 10000 USD included tickers: 20
- Weight sum: 1.0000000000
- Whole-share feasible: 16

## 6. Top50 capped / rank decay 预览
- TOP50 capped weight sum: 1.0000000000
- TOP50 rank decay weight sum: 0.9999999999
- Max position cap: 5%

## 7. 整股可买性 / 价格覆盖情况
- Price available rows: 1832
- Price missing rows: 0
- Missing price 不会阻断输出，会标记为 PRICE_MISSING。

## 8. 为什么这不是下单
- 没有真实账户现金或持仓输入。
- 没有 broker/API 调用。
- 没有 order ticket、broker instruction 或 executable trade file。
- 输出只是理论 target preview。

## 9. 与 V18.39A Alpha Signal Object 的关系
- V18.39B 只消费 V18.39A alpha signal objects。
- 不重算排名，不改信号，不改权重公式。

## 10. Safety / no-impact confirmation
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- ORDER_EXECUTION_USED: FALSE
- BROKER_API_USED: FALSE
- REAL_ACCOUNT_USED: FALSE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE

## 11. 下一步建议
Portfolio target previews are ready for downstream read-only risk model preview.
