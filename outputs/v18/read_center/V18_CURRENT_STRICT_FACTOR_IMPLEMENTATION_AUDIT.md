# V18.36C-R1 Strict Factor Implementation Audit

## Executive Conclusion

V18.36C-R1 reran the factor implementation audit with strict evidence rules. It separates true formula/output/current-pipeline implementation from proxies, report labels, shadow research, and discussion-only inventory items. No factor was added, no formula was changed, and no ranking/gate behavior was modified.

## What Changed From V18.36C To V18.36C-R1

- `IMPLEMENTED` was split into `REAL_IMPLEMENTED` and `PROXY_IMPLEMENTED`.
- Paper trading / forward attribution is treated as observation/shadow unless it feeds current ranking.
- Options fields such as GEX, put/call, and IV rank require true options-chain / open-interest / IV formula evidence for real implementation.
- Ranking impact now requires explicit current formula/output/pipeline evidence, not proximity to candidate-score fields.

## Strict Status Distribution

| strict_status | count |
|---|---|
| REAL_IMPLEMENTED | 16 |
| PROXY_IMPLEMENTED | 8 |
| SHADOW_ONLY | 11 |
| REPORT_ONLY | 3 |
| DISCUSSED_ONLY | 6 |
| MISSING | 17 |

## Downgraded Factors

| factor_id | factor_name | original_implementation_status | strict_implementation_status | downgrade_reason |
|---|---|---|---|---|
| F001 | WorldQuant / Factor Pack | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| F003 | factor_pack_score | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| F004 | factor_pack_rank | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| F005 | composite_candidate_score | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| T001 | Bollinger Bands / BB | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| T002 | RSI | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| T003 | KDJ | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| T004 | technical_timing_score | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| G001 | event risk gating | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| G002 | earnings / cloud earnings event risk | IMPLEMENTED | REPORT_ONLY | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| G003 | data freshness | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| G004 | price freshness | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| P001 | forward attribution / paper trading | IMPLEMENTED | SHADOW_ONLY | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| M001 | Relative Strength vs QQQ | IMPLEMENTED | SHADOW_ONLY | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| M005 | Drawdown from 20D High | IMPLEMENTED | SHADOW_ONLY | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| V003 | Volatility Expansion / Compression | IMPLEMENTED | PROXY_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| VOL001 | Volume Surge | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| VOL003 | Breakout Volume Confirmation | IMPLEMENTED | REAL_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| GROW001 | Revenue Growth | SHADOW_ONLY | MISSING | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| GROW002 | EPS Growth | SHADOW_ONLY | MISSING | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| VAL001 | Valuation / Growth Match | SHADOW_ONLY | MISSING | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| OPT002 | Gamma Exposure / GEX | IMPLEMENTED | PROXY_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| OPT003 | Call / Put Ratio | IMPLEMENTED | PROXY_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| OPT004 | IV Rank / IV Percentile | IMPLEMENTED | PROXY_IMPLEMENTED | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |
| MACRO005 | FOMC / CPI / PCE proximity | SHADOW_ONLY | MISSING | Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient. |

## Factors Still Confirmed As Real Ranking Inputs

| factor_id | factor_name | implementation_depth | ranking_formula_evidence | output_field_evidence |
|---|---|---|---|---|
| F001 | WorldQuant / Factor Pack | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/candidates/V18_25A_R27L_CURRENT_FULL_CANDIDATE_JOIN_AUDIT.csv;outputs/v18/candidates/V18_25A_R27L_CURRENT_POST_PROMOTION_VALIDAT |
| F003 | factor_pack_score | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv;outputs/v18/event_risk/V18_21E_CURRENT_EVE |
| F004 | factor_pack_rank | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/factor_effectiveness/V18_21C_CURRENT_EFFECTIVENESS_READINESS_AUDIT.csv;outputs/v18/factor_pack/V18_25A_R13_TARGETED_FACTOR_PACK_ |
| F005 | composite_candidate_score | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv;outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv;outpu |
| T001 | Bollinger Bands / BB | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py | outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv;outputs/v18/candidates/V18_RESTORED_RANKED_CANDIDATES_FROM_R29C_SNAPSH |
| T002 | RSI | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py | outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv;outputs/v18/candidates/V18_RESTORED_RANKED_CANDIDATES_FROM_R29C_SNAPSH |
| T003 | KDJ | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py | outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv;outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_ |
| T004 | technical_timing_score | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/candidates/V18_35D_FULL_UNIVERSE_COMPUTATION_STATUS.csv;outputs/v18/candidates/V18_35D_FULL_UNIVERSE_RECOMPUTE_FAILURES.csv;outp |
| T005 | overheat_penalty | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py | outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv;outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv;outpu |
| VOL001 | Volume Surge | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py | outputs/v18/factor_pack/V18_25A_R13_TARGETED_FACTOR_PACK_STAGED.csv;outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv;ou |
| VOL003 | Breakout Volume Confirmation | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py | outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_BACKTEST_DAILY_RETURNS.csv;outputs/v18/factor_backtest/V18_4H_CURRENT_FACTOR_LATEST_SCORES |

## Factors Confirmed As Gate Inputs

| factor_id | factor_name | implementation_depth | gate_formula_evidence | output_field_evidence |
|---|---|---|---|---|
| T005 | overheat_penalty | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py | outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv;outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv;outpu |
| G001 | event risk gating | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv;outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv;outpu |
| G003 | data freshness | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_34B_daily_output_freshness_guard.py;scripts/v18/v18_34C_trade_readiness_current_refresh.py;scripts/v18/v18_35F_next_signal_f | outputs/v18/forward_test/V18_25A_R21_CURRENT_SIGNAL_FREEZE_ROWS.csv;outputs/v18/forward_test/V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_ROWS.csv;o |
| G004 | price freshness | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_35D_full_universe_factor_technical_recompute.py;scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py;scripts/v18 | outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv;outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv;outpu |
| G005 | coverage status | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_34B_daily_output_freshness_guard.py;scripts/v18/v18_34C_trade_readiness_current_refresh.py;scripts/v18/v18_35D_full_universe | outputs/v18/coverage_resolution/V18_25A_R27E_CURRENT_TARGET_COVERAGE_RECHECK.csv;outputs/v18/factor_audit/V18_4F_CURRENT_FORWARD_FACTOR_COVE |
| G006 | Daily Trust Level | FORMULA_AND_OUTPUT_AND_PIPELINE | scripts/v18/v18_34B_daily_output_freshness_guard.py;scripts/v18/v18_34C_trade_readiness_current_refresh.py | outputs/v18/ops/V18_34B_DAILY_OUTPUT_FRESHNESS_SUMMARY.csv;outputs/v18/ops/V18_34C_TRADE_READINESS_REFRESH_SUMMARY.csv;outputs/v18/signal_sn |

## Proxy Factors

| factor_id | factor_name | strict_reason | output_field_evidence |
|---|---|---|---|
| M003 | Distance to 50DMA | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. | outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv;outputs/v18/market_regime/V18_21A_R1_CURRENT_LIGHTWEIGHT_MARKET_REGI |
| M006 | Drawdown from 52W High | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. | outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv;outputs/v18/market_regime/V18_21A_R1_CURRENT_LIGHTWEIGHT_MARKET_REGI |
| M008 | MA Alignment | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. | outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv |
| M009 | MA Slope | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. | outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv |
| V003 | Volatility Expansion / Compression | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. | outputs/v18/sell_timing/V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL.csv;outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECH |
| OPT002 | Gamma Exposure / GEX | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. | outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv;outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_ |
| OPT003 | Call / Put Ratio | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. | outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv;outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_ |
| OPT004 | IV Rank / IV Percentile | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. | outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv;outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_ |

## Report-Only / Shadow-Only Factors

| factor_id | factor_name | strict_implementation_status | implementation_depth | strict_reason |
|---|---|---|---|---|
| F002 | F002 | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Evidence is research/backtest/attribution oriented, not current ranking/gate formula. |
| G002 | earnings / cloud earnings event risk | REPORT_ONLY | REPORT_ONLY | Only report/read-center text evidence found. |
| P001 | forward attribution / paper trading | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Paper/forward attribution is implemented as observation layer and does not feed current ranking. |
| M001 | Relative Strength vs QQQ | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Evidence is research/backtest/attribution oriented, not current ranking/gate formula. |
| M002 | Distance to 20DMA | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. |
| M004 | Distance to 200DMA | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. |
| M005 | Drawdown from 20D High | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. |
| M007 | Buy-Zone Distance | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. |
| V001 | 20D Realized Volatility | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Evidence is research/backtest/attribution oriented, not current ranking/gate formula. |
| V002 | 60D Realized Volatility | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Evidence is research/backtest/attribution oriented, not current ranking/gate formula. |
| V004 | Return / Volatility Ratio | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Evidence is research/backtest/attribution oriented, not current ranking/gate formula. |
| VOL004 | Dry-Up Pullback | REPORT_ONLY | REPORT_ONLY | Only report/read-center text evidence found. |
| Q001 | QMJ | REPORT_ONLY | REPORT_ONLY | Only report/read-center text evidence found. |
| EV001 | continuous Event Risk Coefficient | SHADOW_ONLY | SHADOW_RESEARCH_ONLY | Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption. |

## Options-Factor Evidence Review

| factor_id | factor_name | strict_implementation_status | is_proxy_factor | strict_reason |
|---|---|---|---|---|
| OPT001 | Max Pain | MISSING | FALSE | No meaningful script/output/state/config evidence found. |
| OPT002 | Gamma Exposure / GEX | PROXY_IMPLEMENTED | TRUE | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. |
| OPT003 | Call / Put Ratio | PROXY_IMPLEMENTED | TRUE | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. |
| OPT004 | IV Rank / IV Percentile | PROXY_IMPLEMENTED | TRUE | Proxy/reserved field evidence found, but no confirmed full raw-data implementation. |
| OPT005 | IV-RV Spread | MISSING | FALSE | No meaningful script/output/state/config evidence found. |
| OPT006 | IV Crush Risk | MISSING | FALSE | No meaningful script/output/state/config evidence found. |

## Recommended Next Development Order

| factor_id | factor_name | strict_implementation_status | is_true_external_data_factor | recommended_validation_command |
|---|---|---|---|---|
| M003 | Distance to 50DMA | PROXY_IMPLEMENTED | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| M006 | Drawdown from 52W High | PROXY_IMPLEMENTED | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| M008 | MA Alignment | PROXY_IMPLEMENTED | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| M009 | MA Slope | PROXY_IMPLEMENTED | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| M010 | Trend Stability | DISCUSSED_ONLY | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| V003 | Volatility Expansion / Compression | PROXY_IMPLEMENTED | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| VOL002 | Up Volume Ratio | DISCUSSED_ONLY | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| GAP001 | Gap Up / Gap Down / Gap Size | DISCUSSED_ONLY | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| BETA001 | Beta vs QQQ | DISCUSSED_ONLY | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| BETA002 | Beta vs SPY | DISCUSSED_ONLY | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| BETA003 | BAB / Low Beta quality | DISCUSSED_ONLY | FALSE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| Q002 | ROE | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| Q003 | ROIC | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| Q004 | Gross Margin | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| Q005 | Operating Margin | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| Q006 | FCF Margin | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| Q007 | Debt / EBITDA | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| GROW001 | Revenue Growth | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| GROW002 | EPS Growth | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| VAL001 | Valuation / Growth Match | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| OPT001 | Max Pain | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| OPT002 | Gamma Exposure / GEX | PROXY_IMPLEMENTED | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| OPT003 | Call / Put Ratio | PROXY_IMPLEMENTED | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| OPT004 | IV Rank / IV Percentile | PROXY_IMPLEMENTED | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |
| OPT005 | IV-RV Spread | MISSING | TRUE | powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1 |

## Safety

- READ ONLY strict classification audit.
- No ranking formulas changed.
- No factor weights changed.
- No candidate files changed.
- No freeze ledgers changed.
- No universe state changed.
- No paper trading ledgers changed.
- No account state changed.
- No broker/API/order/auto-trade/auto-sell logic added.
- No yfinance or external data fetch was called.
- AUTO_TRADE DISABLED.
- AUTO_SELL DISABLED.
- OFFICIAL_DECISION_IMPACT NONE.
- FACTOR_WEIGHTS_MODIFIED FALSE.
- AUTO_WEIGHT_CHANGE DISABLED.
- FORBIDDEN_MODIFIED FALSE.
