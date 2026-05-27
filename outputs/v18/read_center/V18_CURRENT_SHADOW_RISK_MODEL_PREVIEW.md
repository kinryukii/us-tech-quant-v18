# V18.39C Shadow Risk Model Preview 报告

## 1. 今日结论
- 状态: WARN_V18_39C_SHADOW_RISK_MODEL_PREVIEW_REVIEW_NEEDED
- Scenario + capital rows: 20
- Low / Medium / High / Research-only: 0 / 16 / 0 / 4
- Daily run usable: TRUE

## 2. Shadow Risk Model Preview 是什么
这是对 V18.39B 组合目标预览的只读风险检查，参考 LEAN Risk Management 的分层思想，但只做研究诊断。它检查集中度、整股可买性、信号质量、forward outcome pending、过热与数据质量标签。

## 3. 总体风险分布
- LOW: 0
- MEDIUM: 16
- HIGH: 0
- RESEARCH_ONLY: 4
- UNKNOWN: 0

## 4. 权重集中度风险
- Concentration watch rows: 0
- High concentration rows: 0
- 规则: 单票 >10% 或 Top5 >50% 进入 watch；单票 >20% 或 Top5 >70% 进入 high。

## 5. 小资金整股可买性风险
- Small capital constraint rows: 14
- Price missing risk rows: 0
- 小资金整股约束不代表系统阻断，只说明模拟资金较小时，部分目标无法买入一整股。

## 6. 信号质量与 forward evidence pending
- Forward evidence pending rows: 8
- Pending forward outcome 是当前研究层的可等待状态，不等同于交易阻断。

## 7. 数据质量 / freeze / overheat 风险
- Data quality review rows: 20
- Alpha input status: OK_V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_READY
- Portfolio input status: OK_V18_39B_PORTFOLIO_TARGET_PREVIEW_READY

## 8. 每个 scenario 的风险解释
- TOP20_CONFIDENCE_WEIGHTED / 1000 USD: MEDIUM；small capital whole-share constraints; forward evidence pending; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP20_CONFIDENCE_WEIGHTED / 10000 USD: MEDIUM；forward evidence pending; risk/data tags need review；建议=PREVIEW_USABLE_BUT_WAIT_FORWARD_EVIDENCE
- TOP20_CONFIDENCE_WEIGHTED / 2000 USD: MEDIUM；small capital whole-share constraints; forward evidence pending; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP20_CONFIDENCE_WEIGHTED / 5000 USD: MEDIUM；small capital whole-share constraints; forward evidence pending; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP20_EQUAL_WEIGHT / 1000 USD: MEDIUM；small capital whole-share constraints; forward evidence pending; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP20_EQUAL_WEIGHT / 10000 USD: MEDIUM；forward evidence pending; risk/data tags need review；建议=PREVIEW_USABLE_BUT_WAIT_FORWARD_EVIDENCE
- TOP20_EQUAL_WEIGHT / 2000 USD: MEDIUM；small capital whole-share constraints; forward evidence pending; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP20_EQUAL_WEIGHT / 5000 USD: MEDIUM；small capital whole-share constraints; forward evidence pending; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_EQUAL_WEIGHT_CAPPED / 1000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_EQUAL_WEIGHT_CAPPED / 10000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_EQUAL_WEIGHT_CAPPED / 2000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_EQUAL_WEIGHT_CAPPED / 5000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_RANK_DECAY_WEIGHTED / 1000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_RANK_DECAY_WEIGHTED / 10000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_RANK_DECAY_WEIGHTED / 2000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- TOP50_RANK_DECAY_WEIGHTED / 5000 USD: MEDIUM；small capital whole-share constraints; too many low-confidence signals; risk/data tags need review；建议=REVIEW_FEASIBILITY
- WATCHLIST_RESEARCH_ONLY_FULL318 / 1000 USD: RESEARCH_ONLY；Research-only watchlist scenario; not investable target risk.；建议=RESEARCH_ONLY_NOT_INVESTABLE
- WATCHLIST_RESEARCH_ONLY_FULL318 / 10000 USD: RESEARCH_ONLY；Research-only watchlist scenario; not investable target risk.；建议=RESEARCH_ONLY_NOT_INVESTABLE
- WATCHLIST_RESEARCH_ONLY_FULL318 / 2000 USD: RESEARCH_ONLY；Research-only watchlist scenario; not investable target risk.；建议=RESEARCH_ONLY_NOT_INVESTABLE
- WATCHLIST_RESEARCH_ONLY_FULL318 / 5000 USD: RESEARCH_ONLY；Research-only watchlist scenario; not investable target risk.；建议=RESEARCH_ONLY_NOT_INVESTABLE

## 9. 为什么这不是交易风控/不是下单
- 不使用真实账户现金或持仓。
- 不调用 broker/API。
- 不生成 order ticket、broker instruction、executable trade file 或 account-aware trade plan。
- 输出只用于模拟组合目标的研究风险预览。

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
Preview is usable for research, but wait for forward evidence and review feasibility/data tags.
