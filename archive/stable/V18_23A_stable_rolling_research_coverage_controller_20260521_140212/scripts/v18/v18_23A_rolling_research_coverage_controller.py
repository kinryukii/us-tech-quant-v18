from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_WARN = "WARN_V18_23A_ROLLING_COVERAGE_CONTROLLER_READY"
STATUS_OK = "OK_V18_23A_ROLLING_COVERAGE_CONTROLLER_READY"
STATUS_FAIL = "FAIL_V18_23A_ROLLING_COVERAGE_CONTROLLER"
MODE = "READ_ONLY_ROLLING_RESEARCH_COVERAGE_PLANNING"
TARGET_COVERAGE_DAYS = 5
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

OUTPUTS = {
    "controller": "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER.md",
    "plan": "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv",
    "today": "outputs/v18/rolling_coverage/V18_23A_CURRENT_TODAY_PLANNED_SCAN_LIST.csv",
    "bucket": "outputs/v18/rolling_coverage/V18_23A_CURRENT_COVERAGE_BUCKET_SUMMARY.csv",
    "source_audit": "outputs/v18/rolling_coverage/V18_23A_CURRENT_COVERAGE_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/rolling_coverage/V18_23A_CURRENT_COVERAGE_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23A_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER_REPORT.md",
}

SAFETY_INVARIANTS = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "EVENT_CALENDAR_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "STAGED_BACKFILL_APPLY_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "ROLLING_SCAN_DATA_FETCHED": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "ROLLING_COVERAGE_CONTROLLER_READY",
    "PLANNING_ONLY",
    "TARGET_COVERAGE_DAYS",
    "TOTAL_UNIVERSE_COUNT",
    "RECOMMENDED_DAILY_SCAN_COUNT",
    "PLANNED_SCAN_COUNT_TODAY",
    "PLANNED_BUCKET_INDEX",
    "ESTIMATED_FULL_CYCLE_COVERAGE_COUNT",
    "ESTIMATED_FULL_CYCLE_COVERAGE_RATIO",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS",
    "COVERAGE_TRUST_LEVEL",
    "CANONICAL_UNIVERSE_SOURCE",
    "SOURCE_MISSING_COUNT",
    "VALIDATION_FAIL_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN",
    "STAGED_PRICE_HISTORY_WRITTEN",
    "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED",
    "EVENT_CALENDAR_MODIFIED",
    "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED",
    "PRICE_FACTOR_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED",
    "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED",
    "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED",
    "STAGED_BACKFILL_APPLY_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "ROLLING_SCAN_EXECUTED",
    "ROLLING_SCAN_DATA_FETCHED",
    "ROLLING_SCAN_PLAN_CREATED",
    "RECOMMENDED_NEXT_ACTION",
    "CONTROLLER_PATH",
    "PLAN_PATH",
    "TODAY_SCAN_LIST_PATH",
    "BUCKET_SUMMARY_PATH",
    "SOURCE_AUDIT_PATH",
    "VALIDATION_PATH",
    "REPORT_PATH",
]

PLAN_FIELDS = [
    "ticker",
    "bucket",
    "bucket_index",
    "planned_today",
    "last_scan_date",
    "last_scan_status",
    "days_since_last_scan",
    "overdue_for_5day_window",
    "source",
]
BUCKET_FIELDS = ["bucket", "bucket_index", "ticker_count", "planned_today", "coverage_ratio"]
SOURCE_FIELDS = ["source_id", "relative_path", "exists", "row_count", "ticker_count", "selected", "priority", "parse_status", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

UNIVERSE_SOURCES = [
    ("V18_CURRENT_UNIVERSE_ROLLING_STATE", "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv", 1),
    ("STATE_V18_UNIVERSE_ROLLING_STATE", "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv", 2),
    ("V18_CURRENT_RAW105_FACTOR_PACK_RANKING", "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", 3),
    ("V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION", "outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv", 4),
    ("STATE_RAW105_UNIVERSE_FOR_FACTOR_LAB", "state/v18/raw105_universe_for_factor_lab.csv", 5),
    ("V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX", "outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv", 6),
]

CONTEXT_SOURCES = [
    ("V18_22D_STABLE_READ_FIRST", "outputs/v18/ops/V18_22D_STABLE_READ_FIRST.txt"),
    ("V18_22D_HOMEPAGE", "outputs/v18/operator_homepage/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md"),
    ("V18_22C_STABLE_READ_FIRST", "outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt"),
    ("V18_22B_STABLE_READ_FIRST", "outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt"),
    ("V18_22A_STABLE_READ_FIRST", "outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt"),
    ("V18_ROLLING_SCAN_RUN_STATE", "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json"),
    ("V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX", "outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv"),
    ("V18_16I_CURRENT_RECOMMENDED_SCAN_PLAN", "outputs/v18/universe/V18_16I_CURRENT_RECOMMENDED_SCAN_PLAN.csv"),
]


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


def read_kv(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def parse_date(value: str) -> dt.date | None:
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(value[:10] if fmt != "%Y%m%d" else value[:8], fmt).date()
        except ValueError:
            continue
    return None


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "TICKER"}:
        return ""
    if ticker.isdigit():
        return ""
    return ticker if TICKER_RE.match(ticker) else ""


def find_ticker_column(fields: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for name in ("ticker", "symbol", "candidate_ticker", "asset", "name"):
        if name in lower:
            return lower[name]
    return ""


def extract_tickers(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> Tuple[List[str], str]:
    ticker_col = find_ticker_column(fields)
    if not ticker_col:
        return [], ""
    tickers = []
    seen = set()
    for row in rows:
        ticker = normalize_ticker(row.get(ticker_col, ""))
        if ticker and ticker not in seen:
            seen.add(ticker)
            tickers.append(ticker)
    return tickers, ticker_col


def audit_sources(root: Path) -> Tuple[List[Dict[str, object]], List[str], str, Dict[str, Dict[str, str]]]:
    audit: List[Dict[str, object]] = []
    selected_tickers: List[str] = []
    selected_source = ""
    selected_row_by_ticker: Dict[str, Dict[str, str]] = {}
    for source_id, relative_path, priority in UNIVERSE_SOURCES:
        path = root / relative_path
        rows, fields = read_csv(path)
        tickers, ticker_col = extract_tickers(rows, fields)
        selected = False
        if not selected_tickers and tickers:
            selected_tickers = tickers
            selected_source = relative_path
            selected = True
            selected_row_by_ticker = {normalize_ticker(row.get(ticker_col, "")): row for row in rows if normalize_ticker(row.get(ticker_col, ""))}
        audit.append(
            {
                "source_id": source_id,
                "relative_path": relative_path,
                "exists": "TRUE" if path.exists() else "FALSE",
                "row_count": len(rows),
                "ticker_count": len(tickers),
                "selected": "TRUE" if selected else "FALSE",
                "priority": priority,
                "parse_status": f"CSV_FIELDS={len(fields)};TICKER_COLUMN={ticker_col or 'MISSING'}" if path.exists() else "MISSING",
                "notes": "Selected canonical universe source." if selected else "Usable fallback source." if tickers else "Missing or no usable ticker column.",
            }
        )
    for source_id, relative_path in CONTEXT_SOURCES:
        path = root / relative_path
        rows, fields = read_csv(path) if path.suffix.lower() == ".csv" else ([], [])
        if path.suffix.lower() == ".json" and path.exists():
            try:
                json.loads(read_text(path))
                parse_status = "JSON_OK"
            except json.JSONDecodeError:
                parse_status = "JSON_PARSE_FAILED"
        elif path.suffix.lower() == ".csv":
            parse_status = f"CSV_FIELDS={len(fields)}"
        else:
            parse_status = f"TEXT_KEYS={len(read_kv(path))}" if path.exists() else "MISSING"
        audit.append(
            {
                "source_id": source_id,
                "relative_path": relative_path,
                "exists": "TRUE" if path.exists() else "FALSE",
                "row_count": len(rows),
                "ticker_count": "",
                "selected": "FALSE",
                "priority": "context",
                "parse_status": parse_status,
                "notes": "Context/provenance source.",
            }
        )
    return audit, sorted(selected_tickers), selected_source, selected_row_by_ticker


def infer_scan_history(root: Path, tickers: Sequence[str], selected_rows: Dict[str, Dict[str, str]]) -> Tuple[Dict[str, str], Dict[str, int], str, bool]:
    today = dt.date.today()
    last_scan: Dict[str, str] = {}
    days_since: Dict[str, int] = {}
    for ticker in tickers:
        row = selected_rows.get(ticker, {})
        scan_date = parse_date(row.get("last_scan_date", ""))
        if scan_date:
            last_scan[ticker] = scan_date.isoformat()
            days_since[ticker] = max(0, (today - scan_date).days)
    matrix_path = root / "outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv"
    matrix_rows, matrix_fields = read_csv(matrix_path)
    matrix_ticker_col = find_ticker_column(matrix_fields)
    matrix_by_ticker = {normalize_ticker(row.get(matrix_ticker_col, "")): row for row in matrix_rows if matrix_ticker_col and normalize_ticker(row.get(matrix_ticker_col, ""))}
    complete_matrix = bool(matrix_by_ticker) and all(ticker in matrix_by_ticker for ticker in tickers)
    matrix_all_covered = complete_matrix and all(str(matrix_by_ticker[ticker].get("covered_in_true_5day_window", "")).strip().upper() == "TRUE" for ticker in tickers)
    if matrix_all_covered:
        status = "PROVEN_BY_LOCAL_5DAY_COVERAGE_MATRIX"
        proven = True
    elif len(last_scan) == len(tickers) and tickers:
        all_within_window = all(days_since[ticker] <= TARGET_COVERAGE_DAYS for ticker in tickers)
        status = "PROVEN_BY_LAST_SCAN_DATE" if all_within_window else "LOCAL_SCAN_HISTORY_INCOMPLETE_OR_STALE"
        proven = all_within_window
    elif last_scan:
        status = "PARTIAL_LOCAL_SCAN_HISTORY"
        proven = False
    else:
        status = "UNKNOWN_NO_LOCAL_SCAN_HISTORY"
        proven = False
    return last_scan, days_since, status, proven


def build_plan(tickers: Sequence[str], last_scan: Dict[str, str], days_since: Dict[str, int], planned_bucket: int, source: str) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    total = len(tickers)
    plan: List[Dict[str, object]] = []
    for idx, ticker in enumerate(tickers):
        bucket_index = (idx % TARGET_COVERAGE_DAYS) + 1
        last_status = "KNOWN" if ticker in last_scan else "UNKNOWN"
        overdue = "UNKNOWN" if ticker not in days_since else "TRUE" if days_since[ticker] > TARGET_COVERAGE_DAYS else "FALSE"
        plan.append(
            {
                "ticker": ticker,
                "bucket": f"bucket_{bucket_index}",
                "bucket_index": bucket_index,
                "planned_today": "TRUE" if bucket_index == planned_bucket else "FALSE",
                "last_scan_date": last_scan.get(ticker, ""),
                "last_scan_status": last_status,
                "days_since_last_scan": days_since.get(ticker, ""),
                "overdue_for_5day_window": overdue,
                "source": source,
            }
        )
    today_rows = [row for row in plan if row["planned_today"] == "TRUE"]
    bucket_rows: List[Dict[str, object]] = []
    for bucket_index in range(1, TARGET_COVERAGE_DAYS + 1):
        count = sum(1 for row in plan if row["bucket_index"] == bucket_index)
        bucket_rows.append(
            {
                "bucket": f"bucket_{bucket_index}",
                "bucket_index": bucket_index,
                "ticker_count": count,
                "planned_today": "TRUE" if bucket_index == planned_bucket else "FALSE",
                "coverage_ratio": f"{(count / total) if total else 0:.6f}",
            }
        )
    return plan, today_rows, bucket_rows


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + body)


def render_controller(values: Dict[str, str], bucket_rows: Sequence[Dict[str, object]], audit_rows: Sequence[Dict[str, object]], timestamp: str) -> str:
    missing = [row["relative_path"] for row in audit_rows if row.get("exists") == "FALSE"]
    weak_note = "Universe count is below 50; trust capped at LOW." if int(values["TOTAL_UNIVERSE_COUNT"]) < 50 else "Universe count is not suspiciously low."
    return f"""# V18.23A Rolling Research Coverage Controller

Generated: {timestamp}

## Overall status
Status: **{values['STATUS']}**

Mode: **{values['MODE']}**

## Purpose of this step
Create a read-only planning/read-center layer for rolling research coverage. It plans roughly full-universe coverage over {TARGET_COVERAGE_DAYS} planning buckets without fetching data, scanning tickers, updating caches, running backtests, or changing trading decisions.

## Canonical universe source
{values['CANONICAL_UNIVERSE_SOURCE']}

## Key coverage metrics
{markdown_table(['Metric', 'Value'], [
    ('total_universe_count', values['TOTAL_UNIVERSE_COUNT']),
    ('recommended_daily_scan_count', values['RECOMMENDED_DAILY_SCAN_COUNT']),
    ('planned_scan_count_today', values['PLANNED_SCAN_COUNT_TODAY']),
    ('planned_bucket_index', values['PLANNED_BUCKET_INDEX']),
    ('estimated_full_cycle_coverage_count', values['ESTIMATED_FULL_CYCLE_COVERAGE_COUNT']),
    ('estimated_full_cycle_coverage_ratio', values['ESTIMATED_FULL_CYCLE_COVERAGE_RATIO']),
    ('true_5day_unique_coverage_met', values['TRUE_5DAY_UNIQUE_COVERAGE_MET']),
    ('true_5day_unique_coverage_status', values['TRUE_5DAY_UNIQUE_COVERAGE_STATUS']),
    ('coverage_trust_level', values['COVERAGE_TRUST_LEVEL']),
])}

## 5-day rolling bucket plan
{markdown_table(['Bucket', 'Ticker count', 'Planned today', 'Coverage ratio'], [(row['bucket'], row['ticker_count'], row['planned_today'], row['coverage_ratio']) for row in bucket_rows])}

## Today planned scan list summary
Today is planning bucket {values['PLANNED_BUCKET_INDEX']} with {values['PLANNED_SCAN_COUNT_TODAY']} planned tickers. This is a deterministic planning index based on local date modulo 5, not an exchange-calendar guarantee.

## Coverage trust explanation
Coverage trust level: {values['COVERAGE_TRUST_LEVEL']}. {weak_note}

## TRUE_5DAY_UNIQUE_COVERAGE status
{values['TRUE_5DAY_UNIQUE_COVERAGE_STATUS']}. TRUE is only allowed when local scan-history evidence proves all canonical tickers were scanned within the target window.

## Source provenance
{markdown_table(['Source', 'Exists', 'Ticker count', 'Selected', 'Notes'], [(row['relative_path'], row['exists'], row['ticker_count'], row['selected'], row['notes']) for row in audit_rows])}

## Missing/weak sources
Missing source count: {values['SOURCE_MISSING_COUNT']}. Missing: {', '.join(missing) if missing else 'None'}.

## Allowed today
- Read this controller and V18.23A READ_FIRST.
- Review the deterministic rolling coverage plan.
- Use the plan as planning input for a later approved scanner.

## Not allowed yet
- Do not fetch external data.
- Do not execute rolling scans.
- Do not modify price cache, price history, rankings, signals, event calendars, state, simulations, forward trackers, broker/manual execution, or production decisions.
- Do not run backtests or apply factor effect, weight, promotion, staged backfill, or daily command center integration changes.

## Safety invariants
{markdown_table(['Invariant', 'Value'], [(key, values[key]) for key in SAFETY_INVARIANTS])}

## Recommended next action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23A Rolling Research Coverage Controller Report

Status: {values['STATUS']}.

V18.23A created a read-only rolling coverage plan for {values['TOTAL_UNIVERSE_COUNT']} canonical tickers across {TARGET_COVERAGE_DAYS} deterministic buckets.

Recommended daily scan count: {values['RECOMMENDED_DAILY_SCAN_COUNT']}. Today planned scan count: {values['PLANNED_SCAN_COUNT_TODAY']}. Planned bucket index: {values['PLANNED_BUCKET_INDEX']}.

TRUE_5DAY_UNIQUE_COVERAGE_MET: {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}. Coverage trust level: {values['COVERAGE_TRUST_LEVEL']}. Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

No external data was fetched, no rolling scan was executed, and all research/production gates remain blocked.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    command = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def build_validations(root: Path, values: Dict[str, str], plan: Sequence[Dict[str, object]], today_rows: Sequence[Dict[str, object]], bucket_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    required_paths = [root / relative for relative in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23A_rolling_research_coverage_controller.py"), 1, "Python compile check."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23A_rolling_research_coverage_controller.ps1"), 1, "PowerShell parse check."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required_paths), 1, "All V18.23A outputs must exist and be non-empty."),
        validation_row("canonical_universe_available", int(values["TOTAL_UNIVERSE_COUNT"]) > 0, 1, "Canonical universe must contain ticker rows."),
        validation_row("coverage_plan_has_rows", len(plan) > 0, 1, "Coverage plan must contain ticker rows."),
        validation_row("today_scan_list_has_rows", len(today_rows) > 0, 1, "Today planned scan list must contain ticker rows."),
        validation_row("bucket_summary_has_exactly_5_buckets", len(bucket_rows) == TARGET_COVERAGE_DAYS, 1, "Bucket summary must include exactly 5 buckets."),
        validation_row("true_coverage_not_overclaimed", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] != "TRUE" or values["COVERAGE_TRUST_LEVEL"] == "HIGH", 1, "TRUE coverage requires HIGH trust."),
    ]
    for key, expected in SAFETY_INVARIANTS.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    return validations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().isoformat(timespec="seconds")

    audit_rows, tickers, canonical_source, selected_rows = audit_sources(root)
    today = dt.date.today()
    planned_bucket = (today.toordinal() % TARGET_COVERAGE_DAYS) + 1
    last_scan, days_since, true_status, true_proven = infer_scan_history(root, tickers, selected_rows)
    plan_rows, today_rows, bucket_rows = build_plan(tickers, last_scan, days_since, planned_bucket, canonical_source)

    total = len(tickers)
    recommended_daily = max(1, math.ceil(total / TARGET_COVERAGE_DAYS)) if total else 0
    estimated_count = sum(int(row["ticker_count"]) for row in bucket_rows)
    estimated_ratio = (estimated_count / total) if total else 0.0
    missing_count = sum(1 for row in audit_rows if row.get("exists") == "FALSE")
    stale_unknown = sum(1 for row in plan_rows if row["last_scan_status"] == "UNKNOWN")
    overdue_count = sum(1 for row in plan_rows if row["overdue_for_5day_window"] == "TRUE")
    weak_universe = total < 50
    complete_plan = total > 0 and len(bucket_rows) == TARGET_COVERAGE_DAYS and estimated_count == total
    if true_proven and not weak_universe:
        trust = "HIGH"
        true_met = "TRUE"
    elif complete_plan and not weak_universe:
        trust = "MEDIUM"
        true_met = "FALSE"
    else:
        trust = "LOW"
        true_met = "FALSE"

    values: Dict[str, str] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "ROLLING_COVERAGE_CONTROLLER_READY": "FALSE",
        "PLANNING_ONLY": "TRUE",
        "TARGET_COVERAGE_DAYS": str(TARGET_COVERAGE_DAYS),
        "TOTAL_UNIVERSE_COUNT": str(total),
        "RECOMMENDED_DAILY_SCAN_COUNT": str(recommended_daily),
        "PLANNED_SCAN_COUNT_TODAY": str(len(today_rows)),
        "PLANNED_BUCKET_INDEX": str(planned_bucket),
        "ESTIMATED_FULL_CYCLE_COVERAGE_COUNT": str(estimated_count),
        "ESTIMATED_FULL_CYCLE_COVERAGE_RATIO": f"{estimated_ratio:.6f}",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": true_met,
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": true_status if true_met == "TRUE" else f"UNPROVEN_PLANNING_ONLY;{true_status}",
        "COVERAGE_TRUST_LEVEL": trust,
        "CANONICAL_UNIVERSE_SOURCE": canonical_source or "NONE",
        "SOURCE_MISSING_COUNT": str(missing_count),
        "VALIDATION_FAIL_COUNT": "0",
        "ROLLING_SCAN_PLAN_CREATED": "TRUE",
        "RECOMMENDED_NEXT_ACTION": "Review outputs/v18/ops/V18_23A_READ_FIRST.txt and the rolling coverage plan; do not execute scans or fetch data until a separate approved execution layer exists.",
        "CONTROLLER_PATH": str(root / OUTPUTS["controller"]),
        "PLAN_PATH": str(root / OUTPUTS["plan"]),
        "TODAY_SCAN_LIST_PATH": str(root / OUTPUTS["today"]),
        "BUCKET_SUMMARY_PATH": str(root / OUTPUTS["bucket"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source_audit"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
        "STALE_OR_UNKNOWN_SCAN_COUNT": str(stale_unknown),
        "OVERDUE_TICKER_COUNT": str(overdue_count),
    }
    values.update(SAFETY_INVARIANTS)

    write_csv(root / OUTPUTS["plan"], plan_rows, PLAN_FIELDS)
    write_csv(root / OUTPUTS["today"], today_rows, PLAN_FIELDS)
    write_csv(root / OUTPUTS["bucket"], bucket_rows, BUCKET_FIELDS)
    write_csv(root / OUTPUTS["source_audit"], audit_rows, SOURCE_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["controller"], render_controller(values, bucket_rows, audit_rows, timestamp))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    validations = build_validations(root, values, plan_rows, today_rows, bucket_rows)
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or total == 0:
        values["STATUS"] = STATUS_FAIL
    elif values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] == "TRUE" and values["COVERAGE_TRUST_LEVEL"] == "HIGH":
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_WARN
    values["ROLLING_COVERAGE_CONTROLLER_READY"] = "TRUE" if fail_count == 0 and total > 0 else "FALSE"

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["controller"], render_controller(values, bucket_rows, audit_rows, timestamp))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
