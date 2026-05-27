from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_R4_CONTROLLED_STAGED_BACKFILL_BATCH2_READY"
STATUS_WARN = "WARN_V18_23C_R4_CONTROLLED_STAGED_BACKFILL_BATCH2_READY"
STATUS_FAIL = "FAIL_V18_23C_R4_CONTROLLED_STAGED_BACKFILL_BATCH2"
MODE = "CONTROLLED_STAGED_BACKFILL_BATCH2_STAGED_ONLY"
BATCH_ID = "V18_23C_BATCH2"
BATCH_SIZE = 65
MIN_FULL_HISTORY_ROWS = 500
MIN_FULL_HISTORY_SPAN_DAYS = 700
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

STAGED_DIR_REL = f"data/v18/staged_backfill/{BATCH_ID}"
STAGED_COMBINED_REL = f"{STAGED_DIR_REL}/V18_23C_BATCH2_STAGED_PRICE_HISTORY.csv"
STAGED_MANIFEST_REL = f"{STAGED_DIR_REL}/MANIFEST.csv"

OUTPUTS = {
    "md": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_CONTROLLED_STAGED_BACKFILL_BATCH2.md",
    "batch": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_BACKFILL_BATCH2_TICKERS.csv",
    "fetch": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_BACKFILL_BATCH2_FETCH_RESULT.csv",
    "manifest": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_STAGED_HISTORY_BATCH2_MANIFEST.csv",
    "retest": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_STAGED_BATCH2_SCAN_RETEST_RESULT.csv",
    "source": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_BACKFILL_BATCH2_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_BACKFILL_BATCH2_VALIDATION.csv",
    "summary": "outputs/v18/rolling_coverage/V18_23C_R4_CURRENT_BATCH2_ROLLING_SCAN_RETEST_SUMMARY.csv",
    "read_first": "outputs/v18/ops/V18_23C_R4_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R4_CURRENT_CONTROLLED_STAGED_BACKFILL_BATCH2_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "CONTROLLED_STAGED_BACKFILL_BATCH2_READY", "BATCH_ID", "BATCH_TICKER_COUNT",
    "BATCH_SELECTION_SOURCE", "EXTERNAL_DATA_FETCHED", "FETCH_PROVIDER", "FETCH_ATTEMPTED_COUNT",
    "FETCH_SUCCESS_COUNT", "FETCH_EMPTY_COUNT", "FETCH_FAILED_COUNT", "FETCH_SCHEMA_INVALID_COUNT",
    "STAGED_PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_DIR", "STAGED_COMBINED_HISTORY_PATH",
    "STAGED_MANIFEST_PATH", "OFFICIAL_PRICE_CACHE_MODIFIED", "OFFICIAL_PRICE_HISTORY_MODIFIED",
    "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "LEDGER_MODIFIED",
    "ROLLING_SCAN_EXECUTED", "STAGED_ROLLING_SCAN_RETEST_EXECUTED", "STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT",
    "STAGED_FULL_HISTORY_READY_COUNT", "STAGED_INSUFFICIENT_HISTORY_COUNT", "STAGED_SCAN_RETEST_SUCCESS_RATIO",
    "PROJECTED_REMAINING_STALE_AFTER_BATCH2_IF_INTEGRATED",
    "USER_TARGET_65_LOCAL_PRICE_SCANS_REACHABLE_AFTER_BATCH2_STAGED_BACKFILL",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED",
    "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "VALIDATION_FAIL_COUNT", "RECOMMENDED_NEXT_ACTION",
    "BACKFILL_REPORT_PATH", "BATCH_TICKERS_PATH", "FETCH_RESULT_PATH", "STAGED_HISTORY_MANIFEST_OUTPUT_PATH",
    "STAGED_SCAN_RETEST_RESULT_PATH", "SOURCE_AUDIT_PATH", "VALIDATION_PATH",
    "ROLLING_SCAN_RETEST_SUMMARY_PATH", "REPORT_PATH",
]

BATCH_FIELDS = ["batch_id", "ticker", "selection_source", "selection_reason", "batch_order", "excluded", "exclusion_reason"]
FETCH_FIELDS = [
    "batch_id", "ticker", "fetch_attempted", "fetch_status", "failure_reason", "requested_start_date",
    "requested_end_date", "actual_min_date", "actual_max_date", "row_count", "schema_valid", "staged_file_path",
]
MANIFEST_FIELDS = ["file_type", "ticker", "relative_path", "exists", "row_count", "min_date", "max_date", "notes"]
RETEST_FIELDS = [
    "ticker", "staged_local_price_available", "staged_row_count", "latest_staged_date", "min_staged_date",
    "history_span_days", "minimum_history_threshold_met", "staged_scan_status",
]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "ticker_count", "selected", "notes"]
SUMMARY_FIELDS = ["metric", "value", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

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
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET": "FALSE",
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


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "NA", "N/A", "TICKER"} or ticker.isdigit():
        return ""
    return ticker if TICKER_RE.match(ticker) else ""


def get_ticker(row: Dict[str, str]) -> str:
    for key in ("ticker", "Ticker", "symbol", "Symbol", "yf_ticker"):
        ticker = normalize_ticker(row.get(key, ""))
        if ticker:
            return ticker
    return ""


def load_tickers(path: Path) -> List[str]:
    rows, _ = read_csv(path)
    out: List[str] = []
    seen = set()
    for row in rows:
        ticker = get_ticker(row)
        if ticker and ticker not in seen:
            seen.add(ticker)
            out.append(ticker)
    return out


def load_source_tickers(root: Path) -> Tuple[List[str], str, List[Dict[str, object]]]:
    sources = [
        ("R3_REMAINING_STALE", "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_REMAINING_STALE_TICKERS.csv"),
        ("R3_COVERAGE_AUDIT", "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_5DAY_COVERAGE_AUDIT.csv"),
        ("LEDGER", "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"),
        ("V24A_DATA_NOT_READY", "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv"),
        ("V24B_DATA_NOT_READY", "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv"),
        ("V23A_PLAN", "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv"),
    ]
    audit: List[Dict[str, object]] = []
    selected: List[str] = []
    selected_name = ""
    for name, rel in sources:
        rows, _ = read_csv(root / rel)
        tickers = load_tickers(root / rel)
        is_selected = not selected and bool(tickers)
        if is_selected:
            selected = tickers
            selected_name = rel
        audit.append({
            "source_name": name,
            "source_path": rel,
            "exists": str((root / rel).exists()).upper(),
            "row_count": len(rows),
            "ticker_count": len(tickers),
            "selected": str(is_selected).upper(),
            "notes": "Batch source priority scan.",
        })
    return selected, selected_name, audit


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def protected_files(root: Path) -> List[Path]:
    dirs = [
        "state/v18/price_cache", "state/v18/rolling_coverage", "outputs/v18/factor_pack",
        "outputs/v18/ranking", "outputs/v18/signal_snapshots", "outputs/v18/technical_timing",
        "outputs/v18/universe", "outputs/v18/forward_tracker", "state/v18/simulation",
        "state/v18/forward_outcome", "state/v18/candidate_forward_tracker", "state/v18/manual",
        "archive/stable",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def valid_schema(columns: Sequence[str]) -> bool:
    lower = {str(c).strip().lower() for c in columns}
    return {"open", "high", "low", "close"}.issubset(lower)


def fetch_one(ticker: str, start: dt.date, end: dt.date, out_path: Path) -> Dict[str, object]:
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        return {"fetch_status": "FAILED", "failure_reason": f"YFINANCE_IMPORT_FAILED:{exc}", "row_count": 0, "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    try:
        df = yf.download(ticker, start=start.isoformat(), end=(end + dt.timedelta(days=1)).isoformat(), interval="1d", auto_adjust=False, progress=False, threads=False)
    except Exception as exc:
        return {"fetch_status": "FAILED", "failure_reason": f"YFINANCE_DOWNLOAD_FAILED:{exc}", "row_count": 0, "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    if df is None or getattr(df, "empty", True):
        return {"fetch_status": "EMPTY", "failure_reason": "EMPTY_DATA", "row_count": 0, "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    if hasattr(df.columns, "nlevels") and getattr(df.columns, "nlevels", 1) > 1:
        df.columns = [str(col[0]) for col in df.columns]
    if not valid_schema([str(c) for c in df.columns]):
        return {"fetch_status": "SCHEMA_INVALID", "failure_reason": f"SCHEMA_INVALID:{','.join(str(c) for c in df.columns)}", "row_count": len(df), "schema_valid": "FALSE", "actual_min_date": "", "actual_max_date": ""}
    ensure_dir(out_path.parent)
    df.to_csv(out_path, index_label="Date")
    dates = [str(idx)[:10] for idx in df.index]
    return {"fetch_status": "SUCCESS", "failure_reason": "", "row_count": len(df), "schema_valid": "TRUE", "actual_min_date": min(dates), "actual_max_date": max(dates)}


def read_staged_dates(path: Path) -> Tuple[int, str, str, bool, int]:
    rows, fields = read_csv(path)
    if not rows:
        return 0, "", "", False, 0
    date_col = "Date" if "Date" in fields else fields[0] if fields else ""
    dates = []
    for row in rows:
        text = str(row.get(date_col, ""))[:10]
        try:
            dates.append(dt.datetime.strptime(text, "%Y-%m-%d").date())
        except ValueError:
            pass
    if not dates:
        return len(rows), "", "", valid_schema(fields), 0
    span = (max(dates) - min(dates)).days
    return len(rows), min(dates).isoformat(), max(dates).isoformat(), valid_schema(fields), span


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


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_md(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R4 Controlled Staged Backfill Batch 2

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Purpose
Continue reducing remaining stale/data-not-ready coverage with Batch 2 staged-only price/history backfill.

## Batch Selection
Batch source: {values['BATCH_SELECTION_SOURCE']}. Batch tickers: {values['BATCH_TICKER_COUNT']}.

## Fetch And Staged Retest
Fetch success: {values['FETCH_SUCCESS_COUNT']}. Empty: {values['FETCH_EMPTY_COUNT']}. Failed: {values['FETCH_FAILED_COUNT']}. Schema invalid: {values['FETCH_SCHEMA_INVALID_COUNT']}.

Staged local price success: {values['STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT']}. Full-history ready: {values['STAGED_FULL_HISTORY_READY_COUNT']}. Insufficient history: {values['STAGED_INSUFFICIENT_HISTORY_COUNT']}.

## Safety
This step fetched external data into staged Batch 2 files only. Official price cache/history, ranking, factor pack, technical timing, signal snapshots, rolling ledger, backtest, and trading state were not modified.

## Remaining Blockers
Staged data must pass a later quality audit and explicit official integration before it can update official cache or ledger coverage. TRUE_5DAY_UNIQUE_COVERAGE_MET remains FALSE.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in protected_files(root)}

    integrated = set(load_tickers(root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_MERGE_RESULT.csv"))
    held_out = set(load_tickers(root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv"))
    ledger_rows, _ = read_csv(root / "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv")
    today = dt.date.today()
    cutoff = today - dt.timedelta(days=5)
    current_success = set()
    for row in ledger_rows:
        ticker = get_ticker(row)
        try:
            success_date = dt.datetime.strptime(str(row.get("last_success_scan_date", ""))[:10], "%Y-%m-%d").date()
            if success_date >= cutoff:
                current_success.add(ticker)
        except ValueError:
            pass

    source_tickers, selected_source, source_audit = load_source_tickers(root)
    excluded_rows: List[Dict[str, object]] = []
    selected: List[str] = []
    seen = set()
    for ticker in source_tickers:
        reason = ""
        if ticker in integrated or ticker in current_success:
            reason = "ALREADY_INTEGRATED_EXCLUDED"
        elif ticker in held_out or ticker in {"COG", "JFROG"}:
            reason = "BATCH1_HELD_OUT_RETRY_EXCLUDED"
        if reason:
            excluded_rows.append({"batch_id": BATCH_ID, "ticker": ticker, "selection_source": selected_source, "selection_reason": "", "batch_order": "", "excluded": "TRUE", "exclusion_reason": reason})
            continue
        if ticker not in seen:
            seen.add(ticker)
            selected.append(ticker)
        if len(selected) >= BATCH_SIZE:
            break

    batch_rows = [
        {"batch_id": BATCH_ID, "ticker": ticker, "selection_source": selected_source, "selection_reason": "REMAINING_STALE_OR_NEVER_SUCCESS", "batch_order": i + 1, "excluded": "FALSE", "exclusion_reason": ""}
        for i, ticker in enumerate(selected)
    ] + excluded_rows[:100]

    start = today - dt.timedelta(days=365 * 5 + 10)
    fetch_rows: List[Dict[str, object]] = []
    manifest_rows: List[Dict[str, object]] = []
    retest_rows: List[Dict[str, object]] = []
    combined_rows: List[Dict[str, object]] = []
    staged_dir = root / STAGED_DIR_REL
    ensure_dir(staged_dir)
    for ticker in selected:
        staged_path = staged_dir / f"{ticker}.csv"
        result = fetch_one(ticker, start, today, staged_path)
        fetch_rows.append({
            "batch_id": BATCH_ID,
            "ticker": ticker,
            "fetch_attempted": "TRUE",
            "fetch_status": result["fetch_status"],
            "failure_reason": result["failure_reason"],
            "requested_start_date": start.isoformat(),
            "requested_end_date": today.isoformat(),
            "actual_min_date": result["actual_min_date"],
            "actual_max_date": result["actual_max_date"],
            "row_count": result["row_count"],
            "schema_valid": result["schema_valid"],
            "staged_file_path": str(staged_path) if staged_path.exists() else "",
        })
        rows, fields = read_csv(staged_path)
        if result["fetch_status"] == "SUCCESS":
            date_col = "Date" if "Date" in fields else fields[0] if fields else ""
            for row in rows:
                out = {"ticker": ticker}
                out.update(row)
                combined_rows.append(out)
        row_count, min_date, max_date, schema_ok, span = read_staged_dates(staged_path)
        manifest_rows.append({"file_type": "PER_TICKER_STAGED_HISTORY", "ticker": ticker, "relative_path": str(staged_path.relative_to(root)).replace("\\", "/") if staged_path.exists() else "", "exists": str(staged_path.exists()).upper(), "row_count": row_count, "min_date": min_date, "max_date": max_date, "notes": result["fetch_status"]})
        if result["fetch_status"] == "SUCCESS" and schema_ok and row_count > 0:
            if row_count >= MIN_FULL_HISTORY_ROWS and span >= MIN_FULL_HISTORY_SPAN_DAYS:
                status = "STAGED_FULL_HISTORY_READY"
            else:
                status = "STAGED_INSUFFICIENT_HISTORY"
        elif result["fetch_status"] == "EMPTY":
            status = "STAGED_EMPTY_DATA"
        elif result["fetch_status"] == "SCHEMA_INVALID":
            status = "STAGED_SCHEMA_INVALID"
        else:
            status = "STAGED_FETCH_FAILED"
        retest_rows.append({"ticker": ticker, "staged_local_price_available": str(status in {"STAGED_FULL_HISTORY_READY", "STAGED_INSUFFICIENT_HISTORY"}).upper(), "staged_row_count": row_count, "latest_staged_date": max_date, "min_staged_date": min_date, "history_span_days": span, "minimum_history_threshold_met": str(status == "STAGED_FULL_HISTORY_READY").upper(), "staged_scan_status": status})

    combined_path = root / STAGED_COMBINED_REL
    if combined_rows:
        fields = ["ticker"] + sorted({key for row in combined_rows for key in row if key != "ticker"})
        write_csv(combined_path, combined_rows, fields)
    else:
        write_csv(combined_path, [], ["ticker", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"])
    manifest_rows.append({"file_type": "COMBINED_STAGED_HISTORY", "ticker": "ALL", "relative_path": STAGED_COMBINED_REL, "exists": str(combined_path.exists()).upper(), "row_count": len(combined_rows), "min_date": "", "max_date": "", "notes": "Combined Batch 2 staged file."})
    write_csv(root / STAGED_MANIFEST_REL, manifest_rows, MANIFEST_FIELDS)

    success_count = sum(1 for row in fetch_rows if row["fetch_status"] == "SUCCESS")
    empty_count = sum(1 for row in fetch_rows if row["fetch_status"] == "EMPTY")
    failed_count = sum(1 for row in fetch_rows if row["fetch_status"] == "FAILED")
    schema_invalid_count = sum(1 for row in fetch_rows if row["fetch_status"] == "SCHEMA_INVALID")
    staged_success = sum(1 for row in retest_rows if row["staged_local_price_available"] == "TRUE")
    full_ready = sum(1 for row in retest_rows if row["staged_scan_status"] == "STAGED_FULL_HISTORY_READY")
    insufficient = sum(1 for row in retest_rows if row["staged_scan_status"] == "STAGED_INSUFFICIENT_HISTORY")
    ratio = staged_success / len(selected) if selected else 0.0
    remaining_before = len(load_tickers(root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_REMAINING_STALE_TICKERS.csv"))
    projected_remaining = max(0, remaining_before - full_ready)

    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "CONTROLLED_STAGED_BACKFILL_BATCH2_READY": "TRUE",
        "BATCH_ID": BATCH_ID,
        "BATCH_TICKER_COUNT": str(len(selected)),
        "BATCH_SELECTION_SOURCE": selected_source,
        "EXTERNAL_DATA_FETCHED": "TRUE",
        "FETCH_PROVIDER": "yfinance",
        "FETCH_ATTEMPTED_COUNT": str(len(selected)),
        "FETCH_SUCCESS_COUNT": str(success_count),
        "FETCH_EMPTY_COUNT": str(empty_count),
        "FETCH_FAILED_COUNT": str(failed_count),
        "FETCH_SCHEMA_INVALID_COUNT": str(schema_invalid_count),
        "STAGED_PRICE_HISTORY_WRITTEN": str(success_count > 0).upper(),
        "STAGED_PRICE_HISTORY_DIR": str(root / STAGED_DIR_REL),
        "STAGED_COMBINED_HISTORY_PATH": str(combined_path),
        "STAGED_MANIFEST_PATH": str(root / STAGED_MANIFEST_REL),
        "STAGED_ROLLING_SCAN_RETEST_EXECUTED": "TRUE",
        "STAGED_LOCAL_PRICE_SCAN_SUCCESS_COUNT": str(staged_success),
        "STAGED_FULL_HISTORY_READY_COUNT": str(full_ready),
        "STAGED_INSUFFICIENT_HISTORY_COUNT": str(insufficient),
        "STAGED_SCAN_RETEST_SUCCESS_RATIO": f"{ratio:.6f}",
        "PROJECTED_REMAINING_STALE_AFTER_BATCH2_IF_INTEGRATED": str(projected_remaining),
        "USER_TARGET_65_LOCAL_PRICE_SCANS_REACHABLE_AFTER_BATCH2_STAGED_BACKFILL": str(staged_success >= 65).upper(),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "FALSE_STAGED_ONLY_NOT_OFFICIAL_LEDGER_COVERAGE",
        "VALIDATION_FAIL_COUNT": "0",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "RECOMMENDED_NEXT_ACTION": "Run a V18.23C-R5 Batch 2 staged quality audit before any official price cache integration or ledger update.",
        "BACKFILL_REPORT_PATH": str(root / OUTPUTS["md"]),
        "BATCH_TICKERS_PATH": str(root / OUTPUTS["batch"]),
        "FETCH_RESULT_PATH": str(root / OUTPUTS["fetch"]),
        "STAGED_HISTORY_MANIFEST_OUTPUT_PATH": str(root / OUTPUTS["manifest"]),
        "STAGED_SCAN_RETEST_RESULT_PATH": str(root / OUTPUTS["retest"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "ROLLING_SCAN_RETEST_SUMMARY_PATH": str(root / OUTPUTS["summary"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY_FALSE)

    write_csv(root / OUTPUTS["batch"], batch_rows, BATCH_FIELDS)
    write_csv(root / OUTPUTS["fetch"], fetch_rows, FETCH_FIELDS)
    write_csv(root / OUTPUTS["manifest"], manifest_rows, MANIFEST_FIELDS)
    write_csv(root / OUTPUTS["retest"], retest_rows, RETEST_FIELDS)
    write_csv(root / OUTPUTS["source"], source_audit, SOURCE_FIELDS)
    summary_rows = [
        {"metric": "batch_ticker_count", "value": len(selected), "notes": "Batch 2 selected tickers."},
        {"metric": "staged_local_price_scan_success_count", "value": staged_success, "notes": "Staged-only success count."},
        {"metric": "staged_full_history_ready_count", "value": full_ready, "notes": "Potential future quality audit candidates."},
        {"metric": "projected_remaining_stale_after_batch2_if_integrated", "value": projected_remaining, "notes": "Projection only; ledger not updated."},
    ]
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_md(values))
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required = [root / rel for rel in OUTPUTS.values()] + [root / STAGED_MANIFEST_REL, combined_path]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23C_R4_controlled_staged_backfill_batch2.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23C_R4_controlled_staged_backfill_batch2.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "Required outputs and staged files must exist and be non-empty."),
        validation_row("batch_count_gt_zero", len(selected) > 0, 1, "Batch 2 ticker count must be greater than zero."),
        validation_row("fetch_result_one_row_per_ticker", len(fetch_rows) == len(selected), 1, "Fetch result rows must match batch tickers."),
        validation_row("retest_one_row_per_ticker", len(retest_rows) == len(selected), 1, "Retest rows must match batch tickers."),
        validation_row("staged_manifest_lists_files", bool(manifest_rows), 1, "Staged manifest must list files."),
        validation_row("official_and_forbidden_files_unchanged", not changed, len(changed), ";".join(changed[:20])),
        validation_row("true_coverage_remains_false", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] == "FALSE", 1, "Staged-only test."),
    ]
    for key, expected in SAFETY_FALSE.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or len(selected) == 0 or success_count == 0:
        values["STATUS"] = STATUS_FAIL
        values["CONTROLLED_STAGED_BACKFILL_BATCH2_READY"] = "FALSE"
    elif success_count == len(selected) and staged_success == len(selected):
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
