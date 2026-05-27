# V18.35D 全总池真实因子/技术/排名重算

- STATUS: `WARN_V18_35D_FULL_UNIVERSE_RECOMPUTE_REVIEW_NEEDED`
- RUN_ID: `V18_35D_20260527_234138`
- GENERATED_AT: `2026-05-27T23:41:38`

## 说明
这不是单纯把 ticker 放进列表，而是对全部 total universe ticker 尝试真实计算。
`calculation_attempted=TRUE` 表示该 ticker 已进入计算尝试；`rank_eligible=TRUE` 表示 factor 和 technical 都成功并完成 ranking merge。
缺价格或历史数据的 ticker 不会被伪造分数，只会写入失败原因。

## 汇总
- raw universe token count: `335`
- sanitized universe count: `323`
- invalid pseudo ticker count: `0`
- invalid pseudo tickers: ``
- universe source rejected token count: `12`
- universe source rejected token sample: `0, 105, 11, 20, 250, 252, 303, 318, 325, TICKER, TICKERS, TRUE`
- yfinance failed ticker count raw: `5`
- yfinance failed tickers: `CDTX, CFLT, COG, JFROG, MPW`
- price unavailable excluded count: `5`
- price unavailable excluded tickers: `CDTX, CFLT, COG, JFROG, MPW`
- current price refresh blocking failed ticker count: `0`
- targeted stale retry attempted/success/still stale: `18` / `0` / `18`
- targeted stale retry still stale tickers: `AGX, ALM, BW, HTZ, HUT, MOH, MTSI, MTZ, OLPX, PLUG, PUMP, SITM, STM, TSEM, TTMI, TWLO, VIAV, WOLF`
- 总池数量: `323`
- 实际尝试计算数量: `323`
- price data available/missing: `318` / `5`
- factor success/failure: `318` / `5`
- technical success/failure: `318` / `5`
- ranking merge success/failure: `318` / `5`
- rank eligible/ineligible: `318` / `5`
- apply executed: `TRUE`
- backup path: `D:\us-tech-quant\archive\v18\full_universe_recompute_backups\V18_35D_20260527_234138`
- expected freeze not expanded yet: `FALSE`

## Failure Buckets
| bucket | count |
| --- | ---: |
| `UNAVAILABLE_PRICE_DATA_EXCLUDED` | 5 |

## Failed Ticker Samples
| ticker | bucket | reason |
| --- | --- | --- |
| `CDTX` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `CFLT` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `COG` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `JFROG` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `MPW` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |

## Top 20 Recomputed Candidates
| rank | ticker | score | latest_price_date |
| ---: | --- | ---: | --- |
| 1 | `KEYS` | 57.456 | 2026-05-26 |
| 2 | `VRT` | 57.4 | 2026-05-26 |
| 3 | `ICHR` | 56.64 | 2026-05-26 |
| 4 | `NVDA` | 54.62 | 2026-05-26 |
| 5 | `D` | 53.916 | 2026-05-26 |
| 6 | `AMKR` | 53.592 | 2026-05-26 |
| 7 | `GOOGL` | 53.476 | 2026-05-26 |
| 8 | `FIX` | 53.096 | 2026-05-26 |
| 9 | `MCHP` | 52.448 | 2026-05-26 |
| 10 | `LITE` | 52.332 | 2026-05-26 |
| 11 | `VIAV` | 51.800559 | 2026-05-21 |
| 12 | `CARR` | 51.684 | 2026-05-26 |
| 13 | `ENTG` | 51.572 | 2026-05-26 |
| 14 | `SITM` | 51.403528 | 2026-05-21 |
| 15 | `CRWV` | 50.924 | 2026-05-26 |
| 16 | `ETR` | 50.544 | 2026-05-26 |
| 17 | `TSEM` | 50.428133 | 2026-05-21 |
| 18 | `COHU` | 50.428 | 2026-05-26 |
| 19 | `HUT` | 49.710963 | 2026-05-20 |
| 20 | `GEV` | 49.668 | 2026-05-26 |

## Operator Next Action
- 若 rank_ineligible 仍较多，先补 price_cache/full history，再重跑本步骤。
- 如 apply 后 full candidates 大于 freeze count，这是预期状态：本任务不扩展 freeze ledger。
- freeze 扩展需要单独任务和备份策略。

## Final Conclusion
All total universe tickers were attempted.
No fake scores were created.
No trading/order/account/freeze logic was modified.
`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.
