# V18.48A Top20 Options Data Collector Report

V18.48A is data collection only. It does not recommend options trades, does not suggest buying calls or puts, and does not generate order instructions.

## Sources
| metric | value |
| --- | --- |
| CURRENT_TOP20_SOURCE | D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_TOP_RANKED_CANDIDATES.csv |
| TRACKER_SOURCE | D:\us-tech-quant\outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv |
| EVENT_RISK_SOURCE | D:\us-tech-quant\outputs\v18\event_risk\V18_47C_TOP20_EVENT_EARNINGS_RISK.csv |
| SELECTED_TICKER_COUNT | 20 |

## Tickers with options data available
| ticker | rank | tracking_tier | snapshot_contract_count |
| --- | --- | --- | --- |
| KEYS | 1 | TIER_1_CORE | 12 |
| VRT | 2 | TIER_1_CORE | 24 |
| ICHR | 3 | TIER_1_CORE | 10 |
| NVDA | 4 | TIER_1_CORE | 24 |
| D | 5 | TIER_1_CORE | 12 |
| AMKR | 6 | TIER_2_IMPORTANT | 8 |
| GOOGL | 7 | TIER_2_IMPORTANT | 24 |
| FIX | 8 | TIER_2_IMPORTANT | 6 |
| MCHP | 9 | TIER_2_IMPORTANT | 22 |
| LITE | 10 | TIER_2_IMPORTANT | 24 |
| CARR | 11 | TIER_3_OCCASIONAL | 19 |
| ENTG | 12 | TIER_3_OCCASIONAL | 12 |
| CRWV | 13 | TIER_3_OCCASIONAL | 24 |
| ETR | 14 | TIER_3_OCCASIONAL | 10 |
| COHU | 15 | TIER_3_OCCASIONAL | 7 |
| GEV | 16 | TIER_3_OCCASIONAL | 24 |
| FN | 17 | TIER_3_OCCASIONAL | 6 |
| ETN | 18 | TIER_3_OCCASIONAL | 21 |
| HUBB | 19 | TIER_3_OCCASIONAL | 12 |
| POWL | 20 | TIER_3_OCCASIONAL | 12 |

## Tickers with options data unavailable
| ticker | rank | provider_error_type | options_unavailable_reason |
| --- | --- | --- | --- |

## Liquidity distribution
| liquidity_status | count |
| --- | --- |
| GOOD | 88 |
| OK | 113 |
| THIN | 110 |
| UNUSABLE | 2 |

## DTE bucket coverage
| dte_bucket | count |
| --- | --- |
| DTE_21_45 | 44 |
| DTE_45_75 | 110 |
| DTE_76_120 | 105 |
| DTE_7_14 | 54 |

## THIN / UNUSABLE option liquidity
| ticker | expiration_date | option_type | strike | moneyness_target | liquidity_status | bid_ask_spread_pct | open_interest | volume |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KEYS | 2026-07-17 | CALL | 340.0 | DTE_45_75_ATM | THIN | 0.1155 | 19.0 | 6.0 |
| KEYS | 2026-07-17 | CALL | 370.0 | DTE_45_75_OTM_10PCT | THIN | 0.2667 | 127.0 | 1.0 |
| KEYS | 2026-09-18 | CALL | 340.0 | DTE_76_120_ATM | THIN | 0.0777 | 9.0 | 1.0 |
| KEYS | 2026-09-18 | CALL | 360.0 | DTE_76_120_OTM_5PCT | THIN | 0.0965 | 7.0 | 1.0 |
| KEYS | 2026-09-18 | PUT | 340.0 | DTE_76_120_ATM | THIN | 0.0669 | 1.0 | 1.0 |
| VRT | 2026-07-02 | CALL | 345.0 | DTE_21_45_OTM_10PCT | THIN | 0.2262 | 3.0 | 3.0 |
| VRT | 2026-07-02 | PUT | 315.0 | DTE_21_45_ATM | THIN | 0.1250 | 9.0 | 2.0 |
| VRT | 2026-07-02 | PUT | 285.0 | DTE_21_45_OTM_10PCT | THIN | 0.3111 | 18.0 | 1.0 |
| ICHR | 2026-07-17 | CALL | 70.0 | DTE_45_75_ATM | THIN | 0.1702 | 7.0 | 2.0 |
| ICHR | 2026-07-17 | CALL | 75.0 | DTE_45_75_OTM_5PCT | THIN | 0.2345 | 6.0 | 3.0 |
| ICHR | 2026-07-17 | CALL | 77.5 | DTE_45_75_OTM_10PCT | THIN | 0.2677 | 2.0 | 1.0 |
| ICHR | 2026-07-17 | PUT | 65.0 | DTE_45_75_ATM | THIN | 0.1786 | 4.0 | 1.0 |
| ICHR | 2026-08-21 | PUT | 72.5 | DTE_76_120_ATM | THIN | 0.1270 | 1.0 | UNKNOWN |
| ICHR | 2026-08-21 | PUT | 67.5 | DTE_76_120_OTM_5PCT | THIN | 0.1616 | 1.0 | 1.0 |
| ICHR | 2026-08-21 | PUT | 65.0 | DTE_76_120_OTM_10PCT | THIN | 0.2890 | 7.0 | 1.0 |
| D | 2026-07-17 | CALL | 67.5 | DTE_45_75_ATM | THIN | 0.2857 | 885.0 | 27.0 |
| D | 2026-07-17 | CALL | 70.0 | DTE_45_75_OTM_5PCT | THIN | 0.2564 | 3836.0 | 127.0 |
| D | 2026-07-17 | CALL | 72.5 | DTE_45_75_OTM_10PCT | THIN | 0.6667 | 252.0 | 3.0 |
| D | 2026-07-17 | PUT | 62.5 | DTE_45_75_OTM_5PCT | THIN | 0.5600 | 1013.0 | 131.0 |
| D | 2026-07-17 | PUT | 60.0 | DTE_45_75_OTM_10PCT | THIN | 0.5263 | 404.0 | 71.0 |
| D | 2026-09-18 | CALL | 70.0 | DTE_76_120_OTM_5PCT | THIN | 0.3562 | 1520.0 | 7.0 |
| D | 2026-09-18 | PUT | 67.5 | DTE_76_120_ATM | THIN | 0.5060 | 57.0 | 21.0 |
| D | 2026-09-18 | PUT | 62.5 | DTE_76_120_OTM_5PCT | THIN | 0.4789 | 327.0 | 1.0 |
| D | 2026-09-18 | PUT | 60.0 | DTE_76_120_OTM_10PCT | THIN | 0.4545 | 529.0 | 52.0 |
| GOOGL | 2026-06-12 | CALL | 420.0 | DTE_7_14_OTM_10PCT | THIN | 0.4384 | 1671.0 | 263.0 |
| GOOGL | 2026-06-12 | PUT | 340.0 | DTE_7_14_OTM_10PCT | THIN | 0.2857 | 313.0 | 82.0 |
| GOOGL | 2026-07-02 | CALL | 420.0 | DTE_21_45_OTM_10PCT | THIN | 0.2767 | 287.0 | 112.0 |
| GOOGL | 2026-07-02 | PUT | 340.0 | DTE_21_45_OTM_10PCT | THIN | 0.3018 | 38.0 | 122.0 |
| FIX | 2026-07-17 | CALL | 1920.0 | DTE_45_75_OTM_5PCT | THIN | 0.0961 | 7.0 | 3.0 |
| FIX | 2026-07-17 | CALL | 2020.0 | DTE_45_75_OTM_10PCT | THIN | 0.1034 | 7.0 | 1.0 |
| FIX | 2026-07-17 | PUT | 1820.0 | DTE_45_75_ATM | THIN | 0.0685 | 6.0 | 1.0 |
| FIX | 2026-07-17 | PUT | 1740.0 | DTE_45_75_OTM_5PCT | THIN | 0.0906 | 6.0 | 1.0 |
| MCHP | 2026-06-12 | CALL | 95.0 | DTE_7_14_ATM | THIN | 0.3371 | 5.0 | 3.0 |
| MCHP | 2026-06-12 | CALL | 99.0 | DTE_7_14_OTM_5PCT | THIN | 0.6966 | 12.0 | 3.0 |
| MCHP | 2026-06-12 | CALL | 104.0 | DTE_7_14_OTM_10PCT | THIN | 0.9091 | 6.0 | 1.0 |
| MCHP | 2026-06-12 | PUT | 95.0 | DTE_7_14_ATM | THIN | 0.1124 | 15.0 | 5321.0 |
| MCHP | 2026-06-12 | PUT | 90.0 | DTE_7_14_OTM_5PCT | THIN | 0.7200 | 24.0 | 7.0 |
| MCHP | 2026-06-12 | PUT | 85.0 | DTE_7_14_OTM_10PCT | THIN | 0.9091 | 25.0 | 1.0 |
| MCHP | 2026-07-02 | CALL | 99.0 | DTE_21_45_ATM | THIN | 0.6164 | 1.0 | 1.0 |
| MCHP | 2026-07-02 | CALL | 104.0 | DTE_21_45_OTM_10PCT | THIN | 0.7692 | 2.0 | 1.0 |
| MCHP | 2026-07-02 | PUT | 88.0 | DTE_21_45_ATM | THIN | 0.7130 | 1.0 | 1.0 |
| MCHP | 2026-07-02 | PUT | 84.0 | DTE_21_45_OTM_10PCT | THIN | 1.4409 | 7.0 | 7.0 |
| MCHP | 2026-09-18 | CALL | 100.0 | DTE_76_120_OTM_5PCT | THIN | 0.3093 | 1587.0 | 7.0 |
| MCHP | 2026-09-18 | PUT | 85.0 | DTE_76_120_OTM_10PCT | THIN | 0.2727 | 227.0 | 1.0 |
| LITE | 2026-06-12 | CALL | 855.0 | DTE_7_14_ATM | THIN | 0.1510 | 5.0 | 5.0 |
| LITE | 2026-06-12 | CALL | 940.0 | DTE_7_14_OTM_10PCT | THIN | 0.2701 | 18.0 | 19.0 |
| LITE | 2026-07-02 | CALL | 895.0 | DTE_21_45_ATM | THIN | 0.1285 | 5.0 | 2.0 |
| LITE | 2026-07-02 | CALL | 900.0 | DTE_21_45_OTM_5PCT | THIN | 0.1328 | 7.0 | 6.0 |
| LITE | 2026-07-02 | CALL | 940.0 | DTE_21_45_OTM_10PCT | THIN | 0.1623 | 1.0 | 2.0 |
| LITE | 2026-07-02 | PUT | 855.0 | DTE_21_45_ATM | THIN | 0.0949 | 7.0 | 1.0 |
| LITE | 2026-07-02 | PUT | 810.0 | DTE_21_45_OTM_5PCT | THIN | 0.1398 | 3.0 | 4.0 |
| LITE | 2026-07-02 | PUT | 760.0 | DTE_21_45_OTM_10PCT | THIN | 0.1964 | 16.0 | 3.0 |
| CARR | 2026-06-12 | CALL | 64.0 | DTE_7_14_ATM | THIN | 0.1333 | 1.0 | 11.0 |
| CARR | 2026-06-12 | CALL | 67.0 | DTE_7_14_OTM_5PCT | THIN | 0.2500 | 14.0 | 32.0 |
| CARR | 2026-06-12 | CALL | 70.0 | DTE_7_14_OTM_10PCT | THIN | 1.2000 | 16.0 | 1.0 |
| CARR | 2026-06-12 | PUT | 65.0 | DTE_7_14_ATM | THIN | 0.2222 | 4.0 | 1.0 |
| CARR | 2026-06-12 | PUT | 60.0 | DTE_7_14_OTM_5PCT | THIN | 1.5000 | 24.0 | 24.0 |
| CARR | 2026-06-12 | PUT | 57.0 | DTE_7_14_OTM_10PCT | THIN | 1.7143 | 4.0 | 4.0 |
| CARR | 2026-07-02 | CALL | 66.0 | DTE_21_45_ATM | THIN | 1.5942 | 2.0 | UNKNOWN |
| CARR | 2026-07-17 | CALL | 67.5 | DTE_45_75_OTM_5PCT | THIN | 0.4421 | 140.0 | 9.0 |
| CARR | 2026-07-17 | CALL | 70.0 | DTE_45_75_OTM_10PCT | THIN | 0.2759 | 141.0 | 7.0 |
| CARR | 2026-07-17 | PUT | 60.0 | DTE_45_75_OTM_5PCT | THIN | 0.3562 | 32.0 | 5.0 |
| CARR | 2026-07-17 | PUT | 57.5 | DTE_45_75_OTM_10PCT | THIN | 0.5833 | 39.0 | 6.0 |
| CARR | 2026-09-18 | CALL | 65.0 | DTE_76_120_ATM | THIN | 0.2564 | 464.0 | 11.0 |
| CARR | 2026-09-18 | PUT | 57.5 | DTE_76_120_OTM_10PCT | THIN | 0.2759 | 589.0 | 7.0 |
| ENTG | 2026-07-17 | CALL | 140.0 | DTE_45_75_ATM | THIN | 0.1176 | 14.0 | 1.0 |
| ENTG | 2026-07-17 | CALL | 145.0 | DTE_45_75_OTM_5PCT | THIN | 0.1310 | 16.0 | 3.0 |
| ENTG | 2026-07-17 | CALL | 155.0 | DTE_45_75_OTM_10PCT | THIN | 0.1519 | 7.0 | 2.0 |
| ENTG | 2026-07-17 | PUT | 140.0 | DTE_45_75_ATM | THIN | 0.1000 | 10.0 | 1.0 |
| ENTG | 2026-07-17 | PUT | 130.0 | DTE_45_75_OTM_5PCT | THIN | 0.1304 | 18.0 | 3.0 |
| CRWV | 2026-07-02 | PUT | 99.0 | DTE_21_45_OTM_10PCT | THIN | 0.1132 | 6.0 | 1.0 |
| ETR | 2026-07-17 | CALL | 115.0 | DTE_45_75_OTM_5PCT | THIN | 0.2759 | 31.0 | 11.0 |
| ETR | 2026-07-17 | PUT | 110.0 | DTE_45_75_ATM | THIN | 0.1500 | 16.0 | 3.0 |
| ETR | 2026-07-17 | PUT | 105.0 | DTE_45_75_OTM_5PCT | THIN | 0.2716 | 22.0 | 3.0 |
| ETR | 2026-09-18 | CALL | 110.0 | DTE_76_120_ATM | THIN | 0.3019 | 18.0 | 12.0 |
| ETR | 2026-09-18 | PUT | 105.0 | DTE_76_120_OTM_5PCT | THIN | 0.2857 | 57.0 | 1.0 |
| ETR | 2026-09-18 | PUT | 100.0 | DTE_76_120_OTM_10PCT | THIN | 0.3600 | 71.0 | 1.0 |
| COHU | 2026-07-17 | PUT | 50.0 | DTE_45_75_ATM | THIN | 0.1905 | 1.0 | 1.0 |
| COHU | 2026-08-21 | CALL | 55.0 | DTE_76_120_ATM | THIN | 0.2647 | 236.0 | 31.0 |
| COHU | 2026-08-21 | PUT | 55.0 | DTE_76_120_ATM | THIN | 0.1453 | 7.0 | 5.0 |

## Safety statement
V18.48A does not change official ranking, factor weights, buy/sell permissions, final_action, event risk scoring, trading execution, broker behavior, order behavior, or signal freeze ledgers.

## Suggested next step
V18.48B Options Risk Radar.
