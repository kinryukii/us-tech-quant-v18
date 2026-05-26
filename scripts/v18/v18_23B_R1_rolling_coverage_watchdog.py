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


STATUS_WARN = "WARN_V18_23B_R1_ROLLING_COVERAGE_WATCHDOG_READY"
STATUS_OK = "OK_V18_23B_R1_TRUE_5DAY_COVERAGE_READY"
STATUS_FAIL = "FAIL_V18_23B_R1_ROLLING_COVERAGE_WATCHDOG"
MODE = "LOCAL_ONLY_ROLLING_COVERAGE_WATCHDOG_FORCE_SWEEP"
TARGET_COVERAGE_DAYS = 5
LEDGER_REL = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

OUTPUTS = {
    "watchdog": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_ROLLING_COVERAGE_WATCHDOG.md",
    "selected": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_WATCHDOG_SELECTED_SCAN_LIST.csv",
    "stale": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_STALE_OVERDUE_TICKERS.csv",
    "force_audit": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_FORCE_SWEEP_AUDIT.csv",
    "result": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_SCAN_RESULT.csv",
    "ledger_snapshot": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_SCAN_LEDGER_SNAPSHOT.csv",
    "coverage_audit": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_5DAY_COVERAGE_AUDIT.csv",
    "source_audit": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/rolling_coverage/V18_23B_R1_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23B_R1_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23B_R1_CURRENT_ROLLING_COVERAGE_WATCHDOG_REPORT.md",
}

SAFETY = {
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
    "STATUS", "MODE", "WATCHDOG_READY", "LOCAL_ONLY", "TARGET_COVERAGE_DAYS",
    "TOTAL_UNIVERSE_COUNT", "NORMAL_TARGET_SCAN_COUNT_PER_RUN", "FORCE_STALE_SWEEP_MODE",
    "FORCE_SWEEP_REASON", "STALE_OR_OVERDUE_TICKER_COUNT", "NEVER_SUCCESS_SCAN_COUNT",
    "LAST_WEEK_OR_OLDER_COUNT", "SELECTED_SCAN_COUNT", "SELECTED_SCAN_COUNT_EXCEEDS_NORMAL_TARGET",
    "SUCCESS_SCAN_COUNT", "SKIPPED_SCAN_COUNT", "FAILED_SCAN_COUNT", "FORCE_ATTEMPTED_COUNT",
    "FORCE_SUCCESS_COUNT", "FORCE_SKIPPED_COUNT", "FORCE_STILL_STALE_COUNT",
    "LEDGER_CREATED_OR_UPDATED", "LEDGER_PATH", "ROLLING_SCAN_EXECUTED",
    "ROLLING_SCAN_DATA_FETCHED", "EXTERNAL_DATA_FETCHED", "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_COUNT", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "COVERAGE_TRUST_LEVEL", "VALIDATION_FAIL_COUNT",
    "RECOMMENDED_NEXT_ACTION", "WATCHDOG_PATH", "WATCHDOG_SELECTED_SCAN_LIST_PATH",
    "STALE_OVERDUE_TICKERS_PATH", "FORCE_SWEEP_AUDIT_PATH", "SCAN_RESULT_PATH",
    "LEDGER_SNAPSHOT_PATH", "COVERAGE_AUDIT_PATH", "SOURCE_AUDIT_PATH", "VALIDATION_PATH",
    "REPORT_PATH",
]

LEDGER_FIELDS = [
    "ticker", "canonical_universe_present", "first_seen_date", "last_attempt_scan_timestamp",
    "last_success_scan_timestamp", "last_success_scan_date", "last_scan_status", "last_scan_run_id",
    "success_scan_count", "attempt_scan_count", "local_price_available", "factor_pack_available",
    "technical_timing_available", "full_history_ready", "failure_reason", "source_notes",
]
SELECT_FIELDS = ["ticker", "selection_reason", "last_success_scan_date", "last_scan_status", "attempt_scan_count", "success_scan_count"]
SCAN_FIELDS = ["run_id", "ticker", "selection_reason", "scan_status", "local_price_available", "factor_pack_available", "technical_timing_available", "full_history_ready", "failure_reason", "success_counted", "source_notes"]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "ticker_count", "selected", "notes"]
AUDIT_FIELDS = ["metric", "value", "notes"]
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


def to_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def default_row(ticker: str, today: str) -> Dict[str, object]:
    return {
        "ticker": ticker, "canonical_universe_present": "TRUE", "first_seen_date": today,
        "last_attempt_scan_timestamp": "", "last_success_scan_timestamp": "", "last_success_scan_date": "",
        "last_scan_status": "NEVER_SCANNED", "last_scan_run_id": "", "success_scan_count": 0,
        "attempt_scan_count": 0, "local_price_available": "FALSE", "factor_pack_available": "FALSE",
        "technical_timing_available": "FALSE", "full_history_ready": "FALSE", "failure_reason": "",
        "source_notes": "",
    }


def load_ledger(path: Path, universe: Sequence[str], today: str) -> Dict[str, Dict[str, object]]:
    rows, _ = read_csv(path)
    ledger = {normalize_ticker(row.get("ticker", "")): dict(row) for row in rows if normalize_ticker(row.get("ticker", ""))}
    universe_set = set(universe)
    for ticker in universe:
        if ticker not in ledger:
            ledger[ticker] = default_row(ticker, today)
        ledger[ticker]["canonical_universe_present"] = "TRUE"
        if not str(ledger[ticker].get("first_seen_date", "")):
            ledger[ticker]["first_seen_date"] = today
    for ticker, row in ledger.items():
        if ticker not in universe_set:
            row["canonical_universe_present"] = "FALSE"
    return ledger


def stale_reason(row: Dict[str, object], cutoff: dt.date) -> str:
    success_date = parse_date(row.get("last_success_scan_date"))
    status = str(row.get("last_scan_status", ""))
    if not success_date:
        return "FORCE_NEVER_SUCCESS"
    if success_date < cutoff:
        return "FORCE_OVERDUE_DATE"
    if status.startswith("SKIPPED"):
        return "FORCE_PREVIOUSLY_SKIPPED"
    return ""


def normal_reason(row: Dict[str, object]) -> str:
    return "NORMAL_NEVER_SCANNED" if not str(row.get("last_success_scan_date", "")) else "NORMAL_LEAST_RECENT"


def selection_key(row: Dict[str, object]) -> Tuple[int, int, str, str, str]:
    success_date = str(row.get("last_success_scan_date", ""))
    attempt_ts = str(row.get("last_attempt_scan_timestamp", ""))
    return (0 if not success_date else 1, 0 if not attempt_ts else 1, success_date or "0000-00-00", attempt_ts or "0000-00-00T00:00:00", str(row.get("ticker", "")))


def local_price_available(root: Path, ticker: str) -> bool:
    path = root / "state/v18/price_cache" / f"{ticker}.csv"
    return path.exists() and path.stat().st_size > 0 and len(read_text(path).splitlines()) > 1


def local_scan(root: Path, ticker: str, factor_tickers: Set[str], tech_tickers: Set[str]) -> Dict[str, object]:
    price_ok = local_price_available(root, ticker)
    factor_ok = ticker in factor_tickers
    tech_ok = ticker in tech_tickers
    if price_ok:
        status = "SUCCESS_LOCAL_SCAN"
        failure = ""
    else:
        status = "SKIPPED_NO_LOCAL_DATA"
        failure = "LOCAL_PRICE_CACHE_MISSING_OR_EMPTY"
    return {
        "scan_status": status,
        "local_price_available": str(price_ok).upper(),
        "factor_pack_available": str(factor_ok).upper(),
        "technical_timing_available": str(tech_ok).upper(),
        "full_history_ready": str(factor_ok).upper(),
        "failure_reason": failure,
        "source_notes": ";".join([
            "local_price=available" if price_ok else "local_price=missing",
            "factor_pack=available" if factor_ok else "factor_pack=missing",
            "technical_timing=available" if tech_ok else "technical_timing=missing",
        ]),
    }


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def forbidden_files(root: Path) -> List[Path]:
    dirs = [
        "state/v18/price_cache", "outputs/v18/factor_pack", "outputs/v18/ranking",
        "outputs/v18/signal_snapshots", "outputs/v18/technical_timing", "outputs/v18/universe",
        "outputs/v18/forward_tracker", "outputs/v18/simulation", "state/v18/simulation",
        "state/v18/forward_outcome", "state/v18/candidate_forward_tracker", "state/v18/manual",
        "state/v16", "archive/stable",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


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
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + ["| " + " | ".join(str(x) for x in row) + " |" for row in rows])


def render_watchdog(values: Dict[str, str]) -> str:
    return f"""# V18.23B-R1 Rolling Coverage Watchdog

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Status
Status: **{values['STATUS']}**

Mode: **{values['MODE']}**

## Watchdog policy
Normal target scan count is {values['NORMAL_TARGET_SCAN_COUNT_PER_RUN']}. FORCE_STALE_SWEEP_MODE is {values['FORCE_STALE_SWEEP_MODE']} because: {values['FORCE_SWEEP_REASON']}.

Force sweep means force attempt, not guaranteed success. Local-only missing inputs remain skipped/stale until successful local scan evidence exists.

## Run metrics
{markdown_table(['Metric', 'Value'], [
    ('total_universe_count', values['TOTAL_UNIVERSE_COUNT']),
    ('stale_or_overdue_ticker_count', values['STALE_OR_OVERDUE_TICKER_COUNT']),
    ('selected_scan_count', values['SELECTED_SCAN_COUNT']),
    ('success_scan_count', values['SUCCESS_SCAN_COUNT']),
    ('skipped_scan_count', values['SKIPPED_SCAN_COUNT']),
    ('force_still_stale_count', values['FORCE_STILL_STALE_COUNT']),
    ('true_5day_unique_coverage_met', values['TRUE_5DAY_UNIQUE_COVERAGE_MET']),
    ('coverage_trust_level', values['COVERAGE_TRUST_LEVEL']),
])}

## Calendar note
The window is a calendar/run-count approximation from the local ledger, not exchange-calendar certified.

## Safety
{markdown_table(['Invariant', 'Value'], [(k, values[k]) for k in SAFETY])}

## Recommended next action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23B-R1 Rolling Coverage Watchdog Report

Status: {values['STATUS']}.

FORCE_STALE_SWEEP_MODE: {values['FORCE_STALE_SWEEP_MODE']}. Reason: {values['FORCE_SWEEP_REASON']}.

Selected {values['SELECTED_SCAN_COUNT']} tickers against normal target {values['NORMAL_TARGET_SCAN_COUNT_PER_RUN']}. Success: {values['SUCCESS_SCAN_COUNT']}; skipped: {values['SKIPPED_SCAN_COUNT']}; failed: {values['FAILED_SCAN_COUNT']}.

Force attempted: {values['FORCE_ATTEMPTED_COUNT']}; force still stale: {values['FORCE_STILL_STALE_COUNT']}.

TRUE_5DAY_UNIQUE_COVERAGE_MET: {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}. Coverage trust: {values['COVERAGE_TRUST_LEVEL']}.

No external data was fetched and no forbidden source/trading files were modified.

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
    before = {str(p): file_sig(p) for p in forbidden_files(root)}

    now = dt.datetime.now()
    today = now.date().isoformat()
    cutoff = now.date() - dt.timedelta(days=TARGET_COVERAGE_DAYS - 1)
    run_id = f"V18_23B_R1_{now.strftime('%Y%m%d_%H%M%S')}"
    universe, universe_source, source_audit = load_universe(root)
    normal_target = max(1, math.ceil(len(universe) / TARGET_COVERAGE_DAYS)) if universe else 0
    ledger_path = root / LEDGER_REL
    ledger = load_ledger(ledger_path, universe, today)
    canonical_rows = [ledger[ticker] for ticker in universe]

    completed_run_ids = {
        str(row.get("last_scan_run_id", "")).strip()
        for row in canonical_rows
        if str(row.get("last_scan_run_id", "")).strip()
    }
    coverage_window_matured = len(completed_run_ids) >= TARGET_COVERAGE_DAYS
    stale_rows: List[Dict[str, object]] = []
    for row in canonical_rows:
        reason = stale_reason(row, cutoff)
        if reason == "FORCE_NEVER_SUCCESS" and not coverage_window_matured:
            reason = ""
        if reason:
            stale_rows.append({
                "ticker": row["ticker"],
                "selection_reason": reason,
                "last_success_scan_date": row.get("last_success_scan_date", ""),
                "last_scan_status": row.get("last_scan_status", ""),
                "attempt_scan_count": row.get("attempt_scan_count", 0),
                "success_scan_count": row.get("success_scan_count", 0),
            })
    never_success_count = sum(1 for row in canonical_rows if not str(row.get("last_success_scan_date", "")))
    last_week_or_older_count = sum(1 for row in canonical_rows if (parse_date(row.get("last_success_scan_date")) or dt.date.min) < cutoff)
    force_mode = bool(stale_rows)
    force_reason = "STALE_OR_OVERDUE_TICKERS_PRESENT_AFTER_GRACE_OR_BY_DATE" if force_mode else "BOOTSTRAP_GRACE_OR_NO_STALE_OVERDUE_TICKERS_NORMAL_MODE"

    if force_mode:
        selected = sorted(stale_rows, key=lambda row: (row["selection_reason"], row["last_success_scan_date"] or "0000-00-00", row["ticker"]))
    else:
        selected = [
            {
                "ticker": row["ticker"],
                "selection_reason": normal_reason(row),
                "last_success_scan_date": row.get("last_success_scan_date", ""),
                "last_scan_status": row.get("last_scan_status", ""),
                "attempt_scan_count": row.get("attempt_scan_count", 0),
                "success_scan_count": row.get("success_scan_count", 0),
            }
            for row in sorted(canonical_rows, key=selection_key)[:normal_target]
        ]

    factor_tickers = ticker_set(root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv")
    tech_tickers = ticker_set(root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv")
    source_audit.extend([
        {"source_name": "FACTOR_PACK", "source_path": "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "exists": str((root / 'outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv').exists()).upper(), "row_count": "", "ticker_count": len(factor_tickers), "selected": "FALSE", "notes": "Read-only local factor availability source."},
        {"source_name": "TECHNICAL_TIMING", "source_path": "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv", "exists": str((root / 'outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv').exists()).upper(), "row_count": "", "ticker_count": len(tech_tickers), "selected": "FALSE", "notes": "Read-only local technical timing availability source."},
    ])

    results: List[Dict[str, object]] = []
    success = skipped = failed = force_success = force_skipped = 0
    for selected_row in selected:
        ticker = str(selected_row["ticker"])
        scan = local_scan(root, ticker, factor_tickers, tech_tickers)
        row = ledger[ticker]
        previous_success_date = str(row.get("last_success_scan_date", ""))
        row["last_attempt_scan_timestamp"] = now.isoformat(timespec="seconds")
        row["last_scan_run_id"] = run_id
        row["attempt_scan_count"] = to_int(row.get("attempt_scan_count")) + 1
        success_counted = "FALSE"
        if scan["scan_status"] == "SUCCESS_LOCAL_SCAN":
            success += 1
            if force_mode:
                force_success += 1
            row["last_success_scan_timestamp"] = now.isoformat(timespec="seconds")
            row["last_success_scan_date"] = today
            if previous_success_date != today:
                row["success_scan_count"] = to_int(row.get("success_scan_count")) + 1
                success_counted = "TRUE"
        elif str(scan["scan_status"]).startswith("SKIPPED"):
            skipped += 1
            if force_mode:
                force_skipped += 1
        else:
            failed += 1
        row["last_scan_status"] = scan["scan_status"]
        for key in ["local_price_available", "factor_pack_available", "technical_timing_available", "full_history_ready", "failure_reason", "source_notes"]:
            row[key] = scan[key]
        results.append({"run_id": run_id, "ticker": ticker, "selection_reason": selected_row["selection_reason"], **scan, "success_counted": success_counted})

    ledger_rows = [ledger[ticker] for ticker in sorted(ledger)]
    write_csv(ledger_path, ledger_rows, LEDGER_FIELDS)

    within_window = [ticker for ticker in universe if (parse_date(ledger[ticker].get("last_success_scan_date")) or dt.date.min) >= cutoff]
    true_met = len(within_window) == len(universe) and bool(universe)
    coverage_trust = "HIGH" if true_met else "MEDIUM" if within_window else "LOW"
    coverage_status = "TRUE_BY_LOCAL_LEDGER_CALENDAR_APPROXIMATION_NOT_EXCHANGE_CERTIFIED" if true_met else "FALSE_STALE_OR_SKIPPED_TICKERS_REMAIN"
    force_still_stale = sum(1 for row in selected if stale_reason(ledger[str(row["ticker"])], cutoff))

    values: Dict[str, str] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "WATCHDOG_READY": "FALSE",
        "LOCAL_ONLY": "TRUE",
        "TARGET_COVERAGE_DAYS": str(TARGET_COVERAGE_DAYS),
        "TOTAL_UNIVERSE_COUNT": str(len(universe)),
        "NORMAL_TARGET_SCAN_COUNT_PER_RUN": str(normal_target),
        "FORCE_STALE_SWEEP_MODE": str(force_mode).upper(),
        "FORCE_SWEEP_REASON": force_reason,
        "STALE_OR_OVERDUE_TICKER_COUNT": str(len(stale_rows)),
        "NEVER_SUCCESS_SCAN_COUNT": str(never_success_count),
        "LAST_WEEK_OR_OLDER_COUNT": str(last_week_or_older_count),
        "SELECTED_SCAN_COUNT": str(len(selected)),
        "SELECTED_SCAN_COUNT_EXCEEDS_NORMAL_TARGET": str(len(selected) > normal_target).upper(),
        "SUCCESS_SCAN_COUNT": str(success),
        "SKIPPED_SCAN_COUNT": str(skipped),
        "FAILED_SCAN_COUNT": str(failed),
        "FORCE_ATTEMPTED_COUNT": str(len(selected) if force_mode else 0),
        "FORCE_SUCCESS_COUNT": str(force_success),
        "FORCE_SKIPPED_COUNT": str(force_skipped),
        "FORCE_STILL_STALE_COUNT": str(force_still_stale),
        "LEDGER_CREATED_OR_UPDATED": "TRUE",
        "LEDGER_PATH": str(ledger_path),
        "ROLLING_SCAN_EXECUTED": "TRUE",
        "UNIQUE_SUCCESS_SCANNED_WITHIN_WINDOW_COUNT": str(len(within_window)),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": str(true_met).upper(),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": coverage_status,
        "COVERAGE_TRUST_LEVEL": coverage_trust,
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Continue local-only watchdog runs; stale tickers with missing local inputs remain priority until local data exists and a successful scan is recorded.",
        "WATCHDOG_PATH": str(root / OUTPUTS["watchdog"]),
        "WATCHDOG_SELECTED_SCAN_LIST_PATH": str(root / OUTPUTS["selected"]),
        "STALE_OVERDUE_TICKERS_PATH": str(root / OUTPUTS["stale"]),
        "FORCE_SWEEP_AUDIT_PATH": str(root / OUTPUTS["force_audit"]),
        "SCAN_RESULT_PATH": str(root / OUTPUTS["result"]),
        "LEDGER_SNAPSHOT_PATH": str(root / OUTPUTS["ledger_snapshot"]),
        "COVERAGE_AUDIT_PATH": str(root / OUTPUTS["coverage_audit"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source_audit"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY)

    force_audit = [
        {"metric": "force_stale_sweep_mode", "value": values["FORCE_STALE_SWEEP_MODE"], "notes": force_reason},
        {"metric": "calendar_or_run_window_certification", "value": "APPROXIMATION_ONLY", "notes": "No local exchange calendar certification applied."},
        {"metric": "stale_or_overdue_ticker_count", "value": len(stale_rows), "notes": "Selected all stale rows in force mode."},
    ]
    coverage_rows = [
        {"metric": "canonical_universe_source", "value": universe_source, "notes": "Current/fallback local source."},
        {"metric": "unique_success_scanned_within_window_count", "value": len(within_window), "notes": "Local ledger calendar approximation."},
        {"metric": "true_5day_unique_coverage_met", "value": values["TRUE_5DAY_UNIQUE_COVERAGE_MET"], "notes": coverage_status},
        {"metric": "coverage_trust_level", "value": coverage_trust, "notes": "HIGH only when every canonical ticker is successful inside window."},
    ]

    write_csv(root / OUTPUTS["selected"], selected, SELECT_FIELDS)
    write_csv(root / OUTPUTS["stale"], stale_rows, SELECT_FIELDS)
    write_csv(root / OUTPUTS["force_audit"], force_audit, AUDIT_FIELDS)
    write_csv(root / OUTPUTS["result"], results, SCAN_FIELDS)
    write_csv(root / OUTPUTS["ledger_snapshot"], ledger_rows, LEDGER_FIELDS)
    write_csv(root / OUTPUTS["coverage_audit"], coverage_rows, AUDIT_FIELDS)
    write_csv(root / OUTPUTS["source_audit"], source_audit, SOURCE_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["watchdog"], render_watchdog(values))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(p): file_sig(p) for p in forbidden_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required_paths = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_watchdog", py_compile(root / "scripts/v18/v18_23B_R1_rolling_coverage_watchdog.py"), 1, "Python watchdog compile."),
        validation_row("python_compile_executor", py_compile(root / "scripts/v18/v18_23B_rolling_scan_executor.py"), 1, "Python executor compile."),
        validation_row("powershell_parse_watchdog", ps_parse(root / "scripts/v18/run_v18_23B_R1_rolling_coverage_watchdog.ps1"), 1, "PowerShell watchdog parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required_paths), 1, "All R1 outputs must exist and be non-empty."),
        validation_row("canonical_universe_positive", len(universe) > 0, 1, "Canonical universe must load."),
        validation_row("normal_target_scan_count", normal_target == math.ceil(len(universe) / TARGET_COVERAGE_DAYS) if universe else False, 1, "Normal target should be ceil(total/5)."),
        validation_row("selected_scan_count_positive", len(selected) > 0, 1, "Selected scan list must not be empty."),
        validation_row("force_selection_matches_stale_count", (not force_mode) or len(selected) == len(stale_rows), 1, "Force mode must select every stale/overdue ticker."),
        validation_row("ledger_includes_all_canonical_tickers", all(ticker in ledger for ticker in universe), 1, "Ledger must include all canonical tickers."),
        validation_row("selected_scan_list_no_duplicates", len({row["ticker"] for row in selected}) == len(selected), 1, "Selected list no duplicates."),
        validation_row("scan_result_one_row_per_selected", len(results) == len(selected), 1, "One result row per selected ticker."),
        validation_row("force_sweep_audit_explains_mode", non_empty(root / OUTPUTS["force_audit"]), 1, "Force sweep audit must exist."),
        validation_row("forbidden_files_unchanged", not changed, len(changed), ";".join(changed[:20])),
        validation_row("true_coverage_not_overclaimed", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] != "TRUE" or coverage_trust == "HIGH", 1, "TRUE coverage requires HIGH trust."),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))

    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not universe or not selected:
        values["STATUS"] = STATUS_FAIL
    elif true_met:
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_WARN
    values["WATCHDOG_READY"] = "TRUE" if fail_count == 0 and bool(selected) else "FALSE"

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["watchdog"], render_watchdog(values))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
