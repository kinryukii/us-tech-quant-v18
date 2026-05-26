# V16 Full Universe Compat Shim R4

生成时间：20260519_105311

STATUS: OK_V16_COMPAT_FULL_UNIVERSE_NON_RECURSIVE_R4

MODE: NO_RECURSION_EXACT_V17_6E_YAML_COMPAT

SOURCE: D:\us-tech-quant\state\v18\raw105_universe_for_factor_lab.csv

TICKER_COUNT: 105

SCREENED_ROWS: 105

SECOND_STAGE_ROWS: 20

YAML_FORMAT: TICKERS_COLON_DASH_SYMBOL

OFFICIAL_DECISION_IMPACT: NONE

说明：

- 这是 V18 active chain 的旧 V16 入口兼容层。
- 本脚本不调用 V17_8A / V17_7G / V17_6F，避免递归。
- YAML 使用 V17.6E parser 源码要求的格式：tickers: + "  - TICKER"。
- action/restriction 固定为 REVIEW_ONLY / COMPAT_NO_DIRECT_TRADE，避免兼容层直接产生交易执行含义。
