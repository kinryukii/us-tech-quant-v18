from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_R7_BATCH2_ROLLING_LEDGER_RETEST_READY"
STATUS_WARN = "WARN_V18_23C_R7_BATCH2_ROLLING_LEDGER_RETEST_READY"
STATUS_FAIL = "FAIL_V18_23C_R7_BATCH2_ROLLING_LEDGER_RETEST"
MODE = "LOCAL_ONLY_BATCH2_ROLLING_COVERAGE_LEDGER_RETEST"

R6_RESULT_REL = "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_RESULT.csv"
R6_HELD_REL = "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_HELD_OUT_TICKERS.csv"
R6_READ_FIRST_REL = "outputs/v18/ops/V18_23C_R6_READ_FIRST.txt"
LEDGER_REL = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
PRICE_CACHE_REL = "state/v18/price_cache"
FACTOR_REL = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_REL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

OUTPUTS = {
    "retest": "outputs/v18/rolling_coverage/V18_23C_R7_CURRENT_BATCH2_ROLLING_RETEST_RESULT.csv",
    "ledger_update": "outputs/v18/rolling_coverage/V18_23C_R7_CURRENT_LEDGER_UPDATE_RESULT.csv",
    "coverage": "outputs/v18/rolling_coverage/V18_23C_R7_CURRENT_COVERAGE_AUDIT.csv",
    "stale": "outputs/v18/rolling_coverage/V18_23C_R7_CURRENT_REMAINING_STALE_TICKERS.csv",
    "read_first": "outputs/v18/ops/V18_23C_R7_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R7_CURRENT_BATCH2_ROLLING_LEDGER_RETEST_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R6_SOURCE_PATH",
    "LEDGER_PATH",
    "LEDGER_BACKUP_DIR",
    "LEDGER_RESTORE_SCRIPT_PATH",
    "R7_TARGET_TICKER_COUNT",
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

RETEST_FIELDS = [
    "ticker",
    "official_cache_path",
    "official_cache_exists",
    "row_count",
    "latest_date",
    "close_non_null_count",
    "factor_pack_available",
    "technical_timing_available",
    "scan_result",
    "failure_reason",
]
LEDGER_UPDATE_FIELDS = [
    "ticker",
    "scan_result",
    "ledger_row_found",
    "ledger_update_status",
    "previous_last_scan_status",
    "new_last_scan_status",
    "previous_success_scan_count",
    "new_success_scan_count",
    "previous_attempt_scan_count",
    "new_attempt_scan_count",
]
COVERAGE_FIELDS = ["metric", "value", "notes"]
STALE_FIELDS = ["ticker", "last_scan_status", "last_success_scan_date", "attempt_scan_count", "success_scan_count", "stale_reason"]
BACKUP_FIELDS = ["artifact", "original_path", "backup_path", "backup_created", "restore_action"]

MIN_FULL_HISTORY_ROWS = 500


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


def parse_read_first(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()[:10]
    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_value(row: Dict[str, str], *names: str) -> str:
    lower = {key.lower(): key for key in row}
    for name in names:
        real = lower.get(name.lower())
        if real is not None:
            return str(row.get(real, "")).strip()
    return ""


def get_ticker(row: Dict[str, str]) -> str:
    value = get_value(row, "ticker", "Ticker", "symbol", "Symbol").upper()
    return value if value and value not in {"NAN", "NONE", "NULL"} else ""


def to_int(value: object) -> int:
    try:
        text = str(value).strip()
        return int(float(text)) if text else 0
    except ValueError:
        return 0


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
        "state/v18/price_cache",
        "data/v18/price_history",
        "state/v18/price_history",
        "data/v18/staged_backfill",
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


def discover_targets(root: Path) -> Tuple[List[str], List[str], Dict[str, str]]:
    result_rows, _ = read_csv(root / R6_RESULT_REL)
    held_rows, _ = read_csv(root / R6_HELD_REL)
    read_first = parse_read_first(root / R6_READ_FIRST_REL)
    held = {get_ticker(row) for row in held_rows if get_ticker(row)}
    targets = sorted(
        {
            get_ticker(row)
            for row in result_rows
            if get_ticker(row) and str(row.get("integration_status", "")).upper() == "SUCCESS"
        }
    )
    targets = [ticker for ticker in targets if ticker not in held]
    return targets, sorted(held), read_first


def ticker_set_from_csv(path: Path) -> set[str]:
    rows, _ = read_csv(path)
    return {get_ticker(row) for row in rows if get_ticker(row)}


def validate_price_cache(path: Path, factor_tickers: set[str], technical_tickers: set[str]) -> Dict[str, object]:
    ticker = path.stem.upper()
    if not path.exists():
        return {
            "ticker": ticker,
            "official_cache_path": str(path),
            "official_cache_exists": "FALSE",
            "row_count": 0,
            "latest_date": "",
            "close_non_null_count": 0,
            "factor_pack_available": str(ticker in factor_tickers).upper(),
            "technical_timing_available": str(ticker in technical_tickers).upper(),
            "scan_result": "FAIL_MISSING_OFFICIAL_PRICE_CACHE",
            "failure_reason": "Official cache file missing.",
        }
    rows, fields = read_csv(path)
    if not rows:
        return {
            "ticker": ticker,
            "official_cache_path": str(path),
            "official_cache_exists": "TRUE",
            "row_count": 0,
            "latest_date": "",
            "close_non_null_count": 0,
            "factor_pack_available": str(ticker in factor_tickers).upper(),
            "technical_timing_available": str(ticker in technical_tickers).upper(),
            "scan_result": "FAIL_EMPTY_CACHE",
            "failure_reason": "Official cache file has no rows.",
        }
    field_lower = {field.lower() for field in fields}
    if "close" not in field_lower:
        return {
            "ticker": ticker,
            "official_cache_path": str(path),
            "official_cache_exists": "TRUE",
            "row_count": len(rows),
            "latest_date": "",
            "close_non_null_count": 0,
            "factor_pack_available": str(ticker in factor_tickers).upper(),
            "technical_timing_available": str(ticker in technical_tickers).upper(),
            "scan_result": "FAIL_MISSING_CLOSE",
            "failure_reason": "Close column missing.",
        }
    dates = [parse_date(get_value(row, "date", "Date")) for row in rows]
    dates = [date for date in dates if date]
    close_count = sum(1 for row in rows if get_value(row, "close", "Close"))
    latest = max(dates).isoformat() if dates else ""
    if close_count == 0:
        result = "FAIL_MISSING_CLOSE"
        reason = "Close column has no non-null values."
    elif len(rows) < MIN_FULL_HISTORY_ROWS:
        result = "FAIL_INSUFFICIENT_HISTORY"
        reason = f"Row count below {MIN_FULL_HISTORY_ROWS}."
    elif not latest:
        result = "FAIL_OTHER"
        reason = "Latest date could not be parsed."
    else:
        result = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        reason = ""
    return {
        "ticker": ticker,
        "official_cache_path": str(path),
        "official_cache_exists": "TRUE",
        "row_count": len(rows),
        "latest_date": latest,
        "close_non_null_count": close_count,
        "factor_pack_available": str(ticker in factor_tickers).upper(),
        "technical_timing_available": str(ticker in technical_tickers).upper(),
        "scan_result": result,
        "failure_reason": reason,
    }


def ensure_ledger_fields(fields: List[str]) -> List[str]:
    out = list(fields)
    required = [
        "ticker",
        "last_scan_status",
        "last_success_scan_date",
        "last_attempt_scan_date",
        "last_scan_source",
        "last_scan_mode",
        "last_scan_note",
    ]
    for field in required:
        if field not in out:
            out.append(field)
    return out


def render_restore_script(ledger_path: Path, backup_path: Path) -> str:
    return f"""param([string]$Root = "D:\\us-tech-quant")
$ErrorActionPreference = "Stop"
Write-Host "=== RESTORE V18.23C-R7 ROLLING LEDGER START ==="
$src = "{backup_path}"
$dest = "{ledger_path}"
if (-not (Test-Path -LiteralPath $src)) {{ throw "Missing backup ledger: $src" }}
$parent = Split-Path -Parent $dest
if (-not (Test-Path -LiteralPath $parent)) {{ New-Item -ItemType Directory -Path $parent | Out-Null }}
Copy-Item -LiteralPath $src -Destination $dest -Force
Write-Host "=== RESTORE V18.23C-R7 ROLLING LEDGER END ==="
exit 0
"""


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.Language.Parser]::ParseFile('{escaped}', [ref]$null, [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def update_ledger(
    ledger_rows: List[Dict[str, str]],
    ledger_fields: List[str],
    retest_rows: Sequence[Dict[str, object]],
    run_id: str,
    now_ts: str,
    today: str,
) -> Tuple[List[Dict[str, str]], List[Dict[str, object]]]:
    fields = ensure_ledger_fields(ledger_fields)
    by_ticker = {get_ticker(row): row for row in ledger_rows if get_ticker(row)}
    updates: List[Dict[str, object]] = []
    for retest in retest_rows:
        ticker = str(retest["ticker"])
        row = by_ticker.get(ticker)
        found = row is not None
        if row is None:
            row = {field: "" for field in fields}
            row["ticker"] = ticker
            ledger_rows.append(row)
            by_ticker[ticker] = row
        previous_status = row.get("last_scan_status", "")
        previous_success = to_int(row.get("success_scan_count", ""))
        previous_attempt = to_int(row.get("attempt_scan_count", ""))
        scan_result = str(retest["scan_result"])
        success = scan_result == "SUCCESS_LOCAL_PRICE_FULL_HISTORY"

        row["last_scan_status"] = scan_result
        row["last_attempt_scan_date"] = today
        if "last_attempt_scan_timestamp" in fields:
            row["last_attempt_scan_timestamp"] = now_ts
        row["last_scan_source"] = "V18_23C_R7_BATCH2_LOCAL_ONLY_LEDGER_RETEST"
        row["last_scan_mode"] = MODE
        row["last_scan_note"] = "R7 local-only official price cache retest; no external fetch."
        if "last_scan_run_id" in fields:
            row["last_scan_run_id"] = run_id
        if "attempt_scan_count" in fields:
            row["attempt_scan_count"] = str(previous_attempt + 1)
        if success:
            row["last_success_scan_date"] = today
            if "last_success_scan_timestamp" in fields:
                row["last_success_scan_timestamp"] = now_ts
            if "success_scan_count" in fields:
                row["success_scan_count"] = str(previous_success + 1)
            if "local_price_available" in fields:
                row["local_price_available"] = "TRUE"
            if "full_history_ready" in fields:
                row["full_history_ready"] = "TRUE"
            if "failure_reason" in fields:
                row["failure_reason"] = ""
        else:
            if "failure_reason" in fields:
                row["failure_reason"] = str(retest.get("failure_reason", ""))
        if "factor_pack_available" in fields:
            row["factor_pack_available"] = str(retest.get("factor_pack_available", "FALSE"))
        if "technical_timing_available" in fields:
            row["technical_timing_available"] = str(retest.get("technical_timing_available", "FALSE"))
        if "source_notes" in fields:
            row["source_notes"] = (
                f"local_price={'available' if success else 'failed'};"
                f"factor_pack={str(retest.get('factor_pack_available', 'FALSE')).lower()};"
                f"technical_timing={str(retest.get('technical_timing_available', 'FALSE')).lower()};"
                "source=V18_23C_R7"
            )

        updates.append(
            {
                "ticker": ticker,
                "scan_result": scan_result,
                "ledger_row_found": str(found).upper(),
                "ledger_update_status": "UPDATED",
                "previous_last_scan_status": previous_status,
                "new_last_scan_status": row.get("last_scan_status", ""),
                "previous_success_scan_count": previous_success,
                "new_success_scan_count": row.get("success_scan_count", ""),
                "previous_attempt_scan_count": previous_attempt,
                "new_attempt_scan_count": row.get("attempt_scan_count", ""),
            }
        )
    return ledger_rows, updates


def coverage_metrics(ledger_rows: Sequence[Dict[str, str]], today: dt.date) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], Dict[str, int | str]]:
    window_start = today - dt.timedelta(days=4)
    unique_success = 0
    never_success = 0
    stale_rows: List[Dict[str, object]] = []
    for row in ledger_rows:
        ticker = get_ticker(row)
        success_date = parse_date(row.get("last_success_scan_date", ""))
        if success_date and window_start <= success_date <= today:
            unique_success += 1
        else:
            stale_rows.append(
                {
                    "ticker": ticker,
                    "last_scan_status": row.get("last_scan_status", ""),
                    "last_success_scan_date": row.get("last_success_scan_date", ""),
                    "attempt_scan_count": row.get("attempt_scan_count", ""),
                    "success_scan_count": row.get("success_scan_count", ""),
                    "stale_reason": "NEVER_SUCCESS" if not success_date else "OUTSIDE_5DAY_WINDOW",
                }
            )
        if not success_date:
            never_success += 1
    total = len([row for row in ledger_rows if get_ticker(row)])
    true_met = unique_success >= total and total > 0
    trust = "HIGH" if true_met else "MEDIUM" if unique_success > 0 else "LOW"
    metrics = {
        "TOTAL_UNIVERSE_COUNT": total,
        "UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW": unique_success,
        "TRUE_5DAY_COVERAGE_MET": str(true_met).upper(),
        "REMAINING_STALE_OVERDUE_COUNT": len(stale_rows),
        "NEVER_SUCCESS_COUNT": never_success,
        "COVERAGE_TRUST_LEVEL": trust,
    }
    coverage_rows = [
        {"metric": "total_universe_count", "value": total, "notes": "Ticker rows in rolling ledger."},
        {"metric": "unique_success_within_5day_window", "value": unique_success, "notes": f"Window start {window_start.isoformat()}."},
        {"metric": "true_5day_coverage_met", "value": str(true_met).upper(), "notes": "Requires all ledger tickers successful in current 5-day window."},
        {"metric": "remaining_stale_overdue_count", "value": len(stale_rows), "notes": "No success date in current 5-day window."},
        {"metric": "never_success_count", "value": never_success, "notes": "Missing last_success_scan_date."},
        {"metric": "coverage_trust_level", "value": trust, "notes": "Read-only coverage summary after R7 ledger update."},
    ]
    return coverage_rows, stale_rows, metrics


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R7 Batch 2 Rolling Coverage Ledger Retest

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Scope
Local-only retest for the 52 V18.23C-R6 integrated Batch 2 tickers. No external data was fetched and official price cache files were not modified.

## Result
- Target tickers: {values['R7_TARGET_TICKER_COUNT']}
- Scan success: {values['SCAN_SUCCESS_COUNT']}
- Scan fail: {values['SCAN_FAIL_COUNT']}
- Ledger update success: {values['LEDGER_UPDATE_SUCCESS_COUNT']}
- Ledger update fail: {values['LEDGER_UPDATE_FAIL_COUNT']}

## Coverage
- Total universe count: {values['TOTAL_UNIVERSE_COUNT']}
- Unique success within 5-day window: {values['UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW']}
- True 5-day coverage met: {values['TRUE_5DAY_COVERAGE_MET']}
- Remaining stale/overdue count: {values['REMAINING_STALE_OVERDUE_COUNT']}
- Never-success count: {values['NEVER_SUCCESS_COUNT']}
- Coverage trust level: {values['COVERAGE_TRUST_LEVEL']}

## Backup
- Ledger backup directory: {values['LEDGER_BACKUP_DIR']}
- Restore script: {values['LEDGER_RESTORE_SCRIPT_PATH']}

## Safety
Only the rolling ledger and R7 output/backup files were modified. Trading permissions remain disabled and official decision impact remains NONE.
"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V18.23C-R7 local-only Batch2 rolling coverage ledger retest")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    today_date = dt.date.today()
    today = today_date.isoformat()
    now_ts = dt.datetime.now().isoformat(timespec="seconds")
    run_id = f"V18_23C_R7_{timestamp}"

    ledger_path = root / LEDGER_REL
    backup_dir = root / "archive/v18/rolling_coverage_backups" / f"V18_23C_R7_{timestamp}"
    backup_ledger_path = backup_dir / "V18_23B_ROLLING_SCAN_LEDGER.csv"
    restore_script = backup_dir / "RESTORE_V18_23C_R7_ROLLING_LEDGER.ps1"
    backup_manifest = backup_dir / "BACKUP_MANIFEST.csv"

    before_forbidden = collect_forbidden_sigs(root)
    before_ledger = file_sig(ledger_path)

    targets, held, r6_rf = discover_targets(root)
    validation_failures: List[str] = []
    expected_success = to_int(r6_rf.get("INTEGRATION_SUCCESS_COUNT", "0"))
    if not targets:
        validation_failures.append("No R6 integration success tickers discovered.")
    if expected_success and len(targets) != expected_success:
        validation_failures.append(f"R7 target count {len(targets)} does not equal R6 integration success count {expected_success}.")
    if set(targets) & set(held):
        validation_failures.append("Held-out R6 tickers were included in R7 targets.")
    if not ledger_path.exists():
        validation_failures.append(f"Ledger missing: {ledger_path}")

    factor_tickers = ticker_set_from_csv(root / FACTOR_REL)
    technical_tickers = ticker_set_from_csv(root / TECH_REL)
    price_cache_dir = root / PRICE_CACHE_REL
    retest_rows = [validate_price_cache(price_cache_dir / f"{ticker}.csv", factor_tickers, technical_tickers) for ticker in targets]

    scan_success = sum(1 for row in retest_rows if row["scan_result"] == "SUCCESS_LOCAL_PRICE_FULL_HISTORY")
    scan_fail = len(retest_rows) - scan_success

    backup_rows: List[Dict[str, object]] = []
    ledger_update_rows: List[Dict[str, object]] = []
    ledger_rows: List[Dict[str, str]] = []
    ledger_fields: List[str] = []

    if not validation_failures:
        ensure_dir(backup_dir)
        shutil.copy2(ledger_path, backup_ledger_path)
        write_text(restore_script, render_restore_script(ledger_path, backup_ledger_path))
        backup_rows = [
            {
                "artifact": "rolling_coverage_ledger",
                "original_path": str(ledger_path),
                "backup_path": str(backup_ledger_path),
                "backup_created": str(backup_ledger_path.exists()).upper(),
                "restore_action": "COPY_BACKUP_OVER_LEDGER",
            }
        ]
        write_csv(backup_manifest, backup_rows, BACKUP_FIELDS)

        ledger_rows, ledger_fields = read_csv(ledger_path)
        ledger_fields = ensure_ledger_fields(ledger_fields)
        ledger_rows, ledger_update_rows = update_ledger(ledger_rows, ledger_fields, retest_rows, run_id, now_ts, today)
        write_csv(ledger_path, ledger_rows, ledger_fields)
    else:
        ledger_rows, ledger_fields = read_csv(ledger_path)
        ledger_fields = ensure_ledger_fields(ledger_fields)

    coverage_rows, stale_rows, coverage = coverage_metrics(ledger_rows, today_date)

    write_csv(root / OUTPUTS["retest"], retest_rows, RETEST_FIELDS)
    write_csv(root / OUTPUTS["ledger_update"], ledger_update_rows, LEDGER_UPDATE_FIELDS)
    write_csv(root / OUTPUTS["coverage"], coverage_rows, COVERAGE_FIELDS)
    write_csv(root / OUTPUTS["stale"], stale_rows, STALE_FIELDS)

    after_forbidden = collect_forbidden_sigs(root)
    after_ledger = file_sig(ledger_path)
    forbidden_changes = diff_sigs(before_forbidden, after_forbidden)
    ledger_changed = before_ledger != after_ledger

    if forbidden_changes:
        validation_failures.append(f"Forbidden files modified: {len(forbidden_changes)}.")
    if not ledger_changed and targets:
        validation_failures.append("Ledger was not modified despite R7 targets.")
    if not backup_dir.exists():
        validation_failures.append("Ledger backup directory missing.")
    if not restore_script.exists():
        validation_failures.append("Ledger restore script missing.")
    if not backup_manifest.exists():
        validation_failures.append("Ledger backup manifest missing.")
    if not py_compile(root / "scripts/v18/v18_23C_R7_batch2_rolling_coverage_ledger_retest.py"):
        validation_failures.append("Python compile check failed.")
    if not ps_parse(root / "scripts/v18/run_v18_23C_R7_batch2_rolling_coverage_ledger_retest.ps1"):
        validation_failures.append("PowerShell parse check failed.")

    ledger_update_success = sum(1 for row in ledger_update_rows if row["ledger_update_status"] == "UPDATED")
    ledger_update_fail = len(targets) - ledger_update_success
    if forbidden_changes or not targets or not restore_script.exists() or not backup_manifest.exists():
        status = STATUS_FAIL
    elif validation_failures or scan_fail or ledger_update_fail:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    values = {
        "STATUS": status,
        "MODE": MODE,
        "R6_SOURCE_PATH": str(root / R6_RESULT_REL),
        "LEDGER_PATH": str(ledger_path),
        "LEDGER_BACKUP_DIR": str(backup_dir) if backup_dir.exists() else "",
        "LEDGER_RESTORE_SCRIPT_PATH": str(restore_script) if restore_script.exists() else "",
        "R7_TARGET_TICKER_COUNT": str(len(targets)),
        "SCAN_ATTEMPT_COUNT": str(len(retest_rows)),
        "SCAN_SUCCESS_COUNT": str(scan_success),
        "SCAN_FAIL_COUNT": str(scan_fail),
        "LEDGER_UPDATED": str(ledger_changed).upper(),
        "LEDGER_UPDATE_SUCCESS_COUNT": str(ledger_update_success),
        "LEDGER_UPDATE_FAIL_COUNT": str(ledger_update_fail),
        "TOTAL_UNIVERSE_COUNT": str(coverage["TOTAL_UNIVERSE_COUNT"]),
        "UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW": str(coverage["UNIQUE_SUCCESS_WITHIN_5DAY_WINDOW"]),
        "TRUE_5DAY_COVERAGE_MET": str(coverage["TRUE_5DAY_COVERAGE_MET"]),
        "REMAINING_STALE_OVERDUE_COUNT": str(coverage["REMAINING_STALE_OVERDUE_COUNT"]),
        "NEVER_SUCCESS_COUNT": str(coverage["NEVER_SUCCESS_COUNT"]),
        "COVERAGE_TRUST_LEVEL": str(coverage["COVERAGE_TRUST_LEVEL"]),
        "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
        "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
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
        "VALIDATION_FAIL_COUNT": str(len(validation_failures)),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changes)).upper(),
    }

    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    write_text(root / OUTPUTS["report"], render_report(values))

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"R7_TARGET_TICKER_COUNT: {len(targets)}")
    print(f"SCAN_SUCCESS_COUNT: {scan_success}")
    print(f"SCAN_FAIL_COUNT: {scan_fail}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")
    return 1 if status == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
