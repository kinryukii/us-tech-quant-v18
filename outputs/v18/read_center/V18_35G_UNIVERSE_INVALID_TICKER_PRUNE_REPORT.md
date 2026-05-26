# V18.35G 无效 ticker 清理 / active universe 修正

- STATUS: `OK_V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_READY`
- RUN_ID: `V18_35G_20260525_141052`

## 说明
V18.35E 后剩余 15 个无法计算 ticker 已由用户确认可以从当前 active universe 中剔除。目标是让 active universe 与当前 full candidates 318 对齐，减少后续重算中的无效失败项。
- 明显脏数字 token: `0`, `105`, `20`, `250`, `252`, `303`, `318`, `325`
- 明显表头 token: `TICKER`, `TICKERS`
- 用户确认不再研究的无法计算 ticker: `CDTX`, `CFLT`, `COG`, `JFROG`, `MPW`

## Count Summary
| item | value |
| --- | ---: |
| target exclusion count | 15 |
| found in active universe | 15 |
| applied exclusion count | 15 |
| total universe before | 333 |
| total universe after | 318 |
| current full candidates | 318 |
| latest freeze | 318 |

## Target Detail
| ticker | reason | in universe before | in candidates | in freeze | validation |
| --- | --- | --- | --- | --- | --- |
| `0` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `105` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `20` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `250` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `252` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `303` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `318` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `325` | `INVALID_NUMERIC_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `TICKER` | `INVALID_HEADER_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `TICKERS` | `INVALID_HEADER_TOKEN` | TRUE | FALSE | FALSE | `PASS` |
| `CDTX` | `USER_CONFIRMED_REMOVE_UNCOMPUTED_TICKER` | TRUE | FALSE | FALSE | `PASS` |
| `CFLT` | `USER_CONFIRMED_REMOVE_UNCOMPUTED_TICKER` | TRUE | FALSE | FALSE | `PASS` |
| `COG` | `USER_CONFIRMED_REMOVE_UNCOMPUTED_TICKER` | TRUE | FALSE | FALSE | `PASS` |
| `JFROG` | `USER_CONFIRMED_REMOVE_UNCOMPUTED_TICKER` | TRUE | FALSE | FALSE | `PASS` |
| `MPW` | `USER_CONFIRMED_REMOVE_UNCOMPUTED_TICKER` | TRUE | FALSE | FALSE | `PASS` |

## Safety
- apply used: `TRUE`
- backup path: `D:\us-tech-quant\archive\v18\universe_invalid_ticker_prune_backups\V18_35G_20260525_141052`
- freeze ledger 不修改，因为 V18.35F 已经冻结 318 候选，本任务只修正 active universe 来源。
- candidate/ranking/factor 文件不修改；本任务只读它们用于验证。

## Operator Next Action
- apply 后重跑 V18.35D/E/A，确认 total universe 约 318、rank eligible 约 318、freeze/candidates 仍匹配。
- 后续 universe 构建若再次引入这些 token，应检查上游 CSV/header/数字污染来源。

## Final Conclusion
Active universe invalid ticker cleanup completed or previewed.
Freeze ledger was not modified.
Candidate/ranking/factor logic was not modified.
AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.
