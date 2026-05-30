# V18.40A Candidate Top/Full Canonical Sync

## Status
- STATUS: WARN_V18_40A_CURRENT_TOP_ALIAS_WRITE_DISABLED_BY_V18_50B_R2
- RUN_ID: V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_20260530_221405
- APPLY_CANDIDATE_TOP_FULL_CANONICAL_SYNC: TRUE

## Comparison
- Full candidate count: 318
- Current top candidate count: 20
- Canonical top20 count: 20
- Overlap count: 7
- Mismatch count: 13
- Only current top count: 13
- Only full top20 count: 13
- Order matches full top20: FALSE
- Backup path: D:/us-tech-quant/archive/v18/candidate_top_full_sync_backups/V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_20260530_221405

## Diff
| bucket | position | ticker | current_top_position | full_top20_position | notes |
| --- | ---: | --- | ---: | ---: | --- |
| ONLY_IN_CURRENT_TOP | 2 | BW | 2 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 3 | AEHR | 3 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 4 | INTC | 4 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 6 | FORM | 6 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 9 | WOLF | 9 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 10 | BE | 10 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 11 | POWL | 11 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 12 | ACLS | 12 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 14 | MTZ | 14 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 15 | VECO | 15 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 16 | PUMP | 16 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 19 | COHR | 19 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_CURRENT_TOP | 20 | TTMI | 20 |  | Present in current top alias but absent from canonical full top20. |
| ONLY_IN_FULL_TOP20 | 1 | KEYS |  | 1 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 4 | NVDA |  | 4 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 5 | D |  | 5 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 7 | GOOGL |  | 7 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 8 | FIX |  | 8 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 9 | MCHP |  | 9 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 12 | CARR |  | 12 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 13 | ENTG |  | 13 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 15 | CRWV |  | 15 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 16 | ETR |  | 16 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 18 | COHU |  | 18 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 19 | HUT |  | 19 | Present in canonical full top20 but absent from current top alias. |
| ONLY_IN_FULL_TOP20 | 20 | GEV |  | 20 | Present in canonical full top20 but absent from current top alias. |

## Safety
- OFFICIAL_DECISION_IMPACT: NONE
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE
