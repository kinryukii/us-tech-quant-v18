# V17.6E Screened Universe Latest Price Audit

生成时间：2026-05-27 22:47:44

## 1. 结论

- AUDIT_STATUS: `WARN_MIXED_PRICE_DATES`
- SCREENED_UNIVERSE_COUNT: `105`
- SECOND_STAGE_COUNT: `20`
- PRICE_OK_COUNT: `105`
- PRICE_FAIL_COUNT: `0`
- MIN_LATEST_PRICE_DATE: `2026-05-26`
- MAX_LATEST_PRICE_DATE: `2026-05-27`

## 2. latest_price_date 分布

| latest_price_date | count |
|---|---:|
| 2026-05-26 | 1 |
| 2026-05-27 | 104 |

## 3. 第二阶段候选

| ticker | latest_price_date | latest_close | freshness_status |
|---|---:|---:|---|
| AAPL | 2026-05-27 | 311.08 | OK_LATEST_AVAILABLE |
| ACLS | 2026-05-27 | 160.475 | OK_LATEST_AVAILABLE |
| ACM | 2026-05-27 | 72.46 | OK_LATEST_AVAILABLE |
| ACMR | 2026-05-27 | 84.48 | OK_LATEST_AVAILABLE |
| AEHR | 2026-05-27 | 105.02 | OK_LATEST_AVAILABLE |
| ALAB | 2026-05-27 | 306.14 | OK_LATEST_AVAILABLE |
| AMAT | 2026-05-27 | 445.24 | OK_LATEST_AVAILABLE |
| AMD | 2026-05-27 | 491.32 | OK_LATEST_AVAILABLE |
| AMKR | 2026-05-27 | 71.28 | OK_LATEST_AVAILABLE |
| AMZN | 2026-05-27 | 267.69 | OK_LATEST_AVAILABLE |
| ANET | 2026-05-27 | 154.615 | OK_LATEST_AVAILABLE |
| APH | 2026-05-27 | 138.95 | OK_LATEST_AVAILABLE |
| ARM | 2026-05-27 | 309.6 | OK_LATEST_AVAILABLE |
| ASML | 2026-05-27 | 1600.0 | OK_LATEST_AVAILABLE |
| AVGO | 2026-05-27 | 423.67 | OK_LATEST_AVAILABLE |
| BE | 2026-05-27 | 286.0224 | OK_LATEST_AVAILABLE |
| BTDR | 2026-05-27 | 14.371 | OK_LATEST_AVAILABLE |
| CAMT | 2026-05-27 | 169.075 | OK_LATEST_AVAILABLE |
| CARR | 2026-05-27 | 65.595 | OK_LATEST_AVAILABLE |
| CEG | 2026-05-27 | 292.995 | OK_LATEST_AVAILABLE |

## 4. 输出文件

- SCREENED TICKERS: `D:\us-tech-quant\outputs\v17\price\v17_6E_screened_universe_tickers.csv`
- SECOND STAGE TICKERS: `D:\us-tech-quant\outputs\v17\price\v17_6E_second_stage_tickers.csv`
- LATEST PRICES: `D:\us-tech-quant\outputs\v17\price\v17_6E_screened_universe_latest_prices.csv`
- STATE PRICE SNAPSHOT: `D:\us-tech-quant\state\v17_6E_screened_universe_latest_price_snapshot.csv`
- REPORT: `D:\us-tech-quant\outputs\v17\price\V17_6E_SCREENED_UNIVERSE_LATEST_PRICE_AUDIT.md`

## 5. 下一步

如果 AUDIT_STATUS 为 OK，则下一步 V17.6F 可以把手动 daily 入口改成：

全量链路 → screened universe 66 只 → 最新价格 → second stage candidate → 操作建议。

如果不是 OK，则不允许生成买入建议。