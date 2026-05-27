from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R27D_DRYRUN_PARTIAL_MATURE_INTEGRATION_PLAN_READY"
STATUS_APPLY_OK = "OK_V18_25A_R27D_PARTIAL_MATURE_PRICE_CACHE_LEDGER_INTEGRATION_READY"
STATUS_APPLY_BLOCKED = "WARN_V18_25A_R27D_APPLY_BLOCKED"
STATUS_POST_REVIEW = "WARN_V18_25A_R27D_POST_APPLY_VALIDATION_REVIEW_NEEDED"
STATUS_FORBIDDEN = "FAIL_V18_25A_R27D_FORBIDDEN_MODIFIED"

MODE_DRYRUN = "DRYRUN_PARTIAL_MATURE_PRICE_CACHE_LEDGER_INTEGRATION_PLAN_ONLY"
MODE_APPLY = "APPLY_PARTIAL_MATURE_PRICE_CACHE_LEDGER_INTEGRATION_WITH_BACKUP"

EXPECTED_TICKERS = {"TLN", "RDDT"}
EXPECTED_R27C_STATUS = "OK_V18_25A_R27C_CONTROLLED_PARTIAL_MATURE_INTEGRATION_DRYRUN_READY"

R27C_READ_FIRST = "outputs/v18/ops/V18_25A_R27C_READ_FIRST.txt"
R27C_PRICE_PLAN = "outputs/v18/coverage_resolution/V18_25A_R27C_CURRENT_PARTIAL_MATURE_PRICE_CACHE_INTEGRATION_DRYRUN_PLAN.csv"
R27C_LEDGER_PLAN = "outputs/v18/coverage_resolution/V18_25A_R27C_CURRENT_PARTIAL_MATURE_ROLLING_LEDGER_DRYRUN_PLAN.csv"
R27C_VALIDATION = "outputs/v18/coverage_resolution/V18_25A_R27C_CURRENT_DRYRUN_VALIDATION.csv"
R27C_SUMMARY = "outputs/v18/coverage_resolution/V18_25A_R27C_CURRENT_SUMMARY.csv"

NORMALIZED_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/normalized"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
BACKUP_ROOT = "archive/v18/partial_mature_integration_backups"

OUT_DIR = "outputs/v18/coverage_resolution"
OUT_APPLY_PLAN = f"{OUT_DIR}/V18_25A_R27D_CURRENT_APPLY_PLAN.csv"
OUT_PRICE_RESULT = f"{OUT_DIR}/V18_25A_R27D_CURRENT_PRICE_CACHE_WRITE_RESULT.csv"
OUT_LEDGER_RESULT = f"{OUT_DIR}/V18_25A_R27D_CURRENT_ROLLING_LEDGER_UPDATE_RESULT.csv"
OUT_POST_VALIDATE = f"{OUT_DIR}/V18_25A_R27D_CURRENT_POST_APPLY_VALIDATION.csv"
OUT_COVERAGE = f"{OUT_DIR}/V18_25A_R27D_CURRENT_COVERAGE_AFTER_APPLY.csv"
OUT_BACKUP_MANIFEST = f"{OUT_DIR}/V18_25A_R27D_CURRENT_BACKUP_MANIFEST.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27D_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27D_CURRENT_PARTIAL_MATURE_INTEGRATION_REPORT.md"

REQUIRED_SOURCE_COLUMNS = {"ticker", "date", "open", "high", "low", "close", "volume"}
PRICE_CACHE_FIELDS = ["date", "open", "high", "low", "close", "adj_close", "volume", "source", "source_file", "updated_at"]

APPLY_PLAN_FIELDS = [
    "ticker",
    "source_normalized_file",
    "target_price_cache_file",
    "planned_action",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "plan_status",
    "blocker",
]
PRICE_RESULT_FIELDS = [
    "ticker",
    "target_price_cache_file",
    "write_attempted",
    "write_success",
    "target_action",
    "rows_written",
    "error_message",
]
LEDGER_RESULT_FIELDS = [
    "ticker",
    "ledger_row_found",
    "ledger_update_attempted",
    "ledger_update_success",
    "previous_last_success_scan_date",
    "new_last_success_scan_date",
    "previous_last_scan_status",
    "new_last_scan_status",
    "error_message",
]
POST_VALIDATE_FIELDS = [
    "ticker",
    "price_cache_exists",
    "price_cache_readable",
    "price_row_count_matches_source",
    "latest_date_matches_source",
    "latest_close_matches_source",
    "latest_volume_matches_source",
    "ledger_success_date_set",
    "post_validate_status",
    "error_message",
]
COVERAGE_FIELDS = ["metric", "value", "expected", "status", "notes"]
BACKUP_FIELDS = ["backup_item", "ticker", "source_path", "backup_path", "backup_status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27C_STATUS",
    "APPLY_REQUESTED",
    "EXPECTED_TICKER_MATCH",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "BACKUP_CREATED",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_CREATED",
    "PRICE_CACHE_WRITE_ATTEMPT_COUNT",
    "PRICE_CACHE_WRITE_SUCCESS_COUNT",
    "PRICE_CACHE_WRITE_FAIL_COUNT",
    "ROLLING_LEDGER_UPDATE_ATTEMPT_COUNT",
    "ROLLING_LEDGER_UPDATE_SUCCESS_COUNT",
    "ROLLING_LEDGER_UPDATE_FAIL_COUNT",
    "POST_VALIDATE_SUCCESS_COUNT",
    "POST_VALIDATE_FAIL_COUNT",
    "TOTAL_LEDGER_ROWS_AFTER",
    "COVERED_WITHIN_5D_AFTER",
    "NEVER_SUCCESS_COUNT_AFTER",
    "STALE_COUNT_AFTER",
    "REMAINING_COUNT_AFTER",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "CANDIDATES_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]


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
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except Exception:
            continue
    return None


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def changed_keys(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    return [key for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)]


def norm_key(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def find_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    by_norm = {norm_key(field): field for field in fields}
    for alias in aliases:
        hit = by_norm.get(norm_key(alias))
        if hit:
            return hit
    return None


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value:
            return value
    return ""


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def source_path(root: Path, ticker: str, row: Dict[str, str]) -> Path:
    text = get_field(row, "source_normalized_file")
    path = Path(text) if text else root / NORMALIZED_DIR / f"{ticker}.csv"
    return path if path.is_absolute() else root / path


def validate_source(path: Path, ticker: str) -> Tuple[bool, Dict[str, object], List[Dict[str, object]], str]:
    rows, fields = read_csv(path)
    field_set = {str(field).strip().lower() for field in fields}
    blockers: List[str] = []
    if not path.exists():
        blockers.append("source_missing")
    if path.exists() and not fields:
        blockers.append("source_unreadable")
    if not REQUIRED_SOURCE_COLUMNS.issubset(field_set):
        blockers.append("required_columns_missing")
    dates: List[dt.date] = []
    seen_dates: set[str] = set()
    duplicate_date_count = 0
    null_close_count = 0
    latest_close = ""
    latest_volume = ""
    for row in rows:
        date_text = str(row.get("date", "") or "").strip()[:10]
        parsed = parse_date(date_text)
        if parsed:
            dates.append(parsed)
        if date_text in seen_dates:
            duplicate_date_count += 1
        else:
            seen_dates.add(date_text)
        if not str(row.get("close", "") or "").strip():
            null_close_count += 1
    if rows:
        latest_row = max(rows, key=lambda item: str(item.get("date", "") or ""))
        latest_close = str(latest_row.get("close", "") or "").strip()
        latest_volume = str(latest_row.get("volume", "") or "").strip()
    date_parse_ok = bool(rows) and len(dates) == len(rows)
    if len(rows) < 500:
        blockers.append("row_count_below_500")
    if not date_parse_ok:
        blockers.append("date_parse_failed")
    if duplicate_date_count != 0:
        blockers.append("duplicate_date_count_nonzero")
    if null_close_count != 0:
        blockers.append("null_close_count_nonzero")
    if not non_null(latest_close):
        blockers.append("latest_close_missing")
    if not non_null(latest_volume):
        blockers.append("latest_volume_missing")
    transformed = transform_price_rows(rows, path)
    meta = {
        "ticker": ticker,
        "source_normalized_file": path.as_posix(),
        "row_count": len(rows),
        "min_date": min(dates).isoformat() if dates else "",
        "max_date": max(dates).isoformat() if dates else "",
        "latest_close": latest_close,
        "latest_volume": latest_volume,
        "file_exists": str(path.exists()).upper(),
        "readable": str(bool(fields)).upper(),
        "required_columns_present": str(REQUIRED_SOURCE_COLUMNS.issubset(field_set)).upper(),
        "date_parse_ok": str(date_parse_ok).upper(),
        "duplicate_date_count": duplicate_date_count,
        "null_close_count": null_close_count,
    }
    return not blockers, meta, transformed, ";".join(blockers)


def transform_price_rows(rows: List[Dict[str, str]], path: Path) -> List[Dict[str, object]]:
    updated_at = dt.datetime.now().replace(microsecond=0).isoformat()
    transformed: List[Dict[str, object]] = []
    for row in sorted(rows, key=lambda item: str(item.get("date", "") or "")):
        transformed.append(
            {
                "date": str(row.get("date", "") or "").strip()[:10],
                "open": row.get("open", ""),
                "high": row.get("high", ""),
                "low": row.get("low", ""),
                "close": row.get("close", ""),
                "adj_close": row.get("adj_close", row.get("close", "")),
                "volume": row.get("volume", ""),
                "source": "V18_25A_R27D_PARTIAL_MATURE_STAGED_INTEGRATION",
                "source_file": path.as_posix(),
                "updated_at": updated_at,
            }
        )
    return transformed


def load_required_inputs(root: Path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[str]]:
    errors: List[str] = []
    for rel in [R27C_PRICE_PLAN, R27C_LEDGER_PLAN, R27C_VALIDATION, R27C_SUMMARY]:
        if not (root / rel).exists():
            errors.append(f"missing input: {rel}")
    plan_rows, plan_fields = read_csv(root / R27C_PRICE_PLAN)
    ledger_rows, ledger_fields = read_csv(root / LEDGER)
    if not plan_fields:
        errors.append("R27C price plan unreadable")
    if not ledger_fields:
        errors.append("rolling ledger unreadable")
    return plan_rows, ledger_rows, errors


def build_plan(root: Path, plan_rows: List[Dict[str, str]], ledger_rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, object]], Dict[str, List[Dict[str, object]]], List[str]]:
    ticker_col = find_col(ledger_rows[0].keys(), ["ticker", "symbol"]) if ledger_rows else None
    ledger_by_ticker = {norm_ticker(row.get(ticker_col)): row for row in ledger_rows} if ticker_col else {}
    plan_out: List[Dict[str, object]] = []
    transformed_by_ticker: Dict[str, List[Dict[str, object]]] = {}
    blockers: List[str] = []
    for row in plan_rows:
        ticker = norm_ticker(get_field(row, "ticker"))
        src = source_path(root, ticker, row)
        target = root / PRICE_CACHE / f"{ticker}.csv"
        valid, meta, transformed, blocker = validate_source(src, ticker)
        ledger_row = ledger_by_ticker.get(ticker)
        if not ledger_row:
            valid = False
            blocker = ";".join([part for part in [blocker, "missing_from_rolling_ledger"] if part])
        action = "WOULD_UPDATE" if target.exists() else "WOULD_CREATE"
        status = "READY_TO_APPLY" if valid else "BLOCKED"
        if blocker:
            blockers.append(f"{ticker}: {blocker}")
        plan_out.append(
            {
                "ticker": ticker,
                "source_normalized_file": src.as_posix(),
                "target_price_cache_file": target.as_posix(),
                "planned_action": action,
                "row_count": meta["row_count"],
                "min_date": meta["min_date"],
                "max_date": meta["max_date"],
                "latest_close": meta["latest_close"],
                "latest_volume": meta["latest_volume"],
                "plan_status": status,
                "blocker": blocker,
            }
        )
        transformed_by_ticker[ticker] = transformed
    return plan_out, transformed_by_ticker, blockers


def create_backup(root: Path, tickers: Sequence[str], run_stamp: str) -> Tuple[Path, List[Dict[str, object]], bool]:
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R27D_{run_stamp}"
    ensure_dir(backup_dir)
    rows: List[Dict[str, object]] = []
    ledger_path = root / LEDGER
    ledger_backup = backup_dir / ledger_path.name
    shutil.copy2(ledger_path, ledger_backup)
    rows.append(
        {
            "backup_item": "ROLLING_LEDGER",
            "ticker": "",
            "source_path": ledger_path.as_posix(),
            "backup_path": ledger_backup.as_posix(),
            "backup_status": "BACKED_UP",
            "notes": "",
        }
    )
    for ticker in sorted(tickers):
        price_path = root / PRICE_CACHE / f"{ticker}.csv"
        backup_path = backup_dir / price_path.name
        if price_path.exists():
            shutil.copy2(price_path, backup_path)
            status = "BACKED_UP_EXISTING_FILE"
            backup_text = backup_path.as_posix()
            notes = ""
        else:
            status = "MISSING_BEFORE_APPLY"
            backup_text = ""
            notes = "Restore removes target file if it was created by R27D."
        rows.append(
            {
                "backup_item": "PRICE_CACHE",
                "ticker": ticker,
                "source_path": price_path.as_posix(),
                "backup_path": backup_text,
                "backup_status": status,
                "notes": notes,
            }
        )
    write_csv(backup_dir / "MANIFEST.csv", rows, BACKUP_FIELDS)
    restore_script = backup_dir / "RESTORE_V18_25A_R27D_PARTIAL_MATURE_INTEGRATION.ps1"
    restore_text = """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$manifestPath = Join-Path $PSScriptRoot "MANIFEST.csv"
$manifest = Import-Csv $manifestPath
foreach ($row in $manifest) {
    if ($row.backup_item -eq "ROLLING_LEDGER") {
        Copy-Item -Path $row.backup_path -Destination $row.source_path -Force
        Write-Host "Restored rolling ledger: $($row.source_path)"
    } elseif ($row.backup_item -eq "PRICE_CACHE") {
        if ($row.backup_status -eq "BACKED_UP_EXISTING_FILE") {
            Copy-Item -Path $row.backup_path -Destination $row.source_path -Force
            Write-Host "Restored price cache: $($row.source_path)"
        } elseif ($row.backup_status -eq "MISSING_BEFORE_APPLY") {
            if (Test-Path $row.source_path) {
                Remove-Item -Path $row.source_path -Force
                Write-Host "Removed R27D-created price cache: $($row.source_path)"
            }
        }
    }
}
"""
    write_text(restore_script, restore_text)
    write_text(backup_dir / "README_V18_25A_R27D_RESTORE.txt", "Run RESTORE_V18_25A_R27D_PARTIAL_MATURE_INTEGRATION.ps1 to restore the rolling ledger and affected price cache files to their pre-apply state.\n")
    return backup_dir, rows, restore_script.exists()


def update_ledger(root: Path, tickers: Sequence[str], now: dt.datetime, run_id: str) -> Tuple[List[Dict[str, object]], bool]:
    path = root / LEDGER
    rows, fields = read_csv(path)
    ticker_col = find_col(fields, ["ticker", "symbol"])
    if not ticker_col:
        return [], False
    row_by_ticker = {norm_ticker(row.get(ticker_col)): row for row in rows}
    status_col = find_col(fields, ["last_scan_status", "scan_status", "status"])
    run_col = find_col(fields, ["last_scan_run_id", "scan_run_id", "run_id"])
    success_date_cols = [field for field in fields if norm_key(field) in {"lastsuccessscandate", "lastsuccessdate", "latestsuccessdate"}]
    success_ts_cols = [field for field in fields if norm_key(field) in {"lastsuccessscantimestamp", "lastsuccesstimestamp", "latestsuccesstimestamp"}]
    attempt_ts_col = find_col(fields, ["last_attempt_scan_timestamp", "last_attempt_timestamp"])
    attempt_date_col = find_col(fields, ["last_attempt_scan_date", "last_attempt_date"])
    source_col = find_col(fields, ["last_scan_source", "scan_source"])
    mode_col = find_col(fields, ["last_scan_mode", "scan_mode"])
    note_col = find_col(fields, ["last_scan_note", "scan_note"])
    local_col = find_col(fields, ["local_price_available"])
    full_history_col = find_col(fields, ["full_history_ready"])
    success_count_col = find_col(fields, ["success_scan_count"])
    attempt_count_col = find_col(fields, ["attempt_scan_count"])
    result_rows: List[Dict[str, object]] = []
    for ticker in sorted(tickers):
        row = row_by_ticker.get(ticker)
        prev_date = row.get(success_date_cols[0], "") if row and success_date_cols else ""
        prev_status = row.get(status_col, "") if row and status_col else ""
        result = {
            "ticker": ticker,
            "ledger_row_found": str(bool(row)).upper(),
            "ledger_update_attempted": str(bool(row)).upper(),
            "ledger_update_success": "FALSE",
            "previous_last_success_scan_date": prev_date,
            "new_last_success_scan_date": prev_date,
            "previous_last_scan_status": prev_status,
            "new_last_scan_status": prev_status,
            "error_message": "",
        }
        if not row:
            result["error_message"] = "Missing ledger row."
            result_rows.append(result)
            continue
        for col in success_date_cols:
            row[col] = now.date().isoformat()
        for col in success_ts_cols:
            row[col] = now.replace(microsecond=0).isoformat()
        if status_col:
            row[status_col] = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        if run_col:
            row[run_col] = run_id
        if attempt_ts_col:
            row[attempt_ts_col] = now.replace(microsecond=0).isoformat()
        if attempt_date_col:
            row[attempt_date_col] = now.date().isoformat()
        if source_col:
            row[source_col] = "V18_25A_R27D_PARTIAL_MATURE_INTEGRATION"
        if mode_col:
            row[mode_col] = MODE_APPLY
        if note_col:
            row[note_col] = "R27D partial-mature staged price cache integration applied; no external fetch."
        if local_col:
            row[local_col] = "TRUE"
        if full_history_col:
            row[full_history_col] = "TRUE"
        if success_count_col:
            row[success_count_col] = str(to_int(row.get(success_count_col)) + 1)
        if attempt_count_col:
            row[attempt_count_col] = str(to_int(row.get(attempt_count_col)) + 1)
        result["ledger_update_success"] = "TRUE"
        result["new_last_success_scan_date"] = now.date().isoformat()
        result["new_last_scan_status"] = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        result_rows.append(result)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return result_rows, True


def validate_price_cache(root: Path, ticker: str, source_meta: Dict[str, object]) -> Dict[str, object]:
    path = root / PRICE_CACHE / f"{ticker}.csv"
    rows, fields = read_csv(path)
    readable = bool(fields)
    latest = max(rows, key=lambda row: str(row.get("date", "") or "")) if rows else {}
    latest_date = str(latest.get("date", "") or "")
    latest_close = str(latest.get("close", "") or "")
    latest_volume = str(latest.get("volume", "") or "")
    errors: List[str] = []
    if not path.exists():
        errors.append("price_cache_missing")
    if not readable:
        errors.append("price_cache_unreadable")
    if len(rows) != int(source_meta["row_count"]):
        errors.append("row_count_mismatch")
    if latest_date != str(source_meta["max_date"]):
        errors.append("latest_date_mismatch")
    if latest_close != str(source_meta["latest_close"]):
        errors.append("latest_close_mismatch")
    if latest_volume != str(source_meta["latest_volume"]):
        errors.append("latest_volume_mismatch")
    return {
        "ticker": ticker,
        "price_cache_exists": str(path.exists()).upper(),
        "price_cache_readable": str(readable).upper(),
        "price_row_count_matches_source": str(len(rows) == int(source_meta["row_count"])).upper(),
        "latest_date_matches_source": str(latest_date == str(source_meta["max_date"])).upper(),
        "latest_close_matches_source": str(latest_close == str(source_meta["latest_close"])).upper(),
        "latest_volume_matches_source": str(latest_volume == str(source_meta["latest_volume"])).upper(),
        "ledger_success_date_set": "FALSE",
        "post_validate_status": "PASS" if not errors else "FAIL",
        "error_message": ";".join(errors),
    }


def ledger_health(root: Path, today: dt.date) -> Tuple[Dict[str, int], List[str], Dict[str, Dict[str, str]]]:
    rows, fields = read_csv(root / LEDGER)
    ticker_col = find_col(fields, ["ticker", "symbol"])
    success_col = find_col(fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    success_count_col = find_col(fields, ["success_scan_count"])
    seen: set[str] = set()
    duplicate_tickers: List[str] = []
    by_ticker: Dict[str, Dict[str, str]] = {}
    covered = never = stale = artifact = 0
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col, "")) if ticker_col else ""
        if ticker == "TICKERS":
            artifact += 1
        if ticker in seen:
            duplicate_tickers.append(ticker)
        seen.add(ticker)
        by_ticker[ticker] = row
        success_date = parse_date(row.get(success_col, "")) if success_col else None
        success_count = to_int(row.get(success_count_col, "")) if success_count_col else (1 if success_date else 0)
        if success_count <= 0 or success_date is None:
            never += 1
        elif 0 <= (today - success_date).days <= 5:
            covered += 1
        else:
            stale += 1
    counts = {
        "total": len(rows),
        "covered": covered,
        "never": never,
        "stale": stale,
        "remaining": never + stale,
        "artifact": artifact,
        "duplicates": len(duplicate_tickers),
    }
    return counts, duplicate_tickers, by_ticker


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], blockers: Sequence[str]) -> str:
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- None."
    return "\n".join(
        [
            "# V18.25A-R27D Partial-Mature Price Cache + Ledger Integration",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- APPLY_REQUESTED: {values['APPLY_REQUESTED']}",
            f"- TARGET_TICKERS: {values['TARGET_TICKERS']}",
            "",
            "## Results",
            "",
            f"- PRICE_CACHE_WRITE_SUCCESS_COUNT: {values['PRICE_CACHE_WRITE_SUCCESS_COUNT']}",
            f"- ROLLING_LEDGER_UPDATE_SUCCESS_COUNT: {values['ROLLING_LEDGER_UPDATE_SUCCESS_COUNT']}",
            f"- POST_VALIDATE_SUCCESS_COUNT: {values['POST_VALIDATE_SUCCESS_COUNT']}",
            f"- COVERED_WITHIN_5D_AFTER: {values['COVERED_WITHIN_5D_AFTER']}",
            f"- NEVER_SUCCESS_COUNT_AFTER: {values['NEVER_SUCCESS_COUNT_AFTER']}",
            f"- REMAINING_COUNT_AFTER: {values['REMAINING_COUNT_AFTER']}",
            "",
            "## Backup",
            "",
            f"- BACKUP_CREATED: {values['BACKUP_CREATED']}",
            f"- BACKUP_DIR: {values['BACKUP_DIR']}",
            f"- RESTORE_SCRIPT_CREATED: {values['RESTORE_SCRIPT_CREATED']}",
            "",
            "## Blockers",
            "",
            blocker_text,
            "",
            "## Guardrails",
            "",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def coverage_row(metric: str, value: object, expected: object, notes: str = "") -> Dict[str, object]:
    return {"metric": metric, "value": value, "expected": expected, "status": "OK" if str(value) == str(expected) else "WARN", "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R27D_{run_stamp}"
    now = dt.datetime.now().replace(microsecond=0)
    mode = MODE_APPLY if args.apply else MODE_DRYRUN

    price_before = tree_sig(root / PRICE_CACHE)
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")
    tiers_before = tree_sig(root / "outputs" / "v18" / "tiers")
    official_before = tree_sig(root / "outputs" / "v18" / "official_decisions")

    r27c_status = read_first_value(root / R27C_READ_FIRST, "STATUS")
    r27d_recommended = read_first_value(root / R27C_READ_FIRST, "R27D_APPLY_RECOMMENDED")
    dryrun_pass = to_int(read_first_value(root / R27C_READ_FIRST, "DRYRUN_PASS_COUNT"))
    dryrun_blocked = to_int(read_first_value(root / R27C_READ_FIRST, "DRYRUN_BLOCKED_COUNT"))
    plan_rows, ledger_rows, input_errors = load_required_inputs(root)
    target_tickers = sorted({norm_ticker(get_field(row, "ticker")) for row in plan_rows if norm_ticker(get_field(row, "ticker"))})
    expected_match = set(target_tickers) == EXPECTED_TICKERS and len(target_tickers) == 2
    pre_counts, _, ledger_by_ticker = ledger_health(root, now.date())

    blockers: List[str] = []
    if input_errors:
        blockers.extend(input_errors)
    if r27c_status != EXPECTED_R27C_STATUS:
        blockers.append(f"R27C status is {r27c_status or 'MISSING'}")
    if r27d_recommended != "TRUE":
        blockers.append("R27C did not recommend R27D apply")
    if dryrun_pass != 2 or dryrun_blocked != 0:
        blockers.append(f"R27C dry-run counts invalid pass={dryrun_pass} blocked={dryrun_blocked}")
    if not expected_match:
        blockers.append(f"target tickers are {','.join(target_tickers)} not RDDT,TLN")
    if pre_counts["artifact"] != 0:
        blockers.append("rolling ledger contains TICKERS artifact")
    for ticker in EXPECTED_TICKERS:
        if ticker not in ledger_by_ticker:
            blockers.append(f"{ticker} missing from rolling ledger")

    apply_plan, transformed_by_ticker, plan_blockers = build_plan(root, plan_rows, ledger_rows)
    blockers.extend(plan_blockers)
    write_csv(root / OUT_APPLY_PLAN, apply_plan, APPLY_PLAN_FIELDS)

    backup_dir = Path("")
    backup_rows: List[Dict[str, object]] = []
    restore_created = False
    backup_created = False
    price_results: List[Dict[str, object]] = []
    ledger_results: List[Dict[str, object]] = []
    post_rows: List[Dict[str, object]] = []

    if args.apply and blockers:
        status = STATUS_APPLY_BLOCKED
    elif args.apply:
        try:
            backup_dir, backup_rows, restore_created = create_backup(root, target_tickers, run_stamp)
            backup_created = True
        except Exception as exc:
            blockers.append(f"backup_creation_failed: {type(exc).__name__}: {exc}")
            status = STATUS_APPLY_BLOCKED
        else:
            ensure_dir(root / PRICE_CACHE)
            for row in apply_plan:
                ticker = str(row["ticker"])
                target = root / PRICE_CACHE / f"{ticker}.csv"
                try:
                    write_csv(target, transformed_by_ticker[ticker], PRICE_CACHE_FIELDS)
                    price_results.append(
                        {
                            "ticker": ticker,
                            "target_price_cache_file": target.as_posix(),
                            "write_attempted": "TRUE",
                            "write_success": "TRUE",
                            "target_action": "UPDATE_EXISTING_FILE" if any(b["ticker"] == ticker and b["backup_status"] == "BACKED_UP_EXISTING_FILE" for b in backup_rows) else "CREATE_NEW_FILE",
                            "rows_written": len(transformed_by_ticker[ticker]),
                            "error_message": "",
                        }
                    )
                except Exception as exc:
                    price_results.append(
                        {
                            "ticker": ticker,
                            "target_price_cache_file": target.as_posix(),
                            "write_attempted": "TRUE",
                            "write_success": "FALSE",
                            "target_action": "WRITE_FAILED",
                            "rows_written": 0,
                            "error_message": f"{type(exc).__name__}: {exc}",
                        }
                    )
            if all(row["write_success"] == "TRUE" for row in price_results):
                ledger_results, _ = update_ledger(root, target_tickers, now, run_id)
            else:
                blockers.append("price cache write failure prevented ledger update")
            status = STATUS_APPLY_OK
    else:
        status = STATUS_DRYRUN

    if not args.apply:
        for row in apply_plan:
            price_results.append(
                {
                    "ticker": row["ticker"],
                    "target_price_cache_file": row["target_price_cache_file"],
                    "write_attempted": "FALSE",
                    "write_success": "FALSE",
                    "target_action": "DRYRUN_NO_WRITE",
                    "rows_written": row["row_count"],
                    "error_message": row["blocker"],
                }
            )
        for row in apply_plan:
            ledger_results.append(
                {
                    "ticker": row["ticker"],
                    "ledger_row_found": str(row["ticker"] in ledger_by_ticker).upper(),
                    "ledger_update_attempted": "FALSE",
                    "ledger_update_success": "FALSE",
                    "previous_last_success_scan_date": get_field(ledger_by_ticker.get(str(row["ticker"]), {}), "last_success_scan_date"),
                    "new_last_success_scan_date": "",
                    "previous_last_scan_status": get_field(ledger_by_ticker.get(str(row["ticker"]), {}), "last_scan_status"),
                    "new_last_scan_status": "",
                    "error_message": row["blocker"],
                }
            )

    source_meta_by_ticker = {str(row["ticker"]): row for row in apply_plan}
    if args.apply and status != STATUS_APPLY_BLOCKED:
        post_counts, duplicate_tickers, post_ledger_by_ticker = ledger_health(root, now.date())
        for ticker in target_tickers:
            post = validate_price_cache(root, ticker, source_meta_by_ticker[ticker])
            ledger_row = post_ledger_by_ticker.get(ticker, {})
            ledger_success_set = get_field(ledger_row, "last_success_scan_date") == now.date().isoformat()
            post["ledger_success_date_set"] = str(ledger_success_set).upper()
            if not ledger_success_set:
                post["post_validate_status"] = "FAIL"
                post["error_message"] = ";".join([part for part in [str(post["error_message"]), "ledger_success_date_not_set"] if part])
            post_rows.append(post)
        if post_counts["total"] != 323 or post_counts["artifact"] != 0 or post_counts["duplicates"] != 0:
            blockers.append("post-apply ledger row/artifact/duplicate validation issue")
        if any(row["post_validate_status"] != "PASS" for row in post_rows):
            status = STATUS_POST_REVIEW
    else:
        post_counts, duplicate_tickers, _ = ledger_health(root, now.date())
        for row in apply_plan:
            post_rows.append(
                {
                    "ticker": row["ticker"],
                    "price_cache_exists": str((root / PRICE_CACHE / f"{row['ticker']}.csv").exists()).upper(),
                    "price_cache_readable": "FALSE",
                    "price_row_count_matches_source": "FALSE",
                    "latest_date_matches_source": "FALSE",
                    "latest_close_matches_source": "FALSE",
                    "latest_volume_matches_source": "FALSE",
                    "ledger_success_date_set": "FALSE",
                    "post_validate_status": "NOT_RUN",
                    "error_message": "dry-run or apply blocked",
                }
            )

    write_csv(root / OUT_PRICE_RESULT, price_results, PRICE_RESULT_FIELDS)
    write_csv(root / OUT_LEDGER_RESULT, ledger_results, LEDGER_RESULT_FIELDS)
    write_csv(root / OUT_POST_VALIDATE, post_rows, POST_VALIDATE_FIELDS)
    write_csv(root / OUT_BACKUP_MANIFEST, backup_rows, BACKUP_FIELDS)

    coverage_rows = [
        coverage_row("TOTAL_LEDGER_ROWS_AFTER", post_counts["total"], 323),
        coverage_row("COVERED_WITHIN_5D_AFTER", post_counts["covered"], 303 if args.apply and status != STATUS_APPLY_BLOCKED else 301),
        coverage_row("NEVER_SUCCESS_COUNT_AFTER", post_counts["never"], 20 if args.apply and status != STATUS_APPLY_BLOCKED else 22),
        coverage_row("STALE_COUNT_AFTER", post_counts["stale"], 0),
        coverage_row("REMAINING_COUNT_AFTER", post_counts["remaining"], 20 if args.apply and status != STATUS_APPLY_BLOCKED else 22),
        coverage_row("ARTIFACT_TICKERS_PRESENT_COUNT_AFTER", post_counts["artifact"], 0),
        coverage_row("DUPLICATE_LEDGER_TICKER_COUNT_AFTER", post_counts["duplicates"], 0, ",".join(duplicate_tickers)),
    ]
    write_csv(root / OUT_COVERAGE, coverage_rows, COVERAGE_FIELDS)
    if args.apply and status == STATUS_APPLY_OK and any(row["status"] == "WARN" for row in coverage_rows):
        status = STATUS_POST_REVIEW

    price_after = tree_sig(root / PRICE_CACHE)
    ledger_after = file_sig(root / LEDGER)
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    candidates_modified = tree_sig(root / "outputs" / "v18" / "candidates") != candidates_before
    tiers_modified = tree_sig(root / "outputs" / "v18" / "tiers") != tiers_before
    official_modified = tree_sig(root / "outputs" / "v18" / "official_decisions") != official_before
    price_changed = changed_keys(price_before, price_after)
    price_modified = bool(price_changed)
    ledger_modified = ledger_after != ledger_before
    allowed_price_changes = {"TLN.csv", "RDDT.csv"} if args.apply else set()
    forbidden_price_changes = [key for key in price_changed if key not in allowed_price_changes]
    forbidden_modified = bool(forbidden_price_changes or factor_modified or tech_modified or candidates_modified or tiers_modified or official_modified)
    if not args.apply:
        forbidden_modified = forbidden_modified or ledger_modified or price_modified
    if forbidden_modified:
        status = STATUS_FORBIDDEN

    price_attempts = sum(1 for row in price_results if row["write_attempted"] == "TRUE")
    price_success = sum(1 for row in price_results if row["write_success"] == "TRUE")
    ledger_attempts = sum(1 for row in ledger_results if row["ledger_update_attempted"] == "TRUE")
    ledger_success = sum(1 for row in ledger_results if row["ledger_update_success"] == "TRUE")
    post_success = sum(1 for row in post_rows if row["post_validate_status"] == "PASS")
    post_fail = sum(1 for row in post_rows if row["post_validate_status"] == "FAIL")
    validation_fail_count = 1 if status in {STATUS_APPLY_BLOCKED, STATUS_POST_REVIEW, STATUS_FORBIDDEN} else 0

    values = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "R27C_STATUS": r27c_status or "MISSING",
        "APPLY_REQUESTED": str(args.apply).upper(),
        "EXPECTED_TICKER_MATCH": str(expected_match).upper(),
        "TARGET_TICKER_COUNT": len(target_tickers),
        "TARGET_TICKERS": ",".join(target_tickers),
        "BACKUP_CREATED": str(backup_created).upper(),
        "BACKUP_DIR": backup_dir.as_posix() if backup_created else "",
        "RESTORE_SCRIPT_CREATED": str(restore_created).upper(),
        "PRICE_CACHE_WRITE_ATTEMPT_COUNT": price_attempts,
        "PRICE_CACHE_WRITE_SUCCESS_COUNT": price_success,
        "PRICE_CACHE_WRITE_FAIL_COUNT": price_attempts - price_success,
        "ROLLING_LEDGER_UPDATE_ATTEMPT_COUNT": ledger_attempts,
        "ROLLING_LEDGER_UPDATE_SUCCESS_COUNT": ledger_success,
        "ROLLING_LEDGER_UPDATE_FAIL_COUNT": ledger_attempts - ledger_success,
        "POST_VALIDATE_SUCCESS_COUNT": post_success,
        "POST_VALIDATE_FAIL_COUNT": post_fail,
        "TOTAL_LEDGER_ROWS_AFTER": post_counts["total"],
        "COVERED_WITHIN_5D_AFTER": post_counts["covered"],
        "NEVER_SUCCESS_COUNT_AFTER": post_counts["never"],
        "STALE_COUNT_AFTER": post_counts["stale"],
        "REMAINING_COUNT_AFTER": post_counts["remaining"],
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "CANDIDATES_MODIFIED": str(candidates_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R27E: post-integration downstream readiness audit for TLN/RDDT only; keep auto trade and auto sell disabled.",
    }
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, blockers))
    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FORBIDDEN else 0


if __name__ == "__main__":
    raise SystemExit(main())
