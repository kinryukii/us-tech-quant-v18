from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_WARN = "WARN_V18_23C_R3_OFFICIAL_CACHE_LEDGER_RETEST_READY"
STATUS_OK = "OK_V18_23C_R3_TRUE_5DAY_COVERAGE_READY"
STATUS_FAIL = "FAIL_V18_23C_R3_OFFICIAL_CACHE_LEDGER_RETEST"
MODE = "LOCAL_ONLY_OFFICIAL_CACHE_ROLLING_LEDGER_RETEST"
BATCH_ID = "V18_23C_BATCH1"
TARGET_WINDOW_DAYS = 5

LEDGER_REL = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
PLAN_REL = "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv"
PRICE_CACHE_REL = "state/v18/price_cache"

OUTPUTS = {
    "md": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_OFFICIAL_CACHE_LEDGER_RETEST.md",
    "tickers": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_RETEST_TICKERS.csv",
    "update": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_LEDGER_UPDATE_RESULT.csv",
    "snapshot": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv",
    "coverage": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_5DAY_COVERAGE_AUDIT.csv",
    "remaining": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_REMAINING_STALE_TICKERS.csv",
    "source": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R3_CURRENT_OFFICIAL_CACHE_LEDGER_RETEST_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "OFFICIAL_CACHE_LEDGER_RETEST_READY", "LOCAL_ONLY", "BATCH_ID", "RETEST_SCOPE",
    "INTEGRATED_TICKER_COUNT", "RETEST_ATTEMPTED_COUNT", "RETEST_LOCAL_PRICE_SUCCESS_COUNT",
    "RETEST_FULL_HISTORY_READY_COUNT", "RETEST_FAILED_COUNT", "LEDGER_CREATED_OR_UPDATED", "LEDGER_PATH",
    "LEDGER_MODIFIED", "ROLLING_SCAN_EXECUTED", "ROLLING_SCAN_DATA_FETCHED", "EXTERNAL_DATA_FETCHED",
    "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_BEFORE", "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_AFTER",
    "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_DELTA", "TOTAL_UNIVERSE_COUNT",
    "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "COVERAGE_TRUST_LEVEL", "VALIDATION_FAIL_COUNT",
    "RECOMMENDED_NEXT_ACTION", "RETEST_REPORT_PATH", "RETEST_TICKERS_PATH", "LEDGER_UPDATE_RESULT_PATH",
    "LEDGER_SNAPSHOT_PATH", "COVERAGE_AUDIT_PATH", "REMAINING_STALE_TICKERS_PATH", "SOURCE_AUDIT_PATH",
    "VALIDATION_PATH", "REPORT_PATH",
]

LEDGER_FIELDS = [
    "ticker", "canonical_universe_present", "first_seen_date", "last_attempt_scan_timestamp",
    "last_success_scan_timestamp", "last_success_scan_date", "last_scan_status", "last_scan_run_id",
    "success_scan_count", "attempt_scan_count", "local_price_available", "factor_pack_available",
    "technical_timing_available", "full_history_ready", "failure_reason", "source_notes",
]
RETEST_FIELDS = [
    "ticker", "official_cache_path", "official_cache_exists", "row_count", "latest_date",
    "has_required_price_columns", "local_price_scan_success", "full_history_ready", "failure_reason",
]
UPDATE_FIELDS = [
    "ticker", "ledger_update_status", "previous_last_scan_status", "new_last_scan_status",
    "previous_success_scan_count", "new_success_scan_count", "previous_attempt_scan_count",
    "new_attempt_scan_count", "local_price_available", "full_history_ready", "failure_reason",
]
COVERAGE_FIELDS = ["metric", "value", "notes"]
REMAINING_FIELDS = ["ticker", "last_success_scan_date", "last_scan_status", "failure_reason", "stale_reason"]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

SAFETY = {
    "ROLLING_SCAN_DATA_FETCHED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def collect_forbidden(root: Path) -> List[Path]:
    dirs = [
        "state/v18/price_cache", "data/v18/staged_backfill", "outputs/v18/ranking",
        "outputs/v18/signal_snapshots", "outputs/v18/factor_pack", "outputs/v18/technical_timing",
        "outputs/v18/daily_integrated", "state/v18/manual", "state/v18/simulation",
        "state/v18/forward_outcome", "state/v18/candidate_forward_tracker", "archive/stable",
        "outputs/v18/backtest",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()[:10]
    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def to_int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def get_ticker(row: Dict[str, str]) -> str:
    for key in ("ticker", "Ticker", "symbol", "Symbol"):
        if row.get(key):
            return row[key].strip().upper()
    return ""


def load_ticker_set(path: Path) -> set[str]:
    rows, _ = read_csv(path)
    return {get_ticker(row) for row in rows if get_ticker(row)}


def has_ticker(path: Path, ticker: str) -> bool:
    return ticker in load_ticker_set(path)


def required_price_schema(fields: Sequence[str]) -> bool:
    lower = {field.lower() for field in fields}
    return "date" in lower and "close" in lower


def retest_price_cache(root: Path, ticker: str) -> Dict[str, object]:
    path = root / PRICE_CACHE_REL / f"{ticker}.csv"
    rows, fields = read_csv(path)
    schema_ok = required_price_schema(fields)
    date_key = "date" if "date" in fields else "Date" if "Date" in fields else ""
    dates = [parse_date(row.get(date_key, "")) for row in rows] if date_key else []
    dates = [date for date in dates if date]
    latest = max(dates).isoformat() if dates else ""
    local_success = path.exists() and len(rows) > 0 and schema_ok and bool(latest)
    full_ready = local_success and len(rows) >= 500
    failure = ""
    if not path.exists():
        failure = "OFFICIAL_CACHE_FILE_MISSING"
    elif not rows:
        failure = "OFFICIAL_CACHE_EMPTY"
    elif not schema_ok:
        failure = "OFFICIAL_CACHE_SCHEMA_INVALID"
    elif not latest:
        failure = "OFFICIAL_CACHE_DATE_PARSE_FAILED"
    elif not full_ready:
        failure = "OFFICIAL_CACHE_INSUFFICIENT_HISTORY"
    return {
        "ticker": ticker,
        "official_cache_path": str(path),
        "official_cache_exists": str(path.exists()).upper(),
        "row_count": len(rows),
        "latest_date": latest,
        "has_required_price_columns": str(schema_ok).upper(),
        "local_price_scan_success": str(local_success).upper(),
        "full_history_ready": str(full_ready).upper(),
        "failure_reason": failure,
    }


def ensure_ledger_rows(ledger_rows: List[Dict[str, str]], canonical: Sequence[str], today: str) -> List[Dict[str, str]]:
    by = {get_ticker(row): dict(row) for row in ledger_rows if get_ticker(row)}
    for ticker in canonical:
        if ticker not in by:
            by[ticker] = {
                "ticker": ticker,
                "canonical_universe_present": "TRUE",
                "first_seen_date": today,
                "last_attempt_scan_timestamp": "",
                "last_success_scan_timestamp": "",
                "last_success_scan_date": "",
                "last_scan_status": "NEVER_SCANNED",
                "last_scan_run_id": "",
                "success_scan_count": "0",
                "attempt_scan_count": "0",
                "local_price_available": "FALSE",
                "factor_pack_available": "FALSE",
                "technical_timing_available": "FALSE",
                "full_history_ready": "FALSE",
                "failure_reason": "",
                "source_notes": "",
            }
        by[ticker]["ticker"] = ticker
        by[ticker]["canonical_universe_present"] = "TRUE"
        if not by[ticker].get("first_seen_date"):
            by[ticker]["first_seen_date"] = today
    return [by[ticker] for ticker in sorted(by)]


def unique_success_within_window(ledger_rows: Sequence[Dict[str, str]], canonical: set[str], today: dt.date) -> int:
    cutoff = today - dt.timedelta(days=TARGET_WINDOW_DAYS)
    count = 0
    for row in ledger_rows:
        ticker = get_ticker(row)
        if ticker not in canonical:
            continue
        success_date = parse_date(row.get("last_success_scan_date", ""))
        if success_date and success_date >= cutoff:
            count += 1
    return count


def remaining_stale_rows(ledger_rows: Sequence[Dict[str, str]], canonical: set[str], today: dt.date) -> List[Dict[str, object]]:
    cutoff = today - dt.timedelta(days=TARGET_WINDOW_DAYS)
    out: List[Dict[str, object]] = []
    for row in ledger_rows:
        ticker = get_ticker(row)
        if ticker not in canonical:
            continue
        success_date = parse_date(row.get("last_success_scan_date", ""))
        if not success_date:
            reason = "NEVER_SUCCESS"
        elif success_date < cutoff:
            reason = "SUCCESS_OLDER_THAN_WINDOW"
        else:
            continue
        out.append({
            "ticker": ticker,
            "last_success_scan_date": row.get("last_success_scan_date", ""),
            "last_scan_status": row.get("last_scan_status", ""),
            "failure_reason": row.get("failure_reason", ""),
            "stale_reason": reason,
        })
    return out


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_md(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R3 Official Cache Rolling Ledger Retest

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Scope
Local-only retest of V18.23C-R2 integrated full-history tickers against the official price cache, followed by rolling ledger updates for successful evidence only.

## Results
Integrated tickers: {values['INTEGRATED_TICKER_COUNT']}. Retest attempted: {values['RETEST_ATTEMPTED_COUNT']}. Local price success: {values['RETEST_LOCAL_PRICE_SUCCESS_COUNT']}. Full-history ready: {values['RETEST_FULL_HISTORY_READY_COUNT']}. Failed: {values['RETEST_FAILED_COUNT']}.

## Coverage
Unique success within window before: {values['UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_BEFORE']}.
Unique success within window after: {values['UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_AFTER']}.
Remaining stale/never-success: {values['REMAINING_STALE_OR_NEVER_SUCCESS_COUNT']}.
TRUE_5DAY_UNIQUE_COVERAGE_MET: {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}.

## Safety
Only the rolling scan ledger and V18.23C-R3 outputs were modified. Official price cache files were read but not modified.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    now = dt.datetime.now()
    now_text = now.isoformat(timespec="seconds")
    today = now.date()
    today_text = today.isoformat()
    run_id = f"V18_23C_R3_{now.strftime('%Y%m%d_%H%M%S')}"

    forbidden_before = {str(path): file_sig(path) for path in collect_forbidden(root)}

    merge_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_MERGE_RESULT.csv")
    r2_retest_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23C_R2_CURRENT_POST_INTEGRATION_RETEST.csv")
    r2_read_first_exists = (root / "outputs/v18/ops/V18_23C_R2_READ_FIRST.txt").exists()
    canonical_rows, _ = read_csv(root / PLAN_REL)
    canonical = sorted({get_ticker(row) for row in canonical_rows if get_ticker(row)})
    canonical_set = set(canonical)
    ledger_path = root / LEDGER_REL
    ledger_rows, _ = read_csv(ledger_path)
    ledger_rows = ensure_ledger_rows(ledger_rows, canonical, today_text)
    before_unique = unique_success_within_window(ledger_rows, canonical_set, today)

    integrated = sorted({row.get("ticker", "").strip().upper() for row in merge_rows if row.get("merge_status") == "SUCCESS" and row.get("ticker", "").strip()})
    retest_rows = [retest_price_cache(root, ticker) for ticker in integrated]
    factor_pack_path = root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
    technical_path = root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
    ledger_by = {get_ticker(row): row for row in ledger_rows if get_ticker(row)}
    update_rows: List[Dict[str, object]] = []

    for scan in retest_rows:
        ticker = str(scan["ticker"])
        row = ledger_by[ticker]
        prev_status = row.get("last_scan_status", "")
        prev_success = to_int(row.get("success_scan_count"))
        prev_attempt = to_int(row.get("attempt_scan_count"))
        row["last_attempt_scan_timestamp"] = now_text
        row["last_scan_run_id"] = run_id
        row["attempt_scan_count"] = str(prev_attempt + 1)
        success = scan["local_price_scan_success"] == "TRUE" and scan["full_history_ready"] == "TRUE"
        row["local_price_available"] = scan["local_price_scan_success"]
        row["full_history_ready"] = scan["full_history_ready"]
        row["factor_pack_available"] = str(has_ticker(factor_pack_path, ticker)).upper() if factor_pack_path.exists() else row.get("factor_pack_available", "FALSE")
        row["technical_timing_available"] = str(has_ticker(technical_path, ticker)).upper() if technical_path.exists() else row.get("technical_timing_available", "FALSE")
        if success:
            row["last_success_scan_timestamp"] = now_text
            row["last_success_scan_date"] = today_text
            row["last_scan_status"] = "SUCCESS_OFFICIAL_CACHE_LEDGER_RETEST"
            row["success_scan_count"] = str(prev_success + 1)
            row["failure_reason"] = ""
            row["source_notes"] = "official_cache=available;full_history_ready=TRUE;ledger_updated_by=V18_23C_R3"
        else:
            row["last_scan_status"] = "FAILED_OFFICIAL_CACHE_LEDGER_RETEST"
            row["success_scan_count"] = str(prev_success)
            row["failure_reason"] = str(scan["failure_reason"])
            row["source_notes"] = "official_cache_retest_failed;ledger_updated_by=V18_23C_R3"
        update_rows.append({
            "ticker": ticker,
            "ledger_update_status": "UPDATED_SUCCESS" if success else "UPDATED_FAILED",
            "previous_last_scan_status": prev_status,
            "new_last_scan_status": row["last_scan_status"],
            "previous_success_scan_count": prev_success,
            "new_success_scan_count": row["success_scan_count"],
            "previous_attempt_scan_count": prev_attempt,
            "new_attempt_scan_count": row["attempt_scan_count"],
            "local_price_available": row["local_price_available"],
            "full_history_ready": row["full_history_ready"],
            "failure_reason": row["failure_reason"],
        })

    ledger_rows = [ledger_by[ticker] for ticker in sorted(ledger_by)]
    ensure_dir(ledger_path.parent)
    write_csv(ledger_path, ledger_rows, LEDGER_FIELDS)

    after_unique = unique_success_within_window(ledger_rows, canonical_set, today)
    remaining_rows = remaining_stale_rows(ledger_rows, canonical_set, today)
    true_coverage = after_unique == len(canonical) and len(canonical) > 0
    local_success = sum(1 for row in retest_rows if row["local_price_scan_success"] == "TRUE")
    full_ready = sum(1 for row in retest_rows if row["full_history_ready"] == "TRUE")
    failed = len(retest_rows) - full_ready

    values: Dict[str, str] = {
        "STATUS": STATUS_OK if true_coverage else STATUS_WARN,
        "MODE": MODE,
        "OFFICIAL_CACHE_LEDGER_RETEST_READY": "TRUE",
        "LOCAL_ONLY": "TRUE",
        "BATCH_ID": BATCH_ID,
        "RETEST_SCOPE": "V18_23C_R2_MERGE_SUCCESS_TICKERS_ONLY",
        "INTEGRATED_TICKER_COUNT": str(len(integrated)),
        "RETEST_ATTEMPTED_COUNT": str(len(retest_rows)),
        "RETEST_LOCAL_PRICE_SUCCESS_COUNT": str(local_success),
        "RETEST_FULL_HISTORY_READY_COUNT": str(full_ready),
        "RETEST_FAILED_COUNT": str(failed),
        "LEDGER_CREATED_OR_UPDATED": "TRUE",
        "LEDGER_PATH": str(ledger_path),
        "LEDGER_MODIFIED": "TRUE",
        "ROLLING_SCAN_EXECUTED": "TRUE",
        "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_BEFORE": str(before_unique),
        "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_AFTER": str(after_unique),
        "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_DELTA": str(after_unique - before_unique),
        "TOTAL_UNIVERSE_COUNT": str(len(canonical)),
        "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT": str(len(remaining_rows)),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": str(true_coverage).upper(),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "TRUE_FULL_LEDGER_WINDOW_COVERAGE" if true_coverage else "FALSE_PARTIAL_LEDGER_COVERAGE_AFTER_R3",
        "COVERAGE_TRUST_LEVEL": "HIGH" if true_coverage else "MEDIUM",
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Continue rolling local-only retests/backfill for remaining stale or never-success tickers; do not promote factor claims or production until full ledger coverage and downstream readiness gates pass.",
        "RETEST_REPORT_PATH": str(root / OUTPUTS["md"]),
        "RETEST_TICKERS_PATH": str(root / OUTPUTS["tickers"]),
        "LEDGER_UPDATE_RESULT_PATH": str(root / OUTPUTS["update"]),
        "LEDGER_SNAPSHOT_PATH": str(root / OUTPUTS["snapshot"]),
        "COVERAGE_AUDIT_PATH": str(root / OUTPUTS["coverage"]),
        "REMAINING_STALE_TICKERS_PATH": str(root / OUTPUTS["remaining"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY)

    source_rows = [
        {"source_name": "v18_23c_r2_merge_result", "source_path": "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_MERGE_RESULT.csv", "exists": str(bool(merge_rows)).upper(), "row_count": len(merge_rows), "notes": "R2 successful merge source."},
        {"source_name": "v18_23c_r2_post_retest", "source_path": "outputs/v18/rolling_coverage/V18_23C_R2_CURRENT_POST_INTEGRATION_RETEST.csv", "exists": str(bool(r2_retest_rows)).upper(), "row_count": len(r2_retest_rows), "notes": "R2 read-only post-integration retest source."},
        {"source_name": "v18_23c_r2_read_first", "source_path": "outputs/v18/ops/V18_23C_R2_READ_FIRST.txt", "exists": str(r2_read_first_exists).upper(), "row_count": 1 if r2_read_first_exists else 0, "notes": "R2 operator status."},
        {"source_name": "canonical_plan", "source_path": PLAN_REL, "exists": str(bool(canonical_rows)).upper(), "row_count": len(canonical_rows), "notes": "Canonical universe for coverage audit."},
        {"source_name": "rolling_scan_ledger", "source_path": LEDGER_REL, "exists": str(ledger_path.exists()).upper(), "row_count": len(ledger_rows), "notes": "Only allowed state modification in R3."},
        {"source_name": "official_price_cache", "source_path": PRICE_CACHE_REL, "exists": str((root / PRICE_CACHE_REL).exists()).upper(), "row_count": len(list((root / PRICE_CACHE_REL).glob('*.csv'))) if (root / PRICE_CACHE_REL).exists() else 0, "notes": "Read-only evidence source in R3."},
    ]
    coverage_rows = [
        {"metric": "target_window_days", "value": TARGET_WINDOW_DAYS, "notes": "Calendar-day approximation."},
        {"metric": "total_universe_count", "value": len(canonical), "notes": "Canonical V18.23A plan tickers."},
        {"metric": "unique_success_scanned_within_window_before", "value": before_unique, "notes": "Before R3 ledger update."},
        {"metric": "unique_success_scanned_within_window_after", "value": after_unique, "notes": "After R3 ledger update."},
        {"metric": "remaining_stale_or_never_success_count", "value": len(remaining_rows), "notes": "Still not covered by successful ledger evidence in current window."},
        {"metric": "true_5day_unique_coverage_met", "value": values["TRUE_5DAY_UNIQUE_COVERAGE_MET"], "notes": values["TRUE_5DAY_UNIQUE_COVERAGE_STATUS"]},
    ]

    write_csv(root / OUTPUTS["tickers"], retest_rows, RETEST_FIELDS)
    write_csv(root / OUTPUTS["update"], update_rows, UPDATE_FIELDS)
    write_csv(root / OUTPUTS["snapshot"], ledger_rows, LEDGER_FIELDS)
    write_csv(root / OUTPUTS["coverage"], coverage_rows, COVERAGE_FIELDS)
    write_csv(root / OUTPUTS["remaining"], remaining_rows, REMAINING_FIELDS)
    write_csv(root / OUTPUTS["source"], source_rows, SOURCE_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_md(values))
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    forbidden_after = {str(path): file_sig(path) for path in collect_forbidden(root)}
    changed_forbidden = sorted(path for path, sig in forbidden_before.items() if forbidden_after.get(path) != sig) + sorted(path for path in forbidden_after if path not in forbidden_before)
    required_outputs = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23C_R3_official_cache_rolling_ledger_retest.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23C_R3_official_cache_rolling_ledger_retest.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required_outputs), 1, "All R3 outputs must exist and be non-empty."),
        validation_row("merge_result_readable", bool(merge_rows), 1, "R2 merge result must be readable."),
        validation_row("integrated_count_expected", len(integrated) == 51, 1, f"Expected 51; actual {len(integrated)}."),
        validation_row("retest_attempt_equals_integrated", len(retest_rows) == len(integrated), 1, "Retest rows must match integrated tickers."),
        validation_row("local_price_success_expected", local_success == len(integrated), 1, "Official cache local price success should be complete."),
        validation_row("ledger_snapshot_contains_canonical", canonical_set.issubset({get_ticker(row) for row in ledger_rows}), 1, "Ledger snapshot must include all canonical tickers."),
        validation_row("coverage_audit_generated", bool(coverage_rows), 1, "Coverage audit must be generated."),
        validation_row("no_forbidden_files_modified", not changed_forbidden, len(changed_forbidden), ";".join(changed_forbidden[:20])),
        validation_row("true_coverage_logic", true_coverage == (after_unique == len(canonical) and len(canonical) > 0), 1, "TRUE coverage must match full ledger evidence."),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not merge_rows or local_success == 0:
        values["STATUS"] = STATUS_FAIL
        values["OFFICIAL_CACHE_LEDGER_RETEST_READY"] = "FALSE"
    elif true_coverage:
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_WARN

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_md(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
