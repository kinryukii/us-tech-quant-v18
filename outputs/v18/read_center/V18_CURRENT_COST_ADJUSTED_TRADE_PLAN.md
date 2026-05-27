# V18 Current Cost-Adjusted Trade Plan

1. Final status / run id / timestamp.
STATUS: FAIL_V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_FAILED
RUN_ID: V18_31C_20260524_182841
GENERATED_AT: 2026-05-24T18:28:41

2. Broker profile and fee assumptions.
- Broker profile: `MOOMOO_JP_US_STOCK_BASIC`
- Commission rate pct: `0.1320`
- Commission min USD: `0.00`
- Commission cap USD: `22.00`
- Conservative FX stress assumption JPY/USD: `0.2500`
- Moomoo fee assumptions are configurable and must be verified against the current broker fee schedule before live trading.

3. Cost-adjusted status counts.
| cost_adjusted_trade_status | count |
| --- | --- |
| COST_OK | 0 |
| COST_OK_SMALL_ONLY | 0 |
| COST_REVIEW_REQUIRED | 0 |
| COST_WATCH_ONLY | 0 |
| COST_WAIT_PULLBACK | 0 |
| BLOCKED_BY_MIN_NOTIONAL | 0 |
| BLOCKED_BY_POSITION_POLICY | 0 |
| BLOCKED_BY_OPERATOR_STATE | 252 |
| BLOCKED_BY_DATA_QUALITY | 0 |
| BLOCKED_BY_COST | 0 |

4. Operator readability bucket counts.
| operator_readability_bucket | count |
| --- | --- |
| CURRENT_COST_OK | 0 |
| CURRENT_SMALL_ONLY_COST_OK | 0 |
| CURRENT_BLOCKED_MIN_NOTIONAL | 0 |
| CURRENT_TRUE_COST_REVIEW | 0 |
| REVIEW_FIRST_NOT_TRADE_NOW | 0 |
| WATCH_ONLY_NOT_TRADE_NOW | 0 |
| WAIT_PULLBACK_NOT_TRADE_NOW | 0 |
| BLOCKED_NOT_TRADE | 0 |
| OPERATOR_OR_DATA_BLOCKED | 252 |

5. Today's Current Cost-OK Manual Review Candidates.
- These are not automatic buy orders; they passed static buyability, position, and cost gates.
_None._

6. Current Blocked By Minimum Notional.
- The model may like these, but the current suggested trade size is too small for the configured minimum effective notional.
_None._

7. Review-First / No Current Trade.
- These are not cost failures. They are review-first names with no current trade notional.
_None._

8. Watch-Only / No Current Trade.
- These are not current trades.
_None._

9. Wait-Pullback / No Current Trade.
- These are not current trades.
_None._

10. True Cost Review Required.
- Only rows with suggested_initial_notional_usd > 0 are shown here.
_None._

11. Cost model assumptions.
| assumption | value |
| --- | --- |
| broker_profile | MOOMOO_JP_US_STOCK_BASIC |
| commission_rate_pct | 0.1320 |
| commission_min_usd | 0.00 |
| commission_cap_usd | 22.00 |
| fx_fee_jpy_per_usd | 0.0000 |
| conservative_fx_fee_jpy_per_usd | 0.2500 |
| min_effective_trade_notional_usd | 50.00 |
| cost_safety_multiple | 2.0000 |

12. Safety.
- Manual research guidance only.
- No broker connection.
- No order placement.
- Fee assumptions must be verified before live trading.
- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `OFFICIAL_DECISION_IMPACT: NONE`

13. Warnings.
- `FORWARD_RETURN_NOT_READY_COST_MODEL_ONLY`

14. Next step recommendation.
- Review the readability split and keep all trading decisions manual.
- R31D account-aware manual plan later.
- R29D/R33A forward validation when future price data exists.
