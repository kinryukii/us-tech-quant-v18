# V18.32A Manual Account State Validation Report

## 1. Final Validation Status
STATUS: WARN_V18_32A_MANUAL_ACCOUNT_STATE_TEMPLATE_REVIEW_NEEDED

## 2. Current Account State Mode And Quality
- ACCOUNT_STATE_MODE: `TEMPLATE_OR_EMPTY_ACCOUNT_ASSUMPTION`
- ACCOUNT_STATE_QUALITY: `WARN_TEMPLATE_EMPTY_ACCOUNT`
- ACCOUNT_STATE_FILE: `D:\us-tech-quant\state\v18\manual_account\V18_MANUAL_ACCOUNT_STATE.csv`

## 3. Template / Empty Account Check
- TEMPLATE_EMPTY_ACCOUNT: `TRUE`
- If this is TRUE, V18.31D/R31F account-aware outputs are based on a cash-only manual assumption, not real holdings.

## 4. How To Update The Manual Account File
Edit `state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE.csv` manually.
- Keep one `CASH_USD` row with total account value and cash.
- Add one row per holding with ticker, shares, average cost, current price, market value, position percent, theme, and position type.
- Use manually verified values only. This validator does not connect to a broker and does not fetch prices.

## 5. Example Rows
```csv
account_id,as_of_date,account_total_value_usd,cash_usd,ticker,shares,avg_cost_usd,current_price_usd,market_value_usd,position_pct,primary_theme,position_type,notes
MANUAL_DEFAULT,2026-05-22,2000.00,650.00,CASH_USD,0,0,1,0,0,CASH,CASH,MANUAL_CASH_BALANCE
MANUAL_DEFAULT,2026-05-22,2000.00,650.00,NVDA,1,100.00,120.00,120.00,6.00,AI_INFRA,CORE_HOLDING,MANUALLY_VERIFIED_HOLDING
```

## 6. Required Columns
| column | purpose |
| --- | --- |
| account_id | Manual account identifier. |
| as_of_date | Date the manual values were verified. |
| account_total_value_usd | Total account value in USD. |
| cash_usd | Available cash balance in USD. |
| ticker | CASH_USD or holding ticker. |
| shares | Manual share quantity. |
| avg_cost_usd | Manual average cost per share. |
| current_price_usd | Manual current price per share. |
| market_value_usd | Manual holding market value. |
| position_pct | Holding market value divided by account total value. |
| primary_theme | Theme used for exposure checks. |
| position_type | CASH, CORE_HOLDING, SPECULATIVE, ETF, or another operator label. |
| notes | Manual source notes and warnings. |

## 7. How R31D/R31F Use This File
- R31D reads this file to calculate existing position exposure, cash availability, theme exposure, high-risk exposure, active positions, and whether a current COST_OK name can be considered manually.
- R31F uses R31D as part of the full daily trade-readiness homepage.
- If this file is updated, rerun V18.32A first, then rerun R31F.

## 8. Current Normalized Holdings Preview
| ticker | normalized_market_value_usd | normalized_position_pct | primary_theme | position_type | row_quality | row_warnings |
| --- | --- | --- | --- | --- | --- | --- |
| CASH_USD | 2000.00 | 100.0000 | CASH | CASH | WARN_TEMPLATE_EMPTY_ACCOUNT | TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA |

## 9. Validation Warnings And Failures
### Failures
_None._

### Warnings
| check_name | affected_ticker | message | suggested_fix |
| --- | --- | --- | --- |
| TEMPLATE_EMPTY_ACCOUNT | CASH_USD | Manual account file is still the template/empty cash-only assumption. | Before relying on account-aware constraints, replace the template row values and add real manually verified holdings. |

## 10. Safety
- Manual file only.
- No broker connection.
- No order placement.
- No external data fetch.
- User must verify all values manually before relying on account-aware constraints.
- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `OFFICIAL_DECISION_IMPACT: NONE`

## 11. Next Step
- If template/empty: edit the manual account file with real cash and holdings, then rerun V18.32A and R31F.
- If valid: rerun R31F so account-aware trade-readiness uses the updated manual account state.
