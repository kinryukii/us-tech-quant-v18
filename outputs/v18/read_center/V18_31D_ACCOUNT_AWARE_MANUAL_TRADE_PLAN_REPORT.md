# V18 Current Account-Aware Manual Trade Plan

## 1. Final Status
STATUS: FAIL_V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_FAILED

## 2. Run Id / Timestamp
RUN_ID: V18_31D_20260524_182841
GENERATED_AT: 2026-05-24T18:28:41

## 3. Account State Mode And Quality
- ACCOUNT_STATE_MODE: `TEMPLATE_OR_EMPTY_ACCOUNT_ASSUMPTION`
- ACCOUNT_STATE_QUALITY_FLAG: `WARN_TEMPLATE_EMPTY_ACCOUNT`
- Manual account state is operator-maintained and must be updated before relying on account-aware constraints.

## 4. Account Assumptions
- Account total value USD: `2000.00`
- Cash USD: `2000.00`
- Reserve required USD: `300.00`
- Available cash after reserve USD: `1700.00`
- Max active positions: `8`
- Max speculative positions: `2`
- Max theme exposure pct: `35.0000`
- Max high-risk exposure pct: `25.0000`

## 5. Account-Aware Status Counts
| account_trade_status | count |
| --- | --- |
| BLOCKED_BY_OPERATOR_STATE | 252 |

## 6. Today's Account-Eligible Manual Buy Candidates
_None._

## 7. Blocked By Account Constraints
_None._

## 8. Preserved Non-Trade Groups
### Watch-Only
_None._

### Wait-Pullback
_None._

### Review-First
_None._

### Cost-Plan Blocked
_None._

## 9. Current Theme Exposure Summary
_None._

## 10. Safety
- Manual research guidance only.
- No broker connection.
- No order placement.
- Manual account file must be updated by operator.
- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `OFFICIAL_DECISION_IMPACT: NONE`

## 11. Warnings
- `FORWARD_RETURN_NOT_READY_ACCOUNT_PLAN_ONLY`
- `WARN_TEMPLATE_EMPTY_ACCOUNT`
- `TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA`

## 12. Next Step Recommendation
- R31E Daily Trade Plan Snapshot Ledger.
- R29D/R33A forward validation when future price data exists.
