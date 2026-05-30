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
| 20 | 0 | 12 | 8 | 0 | 0 |

## HIGH options risk tickers
| ticker | rank | overall_options_risk_score | expected_move_level | liquidity_risk_level | options_risk_reason |
| --- | --- | --- | --- | --- | --- |
| ICHR | 3 | 61.00 | EXTREME | HIGH | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=HIGH;EARNINGS_OPTIONS=MEDIUM |
| AMKR | 6 | 52.50 | EXTREME | LOW | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=LOW;EARNINGS_OPTIONS=LOW |
| FIX | 8 | 56.00 | EXTREME | HIGH | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=HIGH;EARNINGS_OPTIONS=MEDIUM |
| LITE | 10 | 56.25 | EXTREME | MEDIUM | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=MEDIUM;EARNINGS_OPTIONS=LOW |
| ENTG | 12 | 51.25 | EXTREME | MEDIUM | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=MEDIUM;EARNINGS_OPTIONS=LOW |
| CRWV | 13 | 55.56 | EXTREME | LOW | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=LOW;EARNINGS_OPTIONS=UNKNOWN |
| COHU | 15 | 56.00 | EXTREME | HIGH | EXPECTED_MOVE=EXTREME;IV=HIGH;SKEW=LOW;LIQUIDITY=HIGH;EARNINGS_OPTIONS=MEDIUM |
| FN | 17 | 52.50 | EXTREME | LOW | EXPECTED_MOVE=EXTREME;IV=EXTREME;SKEW=LOW;LIQUIDITY=LOW;EARNINGS_OPTIONS=LOW |

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
| LOW | 7 |
| MEDIUM | 6 |

## Expected move observations
| ticker | expected_move_pct_near | expected_move_pct_mid | expected_move_pct_far | expected_move_level |
| --- | --- | --- | --- | --- |
| KEYS | UNKNOWN | UNKNOWN | 0.1271 | EXTREME |
| VRT | 0.1053 | 0.1582 | 0.1903 | EXTREME |
| ICHR | UNKNOWN | UNKNOWN | 0.2097 | EXTREME |
| NVDA | 0.0649 | 0.0971 | 0.1196 | HIGH |
| AMKR | UNKNOWN | UNKNOWN | 0.2379 | EXTREME |
| FIX | UNKNOWN | UNKNOWN | 0.1843 | EXTREME |
| MCHP | 0.0940 | 0.0724 | 0.1548 | HIGH |
| LITE | 0.1485 | 0.1985 | 0.2607 | EXTREME |
| CARR | 0.0681 | 0.1552 | 0.1104 | HIGH |
| ENTG | UNKNOWN | UNKNOWN | 0.1989 | EXTREME |
| CRWV | 0.1502 | 0.2230 | 0.2593 | EXTREME |
| COHU | UNKNOWN | UNKNOWN | 0.1744 | EXTREME |
| GEV | 0.0783 | 0.1116 | 0.1440 | HIGH |
| FN | UNKNOWN | UNKNOWN | 0.2423 | EXTREME |
| ETN | 0.0599 | 0.0931 | 0.1118 | HIGH |
| HUBB | UNKNOWN | UNKNOWN | 0.1131 | HIGH |
| POWL | UNKNOWN | UNKNOWN | 0.2299 | EXTREME |

## Earnings/options risk observations
| ticker | days_to_earnings | earnings_options_risk_score | earnings_options_risk_level |
| --- | --- | --- | --- |

## Safety statement
V18.48B does not predict direction, earnings outcomes, or stock prices. It does not recommend options trades, calls, puts, or spreads. It does not change official ranking, factor weights, buy/sell permissions, final_action, event risk scoring, trading execution, broker behavior, order behavior, or signal freeze ledgers.

## Suggested next step
V18.49A Risk-Adjusted Ranking Layer or V18.49B Entry/Exit Plan Generator, depending on readiness.
