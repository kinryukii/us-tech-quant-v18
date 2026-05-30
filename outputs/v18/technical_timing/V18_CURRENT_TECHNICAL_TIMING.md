# V18.6A Technical Timing Shadow Report

## 1. Status

- V18_6A_STATUS: `OK_TECHNICAL_TIMING_SHADOW_READY`
- TOTAL_TICKER_COUNT: `105`
- TECH_TIMING_WATCH_POSITIVE_COUNT: `2`
- TECH_TIMING_PULLBACK_WATCH_COUNT: `3`
- TECH_TIMING_OVERHEAT_AVOID_CHASE_COUNT: `22`
- BB_SQUEEZE_COUNT: `12`
- VIX_DATE: `2026-05-29`
- VIX_CLOSE: `15.32`
- VIX_REGIME: `VIX_NORMAL`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. 技术择时分数靠前

| ticker   | price_date   |   close |   technical_timing_score | technical_signal           | bb_status      | rsi_status   | kdj_status     |   volume_ratio_5_20 | technical_warning_label   |
|:---------|:-------------|--------:|-------------------------:|:---------------------------|:---------------|:-------------|:---------------|--------------------:|:--------------------------|
| ACM      | 2026-05-29   |   69.37 |                       68 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_OVERSOLD | KDJ_DEAD_CROSS |              1.8152 | NONE                      |
| ZS       | 2026-05-29   |  139.73 |                       68 | TECH_TIMING_WATCH_POSITIVE | BB_LOWER_HALF  | RSI_WEAK     | KDJ_NEUTRAL    |              2.3871 | NONE                      |
| ETR      | 2026-05-29   |  109.05 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_LOWER_HALF  | RSI_WEAK     | KDJ_NEUTRAL    |              0.801  | NONE                      |
| GEV      | 2026-05-29   |  968.32 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_BELOW_LOWER | RSI_WEAK     | KDJ_NEUTRAL    |              1.1985 | NONE                      |
| HUBB     | 2026-05-29   |  473.61 |                       64 | TECH_TIMING_PULLBACK_WATCH | BB_LOWER_HALF  | RSI_WEAK     | KDJ_NEUTRAL    |              1.0716 | NONE                      |
| CARR     | 2026-05-29   |   63.87 |                       62 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              1.2215 | NONE                      |
| AMKR     | 2026-05-29   |   69.56 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              1.1392 | NONE                      |
| FIX      | 2026-05-29   | 1828.21 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              1.037  | NONE                      |
| FN       | 2026-05-29   |  654.16 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              1.1482 | NONE                      |
| FORM     | 2026-05-29   |  124.59 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              0.7474 | NONE                      |
| GOOGL    | 2026-05-29   |  380.34 |                       58 | TECH_TIMING_NEUTRAL        | BB_NEAR_LOWER  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              1.024  | NONE                      |
| KEYS     | 2026-05-29   |  338.33 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_DEAD_CROSS |              1.1319 | NONE                      |
| LITE     | 2026-05-29   |  854.96 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              0.8058 | NONE                      |
| MCHP     | 2026-05-29   |   94.65 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              0.9412 | NONE                      |
| MPWR     | 2026-05-29   | 1566.21 |                       58 | TECH_TIMING_NEUTRAL        | BB_LOWER_HALF  | RSI_NEUTRAL  | KDJ_NEUTRAL    |              1.1198 | NONE                      |

## 3. 过热/追高风险靠前

| ticker   | price_date   |   close |   technical_timing_score | technical_signal                 | bb_status      | rsi_status           | kdj_status           |   volume_ratio_5_20 | technical_warning_label                                       |
|:---------|:-------------|--------:|-------------------------:|:---------------------------------|:---------------|:---------------------|:---------------------|--------------------:|:--------------------------------------------------------------|
| DELL     | 2026-05-29   |  420.91 |                       14 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              2.1183 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| SNOW     | 2026-05-29   |  255.55 |                       14 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              1.8277 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| ARM      | 2026-05-29   |  353.29 |                       10 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              0.965  | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| IGV      | 2026-05-29   |  101.66 |                       10 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              0.9405 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| IYW      | 2026-05-29   |  252.92 |                       10 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              0.7588 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| TQQQ     | 2026-05-29   |   84.56 |                       10 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              0.8855 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| XLK      | 2026-05-29   |  191.02 |                       10 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              1.0014 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT |
| HPE      | 2026-05-29   |   43.04 |                       19 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.7043 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| NTAP     | 2026-05-29   |  174.29 |                       19 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_ABOVE_UPPER | RSI_EXTREME_OVERHEAT | KDJ_HIGH_DEAD_CROSS  |              2.1832 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_HIGH_DEAD_CROSS  |
| ALAB     | 2026-05-29   |  342.85 |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              0.978  | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| CRWD     | 2026-05-29   |  731    |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              0.9483 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| IRDM     | 2026-05-29   |   51.78 |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.1692 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| PANW     | 2026-05-29   |  281.69 |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_EXTREME_OVERHEAT | KDJ_OVERHEAT         |              1.0103 | BB_UPPER_CHASE_RISK;RSI_EXTREME_OVERHEAT;KDJ_OVERHEAT         |
| SPY      | 2026-05-29   |  756.48 |                       15 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_NEAR_UPPER  | RSI_OVERHEAT         | KDJ_EXTREME_OVERHEAT |              0.9377 | BB_UPPER_CHASE_RISK;RSI_OVERHEAT;KDJ_EXTREME_OVERHEAT         |
| AMD      | 2026-05-29   |  516.1  |                       20 | TECH_TIMING_OVERHEAT_AVOID_CHASE | BB_UPPER_HALF  | RSI_EXTREME_OVERHEAT | KDJ_EXTREME_OVERHEAT |              0.8194 | RSI_EXTREME_OVERHEAT;KDJ_EXTREME_OVERHEAT                     |

## 4. 说明

本模块加入 Bollinger Bands、RSI、KDJ、VIX；期权和 Gamma Squeeze 字段先预留。当前是 shadow 层，不改变官方交易动作。
