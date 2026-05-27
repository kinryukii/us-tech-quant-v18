# V18.21B-R1 Signal Snapshot Quality Report

## Executive summary
Status: WARN_V18_21B_R1_SIGNAL_SNAPSHOT_QUALITY_DEGRADED. R1 preserves the V18.21B advisory snapshot while separating price-derived row coverage from score-ready coverage and explaining research readiness blockers.

## Safety statement
This patch is advisory-only. It does not modify official decisions, ranking, technical timing, price factor outputs, simulation positions, forward tracker state, manual state, price cache, broker execution, auto-trade, or auto-sell behavior.

## Signal snapshot quality summary
Rows: 325. History copy created: TRUE. History copy matches current: TRUE.

## Price-derived readiness explanation
Price-derived row coverage is 325, but full score-ready coverage is 104 and light score-ready coverage is 0. Row-only tickers are not treated as fully research-ready.

## Research readiness blocker summary
Forward-ready rows: 105. Simulation-ready rows: 31. Full research ready rows: 0. Watch-only degraded rows: 220.

## Link key quality summary
Signal snapshot IDs unique: TRUE. Duplicate signal snapshot IDs: 0. Simulation link keys populated: 31; forward tracker keys populated: 20; manual feedback keys populated: 0.

## History copy consistency summary
The R1 current snapshot was copied to the timestamped history file and compared by row count and SHA-256 hash.

## Degraded data explanation
Status remains WARN because factor pack and technical timing cover only part of the 325-row universe, true 5-day coverage remains FALSE, coverage window is incomplete, daily trust is not HIGH, and VIX remains missing in the market regime layer.

## Validation summary
Validation fail count: 0.

## Next-step recommendation
Use the R1 snapshot for historical factor-effectiveness research with readiness filters. Do not treat row coverage as score-ready coverage.
