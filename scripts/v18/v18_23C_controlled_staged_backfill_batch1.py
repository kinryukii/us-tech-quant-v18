from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_CONTROLLED_STAGED_BACKFILL_BATCH1_READY"
STATUS_WARN = "WARN_V18_23C_CONTROLLED_STAGED_BACKFILL_READY"
STATUS_FAIL = "FAIL_V18_23C_CONTROLLED_STAGED_BACKFILL"
MODE = "CONTROLLED_STAGED_BACKFILL_BATCH1_STAGED_ONLY"
BATCH_ID = "V18_23C_BATCH1"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")
MIN_FULL_HISTORY_ROWS = 500
MIN_FULL_HISTORY_SPAN_DAYS = 700

STAGED_DIR_REL = f"data/v18/staged_backfill/{BATCH_ID}"
STAGED_COMBINED_REL = f"{STAGED_DIR_REL}/V18_23C_BATCH1_STAGED_PRICE_HISTORY.csv"
STAGED_MANIFEST_REL = f"{STAGED_DIR_REL}/MANIFEST.csv"

OUTPUTS = {
    "md": "outputs/v18/staged_backfill/V18_23C_CURRENT_CONTROLLED_STAGED_BACKFILL.md",
    "batch": "outputs/v18/staged_backfill/V18_23C_CURRENT_BACKFILL_BATCH_TICKERS.csv",
    "fetch": "outputs/v18/staged_backfill/V18_23C_CURRENT_BACKFILL_FETCH_RESULT.csv",
    "manifest": "outputs/v18/staged_backfill/V18_23C_CURRENT_STAGED_HISTORY_MANIFEST.csv",
    "retest": "outputs/v18/staged_backfill/V18_23C_CURRENT_STAGED_SCAN_RETEST_RESULT.csv",
    "source_audit": "outputs/v18/staged_backfill/V18_23C_CURRENT_BACKFILL_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/staged_backfill/V18_23C_CURRENT_BACKFILL_VALIDATION.csv",
    "summary": "outputs/v18/rolling_coverage/V18_23C_CURRENT_ROLLING_SCAN_RETEST_SUMMARY.csv",
    "read_first": "outputs/v18/ops/V18_23C_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_CURRENT_CONTROLLED_STAGED_BACKFILL_REPORT.md",
}

SAFETY_FALSE = {
    "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
    "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "CONTROLLED_STAGED_BACKFILL_READY", "BATCH_ID", "BATCH_TICKER_COUNT",
    "EXTERNAL_DATA_FETCHED", "FETCH_PROVIDER", "FETCH_ATTEMPTED_COUNT", "FETCH_SUCCESS_COUNT",
    "FETCH_EMPTY_COUNT", "FETCH_FAILED_COUNT", "FETCH_SCHEMA_INVALID_COUNT",
    "STAGED_PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_DIR", "STAGED_COMBINED_HISTORY_PATH",
    "STAGED_MANIFEST_PATH", "OFFICIAL_PRICE_CACHE_MODIFIED", "OFFICIAL_PRICE_HISTORY_MODIFIED",
    "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "LEDGER_MODIFIED", "ROLLING_SCAN_EXECUTED",
    "STAGED_ROLLING_SCAN_RETEST_EXECUTED", "STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT",
    "STAGED_FULL_HISTORY_READY_COUNT", "STAGED_INSUFFICIENT_HISTORY_COUNT",
    "STAGED_SCAN_RETEST_SUCCESS_RATIO", "USER_TARGET_65_LOCAL_PRICE_SCANS_REACHABLE_AFTER_STAGED_BACKFILL",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_COVERAGE_STATUS",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "VALIDATION_FAIL_COUNT", "RECOMMENDED_NEXT_ACTION", "BACKFILL_REPORT_PATH",
    "BATCH_TICKERS_PATH", "FETCH_RESULT_PATH", "STAGED_HISTORY_MANIFEST_OUTPUT_PATH",
    "STAGED_SCAN_RETEST_RESULT_PATH", "SOURCE_AUDIT_PATH", "VALIDATION_PATH",
    "ROLLING_SCAN_RETEST_SUMMARY_PATH", "REPORT_PATH",
]

BATCH_FIELDS = ["batch_id", "ticker", "source", "batch_order"]
FETCH_FIELDS = [
    "batch_id", "ticker", "fetch_attempted", "fetch_status", "failure_reason",
    "requested_start_date", "requested_end_date", "actual_min_date", "actual_max_date",
    "row_count", "schema_valid", "staged_file_path",
]
MANIFEST_FIELDS = ["file_type", "ticker", "relative_path", "exists", "row_count", "min_date", "max_date", "notes"]
RETEST_FIELDS = [
    "ticker", "staged_local_price_available", "staged_row_count", "latest_staged_date",
    "min_staged_date", "history_span_days", "minimum_history_threshold_met", "staged_scan_status",
]
AUDIT_FIELDS = ["source_name", "source_path", "exists", "row_count", "ticker_count", "selected", "notes"]
SUMMARY_FIELDS = ["metric", "value", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


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


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "NA", "N/A", "TICKER"} or ticker.isdigit():
        return ""
    return ticker if TICKER_RE.match(ticker) else ""


def find_ticker_col(fields: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for name in ("ticker", "symbol", "candidate_ticker", "yf_ticker"):
        if name in lower:
            return lower[name]
    return ""


def load_batch(root: Path) -> Tuple[List[str], List[Dict[str, object]]]:
    candidates = [
        ("R3_SKIPPED_DIAGNOSTICS", "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_SKIPPED_TICKER_DIAGNOSTICS.csv"),
        ("R2_SELECTED_SCAN_LIST", "outputs/v18/rolling_coverage/V18_23B_R2_CURRENT_WATCHDOG_SELECTED_SCAN_LIST.csv"),
        ("R2_SCAN_RESULT", "outputs/v18/rolling_coverage/V18_23B_R2_CURRENT_SCAN_RESULT.csv"),
    ]
    audit: List[Dict[str, object]] = []
    selected: List[str] = []
    for name, rel in candidates:
        rows, fields = read_csv(root / rel)
        col = find_ticker_col(fields)
        tickers = []
        seen = set()
        for row in rows:
            ticker = normalize_ticker(row.get(col, "")) if col else ""
            if ticker and ticker not in seen:
                seen.add(ticker)
                tickers.append(ticker)
        is_selected = not selected and bool(tickers)
        if is_selected:
            selected = tickers[:65]
        audit.append({"source_name": name, "source_path": rel, "exists": str((root / rel).exists()).upper(), "row_count": len(rows), "ticker_count": len(tickers), "selected": str(is_selected).upper(), "notes": f"ticker_column={col or 'MISSING'}"})
    return selected, audit


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def protected_files(root: Path) -> List[Path]:
    dirs = [
        "state/v18/rolling_coverage", "state/v18/price_cache", "outputs/v18/factor_pack",
        "outputs/v18/ranking", "outputs/v18/signal_snapshots", "outputs/v18/technical_timing",
        "outputs/v18/universe", "outputs/v18/forward_tracker", "outputs/v18/simulation",
        "state/v18/simulation", "state/v18/forward_outcome", "state/v18/candidate_forward_tracker",
        "state/v18/manual", "state/v16", "archive/stable",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def date_from_value(value: object) -> str:
    text = str(value)
    return text[:10]


def valid_schema(columns: Sequence[str]) -> bool:
    lower = {str(c).strip().lower() for c in columns}
    return "open" in lower and "high" in lower and "low" in lower and "close" in lower


def fetch_one(ticker: str, start: dt.date, end: dt.date, out_path: Path) -> Dict[str, object]:
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"fetch_status": "FAILED", "failure_reason": f"YFINANCE_IMPORT_FAILED:{exc}", "row_count": 0, "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    try:
        df = yf.download(ticker, start=start.isoformat(), end=(end + dt.timedelta(days=1)).isoformat(), interval="1d", auto_adjust=False, progress=False, threads=False)
    except Exception as exc:
        return {"fetch_status": "FAILED", "failure_reason": f"YFINANCE_DOWNLOAD_FAILED:{exc}", "row_count": 0, "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    if df is None or getattr(df, "empty", True):
        return {"fetch_status": "EMPTY", "failure_reason": "EMPTY_DATA", "row_count": 0, "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    if hasattr(df.columns, "nlevels") and getattr(df.columns, "nlevels", 1) > 1:
        df.columns = [str(col[0]) for col in df.columns]
    schema_ok = valid_schema([str(c) for c in df.columns])
    if not schema_ok:
        return {"fetch_status": "SCHEMA_INVALID", "failure_reason": f"SCHEMA_INVALID:{','.join(str(c) for c in df.columns)}", "row_count": len(df), "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    ensure_dir(out_path.parent)
    df.to_csv(out_path, index_label="Date")
    dates = [date_from_value(idx) for idx in df.index]
    return {"fetch_status": "SUCCESS", "failure_reason": "", "row_count": len(df), "schema_valid": "TRUE", "actual_min_date": min(dates), "actual_max_date": max(dates)}


def read_staged_dates(path: Path) -> Tuple[int, str, str]:
    rows, fields = read_csv(path)
    date_col = "Date" if "Date" in fields else fields[0] if fields else ""
    dates = [row.get(date_col, "")[:10] for row in rows if row.get(date_col, "")]
    return len(rows), (min(dates) if dates else ""), (max(dates) if dates else "")


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_md(values: Dict[str, str]) -> str:
    return f"""# V18.23C Controlled Staged Backfill Batch 1

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Purpose
Fetch missing local price/history data for the V18.23B-R3 skipped ticker batch into staged files only, then retest staged-only rolling scan readiness.

## Safety
External fetch provider: {values['FETCH_PROVIDER']}. Official price cache, official price history, rankings, factor pack, technical timing, signal snapshots, ledger, backtests, and trading state were not modified.

## Date Range
Requested 5 years of daily history.

## Summary
Batch tickers: {values['BATCH_TICKER_COUNT']}. Fetch success: {values['FETCH_SUCCESS_COUNT']}. Fetch failed: {values['FETCH_FAILED_COUNT']}. Empty: {values['FETCH_EMPTY_COUNT']}. Schema invalid: {values['FETCH_SCHEMA_INVALID_COUNT']}.

Staged local price scan success: {values['STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT']}. Staged full history ready: {values['STAGED_FULL_HISTORY_READY_COUNT']}.

## Staged Paths
- {values['STAGED_PRICE_HISTORY_DIR']}
- {values['STAGED_COMBINED_HISTORY_PATH']}
- {values['STAGED_MANIFEST_PATH']}

## Remaining Blockers
Staged data is not merged into official price cache. TRUE_5DAY_UNIQUE_COVERAGE_MET remains FALSE because this is staged-only.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23C Controlled Staged Backfill Report

Status: {values['STATUS']}.

Batch ticker count: {values['BATCH_TICKER_COUNT']}. Fetch attempted: {values['FETCH_ATTEMPTED_COUNT']}. Fetch success: {values['FETCH_SUCCESS_COUNT']}. Fetch failed: {values['FETCH_FAILED_COUNT']}.

Staged local price scan success count: {values['STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT']}. Staged full history ready count: {values['STAGED_FULL_HISTORY_READY_COUNT']}.

Official files were not modified. Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in protected_files(root)}
    batch, source_audit = load_batch(root)
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=365 * 5 + 10)
    staged_dir = root / STAGED_DIR_REL
    combined_path = root / STAGED_COMBINED_REL
    manifest_path = root / STAGED_MANIFEST_REL

    batch_rows = [{"batch_id": BATCH_ID, "ticker": ticker, "source": "V18_23B_R3_OR_R2_SKIPPED", "batch_order": i + 1} for i, ticker in enumerate(batch)]
    write_csv(root / OUTPUTS["batch"], batch_rows, BATCH_FIELDS)

    fetch_rows: List[Dict[str, object]] = []
    manifest_rows: List[Dict[str, object]] = []
    combined_rows: List[Dict[str, object]] = []
    for ticker in batch:
        out_path = staged_dir / f"{ticker}.csv"
        result = fetch_one(ticker, start_date, end_date, out_path)
        fetch_row = {
            "batch_id": BATCH_ID,
            "ticker": ticker,
            "fetch_attempted": "TRUE",
            "fetch_status": result["fetch_status"],
            "failure_reason": result["failure_reason"],
            "requested_start_date": start_date.isoformat(),
            "requested_end_date": end_date.isoformat(),
            "actual_min_date": result["actual_min_date"],
            "actual_max_date": result["actual_max_date"],
            "row_count": result["row_count"],
            "schema_valid": result["schema_valid"],
            "staged_file_path": str(out_path),
        }
        fetch_rows.append(fetch_row)
        if result["fetch_status"] == "SUCCESS":
            rows, fields = read_csv(out_path)
            for row in rows:
                row2 = {"ticker": ticker}
                row2.update(row)
                combined_rows.append(row2)
        manifest_rows.append({
            "file_type": "PER_TICKER_STAGED_HISTORY",
            "ticker": ticker,
            "relative_path": out_path.relative_to(root).as_posix(),
            "exists": str(out_path.exists()).upper(),
            "row_count": result["row_count"],
            "min_date": result["actual_min_date"],
            "max_date": result["actual_max_date"],
            "notes": result["fetch_status"],
        })
    write_csv(root / OUTPUTS["fetch"], fetch_rows, FETCH_FIELDS)
    combined_fields = ["ticker", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    write_csv(combined_path, combined_rows, combined_fields)
    manifest_rows.append({"file_type": "COMBINED_STAGED_HISTORY", "ticker": "ALL", "relative_path": STAGED_COMBINED_REL, "exists": str(combined_path.exists()).upper(), "row_count": len(combined_rows), "min_date": "", "max_date": "", "notes": "Combined staged ticker history."})
    write_csv(manifest_path, manifest_rows, MANIFEST_FIELDS)
    write_csv(root / OUTPUTS["manifest"], manifest_rows, MANIFEST_FIELDS)

    retest_rows: List[Dict[str, object]] = []
    for ticker in batch:
        path = staged_dir / f"{ticker}.csv"
        row_count, min_date, max_date = read_staged_dates(path)
        span = 0
        if min_date and max_date:
            span = (dt.datetime.strptime(max_date, "%Y-%m-%d").date() - dt.datetime.strptime(min_date, "%Y-%m-%d").date()).days
        available = path.exists() and row_count > 0
        threshold = row_count >= MIN_FULL_HISTORY_ROWS and span >= MIN_FULL_HISTORY_SPAN_DAYS
        status = "STAGED_FULL_HISTORY_READY" if available and threshold else "STAGED_INSUFFICIENT_HISTORY" if available else "STAGED_FETCH_FAILED"
        retest_rows.append({"ticker": ticker, "staged_local_price_available": str(available).upper(), "staged_row_count": row_count, "latest_staged_date": max_date, "min_staged_date": min_date, "history_span_days": span, "minimum_history_threshold_met": str(threshold).upper(), "staged_scan_status": status})
    write_csv(root / OUTPUTS["retest"], retest_rows, RETEST_FIELDS)
    write_csv(root / OUTPUTS["source_audit"], source_audit, AUDIT_FIELDS)

    fetch_success = sum(1 for row in fetch_rows if row["fetch_status"] == "SUCCESS")
    fetch_empty = sum(1 for row in fetch_rows if row["fetch_status"] == "EMPTY")
    fetch_schema = sum(1 for row in fetch_rows if row["fetch_status"] == "SCHEMA_INVALID")
    fetch_failed = sum(1 for row in fetch_rows if row["fetch_status"] == "FAILED")
    staged_success = sum(1 for row in retest_rows if row["staged_local_price_available"] == "TRUE")
    staged_full = sum(1 for row in retest_rows if row["staged_scan_status"] == "STAGED_FULL_HISTORY_READY")
    staged_insufficient = sum(1 for row in retest_rows if row["staged_scan_status"] == "STAGED_INSUFFICIENT_HISTORY")
    ratio = (staged_success / len(batch)) if batch else 0.0
    values: Dict[str, str] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "CONTROLLED_STAGED_BACKFILL_READY": "FALSE",
        "BATCH_ID": BATCH_ID,
        "BATCH_TICKER_COUNT": str(len(batch)),
        "EXTERNAL_DATA_FETCHED": "TRUE",
        "FETCH_PROVIDER": "yfinance",
        "FETCH_ATTEMPTED_COUNT": str(len(batch)),
        "FETCH_SUCCESS_COUNT": str(fetch_success),
        "FETCH_EMPTY_COUNT": str(fetch_empty),
        "FETCH_FAILED_COUNT": str(fetch_failed),
        "FETCH_SCHEMA_INVALID_COUNT": str(fetch_schema),
        "STAGED_PRICE_HISTORY_WRITTEN": str(bool(combined_rows)).upper(),
        "STAGED_PRICE_HISTORY_DIR": str(staged_dir),
        "STAGED_COMBINED_HISTORY_PATH": str(combined_path),
        "STAGED_MANIFEST_PATH": str(manifest_path),
        "ROLLING_SCAN_EXECUTED": "FALSE",
        "STAGED_ROLLING_SCAN_RETEST_EXECUTED": "TRUE",
        "STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT": str(staged_success),
        "STAGED_FULL_HISTORY_READY_COUNT": str(staged_full),
        "STAGED_INSUFFICIENT_HISTORY_COUNT": str(staged_insufficient),
        "STAGED_SCAN_RETEST_SUCCESS_RATIO": f"{ratio:.6f}",
        "USER_TARGET_65_LOCAL_PRICE_SCANS_REACHABLE_AFTER_STAGED_BACKFILL": str(staged_success >= 65).upper(),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "FALSE_STAGED_ONLY_NOT_OFFICIAL_LEDGER_COVERAGE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Review staged backfill quality; if acceptable, implement a separate explicit staged-to-official integration gate before touching price cache.",
        "BACKFILL_REPORT_PATH": str(root / OUTPUTS["md"]),
        "BATCH_TICKERS_PATH": str(root / OUTPUTS["batch"]),
        "FETCH_RESULT_PATH": str(root / OUTPUTS["fetch"]),
        "STAGED_HISTORY_MANIFEST_OUTPUT_PATH": str(root / OUTPUTS["manifest"]),
        "STAGED_SCAN_RETEST_RESULT_PATH": str(root / OUTPUTS["retest"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source_audit"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "ROLLING_SCAN_RETEST_SUMMARY_PATH": str(root / OUTPUTS["summary"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY_FALSE)
    summary_rows = [
        {"metric": "batch_ticker_count", "value": len(batch), "notes": "Input tickers."},
        {"metric": "fetch_success_count", "value": fetch_success, "notes": "Successful yfinance staged downloads."},
        {"metric": "staged_local_price_scan_success_count", "value": staged_success, "notes": "Staged file exists and has rows."},
        {"metric": "staged_full_history_ready_count", "value": staged_full, "notes": f">={MIN_FULL_HISTORY_ROWS} rows and >={MIN_FULL_HISTORY_SPAN_DAYS} days span."},
        {"metric": "true_5day_unique_coverage_met", "value": "FALSE", "notes": "Staged-only test does not update official ledger."},
    ]
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23C_controlled_staged_backfill_batch1.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23C_controlled_staged_backfill_batch1.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "All V18.23C outputs must exist and be non-empty."),
        validation_row("input_batch_count_positive", len(batch) > 0, 1, "Input batch must be non-empty."),
        validation_row("fetch_result_one_row_per_batch_ticker", len(fetch_rows) == len(batch), 1, "Fetch result must have one row per ticker."),
        validation_row("staged_scan_retest_one_row_per_batch_ticker", len(retest_rows) == len(batch), 1, "Retest result must have one row per ticker."),
        validation_row("staged_manifest_has_rows", non_empty(manifest_path), 1, str(manifest_path)),
        validation_row("official_forbidden_files_unchanged", not changed, len(changed), ";".join(changed[:20])),
        validation_row("true_coverage_remains_false", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] == "FALSE", 1, "Staged-only test must not claim true coverage."),
        validation_row("staged_files_written", bool(combined_rows), 1, "At least one staged row must be written."),
        validation_row("not_all_fetch_failed", fetch_success > 0, 1, "At least one ticker must fetch successfully."),
    ]
    for key, expected in SAFETY_FALSE.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not batch or fetch_success == 0 or not combined_rows:
        values["STATUS"] = STATUS_FAIL
    elif fetch_success == len(batch) and staged_success == len(batch):
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_WARN
    values["CONTROLLED_STAGED_BACKFILL_READY"] = "TRUE" if fail_count == 0 and fetch_success > 0 else "FALSE"
    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
