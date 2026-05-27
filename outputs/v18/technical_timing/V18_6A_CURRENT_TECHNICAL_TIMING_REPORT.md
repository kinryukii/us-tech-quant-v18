# V18.6A Technical Timing Shadow Report

## 1. Status

- V18_6A_STATUS: `OK_TECHNICAL_TIMING_SHADOW_READY`
- TOTAL_TICKER_COUNT: `105`
- TECH_TIMING_WATCH_POSITIVE_COUNT: `1`
- TECH_TIMING_PULLBACK_WATCH_COUNT: `1`
- TECH_TIMING_OVERHEAT_AVOID_CHASE_COUNT: `17`
- BB_SQUEEZE_COUNT: `9`
- VIX_DATE: `2026-05-27`
- VIX_CLOSE: `16.86`
- VIX_REGIME: `VIX_NORMAL`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. 技术择时分数靠前

| ticker   | price_date   |   close |   technical_timing_score | technical_signal           | bb_status     | rsi_status   | kdj_status           |   volume_ratio_5_20 | technical_warning_label   |
|:---------|:-------------|--------:|-------------------------:|:---------------------------|:--------------|:-------------|:---------------------|--------------------:|:--------------------------|
| ACM      | 2026-05-26   |   72.47 |                       68 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF | RSI_WEAK     | KDJ_NEUTRAL          |              1.3273 | NONE                      |
| HUBB     | 2026-05-26   |  478.05 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_LOWER_HALF | RSI_WEAK     | KDJ_NEUTRAL          |              1.0536 | NONE                      |
| KEYS     | 2026-05-26   |  355.74 |                       62 | TECH_TIMING_NEUTRAL        | BB_UPPER_HALF | RSI_NEUTRAL  | KDJ_LOW_GOLDEN_CROSS |              1.6231 | NONE                      |
| AMKR     | 2026-05-26   |   73.46 |                       58 | TECH_TIMING_NEUTRAL        | BB_UPPER_HALF | RSI_NEUTRAL  | KDJ_LOW_GOLDEN_CROSS |              0.983  | NONE                      |
| AMZN     | 2026-05-26   |  265.29 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF | RSI_NEUTRAL  | KDJ_NEUTRAL          |              0.8152 | NONE                      |
| CARR     | 2026-05-26   |   64.89 |                       58 | TECH_TIMING_NEUTRAL        | BB_MID        | RSI_NEUTRAL  | KDJ_LOW_GOLDEN_CROSS |              1.0457 | NONE                      |
| CRWV     | 2026-05-26   |  105.89 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF | RSI_NEUTRAL  | KDJ_NEUTRAL          |              0.8602 | NONE                      |
| ETR      | 2026-05-26   |  111.97 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF | RSI_NEUTRAL  | KDJ_NEUTRAL          |              0.8404 | NONE                      |
| ICHR     | 2026-05-26   |   72.73 |                       58 | TECH_TIMING_NEUTRAL        | BB_UPPER_HALF | RSI_NEUTRAL  | KDJ_LOW_GOLDEN_CROSS |              0.9894 | NONE                      |
| MCHP     | 2026-05-26   |   98.05 |                       58 | TECH_TIMING_NEUTRAL        | BB_UPPER_HALF | RSI_STRONG   | KDJ_LOW_GOLDEN_CROSS |              0.8402 | NONE                      |
| POWL     | 2026-05-26   |  291.97 |                       58 | TECH_TIMING_NEUTRAL        | BB_MID        | RSI_NEUTRAL  | KDJ_LOW_GOLDEN_CROSS |              0.646  | NONE                      |
| VRT      | 2026-05-26   |  323.91 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF | RSI_NEUTRAL  | KDJ_NEUTRAL          |              1.0947 | NONE                      |
| D        | 2026-05-26   |   67.28 |                       54 | TECH_TIMING_NEUTRAL        | BB_UPPER_HALF | RSI_STRONG   | KDJ_NEUTRAL          |              1.3198 | NONE                      |
| MOD      | 2026-05-26   |  295.88 |                       52 | TECH_TIMING_NEUTRAL        | BB_NEAR_UPPER | RSI_STRONG   | KDJ_LOW_GOLDEN_CROSS |              1.4341 | BB_UPPER_CHASE_RISK       |
| ACLS     | 2026-05-26   |  164.27 |                       50 | TECH_TIMING_NEUTRAL        | BB_UPPER_HALF | RSI_STRONG   | KDJ_NEUTRAL          |              0.6645 | NONE                      |

## 3. 过热/追高风险靠前

| ticker   | price_date   |   close |   technical_timing_score | technical_signal                 | bb_status      | rsi_status           | kdj_status           |   volume_ratio_5_20 | technical_warning_label                                       |
|:---------|:-------------|--------:|-------------------------:|:---------------------------------|:---------------|:---------------------|:---------------------|--------------------:|:--------------------------------------------------------------|
| ALAB     | 2026-05-26   |  318.72 |                       14 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              1.3068 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| ACMR     | 2026-05-26   |   86.46 |                       10 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              1.1252 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| NTAP     | 2026-05-26   |  138.95 |                       19 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.4368 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| HPE      | 2026-05-26   |   38.06 |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              0.998  | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| IRDM     | 2026-05-26   |   50.16 |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.1027 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| ZS       | 2026-05-26   |  184.6  |                       24 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_OVERHEAT         | KDJ_OVERHEAT         |              1.3633 | BB_UPPER_CHASE_RISK;RSI_OVERHEAT;KDJ_OVERHEAT                 |
| ARM      | 2026-05-26   |  321.22 |                       29 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_NEUTRAL          |              1.2812 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT                      |
| DELL     | 2026-05-26   |  305.08 |                       29 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_NEUTRAL          |              1.201  | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT                      |
| AAPL     | 2026-05-26   |  308.33 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_HIGH_DEAD_CROSS  |              0.8828 | RSI_EXTREME_OVERHEAT;KDJ_HIGH_DEAD_CROSS                      |
| AMD      | 2026-05-26   |  503.89 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_NEUTRAL          |              0.8386 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT                      |
| CRWD     | 2026-05-26   |  671.55 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.0833 | RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT                             |
| CSCO     | 2026-05-26   |  118.33 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              0.973  | RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT                             |
| DDOG     | 2026-05-26   |  223.65 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              0.7346 | RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT                             |
| MRVL     | 2026-05-26   |  208.26 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_NEUTRAL          |              1.1488 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT                      |
| PANW     | 2026-05-26   |  256.75 |                       25 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_HIGH_DEAD_CROSS  |              1.017  | RSI_EXTREME_OVERHEAT;KDJ_HIGH_DEAD_CROSS                      |

## 4. 说明

本模块加入 Bollinger Bands、RSI、KDJ、VIX；期权和 Gamma Squeeze 字段先预留。当前是 shadow 层，不改变官方交易动作。
