from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R12_TECHNICAL_TIMING_CURRENT_MERGE_READY"
STATUS_WARN = "WARN_V18_25A_R12_TECHNICAL_TIMING_CURRENT_MERGE_READY"
STATUS_FAIL = "FAIL_V18_25A_R12_TECHNICAL_TIMING_CURRENT_MERGE"
MODE = "TECHNICAL_TIMING_CURRENT_MERGE_WITH_BACKUP"

R11_READ_FIRST = "outputs/v18/ops/V18_25A_R11_READ_FIRST.txt"
R11_STAGED = "outputs/v18/technical_timing/V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_STAGED.csv"
R11_GATE = "outputs/v18/degraded_daily_review/V18_25A_R11_CURRENT_TECHNICAL_MERGE_READINESS_GATE.csv"
R11_SCHEMA = "outputs/v18/technical_timing/V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_SCHEMA_AUDIT.csv"
CURRENT_TECH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
BACKUP_ROOT = "archive/v18/technical_timing_backups"

OUT_PLAN = "outputs/v18/technical_timing/V18_25A_R12_CURRENT_TECHNICAL_TIMING_MERGE_PLAN.csv"
OUT_RESULT = "outputs/v18/technical_timing/V18_25A_R12_CURRENT_TECHNICAL_TIMING_MERGE_RESULT.csv"
OUT_SCHEMA = "outputs/v18/technical_timing/V18_25A_R12_CURRENT_TECHNICAL_TIMING_SCHEMA_MERGE_AUDIT.csv"
OUT_VALIDATION = "outputs/v18/technical_timing/V18_25A_R12_CURRENT_TECHNICAL_TIMING_POST_MERGE_VALIDATION.csv"
OUT_REPORT = "outputs/v18/degraded_daily_review/V18_25A_R12_CURRENT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R12_READ_FIRST.txt"
OUT_OPS_REPORT = "outputs/v18/ops/V18_25A_R12_CURRENT_TECHNICAL_TIMING_MERGE_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R11_SOURCE_PATH",
    "CURRENT_TECHNICAL_PATH",
    "STAGED_TECHNICAL_PATH",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_PATH",
    "R11_MERGE_READY_COUNT",
    "R11_MERGE_BLOCKED_COUNT",
    "TARGET_TICKER_COUNT",
    "PRE_MERGE_CURRENT_ROW_COUNT",
    "STAGED_ROW_COUNT",
    "MERGE_ATTEMPT_COUNT",
    "MERGE_UPDATE_COUNT",
    "MERGE_APPEND_COUNT",
    "MERGE_FAIL_COUNT",
    "POST_MERGE_CURRENT_ROW_COUNT",
    "TARGET_TICKERS_PRESENT_AFTER_MERGE",
    "TARGET_DUPLICATE_COUNT_AFTER_MERGE",
    "NON_TARGET_ROWS_PRESERVED",
    "SCHEMA_COMPATIBILITY_STATUS",
    "CURRENT_TECHNICAL_FILE_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BUY_PERMISSION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

PLAN_FIELDS = ["plan_item", "path", "status", "notes"]
RESULT_FIELDS = ["merge_item", "value", "notes"]
SCHEMA_FIELDS = ["schema_item", "value", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]
BACKUP_FIELDS = ["backup_item", "path", "status", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def parse_read_first(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def lookup(rows: Sequence[Dict[str, str]], key_col: str, value_col: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in rows:
        key = str(row.get(key_col, "")).strip()
        if key:
            out[key] = str(row.get(value_col, "")).strip()
    return out


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def is_allowed_r12_output(path: Path, root: Path) -> bool:
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    allowed = {
        OUT_PLAN,
        OUT_RESULT,
        OUT_SCHEMA,
        OUT_VALIDATION,
        OUT_REPORT,
        OUT_READ_FIRST,
        OUT_OPS_REPORT,
        CURRENT_TECH,
    }
    return rel in allowed


def protected_files(root: Path) -> List[Path]:
    rels = [
        "state/v18/price_cache",
        "state/v18/market_proxy_cache",
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "data/v18/staged_market_proxy",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/ranking",
        "outputs/v18/tier_migration",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
        "outputs/v18/technical_timing",
        "outputs/v18/degraded_daily_review",
    ]
    out: List[Path] = []
    for rel in rels:
        base = root / rel
        if not base.exists():
            continue
        paths = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in paths:
            try:
                if is_allowed_r12_output(path, root):
                    continue
            except ValueError:
                pass
            out.append(path)
    return out


def changed_forbidden_files(root: Path, before: Dict[str, Tuple[int, int]]) -> List[str]:
    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig)
    changed.extend(sorted(path for path in after if path not in before))
    return changed


def render_restore_script(current_path: Path, backup_file: Path) -> str:
    return f"""$ErrorActionPreference = "Stop"
Write-Host "===== RESTORE V18.25A-R12 TECHNICAL TIMING START ====="
if (-not (Test-Path -LiteralPath "{backup_file}")) {{
    throw "Backup file missing: {backup_file}"
}}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent "{current_path}") | Out-Null
Copy-Item -LiteralPath "{backup_file}" -Destination "{current_path}" -Force
Write-Host "RESTORED: {current_path}"
Write-Host "===== RESTORE V18.25A-R12 TECHNICAL TIMING END ====="
"""


def align_row(staged_row: Dict[str, str], current_fields: Sequence[str]) -> Dict[str, object]:
    return {field: staged_row.get(field, "") for field in current_fields}


def row_fingerprint(row: Dict[str, object], fields: Sequence[str]) -> Tuple[str, ...]:
    return tuple(str(row.get(field, "") if row.get(field, "") is not None else "").strip() for field in fields)


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.25A-R12 Technical Timing Current Merge With Backup

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {MODE}

Current technical file: `{values['CURRENT_TECHNICAL_PATH']}`

Staged technical file: `{values['STAGED_TECHNICAL_PATH']}`

Backup directory: `{values['BACKUP_DIR']}`

Restore script: `{values['RESTORE_SCRIPT_PATH']}`

Merge counts: attempted={values['MERGE_ATTEMPT_COUNT']}, updated={values['MERGE_UPDATE_COUNT']}, appended={values['MERGE_APPEND_COUNT']}, failed={values['MERGE_FAIL_COUNT']}

Rows: pre={values['PRE_MERGE_CURRENT_ROW_COUNT']}, staged={values['STAGED_ROW_COUNT']}, post={values['POST_MERGE_CURRENT_ROW_COUNT']}

Schema compatibility: {values['SCHEMA_COMPATIBILITY_STATUS']}

Safety: no external fetch, no price cache/market proxy/factor/tier/degraded-current/decision/trading permission changes. OFFICIAL_DECISION_IMPACT remains NONE.

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    script_path = root / "scripts/v18/v18_25A_R12_technical_timing_current_merge_with_backup.py"
    wrapper_path = root / "scripts/v18/run_v18_25A_R12_technical_timing_current_merge_with_backup.ps1"
    current_path = root / CURRENT_TECH
    staged_path = root / R11_STAGED
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R12_{timestamp}"
    backup_file = backup_dir / "V18_6A_CURRENT_TECHNICAL_TIMING.before_V18_25A_R12.csv"
    restore_path = backup_dir / "RESTORE_V18_25A_R12_TECHNICAL_TIMING.ps1"
    backup_manifest = backup_dir / "BACKUP_MANIFEST.csv"

    before_forbidden = {str(path): file_sig(path) for path in protected_files(root)}
    current_sig_before = file_sig(current_path)

    r11 = parse_read_first(root / R11_READ_FIRST)
    gate_rows, _ = read_csv(root / R11_GATE)
    schema_rows, _ = read_csv(root / R11_SCHEMA)
    schema_lookup = lookup(schema_rows, "schema_check", "value")
    staged_rows, staged_fields = read_csv(staged_path)
    current_rows, current_fields = read_csv(current_path)

    staged_tickers = [norm_ticker(row.get("ticker", "")) for row in staged_rows if norm_ticker(row.get("ticker", ""))]
    target_tickers = sorted(set(staged_tickers))
    gate_ready = sum(1 for row in gate_rows if str(row.get("merge_ready", "")).strip().upper() == "TRUE")
    gate_blocked = sum(1 for row in gate_rows if str(row.get("merge_ready", "")).strip().upper() != "TRUE")
    schema_extra = sorted(set(staged_fields) - set(current_fields))
    schema_missing = sorted(set(current_fields) - set(staged_fields))
    schema_status = "MERGE_SCHEMA_COMPATIBLE" if not schema_missing else "MERGE_SCHEMA_REVIEW_REQUIRED"

    preconditions = {
        "r11_status_ok": r11.get("STATUS", "").startswith("OK_"),
        "r11_merge_ready_52": r11.get("MERGE_READY_COUNT", "") == "52",
        "r11_merge_blocked_0": r11.get("MERGE_BLOCKED_COUNT", "") == "0",
        "staged_exists": staged_path.exists(),
        "staged_row_count_52": len(staged_rows) == 52,
        "current_exists": current_path.exists(),
        "staged_has_ticker": "ticker" in staged_fields,
        "current_has_ticker": "ticker" in current_fields,
        "formula_compatible": r11.get("FORMULA_COMPATIBILITY_STATUS", "") in {"FULL_COMPATIBLE_WITH_LOCAL_REIMPLEMENTATION", "EXACT_COMPATIBLE", "EXACT_V18_6A_FORMULA_REUSED"},
        "vix_overlay_included": r11.get("VIX_OVERLAY_INCLUDED", "").upper() == "TRUE",
    }

    ensure_dir(backup_dir)
    if current_path.exists():
        shutil.copy2(current_path, backup_file)
    write_text(restore_path, render_restore_script(current_path, backup_file))
    backup_rows = [
        {"backup_item": "backup_dir", "path": str(backup_dir), "status": str(backup_dir.exists()).upper(), "notes": "Timestamped R12 technical timing backup directory."},
        {"backup_item": "current_technical_backup", "path": str(backup_file), "status": str(backup_file.exists()).upper(), "notes": "Original current technical timing file before merge."},
        {"backup_item": "restore_script", "path": str(restore_path), "status": str(restore_path.exists()).upper(), "notes": "Restores original V18_6A_CURRENT_TECHNICAL_TIMING.csv."},
    ]
    write_csv(backup_manifest, backup_rows, BACKUP_FIELDS)

    merge_attempt = len(target_tickers)
    merge_update = 0
    merge_append = 0
    merge_fail = 0
    post_rows: List[Dict[str, object]] = []
    staged_by_ticker = {norm_ticker(row.get("ticker", "")): row for row in staged_rows}
    current_target_seen = set()
    non_target_before = [row for row in current_rows if norm_ticker(row.get("ticker", "")) not in set(target_tickers)]

    if all(preconditions.values()) and backup_file.exists() and restore_path.exists():
        for row in current_rows:
            ticker = norm_ticker(row.get("ticker", ""))
            if ticker in staged_by_ticker:
                if ticker in current_target_seen:
                    continue
                post_rows.append(align_row(staged_by_ticker[ticker], current_fields))
                current_target_seen.add(ticker)
                merge_update += 1
            else:
                post_rows.append(row)
        for ticker in target_tickers:
            if ticker not in current_target_seen:
                post_rows.append(align_row(staged_by_ticker[ticker], current_fields))
                merge_append += 1
        merge_fail = merge_attempt - merge_update - merge_append
        write_csv(current_path, post_rows, current_fields)
    else:
        merge_fail = merge_attempt
        post_rows = current_rows

    post_current_rows, post_current_fields = read_csv(current_path)
    post_by_ticker: Dict[str, List[Dict[str, str]]] = {}
    for row in post_current_rows:
        ticker = norm_ticker(row.get("ticker", ""))
        if ticker:
            post_by_ticker.setdefault(ticker, []).append(row)
    target_present = sum(1 for ticker in target_tickers if ticker in post_by_ticker)
    target_duplicate_count = sum(max(0, len(post_by_ticker.get(ticker, [])) - 1) for ticker in target_tickers)
    non_target_after = [row for row in post_current_rows if norm_ticker(row.get("ticker", "")) not in set(target_tickers)]
    non_target_preserved = len(non_target_after) == len(non_target_before)

    aligned_match_count = 0
    for ticker in target_tickers:
        rows_after = post_by_ticker.get(ticker, [])
        if len(rows_after) != 1:
            continue
        expected = align_row(staged_by_ticker[ticker], current_fields)
        if row_fingerprint(rows_after[0], current_fields) == row_fingerprint(expected, current_fields):
            aligned_match_count += 1

    current_modified = file_sig(current_path) != current_sig_before
    forbidden_changed = changed_forbidden_files(root, before_forbidden)
    validations = [
        validation_row("python_compile_check", subprocess.run([sys.executable, "-m", "py_compile", str(script_path)], capture_output=True).returncode == 0, 1, str(script_path)),
        validation_row("powershell_parse_check", ps_parse(wrapper_path), 1, str(wrapper_path)),
        validation_row("target_ticker_count_52", len(target_tickers) == 52, 1, str(len(target_tickers))),
        validation_row("backup_file_exists", backup_file.exists(), 1, str(backup_file)),
        validation_row("restore_script_exists", restore_path.exists(), 1, str(restore_path)),
        validation_row("backup_manifest_exists", backup_manifest.exists(), 1, str(backup_manifest)),
        validation_row("post_current_exists", current_path.exists(), 1, str(current_path)),
        validation_row("post_row_count_gte_pre", len(post_current_rows) >= len(current_rows), 1, f"pre={len(current_rows)} post={len(post_current_rows)}"),
        validation_row("all_targets_present", target_present == len(target_tickers), 1, str(target_present)),
        validation_row("no_target_duplicates", target_duplicate_count == 0, target_duplicate_count, str(target_duplicate_count)),
        validation_row("target_rows_match_staged_aligned", aligned_match_count == len(target_tickers), len(target_tickers) - aligned_match_count, str(aligned_match_count)),
        validation_row("non_target_rows_preserved", non_target_preserved, 1, f"before={len(non_target_before)} after={len(non_target_after)}"),
        validation_row("no_external_fetch", True, 0, "R12 does not fetch external data."),
        validation_row("forbidden_files_unchanged", not forbidden_changed, len(forbidden_changed), ";".join(forbidden_changed[:20])),
    ]
    for name, ok in preconditions.items():
        validations.append(validation_row(f"precondition_{name}", ok, 1, str(ok)))
    fail_count = sum(int(row["fail_count"]) for row in validations)

    status = STATUS_FAIL
    if fail_count == 0 and merge_fail == 0 and schema_status == "MERGE_SCHEMA_COMPATIBLE":
        status = STATUS_OK
    elif fail_count == 0 and merge_fail == 0:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "R11_SOURCE_PATH": str(root / R11_READ_FIRST),
        "CURRENT_TECHNICAL_PATH": str(current_path),
        "STAGED_TECHNICAL_PATH": str(staged_path),
        "BACKUP_DIR": str(backup_dir),
        "RESTORE_SCRIPT_PATH": str(restore_path),
        "R11_MERGE_READY_COUNT": r11.get("MERGE_READY_COUNT", str(gate_ready)),
        "R11_MERGE_BLOCKED_COUNT": r11.get("MERGE_BLOCKED_COUNT", str(gate_blocked)),
        "TARGET_TICKER_COUNT": str(len(target_tickers)),
        "PRE_MERGE_CURRENT_ROW_COUNT": str(len(current_rows)),
        "STAGED_ROW_COUNT": str(len(staged_rows)),
        "MERGE_ATTEMPT_COUNT": str(merge_attempt),
        "MERGE_UPDATE_COUNT": str(merge_update),
        "MERGE_APPEND_COUNT": str(merge_append),
        "MERGE_FAIL_COUNT": str(merge_fail),
        "POST_MERGE_CURRENT_ROW_COUNT": str(len(post_current_rows)),
        "TARGET_TICKERS_PRESENT_AFTER_MERGE": str(target_present),
        "TARGET_DUPLICATE_COUNT_AFTER_MERGE": str(target_duplicate_count),
        "NON_TARGET_ROWS_PRESERVED": str(non_target_preserved).upper(),
        "SCHEMA_COMPATIBILITY_STATUS": schema_status,
        "CURRENT_TECHNICAL_FILE_MODIFIED": str(current_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(current_modified).upper(),
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changed)).upper(),
        "NEXT_RECOMMENDED_STEP": "Run a post-merge daily command/read-center validation before any official decision impact is allowed.",
    }

    plan_rows = [
        {"plan_item": "backup_current_technical", "path": str(backup_file), "status": str(backup_file.exists()).upper(), "notes": "Backup created before current file modification."},
        {"plan_item": "restore_script", "path": str(restore_path), "status": str(restore_path.exists()).upper(), "notes": "Restores pre-R12 current technical timing file."},
        {"plan_item": "merge_strategy", "path": str(current_path), "status": "REPLACE_OR_APPEND_BY_TICKER", "notes": "Preserve current schema and non-target rows."},
        {"plan_item": "schema_extra_fields", "path": str(staged_path), "status": "DOCUMENTED_NOT_MERGED", "notes": ",".join(schema_extra)},
    ]
    result_rows = [
        {"merge_item": "merge_attempt_count", "value": merge_attempt, "notes": "Unique staged target tickers."},
        {"merge_item": "merge_update_count", "value": merge_update, "notes": "Existing target rows replaced."},
        {"merge_item": "merge_append_count", "value": merge_append, "notes": "New target rows appended."},
        {"merge_item": "merge_fail_count", "value": merge_fail, "notes": "Targets not merged."},
        {"merge_item": "post_merge_current_row_count", "value": len(post_current_rows), "notes": "Rows in current file after merge."},
        {"merge_item": "target_rows_match_staged_aligned", "value": aligned_match_count, "notes": "Aligned current-schema target rows matching staged rows."},
    ]
    schema_audit_rows = [
        {"schema_item": "current_field_count", "value": len(current_fields), "notes": ",".join(current_fields)},
        {"schema_item": "staged_field_count", "value": len(staged_fields), "notes": ",".join(staged_fields)},
        {"schema_item": "missing_current_fields_from_staged", "value": len(schema_missing), "notes": ",".join(schema_missing)},
        {"schema_item": "extra_staged_fields_not_merged", "value": len(schema_extra), "notes": ",".join(schema_extra)},
        {"schema_item": "schema_compatibility_status", "value": schema_status, "notes": "Current schema preserved in V18_6A_CURRENT_TECHNICAL_TIMING.csv."},
    ]

    write_csv(root / OUT_PLAN, plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_csv(root / OUT_SCHEMA, schema_audit_rows, SCHEMA_FIELDS)
    write_csv(root / OUT_VALIDATION, validations, VALIDATION_FIELDS)
    report = render_report(values)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_OPS_REPORT, report)
    write_text(root / OUT_READ_FIRST, render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if status != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
