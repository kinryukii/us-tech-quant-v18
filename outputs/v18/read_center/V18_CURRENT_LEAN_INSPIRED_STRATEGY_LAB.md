# V18.37A LEAN-Inspired Strategy Motif Lab

生成时间：2026-05-27T12:59:13

本报告是受 LEAN/QuantConnect 常见策略设计方式启发的研究层：提炼“价值+动量、质量+动量、突破延续、均值回归、风险调整”等策略母题，并映射到当前 V18 已有因子、技术计时和候选排名证据。它不是 LEAN 策略代码复刻，也不包含 broker、API、订单或账户逻辑。

明确边界：官方排名、交易决策、候选冻结、因子权重、纸交易账本、账户状态和执行逻辑均未改变。本步骤只生成研究/观察输出。

## 安全状态

- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- FORBIDDEN_MODIFIED: FALSE
- 候选来源：V18_CURRENT_FULL_RANKED_CANDIDATES.csv

## 总览

| 分组 | 数量 |
| --- | --- |
| 可用真实证据 | 6 |
| 仅代理研究 | 1 |
| 仅影子观察 | 0 |
| 缺少必需因子 | 3 |
| 候选输入数量 | 318 |
| 研究合并宇宙数量 | 318 |

## Motif 状态与候选

| Motif | 中文名 | 证据状态 | 研究可用性 | Top tickers |
| --- | --- | --- | --- | --- |
| VALUE_MOMENTUM | 价值动量 | MISSING_REQUIRED_FACTOR | NOT_READY | FORM, AEIS, AGX, BLTE, LITE |
| QUALITY_MOMENTUM | 质量动量 | MISSING_REQUIRED_FACTOR | NOT_READY | FORM, AEIS, AGX, BLTE, LITE |
| LOW_VOL_MOMENTUM | 低波动动量 | PROXY_RESEARCH_ONLY | PROXY_ONLY | FORM, AEIS, AGX, LITE, ALM |
| BREAKOUT_CONTINUATION | 突破延续 | READY_REAL_EVIDENCE | READY_FOR_PAPER_OBSERVATION | AEIS, BLTE, MU, CAMT, KEYS |
| MEAN_REVERSION_CANDIDATE | 均值回归候选 | READY_REAL_EVIDENCE | READY_FOR_PAPER_OBSERVATION | FORM, AEIS, AGX, BLTE, LITE |
| TECHNICAL_OVERHEAT_AVOIDANCE | 技术过热回避 | READY_REAL_EVIDENCE | READY_FOR_PAPER_OBSERVATION | FORM, AEIS, AGX, BLTE, LITE |
| RISK_ADJUSTED_TOP_RANK | 风险调整高排名 | READY_REAL_EVIDENCE | READY_FOR_PAPER_OBSERVATION | FORM, AEIS, AGX, BLTE, LITE |
| SECTOR_BALANCED_TOP_RANK | 行业均衡高排名 | MISSING_REQUIRED_FACTOR | NOT_READY | FORM, AEIS, AGX, BLTE, LITE |
| EQUAL_WEIGHT_TOP_N_BASELINE | 等权 Top N 基线 | READY_REAL_EVIDENCE | READY_FOR_PAPER_OBSERVATION | FORM, AEIS, AGX, BLTE, LITE |
| SCORE_WEIGHTED_TOP_N_BASELINE | 分数加权 Top N 基线 | READY_REAL_EVIDENCE | READY_FOR_PAPER_OBSERVATION | FORM, AEIS, AGX, BLTE, LITE |

## 逐项解释

### VALUE_MOMENTUM：价值动量
- 含义：寻找已有动量证据支持、但仍需要估值因子确认的候选。
- LEAN 启发：借鉴 LEAN 示例中常见的基本面筛选叠加价格动量框架，只抽象研究主题，不复用代码逻辑。
- 当前支持因子：F003:factor_pack_score:REAL_IMPLEMENTED;F005:composite_candidate_score:REAL_IMPLEMENTED;F001:WorldQuant / Factor Pack:REAL_IMPLEMENTED;VOL001:Volume Surge:REAL_IMPLEMENTED;FIELD:F011_TS_MOMENTUM_60_120:CURRENT_OUTPUT;FIELD:ret_60d:CURRENT_OUTPUT;FIELD:ret_120d:CURRENT_OUTPUT
- 缺失/不足：VAL001:Valuation / Growth Match:MISSING
- 研究状态：MISSING_REQUIRED_FACTOR / NOT_READY
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### QUALITY_MOMENTUM：质量动量
- 含义：寻找已有动量证据支持、但仍需要质量因子确认的候选。
- LEAN 启发：借鉴质量筛选加趋势确认的策略设计母题，只映射到 V18 现有证据。
- 当前支持因子：F003:factor_pack_score:REAL_IMPLEMENTED;F005:composite_candidate_score:REAL_IMPLEMENTED;F001:WorldQuant / Factor Pack:REAL_IMPLEMENTED;VOL001:Volume Surge:REAL_IMPLEMENTED;FIELD:F011_TS_MOMENTUM_60_120:CURRENT_OUTPUT;FIELD:ret_60d:CURRENT_OUTPUT;FIELD:ret_120d:CURRENT_OUTPUT
- 缺失/不足：Q001:QMJ:REPORT_ONLY
- 研究状态：MISSING_REQUIRED_FACTOR / NOT_READY
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### LOW_VOL_MOMENTUM：低波动动量
- 含义：优先观察动量仍在、且波动惩罚较低或技术风险较低的候选。
- LEAN 启发：借鉴风险调整趋势策略的母题，用现有波动/过热代理证据做影子观察。
- 当前支持因子：F003:factor_pack_score:REAL_IMPLEMENTED;F005:composite_candidate_score:REAL_IMPLEMENTED;T005:overheat_penalty:REAL_IMPLEMENTED;V003:Volatility Expansion / Compression:PROXY_IMPLEMENTED;V001:20D Realized Volatility:SHADOW_ONLY;V002:60D Realized Volatility:SHADOW_ONLY;V004:Return / Volatility Ratio:SHADOW_ONLY;FIELD:volatility_penalty:CURRENT_OUTPUT;FIELD:overheat_penalty:CURRENT_OUTPUT;FIELD:F011_TS_MOMENTUM_60_120:CURRENT_OUTPUT
- 缺失/不足：真实 20D/60D 波动率与收益波动比仍是影子或代理证据。
- 研究状态：PROXY_RESEARCH_ONLY / PROXY_ONLY
- 影子候选前列：FORM, AEIS, AGX, LITE, ALM

### BREAKOUT_CONTINUATION：突破延续
- 含义：观察布林、成交量、价格确认共同支持的突破延续候选。
- LEAN 启发：借鉴技术突破策略的设计母题，只使用 V18 已计算的技术计时和成交量确认字段。
- 当前支持因子：T001:Bollinger Bands / BB:REAL_IMPLEMENTED;T004:technical_timing_score:REAL_IMPLEMENTED;VOL001:Volume Surge:REAL_IMPLEMENTED;VOL003:Breakout Volume Confirmation:REAL_IMPLEMENTED;V003:Volatility Expansion / Compression:PROXY_IMPLEMENTED;FIELD:breakout_confirmation_bonus:CURRENT_OUTPUT;FIELD:F009_VOLUME_PRICE_CONFIRM:CURRENT_OUTPUT;FIELD:volume_ratio_5_20:CURRENT_OUTPUT
- 缺失/不足：无需新增交易逻辑；若要实盘化仍需单独风控和订单层设计。
- 研究状态：READY_REAL_EVIDENCE / READY_FOR_PAPER_OBSERVATION
- 影子候选前列：AEIS, BLTE, MU, CAMT, KEYS

### MEAN_REVERSION_CANDIDATE：均值回归候选
- 含义：观察短期回撤、布林下半区或下轨附近但中期趋势仍可接受的候选。
- LEAN 启发：借鉴回撤/均值回归策略母题，当前仅作为等待观察组。
- 当前支持因子：T001:Bollinger Bands / BB:REAL_IMPLEMENTED;T004:technical_timing_score:REAL_IMPLEMENTED;F001:WorldQuant / Factor Pack:REAL_IMPLEMENTED;VOL004:Dry-Up Pullback:REPORT_ONLY;FIELD:F006_SHORT_REV_5D:CURRENT_OUTPUT;FIELD:F007_PULLBACK_IN_UPTREND:CURRENT_OUTPUT;FIELD:F012_TS_PULLBACK_REVERSAL:CURRENT_OUTPUT;FIELD:pullback_status:CURRENT_OUTPUT
- 缺失/不足：干缩回撤等更细成交量结构仍未实现。
- 研究状态：READY_REAL_EVIDENCE / READY_FOR_PAPER_OBSERVATION
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### TECHNICAL_OVERHEAT_AVOIDANCE：技术过热回避
- 含义：观察综合排名靠前且未出现明显过热惩罚或技术警告的候选。
- LEAN 启发：借鉴趋势策略中的过热过滤母题，只生成研究提示，不改变买卖判断。
- 当前支持因子：T002:RSI:REAL_IMPLEMENTED;T003:KDJ:REAL_IMPLEMENTED;T005:overheat_penalty:REAL_IMPLEMENTED;T004:technical_timing_score:REAL_IMPLEMENTED;OPT002:Gamma Exposure / GEX:PROXY_IMPLEMENTED;OPT003:Call / Put Ratio:PROXY_IMPLEMENTED;OPT004:IV Rank / IV Percentile:PROXY_IMPLEMENTED;FIELD:overheat_penalty:CURRENT_OUTPUT;FIELD:technical_warning_label:CURRENT_OUTPUT;FIELD:rsi_14:CURRENT_OUTPUT;FIELD:kdj_status:CURRENT_OUTPUT
- 缺失/不足：期权拥挤和隐波证据仍是代理，不作为官方交易门控。
- 研究状态：READY_REAL_EVIDENCE / READY_FOR_PAPER_OBSERVATION
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### RISK_ADJUSTED_TOP_RANK：风险调整高排名
- 含义：从当前官方候选中观察综合分靠前、技术风险相对温和的研究组。
- LEAN 启发：借鉴风险调整排序母题，但不重算官方排名、不改权重。
- 当前支持因子：F005:composite_candidate_score:REAL_IMPLEMENTED;T004:technical_timing_score:REAL_IMPLEMENTED;T005:overheat_penalty:REAL_IMPLEMENTED;V001:20D Realized Volatility:SHADOW_ONLY;V002:60D Realized Volatility:SHADOW_ONLY;V004:Return / Volatility Ratio:SHADOW_ONLY;FIELD:composite_candidate_score:CURRENT_OUTPUT;FIELD:technical_timing_score:CURRENT_OUTPUT;FIELD:overheat_penalty:CURRENT_OUTPUT
- 缺失/不足：真实风险调整收益因子仍未进入官方排序。
- 研究状态：READY_REAL_EVIDENCE / READY_FOR_PAPER_OBSERVATION
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### SECTOR_BALANCED_TOP_RANK：行业均衡高排名
- 含义：理论上应按行业控制集中度，但当前候选文件没有可靠行业字段。
- LEAN 启发：借鉴组合构建中的行业均衡母题；本步骤只标记缺口。
- 当前支持因子：F005:composite_candidate_score:REAL_IMPLEMENTED;FIELD:composite_candidate_score:CURRENT_OUTPUT
- 缺失/不足：SECTOR001:SECTOR001:NOT_IN_STRICT_AUDIT
- 研究状态：MISSING_REQUIRED_FACTOR / NOT_READY
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### EQUAL_WEIGHT_TOP_N_BASELINE：等权 Top N 基线
- 含义：以当前候选排名前 N 作为等权观察基线；不生成订单、不改仓位。
- LEAN 启发：借鉴组合基线对照思想，仅用于研究观察。
- 当前支持因子：F005:composite_candidate_score:REAL_IMPLEMENTED;FIELD:rank:CURRENT_OUTPUT;FIELD:composite_candidate_score:CURRENT_OUTPUT
- 缺失/不足：等权只是观察标签，不是账户或交易指令。
- 研究状态：READY_REAL_EVIDENCE / READY_FOR_PAPER_OBSERVATION
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

### SCORE_WEIGHTED_TOP_N_BASELINE：分数加权 Top N 基线
- 含义：以当前候选综合分前 N 作为分数加权观察基线；不改变任何官方权重。
- LEAN 启发：借鉴分数加权组合基线思想，只保留研究解释。
- 当前支持因子：F005:composite_candidate_score:REAL_IMPLEMENTED;F003:factor_pack_score:REAL_IMPLEMENTED;T004:technical_timing_score:REAL_IMPLEMENTED;FIELD:rank:CURRENT_OUTPUT;FIELD:composite_candidate_score:CURRENT_OUTPUT
- 缺失/不足：分数加权只是观察标签，不是账户或交易指令。
- 研究状态：READY_REAL_EVIDENCE / READY_FOR_PAPER_OBSERVATION
- 影子候选前列：FORM, AEIS, AGX, BLTE, LITE

## 操作员结论

READY_REAL_EVIDENCE 可进入纸交易观察视角，但仍不代表自动买卖。PROXY_RESEARCH_ONLY 和 SHADOW_ONLY 只能作为研究提示。MISSING_REQUIRED_FACTOR 表示缺少关键因子，不能伪造分数或推断实盘可用性。
