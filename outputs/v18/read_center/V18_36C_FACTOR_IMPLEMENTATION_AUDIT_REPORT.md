# V18.36C Factor Implementation Audit

## Executive Conclusion

V18.36C completed a read-only factor implementation audit across `scripts/v18`, `outputs/v18`, `state/v18`, and `configs/v18`. It maps every canonical factor to exactly one status: IMPLEMENTED, SHADOW_ONLY, DISCUSSED_ONLY, or MISSING. The audit did not change ranking formulas, factor weights, candidates, freeze ledgers, universe state, paper trading ledgers, account state, or trading logic.

## Status Distribution

| status | count |
|---|---|
| IMPLEMENTED | 24 |
| SHADOW_ONLY | 16 |
| DISCUSSED_ONLY | 7 |
| MISSING | 14 |

## Factors That Affect Current Ranking

| factor_id | factor_name | factor_group | current_field_names | confidence |
|---|---|---|---|---|
| F001 | WorldQuant / Factor Pack | Factor Pack | bucket_factor_pack_missing_count;current_in_factor_pack;factor_pack_available;factor_pack_present;factor_pack_present_cu | HIGH |
| F003 | factor_pack_score | Factor Pack | factor_pack_score;factor_pack_score_available;factor_pack_score_present_current | HIGH |
| F004 | factor_pack_rank | Factor Pack | factor_pack_rank;factor_pack_rank_available;factor_pack_rank_present | HIGH |
| F005 | composite_candidate_score | Ranking | "composite_candidate_score";candidate_score;composite_candidate_score;current_candidate_score | HIGH |
| T001 | Bollinger Bands / BB | Technical | "bb_status";bb_bandwidth;bb_lower_20_2;bb_mid_20;bb_percent_b;bb_squeeze_flag;bb_status;bb_upper_20_2;signal_bb_squeeze | HIGH |
| T002 | RSI | Technical | "rsi_status";rsi_14;rsi_status | HIGH |
| T003 | KDJ | Technical | kdj_d;kdj_j;kdj_k | HIGH |
| T004 | technical_timing_score | Technical | "technical_timing_score";technical_timing_score;technical_timing_score_available;technical_timing_score_present | HIGH |
| T005 | overheat_penalty | Technical | "overheat_penalty";overheat_penalty;overheat_penalty_available;overheat_status | HIGH |
| G001 | event risk gating | Gate | calendar_market_event_risk_coefficient;calendar_market_event_risk_level;calendar_ticker_event_risk_coefficient;calendar_ | HIGH |
| G003 | data freshness | Gate | data_freshness_status;freshness_round_consistent;freshness_status;price_freshness_status;source_freshness_status | HIGH |
| G004 | price freshness | Gate | latest_price_date;price_asof_date;price_freshness_status | HIGH |
| P001 | forward attribution / paper trading | Paper Trading | average_forward_return;avg_forward_return;dryrun_forward_return;dryrun_forward_return_formula;dryrun_forward_return_prev | HIGH |
| V003 | Volatility Expansion / Compression | Volatility | bb_squeeze_flag;signal_bb_squeeze | HIGH |
| VOL001 | Volume Surge | Volume | volume_ratio_5_20 | HIGH |
| VOL003 | Breakout Volume Confirmation | Volume | F009_VOLUME_PRICE_CONFIRM;F009_VOLUME_PRICE_CONFIRM__LONG_ONLY_TOPN;F009_VOLUME_PRICE_CONFIRM__LONG_SHORT_SPREAD;F009_VO | HIGH |
| OPT002 | Gamma Exposure / GEX | Options | gamma_squeeze_risk_label;gamma_squeeze_status | HIGH |
| OPT003 | Call / Put Ratio | Options | put_call_ratio | HIGH |
| OPT004 | IV Rank / IV Percentile | Options | iv_rank_proxy | HIGH |

## Factors That Affect Official Gates But Not Ranking

| factor_id | factor_name | factor_group | current_field_names | confidence |
|---|---|---|---|---|
| G002 | earnings / cloud earnings event risk | Gate |  | MEDIUM |
| G005 | coverage status | Gate | "coverage_status";COVERAGE_SHORTFALL_COUNT;COVERAGE_TARGET_MET;COVERAGE_WINDOW_TRADING_DAYS;compact_latest_freeze_covera | MEDIUM |
| G006 | Daily Trust Level | Gate | daily_trust_level | MEDIUM |
| M001 | Relative Strength vs QQQ | Relative Strength | can_compute_relative_strength_vs_qqq;relative_strength_vs_qqq | MEDIUM |
| M005 | Drawdown from 20D High | Drawdown | drawdown_20d_high;max_drawdown_20d | MEDIUM |

## Shadow-Only / Research-Only Factors

| factor_id | factor_name | factor_group | matched_scripts | matched_outputs |
|---|---|---|---|---|
| F002 | F002 | Factor Pack | scripts/v18/run_v18_4D_factor_pack_audit.ps1;scripts/v18/run_v18_4G_R2_stable_snapshot.ps1 | outputs/v18/cockpit/V18_3E_CURRENT_DAILY_COCKPIT.md;outputs/v18/cockpit/V18_3E_CURRENT_DAILY_COCKPIT.txt;outputs/v18/coc |
| M002 | Distance to 20DMA | Moving Average | scripts/v18/v18_16C_scan_scoped_data_update.py;scripts/v18/v18_16D_priority_based_light_scanner.py;scripts/v18/v18_17A_r | outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_REPORT.md;outputs/v18/factor_pack/V18_3D_R2_CURRENT_RAW105_FACTOR_P |
| M003 | Distance to 50DMA | Moving Average | scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py;scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py;scri | outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv;outputs/v18/market_regime/V18_21A_R1_CURRENT_LIG |
| M004 | Distance to 200DMA | Moving Average | scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py;scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py;scri | outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv;outputs/v18/market_regime/V18_21A_R1_CURRENT_LIG |
| M006 | Drawdown from 52W High | Drawdown | scripts/v18/v18_16A_universe_rolling_state_builder.py;scripts/v18/v18_16D_priority_based_light_scanner.py;scripts/v18/v1 | outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv;outputs/v18/market_regime/V18_21A_R1_CURRENT_LIG |
| M007 | Buy-Zone Distance | Entry Quality | scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py;scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py;scri | outputs/v18/factor_effectiveness/V18_21C_CURRENT_EFFECTIVENESS_READINESS_AUDIT.csv;outputs/v18/ops/V18_21A_CURRENT_PRICE |
| M008 | MA Alignment | Moving Average | scripts/v18/v18_21A_price_derived_factor_pack.py | outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv |
| M009 | MA Slope | Moving Average | scripts/v18/v18_21A_price_derived_factor_pack.py | outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv |
| V001 | 20D Realized Volatility | Volatility | scripts/v18/v18_11_calendar_vwap_rv_shadow_factors.py;scripts/v18/v18_16D_priority_based_light_scanner.py;scripts/v18/v1 | outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_REPORT.md;outputs/v18/factor_pack/V18_3D_R2_CURRENT_RAW105_FACTOR_P |
| V002 | 60D Realized Volatility | Volatility | scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py;scripts/v18/v18_21A_price_derived_factor_pack.py | outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv;outputs/v18/price_factors/V18_21A_R2_CURRENT_TICKER_ |
| V004 | Return / Volatility Ratio | Volatility | scripts/v18/v18_18F_technical_timing_current_detail_slimming.py;scripts/v18/v18_4H_R1A_factor_robustness_interpretation_ | outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_REPORT.md;outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_BACKTES |
| GROW001 | Revenue Growth | Growth | scripts/v18/v18_10A_factor_registry_coverage_audit.py |  |
| GROW002 | EPS Growth | Growth | scripts/v18/v18_10A_factor_registry_coverage_audit.py |  |
| VAL001 | Valuation / Growth Match | Valuation | scripts/v18/v18_10A_factor_registry_coverage_audit.py |  |
| MACRO005 | FOMC / CPI / PCE proximity | Macro Event | scripts/v18/v18_10A_factor_registry_coverage_audit.py;scripts/v18/v18_21E_event_risk_coefficient_engine.py |  |
| EV001 | continuous Event Risk Coefficient | Event Risk | scripts/v18/run_v18_21E_R1_hard_lock_overlay_semantics_patch.ps1;scripts/v18/run_v18_21E_R1_stable_snapshot.ps1;scripts/ | outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_REPORT.md;outputs/v18/event_risk/V18_21E_CURRENT_EVENT_ADJUSTED_CAN |

## Missing But Low-Data-Cost Candidates

| factor_id | factor_name | factor_group | implementation_status | recommended_next_action |
|---|---|---|---|---|
| M010 | Trend Stability | Trend | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |
| VOL002 | Up Volume Ratio | Volume | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |
| VOL004 | Dry-Up Pullback | Volume | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |
| GAP001 | Gap Up / Gap Down / Gap Size | Gap | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |
| BETA001 | Beta vs QQQ | Beta | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |
| BETA002 | Beta vs SPY | Beta | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |
| BETA003 | BAB / Low Beta quality | Beta | DISCUSSED_ONLY | Prototype as shadow metric first; do not change official weights. |

## Missing And High-Data-Cost Candidates

| factor_id | factor_name | factor_group | implementation_status | recommended_next_action |
|---|---|---|---|---|
| Q001 | QMJ | Quality | MISSING | Defer until required data source and validation plan exist. |
| Q002 | ROE | Quality | MISSING | Defer until required data source and validation plan exist. |
| Q003 | ROIC | Quality | MISSING | Defer until required data source and validation plan exist. |
| Q004 | Gross Margin | Quality | MISSING | Defer until required data source and validation plan exist. |
| Q005 | Operating Margin | Quality | MISSING | Defer until required data source and validation plan exist. |
| Q006 | FCF Margin | Quality | MISSING | Defer until required data source and validation plan exist. |
| Q007 | Debt / EBITDA | Quality | MISSING | Defer until required data source and validation plan exist. |
| OPT001 | Max Pain | Options | MISSING | Defer until required data source and validation plan exist. |
| OPT005 | IV-RV Spread | Options | MISSING | Defer until required data source and validation plan exist. |
| OPT006 | IV Crush Risk | Options | MISSING | Defer until required data source and validation plan exist. |
| MACRO001 | High Yield Spread | Macro | MISSING | Defer until required data source and validation plan exist. |
| MACRO002 | Credit Spread | Macro | MISSING | Defer until required data source and validation plan exist. |
| MACRO003 | Treasury Yield Regime | Macro | MISSING | Defer until required data source and validation plan exist. |
| MACRO004 | DXY | Macro | MISSING | Defer until required data source and validation plan exist. |

## Recommended Next Development Order

| factor_id | factor_name | factor_group | extra_data_required | recommended_next_action |
|---|---|---|---|---|
| M010 | Trend Stability | Trend | FALSE | Prototype as shadow metric first; do not change official weights. |
| VOL002 | Up Volume Ratio | Volume | FALSE | Prototype as shadow metric first; do not change official weights. |
| VOL004 | Dry-Up Pullback | Volume | FALSE | Prototype as shadow metric first; do not change official weights. |
| GAP001 | Gap Up / Gap Down / Gap Size | Gap | FALSE | Prototype as shadow metric first; do not change official weights. |
| BETA001 | Beta vs QQQ | Beta | FALSE | Prototype as shadow metric first; do not change official weights. |
| BETA002 | Beta vs SPY | Beta | FALSE | Prototype as shadow metric first; do not change official weights. |
| BETA003 | BAB / Low Beta quality | Beta | FALSE | Prototype as shadow metric first; do not change official weights. |
| Q001 | QMJ | Quality | TRUE | Defer until required data source and validation plan exist. |
| Q002 | ROE | Quality | TRUE | Defer until required data source and validation plan exist. |
| Q003 | ROIC | Quality | TRUE | Defer until required data source and validation plan exist. |
| Q004 | Gross Margin | Quality | TRUE | Defer until required data source and validation plan exist. |
| Q005 | Operating Margin | Quality | TRUE | Defer until required data source and validation plan exist. |

## Safety

- READ ONLY audit mode.
- No ranking formulas changed.
- No factor weights changed.
- No candidate files changed.
- No freeze ledgers changed.
- No universe state changed.
- No paper trading ledgers changed.
- No account state changed.
- No broker/API/order/auto-trade/auto-sell logic added.
- AUTO_TRADE DISABLED.
- AUTO_SELL DISABLED.
- OFFICIAL_DECISION_IMPACT NONE.
- FACTOR_WEIGHTS_MODIFIED FALSE.
- AUTO_WEIGHT_CHANGE DISABLED.
