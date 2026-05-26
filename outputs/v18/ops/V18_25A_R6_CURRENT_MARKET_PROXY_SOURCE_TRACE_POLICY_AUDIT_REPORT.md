# V18.25A-R6 Factor / Technical Market Proxy Source Trace & Local Proxy Policy Audit

- Status: WARN_V18_25A_R6_MARKET_PROXY_SOURCE_TRACE_POLICY_AUDIT_READY
- Mode: READ_ONLY_MARKET_PROXY_SOURCE_TRACE_AND_POLICY_AUDIT
- R4 status: OK_V18_25A_R4_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT_READY
- R5 status: WARN_V18_25A_R5_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN_READY
- Source trace scripts: 191
- Factor scripts with requirements: 11
- Technical scripts with requirements: 40
- Local proxy candidates: 6
- Usable local proxy for factor: 2
- Usable local proxy for technical overlay: 0
- Factor required proxy name: VIX/^VIX
- Factor required proxy local available: FALSE
- Factor required proxy full history ready: FALSE
- Technical VIX overlay required: TRUE
- Technical VIX local available: FALSE
- R5 full compatibility blocker: MISSING_LOCAL_VIX_PROXY_FOR_FULL_MARKET_REGIME_AND_V18_6A_OVERLAY
- Policy recommendation: NEEDS_LOCAL_MARKET_PROXY_BACKFILL
- Next recommended step: V18.25A-R7_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT

## Findings

### Factor
- Current factor generation traces a mandatory market-regime block through QQQ, SPY, and VIX/^VIX.
- QQQ and SPY local histories exist in `state/v18/price_cache` and are full-history ready.
- No local VIX history file was found in the searched roots, so the full factor market-regime proxy set is incomplete.

### Technical
- V18.6A technical timing is locally computable for BB, RSI, KDJ, and volume-ratio features.
- The exact V18.6A implementation also fetches `^VIX`, which the R5 dry run intentionally omitted.
- R5 is therefore only `PARTIAL_COMPATIBLE` with the full V18.6A behavior.

### Policy
- Recommended policy: `NEEDS_LOCAL_MARKET_PROXY_BACKFILL`.
- Recommended next step: `V18.25A-R7_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT`.
- The safest immediate path is to repair or source local market-proxy coverage, especially VIX/^VIX.
