# V18.35E 在线补数据与重算候选接管桥接

- STATUS: `WARN_V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_REVIEW_NEEDED`
- RUN_ID: `V18_35E_20260530_222519`
- GENERATED_AT: `2026-05-30T22:25:19`

## 说明
V18.35D 本地重算结果为 total universe 332、attempted 332、rank eligible 303、failed 29。本步骤继续针对 V18.35D 失败 ticker 做在线补数据验证，并桥接新的 full-universe recomputed candidates 与最新 freeze set。
- 本次是否使用 yfinance/online backfill: `FALSE`
- 是否 apply 到 current full candidate aliases: `TRUE`
- freeze ledger 本任务不修改；freeze 扩展需要单独 review 和独立任务。

## Online Backfill Summary
| metric | value |
| --- | ---: |
| target tickers | 1 |
| attempted | 0 |
| success | 0 |
| failed | 1 |

## Recompute Before/After Count Comparison
| item | count |
| --- | ---: |
| V18.35D local rank eligible | 317 |
| V18.35E rank eligible after backfill | 317 |
| latest freeze | 318 |
| new recomputed not in freeze | 0 |

## Adoption Bucket Counts
| bucket | count |
| --- | ---: |
| `EXISTING_FREEZE_AND_RECOMPUTED_OK` | 317 |
| `TOTAL_UNIVERSE_ONLY` | 12 |
| `STILL_UNCOMPUTED_AFTER_BACKFILL` | 5 |
| `EXISTING_FREEZE_BUT_RECOMPUTE_MISSING` | 1 |

## Next Freeze Ready Samples
| rank | ticker | score | bucket |
| ---: | --- | ---: | --- |

## Remaining Failure Bucket Counts
| bucket | count |
| --- | ---: |
| `PRICE_DATA_UNAVAILABLE` | 17 |
| `PRICE_HISTORY_INSUFFICIENT` | 1 |

## Remaining Failure Samples
| ticker | bucket | reason |
| --- | --- | --- |
| `0` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `105` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `11` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `20` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `250` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `252` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `303` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `318` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `325` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `CDTX` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `CFLT` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `COG` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `JFROG` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `MPW` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `TICKER` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `TICKERS` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |
| `TQQQ` | `PRICE_HISTORY_INSUFFICIENT` | price history rows 1 < 120 |
| `TRUE` | `PRICE_DATA_UNAVAILABLE` | price cache file missing |

## Operator Next Action
- 先检查 `V18_35E_NEXT_FREEZE_READINESS_CANDIDATES.csv`，确认新增 recomputed candidates 是否进入下一次 freeze review。
- 对仍无法计算的 ticker，优先补完整价格历史或手工核验退市/改名/不可交易状态。
- V18.35A 仍可能使用 freeze-matched 252 source selection；这是预期限制，不在本任务中修改。

## Final Conclusion
Online backfill and recompute bridge completed.
No fake scores were created.
Freeze ledger was not modified.
No trading/order/account logic was modified.
AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.
