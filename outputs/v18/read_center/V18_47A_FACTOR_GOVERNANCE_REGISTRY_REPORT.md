# V18.47A Factor Governance Registry Report

V18.47A is a read-only governance registry. It does not modify official ranking logic, factor weights, Top20 selection, freshness eligibility, trading execution, broker behavior, order behavior, or signal freeze ledgers.

## Counts
| metric | value |
| --- | --- |
| OFFICIAL_ACTIVE | 3 |
| OFFICIAL_SMALL_WEIGHT | 2 |
| PLANNED_NOT_IMPLEMENTED | 8 |
| RESEARCH_ONLY | 26 |
| RISK_ADJUSTED_ONLY | 1 |
| RISK_GATE_ONLY | 25 |
| SHADOW_ONLY | 6 |

## Official factors currently affecting ranking
| factor_id | factor_group | current_status | official_weight | notes |
| --- | --- | --- | --- | --- |
| factor_pack_rank | ALPHA | OFFICIAL_ACTIVE |  | Official current ranking input inventory; V18.47A records status only. |
| factor_pack_score | ALPHA | OFFICIAL_ACTIVE | CURRENT_SYSTEM_WEIGHT | Official current ranking input inventory; V18.47A records status only. |
| overheat_penalty | TECHNICAL_TIMING | RISK_ADJUSTED_ONLY | CURRENT_SYSTEM_PENALTY_IF_PRESENT | Risk adjustment only; no promotion or demotion in V18.47A. |
| technical_status | TECHNICAL_TIMING | OFFICIAL_SMALL_WEIGHT | CURRENT_SYSTEM_WEIGHT_OR_LABEL | Small-weight or label-style technical input; no V18.47A weight change. |
| technical_timing_score | TECHNICAL_TIMING | OFFICIAL_ACTIVE | CURRENT_SYSTEM_WEIGHT | Official current ranking input inventory; V18.47A records status only. |

## Shadow factors currently not affecting ranking
| factor_id | factor_group | future_leak_risk | notes |
| --- | --- | --- | --- |
| bb_status | TECHNICAL_TIMING | LOW | Shadow-only unless separately promoted by evidence outside V18.47A. |
| exit_signal_forward_validation | TECHNICAL_TIMING | HIGH | Shadow-only unless separately promoted by evidence outside V18.47A. |
| kdj_shadow_signal | TECHNICAL_TIMING | LOW | Shadow-only unless separately promoted by evidence outside V18.47A. |
| macd_shadow_signal | TECHNICAL_TIMING | LOW | Shadow-only unless separately promoted by evidence outside V18.47A. |
| rsi_status | TECHNICAL_TIMING | LOW | Shadow-only unless separately promoted by evidence outside V18.47A. |
| sell_timing_shadow_label | TECHNICAL_TIMING | LOW | Shadow-only unless separately promoted by evidence outside V18.47A. |

## Risk-gate factors
| factor_id | factor_group | current_status | notes |
| --- | --- | --- | --- |
| actionable_allowed_by_freshness | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| blocking_current_failure_count | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| candidate_report_trust | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| current_authoritative_chain_ready | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| daily_trust_level | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| freshness_eligibility | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| price_freshness | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| stale_price_data_flag | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| top_full_mismatch_count | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| validation_fail_count | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| days_to_earnings | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| earnings_event_risk | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| earnings_window_flag | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| macro_event_risk | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| sector_event_exposure | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| manual_event_override | MANUAL_FEEDBACK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| market_regime | MARKET_REGIME | RISK_GATE_ONLY | Market/regime inventory only; no official ranking formula change. |
| vix_risk_flag | MARKET_REGIME | RISK_GATE_ONLY | Market/regime inventory only; no official ranking formula change. |
| high_beta_exposure | PORTFOLIO_RISK | RISK_GATE_ONLY | Risk governance only; does not alter official candidate scoring in V18.47A. |
| portfolio_concentration_risk_score | PORTFOLIO_RISK | RISK_GATE_ONLY | Risk governance only; does not alter official candidate scoring in V18.47A. |
| sector_exposure | PORTFOLIO_RISK | RISK_GATE_ONLY | Risk governance only; does not alter official candidate scoring in V18.47A. |
| single_name_position_limit | PORTFOLIO_RISK | RISK_GATE_ONLY | Risk governance only; does not alter official candidate scoring in V18.47A. |
| theme_exposure | PORTFOLIO_RISK | RISK_GATE_ONLY | Risk governance only; does not alter official candidate scoring in V18.47A. |
| overheat_penalty | TECHNICAL_TIMING | RISK_ADJUSTED_ONLY | Risk adjustment only; no promotion or demotion in V18.47A. |
| invalid_pseudo_ticker_filter | UNIVERSE_COVERAGE | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| unavailable_ticker_quarantine | UNIVERSE_COVERAGE | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |

## Data-quality and system trust factors
| factor_id | factor_group | current_status | notes |
| --- | --- | --- | --- |
| actionable_allowed_by_freshness | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| blocking_current_failure_count | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| candidate_report_trust | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| current_authoritative_chain_ready | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| daily_trust_level | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| freshness_eligibility | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| price_freshness | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| stale_price_data_flag | DATA_QUALITY | RISK_GATE_ONLY | Freshness is a gate/control, not an alpha factor. |
| top_full_mismatch_count | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| validation_fail_count | DATA_QUALITY | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| invalid_pseudo_ticker_filter | UNIVERSE_COVERAGE | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |
| unavailable_ticker_quarantine | UNIVERSE_COVERAGE | RISK_GATE_ONLY | Trust and quality controls are not alpha factors. |

## Planned options, event, and action-response factors
| factor_id | factor_group | current_status | notes |
| --- | --- | --- | --- |
| buy_risk_score | ACTION_RESPONSE | RESEARCH_ONLY | Action response remains advisory/read-center only. |
| entry_strategy | ACTION_RESPONSE | RESEARCH_ONLY | Action response remains advisory/read-center only. |
| exit_plan_present | ACTION_RESPONSE | RESEARCH_ONLY | Action response remains advisory/read-center only. |
| exit_strategy | ACTION_RESPONSE | RESEARCH_ONLY | Action response remains advisory/read-center only. |
| hold_risk_score | ACTION_RESPONSE | RESEARCH_ONLY | Action response remains advisory/read-center only. |
| sell_risk_score | ACTION_RESPONSE | RESEARCH_ONLY | Action response remains advisory/read-center only. |
| days_to_earnings | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| earnings_event_risk | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| earnings_window_flag | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| macro_event_risk | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| sector_event_exposure | EVENT_RISK | RISK_GATE_ONLY | Event risk is conservative gate/research inventory only. |
| atm_iv | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| expected_move_pct | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| iv_rank | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| option_liquidity_status | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| option_volume_abnormal_flag | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| options_risk_level | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| put_call_ratio | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |
| skew_score | OPTIONS_RISK | PLANNED_NOT_IMPLEMENTED | Options factors remain non-ranking controls in V18.47A. |

## High future-leak-risk factors
| factor_id | factor_group | future_leak_reason | used_in_official_ranking |
| --- | --- | --- | --- |
| alpha_after_beta_adjustment | FORWARD_ATTRIBUTION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| benchmark_excess_return | FORWARD_ATTRIBUTION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| beta_to_qqq | FORWARD_ATTRIBUTION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| maturity_10d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| maturity_20d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| maturity_5d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| maturity_60d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| max_drawdown_20d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| max_drawdown_60d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| return_10d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| return_20d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| return_5d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| return_60d | STRATEGY_VALIDATION | Requires future returns or post-signal outcomes; prohibited from official ranking. | FALSE |
| exit_signal_forward_validation | TECHNICAL_TIMING | Forward validation must not be used for same-day ranking. | FALSE |

## Promotion and demotion governance principles
- Promotion requires as-of availability, reproducible backtest evidence, walk-forward evidence, live-forward samples, and explicit approval outside this patch.
- Forward returns, realized drawdowns, maturity flags, and benchmark attribution are validation fields only and must not enter same-day ranking.
- Demotion requires documented underperformance or operational risk evidence; V18.47A performs no demotion.
- Uncertain factors stay RESEARCH_ONLY or SHADOW_ONLY.
