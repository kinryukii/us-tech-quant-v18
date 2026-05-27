# V18 Cleanup Delete Plan

Generated: `2026-05-17 22:56:27`

## Status

- MODE: `DELETE_GENERATED_ONLY`
- DELETE_ENABLED: `True`
- OFFICIAL_DECISION_IMPACT: `NONE`

## Summary

- TARGET_COUNT: `625`
- TARGET_BYTES: `6017696`
- TARGET_MB: `5.739`
- DELETED_COUNT: `625`
- DELETED_BYTES: `6017696`
- FAILED_COUNT: `0`
- SKIPPED_COUNT: `8122`

## Skipped By Reason

| skip_reason | count |
|---|---:|
| PROTECTED_SCRIPTS_V18 | 26 |
| SKIP_RECOMMENDED_ACTION_NOT_DELETE_DRYRUN_ONLY | 8096 |

## Top 30 Delete Targets

| source_path | size_bytes | risk | status |
|---|---:|---|---|
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260517_221536.csv | 104798 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260517_220121.csv | 101009 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260517_215434.csv | 97220 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_155033.csv | 93079 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260516_152701.csv | 92839 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_153902.csv | 89290 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260516_142800.csv | 83593 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_152529.csv | 83309 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_151304.csv | 81909 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_151139.csv | 80509 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_144715.csv | 78528 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260516_141153.csv | 77497 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_144515.csv | 77128 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260515_234059.csv | 75816 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260515_234101.csv | 73338 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_142802.csv | 73338 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260515_234047.csv | 71938 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_142554.csv | 71938 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260516_134014.csv | 70483 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260517_221754.csv | 70318 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260515_192053.csv | 69720 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260515_192054.csv | 68144 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_141154.csv | 68144 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_140949.csv | 66744 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260517_220328.csv | 65712 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260515_184050.csv | 63619 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_20260516_021625.csv | 63474 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_134016.csv | 62955 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4D_FACTOR_PACK_AUDIT_20260516_133757.csv | 61555 | Medium | DELETED |
| outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260517_215621.csv | 61506 | Medium | DELETED |

## Safety Notes

- Default mode is DRY_RUN.
- Direct deletion requires explicit `-DeleteGeneratedOnly` on the wrapper.
- Delete targets are read only from `V18_CLEANUP_QUARANTINE_PLAN_CURRENT.csv`.
- No broad glob-based delete is used.
- Protected paths include `scripts\v18`, `state\v18`, `archive\stable`, `.venv`, and `node_modules`.
- Current wrappers, current read-first files, current official/shadow reports, protected `.bak` files, and stable snapshots are protected.

## Outputs

- DELETE_PLAN_CSV: `D:\us-tech-quant\outputs\v18\ops\V18_CLEANUP_DELETE_PLAN_CURRENT.csv`
- DELETE_PLAN_MD: `D:\us-tech-quant\outputs\v18\ops\V18_CLEANUP_DELETE_PLAN_CURRENT.md`
- DELETE_READ_FIRST: `D:\us-tech-quant\outputs\v18\ops\V18_CLEANUP_DELETE_READ_FIRST.txt`
