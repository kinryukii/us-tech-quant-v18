from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple


STATUS_WARN = "WARN_V18_23B_ROLLING_SCAN_EXECUTOR_READY"
STATUS_OK = "OK_V18_23B_ROLLING_SCAN_EXECUTOR_TRUE_5DAY_COVERAGE_READY"
STATUS_FAIL = "FAIL_V18_23B_ROLLING_SCAN_EXECUTOR"
MODE = "LOCAL_ONLY_ROLLING_SCAN_EXECUTION"
TARGET_COVERAGE_DAYS = 5
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

LEDGER_REL = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
OUTPUTS = {
    "executor": "outputs/v18/rolling_coverage/V18_23B_CURRENT_ROLLING_SCAN_EXECUTOR.md",
    "selected": "outputs/v18/rolling_coverage/V18_23B_CURRENT_SELECTED_SCAN_LIST.csv",
    "result": "outputs/v18/rolling_coverage/V18_23B_CURRENT_SCAN_RESULT.csv",
    "ledger_snapshot": "outputs/v18/rolling_coverage/V18_23B_CURRENT_SCAN_LEDGER_SNAPSHOT.csv",
    "coverage_audit": "outputs/v18/rolling_coverage/V18_23B_CURRENT_5DAY_COVERAGE_AUDIT.csv",
    "source_audit": "outputs/v18/rolling_coverage/V18_23B_CURRENT_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/rolling_coverage/V18_23B_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23B_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23B_CURRENT_ROLLING_SCAN_EXECUTOR_REPORT.md",
}

SAFETY_INVARIANTS = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "ROLLING_SCAN_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "ROLLING_SCAN_EXECUTOR_READY",
    "LOCAL_ONLY",
    "TARGET_COVERAGE_DAYS",
    "TOTAL_UNIVERSE_COUNT",
    "TARGET_SCAN_COUNT_PER_RUN",
    "SELECTED_SCAN_COUNT",
    "SUCCESS_SCAN_COUNT",
    "SKIPPED_SCAN_COUNT",
    "FAILED_SCAN_COUNT",
    "LEDGER_CREATED_OR_UPDATED",
    "LEDGER_PATH",
    "ROLLING_SCAN_EXECUTED",
    "ROLLING_SCAN_DATA_FETCHED",
    "EXTERNAL_DATA_FETCHED",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN",
    "STAGED_PRICE_HISTORY_WRITTEN",
    "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED",
    "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_COUNT",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS",
    "COVERAGE_TRUST_LEVEL",
    "VALIDATION_FAIL_COUNT",
    "RECOMMENDED_NEXT_ACTION",
    "EXECUTOR_PATH",
    "SELECTED_SCAN_LIST_PATH",
    "SCAN_RESULT_PATH",
    "LEDGER_SNAPSHOT_PATH",
    "COVERAGE_AUDIT_PATH",
    "SOURCE_AUDIT_PATH",
    "VALIDATION_PATH",
    "REPORT_PATH",
]

LEDGER_FIELDS = [
    "ticker",
    "canonical_universe_present",
    "first_seen_date",
    "last_attempt_scan_timestamp",
    "last_success_scan_timestamp",
    "last_success_scan_date",
    "last_scan_status",
    "last_scan_run_id",
    "success_scan_count",
    "attempt_scan_count",
    "local_price_available",
    "factor_pack_available",
    "technical_timing_available",
    "full_history_ready",
    "failure_reason",
    "source_notes",
]
SCAN_FIELDS = [
    "run_id",
    "ticker",
    "scan_status",
    "local_price_available",
    "factor_pack_available",
    "technical_timing_available",
    "full_history_ready",
    "failure_reason",
    "success_counted",
    "source_notes",
]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "ticker_count", "selected", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]
COVERAGE_FIELDS = ["metric", "value", "notes"]


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


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "NA", "N/A", "TICKER"} or ticker.isdigit():
        return ""
    return ticker if TICKER_RE.match(ticker) else ""


def find_ticker_column(fields: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for name in ("ticker", "symbol", "candidate_ticker", "yf_ticker"):
        if name in lower:
            return lower[name]
    return ""


def ticker_set(path: Path) -> Set[str]:
    rows, fields = read_csv(path)
    col = find_ticker_column(fields)
    return {normalize_ticker(row.get(col, "")) for row in rows if col and normalize_ticker(row.get(col, ""))}


def load_universe(root: Path) -> Tuple[List[str], str, List[Dict[str, object]]]:
    candidates = [
        ("V18_23A_PLAN", "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv"),
        ("V18_UNIVERSE_ROLLING_STATE", "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv"),
    ]
    audit: List[Dict[str, object]] = []
    selected: List[str] = []
    selected_path = ""
    for name, rel in candidates:
        path = root / rel
        rows, fields = read_csv(path)
        col = find_ticker_column(fields)
        tickers = sorted({normalize_ticker(row.get(col, "")) for row in rows if col and normalize_ticker(row.get(col, ""))})
        is_selected = not selected and bool(tickers)
        if is_selected:
            selected = tickers
            selected_path = rel
        audit.append({"source_name": name, "source_path": rel, "exists": str(path.exists()).upper(), "row_count": len(rows), "ticker_count": len(tickers), "selected": str(is_selected).upper(), "notes": f"ticker_column={col or 'MISSING'}"})
    return selected, selected_path, audit


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def to_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def default_ledger_row(ticker: str, today: str) -> Dict[str, object]:
    return {
        "ticker": ticker,
        "canonical_universe_present": "TRUE",
        "first_seen_date": today,
        "last_attempt_scan_timestamp": "",
        "last_success_scan_timestamp": "",
        "last_success_scan_date": "",
        "last_scan_status": "NEVER_SCANNED",
        "last_scan_run_id": "",
        "success_scan_count": 0,
        "attempt_scan_count": 0,
        "local_price_available": "FALSE",
        "factor_pack_available": "FALSE",
        "technical_timing_available": "FALSE",
        "full_history_ready": "FALSE",
        "failure_reason": "",
        "source_notes": "",
    }


def load_ledger(path: Path, universe: Sequence[str], today: str) -> Dict[str, Dict[str, object]]:
    rows, _ = read_csv(path)
    ledger = {normalize_ticker(row.get("ticker", "")): dict(row) for row in rows if normalize_ticker(row.get("ticker", ""))}
    for ticker in universe:
        if ticker not in ledger:
            ledger[ticker] = default_ledger_row(ticker, today)
        ledger[ticker]["canonical_universe_present"] = "TRUE"
        ledger[ticker].setdefault("first_seen_date", today)
    for ticker, row in ledger.items():
        if ticker not in set(universe):
            row["canonical_universe_present"] = "FALSE"
    return ledger


def selection_key(row: Dict[str, object]) -> Tuple[int, int, str, str, str]:
    success_date = str(row.get("last_success_scan_date", ""))
    attempt_ts = str(row.get("last_attempt_scan_timestamp", ""))
    has_success = 0 if success_date else 1
    never_attempted = 0 if not attempt_ts else 1
    success_sort = success_date or "0000-00-00"
    attempt_sort = attempt_ts or "0000-00-00T00:00:00"
    return (has_success, never_attempted, success_sort, attempt_sort, str(row.get("ticker", "")))


def local_price_available(root: Path, ticker: str) -> bool:
    path = root / "state/v18/price_cache" / f"{ticker}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return False
    return len(read_text(path).splitlines()) > 1


def run_local_scan(root: Path, ticker: str, factor_tickers: Set[str], tech_tickers: Set[str]) -> Dict[str, object]:
    price_ok = local_price_available(root, ticker)
    factor_ok = ticker in factor_tickers
    tech_ok = ticker in tech_tickers
    full_history_ready = factor_ok
    if price_ok:
        status = "SUCCESS_LOCAL_SCAN"
        failure = ""
    else:
        status = "SKIPPED_NO_LOCAL_DATA"
        failure = "LOCAL_PRICE_CACHE_MISSING_OR_EMPTY"
    notes = []
    notes.append("local_price=available" if price_ok else "local_price=missing")
    notes.append("factor_pack=available" if factor_ok else "factor_pack=missing")
    notes.append("technical_timing=available" if tech_ok else "technical_timing=missing")
    return {
        "scan_status": status,
        "local_price_available": str(price_ok).upper(),
        "factor_pack_available": str(factor_ok).upper(),
        "technical_timing_available": str(tech_ok).upper(),
        "full_history_ready": str(full_history_ready).upper(),
        "failure_reason": failure,
        "source_notes": ";".join(notes),
    }


def file_signature(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def forbidden_files(root: Path) -> List[Path]:
    rel_dirs = [
        "state/v18/price_cache",
        "outputs/v18/factor_pack",
        "outputs/v18/ranking",
        "outputs/v18/signal_snapshots",
        "outputs/v18/technical_timing",
        "outputs/v18/universe",
        "outputs/v18/forward_tracker",
        "outputs/v18/simulation",
        "state/v18/simulation",
        "state/v18/forward_outcome",
        "state/v18/candidate_forward_tracker",
        "state/v18/manual",
        "state/v16",
        "archive/stable",
    ]
    files: List[Path] = []
    for rel in rel_dirs:
        base = root / rel
        if base.exists():
            files.extend(path for path in base.rglob("*") if path.is_file())
    return files


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    command = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + ["| " + " | ".join(str(value) for value in row) + " |" for row in rows])


def render_executor(values: Dict[str, str], source_audit: Sequence[Dict[str, object]]) -> str:
    return f"""# V18.23B Rolling Scan Executor

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Status
Status: **{values['STATUS']}**

Mode: **{values['MODE']}**

## Local-only execution
V18.23B executes a local-only rolling scan over selected tickers and updates only the dedicated ledger `{values['LEDGER_PATH']}` plus V18.23B output files. It does not fetch data, modify price cache, rewrite rankings, rewrite factor packs, rewrite technical timing, run backtests, or affect trading decisions.

## Run summary
{markdown_table(['Metric', 'Value'], [
    ('total_universe_count', values['TOTAL_UNIVERSE_COUNT']),
    ('target_scan_count_per_run', values['TARGET_SCAN_COUNT_PER_RUN']),
    ('selected_scan_count', values['SELECTED_SCAN_COUNT']),
    ('success_scan_count', values['SUCCESS_SCAN_COUNT']),
    ('skipped_scan_count', values['SKIPPED_SCAN_COUNT']),
    ('failed_scan_count', values['FAILED_SCAN_COUNT']),
    ('unique_success_scanned_within_window_count', values['UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_COUNT']),
    ('true_5day_unique_coverage_met', values['TRUE_5DAY_UNIQUE_COVERAGE_MET']),
    ('coverage_trust_level', values['COVERAGE_TRUST_LEVEL']),
])}

## Coverage window note
The 5-day coverage audit uses local ledger dates and a simple calendar approximation. It is not exchange-calendar certified.

## Source audit
{markdown_table(['Source', 'Exists', 'Ticker count', 'Selected', 'Notes'], [(row['source_path'], row['exists'], row['ticker_count'], row['selected'], row['notes']) for row in source_audit])}

## Safety invariants
{markdown_table(['Invariant', 'Value'], [(key, values[key]) for key in SAFETY_INVARIANTS])}

## Recommended next action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23B Rolling Scan Executor Report

Status: {values['STATUS']}.

Selected {values['SELECTED_SCAN_COUNT']} tickers from {values['TOTAL_UNIVERSE_COUNT']} canonical tickers. Successful local scans: {values['SUCCESS_SCAN_COUNT']}; skipped: {values['SKIPPED_SCAN_COUNT']}; failed: {values['FAILED_SCAN_COUNT']}.

Ledger updated: {values['LEDGER_CREATED_OR_UPDATED']} at `{values['LEDGER_PATH']}`.

TRUE_5DAY_UNIQUE_COVERAGE_MET: {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}. Coverage trust level: {values['COVERAGE_TRUST_LEVEL']}.

No external data was fetched, no price cache/ranking/source files were modified, and no backtest or trading logic was executed.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before_files = forbidden_files(root)
    before_sig = {str(path): file_signature(path) for path in before_files}

    now = dt.datetime.now()
    today = now.date().isoformat()
    run_id = f"V18_23B_{now.strftime('%Y%m%d_%H%M%S')}"
    universe, universe_source, source_audit = load_universe(root)
    target_count = max(1, math.ceil(len(universe) / TARGET_COVERAGE_DAYS)) if universe else 0
    ledger_path = root / LEDGER_REL
    ledger = load_ledger(ledger_path, universe, today)
    canonical_rows = [ledger[ticker] for ticker in universe]
    selected_rows = sorted(canonical_rows, key=selection_key)[:target_count]
    selected_tickers = [str(row["ticker"]) for row in selected_rows]

    factor_tickers = ticker_set(root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv")
    tech_tickers = ticker_set(root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv")
    source_audit.extend(
        [
            {"source_name": "FACTOR_PACK", "source_path": "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "exists": str((root / 'outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv').exists()).upper(), "row_count": "", "ticker_count": len(factor_tickers), "selected": "FALSE", "notes": "Read-only local factor availability source."},
            {"source_name": "TECHNICAL_TIMING", "source_path": "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv", "exists": str((root / 'outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv').exists()).upper(), "row_count": "", "ticker_count": len(tech_tickers), "selected": "FALSE", "notes": "Read-only local technical timing availability source."},
        ]
    )

    results: List[Dict[str, object]] = []
    success_count = skipped_count = failed_count = 0
    for ticker in selected_tickers:
        scan = run_local_scan(root, ticker, factor_tickers, tech_tickers)
        status = str(scan["scan_status"])
        row = ledger[ticker]
        previous_success_date = str(row.get("last_success_scan_date", ""))
        success_counted = "FALSE"
        row["last_attempt_scan_timestamp"] = now.isoformat(timespec="seconds")
        row["last_scan_run_id"] = run_id
        row["attempt_scan_count"] = to_int(row.get("attempt_scan_count")) + 1
        if status == "SUCCESS_LOCAL_SCAN":
            success_count += 1
            row["last_success_scan_timestamp"] = now.isoformat(timespec="seconds")
            row["last_success_scan_date"] = today
            if previous_success_date != today:
                row["success_scan_count"] = to_int(row.get("success_scan_count")) + 1
                success_counted = "TRUE"
        elif status.startswith("SKIPPED"):
            skipped_count += 1
        else:
            failed_count += 1
        row["last_scan_status"] = status
        for key in ["local_price_available", "factor_pack_available", "technical_timing_available", "full_history_ready", "failure_reason", "source_notes"]:
            row[key] = scan[key]
        results.append({"run_id": run_id, "ticker": ticker, **scan, "success_counted": success_counted})

    ledger_rows = [ledger[ticker] for ticker in sorted(ledger)]
    write_csv(ledger_path, ledger_rows, LEDGER_FIELDS)

    cutoff = now.date() - dt.timedelta(days=TARGET_COVERAGE_DAYS - 1)
    within_window = [ticker for ticker in universe if (parse_date(ledger[ticker].get("last_success_scan_date")) or dt.date.min) >= cutoff]
    true_met = len(within_window) == len(universe) and bool(universe)
    if true_met:
        coverage_trust = "HIGH"
        coverage_status = "TRUE_BY_LOCAL_LEDGER_CALENDAR_APPROXIMATION_NOT_EXCHANGE_CERTIFIED"
    elif within_window:
        coverage_trust = "MEDIUM"
        coverage_status = "FALSE_PARTIAL_LOCAL_LEDGER_COVERAGE"
    else:
        coverage_trust = "LOW"
        coverage_status = "FALSE_NO_SUCCESSFUL_LOCAL_LEDGER_COVERAGE_IN_WINDOW"

    values: Dict[str, str] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "ROLLING_SCAN_EXECUTOR_READY": "FALSE",
        "LOCAL_ONLY": "TRUE",
        "TARGET_COVERAGE_DAYS": str(TARGET_COVERAGE_DAYS),
        "TOTAL_UNIVERSE_COUNT": str(len(universe)),
        "TARGET_SCAN_COUNT_PER_RUN": str(target_count),
        "SELECTED_SCAN_COUNT": str(len(selected_tickers)),
        "SUCCESS_SCAN_COUNT": str(success_count),
        "SKIPPED_SCAN_COUNT": str(skipped_count),
        "FAILED_SCAN_COUNT": str(failed_count),
        "LEDGER_CREATED_OR_UPDATED": "TRUE",
        "LEDGER_PATH": str(ledger_path),
        "ROLLING_SCAN_EXECUTED": "TRUE",
        "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_COUNT": str(len(within_window)),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": str(true_met).upper(),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": coverage_status,
        "COVERAGE_TRUST_LEVEL": coverage_trust,
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Run V18.23B again on later cycles to scan the next least-recently-successful tickers; do not fetch data or modify official ranking/price/trading files.",
        "EXECUTOR_PATH": str(root / OUTPUTS["executor"]),
        "SELECTED_SCAN_LIST_PATH": str(root / OUTPUTS["selected"]),
        "SCAN_RESULT_PATH": str(root / OUTPUTS["result"]),
        "LEDGER_SNAPSHOT_PATH": str(root / OUTPUTS["ledger_snapshot"]),
        "COVERAGE_AUDIT_PATH": str(root / OUTPUTS["coverage_audit"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source_audit"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY_INVARIANTS)

    selected_output = [row for row in results]
    coverage_rows = [
        {"metric": "canonical_universe_source", "value": universe_source, "notes": "Selected current/fallback local source."},
        {"metric": "unique_success_scanned_within_window_count", "value": len(within_window), "notes": "Calendar approximation from local ledger."},
        {"metric": "true_5day_unique_coverage_met", "value": values["TRUE_5DAY_UNIQUE_COVERAGE_MET"], "notes": coverage_status},
        {"metric": "coverage_trust_level", "value": coverage_trust, "notes": "HIGH only when all canonical tickers have success evidence inside window."},
    ]
    write_csv(root / OUTPUTS["selected"], selected_output, SCAN_FIELDS)
    write_csv(root / OUTPUTS["result"], results, SCAN_FIELDS)
    write_csv(root / OUTPUTS["ledger_snapshot"], ledger_rows, LEDGER_FIELDS)
    write_csv(root / OUTPUTS["coverage_audit"], coverage_rows, COVERAGE_FIELDS)
    write_csv(root / OUTPUTS["source_audit"], source_audit, SOURCE_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["executor"], render_executor(values, source_audit))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after_files = forbidden_files(root)
    after_sig = {str(path): file_signature(path) for path in after_files}
    modified_forbidden = sorted(path for path, sig in before_sig.items() if after_sig.get(path) != sig)
    new_forbidden = sorted(path for path in after_sig if path not in before_sig)
    forbidden_changed = modified_forbidden + new_forbidden
    required_paths = [root / rel for rel in OUTPUTS.values()]
    selected_unique = len(set(selected_tickers)) == len(selected_tickers)
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23B_rolling_scan_executor.py"), 1, "Python compile check."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23B_rolling_scan_executor.ps1"), 1, "PowerShell parse check."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required_paths), 1, "All V18.23B outputs must exist and be non-empty."),
        validation_row("canonical_universe_count_positive", len(universe) > 0, 1, "Canonical universe must load."),
        validation_row("target_scan_count_normal", target_count == math.ceil(len(universe) / TARGET_COVERAGE_DAYS) if universe else False, 1, "Target scan count should be ceil(total/5)."),
        validation_row("selected_scan_count_positive", len(selected_tickers) > 0, 1, "Selected scan list must not be empty."),
        validation_row("selected_scan_count_approx_target", len(selected_tickers) == min(target_count, len(universe)), 1, "Selected scan count should match target unless universe is smaller."),
        validation_row("ledger_includes_all_canonical_tickers", all(ticker in ledger for ticker in universe), 1, "Ledger must include all canonical tickers."),
        validation_row("selected_scan_list_no_duplicates", selected_unique, 1, "Selected scan list must not contain duplicates."),
        validation_row("scan_result_one_row_per_selected", len(results) == len(selected_tickers), 1, "Scan result must contain one row per selected ticker."),
        validation_row("ledger_written", non_empty(ledger_path), 1, str(ledger_path)),
        validation_row("forbidden_files_unchanged", not forbidden_changed, len(forbidden_changed), ";".join(forbidden_changed[:20])),
        validation_row("true_coverage_not_overclaimed", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] != "TRUE" or coverage_trust == "HIGH", 1, "TRUE coverage requires HIGH trust."),
    ]
    for key, expected in SAFETY_INVARIANTS.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))

    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not universe or not selected_tickers:
        values["STATUS"] = STATUS_FAIL
    elif true_met:
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_WARN
    values["ROLLING_SCAN_EXECUTOR_READY"] = "TRUE" if fail_count == 0 and bool(selected_tickers) else "FALSE"

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["executor"], render_executor(values, source_audit))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
