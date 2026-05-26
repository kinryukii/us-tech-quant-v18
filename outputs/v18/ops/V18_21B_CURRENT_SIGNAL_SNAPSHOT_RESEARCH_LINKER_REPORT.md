# V18.21B Signal Snapshot + Simulation Research Linker

## Executive summary
Status: WARN_V18_21B_SIGNAL_SNAPSHOT_RESEARCH_LINKER_DEGRADED. The module created an advisory-only signal snapshot with 325 ticker rows and a timestamped history copy.

## Safety statement
This is a snapshot/linking layer only. It does not modify official decisions, ranking logic, technical timing logic, price factors, simulation positions, forward tracker state, manual state, price cache, broker execution, auto-trade, or auto-sell behavior.

## Input source summary
Input sources considered: 17. Missing sources: 0. Missing or degraded inputs are recorded in `V18_21B_CURRENT_SIGNAL_SOURCE_AUDIT.csv`.

## Signal snapshot field summary
Rows include ranking, technical timing, price-derived factor, factor scope, market regime, coverage/trust, simulation link, forward tracker link, and manual feedback link fields when available. Missing components are marked in `signal_snapshot_quality_status`.

## Component coverage summary
Factor pack coverage: 105. Technical timing coverage: 105. Price-derived coverage: 325.

## Simulation/forward/manual link keys
Link keys are deterministic references generated from the snapshot date and ticker when a local source row exists. They do not create or modify simulation, forward tracker, or manual feedback state.

## Degraded/missing data summary
Market regime status: DEGRADED_VIX_MISSING. True 5-day unique coverage met: FALSE. Coverage window complete: FALSE. Degraded snapshot rows: 220.

Missing sources:
- None

Degraded components:
- factor_pack: PARTIAL
- technical_timing: PARTIAL
- simulation_reference: PARTIAL
- forward_tracker_reference: PARTIAL
- manual_feedback_reference: MISSING

## Validation summary
Validation fail count: 0. Required outputs and READ_FIRST fields were checked during the run.

## Next-step recommendation
Use the history snapshot as the immutable as-of signal state for future forward-return research and simulation analysis. Keep this advisory layer separate from official trading and ranking systems.
