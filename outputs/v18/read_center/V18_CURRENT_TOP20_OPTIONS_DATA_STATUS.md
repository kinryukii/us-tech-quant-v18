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
| KEYS | 1 | TIER_2_IMPORTANT | 18 |
| VRT | 2 | TIER_2_IMPORTANT | 24 |
| ICHR | 3 | TIER_2_IMPORTANT | 17 |
| NVDA | 4 | TIER_2_IMPORTANT | 24 |
| D | 5 | TIER_2_IMPORTANT | 18 |
| AMKR | 6 | TIER_2_IMPORTANT | 15 |
| GOOGL | 7 | TIER_2_IMPORTANT | 24 |
| FIX | 8 | TIER_2_IMPORTANT | 12 |
| MCHP | 9 | TIER_2_IMPORTANT | 22 |
| LITE | 10 | TIER_2_IMPORTANT | 24 |
| CARR | 11 | TIER_3_OCCASIONAL | 19 |
| ENTG | 12 | TIER_3_OCCASIONAL | 18 |
| CRWV | 13 | TIER_3_OCCASIONAL | 24 |
| ETR | 14 | TIER_3_OCCASIONAL | 17 |
| COHU | 15 | TIER_3_OCCASIONAL | 10 |
| GEV | 16 | TIER_3_OCCASIONAL | 24 |
| FN | 17 | TIER_3_OCCASIONAL | 12 |
| ETN | 18 | TIER_3_OCCASIONAL | 21 |
| HUBB | 19 | TIER_3_OCCASIONAL | 17 |
| POWL | 20 | TIER_3_OCCASIONAL | 18 |

## Tickers with options data unavailable
| ticker | rank | provider_error_type | options_unavailable_reason |
| --- | --- | --- | --- |

## Liquidity distribution
| liquidity_status | count |
| --- | --- |
| GOOD | 98 |
| OK | 122 |
| THIN | 151 |
| UNUSABLE | 7 |

## DTE bucket coverage
| dte_bucket | count |
| --- | --- |
| DTE_21_45 | 107 |
| DTE_45_75 | 112 |
| DTE_76_120 | 105 |
| DTE_7_14 | 54 |

## THIN / UNUSABLE option liquidity
| ticker | expiration_date | option_type | strike | moneyness_target | liquidity_status | bid_ask_spread_pct | open_interest | volume |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KEYS | 2026-06-18 | CALL | 370.0 | DTE_21_45_OTM_5PCT | THIN | 0.3106 | 374.0 | 8.0 |
| KEYS | 2026-06-18 | CALL | 380.0 | DTE_21_45_OTM_10PCT | THIN | 0.3423 | 429.0 | 112.0 |
| KEYS | 2026-06-18 | PUT | 310.0 | DTE_21_45_OTM_10PCT | THIN | 0.4416 | 209.0 | 8.0 |
| KEYS | 2026-08-21 | PUT | 350.0 | DTE_76_120_ATM | THIN | 0.0729 | 2.0 | 1.0 |
| KEYS | 2026-08-21 | PUT | 330.0 | DTE_76_120_OTM_5PCT | THIN | 0.0896 | 4.0 | 2001.0 |
| KEYS | 2026-08-21 | PUT | 310.0 | DTE_76_120_OTM_10PCT | THIN | 0.1125 | 14.0 | 1.0 |
| VRT | 2026-06-05 | PUT | 290.0 | DTE_7_14_OTM_10PCT | THIN | 0.2975 | 747.0 | 138.0 |
| VRT | 2026-07-02 | CALL | 315.0 | DTE_21_45_ATM | THIN | 0.1040 | 1.0 | 10.0 |
| VRT | 2026-07-02 | CALL | 335.0 | DTE_21_45_OTM_5PCT | THIN | 0.1640 | 17.0 | 3.0 |
| VRT | 2026-07-02 | CALL | 350.0 | DTE_21_45_OTM_10PCT | THIN | 0.1997 | 5.0 | 5.0 |
| VRT | 2026-07-02 | PUT | 320.0 | DTE_21_45_ATM | THIN | 0.1514 | 8.0 | 2.0 |
| VRT | 2026-07-02 | PUT | 305.0 | DTE_21_45_OTM_5PCT | THIN | 0.1714 | 2.0 | 5.0 |
| VRT | 2026-07-02 | PUT | 290.0 | DTE_21_45_OTM_10PCT | THIN | 0.2574 | 35.0 | 14.0 |
| ICHR | 2026-06-18 | CALL | 77.5 | DTE_21_45_OTM_5PCT | THIN | 0.7273 | 9.0 | 10.0 |
| ICHR | 2026-06-18 | CALL | 80.0 | DTE_21_45_OTM_10PCT | THIN | 0.4000 | 554.0 | 3.0 |
| ICHR | 2026-06-18 | PUT | 72.5 | DTE_21_45_ATM | THIN | 0.6316 | 8.0 | 1.0 |
| ICHR | 2026-06-18 | PUT | 70.0 | DTE_21_45_OTM_5PCT | THIN | 0.6667 | 33.0 | 5.0 |
| ICHR | 2026-06-18 | PUT | 67.5 | DTE_21_45_OTM_10PCT | THIN | 0.8657 | 13.0 | 10.0 |
| ICHR | 2026-07-17 | CALL | 75.0 | DTE_45_75_ATM | THIN | 0.2222 | 4.0 | 3.0 |
| ICHR | 2026-07-17 | CALL | 77.5 | DTE_45_75_OTM_5PCT | THIN | 0.2282 | 2.0 | UNKNOWN |
| ICHR | 2026-07-17 | CALL | 80.0 | DTE_45_75_OTM_10PCT | THIN | 0.5152 | 25.0 | 5.0 |
| ICHR | 2026-07-17 | PUT | 80.0 | DTE_45_75_ATM | THIN | 0.2595 | 3.0 | 3.0 |
| ICHR | 2026-07-17 | PUT | 65.0 | DTE_45_75_OTM_5PCT | THIN | 0.6796 | 3.0 | 3.0 |
| ICHR | 2026-08-21 | CALL | 77.5 | DTE_76_120_OTM_5PCT | THIN | 0.2707 | 42.0 | 2.0 |
| ICHR | 2026-08-21 | CALL | 80.0 | DTE_76_120_OTM_10PCT | THIN | 0.2642 | 33.0 | 11.0 |
| ICHR | 2026-08-21 | PUT | 72.5 | DTE_76_120_ATM | THIN | 0.2927 | 1.0 | UNKNOWN |
| ICHR | 2026-08-21 | PUT | 70.0 | DTE_76_120_OTM_5PCT | THIN | 0.2884 | 25.0 | 1.0 |
| ICHR | 2026-08-21 | PUT | 67.5 | DTE_76_120_OTM_10PCT | THIN | 0.3158 | 1.0 | 1.0 |
| D | 2026-06-18 | CALL | 67.5 | DTE_21_45_ATM | THIN | 0.5000 | 2790.0 | 78.0 |
| D | 2026-06-18 | CALL | 70.0 | DTE_21_45_OTM_5PCT | THIN | 0.9091 | 4360.0 | 64.0 |
| D | 2026-06-18 | CALL | 75.0 | DTE_21_45_OTM_10PCT | UNUSABLE | 2.0000 | 617.0 | 5.0 |
| D | 2026-06-18 | PUT | 67.5 | DTE_21_45_ATM | THIN | 0.4935 | 244.0 | 1.0 |
| D | 2026-06-18 | PUT | 65.0 | DTE_21_45_OTM_5PCT | THIN | 0.5882 | 1622.0 | 1.0 |
| D | 2026-06-18 | PUT | 60.0 | DTE_21_45_OTM_10PCT | THIN | 0.5000 | 4213.0 | 1593.0 |
| D | 2026-07-17 | CALL | 67.5 | DTE_45_75_ATM | THIN | 0.3158 | 755.0 | 18.0 |
| D | 2026-07-17 | CALL | 70.0 | DTE_45_75_OTM_5PCT | THIN | 0.4762 | 3374.0 | 19.0 |
| D | 2026-07-17 | CALL | 75.0 | DTE_45_75_OTM_10PCT | THIN | 0.5000 | 173.0 | 101.0 |
| D | 2026-07-17 | PUT | 67.5 | DTE_45_75_ATM | THIN | 0.3396 | 507.0 | 11.0 |
| D | 2026-07-17 | PUT | 65.0 | DTE_45_75_OTM_5PCT | THIN | 0.6667 | 81.0 | 1.0 |
| D | 2026-07-17 | PUT | 60.0 | DTE_45_75_OTM_10PCT | THIN | 1.1304 | 397.0 | 11.0 |
| D | 2026-09-18 | CALL | 75.0 | DTE_76_120_OTM_10PCT | THIN | 0.5806 | 543.0 | 1.0 |
| D | 2026-09-18 | PUT | 65.0 | DTE_76_120_OTM_5PCT | THIN | 0.4561 | 122.0 | 36.0 |
| D | 2026-09-18 | PUT | 60.0 | DTE_76_120_OTM_10PCT | THIN | 0.3478 | 391.0 | 180.0 |
| GOOGL | 2026-06-05 | CALL | 427.5 | DTE_7_14_OTM_10PCT | THIN | 0.3871 | 38.0 | 94.0 |
| GOOGL | 2026-06-05 | PUT | 350.0 | DTE_7_14_OTM_10PCT | THIN | 0.3673 | 1204.0 | 391.0 |
| GOOGL | 2026-07-02 | CALL | 430.0 | DTE_21_45_OTM_10PCT | THIN | 0.2378 | 6.0 | 58.0 |
| FIX | 2026-06-18 | PUT | 1680.0 | DTE_21_45_OTM_10PCT | THIN | 0.2667 | 24.0 | 13.0 |
| FIX | 2026-07-17 | CALL | 1960.0 | DTE_45_75_OTM_5PCT | THIN | 0.0957 | 10.0 | 1.0 |
| FIX | 2026-07-17 | CALL | 2060.0 | DTE_45_75_OTM_10PCT | THIN | 0.1101 | 4.0 | 3.0 |
| FIX | 2026-07-17 | PUT | 1860.0 | DTE_45_75_ATM | THIN | 0.0958 | 6.0 | 3.0 |
| FIX | 2026-07-17 | PUT | 1780.0 | DTE_45_75_OTM_5PCT | THIN | 0.1190 | 19.0 | 1.0 |
| MCHP | 2026-06-05 | CALL | 102.0 | DTE_7_14_OTM_5PCT | THIN | 0.5882 | 165.0 | 5.0 |
| MCHP | 2026-06-05 | CALL | 107.0 | DTE_7_14_OTM_10PCT | THIN | 1.2000 | 100.0 | 100.0 |
| MCHP | 2026-06-05 | PUT | 97.0 | DTE_7_14_ATM | THIN | 0.2222 | 3.0 | 1.0 |
| MCHP | 2026-06-05 | PUT | 92.0 | DTE_7_14_OTM_5PCT | THIN | 0.2759 | 9.0 | 2.0 |
| MCHP | 2026-06-05 | PUT | 87.0 | DTE_7_14_OTM_10PCT | THIN | 0.8571 | 7.0 | 1.0 |
| MCHP | 2026-07-02 | CALL | 99.0 | DTE_21_45_ATM | THIN | 0.4144 | 1.0 | 1.0 |
| MCHP | 2026-07-02 | CALL | 100.0 | DTE_21_45_OTM_5PCT | THIN | 0.5357 | 13.0 | 2.0 |
| MCHP | 2026-07-02 | CALL | 105.0 | DTE_21_45_OTM_10PCT | THIN | 0.4658 | 8.0 | 1.0 |
| MCHP | 2026-07-02 | PUT | 88.0 | DTE_21_45_ATM | THIN | 0.3396 | 1.0 | 1.0 |
| LITE | 2026-06-05 | PUT | 855.0 | DTE_7_14_OTM_5PCT | THIN | 0.2333 | 15.0 | 2.0 |
| LITE | 2026-07-02 | CALL | 900.0 | DTE_21_45_ATM | THIN | 0.1081 | 5.0 | 2.0 |
| LITE | 2026-07-02 | CALL | 945.0 | DTE_21_45_OTM_5PCT | THIN | 0.1088 | 5.0 | 7.0 |
| LITE | 2026-07-02 | CALL | 1000.0 | DTE_21_45_OTM_10PCT | THIN | 0.1350 | 1.0 | 6.0 |
| LITE | 2026-07-02 | PUT | 915.0 | DTE_21_45_ATM | THIN | 0.0967 | 1.0 | 2.0 |
| LITE | 2026-07-02 | PUT | 855.0 | DTE_21_45_OTM_5PCT | THIN | 0.1212 | 6.0 | 7.0 |
| LITE | 2026-07-02 | PUT | 810.0 | DTE_21_45_OTM_10PCT | THIN | 0.1640 | 3.0 | 1.0 |
| LITE | 2026-07-17 | CALL | 990.0 | DTE_45_75_OTM_10PCT | THIN | 0.0885 | 16.0 | 1.0 |
| CARR | 2026-06-05 | CALL | 65.0 | DTE_7_14_ATM | THIN | 0.5882 | 32.0 | 2.0 |
| CARR | 2026-06-05 | CALL | 67.5 | DTE_7_14_OTM_5PCT | THIN | 0.8333 | 5.0 | 1.0 |
| CARR | 2026-06-05 | CALL | 70.0 | DTE_7_14_OTM_10PCT | THIN | 1.6000 | 3.0 | 3.0 |
| CARR | 2026-06-05 | PUT | 63.5 | DTE_7_14_ATM | THIN | 0.7317 | 0.0 | 2.0 |
| CARR | 2026-06-05 | PUT | 61.0 | DTE_7_14_OTM_5PCT | THIN | 1.7143 | 6.0 | 20.0 |
| CARR | 2026-06-05 | PUT | 57.0 | DTE_7_14_OTM_10PCT | UNUSABLE | 2.0000 | 1.0 | 5.0 |
| CARR | 2026-07-02 | CALL | 66.0 | DTE_21_45_ATM | THIN | 0.4490 | 2.0 | UNKNOWN |
| CARR | 2026-07-17 | CALL | 65.0 | DTE_45_75_ATM | THIN | 0.2778 | 43.0 | 24.0 |
| CARR | 2026-07-17 | CALL | 67.5 | DTE_45_75_OTM_5PCT | THIN | 0.3178 | 134.0 | 13.0 |
| CARR | 2026-07-17 | CALL | 70.0 | DTE_45_75_OTM_10PCT | THIN | 0.4118 | 103.0 | 48.0 |
| CARR | 2026-07-17 | PUT | 65.0 | DTE_45_75_ATM | THIN | 0.3188 | 26.0 | 4.0 |
| CARR | 2026-07-17 | PUT | 57.5 | DTE_45_75_OTM_10PCT | THIN | 0.3256 | 32.0 | 3.0 |

## Safety statement
V18.48A does not change official ranking, factor weights, buy/sell permissions, final_action, event risk scoring, trading execution, broker behavior, order behavior, or signal freeze ledgers.

## Suggested next step
V18.48B Options Risk Radar.
