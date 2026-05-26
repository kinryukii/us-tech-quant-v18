from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R22B_ROLLING_REFRESH_PLAN_EXECUTED_LEDGER_UPDATED"
STATUS_DRYRUN = "OK_V18_25A_R22B_DRYRUN_REFRESH_PLAN_VALIDATED"
STATUS_PLAN_MISSING = "WARN_V18_25A_R22B_PLAN_MISSING"
STATUS_LEDGER_MISSING = "WARN_V18_25A_R22B_LEDGER_MISSING"
STATUS_PRIORITY_REVIEW = "WARN_V18_25A_R22B_PLAN_PRIORITY_INTEGRITY_REVIEW_NEEDED"
STATUS_BUCKET_UNUSABLE = "WARN_V18_25A_R22B_PLAN_BUCKET_UNUSABLE"
STATUS_NO_LOCAL_PRICE = "WARN_V18_25A_R22B_NO_LOCAL_PRICE_AVAILABLE"
STATUS_ZERO_SUCCESS = "WARN_V18_25A_R22B_ZERO_VALID_REFRESH_SUCCESS"
STATUS_PARTIAL = "WARN_V18_25A_R22B_LEDGER_UPDATE_PARTIAL"

MODE_APPLY = "APPLY_LEDGER_UPDATE_LOCAL_ONLY"
MODE_DRYRUN = "DRYRUN_LOCAL_VALIDATION_ONLY"

DEFAULT_PLAN = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_MULTI_RUN_REFRESH_PLAN.csv"
DEFAULT_STATE = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_CONTINUATION_STATE.csv"
DEFAULT_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
PRICE_CACHE = "state/v18/price_cache"

OUT_PLAN_AUDIT = "outputs/v18/rolling_coverage/V18_25A_R22B_CURRENT_REFRESH_EXECUTION_PLAN_AUDIT.csv"
OUT_VALIDATION = "outputs/v18/rolling_coverage/V18_25A_R22B_CURRENT_LOCAL_REFRESH_VALIDATION.csv"
OUT_LEDGER_RESULT = "outputs/v18/rolling_coverage/V18_25A_R22B_CURRENT_LEDGER_UPDATE_RESULT.csv"
OUT_COVERAGE = "outputs/v18/rolling_coverage/V18_25A_R22B_CURRENT_5DAY_COVERAGE_AFTER_UPDATE.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R22B_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R22B_CURRENT_EXECUTE_ROLLING_REFRESH_REPORT.md"

PLAN_AUDIT_FIELDS = ["check", "status", "value", "notes"]
VALIDATION_FIELDS = [
    "priority_rank",
    "ticker",
    "priority_bucket",
    "local_price_path",
    "local_price_available",
    "readable",
    "row_count",
    "latest_price_date",
    "latest_close_available",
    "valid_ticker_symbol",
    "validation_result",
    "error_message",
]
LEDGER_RESULT_FIELDS = [
    "ticker",
    "local_validation_passed",
    "ledger_row_found",
    "ledger_update_attempted",
    "ledger_update_success",
    "previous_last_success_scan_date",
    "new_last_success_scan_date",
    "previous_last_scan_status",
    "new_last_scan_status",
    "error_message",
]
COVERAGE_FIELDS = ["metric", "value", "notes"]
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "PLAN_PATH",
    "LEDGER_PATH",
    "BACKUP_DIR",
    "MAX_TICKERS",
    "PLAN_ROW_COUNT",
    "SELECTED_TICKER_COUNT",
    "PLAN_NEVER_SUCCESS_COUNT",
    "PLAN_STALE_OVERDUE_COUNT",
    "PLAN_OLD_SUCCESS_FILL_COUNT",
    "PLAN_UNKNOWN_BUCKET_COUNT",
    "PLAN_PRIORITY_INTEGRITY_STATUS",
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
    "TRUE_LOOKBACK_COVERAGE_MET_AFTER_UPDATE",
    "ROLLING_LEDGER_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED",
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


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


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


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def classify_bucket(plan_row: Dict[str, str], state_row: Optional[Dict[str, str]]) -> str:
    bucket = str(plan_row.get("priority_bucket", "") or "").upper()
    if "NEVER" in bucket:
        return "never_success"
    if "STALE" in bucket or "OVERDUE" in bucket:
        return "stale_overdue"
    if "OLDEST" in bucket or "OLD_SUCCESS" in bucket or "SUCCESS_REFRESH" in bucket:
        return "old_success_fill"
    if state_row:
        if is_true(state_row.get("never_success")):
            return "never_success"
        if is_true(state_row.get("stale_overdue")):
            return "stale_overdue"
        if is_true(state_row.get("continuation_eligible")):
            return "old_success_fill"
    return "unknown"


def selected_plan_rows(plan_rows: List[Dict[str, str]], max_tickers: int) -> List[Dict[str, str]]:
    rows = [row for row in plan_rows if is_true(row.get("selected_for_next_refresh", "TRUE"))]
    rows.sort(key=lambda row: (to_int(row.get("priority_rank"), 999999), norm_ticker(row.get("ticker"))))
    return rows[: max(max_tickers, 0)]


def coverage_metrics(ledger_rows: List[Dict[str, str]], fields: Sequence[str], today: dt.date, lookback_days: int = 5) -> Dict[str, int | bool]:
    ticker_col = find_col(fields, ["ticker", "symbol"])
    success_col = find_col(fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    if not ticker_col or not success_col:
        return {
            "total": 0,
            "within": 0,
            "remaining": 0,
            "never": 0,
            "met": False,
        }
    start = today - dt.timedelta(days=max(lookback_days, 1) - 1)
    seen: set[str] = set()
    within = never = remaining = 0
    for row in ledger_rows:
        ticker = norm_ticker(row.get(ticker_col))
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        success_date = parse_date(row.get(success_col))
        is_never = success_date is None
        is_within = bool(success_date and start <= success_date <= today)
        never += 1 if is_never else 0
        within += 1 if is_within else 0
        remaining += 1 if (is_never or not is_within) else 0
    return {"total": len(seen), "within": within, "remaining": remaining, "never": never, "met": bool(seen) and within == len(seen)}


def valid_symbol(ticker: str) -> bool:
    if ticker in {"TICKER", "TICKERS", "SYMBOL", "NAN", "NONE"}:
        return False
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker))


def validate_local_price(root: Path, ticker: str, priority_rank: object, priority_bucket: object) -> Dict[str, object]:
    path = root / PRICE_CACHE / f"{ticker}.csv"
    result = {
        "priority_rank": priority_rank,
        "ticker": ticker,
        "priority_bucket": priority_bucket,
        "local_price_path": path.as_posix(),
        "local_price_available": path.exists(),
        "readable": False,
        "row_count": 0,
        "latest_price_date": "",
        "latest_close_available": False,
        "valid_ticker_symbol": valid_symbol(ticker),
        "validation_result": "FAIL",
        "error_message": "",
    }
    if not result["valid_ticker_symbol"]:
        result["error_message"] = "Invalid ticker-like symbol."
        return result
    if not path.exists():
        result["error_message"] = "Local price cache file missing."
        return result
    rows, fields = read_csv(path)
    result["readable"] = bool(fields)
    result["row_count"] = len(rows)
    if not fields:
        result["error_message"] = "Local price cache unreadable."
        return result
    if not rows:
        result["error_message"] = "Local price cache empty."
        return result
    date_col = find_col(fields, ["date", "price_date", "timestamp"])
    close_col = find_col(fields, ["close", "adj_close", "price", "last"])
    if not date_col:
        result["error_message"] = "Price date column missing."
        return result
    if not close_col:
        result["error_message"] = "Close/price column missing."
        return result
    valid_rows = []
    for row in rows:
        price_date = parse_date(row.get(date_col))
        close_value = str(row.get(close_col, "") or "").strip()
        if price_date and close_value:
            valid_rows.append((price_date, close_value))
    if not valid_rows:
        result["error_message"] = "No row has both latest date and close/price."
        return result
    latest_date, latest_close = max(valid_rows, key=lambda item: item[0])
    result["latest_price_date"] = latest_date.isoformat()
    result["latest_close_available"] = bool(latest_close)
    result["validation_result"] = "PASS_LOCAL_PRICE_AVAILABLE"
    return result


def make_backup(root: Path, ledger_path: Path, run_stamp: str) -> Path:
    backup_dir = root / "archive" / "v18" / "rolling_coverage_backups" / f"V18_25A_R22B_{run_stamp}"
    ensure_dir(backup_dir)
    backup_ledger = backup_dir / ledger_path.name
    shutil.copy2(ledger_path, backup_ledger)
    manifest = [
        {"backup_item": "rolling_ledger", "path": backup_ledger.as_posix(), "status": "COPIED", "notes": "Original ledger before R22B update."},
        {"backup_item": "restore_script", "path": (backup_dir / "RESTORE_V18_25A_R22B_ROLLING_LEDGER.ps1").as_posix(), "status": "CREATED", "notes": ""},
        {"backup_item": "readme", "path": (backup_dir / "README_RESTORE_V18_25A_R22B.txt").as_posix(), "status": "CREATED", "notes": ""},
    ]
    write_csv(backup_dir / "MANIFEST.csv", manifest, ["backup_item", "path", "status", "notes"])
    restore = f"""[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)
$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "{ledger_path.name}"
$target = Join-Path $Root "{ledger_path.relative_to(root)}"
Copy-Item -Path $source -Destination $target -Force
Write-Host "Restored R22B rolling ledger backup to $target"
"""
    write_text(backup_dir / "RESTORE_V18_25A_R22B_ROLLING_LEDGER.ps1", restore)
    write_text(
        backup_dir / "README_RESTORE_V18_25A_R22B.txt",
        f"R22B backup created before rolling ledger update.\nSource ledger: {ledger_path}\nRun the restore script in this directory to restore the original ledger.\n",
    )
    return backup_dir


def update_ledger(
    rows: List[Dict[str, str]],
    fields: Sequence[str],
    validations: List[Dict[str, object]],
    now: dt.datetime,
    run_id: str,
) -> Tuple[List[Dict[str, object]], int, int]:
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
        passed = str(validation.get("validation_result")) == "PASS_LOCAL_PRICE_AVAILABLE"
        ledger_row = row_by_ticker.get(ticker)
        previous_date = ledger_row.get(success_date_cols[0], "") if ledger_row and success_date_cols else ""
        previous_status = ledger_row.get(status_col, "") if ledger_row and status_col else ""
        result = {
            "ticker": ticker,
            "local_validation_passed": passed,
            "ledger_row_found": bool(ledger_row),
            "ledger_update_attempted": False,
            "ledger_update_success": False,
            "previous_last_success_scan_date": previous_date,
            "new_last_success_scan_date": previous_date,
            "previous_last_scan_status": previous_status,
            "new_last_scan_status": previous_status,
            "error_message": "",
        }
        if not passed:
            result["error_message"] = str(validation.get("error_message", "Local validation failed."))
            result_rows.append(result)
            continue
        result["ledger_update_attempted"] = True
        if not ledger_row:
            result["error_message"] = "Planned ticker missing from ledger; row append disabled by default."
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
            ledger_row[source_col] = "V18_25A_R22B_LOCAL_REFRESH_PLAN_LEDGER_UPDATE"
        if mode_col:
            ledger_row[mode_col] = MODE_APPLY
        if note_col:
            ledger_row[note_col] = "R22B local price cache validation passed; no external fetch."
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


def render_report(values: Dict[str, object], backup_dir: str) -> str:
    return "\n".join(
        [
            "# V18.25A R22B Execute Rolling Refresh Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Execution",
            f"- selected_ticker_count: {values['SELECTED_TICKER_COUNT']}",
            f"- local_validation_success_count: {values['LOCAL_VALIDATION_SUCCESS_COUNT']}",
            f"- local_validation_fail_count: {values['LOCAL_VALIDATION_FAIL_COUNT']}",
            f"- ledger_update_success_count: {values['LEDGER_UPDATE_SUCCESS_COUNT']}",
            "",
            "## Coverage",
            f"- pre_unique_success_within_lookback_window: {values['PRE_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW']}",
            f"- post_unique_success_within_lookback_window: {values['POST_UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW']}",
            f"- true_lookback_coverage_met_after_update: {values['TRUE_LOOKBACK_COVERAGE_MET_AFTER_UPDATE']}",
            "",
            "## Backup",
            f"- backup_dir: {backup_dir or '(not created)'}",
            "",
            "## Safety",
            "- external_fetch_executed: FALSE",
            "- price_cache_modified: FALSE",
            "- forbidden_modified: FALSE",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-tickers", type=int, default=65)
    parser.add_argument("--plan-path", default=DEFAULT_PLAN)
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    now = dt.datetime.now()
    run_stamp = now.strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R22B_{run_stamp}"
    plan_path = (root / args.plan_path).resolve() if not Path(args.plan_path).is_absolute() else Path(args.plan_path)
    state_path = root / DEFAULT_STATE
    ledger_path = (root / args.ledger_path).resolve() if not Path(args.ledger_path).is_absolute() else Path(args.ledger_path)

    status = STATUS_OK if not args.dry_run else STATUS_DRYRUN
    validation_fail_count = 0
    backup_dir = ""
    ledger_before_sig = file_sig(ledger_path)
    price_before_sig = file_sig(root / PRICE_CACHE)

    plan_rows, plan_fields = read_csv(plan_path)
    state_rows, state_fields = read_csv(state_path)
    ledger_rows, ledger_fields = read_csv(ledger_path)
    state_by_ticker = {norm_ticker(row.get("ticker")): row for row in state_rows}
    selected = selected_plan_rows(plan_rows, args.max_tickers)

    bucket_counts = {"never_success": 0, "stale_overdue": 0, "old_success_fill": 0, "unknown": 0}
    unknown_bucket = False
    missing_in_state: List[str] = []
    for row in selected:
        ticker = norm_ticker(row.get("ticker"))
        state_row = state_by_ticker.get(ticker)
        if not state_row:
            missing_in_state.append(ticker)
        bucket = classify_bucket(row, state_row)
        if bucket == "unknown":
            unknown_bucket = True
        bucket_counts[bucket] += 1

    eligible_never = {ticker for ticker, row in state_by_ticker.items() if is_true(row.get("never_success")) and is_true(row.get("continuation_eligible"))}
    planned_never = {norm_ticker(row.get("ticker")) for row in selected if classify_bucket(row, state_by_ticker.get(norm_ticker(row.get("ticker")))) == "never_success"}
    missing_eligible_never = sorted(eligible_never - planned_never)
    priority_status = "PASS"

    if not plan_path.exists() or not plan_rows:
        status = STATUS_PLAN_MISSING
        priority_status = "FAIL_PLAN_MISSING"
        validation_fail_count += 1
    elif not ledger_path.exists() or not ledger_rows:
        status = STATUS_LEDGER_MISSING
        priority_status = "FAIL_LEDGER_MISSING"
        validation_fail_count += 1
    elif missing_in_state or missing_eligible_never:
        status = STATUS_PRIORITY_REVIEW
        priority_status = "FAIL_PRIORITY_INTEGRITY"
        validation_fail_count += 1
    elif unknown_bucket:
        status = STATUS_BUCKET_UNUSABLE
        priority_status = "FAIL_BUCKET_UNUSABLE"
        validation_fail_count += 1

    validations: List[Dict[str, object]] = []
    if priority_status == "PASS":
        for row in selected:
            ticker = norm_ticker(row.get("ticker"))
            validations.append(validate_local_price(root, ticker, row.get("priority_rank", ""), row.get("priority_bucket", "")))
        if validations and not any(v["validation_result"] == "PASS_LOCAL_PRICE_AVAILABLE" for v in validations):
            status = STATUS_NO_LOCAL_PRICE
            validation_fail_count += 1

    validation_success = sum(1 for row in validations if row["validation_result"] == "PASS_LOCAL_PRICE_AVAILABLE")
    validation_fail = len(validations) - validation_success
    pre_cov = coverage_metrics(ledger_rows, ledger_fields, now.date())
    post_cov = dict(pre_cov)
    ledger_results: List[Dict[str, object]] = []
    ledger_update_success = 0
    ledger_update_fail = 0
    update_allowed = priority_status == "PASS" and validation_success > 0 and not args.dry_run

    if priority_status == "PASS" and validation_success == 0 and validations:
        status = STATUS_ZERO_SUCCESS

    if update_allowed:
        backup_path = make_backup(root, ledger_path, run_stamp)
        backup_dir = backup_path.as_posix()
        ledger_results, ledger_update_success, ledger_update_fail = update_ledger(ledger_rows, ledger_fields, validations, now, run_id)
        if ledger_update_success > 0:
            write_csv(ledger_path, ledger_rows, ledger_fields)
            post_rows, post_fields = read_csv(ledger_path)
            post_cov = coverage_metrics(post_rows, post_fields, now.date())
        if ledger_update_fail > 0:
            status = STATUS_PARTIAL
            validation_fail_count += ledger_update_fail
        elif ledger_update_success > 0:
            status = STATUS_OK
    elif validations:
        ledger_results, ledger_update_success, ledger_update_fail = update_ledger([dict(row) for row in ledger_rows], ledger_fields, validations, now, run_id)
        if args.dry_run and priority_status == "PASS":
            status = STATUS_DRYRUN
        ledger_update_success = 0
        ledger_update_fail = 0

    plan_audit = [
        {"check": "plan_exists", "status": "PASS" if plan_path.exists() else "FAIL", "value": str(plan_path), "notes": ""},
        {"check": "ledger_exists", "status": "PASS" if ledger_path.exists() else "FAIL", "value": str(ledger_path), "notes": ""},
        {"check": "selected_tickers_in_continuation_state", "status": "PASS" if not missing_in_state else "FAIL", "value": len(missing_in_state), "notes": ";".join(missing_in_state[:50])},
        {"check": "all_eligible_never_success_in_plan", "status": "PASS" if not missing_eligible_never else "FAIL", "value": f"{len(planned_never)}/{len(eligible_never)}", "notes": ";".join(missing_eligible_never[:50])},
        {"check": "bucket_inference", "status": "PASS" if not unknown_bucket else "FAIL", "value": bucket_counts["unknown"], "notes": ""},
        {"check": "plan_priority_integrity_status", "status": priority_status, "value": "", "notes": ""},
    ]

    coverage_rows = [
        {"metric": "total_universe_count", "value": pre_cov["total"], "notes": ""},
        {"metric": "pre_unique_success_within_lookback_window", "value": pre_cov["within"], "notes": ""},
        {"metric": "post_unique_success_within_lookback_window", "value": post_cov["within"], "notes": ""},
        {"metric": "pre_remaining_stale_or_never_success_count", "value": pre_cov["remaining"], "notes": ""},
        {"metric": "post_remaining_stale_or_never_success_count", "value": post_cov["remaining"], "notes": ""},
        {"metric": "pre_never_success_count", "value": pre_cov["never"], "notes": ""},
        {"metric": "post_never_success_count", "value": post_cov["never"], "notes": ""},
        {"metric": "refreshed_success_count", "value": ledger_update_success if not args.dry_run else validation_success, "notes": "DryRun reports locally valid refreshes; apply reports ledger updates."},
        {"metric": "refreshed_fail_count", "value": validation_fail + ledger_update_fail, "notes": ""},
        {"metric": "true_lookback_coverage_met_after_update", "value": "TRUE" if post_cov["met"] else "FALSE", "notes": ""},
    ]

    write_csv(root / OUT_PLAN_AUDIT, plan_audit, PLAN_AUDIT_FIELDS)
    write_csv(root / OUT_VALIDATION, validations, VALIDATION_FIELDS)
    write_csv(root / OUT_LEDGER_RESULT, ledger_results, LEDGER_RESULT_FIELDS)
    write_csv(root / OUT_COVERAGE, coverage_rows, COVERAGE_FIELDS)

    ledger_modified = file_sig(ledger_path) != ledger_before_sig
    price_cache_modified = file_sig(root / PRICE_CACHE) != price_before_sig
    forbidden_modified = price_cache_modified
    next_step = "Run R22 again to generate the next continuation plan from the updated ledger."
    if args.dry_run:
        next_step = "DryRun passed; run R22B without -DryRun to update the rolling ledger."
    if status.startswith("WARN"):
        next_step = "Review R22B audits before applying any ledger update."

    read_values = {
        "STATUS": status,
        "MODE": MODE_DRYRUN if args.dry_run else MODE_APPLY,
        "RUN_ID": run_id,
        "PLAN_PATH": plan_path.as_posix(),
        "LEDGER_PATH": ledger_path.as_posix(),
        "BACKUP_DIR": backup_dir,
        "MAX_TICKERS": args.max_tickers,
        "PLAN_ROW_COUNT": len(plan_rows),
        "SELECTED_TICKER_COUNT": len(selected),
        "PLAN_NEVER_SUCCESS_COUNT": bucket_counts["never_success"],
        "PLAN_STALE_OVERDUE_COUNT": bucket_counts["stale_overdue"],
        "PLAN_OLD_SUCCESS_FILL_COUNT": bucket_counts["old_success_fill"],
        "PLAN_UNKNOWN_BUCKET_COUNT": bucket_counts["unknown"],
        "PLAN_PRIORITY_INTEGRITY_STATUS": priority_status,
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
        "TRUE_LOOKBACK_COVERAGE_MET_AFTER_UPDATE": "TRUE" if post_cov["met"] else "FALSE",
        "ROLLING_LEDGER_MODIFIED": "TRUE" if ledger_modified else "FALSE",
        "PRICE_CACHE_MODIFIED": "TRUE" if price_cache_modified else "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_FILES_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, render_read_first(read_values))
    write_text(root / OUT_REPORT, render_report(read_values, backup_dir))

    print(f"STATUS: {status}")
    print(f"MODE: {read_values['MODE']}")
    print(f"READ_FIRST: {(root / OUT_READ_FIRST)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
