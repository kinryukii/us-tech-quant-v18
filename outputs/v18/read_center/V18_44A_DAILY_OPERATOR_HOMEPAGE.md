# V18.44A 每日操作首页 / Daily Operator Homepage V2

## 1. 今天先看结论

| 项目 | 结论 |
| --- | --- |
| 今日系统是否可用 | 是 |
| 候选池是否可读 | 是 |
| 是否有阻塞失败 | 否 |
| 是否允许交易 | 否 |
| 自动交易 | DISABLED |
| 自动卖出 | DISABLED |
| 当前状态 | WARN |
| 一句话解释 | 今天 pipeline 可用，没有 blocking failure；WARN 主要来自非阻塞的覆盖率、risk preview 或 supporting inputs partial。 |

## 2. 今日核心数字

| Machine field | Value |
| --- | --- |
| LATEST_SIGNAL_DATE | `2026-05-27` |
| LATEST_SIGNAL_FREEZE_COUNT | `318` |
| CURRENT_FULL_CANDIDATE_COUNT | `318` |
| CURRENT_TOP_CANDIDATE_COUNT | `20` |
| LONG_CANDIDATE_COUNT | `20` |
| TOP_FULL_MISMATCH_COUNT | `0` |
| BLOCKING_CURRENT_FAILURE_COUNT | `0` |
| EXPECTED_REMAINING_ACTION_REQUIRED_COUNT | `0` |
| DAILY_RUN_USABLE | `TRUE` |
| BUY_CANDIDATE_REPORT_USABLE | `TRUE` |
| TRADING_EXECUTION_ALLOWED | `FALSE` |


> 旧中文首页候选数与当前 pipeline 口径不一致，V18.44A 以 V18.41A 当前口径为准。

## 3. TopN 排名解释摘要

| Machine field | Value |
| --- | --- |
| STATUS | `WARN_V18_43A_SUPPORTING_INPUTS_PARTIAL` |
| TOP_N_EFFECTIVE | `20` |
| TOP_SCORE | `59.2000` |
| BOTTOM_SCORE_WITHIN_TOPN | `51.6840` |
| TOPN_SCORE_SPREAD | `7.5160` |
| CLOSE_GAP_COUNT | `10` |
| CURRENT_ALIAS_WRITTEN | `TRUE` |
| CURRENT_READ_FIRST_WRITTEN | `TRUE` |

- Packet: `outputs/v18/read_center/V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`
- Driver matrix: `outputs/v18/ops/V18_CURRENT_TOPN_RANKING_DRIVER_MATRIX.csv`
- Close rank gaps: `outputs/v18/ops/V18_CURRENT_TOPN_CLOSE_RANK_GAPS.csv`

## 4. 当前单票解释摘要

| Machine field | Value |
| --- | --- |
| STATUS | `WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL` |
| TICKER | `FORM` |
| TICKER_FOUND | `TRUE` |
| TARGET_RANK | `1` |
| TARGET_SCORE_COLUMN | `composite_candidate_score` |
| TARGET_SCORE_VALUE | `59.2` |
| CURRENT_ALIAS_WRITTEN | `TRUE` |

- Report: `outputs/v18/read_center/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md`
- Attribution: `outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_RANKING_ATTRIBUTION.csv`
- Neighbor comparison: `outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv`

## 5. WARN 分类

### A. Blocking / 阻塞
- 当前未发现 blocking warning。

### B. Nonblocking but review / 非阻塞但建议看
- `V18_41A_STATUS`: 状态为 WARN，通常表示非阻塞但建议阅读。 状态: `WARN_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_REVIEW_NEEDED`
- `TOPN_STATUS`: 状态为 WARN，通常表示非阻塞但建议阅读。 状态: `WARN_V18_43A_SUPPORTING_INPUTS_PARTIAL`
- `SINGLE_STATUS`: 状态为 WARN，通常表示非阻塞但建议阅读。 状态: `WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL`
- `RISK_PREVIEW_REVIEW_NEEDED`: 发现非阻塞 review 信号。 状态: `V18.39C risk preview review needed`

### C. Expected / 预期存在
- `AUTO_TRADE_DISABLED_EXPECTED`: 这是预期安全边界，不是故障。
- `AUTO_SELL_DISABLED_EXPECTED`: 这是预期安全边界，不是故障。
- `TRADING_EXECUTION_ALLOWED_FALSE_EXPECTED`: 这是预期安全边界，不是故障。
- `OFFICIAL_DECISION_IMPACT_NONE_EXPECTED`: 这是预期安全边界，不是故障。
- `FORWARD_EVIDENCE_PENDING_EXPECTED`: 前向证据等待未来价格是研究流程中的预期状态。
- `SHADOW_RESEARCH_ONLY_EXPECTED`: shadow/research-only warning 不代表可交易。

## 6. 今天建议阅读顺序

1. `outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_V2.md`
2. `outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt`
3. `outputs/v18/read_center/V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`
4. `outputs/v18/read_center/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md`
5. `outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md`
6. `outputs/v18/read_center/V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md`
7. `outputs/v18/read_center/V18_CURRENT_OPERATOR_CLEAN_STATUS.md`

## 7. 下一步操作建议

- 今天不需要修复阻塞问题，可以直接阅读 TopN 与单票解释。
- 排名接近区较多，建议重点看 close rank gaps。
- 当前单票解释对象是 `FORM`，可继续换 ticker 做 drilldown。
- WARN 主要是非阻塞 review，不影响候选池阅读。

## 8. Safety / 安全边界

- 本首页不重新计算排名。
- 本首页不修改候选池。
- 本首页不修改 signal freeze ledger。
- 本首页不改变交易决策。
- 本首页不允许自动交易。
- AUTO_TRADE remains DISABLED.
- AUTO_SELL remains DISABLED.

## 附录 A. Warning 明细

| warning_key | severity | source | status_text |
| --- | --- | --- | --- |
| `V18_41A_STATUS` | `REVIEW` | `V18_41A_READ_FIRST` | `WARN_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_REVIEW_NEEDED` |
| `TOPN_STATUS` | `REVIEW` | `TopN READ_FIRST` | `WARN_V18_43A_SUPPORTING_INPUTS_PARTIAL` |
| `SINGLE_STATUS` | `REVIEW` | `V18_42A_READ_FIRST` | `WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL` |
| `RISK_PREVIEW_REVIEW_NEEDED` | `REVIEW` | `outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md` | `V18.39C risk preview review needed` |
| `AUTO_TRADE_DISABLED_EXPECTED` | `EXPECTED` | `V18.44A safety guard` | `DISABLED` |
| `AUTO_SELL_DISABLED_EXPECTED` | `EXPECTED` | `V18.44A safety guard` | `DISABLED` |
| `TRADING_EXECUTION_ALLOWED_FALSE_EXPECTED` | `EXPECTED` | `V18.44A safety guard` | `FALSE` |
| `OFFICIAL_DECISION_IMPACT_NONE_EXPECTED` | `EXPECTED` | `V18.44A safety guard` | `NONE` |
| `FORWARD_EVIDENCE_PENDING_EXPECTED` | `EXPECTED` | `research-only daily process` | `EXPECTED` |
| `SHADOW_RESEARCH_ONLY_EXPECTED` | `EXPECTED` | `shadow/read-only reports` | `EXPECTED` |

## 附录 B. 文件检查清单

| file_key | exists | required_level | parse_status |
| --- | --- | --- | --- |
| `v18_41a_read_first` | `TRUE` | `CORE` | `OK` |
| `daily_clean_status` | `TRUE` | `CORE` | `OK` |
| `topn_read_first` | `TRUE` | `IMPORTANT` | `OK` |
| `topn_packet` | `TRUE` | `IMPORTANT` | `OK` |
| `topn_summary` | `TRUE` | `IMPORTANT` | `OK` |
| `topn_close_gaps` | `TRUE` | `IMPORTANT` | `OK` |
| `topn_driver_matrix` | `TRUE` | `IMPORTANT` | `OK` |
| `single_read_first` | `TRUE` | `IMPORTANT` | `OK` |
| `single_report` | `TRUE` | `IMPORTANT` | `OK` |
| `single_summary` | `TRUE` | `IMPORTANT` | `OK` |
| `single_attribution` | `TRUE` | `IMPORTANT` | `OK` |
| `single_neighbors` | `TRUE` | `IMPORTANT` | `OK` |
| `old_chinese_homepage` | `TRUE` | `OPTIONAL` | `OK` |
| `daily_brief` | `TRUE` | `OPTIONAL` | `OK` |
| `portfolio_target_preview` | `TRUE` | `OPTIONAL` | `OK` |
| `shadow_risk_model_preview` | `TRUE` | `OPTIONAL` | `OK` |
| `operator_clean_status` | `TRUE` | `OPTIONAL` | `OK` |
| `fixable_warning_reducer` | `TRUE` | `OPTIONAL` | `OK` |
| `residual_action_warning_resolver` | `TRUE` | `OPTIONAL` | `OK` |
| `alpha_signal_objects` | `TRUE` | `OPTIONAL` | `OK` |
| `candidate_top_full_sync` | `TRUE` | `OPTIONAL` | `OK` |
