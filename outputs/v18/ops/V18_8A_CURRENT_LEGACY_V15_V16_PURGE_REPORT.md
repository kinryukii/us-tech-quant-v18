# V18.8A Legacy V15/V16 Purge Report

- STATUS: `OK_LEGACY_V15_V16_PURGED`
- MODE: `APPLY_DELETE`
- GENERATED_AT: `20260516_185405`
- DELETE_CANDIDATE_COUNT: `5`
- DELETE_CANDIDATE_MB: `0.0784`
- CSV: `D:\us-tech-quant\outputs\v18\ops\V18_8A_CURRENT_LEGACY_V15_V16_PURGE_AUDIT.csv`

## Policy

- Active V15/V16 directories, scripts, configs, and V16 simulation/feedback source remnants are candidates.
- V18 active files are protected.
- archive\\stable internals are protected to avoid corrupting restore snapshots.
- V17 dashboard legacy is optional via `-IncludeV17DashboardLegacy`.

## Candidates

| Category | Type | SizeMB | FullName |
|---|---|---:|---|
| OPTIONAL_V17_DASHBOARD_LEGACY | Directory | 0.0471 | `D:\us-tech-quant\outputs\v17\factor_effectiveness` |
| OPTIONAL_V17_DASHBOARD_LEGACY | File | 0.0058 | `D:\us-tech-quant\scripts\run_v17_3_1_factor_dashboard_status_semantics.ps1` |
| OPTIONAL_V17_DASHBOARD_LEGACY | File | 0.0064 | `D:\us-tech-quant\scripts\run_v17_3_1B_factor_dashboard_status_semantics.ps1` |
| OPTIONAL_V17_DASHBOARD_LEGACY | File | 0.0011 | `D:\us-tech-quant\scripts\run_v17_3_factor_performance_dashboard.ps1` |
| OPTIONAL_V17_DASHBOARD_LEGACY | File | 0.018 | `D:\us-tech-quant\scripts\run_v17_3_factor_performance_dashboard.py` |
