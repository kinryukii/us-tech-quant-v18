# V18.35D 全总池真实因子/技术/排名重算

- STATUS: `WARN_V18_35D_FULL_UNIVERSE_RECOMPUTE_REVIEW_NEEDED`
- RUN_ID: `V18_35D_20260525_141107`
- GENERATED_AT: `2026-05-25T14:11:07`

## 说明
这不是单纯把 ticker 放进列表，而是对全部 total universe ticker 尝试真实计算。
`calculation_attempted=TRUE` 表示该 ticker 已进入计算尝试；`rank_eligible=TRUE` 表示 factor 和 technical 都成功并完成 ranking merge。
缺价格或历史数据的 ticker 不会被伪造分数，只会写入失败原因。

## 汇总
- 总池数量: `318`
- 实际尝试计算数量: `318`
- price data available/missing: `318` / `0`
- factor success/failure: `318` / `0`
- technical success/failure: `318` / `0`
- ranking merge success/failure: `318` / `0`
- rank eligible/ineligible: `318` / `0`
- apply executed: `FALSE`
- backup path: `NONE`
- expected freeze not expanded yet: `FALSE`

## Failure Buckets
| bucket | count |
| --- | ---: |

## Failed Ticker Samples
| ticker | bucket | reason |
| --- | --- | --- |

## Top 20 Recomputed Candidates
| rank | ticker | score | latest_price_date |
| ---: | --- | ---: | --- |
| 1 | `FORM` | 59.2 | 2026-05-18 |
| 2 | `AEIS` | 58.86 | 2026-05-20 |
| 3 | `AGX` | 57.4 | 2026-05-20 |
| 4 | `BLTE` | 57.324 | 2026-05-20 |
| 5 | `LITE` | 57.02 | 2026-05-18 |
| 6 | `ALM` | 56.892 | 2026-05-20 |
| 7 | `POWL` | 56.64 | 2026-05-18 |
| 8 | `MTZ` | 56.632 | 2026-05-20 |
| 9 | `MOD` | 54.352 | 2026-05-18 |
| 10 | `OC` | 53.908 | 2026-05-20 |
| 11 | `MU` | 53.856 | 2026-05-18 |
| 12 | `CAMT` | 53.544 | 2026-05-18 |
| 13 | `SOXL` | 53.476 | 2026-05-18 |
| 14 | `CLH` | 53.048 | 2026-05-20 |
| 15 | `AMKR` | 52.828 | 2026-05-18 |
| 16 | `KEYS` | 52.504 | 2026-05-18 |
| 17 | `AEHR` | 52.116 | 2026-05-18 |
| 18 | `VIAV` | 51.800559 | 2026-05-21 |
| 19 | `ICHR` | 51.732 | 2026-05-18 |
| 20 | `COHU` | 51.684 | 2026-05-18 |

## Operator Next Action
- 若 rank_ineligible 仍较多，先补 price_cache/full history，再重跑本步骤。
- 如 apply 后 full candidates 大于 freeze count，这是预期状态：本任务不扩展 freeze ledger。
- freeze 扩展需要单独任务和备份策略。

## Final Conclusion
All total universe tickers were attempted.
No fake scores were created.
No trading/order/account/freeze logic was modified.
`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.
