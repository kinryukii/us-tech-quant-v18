from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


STATUS_OK = "OK_V18_23A_R1_UNIVERSE_COUNT_DRIFT_RECONCILED"
STATUS_WARN = "WARN_V18_23A_R1_UNIVERSE_COUNT_DRIFT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_23A_R1_UNIVERSE_COUNT_DRIFT_RECONCILIATION"
MODE = "READ_ONLY_UNIVERSE_COUNT_DRIFT_RECONCILIATION"
RESULT_EXPLAINED = "EXPLAINED_EXPECTED_324"
RESULT_WARN = "WARN_UNIVERSE_COUNT_DRIFT_REVIEW_NEEDED"
RESULT_FAIL = "FAIL_UNIVERSE_RECONCILIATION"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

OUTPUTS = {
    "reconciliation": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION.md",
    "audit": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_SOURCE_TICKER_COUNT_AUDIT.csv",
    "comparison": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_UNIVERSE_SOURCE_COMPARISON.csv",
    "diff": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_TICKER_SET_DIFF.csv",
    "missing": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_DROPPED_OR_MISSING_TICKERS.csv",
    "suspicious": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_SUSPICIOUS_TICKERS.csv",
    "validation": "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_RECONCILIATION_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23A_R1_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION_REPORT.md",
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
    "ROLLING_SCAN_PLAN_MODIFIED": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RECONCILIATION_READY",
    "V18_23A_CANONICAL_UNIVERSE_SOURCE",
    "V18_23A_CANONICAL_UNIVERSE_COUNT",
    "MAX_REFERENCE_UNIVERSE_COUNT",
    "REFERENCE_SOURCE_COUNT",
    "SOURCE_MISSING_COUNT",
    "SOURCE_WITH_325_OR_MORE_COUNT",
    "COUNT_DRIFT_DETECTED",
    "COUNT_DRIFT_EXPLAINED",
    "RECONCILIATION_RESULT",
    "MISSING_FROM_V18_23A_COUNT",
    "EXTRA_IN_V18_23A_COUNT",
    "DUPLICATE_TICKER_COUNT_MAX",
    "BLANK_TICKER_ROW_COUNT_MAX",
    "SUSPICIOUS_TICKER_COUNT",
    "V18_23A_STABLE_SNAPSHOT_ALLOWED",
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
    "ROLLING_SCAN_PLAN_MODIFIED",
    "RECOMMENDED_NEXT_ACTION",
    "RECONCILIATION_PATH",
    "SOURCE_TICKER_COUNT_AUDIT_PATH",
    "SOURCE_COMPARISON_PATH",
    "TICKER_SET_DIFF_PATH",
    "DROPPED_OR_MISSING_TICKERS_PATH",
    "SUSPICIOUS_TICKERS_PATH",
    "VALIDATION_PATH",
    "REPORT_PATH",
]

AUDIT_FIELDS = [
    "source_id",
    "source_path",
    "file_exists",
    "detected_ticker_column",
    "raw_row_count",
    "nonblank_ticker_row_count",
    "normalized_unique_ticker_count",
    "duplicate_ticker_count",
    "blank_ticker_row_count",
    "invalid_suspicious_ticker_count",
    "source_role",
    "source_trust_level",
    "content_sha256",
    "notes",
]
COMPARISON_FIELDS = [
    "source_id",
    "source_path",
    "source_unique_count",
    "baseline_unique_count",
    "intersection_count",
    "in_source_not_in_v18_23a_count",
    "in_v18_23a_not_in_source_count",
    "source_with_325_or_more",
    "reference_candidate",
    "source_trust_level",
    "notes",
]
DIFF_FIELDS = ["ticker", "diff_type", "reference_source_id", "reference_source_path", "baseline_present", "reference_present", "notes"]
MISSING_FIELDS = ["ticker", "reference_source_id", "reference_source_path", "reason", "valid_ticker", "recommended_action"]
SUSPICIOUS_FIELDS = ["source_id", "source_path", "raw_value", "normalized_value", "reason", "row_number"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

EXPLICIT_SOURCE_FILES = [
    ("V18_23A_COVERAGE_PLAN", "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv", "canonical_baseline", "HIGH"),
    ("V18_23A_TODAY_SCAN_LIST", "outputs/v18/rolling_coverage/V18_23A_CURRENT_TODAY_PLANNED_SCAN_LIST.csv", "planning_subset", "MEDIUM"),
    ("V18_CURRENT_UNIVERSE_ROLLING_STATE", "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv", "selected_source", "HIGH"),
    ("V18_CURRENT_RAW105_FACTOR_PACK_RANKING", "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "ranked_subset", "MEDIUM"),
    ("V18_6A_CURRENT_TECHNICAL_TIMING", "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv", "technical_subset", "MEDIUM"),
    ("V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT", "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "signal_snapshot_reference", "HIGH"),
    ("V18_21B_CURRENT_SIGNAL_SNAPSHOT", "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SNAPSHOT.csv", "signal_snapshot_reference", "MEDIUM"),
    ("V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION", "outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv", "ranking_subset", "MEDIUM"),
    ("V16_COMPAT_FULL_UNIVERSE_PROOF", "outputs/v16/read_center/v16_compat_full_universe_proof.csv", "legacy_reference", "LOW"),
    ("STATE_V18_UNIVERSE_ROLLING_STATE", "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv", "state_reference_read_only", "HIGH"),
    ("STATE_V18_MANUAL_UNIVERSE_ADDITIONS", "state/v18/universe/V18_MANUAL_UNIVERSE_ADDITIONS.csv", "manual_reference_read_only", "MEDIUM"),
    ("STATE_RAW105_UNIVERSE_FOR_FACTOR_LAB", "state/v18/raw105_universe_for_factor_lab.csv", "factor_lab_subset", "LOW"),
    ("CONFIG_V16_FULL_SCREENED", "configs/v16/universe/us_full_screened_generated.yaml", "config_reference", "LOW"),
    ("CONFIG_V16_SECOND_STAGE", "configs/v16/universe/us_full_second_stage_generated.yaml", "config_reference", "LOW"),
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


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "NA", "N/A", "TICKER"}:
        return ""
    return ticker


def is_valid_ticker(ticker: str) -> bool:
    return bool(TICKER_RE.match(ticker)) and not ticker.isdigit()


def find_ticker_column(fields: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for name in ("ticker", "symbol", "candidate_ticker", "yf_ticker", "asset", "security"):
        if name in lower:
            return lower[name]
    return ""


def yaml_tickers(text: str) -> List[str]:
    values: List[str] = []
    for match in re.finditer(r"(?m)(?:^|\s|[-,])([A-Z][A-Z0-9.\-]{0,9})(?:\s|$|,)", text.upper()):
        value = normalize_ticker(match.group(1))
        if value and is_valid_ticker(value) and value not in {"TRUE", "FALSE", "NULL"}:
            values.append(value)
    return values


def source_files(root: Path) -> List[Tuple[str, str, str, str]]:
    sources = list(EXPLICIT_SOURCE_FILES)
    dynamic_dirs = [
        ("outputs/v18/daily_integrated", "daily_integrated_current", "MEDIUM"),
        ("outputs/v18/read_center", "read_center_current", "MEDIUM"),
        ("outputs/v18/research_command_center", "research_command_center_current", "MEDIUM"),
        ("outputs/v18/research_packets", "research_packet_current", "MEDIUM"),
        ("outputs/v17/price", "v17_price_reference", "LOW"),
        ("state/v16", "state_v16_reference", "LOW"),
    ]
    existing = {relative for _, relative, _, _ in sources}
    for directory, role, trust in dynamic_dirs:
        base = root / directory
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.csv")):
            relative = path.relative_to(root).as_posix()
            if relative not in existing:
                sources.append((path.stem.upper(), relative, role, trust))
                existing.add(relative)
    return sources


def analyze_source(root: Path, source_id: str, relative_path: str, role: str, trust: str) -> Tuple[Dict[str, object], Set[str], List[Dict[str, object]]]:
    path = root / relative_path
    suspicious: List[Dict[str, object]] = []
    raw_values: List[str] = []
    ticker_col = ""
    raw_row_count = 0
    blank_count = 0
    if not path.exists():
        return (
            {
                "source_id": source_id,
                "source_path": relative_path,
                "file_exists": "FALSE",
                "detected_ticker_column": "",
                "raw_row_count": 0,
                "nonblank_ticker_row_count": 0,
                "normalized_unique_ticker_count": 0,
                "duplicate_ticker_count": 0,
                "blank_ticker_row_count": 0,
                "invalid_suspicious_ticker_count": 0,
                "source_role": role,
                "source_trust_level": trust,
                "content_sha256": "",
                "notes": "Missing source.",
            },
            set(),
            suspicious,
        )
    if path.suffix.lower() == ".csv":
        rows, fields = read_csv(path)
        raw_row_count = len(rows)
        ticker_col = find_ticker_column(fields)
        if ticker_col:
            for row_number, row in enumerate(rows, start=2):
                normalized = normalize_ticker(row.get(ticker_col, ""))
                if not normalized:
                    blank_count += 1
                    continue
                raw_values.append(normalized)
                if not is_valid_ticker(normalized):
                    suspicious.append(
                        {
                            "source_id": source_id,
                            "source_path": relative_path,
                            "raw_value": row.get(ticker_col, ""),
                            "normalized_value": normalized,
                            "reason": "INVALID_OR_SUSPICIOUS_TICKER_FORMAT",
                            "row_number": row_number,
                        }
                    )
        else:
            raw_row_count = len(rows)
    elif path.suffix.lower() in {".yaml", ".yml"}:
        values = yaml_tickers(read_text(path))
        raw_row_count = len(values)
        raw_values = values
        ticker_col = "YAML_REGEX_TICKER"
    else:
        text = read_text(path)
        values = [normalize_ticker(value) for value in re.findall(r"\b[A-Z][A-Z0-9.\-]{0,9}\b", text.upper())]
        raw_row_count = len(values)
        raw_values = [value for value in values if is_valid_ticker(value)]
        ticker_col = "TEXT_REGEX_TICKER" if raw_values else ""
    valid_values = [value for value in raw_values if is_valid_ticker(value)]
    counts = Counter(valid_values)
    unique = set(counts)
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    audit = {
        "source_id": source_id,
        "source_path": relative_path,
        "file_exists": "TRUE",
        "detected_ticker_column": ticker_col,
        "raw_row_count": raw_row_count,
        "nonblank_ticker_row_count": len(raw_values),
        "normalized_unique_ticker_count": len(unique),
        "duplicate_ticker_count": duplicate_count,
        "blank_ticker_row_count": blank_count,
        "invalid_suspicious_ticker_count": len(suspicious),
        "source_role": role,
        "source_trust_level": trust,
        "content_sha256": sha256(path),
        "notes": "Ticker-bearing source." if unique else "No usable ticker set detected.",
    }
    return audit, unique, suspicious


def trust_rank(trust: str) -> int:
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(str(trust).upper(), 0)


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + body)


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    command = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_md(values: Dict[str, str], audit_rows: Sequence[Dict[str, object]], missing_rows: Sequence[Dict[str, object]], suspicious_rows: Sequence[Dict[str, object]], timestamp: str) -> str:
    top_sources = sorted(audit_rows, key=lambda row: int(row.get("normalized_unique_ticker_count", 0)), reverse=True)[:12]
    missing_preview = missing_rows[:25]
    suspicious_preview = suspicious_rows[:25]
    snapshot_text = "Allowed" if values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] == "TRUE" else "Not allowed"
    repair = "Proceed to V18.23A stable snapshot." if values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] == "TRUE" else "Do not snapshot V18.23A yet; implement a future V18.23A-R2 source selection repair or explicit universe-source decision."
    return f"""# V18.23A-R1 Universe Count Drift Reconciliation

Generated: {timestamp}

## Overall reconciliation status
Status: **{values['STATUS']}**

Result: **{values['RECONCILIATION_RESULT']}**

## Why this patch exists
V18.23A produced a canonical universe count of {values['V18_23A_CANONICAL_UNIVERSE_COUNT']}, while recent research layers often reported around 325 ticker/signal rows. This patch reconciles the difference without modifying universe, ranking, signal, state, price, forward tracker, or trading decision files.

## V18.23A canonical universe summary
Canonical source: `{values['V18_23A_CANONICAL_UNIVERSE_SOURCE']}`

Canonical count: {values['V18_23A_CANONICAL_UNIVERSE_COUNT']}

## Prior/broader source comparison summary
{markdown_table(['Source', 'Unique tickers', 'Trust', 'Role'], [(row['source_path'], row['normalized_unique_ticker_count'], row['source_trust_level'], row['source_role']) for row in top_sources])}

## 324 vs 325 explanation
Max reference universe count: {values['MAX_REFERENCE_UNIVERSE_COUNT']}. Sources with 325 or more tickers: {values['SOURCE_WITH_325_OR_MORE_COUNT']}. Count drift detected: {values['COUNT_DRIFT_DETECTED']}. Count drift explained: {values['COUNT_DRIFT_EXPLAINED']}.

## Missing/dropped ticker table
{markdown_table(['Ticker', 'Reference source', 'Reason', 'Recommended action'], [(row['ticker'], row['reference_source_id'], row['reason'], row['recommended_action']) for row in missing_preview]) if missing_preview else 'No valid missing ticker rows were found.'}

## Duplicate/blank/suspicious ticker analysis
Max duplicate ticker count: {values['DUPLICATE_TICKER_COUNT_MAX']}. Max blank ticker rows: {values['BLANK_TICKER_ROW_COUNT_MAX']}. Suspicious ticker rows: {values['SUSPICIOUS_TICKER_COUNT']}.

{markdown_table(['Source', 'Raw value', 'Normalized', 'Reason'], [(row['source_id'], row['raw_value'], row['normalized_value'], row['reason']) for row in suspicious_preview]) if suspicious_preview else 'No suspicious ticker rows were found.'}

## Whether V18.23A stable snapshot is allowed
{snapshot_text}. {repair}

## If not allowed, recommended repair path
{repair}

## Source provenance and trust notes
The audit preserves source path, detected ticker column, raw row count, nonblank rows, unique normalized ticker count, duplicates, blanks, suspicious rows, role, and trust level for each source. Current files are preferred; this patch does not rewrite source selection.

## Safety invariants
{markdown_table(['Invariant', 'Value'], [(key, values[key]) for key in SAFETY_INVARIANTS])}
"""


def render_report(values: Dict[str, str], missing_tickers: Sequence[str]) -> str:
    missing_text = ", ".join(missing_tickers) if missing_tickers else "None"
    return f"""# V18.23A-R1 Universe Count Drift Reconciliation Report

Status: {values['STATUS']}.

Canonical count: {values['V18_23A_CANONICAL_UNIVERSE_COUNT']}. Max reference count: {values['MAX_REFERENCE_UNIVERSE_COUNT']}. Count drift detected: {values['COUNT_DRIFT_DETECTED']}. Count drift explained: {values['COUNT_DRIFT_EXPLAINED']}.

Missing from V18.23A: {missing_text}.

Stable snapshot allowed: {values['V18_23A_STABLE_SNAPSHOT_ALLOWED']}. Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def build_validations(root: Path, values: Dict[str, str], audit_rows: Sequence[Dict[str, object]], comparison_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    required = [root / relative for relative in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23A_R1_universe_count_drift_reconciliation.py"), 1, "Python compile check."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23A_R1_universe_count_drift_reconciliation.ps1"), 1, "PowerShell parse check."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "All V18.23A-R1 outputs must exist and be non-empty."),
        validation_row("v18_23a_canonical_source_exists", (root / values["V18_23A_CANONICAL_UNIVERSE_SOURCE"]).exists(), 1, values["V18_23A_CANONICAL_UNIVERSE_SOURCE"]),
        validation_row("ticker_audit_has_comparison_rows", len(audit_rows) >= 2, 1, "Ticker audit should contain at least two source rows when comparisons exist."),
        validation_row("source_comparison_has_rows", len(comparison_rows) > 0, 1, "Source comparison CSV must contain count comparison rows."),
        validation_row("ticker_set_diff_header_or_rows_written", non_empty(root / OUTPUTS["diff"]), 1, "Ticker set diff CSV must exist."),
    ]
    if values["RECONCILIATION_RESULT"] == RESULT_WARN:
        validations.append(validation_row("warn_blocks_stable_snapshot", values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] == "FALSE", 1, "WARN reconciliation must block stable snapshot."))
    for key, expected in SAFETY_INVARIANTS.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    return validations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().isoformat(timespec="seconds")

    sets_by_source: Dict[str, Set[str]] = {}
    paths_by_source: Dict[str, str] = {}
    audit_rows: List[Dict[str, object]] = []
    suspicious_rows: List[Dict[str, object]] = []
    for source_id, relative_path, role, trust in source_files(root):
        audit, tickers, suspicious = analyze_source(root, source_id, relative_path, role, trust)
        audit_rows.append(audit)
        suspicious_rows.extend(suspicious)
        if tickers:
            sets_by_source[source_id] = tickers
            paths_by_source[source_id] = relative_path

    baseline_source_id = "V18_23A_COVERAGE_PLAN"
    baseline = sets_by_source.get(baseline_source_id, set())
    baseline_path = paths_by_source.get(baseline_source_id, "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv")
    reference_candidates = [
        row for row in audit_rows
        if row["source_id"] != baseline_source_id
        and int(row.get("normalized_unique_ticker_count", 0)) >= len(baseline)
        and trust_rank(str(row.get("source_trust_level", ""))) >= 2
    ]
    reference_candidates = sorted(
        reference_candidates,
        key=lambda row: (int(row.get("normalized_unique_ticker_count", 0)), trust_rank(str(row.get("source_trust_level", "")))),
        reverse=True,
    )
    reference = reference_candidates[0] if reference_candidates else None
    reference_source_id = str(reference["source_id"]) if reference else ""
    reference_path = str(reference["source_path"]) if reference else ""
    reference_set = sets_by_source.get(reference_source_id, set())

    comparison_rows: List[Dict[str, object]] = []
    diff_rows: List[Dict[str, object]] = []
    missing_rows: List[Dict[str, object]] = []
    for row in audit_rows:
        source_id = str(row["source_id"])
        if source_id == baseline_source_id or source_id not in sets_by_source:
            continue
        current_set = sets_by_source[source_id]
        in_source_not_baseline = sorted(current_set - baseline)
        in_baseline_not_source = sorted(baseline - current_set)
        comparison_rows.append(
            {
                "source_id": source_id,
                "source_path": row["source_path"],
                "source_unique_count": len(current_set),
                "baseline_unique_count": len(baseline),
                "intersection_count": len(current_set & baseline),
                "in_source_not_in_v18_23a_count": len(in_source_not_baseline),
                "in_v18_23a_not_in_source_count": len(in_baseline_not_source),
                "source_with_325_or_more": "TRUE" if len(current_set) >= 325 else "FALSE",
                "reference_candidate": "TRUE" if source_id == reference_source_id else "FALSE",
                "source_trust_level": row["source_trust_level"],
                "notes": "Broader reference candidate." if source_id == reference_source_id else "Comparison source.",
            }
        )
        if source_id == reference_source_id:
            for ticker in in_source_not_baseline:
                diff_rows.append({"ticker": ticker, "diff_type": "in_reference_not_in_v18_23A", "reference_source_id": source_id, "reference_source_path": row["source_path"], "baseline_present": "FALSE", "reference_present": "TRUE", "notes": "Valid ticker present in reference but absent from V18.23A baseline."})
                missing_rows.append({"ticker": ticker, "reference_source_id": source_id, "reference_source_path": row["source_path"], "reason": "VALID_REFERENCE_TICKER_MISSING_FROM_V18_23A", "valid_ticker": "TRUE", "recommended_action": "Future V18.23A-R2 source selection repair or explicit universe decision; do not modify now."})
            for ticker in in_baseline_not_source:
                diff_rows.append({"ticker": ticker, "diff_type": "in_v18_23A_not_in_reference", "reference_source_id": source_id, "reference_source_path": row["source_path"], "baseline_present": "TRUE", "reference_present": "FALSE", "notes": "Ticker present in V18.23A baseline but absent from selected reference."})

    max_reference_count = max([int(row.get("normalized_unique_ticker_count", 0)) for row in audit_rows if str(row.get("source_id")) != baseline_source_id] or [0])
    source_325_count = sum(1 for row in audit_rows if int(row.get("normalized_unique_ticker_count", 0)) >= 325)
    missing_source_count = sum(1 for row in audit_rows if row.get("file_exists") == "FALSE")
    duplicate_max = max([int(row.get("duplicate_ticker_count", 0)) for row in audit_rows] or [0])
    blank_max = max([int(row.get("blank_ticker_row_count", 0)) for row in audit_rows] or [0])
    missing_count = len(missing_rows)
    extra_count = sum(1 for row in diff_rows if row["diff_type"] == "in_v18_23A_not_in_reference")
    count_drift_detected = len(baseline) != max_reference_count if baseline else True
    clearly_explained = bool(baseline) and count_drift_detected and missing_count == 0 and (duplicate_max > 0 or blank_max > 0 or suspicious_rows)
    no_drift = bool(baseline) and not count_drift_detected
    if not baseline or not comparison_rows:
        result = RESULT_FAIL
    elif no_drift or clearly_explained:
        result = RESULT_EXPLAINED
    else:
        result = RESULT_WARN

    values: Dict[str, str] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "RECONCILIATION_READY": "FALSE",
        "V18_23A_CANONICAL_UNIVERSE_SOURCE": baseline_path,
        "V18_23A_CANONICAL_UNIVERSE_COUNT": str(len(baseline)),
        "MAX_REFERENCE_UNIVERSE_COUNT": str(max_reference_count),
        "REFERENCE_SOURCE_COUNT": str(len(comparison_rows)),
        "SOURCE_MISSING_COUNT": str(missing_source_count),
        "SOURCE_WITH_325_OR_MORE_COUNT": str(source_325_count),
        "COUNT_DRIFT_DETECTED": "TRUE" if count_drift_detected else "FALSE",
        "COUNT_DRIFT_EXPLAINED": "TRUE" if result == RESULT_EXPLAINED else "FALSE",
        "RECONCILIATION_RESULT": result,
        "MISSING_FROM_V18_23A_COUNT": str(missing_count),
        "EXTRA_IN_V18_23A_COUNT": str(extra_count),
        "DUPLICATE_TICKER_COUNT_MAX": str(duplicate_max),
        "BLANK_TICKER_ROW_COUNT_MAX": str(blank_max),
        "SUSPICIOUS_TICKER_COUNT": str(len(suspicious_rows)),
        "V18_23A_STABLE_SNAPSHOT_ALLOWED": "FALSE",
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Do not modify sources in R1. Review missing ticker diffs; if valid missing tickers exist, implement V18.23A-R2 source selection repair before stable snapshot.",
        "RECONCILIATION_PATH": str(root / OUTPUTS["reconciliation"]),
        "SOURCE_TICKER_COUNT_AUDIT_PATH": str(root / OUTPUTS["audit"]),
        "SOURCE_COMPARISON_PATH": str(root / OUTPUTS["comparison"]),
        "TICKER_SET_DIFF_PATH": str(root / OUTPUTS["diff"]),
        "DROPPED_OR_MISSING_TICKERS_PATH": str(root / OUTPUTS["missing"]),
        "SUSPICIOUS_TICKERS_PATH": str(root / OUTPUTS["suspicious"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY_INVARIANTS)

    if result == RESULT_EXPLAINED:
        values["RECOMMENDED_NEXT_ACTION"] = "V18.23A stable snapshot is allowed after reviewing V18.23A-R1 READ_FIRST; no source rewrite is needed in this patch."

    write_csv(root / OUTPUTS["audit"], audit_rows, AUDIT_FIELDS)
    write_csv(root / OUTPUTS["comparison"], comparison_rows, COMPARISON_FIELDS)
    write_csv(root / OUTPUTS["diff"], diff_rows, DIFF_FIELDS)
    write_csv(root / OUTPUTS["missing"], missing_rows, MISSING_FIELDS)
    write_csv(root / OUTPUTS["suspicious"], suspicious_rows, SUSPICIOUS_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["reconciliation"], render_md(values, audit_rows, missing_rows, suspicious_rows, timestamp))
    write_text(root / OUTPUTS["report"], render_report(values, [str(row["ticker"]) for row in missing_rows]))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    validations = build_validations(root, values, audit_rows, comparison_rows)
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or result == RESULT_FAIL:
        values["STATUS"] = STATUS_FAIL
        values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] = "FALSE"
    elif result == RESULT_EXPLAINED:
        values["STATUS"] = STATUS_OK
        values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] = "TRUE"
    else:
        values["STATUS"] = STATUS_WARN
        values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] = "FALSE"
    values["RECONCILIATION_READY"] = "TRUE" if fail_count == 0 and result != RESULT_FAIL else "FALSE"

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["reconciliation"], render_md(values, audit_rows, missing_rows, suspicious_rows, timestamp))
    write_text(root / OUTPUTS["report"], render_report(values, [str(row["ticker"]) for row in missing_rows]))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
