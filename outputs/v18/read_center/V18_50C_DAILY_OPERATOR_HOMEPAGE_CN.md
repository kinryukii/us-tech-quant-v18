# V18.50C 每日操作员中文首页

- 生成时间: `2026-05-30T22:57:57`
- 报告状态: `PASS`
- Source gate: `PASS` / OK=`TRUE`

## 1. 每日 source-chain 状态

| 项目 | 值 |
| --- | --- |
| V18.50B-R2 PATCH_VERSION | `V18.50B-R2` |
| source-chain status | `PASS` |
| sole-writer audit | `TRUE` |
| active legacy writer count | `0` |
| current Top20 write allowed | `TRUE` |
| current Top20 blocked reason | `NONE` |
| reconciliation | `317 + 6 == 323` / `TRUE` |
| freshness | full=`TRUE`, top20=`TRUE` |
| safety | ranking=`FALSE`, weights=`FALSE`, trading=`FALSE` |

## 2. 今日可用性结论

| 判断 | 值 |
| --- | --- |
| 今日系统可读 | `TRUE` |
| 今日数据可信 | `TRUE` |
| 今日 Top20 可用 | `TRUE` |
| 今日模拟动作可参考 | `TRUE` |
| 今日真实持仓动作可参考 | `FALSE` |
| 今日是否允许交易执行 | `FALSE` |

## 3. 当前 Top20

| rank | ticker | company_name | composite_candidate_score | factor_score | technical_score | latest_price_date | authoritative_row_ok | explanation_cn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | VIAV | Viavi Solutions Inc. | 54.7190 | 84.2974 | 70.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 2 | BW | Babcock & Wilcox Enterprises Inc. | 53.8162 | 97.0404 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 3 | AEHR | Aehr Test Systems | 52.7858 | 94.4644 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 4 | INTC | Intel Corporation | 52.7075 | 94.2687 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 5 | SITM | SiTime Corporation | 50.9635 | 89.9086 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 6 | FORM | FormFactor Inc. | 50.7091 | 81.7728 | 60.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 7 | TSEM | Tower Semiconductor Ltd. | 50.6445 | 89.1114 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 8 | LITE | Lumentum Holdings Inc. | 50.4882 | 81.2206 | 60.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 9 | WOLF |  | 49.6981 | 86.7453 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 10 | BE | Bloom Energy Corporation | 49.5652 | 86.4131 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 11 | POWL | Powell Industries Inc. | 49.4650 | 86.1626 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 12 | ACLS | Axcelis Technologies Inc. | 48.7277 | 84.3193 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 13 | AMKR | Amkor Technology Inc. | 48.3068 | 75.7671 | 60.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 14 | MTZ | MasTec Inc. | 48.2939 | 68.2346 | 70.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 15 | VECO | Veeco Instruments Inc. | 46.9072 | 79.7679 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 16 | PUMP | ProPetro Holding Corp. | 46.3346 | 63.3365 | 70.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 17 | ICHR | Ichor Holdings Ltd. | 46.2932 | 78.2330 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 18 | VRT | Vertiv Holdings Co. | 46.2677 | 70.6691 | 60.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 19 | COHR | Coherent Corp. | 46.1899 | 77.9748 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |
| 20 | TTMI | TTM Technologies Inc. | 45.9414 | 77.3535 | 50.0000 | 2026-05-29 | TRUE | 权威重算Top20；仅供复核，不代表自动买入。 |

## 4. V18.50A action packet 摘要

- action packet found: `TRUE`
- action packet rows: `31`
- PAPER_BUY: `3`
- PAPER_WATCH: `0`
- PAPER_SKIP_POLICY_LIMIT: `17`
- REAL_POSITION_DATA_MISSING: `20`

### Top20 动作明细

| rank | ticker | simulation_action | real_position_action |
| --- | --- | --- | --- |
| 1 | VIAV | PAPER_BUY_CANDIDATE | REAL_POSITION_DATA_MISSING |
| 2 | BW | PAPER_BUY_CANDIDATE | REAL_POSITION_DATA_MISSING |
| 3 | AEHR | PAPER_BUY_CANDIDATE | REAL_POSITION_DATA_MISSING |
| 4 | INTC | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 5 | SITM | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 6 | FORM | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 7 | TSEM | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 8 | LITE | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 9 | WOLF | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 10 | BE | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 11 | POWL | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 12 | ACLS | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 13 | AMKR | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 14 | MTZ | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 15 | VECO | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 16 | PUMP | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 17 | ICHR | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 18 | VRT | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 19 | COHR | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |
| 20 | TTMI | PAPER_SKIP_POLICY_LIMIT | REAL_POSITION_DATA_MISSING |

## 5. 风险与阻塞摘要

| 来源 | 摘要 |
| --- | --- |
| Event risk | TOP20_TOTAL=`20`, EARNINGS_FOUND=`1`, UNKNOWN=`19` |
| Options risk | ticker_count=`20`, medium=`12`, high=`8`, avg_score=`45.60` |
| Priority tracker | SNAPSHOT_ROWS=`20`, TRACKER_ROWS=`20` |
| V18.49A/B/C/D | 49A=`WARN_V18_49A_R1_LIMITED_POINT_IN_TIME_EVIDENCE`, 49B=`WARN_V18_49B_SOURCE_BACKTEST_LOW_EVIDENCE`, 49C=`WARN_V18_49C_SOURCE_POLICY_LOW_CONFIDENCE`, 49D=`WARN_V18_49D_NO_USER_UPLOADS_FOUND` |
| V18.50A | status=`PASS`, simulation_decision=`SIM_BALANCED`, source_policy_confidence=`LOW` |

### 可选风险报告文件

| name | exists | row_count | status |
| --- | --- | --- | --- |
| event_risk_summary | TRUE | 10 | FOUND |
| event_risk_diagnostics | TRUE | 20 | FOUND |
| options_risk_summary | TRUE | 1 | FOUND |
| options_risk_detail | TRUE | 56 | FOUND |
| priority_summary | TRUE | 10 | FOUND |
| priority_snapshot | TRUE | 20 | FOUND |
| v18_49a_read_first | TRUE | 0 | FOUND |
| v18_49b_read_first | TRUE | 0 | FOUND |
| v18_49c_read_first | TRUE | 0 | FOUND |
| v18_49d_read_first | TRUE | 0 | FOUND |
| v18_50a_read_first | TRUE | 0 | FOUND |
| v18_50a_action_summary | TRUE | 1 | FOUND |

## 6. 今日需要注意的问题

- 真实持仓数据缺失，真实持仓动作不可参考。
- 不可用/疑似退市 ticker: `CDTX, CFLT, COG, JFROG, MPW`
- 价格历史不足 ticker: `TQQQ`

## 7. 操作员下一步

- 先确认 V18.50B-R2 source gate PASS。
- 看 Top20 表，确认价格日期和权威来源。
- 看 action packet，确认 simulation_action 与 real_position_action。
- 看 event/options risk 和 priority tracker。
- 若 simulation_action 全部为 PAPER_SKIP_POLICY_LIMIT，说明买入策略尚未恢复，不要当作买入建议。
- 不做真实交易。
- 下一阶段才做模拟买入策略矩阵。

## 安全声明

V18.50C 只做可读性和 source audit 汇总；不改排名、不改权重、不改买卖策略、不写 Top20 current alias、不启用交易。
