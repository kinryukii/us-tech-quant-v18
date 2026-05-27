# V18.6A Technical Timing Shadow Report

## 1. Status

- V18_6A_STATUS: `OK_TECHNICAL_TIMING_SHADOW_READY`
- TOTAL_TICKER_COUNT: `105`
- TECH_TIMING_WATCH_POSITIVE_COUNT: `8`
- TECH_TIMING_PULLBACK_WATCH_COUNT: `10`
- TECH_TIMING_OVERHEAT_AVOID_CHASE_COUNT: `6`
- BB_SQUEEZE_COUNT: `9`
- VIX_DATE: `2026-05-18`
- VIX_CLOSE: `17.82`
- VIX_REGIME: `VIX_NORMAL`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. 技术择时分数靠前

| ticker   | price_date   |   close |   technical_timing_score | technical_signal           | bb_status      | rsi_status   | kdj_status           |   volume_ratio_5_20 | technical_warning_label   |
|:---------|:-------------|--------:|-------------------------:|:---------------------------|:---------------|:-------------|:---------------------|--------------------:|:--------------------------|
| ANET     | 2026-05-18   |  141.71 |                       72 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_WEAK     | KDJ_LOW_GOLDEN_CROSS |              0.9989 | NONE                      |
| APH      | 2026-05-18   |  121.72 |                       72 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_WEAK     | KDJ_OVERSOLD         |              1.0932 | NONE                      |
| ECL      | 2026-05-18   |  249.21 |                       72 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_WEAK     | KDJ_LOW_GOLDEN_CROSS |              1.0846 | NONE                      |
| HUBB     | 2026-05-18   |  470.87 |                       72 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_OVERSOLD | KDJ_OVERSOLD         |              0.9808 | NONE                      |
| VST      | 2026-05-18   |  136.75 |                       72 | TECH_TIMING_WATCH_POSITIVE | BB_NEAR_LOWER  | RSI_WEAK     | KDJ_OVERSOLD         |              1.1279 | NONE                      |
| ACM      | 2026-05-18   |   71.49 |                       68 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_OVERSOLD | KDJ_NEUTRAL          |              1.5309 | NONE                      |
| CAMT     | 2026-05-18   |  155.74 |                       68 | TECH_TIMING_WATCH_POSITIVE | BB_BELOW_LOWER | RSI_WEAK     | KDJ_NEUTRAL          |              1.7349 | NONE                      |
| CEG      | 2026-05-18   |  262    |                       68 | TECH_TIMING_WATCH_POSITIVE | BB_NEAR_LOWER  | RSI_WEAK     | KDJ_NEUTRAL          |              1.2911 | NONE                      |
| CLS      | 2026-05-18   |  342.67 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_BELOW_LOWER | RSI_WEAK     | KDJ_NEUTRAL          |              0.7645 | NONE                      |
| CRDO     | 2026-05-18   |  156.27 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_BELOW_LOWER | RSI_WEAK     | KDJ_NEUTRAL          |              1.0451 | NONE                      |
| CRWV     | 2026-05-18   |  103.77 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_LOWER_HALF  | RSI_WEAK     | KDJ_NEUTRAL          |              0.9791 | NONE                      |
| ENTG     | 2026-05-18   |  127.21 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_BELOW_LOWER | RSI_WEAK     | KDJ_NEUTRAL          |              0.8672 | NONE                      |
| ETN      | 2026-05-18   |  381.87 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_BELOW_LOWER | RSI_WEAK     | KDJ_NEUTRAL          |              0.9033 | NONE                      |
| ETR      | 2026-05-18   |  109.58 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_LOWER_HALF  | RSI_WEAK     | KDJ_NEUTRAL          |              0.9033 | NONE                      |
| FLR      | 2026-05-18   |   44.35 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_LOWER_HALF  | RSI_WEAK     | KDJ_NEUTRAL          |              1.0508 | NONE                      |

## 3. 过热/追高风险靠前

| ticker   | price_date   |   close |   technical_timing_score | technical_signal                 | bb_status      | rsi_status           | kdj_status           |   volume_ratio_5_20 | technical_warning_label                                       |
|:---------|:-------------|--------:|-------------------------:|:---------------------------------|:---------------|:---------------------|:---------------------|--------------------:|:--------------------------------------------------------------|
| CRWD     | 2026-05-18   |  618.83 |                       14 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              1.2131 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| PANW     | 2026-05-18   |  247.55 |                       14 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              1.29   | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| CSCO     | 2026-05-18   |  118.88 |                       19 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.6833 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| ZS       | 2026-05-18   |  174.69 |                       29 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_OVERHEAT         | KDJ_OVERHEAT         |              1.4569 | BB_UPPER_CHASE_RISK;RSI_OVERHEAT;KDJ_OVERHEAT                 |
| MDB      | 2026-05-18   |  330    |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_OVERHEAT         | KDJ_OVERHEAT         |              1.1882 | BB_UPPER_CHASE_RISK;RSI_OVERHEAT;KDJ_OVERHEAT                 |
| DDOG     | 2026-05-18   |  208.82 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              0.7486 | RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT                             |
| NTAP     | 2026-05-18   |  120.6  |                       34 | TECH_TIMING_NEUTRAL              | BB_NEAR_UPPER  | RSI_OVERHEAT         | KDJ_NEUTRAL          |              1.2785 | BB_UPPER_CHASE_RISK;RSI_OVERHEAT                              |
| AAPL     | 2026-05-18   |  297.84 |                       30 | TECH_TIMING_NEUTRAL              | BB_UPPER_HALF  | RSI_OVERHEAT         | KDJ_HIGH_DEAD_CROSS  |              0.9234 | RSI_OVERHEAT;KDJ_HIGH_DEAD_CROSS                              |
| TXN      | 2026-05-18   |  300.6  |                       30 | TECH_TIMING_NEUTRAL              | BB_UPPER_HALF  | RSI_OVERHEAT         | KDJ_OVERHEAT         |              0.7278 | RSI_OVERHEAT;KDJ_OVERHEAT                                     |
| D        | 2026-05-18   |   67.56 |                       49 | TECH_TIMING_NEUTRAL              | BB_ABOVE_UPPER | RSI_STRONG           | KDJ_NEUTRAL          |              1.7841 | BB_UPPER_CHASE_RISK                                           |
| AEHR     | 2026-05-18   |   83.57 |                       48 | TECH_TIMING_NEUTRAL              | BB_LOWER_HALF  | RSI_NEUTRAL          | KDJ_HIGH_DEAD_CROSS  |              0.9751 | KDJ_HIGH_DEAD_CROSS                                           |
| ICHR     | 2026-05-18   |   66.6  |                       48 | TECH_TIMING_NEUTRAL              | BB_LOWER_HALF  | RSI_NEUTRAL          | KDJ_HIGH_DEAD_CROSS  |              0.8458 | KDJ_HIGH_DEAD_CROSS                                           |
| NOW      | 2026-05-18   |  103.42 |                       45 | TECH_TIMING_NEUTRAL              | BB_ABOVE_UPPER | RSI_STRONG           | KDJ_NEUTRAL          |              1.0377 | BB_UPPER_CHASE_RISK                                           |
| SNOW     | 2026-05-18   |  164.24 |                       45 | TECH_TIMING_NEUTRAL              | BB_ABOVE_UPPER | RSI_STRONG           | KDJ_NEUTRAL          |              1.019  | BB_UPPER_CHASE_RISK                                           |
| ACMR     | 2026-05-18   |   63.25 |                       44 | TECH_TIMING_NEUTRAL              | BB_UPPER_HALF  | RSI_STRONG           | KDJ_HIGH_DEAD_CROSS  |              1.5598 | KDJ_HIGH_DEAD_CROSS                                           |

## 4. 说明

本模块加入 Bollinger Bands、RSI、KDJ、VIX；期权和 Gamma Squeeze 字段先预留。当前是 shadow 层，不改变官方交易动作。
