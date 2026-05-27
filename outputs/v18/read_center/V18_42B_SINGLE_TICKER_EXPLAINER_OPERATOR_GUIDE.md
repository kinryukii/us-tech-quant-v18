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

说明：

- `-Ticker "VIAV"`：要解释的 ticker。
- `-NeighborWindow 3`：显示目标前后各 3 名。
- `-WriteCurrent`：当 ticker 存在时，更新 `V18_CURRENT_*` 当前解释器别名。

## 3. 推荐读取文件

- `outputs\v18\ops\V18_42A_READ_FIRST.txt`
- `outputs\v18\read_center\V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md`
- `outputs\v18\ops\V18_CURRENT_SINGLE_TICKER_RANKING_ATTRIBUTION.csv`
- `outputs\v18\ops\V18_CURRENT_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv`
- `outputs\v18\ops\V18_CURRENT_SINGLE_TICKER_INPUT_PROVENANCE.csv`

## 4. 怎么理解状态

- `OK_V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_READY`
  - ticker 已找到，核心排名文件可读，报告已生成。

- `WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL`
  - ticker 已找到，核心解释可用，但部分 supporting/provenance 文件缺失或不可读。
  - 这不是交易阻塞，也不代表排名错误。

- `WARN_V18_42A_SINGLE_TICKER_NOT_FOUND`
  - ticker 不在当前 ranked candidate pool 中。
  - 非 strict 模式不会崩溃，会写版本化报告，并给出 close matches / 当前 top candidates。

- `FAIL_V18_42A_NO_RANKING_SOURCE`
  - 找不到可用的当前排名候选池文件。
  - 这是核心输入失败。

- `FAIL_V18_42A_TICKER_NOT_FOUND_STRICT`
  - strict 模式下 ticker 不存在。
  - 这会返回非零退出码。

## 5. 怎么理解 CURRENT_ALIAS_WRITTEN

- `CURRENT_ALIAS_WRITTEN: TRUE`
  - 当前 report alias 代表本次请求的真实 ticker。

- `CURRENT_ALIAS_WRITTEN: FALSE` 且 `CURRENT_ALIAS_SKIP_REASON: TICKER_NOT_FOUND`
  - 本次请求 ticker 不存在。
  - V18.42B 之后，缺失 ticker 测试不会覆盖 `V18_CURRENT_*` 当前解释器别名。
  - 这是有意的安全保护，避免当前报告被 fake/missing ticker 验证结果污染。

- 如需恢复旧行为，必须显式使用 override：

```powershell
-AllowCurrentMissingOverwrite
```

正常操作不建议使用该 override。

## 6. 注意事项

- This tool does not recalculate official rank.
- It reads existing current ranking output.
- It does not invent factor weights.
- If weight metadata is missing, attribution is descriptive only.
- KDJ/MACD remains shadow-only unless proven by official ranking input.
- This tool does not allow trading execution.
- `AUTO_TRADE` 始终为 `DISABLED`。
- `AUTO_SELL` 始终为 `DISABLED`。
- `BROKER_API_USED` 为 `FALSE`。
- `ORDER_EXECUTION_USED` 为 `FALSE`。
