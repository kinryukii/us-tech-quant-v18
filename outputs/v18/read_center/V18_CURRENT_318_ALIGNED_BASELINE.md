# V18.35H 318 对齐稳定快照

- STATUS: `OK_V18_35H_STABLE_SNAPSHOT_318_ALIGNED_READY`
- RUN_ID: `V18_35H_20260525_144305`
- SNAPSHOT_PATH: `D:/us-tech-quant/archive/stable/V18_35H_318_aligned_universe_candidate_freeze_20260525_144305`

## 说明
V18.35A-G 已经把 active universe、current candidates、latest freeze 和 rank eligible 全部对齐到 318，并清理了 15 个无效 ticker。
旧的 2026-05-22 / 252 freeze 历史仍保留在 ledger 中，新的 318 baseline 已经成为当前稳定快照参考。

## Count Summary
| item | value |
| --- | ---: |
| total universe | 318 |
| current full candidates | 318 |
| current ranked candidates | 318 |
| current top candidates | 20 |
| latest signal freeze | 318 |
| rank eligible | 318 |
| rank ineligible | 0 |
| remaining uncomputed | 0 |
| new recomputed not in freeze | 0 |
| duplicate universe tickers | 0 |
| duplicate candidate tickers | 0 |
| duplicate latest signal_date+ticker | 0 |

## Validation
| check | status | detail |
| --- | --- | --- |
| TOTAL_UNIVERSE_COUNT_318 | `PASS` | 318 |
| CURRENT_FULL_CANDIDATE_COUNT_318 | `PASS` | 318 |
| CURRENT_RANKED_CANDIDATE_COUNT_318 | `PASS` | 318 |
| CURRENT_TOP_CANDIDATE_COUNT_20 | `PASS` | 20 |
| LATEST_SIGNAL_FREEZE_COUNT_318 | `PASS` | 318 |
| RANK_ELIGIBLE_COUNT_318 | `PASS` | 318 |
| RANK_INELIGIBLE_COUNT_0 | `PASS` | 0 |
| REMAINING_UNCOMPUTED_COUNT_0 | `PASS` | 0 |
| NEW_RECOMPUTED_NOT_IN_FREEZE_0 | `PASS` | 0 |
| DUPLICATE_UNIVERSE_TICKER_COUNT_0 | `PASS` | 0 |
| DUPLICATE_CANDIDATE_TICKER_COUNT_0 | `PASS` | 0 |
| DUPLICATE_LATEST_SIGNAL_DATE_TICKER_COUNT_0 | `PASS` | 0 |
| AUTO_TRADE_DISABLED | `PASS` | DISABLED |
| AUTO_SELL_DISABLED | `PASS` | DISABLED |
| OFFICIAL_DECISION_IMPACT_NONE | `PASS` | NONE |
| FORBIDDEN_MODIFIED_FALSE | `PASS` | FALSE |

## Archive
- Snapshot path: `D:/us-tech-quant/archive/stable/V18_35H_318_aligned_universe_candidate_freeze_20260525_144305`
- Restore script: `D:/us-tech-quant/archive/stable/V18_35H_318_aligned_universe_candidate_freeze_20260525_144305/RESTORE_V18_35H.ps1`

## Operator Next Action
- Keep this snapshot as the baseline for V18.36A paper trading / forward attribution work.
- If a restore is ever needed, run the restore script from the snapshot root and then re-run the V18.35 validation chain.

## Final Conclusion
这是进入 paper trading 前的稳定封存。
No trading/order/account logic was modified.
AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.
