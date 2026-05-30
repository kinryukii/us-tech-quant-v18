# V18.39A Alpha Signal Object Layer 报告

## 1. 今日结论
- 状态: OK_V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_READY
- Signal object 数量: 318
- 最新 signal date: 2026-05-29
- 最新 freeze 数量: 318
- 当前候选池数量: 318

## 2. Alpha signal object 是什么
- 这是把 ranked candidates、factor score、technical timing、risk/data tags、freeze 和研究状态整理成统一信号对象的只读层。
- 它不是买入建议，不下单，不连接账户，不改变排名或权重。

## 3. 总体信号分布
- LONG_CANDIDATE: 20
- WATCH: 298
- AVOID: 0
- UNKNOWN: 0

## 4. Top20 / Top50 / Top100 信号概览
- TOP20: 20
- TOP50: 50
- TOP100: 100
- TOP/FULL ticker overlap count: 20
- TOP/FULL ticker mismatch count: 0
- TOP/FULL order matches: TRUE
- TOP/FULL canonical sync required: FALSE
- 当前 top candidate 数量: 20

## 5. 置信度分布
- HIGH: 0
- MEDIUM: 20
- LOW: 298

## 6. 风险与过热标签
- Severe overheat 数量: 0
- Data quality warning 数量: 0

## 7. Forward evidence 状态
- Pending forward outcome 数量: 318
- Forward research usable: TRUE

## 8. 与 V18.38A/B/C 的关系
- V18.38A 提供 forward evidence readiness。
- V18.38B 提供 experiment registry / research context。
- V18.38C-R1 提供 current-vs-legacy command status scope。
- COMMAND_STATUS_CURRENT_BLOCKING_COUNT: 0
- DAILY_RUN_USABLE: TRUE

## 9. Safety / no-impact confirmation
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

## 10. 下一步建议
Signal objects are ready for downstream read-only portfolio/risk preview modules.
