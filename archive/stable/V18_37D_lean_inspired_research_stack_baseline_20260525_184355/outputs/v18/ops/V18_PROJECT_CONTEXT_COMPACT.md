# V18 Project Context Compact

## Purpose
V18 is the daily quant/trade-readiness pipeline for manual research review. It is not a live-trading system.

## Current Daily Entrypoint
- Primary runner: `scripts/v18/run_v18_31F_full_daily_trade_readiness_runner.ps1`
- Python runner: `scripts/v18/v18_31F_full_daily_trade_readiness_runner.py`

## Current Snapshot
- Expected candidate count: `252`
- Ranked candidates: `252`
- Recommendation rows: `252`
- Theme rows: `252`
- Latest signal date: `2026-05-22`
- Latest relevant signal date: `2026-05-22`
- Latest freeze coverage status: `FULL_MATCH`
- Latest freeze ticker count: `252`
- Latest freeze expected count: `252`
- Latest freeze missing tickers: `NONE`
- Current allowed trade candidates: `0`
- Current allowed trade candidate count: `0`
- Current allowed trade candidate tickers: `NONE`
- Account state quality: `WARN_TEMPLATE_EMPTY_ACCOUNT`
- Forward-return readiness: `NOT_READY_WAIT_FOR_FUTURE_PRICE_DATA`

## Key Reports To Read
- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`
- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`
- `outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REPORT.md`
- `outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md`
- `outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md`

## Known Warnings
- Manual account state is template/manual and not broker data.
- Forward-return extraction is not ready until future price bars exist.
- Non-trading-day signal-date guard may reuse the latest supported signal date.
- Context extraction confidence: `HIGH`
- Context extraction warning count: `0`
- Freeze source paths: `state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv`
- Allowed-trade source paths: `outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REPORT.md;outputs/v18/read_center/V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_REPORT.md;outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`

## Safety State
- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `OFFICIAL_DECISION_IMPACT: NONE`
- `FORBIDDEN_MODIFIED: FALSE`
- No broker API, no order placement, no live trading, no account login, no external trading integration.

## Development Rule
Use this compact context, `docs/v18/V18_CODEX_SAFETY_CONTRACT.md`, and `docs/v18/V18_CODEX_TASK_TEMPLATE.md` before touching code.

Do not infer from archived stale files unless asked.

Prefer current files over historical reports.
