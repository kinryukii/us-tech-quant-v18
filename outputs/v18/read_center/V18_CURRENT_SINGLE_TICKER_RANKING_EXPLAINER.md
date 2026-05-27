# V18.42A Single Ticker Ranking Explainer

## 1. Operator Summary / 操作员摘要
- Ticker: `FORM`
- Company/name: 
- Current rank: 1
- Candidate pool size: 318
- Composite score column/value: composite_candidate_score = 59.2
- Latest signal/as-of date: 2026-05-27
- Ranking source file: D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv
- Report status: WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED

## 2. Why This Rank? / 为什么排在这里？
这个 ticker 排在当前名次，直接原因是当前 ranked candidate 输出中 `composite_candidate_score` 为 `59.2`。本解释器不重算官方排名，只读取已有排名输出。
它相对前后名候选的差异，主要来自下方 neighbor comparison 中差异最大的字段。
- Strongest positive descriptive drivers: composite_candidate_score=59.2; score_source_status=OK_RECOMPUTED_FACTOR_TECHNICAL; technical_status=TECH_TIMING_PULLBACK_WATCH; factor_pack_score=100.0; F010_XSEC_COMPOSITE_RANK=100.0; F011_TS_MOMENTUM_60_120=79.047619; pullback_timing_bonus=14; technical_timing_score=64.0
- Strongest negative/penalty descriptive drivers: rank=1; factor_pack_rank=2; volatility_penalty=71.428571; bb_percent_b=-0.0604; rsi_14=39.3157; kdj_k=20.4134; kdj_d=32.2286; kdj_j=-3.2171
- 未发现可靠当前权重文件时，所有 attribution 均标记为 DESCRIPTIVE_ONLY，不声称精确公式权重。

## 3. Score Component Breakdown / 分数组件拆解
| column_name | ticker_value | pool_median | pool_percentile | direction | source | role | mode |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| rank | 1 | 159.5000 | 0.3145 | NEGATIVE | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| composite_candidate_score | 59.2 | 32.4906 | 100.0000 | POSITIVE | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  |  | UNKNOWN | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  |  | UNKNOWN | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  |  | POSITIVE | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  |  | UNKNOWN | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| score_source_columns | factor_pack_score;technical_timing_score |  |  | UNKNOWN | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| technical_status | TECH_TIMING_PULLBACK_WATCH |  |  | POSITIVE | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| event_risk_status |  |  |  | UNKNOWN | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| overheat_status | NOT_AVAILABLE_RESERVED |  |  | UNKNOWN | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| factor_pack_rank | 2 | 124.5000 | 1.5873 | NEGATIVE | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| factor_pack_score | 100.0 | 41.9759 | 100.0000 | POSITIVE | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| F010_XSEC_COMPOSITE_RANK | 100.0 | 41.9783 | 100.0000 | POSITIVE | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| F011_TS_MOMENTUM_60_120 | 79.047619 | 41.0491 | 82.9365 | POSITIVE | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| volatility_penalty | 71.428571 | 50.4762 | 71.3376 | NEGATIVE | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| overheat_penalty | 39.047619 | 50.4762 | 38.8535 | NEUTRAL | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_mid_20 | 139.203 | 123.4945 | 53.1746 | NEUTRAL | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_upper_20_2 | 158.6378 | 140.8338 | 53.1746 | NEUTRAL | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_lower_20_2 | 119.7682 | 109.3827 | 54.3651 | NEUTRAL | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_percent_b | -0.0604 | 0.4855 | 1.9841 | NEGATIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_bandwidth | 0.2792 | 0.2281 | 64.2857 | NEUTRAL | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_squeeze_flag | False |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| bb_status | BB_BELOW_LOWER |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| rsi_14 | 39.3157 | 51.9380 | 17.8571 | NEGATIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| rsi_status | RSI_WEAK |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| kdj_k | 20.4134 | 45.7261 | 15.8730 | NEGATIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| kdj_d | 32.2286 | 49.0996 | 28.5714 | NEGATIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| kdj_j | -3.2171 | 33.5957 | 3.9683 | NEGATIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| kdj_status | KDJ_NEUTRAL |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| overheat_penalty | 0 | 0.0000 | 88.4921 | NEGATIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| pullback_timing_bonus | 14 | 0.0000 | 94.8413 | POSITIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| technical_timing_score | 64.0 | 50.0000 | 82.5397 | POSITIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| technical_signal | TECH_TIMING_PULLBACK_WATCH |  |  | POSITIVE | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| technical_warning_label | NONE |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| iv_rank_proxy |  |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| gamma_squeeze_risk_label | NOT_AVAILABLE_RESERVED |  |  | UNKNOWN | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| candidate_rank | 1 | 159.5000 | 0.3145 | NEGATIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| composite_candidate_score | 59.2 | 32.4906 | 100.0000 | POSITIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| factor_pack_score |  |  |  | UNKNOWN | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| technical_timing_score | 64.0 | 50.0000 | 80.8176 | POSITIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| kdj_k | 15.2101 | 48.4184 | 6.3091 | NEGATIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| kdj_d | 31.9855 | 47.5150 | 28.0757 | NEGATIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| kdj_j | -18.3406 | 46.7670 | 0.9464 | NEGATIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| kdj_signal | KDJ_NEUTRAL |  |  | UNKNOWN | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| kdj_risk_label | KDJ_OVERSOLD;KDJ_J_EXTREME_LOW |  |  | UNKNOWN | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| macd_dif | 3.1890 | 0.6468 | 65.2997 | POSITIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| macd_dea | 6.6205 | 0.9260 | 73.1861 | POSITIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| macd_histogram | -3.4315 | -0.0974 | 5.6782 | NEGATIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| macd_signal | MACD_ABOVE_ZERO |  |  | UNKNOWN | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| macd_momentum_label | MACD_HIST_CONTRACTING;MACD_MOMENTUM_WEAKENING |  |  | UNKNOWN | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| shadow_confirmation_score | 1 | 0.0000 | 87.7358 | POSITIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| shadow_risk_score | 1 | 0.0000 | 85.5346 | NEGATIVE | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv | SHADOW_ONLY | DESCRIPTIVE_ONLY |
| source_rank | 163 | 148.5000 | 55.0676 | NEUTRAL | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| factor_pack_rank | 163 | 148.5000 | 55.0676 | NEUTRAL | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| factor_score | 100.0 | 39.4490 | 100.0000 | POSITIVE | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| technical_timing_score | 64.0 | 50.0000 | 81.3063 | POSITIVE | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| composite_candidate_score | -51.276190 | 30.1423 | 10.1351 | NEGATIVE | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| event_risk_status |  |  |  | UNKNOWN | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| source_quality | OK_USABLE_SIGNAL_SOURCE |  |  | POSITIVE | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| technical_source_file | D:\us-tech-quant\outputs\v18\technical_timing\V18_6A_CURRENT_TECHNICAL_TIMING.csv |  |  | UNKNOWN | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| technical_source_file_mtime | 2026-05-23T01:57:24 |  |  | UNKNOWN | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| model_version | V18.32D-FREEZE-REPAIR |  |  | UNKNOWN | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |
| pipeline_version | V18.32D |  |  | UNKNOWN | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv | SUPPORTING_CONTEXT | DESCRIPTIVE_ONLY |

## 4. Neighbor Comparison / 前后名对比
为什么它没有排得更高：上方候选在 composite score 或若干组件字段上更强。为什么它没有排得更低：下方候选在这些字段上相对弱。
| rank | ticker | name | score | delta_vs_target | top_differing_columns |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | FORM |  | 59.2000 | 0.0000 | TARGET |
| 2 | AEIS |  | 58.8600 | -0.3400 | latest_close: 117.419998 -> 313.049988; rank: 1 -> 2; technical_status: TECH_TIMING_PULLBACK_WATCH -> TECH_TIMING_WATCH_POSITIVE; composite_candidate_score: 59.2 -> 58.86 |
| 3 | AGX |  | 57.4000 | -1.8000 | latest_close: 117.419998 -> 630.5; rank: 1 -> 3; composite_candidate_score: 59.2 -> 57.4; technical_status: TECH_TIMING_PULLBACK_WATCH -> TECH_TIMING_NEUTRAL |
| 4 | BLTE |  | 57.3240 | -1.8760 | latest_close: 117.419998 -> 143.360001; rank: 1 -> 4; composite_candidate_score: 59.2 -> 57.324; technical_status: TECH_TIMING_PULLBACK_WATCH -> TECH_TIMING_WATCH_POSITIVE |

## 5. Factor / Technical / Shadow Context / 因子、技术面、影子信号上下文
- OFFICIAL_RANKING_INPUT: 来自主 ranked candidate 文件的字段。
- SUPPORTING_CONTEXT: factor/technical/freeze 等辅助上下文。
- SHADOW_ONLY: V18.40A KDJ/MACD shadow fields are research-only unless explicitly present in current ranking fields.
- PROVENANCE_ONLY: read-center/status provenance only.

## 6. Source Provenance and Trust / 来源与可信度
| input | exists | rows | parse_status | role | trust | path |
| --- | --- | ---: | --- | --- | --- | --- |
| primary_ranking | TRUE | 318 | OK | OFFICIAL_RANKING_INPUT | HIGH | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv |
| factor_pack | TRUE | 252 | OK | SUPPORTING_CONTEXT | MEDIUM | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv |
| technical_timing | TRUE | 252 | OK | SUPPORTING_CONTEXT | MEDIUM | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv |
| kdj_macd_shadow | TRUE | 318 | OK | SHADOW_ONLY | MEDIUM | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv |
| v18_41a_summary | TRUE | 1 | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/ops/V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_SUMMARY.csv |
| v18_41a_read_first | TRUE |  | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/ops/V18_41A_READ_FIRST.txt |
| clean_operator_status | TRUE |  | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md |
| daily_brief | TRUE |  | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md |
| top_ranked_candidates_md | FALSE |  | MISSING_OPTIONAL | PROVENANCE_ONLY | LOW | outputs/v18/read_center/V18_CURRENT_TOP_RANKED_CANDIDATES.md |
| signal_freeze_ledger | TRUE | 888 | OK | SUPPORTING_CONTEXT | MEDIUM | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv |

## 7. Limitations / 限制
- This explainer does not recalculate the official rank.
- It reads existing current ranking output.
- It explains available columns and relative differences.
- It does not invent factor weights.
- If no current weight metadata is found, attribution is descriptive only.
