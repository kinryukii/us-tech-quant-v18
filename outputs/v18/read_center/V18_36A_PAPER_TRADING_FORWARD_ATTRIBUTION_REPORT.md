# V18.36A 模拟交易与前向归因基线

## 运行结论

V18.35H 之后，系统已经形成 318 对齐基线；本步骤开始建立 paper trading 和 forward attribution 的观察层。这里不是实盘交易，不创建真实买卖建议，不发送订单，也不修改 broker/API/account/trading execution 逻辑。

| 项目 | 数值 |
|---|---:|
| latest signal date | 2026-05-25 |
| latest freeze count | 318 |
| current full candidates | 318 |
| current top candidates | 20 |
| paper entries | 488 |
| entry price available | 488 |
| entry price missing | 0 |
| paper ledger updated | FALSE |

## Paper Portfolio

| portfolio | entries | capital | commission bps | slippage bps |
|---|---:|---:|---:|---:|
| TOP20_EQUAL_WEIGHT | 20 | 100000 | 1.0 | 5.0 |
| TOP50_EQUAL_WEIGHT | 50 | 100000 | 1.0 | 5.0 |
| TOP100_EQUAL_WEIGHT | 100 | 100000 | 1.0 | 5.0 |
| FULL318_EQUAL_WEIGHT_OBSERVATION | 318 | 100000 | 1.0 | 5.0 |

组合按 Top20 / Top50 / Top100 / Full318 observation 等权构建；不加杠杆，不做空，模拟层允许 fractional shares。默认资金为 100000 USD，成本假设为 commission 1.0 bps + slippage 5.0 bps。

## Forward Horizon 可填充状态

| horizon | fillable rows | pending rows |
|---|---:|---:|
| 1D | 0 | 488 |
| 3D | 0 | 488 |
| 5D | 0 | 488 |
| 10D | 0 | 488 |
| 20D | 0 | 488 |

如果本地未来价格还没有覆盖对应 horizon，状态会保持 PENDING_FUTURE_PRICE，不会伪造价格或收益。

## Benchmark

| benchmark | availability |
|---|---|
| SPY | AVAILABLE |
| QQQ | AVAILABLE |

## Top 20 Entry Sample

| ticker | rank | score | entry price | entry status |
|---|---:|---:|---:|---|
| FORM | 1 | 59.2 | 126.434998 | ENTRY_PRICE_STALE_WARNING |
| AEIS | 2 | 58.86 | 313.049988 | ENTRY_PRICE_STALE_WARNING |
| AGX | 3 | 57.4 | 630.5 | ENTRY_PRICE_STALE_WARNING |
| BLTE | 4 | 57.324 | 143.360001 | ENTRY_PRICE_STALE_WARNING |
| LITE | 5 | 57.02 | 977.669983 | ENTRY_PRICE_STALE_WARNING |
| ALM | 6 | 56.892 | 17.639999 | ENTRY_PRICE_STALE_WARNING |
| POWL | 7 | 56.64 | 289.290009 | ENTRY_PRICE_STALE_WARNING |
| MTZ | 8 | 56.632 | 384.209991 | ENTRY_PRICE_STALE_WARNING |
| MOD | 9 | 54.352 | 275.799988 | ENTRY_PRICE_STALE_WARNING |
| OC | 10 | 53.908 | 113.43 | ENTRY_PRICE_STALE_WARNING |
| MU | 11 | 53.856 | 735.75 | ENTRY_PRICE_STALE_WARNING |
| CAMT | 12 | 53.544 | 170.535004 | ENTRY_PRICE_STALE_WARNING |
| SOXL | 13 | 53.476 | 169.009995 | ENTRY_PRICE_STALE_WARNING |
| CLH | 14 | 53.048 | 291.399994 | ENTRY_PRICE_STALE_WARNING |
| AMKR | 15 | 52.828 | 70.860001 | ENTRY_PRICE_STALE_WARNING |
| KEYS | 16 | 52.504 | 351.75 | ENTRY_PRICE_STALE_WARNING |
| AEHR | 17 | 52.116 | 101.184998 | ENTRY_PRICE_STALE_WARNING |
| VIAV | 18 | 51.800559 | 48.98 | ENTRY_PRICE_STALE_WARNING |
| ICHR | 19 | 51.732 | 72.839996 | ENTRY_PRICE_STALE_WARNING |
| COHU | 20 | 51.684 | 46.98 | ENTRY_PRICE_STALE_WARNING |

## Operator Next Action

若仅需要观察，继续使用 preview/report 模式。若要让后续 paper tracking 读取 state/v18/paper_trading/，再显式运行 -UpdatePaperTradingLedger；该模式只写 paper ledger，并会先创建备份。

## Final Conclusion

This is paper trading only. No real orders were created. No broker/API/account/trading execution logic was modified. AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.
