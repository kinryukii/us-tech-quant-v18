# V18.4K Workspace Cleanup Report

Generated at: 2026-05-15 17:20:36

## 1. Mode

- APPLY: True
- ARCHIVE_TARGET: D:\us-tech-quant\archive\deprecated\v18_4K_workspace_cleanup_20260515_172036
- FINAL_DAILY_COMMAND: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"

## 2. Protected

- KEEP: scripts
- KEEP: src
- KEEP: state
- KEEP: configs
- KEEP: archive\stable
- KEEP: outputs\v18\read_center
- KEEP: outputs\v18\daily_integrated
- KEEP: outputs\v18\promotion_merge
- KEEP: outputs\v18\outcome_summary
- KEEP: outputs\v18\forward_outcome
- KEEP: outputs\v18\factor_audit
- KEEP: outputs\v18\factor_backtest
- KEEP: outputs\v18\factor_pack
- KEEP: outputs\v18\ops

## 3. Candidates

| path | files | size_mb | action |
|---|---:|---:|---|
| outputs\v16 | 24 | 0.166 | MOVE_TO_ARCHIVE |
| outputs\v17 | 83 | 0.393 | MOVE_TO_ARCHIVE |
| logs\v16 | 0 | 0 | MOVE_TO_ARCHIVE |
| outputs\v18\factor_lab | 6 | 0.08 | MOVE_TO_ARCHIVE |
| outputs\v18\factor_shadow | 15 | 0.091 | MOVE_TO_ARCHIVE |
| outputs\v18\factor_validation | 13 | 0.625 | MOVE_TO_ARCHIVE |
| outputs\v18\manifests | 6 | 0.005 | MOVE_TO_ARCHIVE |
| outputs\v18\cockpit | 5 | 0.007 | MOVE_TO_ARCHIVE |
| outputs\v18\daily | 0 | 0 | MOVE_TO_ARCHIVE |
| data\prices | 105 | 4.536 | MOVE_TO_ARCHIVE |
| data\events | 3 | 0.001 | MOVE_TO_ARCHIVE |

## 4. Result

- CANDIDATE_COUNT: 11
- MOVE_FAIL_COUNT: 0
- REPORT_CSV: D:\us-tech-quant\outputs\v18\ops\V18_4K_WORKSPACE_CLEANUP_CANDIDATES_20260515_172036.csv
