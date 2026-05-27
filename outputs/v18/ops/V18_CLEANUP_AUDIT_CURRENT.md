# V18 Cleanup Audit

Generated: `2026-05-18 13:14:39`

## Status

- MODE: `DRY_RUN`
- OFFICIAL_DECISION_IMPACT: `NONE`
- DELETE_ENABLED: `False`
- MOVE_ENABLED: `False`

## Total Reclaimable Size By Category

| category | bytes | mb |
|---|---:|---:|
| KEEP_BUT_REVIEW | 2964511 | 2.827 |
| SAFE_DELETE_GENERATED | 1316845 | 1.256 |

## Row Counts

| category | count |
|---|---:|
| BUG_OR_RISK_TO_FIX | 5 |
| KEEP_BUT_REVIEW | 5111 |
| MUST_KEEP_ACTIVE | 899 |
| SAFE_DELETE_GENERATED | 86 |

## Top 30 Cleanup Candidates

| path | category | size_bytes | reason | risk | action |
|---|---|---:|---|---|---|
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260518_131112.bak | KEEP_BUT_REVIEW | 155452 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260517_220115.bak | KEEP_BUT_REVIEW | 129586 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260518_130610.bak | KEEP_BUT_REVIEW | 129586 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260517_221527.bak | KEEP_BUT_REVIEW | 129571 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260518_130936.bak | KEEP_BUT_REVIEW | 116960 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260518_131419.bak | KEEP_BUT_REVIEW | 116960 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_015744.bak | KEEP_BUT_REVIEW | 103720 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_140943.bak | KEEP_BUT_REVIEW | 103720 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_142549.bak | KEEP_BUT_REVIEW | 103720 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_144509.bak | KEEP_BUT_REVIEW | 103720 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_152523.bak | KEEP_BUT_REVIEW | 103720 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_014623.bak | KEEP_BUT_REVIEW | 103710 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_133751.bak | KEEP_BUT_REVIEW | 103705 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_151134.bak | KEEP_BUT_REVIEW | 103705 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_153857.bak | KEEP_BUT_REVIEW | 103705 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_155028.bak | KEEP_BUT_REVIEW | 103705 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260517_215429.bak | KEEP_BUT_REVIEW | 103705 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_021409.bak | KEEP_BUT_REVIEW | 103695 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_210713.bak | KEEP_BUT_REVIEW | 101712 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_212019.bak | KEEP_BUT_REVIEW | 101712 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_220436.bak | KEEP_BUT_REVIEW | 77976 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260515_235611.bak | KEEP_BUT_REVIEW | 77864 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260515_184039.bak | KEEP_BUT_REVIEW | 77839 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260515_192042.bak | KEEP_BUT_REVIEW | 77839 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260515_234041.bak | KEEP_BUT_REVIEW | 77839 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\factor_shadow_outcome_tracker.csv.before_v18_3B_R2_20260516_013225.bak | KEEP_BUT_REVIEW | 77839 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_014422.bak | KEEP_BUT_REVIEW | 77418 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_014958.bak | KEEP_BUT_REVIEW | 77418 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| state\v18\simulation\V18_CURRENT_SIM_CANDIDATE_TRACKER.csv.before_v18_10A_R2_factor_capture_20260517_020200.bak | KEEP_BUT_REVIEW | 77418 | State backup; never delete directly from this audit. | High | QUARANTINE_FIRST |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260518_131254.csv | SAFE_DELETE_GENERATED | 54376 | Timestamped generated report/audit superseded by current outputs. | Medium | DELETE_DRYRUN_ONLY |

## Active-Chain Exclusions

- `run_v18_current_official_daily.ps1` is protected and remains outside cleanup.
- `run_v18_current_shadow_research_daily.ps1` is protected and remains outside cleanup.
- Active V18.9C official chain and V18.10B/10C/10D shadow research chain scripts are protected.
- `state\v18` is protected from delete actions by this audit.
- Current read-first/current report outputs are protected.

## Stable Snapshot Retention Notes

- Latest protected V18_10D_R2 snapshot: `archive\stable\v18_10d_r2_stable_current_shadow_research_daily_20260517_020553`
- Older stable snapshots are classified `KEEP_BUT_REVIEW`, not delete candidates.
- Stable snapshot deletion requires a separate retention policy and approval.

## Dangerous Cleanup Script Warnings

- `run_v18_4K_R2_safe_delete_cleanup.ps1` has an `-Apply` path or delete/move behavior. Do not run with `-Apply` without explicit approval.
- `run_v18_4K_workspace_cleanup.ps1` has an `-Apply` path or delete/move behavior. Do not run with `-Apply` without explicit approval.
- `run_v18_5D_generated_output_retention_cleanup.ps1` has an `-Apply` path or delete/move behavior. Do not run with `-Apply` without explicit approval.
- `run_v18_8A_legacy_v15_v16_purge.ps1` has an `-Apply` path or delete/move behavior. Do not run with `-Apply` without explicit approval.

## Outputs

- CSV: `D:\us-tech-quant\outputs\v18\ops\V18_CLEANUP_AUDIT_CURRENT.csv`
- MD: `D:\us-tech-quant\outputs\v18\ops\V18_CLEANUP_AUDIT_CURRENT.md`
- READ_FIRST: `D:\us-tech-quant\outputs\v18\ops\V18_CLEANUP_AUDIT_READ_FIRST.txt`
