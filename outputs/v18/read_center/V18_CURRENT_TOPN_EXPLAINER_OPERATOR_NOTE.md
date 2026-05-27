# V18.43B TopN Explainer Operator Note

## 每日优先看 current 文件

- `outputs\v18\ops\V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt`
- `outputs\v18\read_center\V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`
- `outputs\v18\ops\V18_CURRENT_TOPN_RANKING_DRIVER_MATRIX.csv`
- `outputs\v18\ops\V18_CURRENT_TOPN_CLOSE_RANK_GAPS.csv`

## 文件含义

- `V18_43A_READ_FIRST.txt` 是最近一次运行，可能是测试。
- `V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt` 是最近一次 current/operator run。
- 不带 `-WriteCurrent` 的小 TopN 测试不会覆盖 current aliases。

## 正式命令

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_43A_topn_ranking_explainer_packet.ps1" -TopN 20 -NeighborWindow 2 -WriteCurrent -IncludeSingleTickerHints
```

## 安全说明

V18.43B 不改变排名、权重、候选池、freeze ledger、交易逻辑或账户状态。
