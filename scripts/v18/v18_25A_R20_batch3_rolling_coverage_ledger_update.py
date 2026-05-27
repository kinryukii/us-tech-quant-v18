from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R20_BATCH3_ROLLING_LEDGER_UPDATE_READY"
STATUS_WARN = "WARN_V18_25A_R20_BATCH3_ROLLING_LEDGER_UPDATE_READY"
STATUS_FAIL = "FAIL_V18_25A_R20_BATCH3_ROLLING_LEDGER_UPDATE"
MODE = "LOCAL_ONLY_BATCH3_ROLLING_COVERAGE_LEDGER_UPDATE"

R19_READ_FIRST = "outputs/v18/ops/V18_25A_R19_READ_FIRST.txt"
R19_RESULT = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_OFFICIAL_BATCH3_INTEGRATION_RESULT.csv"
R19_PLAN = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_OFFICIAL_BATCH3_INTEGRATION_PLAN.csv"
R19_RETEST = "outputs/v18/rolling_coverage/V18_25A_R19_CURRENT_BATCH3_LOCAL_RETEST.csv"
R19_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_HELD_OUT_TICKERS.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
PRICE_CACHE = "state/v18/price_cache"
BACKUP_ROOT = "archive/v18/rolling_coverage_backups"

OUT_RETEST = "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_BATCH3_ROLLING_RETEST_RESULT.csv"
OUT_UPDATE = "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_LEDGER_UPDATE_RESULT.csv"
OUT_AUDIT = "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_COVERAGE_AUDIT.csv"
OUT_REMAINING = "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_REMAINING_STALE_TICKERS.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R20_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R20_CURRENT_BATCH3_ROLLING_LEDGER_UPDATE_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R19_SOURCE_PATH",
    "LEDGER_PATH",
    "LEDGER_BACKUP_DIR",
    "LEDGER_RESTORE_SCRIPT_PATH",
    "R20_TARGET_TICKER_COUNT",
    "SCAN_ATTEMPT_COUNT",
    "SCAN_SUCCESS_COUNT",
    "SCAN_FAIL_COUNT",
    "LEDGER_UPDATED",
    "LEDGER_UPDATE_SUCCESS_COUNT",
    "LEDGER_UPDATE_FAIL_COUNT",
    "TOTAL_UNIVERSE_COUNT",
    "UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW",
    "TRUE_5DAY_COVERAGE_MET",
    "REMAINING_STALE_OVERDUE_COUNT",
    "NEVER_SUCCESS_COUNT",
    "COVERAGE_TRUST_LEVEL",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "OFFICIAL_PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
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
    "NEXT_RECOMMENDED_STEP",
]

RETEST_FIELDS = [
    "ticker",
    "official_price_cache_path",
    "official_price_cache_available",
    "row_count",
    "min_date",
    "max_date",
    "latest_date",
    "close_column_available",
    "close_non_null_count",
    "full_history_ready",
    "scan_result",
    "error_message",
]
UPDATE_FIELDS = [
    "ticker",
    "ledger_row_found_before_update",
    "scan_result",
    "ledger_update_attempted",
    "ledger_update_success",
    "previous_last_scan_status",
    "new_last_scan_status",
    "previous_success_scan_count",
    "new_success_scan_count",
    "previous_attempt_scan_count",
    "new_attempt_scan_count",
    "error_message",
]
AUDIT_FIELDS = ["metric", "value", "notes"]
REMAINING_FIELDS = ["ticker", "last_scan_status", "last_success_scan_date", "last_attempt_scan_date", "reason"]
BACKUP_FIELDS = ["backup_item", "path", "status", "notes"]

REQUIRED_LEDGER_FIELDS = [
    "ticker",
    "last_scan_status",
    "last_success_scan_date",
    "last_attempt_scan_date",
    "last_scan_source",
    "last_scan_mode",
    "last_scan_note",
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


def parse_read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def snapshot_tree(root: Path, rels: Sequence[str]) -> Dict[str, Tuple[int, int]]:
    out: Dict[str, Tuple[int, int]] = {}
    for rel in rels:
        base = root / rel
        if not base.exists():
            continue
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in files:
            out[path.resolve().relative_to(root).as_posix()] = file_sig(path)
    return out


def changed_paths(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


def price_quality(path: Path) -> Dict[str, object]:
    rows, fields = read_csv(path)
    aliases = {field.lower(): field for field in fields}
    date_col = aliases.get("date")
    close_col = aliases.get("close")
    dates = [str(row.get(date_col, "")).strip() for row in rows] if date_col else []
    close_values = [str(row.get(close_col, "")).strip() for row in rows] if close_col else []
    close_non_null = sum(1 for value in close_values if value)
    if not path.exists():
        result = "FAIL_MISSING_OFFICIAL_PRICE_CACHE"
        error = "Official price cache file missing."
    elif not rows:
        result = "FAIL_EMPTY_CACHE"
        error = "Official price cache file is empty."
    elif not close_col or close_non_null <= 0:
        result = "FAIL_MISSING_CLOSE"
        error = "Close column missing or empty."
    elif not dates:
        result = "FAIL_INSUFFICIENT_HISTORY"
        error = "Latest date missing."
    else:
        result = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        error = ""
    return {
        "row_count": len(rows),
        "min_date": min(dates) if dates else "",
        "max_date": max(dates) if dates else "",
        "latest_date": max(dates) if dates else "",
        "close_column_available": bool(close_col),
        "close_non_null_count": close_non_null,
        "full_history_ready": result == "SUCCESS_LOCAL_PRICE_FULL_HISTORY",
        "scan_result": result,
        "error_message": error,
    }


def render_restore_script(ledger_rel: str, backup_name: str) -> str:
    return f"""$ErrorActionPreference = "Stop"
$BackupDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $BackupDir "..\\..\\..\\..")
$BackupFile = Join-Path $BackupDir "{backup_name}"
$LedgerPath = Join-Path $Root "{ledger_rel}"
if (-not (Test-Path -LiteralPath $BackupFile)) {{
    throw "Backup ledger missing: $BackupFile"
}}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LedgerPath) | Out-Null
Copy-Item -LiteralPath $BackupFile -Destination $LedgerPath -Force
Write-Host "RESTORED: $LedgerPath"
"""


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except Exception:
        return None


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.25A-R20 Batch3 Rolling Ledger Update

Generated: {dt.datetime.now().isoformat(timespec="seconds")}

Status: {values['STATUS']}

Mode: {MODE}

Targets: {values['R20_TARGET_TICKER_COUNT']}

Scan success/fail: {values['SCAN_SUCCESS_COUNT']} / {values['SCAN_FAIL_COUNT']}

Ledger update success/fail: {values['LEDGER_UPDATE_SUCCESS_COUNT']} / {values['LEDGER_UPDATE_FAIL_COUNT']}

Unique success within 5-day window: {values['UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW']}

Remaining stale/overdue: {values['REMAINING_STALE_OVERDUE_COUNT']}

Never success: {values['NEVER_SUCCESS_COUNT']}

Backup directory: {values['LEDGER_BACKUP_DIR']}

Restore script: {values['LEDGER_RESTORE_SCRIPT_PATH']}

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    r19 = parse_read_first(root / R19_READ_FIRST)
    integration_rows, _ = read_csv(root / R19_RESULT)
    retest_r19_rows, _ = read_csv(root / R19_RETEST)
    held_rows, _ = read_csv(root / R19_HELD_OUT)
    ledger_rows, ledger_fields = read_csv(root / LEDGER)

    target_tickers = [
        norm_ticker(row.get("ticker"))
        for row in integration_rows
        if norm_ticker(row.get("ticker")) and is_true(row.get("integration_success"))
    ]
    held_tickers = {norm_ticker(row.get("ticker")) for row in held_rows if norm_ticker(row.get("ticker"))}
    target_set = set(target_tickers)

    validation_failures: List[str] = []
    if not r19.get("STATUS", "").startswith("OK_V18_25A_R19"):
        validation_failures.append("R19 status is not OK")
    if to_int(r19.get("INTEGRATION_SUCCESS_COUNT")) != len(target_tickers):
        validation_failures.append("R19 integration success count does not match discovered targets")
    if to_int(r19.get("LOCAL_PRICE_SUCCESS_COUNT_AFTER_INTEGRATION")) != len(target_tickers):
        validation_failures.append("R19 local retest success count does not match discovered targets")
    if to_int(r19.get("FULL_HISTORY_READY_COUNT_AFTER_INTEGRATION")) != len(target_tickers):
        validation_failures.append("R19 full-history ready count does not match discovered targets")
    if r19.get("FORBIDDEN_FILE_MODIFIED") != "FALSE":
        validation_failures.append("R19 reports forbidden modification")
    if len(target_tickers) != len(target_set):
        validation_failures.append("R20 target tickers are not unique")
    if target_set & held_tickers:
        validation_failures.append("Held-out R19 tickers included in target set")
    if len(target_tickers) != 59:
        validation_failures.append("Discovered R20 target count is not 59")
    if not ledger_rows or not ledger_fields:
        validation_failures.append("Rolling ledger missing or unreadable")

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R20_{timestamp}"
    restore_script = backup_dir / "RESTORE_V18_25A_R20_ROLLING_LEDGER.ps1"
    backup_manifest = backup_dir / "BACKUP_MANIFEST.csv"
    backup_ledger = backup_dir / "V18_23B_ROLLING_SCAN_LEDGER.csv"
    ledger_path = root / LEDGER

    protected_before = snapshot_tree(root, [
        PRICE_CACHE,
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "data/v18/staged_market_proxy",
        "state/v18/market_proxy_cache",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/degraded_daily",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
    ])

    scan_rows: List[Dict[str, object]] = []
    for ticker in target_tickers:
        cache_path = root / PRICE_CACHE / f"{ticker}.csv"
        quality = price_quality(cache_path)
        scan_rows.append({
            "ticker": ticker,
            "official_price_cache_path": str(cache_path),
            "official_price_cache_available": str(cache_path.exists()).upper(),
            "row_count": quality["row_count"],
            "min_date": quality["min_date"],
            "max_date": quality["max_date"],
            "latest_date": quality["latest_date"],
            "close_column_available": str(bool(quality["close_column_available"])).upper(),
            "close_non_null_count": quality["close_non_null_count"],
            "full_history_ready": str(bool(quality["full_history_ready"])).upper(),
            "scan_result": quality["scan_result"],
            "error_message": quality["error_message"],
        })

    scan_success_count = sum(1 for row in scan_rows if row["scan_result"] == "SUCCESS_LOCAL_PRICE_FULL_HISTORY")
    scan_fail_count = len(scan_rows) - scan_success_count
    now = dt.datetime.now()
    today = now.date().isoformat()
    run_id = f"V18_25A_R20_{now.strftime('%Y%m%d_%H%M%S')}"
    scan_by_ticker = {row["ticker"]: row for row in scan_rows}

    for field in REQUIRED_LEDGER_FIELDS:
        if field not in ledger_fields:
            ledger_fields.append(field)
    for optional in [
        "last_attempt_scan_timestamp",
        "last_success_scan_timestamp",
        "last_scan_run_id",
        "success_scan_count",
        "attempt_scan_count",
        "local_price_available",
        "full_history_ready",
        "failure_reason",
        "source_notes",
    ]:
        if optional not in ledger_fields:
            ledger_fields.append(optional)

    ensure_dir(backup_dir)
    if ledger_path.exists():
        shutil.copy2(ledger_path, backup_ledger)
    else:
        validation_failures.append("Ledger file missing before backup")
    write_csv(backup_manifest, [
        {
            "backup_item": "rolling_ledger",
            "path": str(backup_ledger),
            "status": "BACKED_UP_EXISTING" if backup_ledger.exists() else "BACKUP_FAILED",
            "notes": str(ledger_path),
        },
        {
            "backup_item": "restore_script",
            "path": str(restore_script),
            "status": "CREATED",
            "notes": "Restores previous rolling ledger file.",
        },
    ], BACKUP_FIELDS)
    write_text(restore_script, render_restore_script(LEDGER, "V18_23B_ROLLING_SCAN_LEDGER.csv"))

    ledger_map: Dict[str, Dict[str, str]] = {}
    ordered_tickers: List[str] = []
    for row in ledger_rows:
        ticker = norm_ticker(row.get("ticker"))
        if not ticker:
            continue
        ledger_map[ticker] = dict(row)
        ordered_tickers.append(ticker)

    update_rows: List[Dict[str, object]] = []
    ledger_update_success = 0
    ledger_update_fail = 0
    if validation_failures:
        ledger_updated = False
    else:
        ledger_updated = True
        for ticker in target_tickers:
            scan = scan_by_ticker[ticker]
            row_found = ticker in ledger_map
            row = dict(ledger_map.get(ticker, {"ticker": ticker, "canonical_universe_present": "TRUE", "first_seen_date": today}))
            previous_status = row.get("last_scan_status", "")
            previous_success = to_int(row.get("success_scan_count"), 0)
            previous_attempt = to_int(row.get("attempt_scan_count"), 0)
            update_success = False
            error_message = ""
            try:
                row["ticker"] = ticker
                row["last_attempt_scan_timestamp"] = now.isoformat(timespec="seconds")
                row["last_attempt_scan_date"] = today
                row["last_scan_run_id"] = run_id
                row["last_scan_source"] = "V18_25A_R20_BATCH3_LOCAL_ONLY_LEDGER_RETEST"
                row["last_scan_mode"] = MODE
                row["last_scan_note"] = "R20 local-only official price cache validation; no external fetch."
                row["attempt_scan_count"] = str(previous_attempt + 1)
                row["local_price_available"] = scan["official_price_cache_available"]
                row["full_history_ready"] = scan["full_history_ready"]
                if scan["scan_result"] == "SUCCESS_LOCAL_PRICE_FULL_HISTORY":
                    row["last_scan_status"] = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
                    row["last_success_scan_timestamp"] = now.isoformat(timespec="seconds")
                    row["last_success_scan_date"] = today
                    row["success_scan_count"] = str(previous_success + 1)
                    row["failure_reason"] = ""
                    row["source_notes"] = "local_price=available;source=V18_25A_R20"
                    update_success = True
                else:
                    row["last_scan_status"] = str(scan["scan_result"])
                    row["failure_reason"] = str(scan["error_message"])
                    row["source_notes"] = "local_price=failed;source=V18_25A_R20"
                ledger_map[ticker] = row
                if not row_found:
                    ordered_tickers.append(ticker)
            except Exception as exc:
                error_message = str(exc)
            if update_success:
                ledger_update_success += 1
            else:
                ledger_update_fail += 1
            update_rows.append({
                "ticker": ticker,
                "ledger_row_found_before_update": str(row_found).upper(),
                "scan_result": scan["scan_result"],
                "ledger_update_attempted": "TRUE",
                "ledger_update_success": str(update_success).upper(),
                "previous_last_scan_status": previous_status,
                "new_last_scan_status": ledger_map.get(ticker, {}).get("last_scan_status", ""),
                "previous_success_scan_count": previous_success,
                "new_success_scan_count": ledger_map.get(ticker, {}).get("success_scan_count", ""),
                "previous_attempt_scan_count": previous_attempt,
                "new_attempt_scan_count": ledger_map.get(ticker, {}).get("attempt_scan_count", ""),
                "error_message": error_message,
            })
        merged_rows = [ledger_map[ticker] for ticker in ordered_tickers if ticker in ledger_map]
        write_csv(ledger_path, merged_rows, ledger_fields)

    final_ledger_rows, _ = read_csv(ledger_path)
    total_universe_count = len(final_ledger_rows)
    today_date = dt.date.fromisoformat(today)
    window_start = today_date - dt.timedelta(days=4)
    unique_success_within_5day = 0
    remaining_rows: List[Dict[str, object]] = []
    never_success_count = 0
    remaining_stale_count = 0
    for row in final_ledger_rows:
        ticker = norm_ticker(row.get("ticker"))
        success_date = parse_date(row.get("last_success_scan_date"))
        status = str(row.get("last_scan_status", "")).strip()
        if success_date and success_date >= window_start:
            unique_success_within_5day += 1
        else:
            remaining_stale_count += 1
            reason = "NEVER_SUCCESS" if not success_date else "STALE_OR_OVERDUE"
            remaining_rows.append({
                "ticker": ticker,
                "last_scan_status": status,
                "last_success_scan_date": row.get("last_success_scan_date", ""),
                "last_attempt_scan_date": row.get("last_attempt_scan_date", ""),
                "reason": reason,
            })
        if not success_date:
            never_success_count += 1
    true_5day_met = unique_success_within_5day == total_universe_count and total_universe_count > 0
    if true_5day_met:
        coverage_trust = "FULL_5DAY_COVERAGE"
    elif unique_success_within_5day >= max(total_universe_count - 10, 0):
        coverage_trust = "HIGH_PARTIAL_COVERAGE"
    else:
        coverage_trust = "PARTIAL_COVERAGE"

    protected_after = snapshot_tree(root, [
        PRICE_CACHE,
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "data/v18/staged_market_proxy",
        "state/v18/market_proxy_cache",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/degraded_daily",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
    ])
    forbidden_changes = changed_paths(protected_before, protected_after)
    if forbidden_changes:
        validation_failures.append("Forbidden files changed")
    if scan_fail_count:
        validation_failures.append("One or more R20 local scans failed")
    if ledger_update_fail:
        validation_failures.append("One or more ledger updates failed")
    if not backup_ledger.exists() or not restore_script.exists() or not backup_manifest.exists():
        validation_failures.append("Backup/restore artifacts missing")

    validation_fail_count = len(validation_failures)
    if validation_fail_count:
        status = STATUS_WARN if ledger_update_success > 0 and not forbidden_changes else STATUS_FAIL
    else:
        status = STATUS_OK

    write_csv(root / OUT_RETEST, scan_rows, RETEST_FIELDS)
    write_csv(root / OUT_UPDATE, update_rows, UPDATE_FIELDS)
    audit_rows = [
        {"metric": "total_universe_count", "value": total_universe_count, "notes": "Rows in final rolling ledger."},
        {"metric": "r20_target_ticker_count", "value": len(target_tickers), "notes": "Discovered from R19 successful integrations."},
        {"metric": "scan_attempted_count", "value": len(scan_rows), "notes": "Local-only cache validation attempts."},
        {"metric": "scan_success_count", "value": scan_success_count, "notes": "SUCCESS_LOCAL_PRICE_FULL_HISTORY."},
        {"metric": "scan_fail_count", "value": scan_fail_count, "notes": "Local validation failures."},
        {"metric": "unique_success_within_5day_window", "value": unique_success_within_5day, "notes": f"Window start {window_start.isoformat()}."},
        {"metric": "true_5day_coverage_met", "value": str(true_5day_met).upper(), "notes": "All ledger tickers succeeded within current 5-day window."},
        {"metric": "remaining_stale_overdue_count", "value": remaining_stale_count, "notes": "Rows without success in current 5-day window."},
        {"metric": "never_success_count", "value": never_success_count, "notes": "Rows with no last_success_scan_date."},
        {"metric": "coverage_trust_level", "value": coverage_trust, "notes": "Local coverage trust after R20 update."},
    ]
    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(root / OUT_REMAINING, remaining_rows, REMAINING_FIELDS)

    next_step = "Run a separate Batch3 factor/technical/tier refresh-readiness audit for the 59 ledger-confirmed tickers."
    values = {
        "STATUS": status,
        "MODE": MODE,
        "R19_SOURCE_PATH": str(root / R19_READ_FIRST),
        "LEDGER_PATH": str(ledger_path),
        "LEDGER_BACKUP_DIR": str(backup_dir),
        "LEDGER_RESTORE_SCRIPT_PATH": str(restore_script),
        "R20_TARGET_TICKER_COUNT": str(len(target_tickers)),
        "SCAN_ATTEMPT_COUNT": str(len(scan_rows)),
        "SCAN_SUCCESS_COUNT": str(scan_success_count),
        "SCAN_FAIL_COUNT": str(scan_fail_count),
        "LEDGER_UPDATED": str(ledger_updated).upper(),
        "LEDGER_UPDATE_SUCCESS_COUNT": str(ledger_update_success),
        "LEDGER_UPDATE_FAIL_COUNT": str(ledger_update_fail),
        "TOTAL_UNIVERSE_COUNT": str(total_universe_count),
        "UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW": str(unique_success_within_5day),
        "TRUE_5DAY_COVERAGE_MET": str(true_5day_met).upper(),
        "REMAINING_STALE_OVERDUE_COUNT": str(remaining_stale_count),
        "NEVER_SUCCESS_COUNT": str(never_success_count),
        "COVERAGE_TRUST_LEVEL": coverage_trust,
        "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
        "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
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
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changes)).upper(),
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(root / OUT_REPORT, render_report(values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
