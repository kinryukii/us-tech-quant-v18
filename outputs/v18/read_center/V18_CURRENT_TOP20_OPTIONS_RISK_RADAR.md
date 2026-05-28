# V18.48B Top20 Options Risk Radar Report

V18.48B is a read-only options risk-reference layer based on V18.48A option snapshots.

## Sources
| metric | value |
| --- | --- |
| OPTIONS_SNAPSHOT_SOURCE | D:\us-tech-quant\outputs\v18\options\V18_48A_TOP20_OPTIONS_SNAPSHOT.csv |
| EVENT_RISK_SOURCE | D:\us-tech-quant\outputs\v18\event_risk\V18_47C_TOP20_EVENT_EARNINGS_RISK.csv |

## Top20 options risk distribution
| ticker_count | low_risk_count | medium_risk_count | high_risk_count | extreme_risk_count | unknown_review_count |
| --- | --- | --- | --- | --- | --- |
| 20 | 0 | 11 | 9 | 0 | 0 |

## HIGH options risk tickers
| ticker | rank | overall_options_risk_score | expected_move_level | liquidity_risk_level | options_risk_reason |
| --- | --- | --- | --- | --- | --- |
| FIX | 3 | 51.25 | EXTREME | MEDIUM | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=MEDIUM;EARNINGS_OPTIONS=LOW |
| LITE | 4 | 56.25 | EXTREME | MEDIUM | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=MEDIUM;EARNINGS_OPTIONS=LOW |
| AMKR | 7 | 52.50 | EXTREME | LOW | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=LOW;EARNINGS_OPTIONS=LOW |
| ENTG | 8 | 56.00 | EXTREME | HIGH | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=HIGH;EARNINGS_OPTIONS=MEDIUM |
| ICHR | 13 | 61.00 | EXTREME | HIGH | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=HIGH;EARNINGS_OPTIONS=MEDIUM |
| CRWV | 14 | 55.56 | EXTREME | LOW | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=LOW;EARNINGS_OPTIONS=UNKNOWN |
| COHU | 15 | 56.00 | EXTREME | HIGH | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=HIGH;EARNINGS_OPTIONS=MEDIUM |
| FN | 17 | 52.50 | EXTREME | LOW | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=LOW;EARNINGS_OPTIONS=LOW |
| POWL | 20 | 51.25 | EXTREME | MEDIUM | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=MEDIUM;EARNINGS_OPTIONS=LOW |

## EXTREME options risk tickers
| ticker | rank | overall_options_risk_score | expected_move_level | liquidity_risk_level | options_risk_reason |
| --- | --- | --- | --- | --- | --- |

## UNKNOWN_REVIEW tickers
| ticker | rank | data_quality | options_risk_reason |
| --- | --- | --- | --- |

## Liquidity risk distribution
| liquidity_risk_level | count |
| --- | --- |
| HIGH | 7 |
| LOW | 6 |
| MEDIUM | 7 |

## Expected move observations
| ticker | expected_move_pct_near | expected_move_pct_mid | expected_move_pct_far | expected_move_level |
| --- | --- | --- | --- | --- |
| KEYS | UNKNOWN | 0.0912 | 0.1358 | HIGH |
| VRT | 0.0858 | 0.1702 | 0.1933 | EXTREME |
| FIX | UNKNOWN | 0.1288 | 0.1879 | EXTREME |
| LITE | 0.1311 | 0.2434 | 0.2750 | EXTREME |
| NVDA | 0.0476 | 0.0952 | 0.1143 | HIGH |
| GEV | 0.0638 | 0.1103 | 0.1510 | HIGH |
| AMKR | UNKNOWN | 0.1683 | 0.2459 | EXTREME |
| ENTG | UNKNOWN | 0.1386 | 0.1957 | EXTREME |
| MCHP | 0.0749 | 0.0847 | 0.1585 | HIGH |
| ICHR | UNKNOWN | 0.1695 | 0.2936 | EXTREME |
| CRWV | 0.1148 | 0.2160 | 0.2556 | EXTREME |
| COHU | UNKNOWN | 0.1538 | 0.1847 | EXTREME |
| HUBB | UNKNOWN | 0.0712 | 0.0972 | HIGH |
| FN | UNKNOWN | 0.1637 | 0.2368 | EXTREME |
| CARR | 0.0357 | 0.1402 | 0.1093 | HIGH |
| ETN | 0.0500 | 0.0990 | 0.1163 | HIGH |
| POWL | UNKNOWN | 0.1593 | 0.2315 | EXTREME |

## Earnings/options risk observations
| ticker | days_to_earnings | earnings_options_risk_score | earnings_options_risk_level |
| --- | --- | --- | --- |

## Safety statement
V18.48B does not predict direction, earnings outcomes, or stock prices. It does not recommend options trades, calls, puts, or spreads. It does not change official ranking, factor weights, buy/sell permissions, final_action, event risk scoring, trading execution, broker behavior, order behavior, or signal freeze ledgers.

## Suggested next step
V18.49A Risk-Adjusted Ranking Layer or V18.49B Entry/Exit Plan Generator, depending on readiness.
