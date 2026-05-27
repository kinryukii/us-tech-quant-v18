# V18.42B 单票评分/排名解释器操作指南

## 1. 这个工具解决什么问题

V18.42A/V18.42B 单票解释器用于人工检查某一只股票在当前候选池中的排名和分数。

- 看某只股票为什么是这个分数。
- 看它为什么排在当前名次。
- 看它和前后名候选差在哪里。
- 看哪些字段是 `OFFICIAL_RANKING_INPUT`，哪些只是 `SUPPORTING_CONTEXT`、`SHADOW_ONLY` 或 `PROVENANCE_ONLY`。

该工具只读取现有输出，不重算排名，不改候选池。

## 2. 每日怎么使用

推荐命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "VIAV" -NeighborWindow 3 -WriteCurrent
```

## 3. 推荐读取文件

- `outputs\v18\ops\V18_42A_READ_FIRST.txt`
- `outputs\v18\read_center\V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md`
- `outputs\v18\ops\V18_CURRENT_SINGLE_TICKER_RANKING_ATTRIBUTION.csv`
- `outputs\v18\ops\V18_CURRENT_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv`
- `outputs\v18\ops\V18_CURRENT_SINGLE_TICKER_INPUT_PROVENANCE.csv`

## 4. 怎么理解状态

- `OK_V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_READY`: ticker 已找到，报告已生成。
- `WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL`: ticker 已找到，但部分 supporting/provenance 文件缺失。
- `WARN_V18_42A_SINGLE_TICKER_NOT_FOUND`: ticker 不在当前候选池中，非 strict 模式不会崩溃。
- `FAIL_V18_42A_NO_RANKING_SOURCE`: 找不到可用排名源。
- `FAIL_V18_42A_TICKER_NOT_FOUND_STRICT`: strict 模式下 ticker 不存在。

## 5. 怎么理解 CURRENT_ALIAS_WRITTEN

- `TRUE` 表示当前 report alias 代表本次请求的真实 ticker。
- `FALSE` 且 `TICKER_NOT_FOUND` 表示缺失 ticker 测试没有覆盖当前别名。
- V18.42B 后这是默认安全行为。

## 6. 注意事项

- This tool does not recalculate official rank.
- It does not invent factor weights.
- Attribution is descriptive only when weight metadata is missing.
- KDJ/MACD remains shadow-only unless proven by official ranking input.
- This tool does not allow trading execution.
