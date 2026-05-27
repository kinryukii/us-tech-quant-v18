# V18.43A Top-N Ranking Explainer Packet

## 1. Operator Summary / 操作员摘要
- TopN requested: 20
- TopN effective: 20
- Ranking source file: D:\us-tech-quant\outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv
- Candidate pool size: 318
- Score column: composite_candidate_score
- Highest score: 59.2000
- Lowest score inside TopN: 51.6840
- TopN score spread: 7.5160
- Close rank gap count: 10
- Status: WARN_V18_43A_SUPPORTING_INPUTS_PARTIAL
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED

## 2. Top-N Ranking Table / Top-N 排名总览
| rank | ticker | name | score | delta_prev | delta_rank1 | quick_driver_label | quick_risk_penalty_label | drilldown |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | FORM |  | 59.2000 |  | 0.0000 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "FORM" -NeighborWindow 3 -WriteCurrent` |
| 2 | AEIS |  | 58.8600 | -0.3400 | -0.3400 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "AEIS" -NeighborWindow 3 -WriteCurrent` |
| 3 | AGX |  | 57.4000 | -1.4600 | -1.8000 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "AGX" -NeighborWindow 3 -WriteCurrent` |
| 4 | BLTE |  | 57.3240 | -0.0760 | -1.8760 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "BLTE" -NeighborWindow 3 -WriteCurrent` |
| 5 | LITE |  | 57.0200 | -0.3040 | -2.1800 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "LITE" -NeighborWindow 3 -WriteCurrent` |
| 6 | ALM |  | 56.8920 | -0.1280 | -2.3080 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "ALM" -NeighborWindow 3 -WriteCurrent` |
| 7 | POWL |  | 56.6400 | -0.2520 | -2.5600 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "POWL" -NeighborWindow 3 -WriteCurrent` |
| 8 | MTZ |  | 56.6320 | -0.0080 | -2.5680 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "MTZ" -NeighborWindow 3 -WriteCurrent` |
| 9 | MOD |  | 54.3520 | -2.2800 | -4.8480 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "MOD" -NeighborWindow 3 -WriteCurrent` |
| 10 | OC |  | 53.9080 | -0.4440 | -5.2920 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "OC" -NeighborWindow 3 -WriteCurrent` |
| 11 | MU |  | 53.8560 | -0.0520 | -5.3440 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "MU" -NeighborWindow 3 -WriteCurrent` |
| 12 | CAMT |  | 53.5440 | -0.3120 | -5.6560 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "CAMT" -NeighborWindow 3 -WriteCurrent` |
| 13 | SOXL |  | 53.4760 | -0.0680 | -5.7240 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "SOXL" -NeighborWindow 3 -WriteCurrent` |
| 14 | CLH |  | 53.0480 | -0.4280 | -6.1520 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "CLH" -NeighborWindow 3 -WriteCurrent` |
| 15 | AMKR |  | 52.8280 | -0.2200 | -6.3720 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "AMKR" -NeighborWindow 3 -WriteCurrent` |
| 16 | KEYS |  | 52.5040 | -0.3240 | -6.6960 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "KEYS" -NeighborWindow 3 -WriteCurrent` |
| 17 | AEHR |  | 52.1160 | -0.3880 | -7.0840 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "AEHR" -NeighborWindow 3 -WriteCurrent` |
| 18 | VIAV |  | 51.8006 | -0.3154 | -7.3994 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "VIAV" -NeighborWindow 3 -WriteCurrent` |
| 19 | ICHR |  | 51.7320 | -0.0686 | -7.4680 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "ICHR" -NeighborWindow 3 -WriteCurrent` |
| 20 | COHU |  | 51.6840 | -0.0480 | -7.5160 | DESCRIPTIVE_SCORE_ONLY | NO_MAJOR_RISK_LABEL | `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "COHU" -NeighborWindow 3 -WriteCurrent` |

## 3. Why These Names Are Top Ranked / 为什么这些票在前面？
这些候选排在前面，是因为它们在当前 ranking output 中拥有最高的 existing `composite_candidate_score` 或 score column 值。本 patch 不重算排名，只读取已有排名输出并解释可见字段。
- Common driver class counts: {'STRONG_NEGATIVE': 20, 'STRONG_POSITIVE': 20, 'UNKNOWN': 136, 'POSITIVE': 24}

## 4. Driver Matrix / 驱动矩阵
| rank | ticker | column_name | value | percentile | driver_class | role | mode |
| ---: | --- | --- | --- | ---: | --- | --- | --- |
| 1 | FORM | rank | 1 | 0.3145 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | composite_candidate_score | 59.2 | 100.0000 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | technical_status | TECH_TIMING_PULLBACK_WATCH |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 1 | FORM | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | rank | 2 | 0.6289 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | composite_candidate_score | 58.86 | 99.6855 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | technical_status | TECH_TIMING_WATCH_POSITIVE |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 2 | AEIS | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | rank | 3 | 0.9434 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | composite_candidate_score | 57.4 | 99.3711 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | technical_status | TECH_TIMING_NEUTRAL |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 3 | AGX | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | rank | 4 | 1.2579 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | composite_candidate_score | 57.324 | 99.0566 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | technical_status | TECH_TIMING_WATCH_POSITIVE |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 4 | BLTE | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | rank | 5 | 1.5723 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | composite_candidate_score | 57.02 | 98.7421 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | technical_status | TECH_TIMING_NEUTRAL |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 5 | LITE | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | rank | 6 | 1.8868 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | composite_candidate_score | 56.892 | 98.4277 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | technical_status | TECH_TIMING_PULLBACK_WATCH |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 6 | ALM | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | rank | 7 | 2.2013 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | composite_candidate_score | 56.64 | 98.1132 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | technical_status | TECH_TIMING_NEUTRAL |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 7 | POWL | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | rank | 8 | 2.5157 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | composite_candidate_score | 56.632 | 97.7987 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | technical_status | TECH_TIMING_NEUTRAL |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 8 | MTZ | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | rank | 9 | 2.8302 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | composite_candidate_score | 54.352 | 97.4843 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | technical_status | TECH_TIMING_NEUTRAL |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 9 | MOD | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | rank | 10 | 3.1447 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | composite_candidate_score | 53.908 | 97.1698 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | technical_status | TECH_TIMING_WATCH_POSITIVE |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 10 | OC | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | rank | 11 | 3.4591 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | composite_candidate_score | 53.856 | 96.8553 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | technical_status | TECH_TIMING_NEUTRAL |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 11 | MU | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | rank | 12 | 3.7736 | STRONG_NEGATIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | composite_candidate_score | 53.544 | 96.5409 | STRONG_POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | ranking_source_policy | V18_35E_ONLINE_BACKFILL_RECOMPUTE |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | primary_score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | score_source_status | OK_RECOMPUTED_FACTOR_TECHNICAL |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | score_source_files | outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv;outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | score_source_columns | factor_pack_score;technical_timing_score |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | technical_status | TECH_TIMING_WATCH_POSITIVE |  | POSITIVE | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | event_risk_status |  |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |
| 12 | CAMT | overheat_status | NOT_AVAILABLE_RESERVED |  | UNKNOWN | OFFICIAL_RANKING_INPUT | DESCRIPTIVE_ONLY |

## 5. Close Rank Gaps / 排名接近区
| upper_rank | lower_rank | upper_ticker | lower_ticker | upper_score | lower_score | absolute_gap | relative_gap | reason |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 3 | 4 | AGX | BLTE | 57.4000 | 57.3240 | 0.0760 | 0.001324 | rank: 3 vs 4; technical_status: TECH_TIMING_NEUTRAL vs TECH_TIMING_WATCH_POSITIVE; composite_candidate_score: 57.4 vs 57.324 |
| 4 | 5 | BLTE | LITE | 57.3240 | 57.0200 | 0.3040 | 0.005303 | rank: 4 vs 5; technical_status: TECH_TIMING_WATCH_POSITIVE vs TECH_TIMING_NEUTRAL; composite_candidate_score: 57.324 vs 57.02 |
| 5 | 6 | LITE | ALM | 57.0200 | 56.8920 | 0.1280 | 0.002245 | rank: 5 vs 6; technical_status: TECH_TIMING_NEUTRAL vs TECH_TIMING_PULLBACK_WATCH; composite_candidate_score: 57.02 vs 56.892 |
| 6 | 7 | ALM | POWL | 56.8920 | 56.6400 | 0.2520 | 0.004429 | rank: 6 vs 7; technical_status: TECH_TIMING_PULLBACK_WATCH vs TECH_TIMING_NEUTRAL; composite_candidate_score: 56.892 vs 56.64 |
| 7 | 8 | POWL | MTZ | 56.6400 | 56.6320 | 0.0080 | 0.000141 | rank: 7 vs 8; composite_candidate_score: 56.64 vs 56.632 |
| 10 | 11 | OC | MU | 53.9080 | 53.8560 | 0.0520 | 0.000965 | rank: 10 vs 11; technical_status: TECH_TIMING_WATCH_POSITIVE vs TECH_TIMING_NEUTRAL; composite_candidate_score: 53.908 vs 53.856 |
| 12 | 13 | CAMT | SOXL | 53.5440 | 53.4760 | 0.0680 | 0.001270 | rank: 12 vs 13; technical_status: TECH_TIMING_WATCH_POSITIVE vs TECH_TIMING_NEUTRAL; composite_candidate_score: 53.544 vs 53.476 |
| 14 | 15 | CLH | AMKR | 53.0480 | 52.8280 | 0.2200 | 0.004147 | rank: 14 vs 15; technical_status: TECH_TIMING_PULLBACK_WATCH vs TECH_TIMING_NEUTRAL; composite_candidate_score: 53.048 vs 52.828 |
| 18 | 19 | VIAV | ICHR | 51.8006 | 51.7320 | 0.0686 | 0.001324 | rank: 18 vs 19; technical_status: TECH_TIMING_STAGED_REFRESH vs TECH_TIMING_NEUTRAL; composite_candidate_score: 51.800559 vs 51.732 |
| 19 | 20 | ICHR | COHU | 51.7320 | 51.6840 | 0.0480 | 0.000928 | rank: 19 vs 20; composite_candidate_score: 51.732 vs 51.684 |

## 6. Factor / Technical / Shadow Context / 因子、技术面、影子信号上下文
- `OFFICIAL_RANKING_INPUT`: 来自主 ranked candidate 文件。
- `SUPPORTING_CONTEXT`: factor/technical/freeze 等辅助上下文。
- `SHADOW_ONLY`: V18.40A KDJ/MACD shadow fields; unless present in official ranking fields, do not treat as official drivers.
- `PROVENANCE_ONLY`: status/read-center provenance.

## 7. Drilldown Suggestions / 单票深挖建议
- `FORM`: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "FORM" -NeighborWindow 3 -WriteCurrent`
- `AGX`: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "AGX" -NeighborWindow 3 -WriteCurrent`
- `BLTE`: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "BLTE" -NeighborWindow 3 -WriteCurrent`
- `LITE`: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "LITE" -NeighborWindow 3 -WriteCurrent`
- `ALM`: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "ALM" -NeighborWindow 3 -WriteCurrent`

## 8. Source Provenance and Trust / 来源与可信度
| input | exists | rows | parse_status | role | trust | path |
| --- | --- | ---: | --- | --- | --- | --- |
| primary_ranking | TRUE | 318 | OK | OFFICIAL_RANKING_INPUT | HIGH | outputs\v18\candidates\V18_CURRENT_RANKED_CANDIDATES.csv |
| factor_pack | TRUE | 252 | OK | SUPPORTING_CONTEXT | MEDIUM | outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv |
| technical_timing | TRUE | 252 | OK | SUPPORTING_CONTEXT | MEDIUM | outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv |
| kdj_macd_shadow | TRUE | 318 | OK | SHADOW_ONLY | MEDIUM | outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv |
| v18_42a_attribution | TRUE | 63 | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/ops/V18_42A_SINGLE_TICKER_RANKING_ATTRIBUTION.csv |
| v18_42a_provenance | TRUE | 10 | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/ops/V18_42A_SINGLE_TICKER_INPUT_PROVENANCE.csv |
| v18_41a_summary | TRUE | 1 | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/ops/V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_SUMMARY.csv |
| v18_41a_read_first | TRUE |  | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/ops/V18_41A_READ_FIRST.txt |
| clean_operator_status | TRUE |  | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md |
| daily_brief | TRUE |  | OK | PROVENANCE_ONLY | MEDIUM | outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md |
| top_ranked_candidates_md | FALSE |  | MISSING_OPTIONAL | PROVENANCE_ONLY | LOW | outputs/v18/read_center/V18_CURRENT_TOP_RANKED_CANDIDATES.md |
| signal_freeze_ledger | TRUE | 888 | OK | SUPPORTING_CONTEXT | MEDIUM | state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv |

## 9. Limitations / 限制
- This patch does not recalculate official rank.
- It reads existing current ranking output.
- It does not invent factor weights.
- If no current weight metadata is found, attribution is descriptive only.
- It does not change trading decisions.
- It does not allow trading execution.
