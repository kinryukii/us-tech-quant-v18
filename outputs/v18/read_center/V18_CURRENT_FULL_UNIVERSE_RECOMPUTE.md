# V18.35D 全总池真实因子/技术/排名重算

- STATUS: `FAIL_V18_35D_FULL_UNIVERSE_RECOMPUTE_FAILED`
- RUN_ID: `V18_35D_20260530_221348`
- GENERATED_AT: `2026-05-30T22:13:48`

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
- targeted stale retry attempted/success/still stale: `0` / `0` / `0`
- targeted stale retry still stale tickers: ``
- 总池数量: `323`
- 实际尝试计算数量: `323`
- price data available/missing: `318` / `5`
- factor success/failure: `317` / `6`
- technical success/failure: `317` / `6`
- ranking merge success/failure: `317` / `6`
- rank eligible/ineligible: `317` / `6`
- apply executed: `TRUE`
- backup path: `NONE`
- expected freeze not expanded yet: `FALSE`

## Failure Buckets
| bucket | count |
| --- | ---: |
| `UNAVAILABLE_PRICE_DATA_EXCLUDED` | 5 |
| `PRICE_HISTORY_INSUFFICIENT` | 1 |

## Failed Ticker Samples
| ticker | bucket | reason |
| --- | --- | --- |
| `CDTX` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `CFLT` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `COG` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `JFROG` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `MPW` | `UNAVAILABLE_PRICE_DATA_EXCLUDED` | yfinance returned empty data |
| `TQQQ` | `PRICE_HISTORY_INSUFFICIENT` | price history rows 2 < 120 |

## Top 20 Recomputed Candidates
| rank | ticker | score | latest_price_date |
| ---: | --- | ---: | --- |
| 1 | `VIAV` | 54.718958 | 2026-05-29 |
| 2 | `BW` | 53.81616 | 2026-05-29 |
| 3 | `AEHR` | 52.78576 | 2026-05-29 |
| 4 | `INTC` | 52.707467 | 2026-05-29 |
| 5 | `SITM` | 50.963459 | 2026-05-29 |
| 6 | `FORM` | 50.70911 | 2026-05-29 |
| 7 | `TSEM` | 50.644541 | 2026-05-29 |
| 8 | `LITE` | 50.488231 | 2026-05-29 |
| 9 | `WOLF` | 49.698107 | 2026-05-29 |
| 10 | `BE` | 49.565227 | 2026-05-29 |
| 11 | `POWL` | 49.46505 | 2026-05-29 |
| 12 | `ACLS` | 48.727715 | 2026-05-29 |
| 13 | `AMKR` | 48.306825 | 2026-05-29 |
| 14 | `MTZ` | 48.293852 | 2026-05-29 |
| 15 | `VECO` | 46.907178 | 2026-05-29 |
| 16 | `PUMP` | 46.334602 | 2026-05-29 |
| 17 | `ICHR` | 46.293189 | 2026-05-29 |
| 18 | `VRT` | 46.267654 | 2026-05-29 |
| 19 | `COHR` | 46.189931 | 2026-05-29 |
| 20 | `TTMI` | 45.941409 | 2026-05-29 |

## Operator Next Action
- 若 rank_ineligible 仍较多，先补 price_cache/full history，再重跑本步骤。
- 如 apply 后 full candidates 大于 freeze count，这是预期状态：本任务不扩展 freeze ledger。
- freeze 扩展需要单独任务和备份策略。

## Final Conclusion
All total universe tickers were attempted.
No fake scores were created.
No trading/order/account/freeze logic was modified.
`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.
