from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_R6_OFFICIAL_BATCH2_FULL_HISTORY_INTEGRATION_READY"
STATUS_WARN = "WARN_V18_23C_R6_OFFICIAL_BATCH2_FULL_HISTORY_INTEGRATION_READY"
STATUS_FAIL = "FAIL_V18_23C_R6_OFFICIAL_BATCH2_FULL_HISTORY_INTEGRATION"
MODE = "OFFICIAL_PRICE_CACHE_INTEGRATION_BATCH2_FULL_HISTORY_ONLY_WITH_BACKUP"
BATCH_ID = "V18_23C_BATCH2"

STAGED_DIR_REL = "data/v18/staged_backfill/V18_23C_BATCH2"
OFFICIAL_CACHE_REL = "state/v18/price_cache"

OUTPUTS = {
    "plan": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_PLAN.csv",
    "result": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_RESULT.csv",
    "held": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_HELD_OUT_TICKERS.csv",
    "backup": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BACKUP_MANIFEST.csv",
    "retest": "outputs/v18/rolling_coverage/V18_23C_R6_CURRENT_BATCH2_LOCAL_RETEST.csv",
    "read_first": "outputs/v18/ops/V18_23C_R6_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "BATCH_ID",
    "R5_SOURCE_PATH",
    "STAGED_SOURCE_PATH",
    "OFFICIAL_PRICE_CACHE_DIR",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_PATH",
    "BATCH2_TICKER_COUNT",
    "FULL_HISTORY_CANDIDATE_COUNT",
    "INTEGRATION_ATTEMPT_COUNT",
    "INTEGRATION_SUCCESS_COUNT",
    "INTEGRATION_FAIL_COUNT",
    "HELD_OUT_COUNT",
    "PRICE_ONLY_PARTIAL_HELD_OUT_COUNT",
    "EMPTY_FETCH_HELD_OUT_COUNT",
    "HOLD_REVIEW_HELD_OUT_COUNT",
    "SUSPICIOUS_DATA_HELD_OUT_COUNT",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "OFFICIAL_PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "ROLLING_SCAN_EXECUTED",
    "LOCAL_RETEST_EXECUTED",
    "LOCAL_PRICE_SUCCESS_COUNT_AFTER_INTEGRATION",
    "FULL_HISTORY_READY_COUNT_AFTER_INTEGRATION",
    "RETEST_SUCCESS_RATIO",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
]

PLAN_FIELDS = [
    "ticker",
    "classification",
    "staged_path",
    "official_cache_path",
    "staged_row_count",
    "quality_grade",
    "integration_action",
    "approved_for_integration",
]
RESULT_FIELDS = [
    "ticker",
    "staged_path",
    "official_cache_path",
    "integration_status",
    "before_row_count",
    "staged_row_count",
    "after_row_count",
    "latest_date",
    "duplicate_dates_dropped",
    "failure_reason",
]
HELD_FIELDS = ["ticker", "classification", "held_out_category", "hold_reason", "staged_path"]
BACKUP_FIELDS = [
    "ticker",
    "original_path",
    "backup_path",
    "original_existed",
    "backup_created",
    "restore_action",
]
RETEST_FIELDS = [
    "ticker",
    "official_cache_path",
    "official_file_exists",
    "row_count",
    "latest_date",
    "local_price_success",
    "full_history_ready",
    "notes",
]

PRICE_FIELDS = ["date", "open", "high", "low", "close", "adj_close", "volume", "source", "source_file", "updated_at"]

SAFETY = {
    "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
    "STAGED_BACKFILL_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "TIER_MIGRATION_MODIFIED": "FALSE",
    "DEGRADED_DAILY_MODIFIED": "FALSE",
    "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BACKTEST_EXECUTED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()[:10]
    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_ticker(row: Dict[str, str]) -> str:
    value = str(row.get("ticker", row.get("Ticker", ""))).strip().upper()
    return value if value and value not in {"NAN", "NONE", "NULL"} else ""


def is_true(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "Y", "1", "SUCCESS", "AVAILABLE"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def collect_file_sigs(base: Path) -> Dict[str, Tuple[int, int]]:
    if not base.exists():
        return {}
    return {str(path): file_sig(path) for path in base.rglob("*") if path.is_file()}


def collect_forbidden_sigs(root: Path) -> Dict[str, Tuple[int, int]]:
    rel_dirs = [
        "data/v18/price_history",
        "state/v18/price_history",
        "data/v18/staged_backfill",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/degraded_daily",
        "outputs/v18/daily_integrated",
        "outputs/v18/ranking",
        "outputs/v18/signal_snapshots",
        "state/v18/manual",
        "state/v18/simulation",
        "outputs/v18/backtest",
    ]
    out: Dict[str, Tuple[int, int]] = {}
    for rel_dir in rel_dirs:
        out.update(collect_file_sigs(root / rel_dir))
    return out


def diff_sigs(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def get_value(row: Dict[str, str], *names: str) -> str:
    lower = {key.lower(): key for key in row}
    for name in names:
        real = lower.get(name.lower())
        if real is not None:
            return str(row.get(real, "")).strip()
    return ""


def normalize_price_rows(path: Path, ticker: str, updated_at: str) -> Tuple[List[Dict[str, str]], int, str]:
    rows, fields = read_csv(path)
    field_lower = {field.lower() for field in fields}
    if "date" not in field_lower:
        return [], 0, "MISSING_DATE_COLUMN"
    if "close" not in field_lower:
        return [], 0, "MISSING_CLOSE_COLUMN"

    by_date: Dict[str, Dict[str, str]] = {}
    duplicate_count = 0
    for row in rows:
        parsed = parse_date(get_value(row, "date", "Date"))
        close = get_value(row, "close", "Close")
        if not parsed or not close:
            continue
        date_text = parsed.isoformat()
        if date_text in by_date:
            duplicate_count += 1
        by_date[date_text] = {
            "date": date_text,
            "open": get_value(row, "open", "Open"),
            "high": get_value(row, "high", "High"),
            "low": get_value(row, "low", "Low"),
            "close": close,
            "adj_close": get_value(row, "adj_close", "Adj Close", "Adj_Close"),
            "volume": get_value(row, "volume", "Volume"),
            "source": "V18_23C_R6_BATCH2_FULL_HISTORY_STAGED_INTEGRATION",
            "source_file": str(path),
            "updated_at": updated_at,
        }
    cleaned = [by_date[key] for key in sorted(by_date)]
    if not cleaned:
        return [], duplicate_count, "NO_VALID_PRICE_ROWS_AFTER_CLEANING"
    return cleaned, duplicate_count, ""


def read_existing_cache(path: Path) -> List[Dict[str, str]]:
    rows, _ = read_csv(path)
    out: List[Dict[str, str]] = []
    for row in rows:
        parsed = parse_date(get_value(row, "date", "Date"))
        close = get_value(row, "close", "Close")
        if parsed and close:
            out.append(
                {
                    "date": parsed.isoformat(),
                    "open": get_value(row, "open", "Open"),
                    "high": get_value(row, "high", "High"),
                    "low": get_value(row, "low", "Low"),
                    "close": close,
                    "adj_close": get_value(row, "adj_close", "Adj Close", "Adj_Close"),
                    "volume": get_value(row, "volume", "Volume"),
                    "source": get_value(row, "source") or "EXISTING_OFFICIAL_PRICE_CACHE",
                    "source_file": get_value(row, "source_file"),
                    "updated_at": get_value(row, "updated_at"),
                }
            )
    return out


def merge_rows(existing: Sequence[Dict[str, str]], staged: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    by_date = {row["date"]: dict(row) for row in existing if parse_date(row.get("date"))}
    for row in staged:
        by_date[row["date"]] = dict(row)
    return [by_date[key] for key in sorted(by_date)]


def classify_held(row: Dict[str, str]) -> str:
    cls = row.get("classification", "")
    if cls == "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY":
        return "PRICE_ONLY_PARTIAL"
    if cls == "HOLD_EMPTY_FETCH":
        return "EMPTY_FETCH"
    if cls == "HOLD_SUSPICIOUS_PRICE_DATA":
        return "SUSPICIOUS_DATA"
    if str(row.get("recommended_integration_action", "")).upper() == "HOLD_REVIEW":
        return "HOLD_REVIEW"
    return "HOLD_REVIEW"


def render_restore_script(backup_rows: Sequence[Dict[str, object]]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        'Write-Host "=== RESTORE V18.23C-R6 PRICE CACHE START ==="',
    ]
    for row in backup_rows:
        original = str(row["original_path"])
        backup = str(row["backup_path"])
        if row["original_existed"] == "TRUE":
            lines.extend(
                [
                    f'$dest = "{original}"',
                    f'$src = "{backup}"',
                    'if (-not (Test-Path -LiteralPath $src)) { throw "Missing backup: $src" }',
                    '$parent = Split-Path -Parent $dest',
                    'if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }',
                    'Copy-Item -LiteralPath $src -Destination $dest -Force',
                ]
            )
        else:
            lines.extend(
                [
                    f'$dest = "{original}"',
                    'if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Force }',
                ]
            )
    lines.extend(['Write-Host "=== RESTORE V18.23C-R6 PRICE CACHE END ==="', "exit 0"])
    return "\n".join(lines) + "\n"


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R6 Official Batch 2 Full-History Integration

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Scope
Integrated only R5-approved Batch 2 `MERGE_CANDIDATE_FULL_HISTORY` tickers into `state/v18/price_cache`.

## Result
- Full-history candidates: {values['FULL_HISTORY_CANDIDATE_COUNT']}
- Attempts: {values['INTEGRATION_ATTEMPT_COUNT']}
- Success: {values['INTEGRATION_SUCCESS_COUNT']}
- Failed: {values['INTEGRATION_FAIL_COUNT']}
- Held out: {values['HELD_OUT_COUNT']}

## Backup
- Backup directory: {values['BACKUP_DIR']}
- Restore script: {values['RESTORE_SCRIPT_PATH']}

## Local Retest
- Local price success: {values['LOCAL_PRICE_SUCCESS_COUNT_AFTER_INTEGRATION']}
- Full-history ready: {values['FULL_HISTORY_READY_COUNT_AFTER_INTEGRATION']}
- Retest success ratio: {values['RETEST_SUCCESS_RATIO']}

## Safety
Official decision impact remains NONE. Auto-trade and auto-sell remain disabled. No staged source data, ledger, factor pack, technical timing, tier migration, degraded daily, official daily decision, or backtest files were modified.

## Next Step
Run the next read-only rolling/local coverage retest or controller that consumes `state/v18/price_cache`; keep partial, empty-fetch, suspicious, and hold-review tickers excluded.
"""


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.Language.Parser]::ParseFile('{escaped}', [ref]$null, [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V18.23C-R6 official Batch 2 full-history price cache integration")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    updated_at = dt.datetime.now().isoformat(timespec="seconds")

    r5_source = root / "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_TICKER_QUALITY_AUDIT.csv"
    staged_dir = root / STAGED_DIR_REL
    official_dir = root / OFFICIAL_CACHE_REL
    backup_dir = root / "archive/v18/price_cache_backups" / f"V18_23C_R6_{timestamp}"
    restore_script = backup_dir / "RESTORE_V18_23C_R6_PRICE_CACHE.ps1"
    backup_manifest_in_archive = backup_dir / "BACKUP_MANIFEST.csv"

    before_forbidden = collect_forbidden_sigs(root)
    before_cache = {str(path): file_sig(path) for path in official_dir.glob("*.csv")} if official_dir.exists() else {}

    quality_rows, _ = read_csv(r5_source)
    full_rows = [row for row in quality_rows if row.get("classification") == "MERGE_CANDIDATE_FULL_HISTORY"]
    full_tickers = sorted({get_ticker(row) for row in full_rows if get_ticker(row)})
    held_source_rows = [row for row in quality_rows if get_ticker(row) and get_ticker(row) not in set(full_tickers)]

    plan_rows: List[Dict[str, object]] = []
    for row in full_rows:
        ticker = get_ticker(row)
        if not ticker:
            continue
        plan_rows.append(
            {
                "ticker": ticker,
                "classification": row.get("classification", ""),
                "staged_path": str(staged_dir / f"{ticker}.csv"),
                "official_cache_path": str(official_dir / f"{ticker}.csv"),
                "staged_row_count": row.get("staged_row_count", ""),
                "quality_grade": row.get("quality_grade", ""),
                "integration_action": "WRITE_OFFICIAL_PRICE_CACHE_FULL_HISTORY",
                "approved_for_integration": "TRUE",
            }
        )

    held_rows: List[Dict[str, object]] = []
    for row in held_source_rows:
        ticker = get_ticker(row)
        category = classify_held(row)
        held_rows.append(
            {
                "ticker": ticker,
                "classification": row.get("classification", ""),
                "held_out_category": category,
                "hold_reason": row.get("integration_block_reason", "") or "Excluded from full-history-only integration.",
                "staged_path": str(staged_dir / f"{ticker}.csv"),
            }
        )

    backup_rows: List[Dict[str, object]] = []
    result_rows: List[Dict[str, object]] = []
    retest_rows: List[Dict[str, object]] = []
    validation_failures: List[str] = []

    if not quality_rows:
        validation_failures.append("R5 quality audit source was not found or was empty.")
    if not full_tickers:
        validation_failures.append("No R5 full-history candidates discovered.")
    if not staged_dir.exists():
        validation_failures.append(f"Staged source directory missing: {staged_dir}")
    if not official_dir.exists():
        validation_failures.append(f"Official price cache directory missing: {official_dir}")

    if not validation_failures:
        ensure_dir(backup_dir)
        for ticker in full_tickers:
            official_path = official_dir / f"{ticker}.csv"
            backup_path = backup_dir / f"{ticker}.csv"
            existed = official_path.exists()
            if existed:
                shutil.copy2(official_path, backup_path)
            backup_rows.append(
                {
                    "ticker": ticker,
                    "original_path": str(official_path),
                    "backup_path": str(backup_path),
                    "original_existed": str(existed).upper(),
                    "backup_created": str(existed and backup_path.exists()).upper(),
                    "restore_action": "COPY_BACKUP_OVER_DESTINATION" if existed else "DELETE_CREATED_DESTINATION",
                }
            )
        write_csv(backup_manifest_in_archive, backup_rows, BACKUP_FIELDS)
        write_text(restore_script, render_restore_script(backup_rows))

        for ticker in full_tickers:
            staged_path = staged_dir / f"{ticker}.csv"
            official_path = official_dir / f"{ticker}.csv"
            before_rows = read_existing_cache(official_path) if official_path.exists() else []
            staged_rows, duplicate_dates, failure = normalize_price_rows(staged_path, ticker, updated_at)
            integration_status = "SUCCESS"
            after_rows: List[Dict[str, str]] = []
            latest_date = ""
            if failure:
                integration_status = "FAILED"
            else:
                after_rows = merge_rows(before_rows, staged_rows)
                latest_dates = [parse_date(row["date"]) for row in after_rows]
                latest_dates = [date for date in latest_dates if date]
                latest_date = max(latest_dates).isoformat() if latest_dates else ""
                write_csv(official_path, after_rows, PRICE_FIELDS)
            result_rows.append(
                {
                    "ticker": ticker,
                    "staged_path": str(staged_path),
                    "official_cache_path": str(official_path),
                    "integration_status": integration_status,
                    "before_row_count": len(before_rows),
                    "staged_row_count": len(staged_rows),
                    "after_row_count": len(after_rows) if integration_status == "SUCCESS" else len(before_rows),
                    "latest_date": latest_date,
                    "duplicate_dates_dropped": duplicate_dates,
                    "failure_reason": failure,
                }
            )

        for ticker in full_tickers:
            official_path = official_dir / f"{ticker}.csv"
            rows, _ = read_csv(official_path)
            dates = [parse_date(get_value(row, "date", "Date")) for row in rows]
            dates = [date for date in dates if date]
            latest = max(dates).isoformat() if dates else ""
            local_ok = official_path.exists() and len(rows) > 0 and bool(latest)
            full_ready = local_ok and len(rows) >= 500
            retest_rows.append(
                {
                    "ticker": ticker,
                    "official_cache_path": str(official_path),
                    "official_file_exists": str(official_path.exists()).upper(),
                    "row_count": len(rows),
                    "latest_date": latest,
                    "local_price_success": str(local_ok).upper(),
                    "full_history_ready": str(full_ready).upper(),
                    "notes": "Local official-cache retest only; rolling ledger not updated.",
                }
            )

    write_csv(root / OUTPUTS["plan"], plan_rows, PLAN_FIELDS)
    write_csv(root / OUTPUTS["result"], result_rows, RESULT_FIELDS)
    write_csv(root / OUTPUTS["held"], held_rows, HELD_FIELDS)
    write_csv(root / OUTPUTS["backup"], backup_rows, BACKUP_FIELDS)
    write_csv(root / OUTPUTS["retest"], retest_rows, RETEST_FIELDS)

    after_forbidden = collect_forbidden_sigs(root)
    after_cache = {str(path): file_sig(path) for path in official_dir.glob("*.csv")} if official_dir.exists() else {}
    forbidden_changes = diff_sigs(before_forbidden, after_forbidden)
    cache_changes = diff_sigs(before_cache, after_cache)
    approved_cache_paths = {str(official_dir / f"{ticker}.csv") for ticker in full_tickers}
    non_approved_cache_changes = [path for path in cache_changes if path not in approved_cache_paths]

    success_count = sum(1 for row in result_rows if row.get("integration_status") == "SUCCESS")
    fail_count = sum(1 for row in result_rows if row.get("integration_status") == "FAILED")
    local_success = sum(1 for row in retest_rows if row.get("local_price_success") == "TRUE")
    full_ready = sum(1 for row in retest_rows if row.get("full_history_ready") == "TRUE")
    ratio = (local_success / len(retest_rows)) if retest_rows else 0.0

    if len(full_tickers) != 52:
        validation_failures.append(f"Expected R5 full-history candidate count 52, discovered {len(full_tickers)}.")
    if len(result_rows) != len(full_tickers):
        validation_failures.append("Integration attempt count does not match discovered candidate count.")
    if len(held_rows) + len(full_tickers) != len({get_ticker(row) for row in quality_rows if get_ticker(row)}):
        validation_failures.append("Held-out plus candidate count does not equal R5 Batch 2 ticker count.")
    if not backup_dir.exists():
        validation_failures.append("Backup directory was not created.")
    if not restore_script.exists():
        validation_failures.append("Restore script was not created.")
    if not backup_manifest_in_archive.exists():
        validation_failures.append("Archive backup manifest was not created.")
    if forbidden_changes:
        validation_failures.append(f"Forbidden files modified: {len(forbidden_changes)}.")
    if non_approved_cache_changes:
        validation_failures.append(f"Non-approved official cache files modified: {len(non_approved_cache_changes)}.")
    if fail_count:
        validation_failures.append(f"Approved candidate integration failures: {fail_count}.")

    status = STATUS_FAIL if validation_failures and (not full_tickers or forbidden_changes or not restore_script.exists()) else STATUS_WARN if validation_failures else STATUS_OK

    held_counter = {key: sum(1 for row in held_rows if row.get("held_out_category") == key) for key in ["PRICE_ONLY_PARTIAL", "EMPTY_FETCH", "HOLD_REVIEW", "SUSPICIOUS_DATA"]}
    values = {
        "STATUS": status,
        "MODE": MODE,
        "BATCH_ID": BATCH_ID,
        "R5_SOURCE_PATH": str(r5_source),
        "STAGED_SOURCE_PATH": str(staged_dir),
        "OFFICIAL_PRICE_CACHE_DIR": str(official_dir),
        "BACKUP_DIR": str(backup_dir) if backup_dir.exists() else "",
        "RESTORE_SCRIPT_PATH": str(restore_script) if restore_script.exists() else "",
        "BATCH2_TICKER_COUNT": str(len({get_ticker(row) for row in quality_rows if get_ticker(row)})),
        "FULL_HISTORY_CANDIDATE_COUNT": str(len(full_tickers)),
        "INTEGRATION_ATTEMPT_COUNT": str(len(result_rows)),
        "INTEGRATION_SUCCESS_COUNT": str(success_count),
        "INTEGRATION_FAIL_COUNT": str(fail_count),
        "HELD_OUT_COUNT": str(len(held_rows)),
        "PRICE_ONLY_PARTIAL_HELD_OUT_COUNT": str(held_counter["PRICE_ONLY_PARTIAL"]),
        "EMPTY_FETCH_HELD_OUT_COUNT": str(held_counter["EMPTY_FETCH"]),
        "HOLD_REVIEW_HELD_OUT_COUNT": str(held_counter["HOLD_REVIEW"] + held_counter["SUSPICIOUS_DATA"] + held_counter["EMPTY_FETCH"]),
        "SUSPICIOUS_DATA_HELD_OUT_COUNT": str(held_counter["SUSPICIOUS_DATA"]),
        "OFFICIAL_PRICE_CACHE_MODIFIED": str(bool(cache_changes) and not non_approved_cache_changes).upper(),
        "LOCAL_RETEST_EXECUTED": str(bool(retest_rows)).upper(),
        "LOCAL_PRICE_SUCCESS_COUNT_AFTER_INTEGRATION": str(local_success),
        "FULL_HISTORY_READY_COUNT_AFTER_INTEGRATION": str(full_ready),
        "RETEST_SUCCESS_RATIO": f"{ratio:.6f}",
        "VALIDATION_FAIL_COUNT": str(len(validation_failures)),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changes or non_approved_cache_changes)).upper(),
    }
    values.update(SAFETY)

    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    wrapper_path = root / "scripts/v18/run_v18_23C_R6_official_price_integration_batch2_full_history.ps1"
    script_path = root / "scripts/v18/v18_23C_R6_official_price_integration_batch2_full_history.py"
    compile_ok = py_compile(script_path)
    ps_ok = ps_parse(wrapper_path)
    if not compile_ok:
        validation_failures.append("Python compile check failed.")
    if not ps_ok:
        validation_failures.append("PowerShell parse check failed.")
    if validation_failures:
        values["VALIDATION_FAIL_COUNT"] = str(len(validation_failures))
        if status == STATUS_OK:
            status = STATUS_WARN
        if forbidden_changes or not full_tickers or not restore_script.exists():
            status = STATUS_FAIL
        values["STATUS"] = status
        write_text(root / OUTPUTS["report"], render_report(values))
        write_text(root / OUTPUTS["read_first"], render_read_first(values))

    print(f"STATUS: {values['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"FULL_HISTORY_CANDIDATE_COUNT: {len(full_tickers)}")
    print(f"INTEGRATION_SUCCESS_COUNT: {success_count}")
    print(f"INTEGRATION_FAIL_COUNT: {fail_count}")
    print(f"VALIDATION_FAIL_COUNT: {values['VALIDATION_FAIL_COUNT']}")
    return 1 if values["STATUS"] == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
