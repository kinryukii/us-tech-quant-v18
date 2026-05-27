from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R23E_DRYRUN_ROLLING_LEDGER_UPDATE_PLAN_READY"
STATUS_OK = "OK_V18_25A_R23E_ROLLING_LEDGER_UPDATED_AFTER_PRICE_INTEGRATION"
STATUS_RESULTS_MISSING = "WARN_V18_25A_R23E_R23D_RESULTS_MISSING"
STATUS_ZERO_TARGETS = "WARN_V18_25A_R23E_ZERO_TARGETS"
STATUS_LOCAL_VALIDATION_FAILURE = "WARN_V18_25A_R23E_LOCAL_VALIDATION_FAILURE"
STATUS_PARTIAL = "WARN_V18_25A_R23E_LEDGER_UPDATE_PARTIAL"
STATUS_MISSING_LEDGER = "WARN_V18_25A_R23E_TARGETS_MISSING_FROM_LEDGER"
STATUS_ZERO_LEDGER = "WARN_V18_25A_R23E_ZERO_LEDGER_UPDATE_SUCCESS"

MODE_DRYRUN = "DRYRUN_ROLLING_LEDGER_UPDATE_PLAN_ONLY"
MODE_APPLY = "APPLY_ROLLING_LEDGER_UPDATE_AFTER_PRICE_INTEGRATION"

R23D_RESULT = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_INTEGRATION_RESULT.csv"
R23D_RETEST = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_POST_INTEGRATION_LOCAL_RETEST.csv"
R23C_CANDIDATES = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_OFFICIAL_INTEGRATION_CANDIDATES.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_TARGETS = "outputs/v18/rolling_coverage/V18_25A_R23E_CURRENT_TARGETS.csv"
OUT_VALIDATION = "outputs/v18/rolling_coverage/V18_25A_R23E_CURRENT_LOCAL_COVERAGE_VALIDATION.csv"
OUT_LEDGER = "outputs/v18/rolling_coverage/V18_25A_R23E_CURRENT_LEDGER_UPDATE_RESULT.csv"
OUT_COVERAGE = "outputs/v18/rolling_coverage/V18_25A_R23E_CURRENT_5DAY_COVERAGE_AFTER_UPDATE.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R23E_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R23E_CURRENT_ROLLING_LEDGER_UPDATE_REPORT.md"

TARGET_FIELDS = ["priority_rank", "ticker", "source", "r23d_integration_success", "r23d_retest_success", "r23c_candidate_confirmed", "target_status", "reason"]
VALIDATION_FIELDS = ["ticker", "official_cache_file", "file_exists", "readable", "row_count", "latest_date", "latest_close", "required_columns_available", "validation_status", "error_message"]
LEDGER_FIELDS = ["ticker", "local_validation_passed", "ledger_row_found", "ledger_update_attempted", "ledger_update_success", "previous_last_success_scan_date", "new_last_success_scan_date", "previous_last_scan_status", "new_last_scan_status", "error_message"]
COVERAGE_FIELDS = ["metric", "value", "notes"]
BACKUP_FIELDS = ["backup_item", "path", "status", "notes"]
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "TARGET_SOURCE_PATH",
    "LEDGER_PATH",
    "PRICE_CACHE_DIR",
    "BACKUP_DIR",
    "MAX_TICKERS",
    "R23D_INTEGRATION_SUCCESS_COUNT",
    "TARGET_TICKER_COUNT",
    "LOCAL_VALIDATION_ATTEMPT_COUNT",
    "LOCAL_VALIDATION_SUCCESS_COUNT",
    "LOCAL_VALIDATION_FAIL_COUNT",
    "LEDGER_UPDATE_ATTEMPT_COUNT",
    "LEDGER_UPDATE_SUCCESS_COUNT",
    "LEDGER_UPDATE_FAIL_COUNT",
    "PRE_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW",
    "POST_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW",
    "PRE_REMAINING_STALE_OR_NEVER_SUCCESS_COUNT",
    "POST_REMAINING_STALE_OR_NEVER_SUCCESS_COUNT",
    "PRE_NEVER_SUCCESS_COUNT",
    "POST_NEVER_SUCCESS_COUNT",
    "PRE_STALE_OVERDUE_COUNT",
    "POST_STALE_OVERDUE_COUNT",
    "TRUE_LOOKBACK_COVERAGE_MET_AFTER_UPDATE",
    "ROLLING_LEDGER_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED",
    "OFFICIAL_DECISION_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
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


def norm_key(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def find_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    by_norm = {norm_key(field): field for field in fields}
    for alias in aliases:
        hit = by_norm.get(norm_key(alias))
        if hit:
            return hit
    return None


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except Exception:
            continue
    return None


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def valid_symbol(ticker: str) -> bool:
    if ticker in {"", "TICKER", "TICKERS", "HEADER", "NULL", "NONE", "NAN", "SYMBOL"}:
        return False
    if any(ch in ticker for ch in '<>:"/\\|?*'):
        return False
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker))


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def coverage_metrics(rows: List[Dict[str, str]], fields: Sequence[str], today: dt.date, lookback_days: int = 5) -> Dict[str, object]:
    ticker_col = find_col(fields, ["ticker", "symbol"])
    success_col = find_col(fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    if not ticker_col or not success_col:
        return {"total": 0, "within": 0, "remaining": 0, "never": 0, "stale": 0, "met": False}
    start = today - dt.timedelta(days=max(lookback_days, 1) - 1)
    seen = set()
    within = remaining = never = stale = 0
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col))
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        d = parse_date(row.get(success_col))
        is_never = d is None
        is_within = bool(d and start <= d <= today)
        is_stale = bool(d and d < start)
        within += 1 if is_within else 0
        never += 1 if is_never else 0
        stale += 1 if is_stale else 0
        remaining += 1 if (is_never or not is_within) else 0
    return {"total": len(seen), "within": within, "remaining": remaining, "never": never, "stale": stale, "met": bool(seen) and within == len(seen)}


def validate_cache(root: Path, ticker: str) -> Dict[str, object]:
    path = root / PRICE_CACHE / f"{ticker}.csv"
    rows, fields = read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    field_set = {str(f).strip().lower() for f in fields}
    latest_date = ""
    latest_close = ""
    if rows:
        latest = sorted(rows, key=lambda row: str(row.get("date", "")))[-1]
        latest_date = str(latest.get("date", "") or "")
        latest_close = str(latest.get("close", "") or "")
    close = parse_float(latest_close)
    ok = path.exists() and bool(fields) and bool(rows) and bool(latest_date) and close is not None and close > 0 and required.issubset(field_set)
    return {
        "ticker": ticker,
        "official_cache_file": path.as_posix(),
        "file_exists": str(path.exists()).upper(),
        "readable": str(bool(fields)).upper(),
        "row_count": len(rows),
        "latest_date": latest_date,
        "latest_close": latest_close,
        "required_columns_available": str(required.issubset(field_set)).upper(),
        "validation_status": "LOCAL_PRICE_CACHE_READY" if ok else "LOCAL_PRICE_CACHE_VALIDATION_FAIL",
        "error_message": "" if ok else "Official cache failed local coverage validation.",
    }


def make_backup(root: Path, ledger_path: Path, run_stamp: str) -> Path:
    backup_dir = root / "archive" / "v18" / "rolling_coverage_backups" / f"V18_25A_R23E_{run_stamp}"
    ensure_dir(backup_dir)
    backup_ledger = backup_dir / ledger_path.name
    shutil.copy2(ledger_path, backup_ledger)
    rows = [
        {"backup_item": "rolling_ledger", "path": backup_ledger.as_posix(), "status": "COPIED", "notes": "Original ledger before R23E update."},
        {"backup_item": "restore_script", "path": (backup_dir / "RESTORE_V18_25A_R23E_ROLLING_LEDGER.ps1").as_posix(), "status": "CREATED", "notes": ""},
        {"backup_item": "readme", "path": (backup_dir / "README_RESTORE_V18_25A_R23E.txt").as_posix(), "status": "CREATED", "notes": ""},
    ]
    write_csv(backup_dir / "MANIFEST.csv", rows, BACKUP_FIELDS)
    restore = f"""[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)
$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "{ledger_path.name}"
$target = Join-Path $Root "{ledger_path.relative_to(root)}"
Copy-Item -Path $source -Destination $target -Force
Write-Host "Restored R23E rolling ledger backup to $target"
"""
    write_text(backup_dir / "RESTORE_V18_25A_R23E_ROLLING_LEDGER.ps1", restore)
    write_text(backup_dir / "README_RESTORE_V18_25A_R23E.txt", f"R23E backup created before rolling ledger update.\nSource ledger: {ledger_path}\nRun the restore script in this directory to restore the original ledger.\n")
    return backup_dir


def update_ledger(rows: List[Dict[str, str]], fields: Sequence[str], validations: List[Dict[str, object]], now: dt.datetime, run_id: str) -> Tuple[List[Dict[str, object]], int, int]:
    ticker_col = find_col(fields, ["ticker", "symbol"])
    row_by_ticker = {norm_ticker(row.get(ticker_col)): row for row in rows} if ticker_col else {}
    success_date_cols = [col for col in fields if norm_key(col) in {"lastsuccessscandate", "lastsuccessdate", "latestsuccessdate"}]
    success_ts_cols = [col for col in fields if norm_key(col) in {"lastsuccessscantimestamp", "lastsuccesstimestamp", "latestsuccesstimestamp"}]
    status_col = find_col(fields, ["last_scan_status", "scan_status", "status"])
    run_col = find_col(fields, ["last_scan_run_id", "scan_run_id", "run_id"])
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
    success = fail = 0
    for validation in validations:
        ticker = norm_ticker(validation.get("ticker"))
        passed = validation.get("validation_status") == "LOCAL_PRICE_CACHE_READY"
        ledger_row = row_by_ticker.get(ticker)
        prev_date = ledger_row.get(success_date_cols[0], "") if ledger_row and success_date_cols else ""
        prev_status = ledger_row.get(status_col, "") if ledger_row and status_col else ""
        result = {
            "ticker": ticker,
            "local_validation_passed": passed,
            "ledger_row_found": bool(ledger_row),
            "ledger_update_attempted": False,
            "ledger_update_success": False,
            "previous_last_success_scan_date": prev_date,
            "new_last_success_scan_date": prev_date,
            "previous_last_scan_status": prev_status,
            "new_last_scan_status": prev_status,
            "error_message": "",
        }
        if not passed:
            result["error_message"] = str(validation.get("error_message", "Local validation failed."))
            result_rows.append(result)
            continue
        result["ledger_update_attempted"] = True
        if not ledger_row:
            result["error_message"] = "Target missing from ledger; append disabled."
            fail += 1
            result_rows.append(result)
            continue
        for col in success_date_cols:
            ledger_row[col] = now.date().isoformat()
        for col in success_ts_cols:
            ledger_row[col] = now.replace(microsecond=0).isoformat()
        if status_col:
            ledger_row[status_col] = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        if run_col:
            ledger_row[run_col] = run_id
        if attempt_ts_col:
            ledger_row[attempt_ts_col] = now.replace(microsecond=0).isoformat()
        if attempt_date_col:
            ledger_row[attempt_date_col] = now.date().isoformat()
        if source_col:
            ledger_row[source_col] = "V18_25A_R23E_AFTER_PRICE_CACHE_INTEGRATION"
        if mode_col:
            ledger_row[mode_col] = MODE_APPLY
        if note_col:
            ledger_row[note_col] = "R23E official price cache local validation passed; no external fetch."
        if local_col:
            ledger_row[local_col] = "TRUE"
        if full_history_col:
            ledger_row[full_history_col] = "TRUE"
        if success_count_col:
            ledger_row[success_count_col] = str(to_int(ledger_row.get(success_count_col), 0) + 1)
        if attempt_count_col:
            ledger_row[attempt_count_col] = str(to_int(ledger_row.get(attempt_count_col), 0) + 1)
        result["ledger_update_success"] = True
        result["new_last_success_scan_date"] = now.date().isoformat()
        result["new_last_scan_status"] = "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        success += 1
        result_rows.append(result)
    return result_rows, success, fail


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object]) -> str:
    return "\n".join(
        [
            "# V18.25A R23E Rolling Ledger Update Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Coverage",
            f"- pre_unique_success_within_lookback_window: {values['PRE_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW']}",
            f"- post_unique_success_within_lookback_window: {values['POST_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW']}",
            f"- pre_remaining_stale_or_never_success_count: {values['PRE_REMAINING_STALE_OR_NEVER_SUCCESS_COUNT']}",
            f"- post_remaining_stale_or_never_success_count: {values['POST_REMAINING_STALE_OR_NEVER_SUCCESS_COUNT']}",
            "",
            "## Safety",
            "- external_fetch_executed: FALSE",
            "- price_cache_modified: FALSE",
            "- rolling ledger modified only in apply mode after backup.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-tickers", type=int, default=36)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    now = dt.datetime.now()
    run_stamp = now.strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R23E_{run_stamp}"
    ledger_path = root / LEDGER
    result_rows_in, _ = read_csv(root / R23D_RESULT)
    retest_rows_in, _ = read_csv(root / R23D_RETEST)
    candidate_rows, _ = read_csv(root / R23C_CANDIDATES)
    ledger_rows, ledger_fields = read_csv(ledger_path)

    ledger_before = file_sig(ledger_path)
    price_before = tree_sig(root / PRICE_CACHE)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    tiers_before = tree_sig(root / "outputs" / "v18" / "tiers")
    decision_before = tree_sig(root / "outputs" / "v18" / "daily_decision")

    status = STATUS_DRYRUN if args.dry_run else STATUS_OK
    validation_fail_count = 0
    backup_dir = ""
    if not result_rows_in or not retest_rows_in:
        status = STATUS_RESULTS_MISSING
        validation_fail_count = 1

    integrated = {norm_ticker(row.get("ticker")) for row in result_rows_in if is_true(row.get("integration_success"))}
    retested = {norm_ticker(row.get("ticker")) for row in retest_rows_in if str(row.get("retest_status", "")).upper() == "LOCAL_PRICE_CACHE_READY"}
    candidates = {norm_ticker(row.get("ticker")) for row in candidate_rows}
    valid_targets = sorted(t for t in (integrated & retested & candidates) if valid_symbol(t))
    valid_targets = valid_targets[: max(args.max_tickers, 0)]
    if status in {STATUS_DRYRUN, STATUS_OK} and not valid_targets:
        status = STATUS_ZERO_TARGETS
        validation_fail_count = 1

    target_rows = []
    for idx, ticker in enumerate(valid_targets, 1):
        target_rows.append({"priority_rank": idx, "ticker": ticker, "source": "R23D_INTEGRATION_RESULT_AND_RETEST", "r23d_integration_success": "TRUE", "r23d_retest_success": "TRUE", "r23c_candidate_confirmed": "TRUE", "target_status": "TARGET_READY", "reason": "R23D integration and post-integration retest succeeded; R23C candidate confirmed."})

    validations = [validate_cache(root, ticker) for ticker in valid_targets]
    validation_success = sum(1 for row in validations if row["validation_status"] == "LOCAL_PRICE_CACHE_READY")
    validation_fail = len(validations) - validation_success
    if validation_fail and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_LOCAL_VALIDATION_FAILURE
        validation_fail_count += validation_fail

    pre_cov = coverage_metrics(ledger_rows, ledger_fields, now.date())
    post_cov = dict(pre_cov)
    ledger_results: List[Dict[str, object]] = []
    ledger_update_success = ledger_update_fail = 0
    if validations and validation_success > 0:
        dry_rows = [dict(row) for row in ledger_rows]
        ledger_results, dry_success, dry_fail = update_ledger(dry_rows, ledger_fields, validations, now, run_id)
        missing_targets = [row["ticker"] for row in ledger_results if row["ledger_update_attempted"] and not row["ledger_row_found"]]
        if missing_targets and status in {STATUS_DRYRUN, STATUS_OK}:
            status = STATUS_MISSING_LEDGER
            validation_fail_count += len(missing_targets)
        if not args.dry_run and status == STATUS_OK:
            backup_path = make_backup(root, ledger_path, run_stamp)
            backup_dir = backup_path.as_posix()
            ledger_results, ledger_update_success, ledger_update_fail = update_ledger(ledger_rows, ledger_fields, validations, now, run_id)
            if ledger_update_success > 0:
                write_csv(ledger_path, ledger_rows, ledger_fields)
                post_rows, post_fields = read_csv(ledger_path)
                post_cov = coverage_metrics(post_rows, post_fields, now.date())
            if ledger_update_fail:
                status = STATUS_PARTIAL
                validation_fail_count += ledger_update_fail
            elif ledger_update_success == 0:
                status = STATUS_ZERO_LEDGER
                validation_fail_count += 1
        elif args.dry_run and status == STATUS_DRYRUN:
            post_cov = coverage_metrics(dry_rows, ledger_fields, now.date())
    elif validations and validation_success == 0 and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_ZERO_LEDGER
        validation_fail_count += 1

    coverage_rows = [
        {"metric": "total_universe_count", "value": pre_cov["total"], "notes": ""},
        {"metric": "pre_unique_success_within_lookback_window", "value": pre_cov["within"], "notes": ""},
        {"metric": "post_unique_success_within_lookback_window", "value": post_cov["within"], "notes": ""},
        {"metric": "pre_remaining_stale_or_never_success_count", "value": pre_cov["remaining"], "notes": ""},
        {"metric": "post_remaining_stale_or_never_success_count", "value": post_cov["remaining"], "notes": ""},
        {"metric": "pre_never_success_count", "value": pre_cov["never"], "notes": ""},
        {"metric": "post_never_success_count", "value": post_cov["never"], "notes": ""},
        {"metric": "pre_stale_overdue_count", "value": pre_cov["stale"], "notes": ""},
        {"metric": "post_stale_overdue_count", "value": post_cov["stale"], "notes": ""},
        {"metric": "true_lookback_coverage_met_after_update", "value": str(post_cov["met"]).upper(), "notes": ""},
    ]
    write_csv(root / OUT_TARGETS, target_rows, TARGET_FIELDS)
    write_csv(root / OUT_VALIDATION, validations, VALIDATION_FIELDS)
    write_csv(root / OUT_LEDGER, ledger_results, LEDGER_FIELDS)
    write_csv(root / OUT_COVERAGE, coverage_rows, COVERAGE_FIELDS)

    ledger_modified = file_sig(ledger_path) != ledger_before
    price_modified = tree_sig(root / PRICE_CACHE) != price_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    tiers_modified = tree_sig(root / "outputs" / "v18" / "tiers") != tiers_before
    decision_modified = tree_sig(root / "outputs" / "v18" / "daily_decision") != decision_before
    forbidden_modified = price_modified or factor_modified or tech_modified or tiers_modified or decision_modified or (ledger_modified and args.dry_run)

    values = {
        "STATUS": status,
        "MODE": MODE_DRYRUN if args.dry_run else MODE_APPLY,
        "RUN_ID": run_id,
        "TARGET_SOURCE_PATH": R23D_RESULT,
        "LEDGER_PATH": LEDGER,
        "PRICE_CACHE_DIR": PRICE_CACHE,
        "BACKUP_DIR": backup_dir,
        "MAX_TICKERS": args.max_tickers,
        "R23D_INTEGRATION_SUCCESS_COUNT": len(integrated),
        "TARGET_TICKER_COUNT": len(valid_targets),
        "LOCAL_VALIDATION_ATTEMPT_COUNT": len(validations),
        "LOCAL_VALIDATION_SUCCESS_COUNT": validation_success,
        "LOCAL_VALIDATION_FAIL_COUNT": validation_fail,
        "LEDGER_UPDATE_ATTEMPT_COUNT": ledger_update_success + ledger_update_fail if not args.dry_run else 0,
        "LEDGER_UPDATE_SUCCESS_COUNT": ledger_update_success,
        "LEDGER_UPDATE_FAIL_COUNT": ledger_update_fail,
        "PRE_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW": pre_cov["within"],
        "POST_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW": post_cov["within"],
        "PRE_REMAINING_STALE_OR_NEVER_SUCCESS_COUNT": pre_cov["remaining"],
        "POST_REMAINING_STALE_OR_NEVER_SUCCESS_COUNT": post_cov["remaining"],
        "PRE_NEVER_SUCCESS_COUNT": pre_cov["never"],
        "POST_NEVER_SUCCESS_COUNT": post_cov["never"],
        "PRE_STALE_OVERDUE_COUNT": pre_cov["stale"],
        "POST_STALE_OVERDUE_COUNT": post_cov["stale"],
        "TRUE_LOOKBACK_COVERAGE_MET_AFTER_UPDATE": str(post_cov["met"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "TIER_FILES_MODIFIED": str(tiers_modified).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(decision_modified).upper(),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R24: Batch3/R23 integrated tickers factor, technical, and tier refresh-readiness audit.",
    }
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values))
    print(f"STATUS: {status}")
    print(f"MODE: {values['MODE']}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
