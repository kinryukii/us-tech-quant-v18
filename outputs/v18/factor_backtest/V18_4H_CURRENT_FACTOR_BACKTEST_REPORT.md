# V18.4H 当前量化因子滚动回测报告

## 1. 结论

本模块用于评估当前 WorldQuant-style 因子 F006-F011 的历史表现。
它只提供历史证据层，不直接改变 official daily decision。

## 2. 回测配置

- UNIVERSE_SOURCE: `D:\us-tech-quant\outputs\v18\factor_pack\V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv`
- RAW_UNIVERSE_COUNT: `105`
- AVAILABLE_TICKER_COUNT: `105`
- MISSING_TICKER_COUNT: `0`
- START_DATE: `2022-12-02`
- END_DATE: `2026-05-15`
- HOLD_DAYS: `5`
- TOP_N: `10`
- BOTTOM_N: `10`
- COST_BPS_ONE_WAY: `50.0`
- BENCHMARK: `QQQ`

## 3. 因子说明

| factor | meaning |
|---|---|
| F006_SHORT_REV_5D | 5日短期反转 |
| F007_PULLBACK_IN_UPTREND | 中期上行趋势中的短线回撤 |
| F008_VOLUME_ABNORMAL_5_20 | 成交量相对20日均量异常 |
| F009_VOLUME_PRICE_CONFIRM | 20日价格强度 × 成交量确认 |
| F010_XSEC_COMPOSITE_RANK | 综合横截面排名 |
| F011_TS_MOMENTUM_60_120 | 60日和120日时间序列动量 |

## 4. LONG_ONLY_TOPN 排名

| rank | factor | CAGR | Sharpe | Max DD | Excess CAGR vs QQQ | Avg Turnover |
|---:|---|---:|---:|---:|---:|---:|
| 1 | F007_PULLBACK_IN_UPTREND | 107.35% | 1.80 | -42.75% | 76.44% | 31.66% |
| 2 | F010_XSEC_COMPOSITE_RANK | 79.23% | 1.57 | -43.86% | 48.33% | 62.89% |
| 3 | F011_TS_MOMENTUM_60_120 | 85.32% | 1.52 | -44.41% | 54.41% | 19.53% |
| 4 | F006_SHORT_REV_5D | 74.02% | 1.49 | -42.64% | 43.11% | 87.21% |
| 5 | F009_VOLUME_PRICE_CONFIRM | 71.19% | 1.42 | -43.81% | 40.28% | 53.43% |
| 6 | F008_VOLUME_ABNORMAL_5_20 | 57.73% | 1.36 | -47.85% | 26.82% | 88.19% |

## 5. LONG_SHORT_SPREAD 因子区分度

| rank | factor | Spread CAGR | Spread Sharpe | Spread Max DD |
|---:|---|---:|---:|---:|
| 1 | F011_TS_MOMENTUM_60_120 | 20.33% | 0.65 | -51.19% |
| 2 | F010_XSEC_COMPOSITE_RANK | 13.92% | 0.54 | -47.78% |
| 3 | F007_PULLBACK_IN_UPTREND | 4.29% | 0.30 | -59.53% |
| 4 | F009_VOLUME_PRICE_CONFIRM | -17.23% | -0.27 | -73.76% |
| 5 | F008_VOLUME_ABNORMAL_5_20 | -17.94% | -0.58 | -59.05% |
| 6 | F006_SHORT_REV_5D | -30.91% | -0.80 | -72.81% |

## 6. 输出文件

- `V18_4H_CURRENT_FACTOR_BACKTEST_SUMMARY.csv`
- `V18_4H_CURRENT_FACTOR_BACKTEST_DAILY_RETURNS.csv`
- `V18_4H_CURRENT_FACTOR_BACKTEST_HOLDINGS.csv`
- `V18_4H_CURRENT_FACTOR_LATEST_SCORES.csv`

## 7. 解释边界

LONG_ONLY_TOPN 更接近实际交易。
LONG_SHORT_SPREAD 主要用于判断因子排序能力，不代表当前账户要做空。
本模块暂时不纳入事件门、预算锁、Rakuten 一股最小单位、行为纪律。