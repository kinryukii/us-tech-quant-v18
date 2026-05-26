# V18.35A 总池到候选池差异审计

- STATUS: `OK_V18_35A_UNIVERSE_TO_CANDIDATE_AUDIT_READY`
- RUN_ID: `V18_35A_20260525_184808`
- GENERATED_AT: `2026-05-25T18:48:08`

## 一句话结论
当前 rolling universe 总池为 `334`，current ranked candidates 为 `318`，总池中未进入当前候选池为 `16`。
最新 signal freeze 数量为 `318`，candidate 与 freeze 差异为 candidates_not_in_freeze=`0`，freeze_not_in_candidates=`0`。

这不是交易信号，也不是排名/候选生成逻辑变更；它只是解释为什么总池数量大于当前候选池数量。

## 核心数量
- 总池数量: `334`
- 当前候选数量: `318`
- 总池未进入候选数量: `16`
- 候选但不在总池数量: `0`
- 最新 freeze 数量: `318`
- freeze 是否匹配 current candidates: `YES`

## 未进入候选池原因分布
| exclusion_bucket | count |
| --- | ---: |
| `NOT_RECENTLY_SCANNED` | 16 |

## 分桶样例
- `NOT_RECENTLY_SCANNED`: 0, 105, 20, 250, 252, 303, 318, 325, CDTX, CFLT, COG, JFROG, MPW, TICKER, TICKERS, TRUE
- `PRICE_DATA_UNAVAILABLE`: NONE
- `PRICE_STALE_OR_NOT_LATEST`: NONE
- `FACTOR_PACK_MISSING`: NONE
- `TECHNICAL_TIMING_MISSING`: NONE
- `HISTORY_INSUFFICIENT_OR_LATEST_ONLY`: NONE
- `FILTERED_BY_CURRENT_CANDIDATE_RULES`: NONE
- `PRESENT_IN_CANDIDATE_BUT_NOT_FREEZE`: NONE
- `ORPHAN_CANDIDATE_NOT_IN_TOTAL_UNIVERSE`: NONE
- `UNKNOWN_INSUFFICIENT_EVIDENCE`: NONE
- `IN_FREEZE_NOT_CANDIDATE`: NONE

## 是否说明丢票
不直接说明丢票。这个审计只说明 total rolling universe 与 current ranked candidates 的集合差异，并按现有证据归因。
如果某个 ticker 被标记为 `UNKNOWN_INSUFFICIENT_EVIDENCE`，含义是当前报告层证据不足，不能把它说成被规则过滤或数据缺失。

## Operator Next Action
- 若主要分桶是 `FILTERED_BY_CURRENT_CANDIDATE_RULES`，优先查看 rolling universe state 的 tier/promotion/demotion 字段。
- 若出现 `FACTOR_PACK_MISSING` 或 `TECHNICAL_TIMING_MISSING`，优先查看对应 current factor/timing 文件是否覆盖该 ticker。
- 若出现 orphan 或 candidate/freeze mismatch，再进入修复任务；本审计不会自动修复。

## Evidence Source Paths
- `state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv`
- `outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv`
- `state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv`
- `outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv`
- `outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv`
- `state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv`
- `outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv`
- `outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md`
- `outputs/v18/read_center/V18_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN.md`

## Warnings
- NONE

## Output Files
- Current report: `outputs/v18/read_center/V18_CURRENT_UNIVERSE_TO_CANDIDATE_AUDIT.md`
- Detail CSV: `outputs/v18/ops/V18_35A_UNIVERSE_TO_CANDIDATE_DIFF_DETAIL.csv`
- Summary CSV: `outputs/v18/ops/V18_35A_UNIVERSE_TO_CANDIDATE_DIFF_SUMMARY.csv`

## Final Conclusion
这是解释性审计，不改变任何交易/排名/冻结逻辑。
`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.
