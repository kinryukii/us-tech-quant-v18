# V18.43B TopN Explainer Operator Note

## 1. READ_FIRST 文件怎么区分

- `outputs\v18\ops\V18_43A_READ_FIRST.txt` 表示最近一次 V18.43A 运行。
- 最近一次运行可能是正式 TopN 20，也可能是小样本测试，例如 `-TopN 5`。
- 因此它适合看“刚刚这次命令”的状态。

## 2. 每日 operator 应该优先看 current 文件

每日正式操作请优先看：

- `outputs\v18\ops\V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt`
- `outputs\v18\read_center\V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`
- `outputs\v18\ops\V18_CURRENT_TOPN_RANKING_DRIVER_MATRIX.csv`
- `outputs\v18\ops\V18_CURRENT_TOPN_CLOSE_RANK_GAPS.csv`

这些 `V18_CURRENT_TOPN_*` 文件只会在使用 `-WriteCurrent` 时更新。

## 3. 小 TopN 测试不会覆盖 current aliases

例如：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_43A_topn_ranking_explainer_packet.ps1" -TopN 5 -NeighborWindow 1
```

这会更新版本化文件：

- `outputs\v18\ops\V18_43A_READ_FIRST.txt`
- `outputs\v18\read_center\V18_43A_TOPN_RANKING_EXPLAINER_PACKET.md`

但不会更新：

- `outputs\v18\ops\V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt`
- `outputs\v18\read_center\V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`

## 4. 正式 TopN 当前报告命令

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_43A_topn_ranking_explainer_packet.ps1" -TopN 20 -NeighborWindow 2 -WriteCurrent -IncludeSingleTickerHints
```

## 5. 安全说明

- This patch does not change ranking logic.
- It does not change factor weights.
- It does not modify candidate files.
- It does not modify signal freeze ledger.
- It does not call broker APIs.
- It does not allow order execution.
- `AUTO_TRADE` remains `DISABLED`.
- `AUTO_SELL` remains `DISABLED`.
- `TRADING_EXECUTION_ALLOWED` remains `FALSE`.
