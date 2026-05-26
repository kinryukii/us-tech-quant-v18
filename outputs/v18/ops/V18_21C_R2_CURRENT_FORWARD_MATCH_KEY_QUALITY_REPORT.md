# V18.21C-R2 Forward Match Key Quality Report

## Executive summary
Status: WARN_V18_21C_R2_FORWARD_MATCH_KEY_QUALITY_PLAN_READY. R2 diagnoses low-confidence forward matching and creates a multi-horizon readiness/key-upgrade plan.

## Safety statement
This is advisory-only and plan-only. It does not modify signal snapshots, forward tracker files, simulation positions, prices, ranking, promotion/demotion, official decisions, auto-trade, or auto-sell. External data fetched: FALSE.

## Forward source key availability summary
High-quality sources: 0; medium-quality: 0; ticker/date-only: 5; ticker-only low confidence: 1; unusable: 0.

## Match failure reason summary
High-confidence matches: 0; medium: 0; low: 20; unmatched/ambiguous: 305.

## Multi-horizon readiness plan
1D usable count: 20. 3D/5D/10D/20D usable counts: 0/0/0/0. Status: NOT_READY_MULTI_HORIZON.

## Forward research key upgrade plan
The plan recommends future direct key propagation, especially `signal_snapshot_id` into forward tracker/outcome rows. This patch does not apply it.

## Conservative research conclusion
No factor effectiveness claims are allowed. Weight changes and production promotions remain disallowed.

## Why no factor effectiveness claims are allowed
The current evidence is dominated by low-confidence ticker-only matches and a single usable horizon.

## Validation summary
Validation fail count: 0.

## Next-step recommendation
Run a separate, explicitly approved key propagation implementation later; then let additional horizons mature before re-evaluating factors.
