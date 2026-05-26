# V18.25A R1 Degraded Daily Output Review

- STATUS: OK_V18_25A_R1_DEGRADED_DAILY_OUTPUT_REVIEW_READY
- MODE: READ_ONLY_DEGRADED_DAILY_OUTPUT_REVIEW
- GENERATED_AT: 2026-05-22T00:59:06
- TOTAL_OUTPUT_ROWS: 324
- HIGH_TRUST_SUSPICIOUS_COUNT: 0
- SOURCE_MISSING_WARNING_COUNT: 0
- NEXT_RECOMMENDED_STEP: C: Continue Batch3 staged backfill / remaining stale coverage expansion

## Bucket Composition

| Category | Value | Count | Expected | Matches READ_FIRST |
| --- | --- | ---: | ---: | --- |
| OUTPUT_BUCKET | HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | 155 | 155 | TRUE |
| OUTPUT_BUCKET | DATA_NOT_READY | 103 | 103 | TRUE |
| OUTPUT_BUCKET | LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH | 64 | 64 | TRUE |
| OUTPUT_BUCKET | MEDIUM_TRUST_PARTIAL_WATCH | 2 | 2 | TRUE |
| OFFICIAL_RANK_ALLOWED | FALSE | 169 |  |  |
| OFFICIAL_RANK_ALLOWED | TRUE | 155 | 155 | TRUE |
| WATCH_ONLY | FALSE | 258 |  |  |
| WATCH_ONLY | TRUE | 66 | 66 | TRUE |
| TRADE_ALLOWED | FALSE | 324 |  |  |

Trust level counts:
| Trust Level | Count |
| --- | ---: |
| HIGH | 155 |
| MEDIUM | 2 |
| LOW | 64 |
| NONE | 103 |

## Validation

- Validation failures: 0
- Forbidden file changes: 0
- High-trust suspicious rows: 0
- Warning inputs: NONE

## High-Trust Review

Top 30 high-trust candidates reviewed: 30

| Rank | Ticker | Score | Tier | Technical Status | Official Price Cache | Reason Summary | Suspicious Fields |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | AGX | 100.0 | TIER_0_DATA_NOT_READY | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 2 | FORM | 100.0 | TIER_1_CORE_CANDIDATE | TECH_TIMING_PULLBACK_WATCH | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 3 | LITE | 99.05 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 4 | POWL | 98.1 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 5 | MTZ | 98.08 | TIER_0_DATA_NOT_READY | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 6 | MU | 97.14 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 7 | SOXL | 96.19 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 8 | AEIS | 96.15 | TIER_0_DATA_NOT_READY | TECH_TIMING_WATCH_POSITIVE | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 9 | GLW | 95.24 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 10 | AEHR | 94.29 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 11 | ALM | 94.23 | TIER_0_DATA_NOT_READY | TECH_TIMING_PULLBACK_WATCH | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 12 | ICHR | 93.33 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 13 | MOD | 92.38 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 14 | BLTE | 92.31 | TIER_0_DATA_NOT_READY | TECH_TIMING_WATCH_POSITIVE | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 15 | SNDK | 91.43 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 16 | INTC | 90.48 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 17 | AA | 90.38 | TIER_0_DATA_NOT_READY | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 18 | WDC | 89.52 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 19 | AMKR | 88.57 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 20 | BIDU | 88.46 | TIER_0_DATA_NOT_READY | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 21 | STX | 87.62 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 22 | FIX | 86.67 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 23 | MTSI | 86.54 | TIER_0_DATA_NOT_READY | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 24 | COHU | 85.71 | TIER_1_CORE_CANDIDATE | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 25 | KEYS | 84.76 | TIER_2_STRONG_WATCHLIST | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 26 | CLH | 84.62 | TIER_0_DATA_NOT_READY | TECH_TIMING_PULLBACK_WATCH | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 27 | CIEN | 83.81 | TIER_2_STRONG_WATCHLIST | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 28 | CAMT | 82.86 | TIER_2_STRONG_WATCHLIST | TECH_TIMING_WATCH_POSITIVE | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 29 | LYB | 82.69 | TIER_0_DATA_NOT_READY | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=yes; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |
| 30 | FLEX | 81.9 | TIER_2_STRONG_WATCHLIST | TECH_TIMING_NEUTRAL | TRUE | score=yes; technical=yes; official_price=yes; staged=no; bucket=HIGH_TRUST_OFFICIAL_RANK_CANDIDATE | NONE |

## Medium/Low-Trust Review

The downgrade pattern is consistent: medium-trust names mostly miss score and technical timing evidence, while low-trust names usually add official-price-cache loss on top of the same missing score/technical pattern.

| Bucket | Data Gap Reason | Count |
| --- | --- | ---: |
| MEDIUM_TRUST_PARTIAL_WATCH | OFFICIAL_PRICE_CACHE_MISSING | 2 |
| LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH | SCORE_MISSING|TECHNICAL_TIMING_MISSING | 51 |
| LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH | OFFICIAL_PRICE_CACHE_MISSING|SCORE_MISSING|TECHNICAL_TIMING_MISSING|ROLLING_LEDGER_FULL_HISTORY_NOT_READY|STAGED_BACKFILL_HOLD_OR_PARTIAL | 8 |
| LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH | OFFICIAL_PRICE_CACHE_MISSING|SCORE_MISSING|TECHNICAL_TIMING_MISSING|ROLLING_LEDGER_FULL_HISTORY_NOT_READY | 5 |

### Watch-Only Names With Upgrade Potential

The highest-probability recoveries are the names with staged full-history candidates or official-integration need. The current recommendation file identifies 13 `NEEDS_OFFICIAL_INTEGRATION` watch-only names and 8 `EMPTY_FETCH_OR_HOLD_REVIEW` names, with a larger `PARTIAL_HISTORY` tail that is usually just missing score/technical context.

Top watch-only priority names: VECO, XLK, BLSH, CAI, CHYM, CNM, COF, CPAY, CPNG, CRH, CRS, CSGP, DAKT, DAL, DASH, DB, DIS, DOCU, DUOL, EEM

## Data-Not-Ready Review

All `DATA_NOT_READY` rows share the same gap pattern in this run: `OFFICIAL_PRICE_CACHE_MISSING|SCORE_MISSING|TECHNICAL_TIMING_MISSING|ROLLING_LEDGER_FULL_HISTORY_NOT_READY`.
No current `DATA_NOT_READY` ticker shows staged-backfill evidence or a prior high-confidence tier score in the loaded history snapshots, so the bucket is a uniform no-local-data miss rather than a staged recovery queue.

Top data-not-ready priorities: COG, COGT, CRCL, CVNA, DBVT, FCNCA, FIGR, GEMI, HOOD, HTZ, INSM, JBS, JFROG, KLAR, OKTA, OLMA, OLPX, OPCH, PATH, PCOR

## Data Gap Recommendations

| Recommendation Group | Count | Top Examples |
| --- | ---: | --- |
| NEEDS_OFFICIAL_INTEGRATION | 13 | AMC, APLD, BLSH, BW, BYND, CAI, CDTX, CFLT |
| NEEDS_STAGED_BACKFILL | 0 |  |
| PARTIAL_HISTORY_REVIEW | 116 | AMC, APLD, BLSH, BW, BYND, CAI, CDTX, CFLT |
| EMPTY_FETCH_OR_HOLD_REVIEW | 8 | AMC, APLD, BW, BYND, CDTX, CFLT, MPW, NVAX |
| UNKNOWN_OR_OTHER_GAP | 0 |  |

## Next Action Recommendation

Recommended order:
1. C: Continue Batch3 staged backfill / remaining stale coverage expansion
2. C: Batch 3 staged backfill
3. A: V18.23C-R6 Batch 2 official full-history-only integration
4. B: V18.25A-R2 classification logic refinement

Rationale: the audit is already internally consistent, but one source alias is missing and the review would benefit from fixing source discovery before refining classification or widening integration.
