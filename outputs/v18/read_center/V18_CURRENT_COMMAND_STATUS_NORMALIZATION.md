# V18.38C-R1 命令中心状态归一化报告

生成时间: 2026-05-27T17:52:31

## 1. 今日总判定
- 总状态: WARN_V18_38C_R1_COMMAND_STATUS_NORMALIZATION_REVIEW_NEEDED
- 今日只读日报是否可用: TRUE
- Forward research 是否可用: TRUE
- 当前 blocking 数量: 0
- 历史 FAIL 数量: 7
- 历史问题是否存在: TRUE

## 2. 当前关键源状态
- CURRENT_CRITICAL 数量: 13
- CURRENT_SUPPORTING 数量: 10
- V18_33A_READ_FIRST.txt [CURRENT_CRITICAL]: OK_READY - OK status with read-only safety contract intact
- V18_35A_READ_FIRST.txt [CURRENT_CRITICAL]: OK_READY - OK status with read-only safety contract intact
- V18_35F_READ_FIRST.txt [CURRENT_CRITICAL]: OK_READY - OK status with read-only safety contract intact
- V18_35G_READ_FIRST.txt [CURRENT_CRITICAL]: OK_READY - OK status with read-only safety contract intact
- V18_37C_READ_FIRST.txt [CURRENT_CRITICAL]: OK_READY - OK status with read-only safety contract intact

## 3. 历史旧问题与当前问题的区分
- HISTORICAL_LEGACY 数量: 244
- UNKNOWN_LEGACY 数量: 50
- 这些旧问题会写入 detail 和 summary，但不会让 DAILY_RUN_USABLE 变成 FALSE。
- V18_10B_R3_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_10C_R2_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_10D_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_10D_R2_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_11F_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12A_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12B_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12C_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12D_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12E_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12F_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12F_R2_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12G_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_12H_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_13A_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_13B_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_13C_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_13D_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_14A_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_REPORT_STALE_WARN - Legacy source is stale or has no current generated date
- V18_14A_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_FAIL - Explicit FAIL_ status outside current critical blocking scope
- 另有 229 项未展开，详见 detail CSV。

## 4. 是否有真正阻断
- 未发现当前真正阻断。

## 5. 可忽略/可等待的问题
- V18_38A_READ_FIRST.txt [CURRENT_CRITICAL]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_38B_READ_FIRST.txt [CURRENT_CRITICAL]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md [CURRENT_SUPPORTING]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md [CURRENT_SUPPORTING]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_39A_READ_FIRST.txt [HISTORICAL_LEGACY]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_40B_READ_FIRST.txt [HISTORICAL_LEGACY]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_CURRENT_OPERATOR_CLEAN_STATUS.md [UNKNOWN_LEGACY]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured

## 6. 需要之后处理的问题
- V18_19A_READ_FIRST.txt [CURRENT_CRITICAL]: REVIEW_NEEDED_NON_BLOCKING - Current WARN_ status needs operator review
- V18_34B_READ_FIRST.txt [CURRENT_CRITICAL]: REVIEW_NEEDED_NON_BLOCKING - Current WARN_ status needs operator review
- V18_34C_READ_FIRST.txt [CURRENT_CRITICAL]: REVIEW_NEEDED_NON_BLOCKING - Current WARN_ status needs operator review
- V18_35B_READ_FIRST.txt [CURRENT_CRITICAL]: REVIEW_NEEDED_NON_BLOCKING - Current WARN_ status needs operator review
- V18_35C_READ_FIRST.txt [CURRENT_CRITICAL]: REVIEW_NEEDED_NON_BLOCKING - Current WARN_ status needs operator review
- V18_36A_READ_FIRST.txt [CURRENT_CRITICAL]: DATA_PROVIDER_WARN - Current data provider, yfinance, preflight, or price-cache warning
- V18_CURRENT_CANDIDATE_SOURCE_DEPENDENCY_REVIEW.md [CURRENT_SUPPORTING]: REPORT_STALE_WARN - Current supporting report does not appear to be generated today
- V18_CURRENT_CANDIDATE_SOURCE_NORMALIZATION.md [CURRENT_SUPPORTING]: UNKNOWN_REVIEW - No STATUS key found
- V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md [CURRENT_SUPPORTING]: UNKNOWN_REVIEW - No STATUS key found
- V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md [CURRENT_SUPPORTING]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_CURRENT_DAILY_TRADE_READINESS.md [CURRENT_SUPPORTING]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_CURRENT_FULL_UNIVERSE_RECOMPUTE.md [CURRENT_SUPPORTING]: UNKNOWN_REVIEW - No STATUS key found
- V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md [CURRENT_SUPPORTING]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_CURRENT_UNIVERSE_TO_CANDIDATE_AUDIT.md [CURRENT_SUPPORTING]: UNKNOWN_REVIEW - No STATUS key found

## 7. Forward outcome 状态
- V18_38A_READ_FIRST.txt [CURRENT_CRITICAL]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_38B_READ_FIRST.txt [CURRENT_CRITICAL]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md [CURRENT_SUPPORTING]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md [CURRENT_SUPPORTING]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_39A_READ_FIRST.txt [HISTORICAL_LEGACY]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_40B_READ_FIRST.txt [HISTORICAL_LEGACY]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured
- V18_CURRENT_OPERATOR_CLEAN_STATUS.md [UNKNOWN_LEGACY]: EXPECTED_PENDING_FORWARD_OUTCOME - Forward price horizon has not matured

## 8. 数据源 warning 状态
- 当前数据源 warning: 1
- 历史数据源 warning: 128
- V18_36A_READ_FIRST.txt [CURRENT_CRITICAL]: DATA_PROVIDER_WARN - Current data provider, yfinance, preflight, or price-cache warning
- V18_10D_R2_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16C_P1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16C_P2_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16C_P3_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16C_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16F_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16J_R2A_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16K_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16K_R2_STABLE_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_16K_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_17A_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_18A_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_18B_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_18C_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_18D_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_18F_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_20F_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_20G_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- V18_20I_READ_FIRST.txt [HISTORICAL_LEGACY]: LEGACY_DATA_PROVIDER_WARN - Legacy data provider, yfinance, preflight, or price-cache warning
- 另有 109 项未展开，详见 detail CSV。

## 9. 账户 template warning 状态
- V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md [CURRENT_SUPPORTING]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_CURRENT_DAILY_TRADE_READINESS.md [CURRENT_SUPPORTING]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md [CURRENT_SUPPORTING]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_31D_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_31E_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_31F_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_32A_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_32B_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_32C_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_37B_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_38C_R1_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_38C_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_38D_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_39B_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_39C_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_39D_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_40C_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_40D_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_41A_READ_FIRST.txt [HISTORICAL_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md [UNKNOWN_LEGACY]: ACCOUNT_TEMPLATE_WARN - Account template or account-state quality warning
- 另有 7 项未展开，详见 detail CSV。

## 10. 安全确认
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE
- TRADING_EXECUTION_ALLOWED: FALSE

## 11. 下一步建议
Daily run is usable; review current warnings and keep legacy issues separated from today's blocking status.
