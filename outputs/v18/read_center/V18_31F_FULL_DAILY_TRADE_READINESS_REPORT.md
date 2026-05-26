# V18.31F Full Daily Trade-Readiness Runner

STATUS: WARN_V18_31F_R1_NON_TRADING_DAY_REUSE_LATEST_READY
RUN_ID: V18_31F_20260524_182839

## Step Results
| step_order | step_name | parsed_status | exit_code | result | continue_allowed | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | R31G trading-day signal-date guard | WARN_V18_31G_TRADING_DAY_SIGNAL_DATE_BLOCKED_REUSE_LATEST | 0 | WARN_ACCEPTED | TRUE | WARN accepted for structural orchestration; final status will remain WARN unless all warnings clear. |
| 2 | R30E safe daily operator sequence | FAIL_V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_FAILED | 1 | WARN_ACCEPTED | TRUE | R30E failed in non-trading reuse mode; softened because independent structural validation passed: PASS_CURRENT_ONLY_FREEZE_PARTIAL_250. |
| 3 | R31A static buyability gate | WARN_V18_31A_STATIC_BUYABILITY_GATE_REVIEW_NEEDED | 0 | WARN_ACCEPTED | TRUE | WARN accepted for structural orchestration; final status will remain WARN unless all warnings clear. |
| 4 | R31B manual position sizing policy | WARN_V18_31B_MANUAL_POSITION_SIZING_POLICY_REVIEW_NEEDED | 0 | WARN_ACCEPTED | TRUE | WARN accepted for structural orchestration; final status will remain WARN unless all warnings clear. |
| 5 | R31C cost/slippage constraints | FAIL_V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_FAILED | 1 | WARN_ACCEPTED | TRUE | R31C failed from propagated non-trading operator state, but produced structurally valid 252-row current-only cost output. |
| 6 | R31D account-aware manual trade plan | FAIL_V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_FAILED | 1 | WARN_ACCEPTED | TRUE | R31D failed from propagated non-trading operator state, but produced structurally valid 252-row current-only account-aware output. |
| 7 | R31E daily trade plan snapshot ledger | FAIL_V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_FAILED | 1 | WARN_ACCEPTED | TRUE | R31E returned FAIL from inherited non-trading/partial-freeze validation, but signal-date override, 252-row replace, and duplicate checks passed. |

## Child Statuses
- R31G: `WARN_V18_31G_TRADING_DAY_SIGNAL_DATE_BLOCKED_REUSE_LATEST`
- R30E: `FAIL_V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_FAILED`
- R31A: `WARN_V18_31A_STATIC_BUYABILITY_GATE_REVIEW_NEEDED`
- R31B: `WARN_V18_31B_MANUAL_POSITION_SIZING_POLICY_REVIEW_NEEDED`
- R31C: `FAIL_V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_FAILED`
- R31C-R1: `FAIL_V18_31C_R1_COST_PLAN_READABILITY_PATCH_FAILED`
- R31D: `FAIL_V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_FAILED`
- R31E: `FAIL_V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_FAILED`

## Key Counts
- Ranked rows: `252`
- Recommendation rows: `252`
- Theme rows: `252`
- R31A rows: `252`
- R31B rows: `252`
- R31C rows: `252`
- R31D rows: `252`
- R31E appended rows: `252`
- R31E post-ledger rows: `252`
- R31E duplicate keys: `0`

## Trade Readiness Counts
- Account trade allowed: `0`
- Account trade small-only: `0`
- Cost OK: `0`
- Blocked by min notional: `0`
- Review-first/no-current-trade: `0`
- Watch-only/no-current-trade: `0`
- Wait-pullback/no-current-trade: `0`

## Ledger Action
- Signal date: `2026-05-22`
- Snapshot date: `2026-05-24`
- Same-day policy: `REPLACE`
- Trading-day guard action: `REUSE_LATEST_SIGNAL_DATE_SKIP_NEW_LEDGER_DATE`
- Guard recommended signal date: `2026-05-22`

## Warnings
- `R31G:WARN_V18_31G_TRADING_DAY_SIGNAL_DATE_BLOCKED_REUSE_LATEST`
- `R31A:WARN_V18_31A_STATIC_BUYABILITY_GATE_REVIEW_NEEDED`
- `R31B:WARN_V18_31B_MANUAL_POSITION_SIZING_POLICY_REVIEW_NEEDED`
- `FORWARD_RETURN_NOT_READY`
- `WARN_TEMPLATE_EMPTY_ACCOUNT`

## Validation Failures
- `NONE`

## Safety
- AUTO_TRADE: `DISABLED`
- AUTO_SELL: `DISABLED`
- OFFICIAL_DECISION_IMPACT: `NONE`
- Broker/API calls: `NOT_EXECUTED`
- Order placement: `NOT_EXECUTED`
