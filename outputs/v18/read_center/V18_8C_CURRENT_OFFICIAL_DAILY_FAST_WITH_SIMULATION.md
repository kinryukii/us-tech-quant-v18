# V18.8C Official Daily Fast With Simulation

- STATUS: `OK_OFFICIAL_DAILY_FAST_WITH_SIMULATION_READY`
- MODE: `OFFICIAL_DAILY_PLUS_SHADOW_SIMULATION`
- TOTAL_SECONDS: `273.238`
- FINAL_ACTION: `BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION`
- BUY_PERMISSION: `UNKNOWN`
- VIX_REGIME: `VIX_CAUTION`
- OFFICIAL_DECISION_IMPACT: `NONE`

## Simulation Cabin

- SIM_STATUS: `OK_SIM_CABIN_READY`
- SIM_MODE: `SHADOW_ONLY`
- OFFICIAL_PERMISSION: `OFFICIAL_UNKNOWN_CONSERVATIVE_BLOCK`
- CASH_USD: `2000.0000`
- MARKET_VALUE_USD: `0.0000`
- EQUITY_USD: `2000.0000`
- POSITION_COUNT: `0`
- NEW_TRADE_LOG_ROWS_TODAY: `0`

## Files

- OFFICIAL_READ_FIRST: `D:\us-tech-quant\outputs\v18\read_center\V18_6E_READ_FIRST.txt`
- OFFICIAL_READ_CENTER: `D:\us-tech-quant\outputs\v18\read_center\V18_6E_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md`
- SIM_READ_FIRST: `D:\us-tech-quant\outputs\v18\simulation\V18_8B_READ_FIRST.txt`
- SIM_REPORT: `D:\us-tech-quant\outputs\v18\simulation\V18_CURRENT_SIM_CABIN.md`
- COMBINED_READ_FIRST: `D:\us-tech-quant\outputs\v18\read_center\V18_8C_READ_FIRST.txt`
- COMBINED_REPORT: `D:\us-tech-quant\outputs\v18\read_center\V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION.md`
- STEP_CSV: `D:\us-tech-quant\outputs\v18\ops\V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION_STEPS.csv`
- PROFILE: `D:\us-tech-quant\outputs\v18\ops\V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION_PROFILE.csv`

## Steps

| Step | Status | Seconds | Detail |
|---|---|---:|---|
| V18_7D_OFFICIAL_DAILY_FAST | OK | 272.797 | `D:\us-tech-quant\scripts\v18\run_v18_7D_official_daily_fast_main_with_technical.ps1` |
| V18_8B_SIMULATION_CABIN | OK | 0.365 | `D:\us-tech-quant\scripts\v18\run_v18_8B_current_simulation_cabin.ps1` |

## Interpretation

- The official daily decision remains the source of truth.
- The simulation cabin is shadow-only.
- Simulation output is now generated together with the official fast daily wrapper.
- No simulation result is allowed to modify official buy permission.
