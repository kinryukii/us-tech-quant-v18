# V18.5C Archive Zero-Runtime Candidates

Generated: 2026-05-15 19:17:06

## 1. Status

- STATUS: OK_ARCHIVE_ZERO_RUNTIME_CANDIDATES_READY
- MODE: APPLY
- INPUT: D:\us-tech-quant\outputs\v18\ops\V18_5B_CURRENT_DELETE_CANDIDATE_RUNTIME_AUDIT.csv
- RULE: archive-only; no permanent delete.

## 2. Summary

| Metric | Value |
|---|---|
| MODE | APPLY |
| CANDIDATE_COUNT | 1 |
| DRYRUN_WOULD_ARCHIVE_COUNT | 0 |
| ARCHIVED_COUNT | 1 |
| ALREADY_MISSING_COUNT | 0 |
| FAIL_COUNT | 0 |
| ARCHIVE_ROOT | D:\us-tech-quant\archive\deprecated\v18_5C_zero_runtime_archive_20260515_191705 |
| RESTORE_SCRIPT | D:\us-tech-quant\archive\deprecated\v18_5C_zero_runtime_archive_20260515_191705\restore_v18_5C_zero_runtime_archive.ps1 |

## 3. Results

| CandidateRel | ExistsBefore | Action | Status | SourcePath | ArchivePath | Sha256 | SizeBytes |
|---|---|---|---|---|---|---|---|
| scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | True | APPLY | ARCHIVED | D:\us-tech-quant\scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | D:\us-tech-quant\archive\deprecated\v18_5C_zero_runtime_archive_20260515_191705\scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1 | 6D347EE42C13BD3A48C522EDB44EDEB5A08CE5130CB67BA28F22781029A25576 | 7891 |

## 4. Next Action

Run V18.4J-R1 final daily read center wrapper to validate full chain after archive.
If validation fails, use the restore script listed above.


