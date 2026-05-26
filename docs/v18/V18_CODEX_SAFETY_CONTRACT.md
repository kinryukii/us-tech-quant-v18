# V18 Codex Safety Contract

This file is the stable safety contract for future V18 Codex work.

## Hard Safety Rules
- No broker/API/trading/order execution code.
- `AUTO_TRADE` and `AUTO_SELL` must remain `DISABLED`.
- `OFFICIAL_DECISION_IMPACT` must remain `NONE` unless the user explicitly asks otherwise in a future separate task.
- Do not modify ranking, factor, recommendation, buyability, sizing, cost, or account-aware logic unless explicitly scoped.
- Do not modify protected state or ledgers unless explicitly scoped and backed up.
- No external fetch unless explicitly scoped.

## Development Rules
- Always read this safety contract before touching V18 code.
- Always produce parse, compile, and run validation appropriate to the changed files.
- Always create or update `READ_FIRST` for new V18 task steps.
- Prefer small, scoped patches.
- Preserve auditability, stable field names, and clear status codes.
- Do not hide warnings by printing `OK`.
- If a warning is expected, label it as `WARN` with the reason.

## Current Safety Baseline
- Broker connection: `NOT_EXECUTED`
- Order placement: `NOT_EXECUTED`
- External trading integration: `NOT_EXECUTED`
- Manual research guidance only.
