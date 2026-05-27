from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_WARN = "WARN_V18_22D_DAILY_RESEARCH_OPERATOR_HOMEPAGE_READY"
STATUS_OK = "OK_V18_22D_DAILY_RESEARCH_OPERATOR_HOMEPAGE_READY"
STATUS_FAIL = "FAIL_V18_22D_DAILY_RESEARCH_OPERATOR_HOMEPAGE_VALIDATION_FAILED"
MODE = "READ_ONLY_DAILY_RESEARCH_OPERATOR_HOMEPAGE"

OUTPUTS = {
    "homepage": "outputs/v18/operator_homepage/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md",
    "gate_summary": "outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_GATE_SUMMARY.csv",
    "source_audit": "outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_22D_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE_REPORT.md",
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
}

PRIMARY_METRICS = {
    "STABLE_LAYER_COUNT": "stable layer count",
    "STABLE_LAYER_OK_COUNT": "stable layer OK count",
    "CURRENT_SCORE_READY_RATIO": "score-ready ratio",
    "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": "full-history factor-ready count",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT": "missing history ticker count",
    "FORWARD_TRACKER_SHADOW_ROW_COUNT": "forward tracker shadow rows",
    "FORWARD_RETURN_FILLED_COUNT": "forward return filled",
    "FORWARD_RETURN_PENDING_COUNT": "forward return pending",
    "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT": "high-confidence forward match count",
    "MULTI_HORIZON_READINESS_STATUS": "multi-horizon readiness",
    "SIGNAL_SNAPSHOT_ROW_COUNT": "signal snapshot rows",
    "SIGNAL_SNAPSHOT_HISTORY_COUNT": "signal snapshot history count",
    "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT": "event final advisory market coefficient",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "event risk coefficient applied to official decision",
    "BACKTEST_EXECUTION_READINESS_STATUS": "backtest execution readiness",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "OPERATOR_HOMEPAGE_READY",
    "SOURCE_CURRENT_AVAILABLE",
    "SOURCE_STABLE_AVAILABLE",
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
    "RECOMMENDED_NEXT_ACTION",
    "HOMEPAGE_PATH",
    "REPORT_PATH",
    "GATE_SUMMARY_PATH",
    "SOURCE_AUDIT_PATH",
    "VALIDATION_PATH",
]

GATE_FIELDS = ["gate_name", "allowed", "status", "why_blocked", "unlock_condition", "operator_instruction"]
SOURCE_FIELDS = [
    "source_id",
    "relative_path",
    "candidate_role",
    "exists",
    "selected",
    "modified_time",
    "parse_status",
    "notes",
]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

SOURCE_CANDIDATES = {
    "V18_22C_READ_FIRST": [
        "outputs/v18/ops/V18_22C_READ_FIRST.txt",
        "outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt",
    ],
    "V18_22C_REPORT": [
        "outputs/v18/ops/V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md",
        "outputs/v18/ops/V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    ],
    "V18_22C_EXECUTIVE_BRIEF": [
        "outputs/v18/research_packets/V18_22C_CURRENT_EXECUTIVE_RESEARCH_BRIEF.md",
    ],
    "V18_22C_DETAILED_PACKET": [
        "outputs/v18/research_packets/V18_22C_CURRENT_DETAILED_RESEARCH_PACKET.md",
    ],
    "V18_22C_BLOCKED_GATE_EXPLANATION": [
        "outputs/v18/research_packets/V18_22C_CURRENT_BLOCKED_GATE_EXPLANATION.md",
    ],
    "V18_22C_NEXT_ACTION_CHECKLIST": [
        "outputs/v18/research_packets/V18_22C_CURRENT_NEXT_ACTION_CHECKLIST.csv",
    ],
    "V18_22C_DO_NOT_DO_YET_CHECKLIST": [
        "outputs/v18/research_packets/V18_22C_CURRENT_DO_NOT_DO_YET_CHECKLIST.csv",
    ],
    "V18_22C_SOURCE_AUDIT": [
        "outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_SOURCE_AUDIT.csv",
    ],
    "V18_22C_VALIDATION": [
        "outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_VALIDATION.csv",
    ],
    "V18_22B_READ_FIRST": [
        "outputs/v18/ops/V18_22B_READ_FIRST.txt",
        "outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt",
    ],
    "V18_22B_GATE_SUMMARY": [
        "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv",
    ],
    "V18_22A_READ_FIRST": [
        "outputs/v18/ops/V18_22A_READ_FIRST.txt",
        "outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt",
    ],
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_kv_text(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


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


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def modified_time(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def to_int(value: object) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0


def truth(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def archive_candidates(root: Path, source_id: str) -> List[str]:
    if source_id != "V18_22C_READ_FIRST":
        return []
    archive = root / "archive/stable"
    if not archive.exists():
        return []
    matches = sorted(
        archive.glob("V18_22C_stable_research_packet_writer_*/outputs/v18/ops/V18_22C_READ_FIRST.txt"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    return [rel(path, root) for path in matches]


def parse_status_for(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() == ".csv":
        rows, fields = read_csv(path)
        return f"CSV_ROWS={len(rows)};FIELDS={len(fields)}"
    if path.suffix.lower() == ".json":
        try:
            json.loads(read_text(path))
            return "JSON_OK"
        except json.JSONDecodeError:
            return "JSON_PARSE_FAILED"
    values = read_kv_text(path)
    return f"TEXT_READ;KEYS={len(values)}"


def select_sources(root: Path) -> Tuple[Dict[str, Path], List[Dict[str, object]]]:
    selected: Dict[str, Path] = {}
    audit: List[Dict[str, object]] = []
    for source_id, base_candidates in SOURCE_CANDIDATES.items():
        candidates = list(base_candidates) + archive_candidates(root, source_id)
        selected_path = next((root / candidate for candidate in candidates if (root / candidate).exists()), None)
        for index, candidate in enumerate(candidates):
            path = root / candidate
            role = "current" if index == 0 else "fallback"
            is_selected = selected_path is not None and path.resolve() == selected_path.resolve()
            audit.append(
                {
                    "source_id": source_id,
                    "relative_path": candidate,
                    "candidate_role": role,
                    "exists": truth(path.exists()),
                    "selected": truth(is_selected),
                    "modified_time": modified_time(path),
                    "parse_status": parse_status_for(path),
                    "notes": "Selected first existing current/stable candidate." if is_selected else "Available fallback candidate." if path.exists() else "Missing source candidate.",
                }
            )
        if selected_path is not None:
            selected[source_id] = selected_path
    return selected, audit


def metric_value(metrics: Dict[str, str], key: str, default: str = "") -> str:
    return str(metrics.get(key, default)).strip()


def derive_gates(metrics: Dict[str, str]) -> Tuple[Dict[str, str], List[Dict[str, object]]]:
    filled = to_int(metric_value(metrics, "FORWARD_RETURN_FILLED_COUNT"))
    pending = to_int(metric_value(metrics, "FORWARD_RETURN_PENDING_COUNT"))
    high_conf = to_int(metric_value(metrics, "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT"))
    multi = metric_value(metrics, "MULTI_HORIZON_READINESS_STATUS", "UNKNOWN")
    readiness = metric_value(metrics, "BACKTEST_EXECUTION_READINESS_STATUS", "UNKNOWN")

    factor_allowed = filled > 0 and high_conf > 0 and multi != "NOT_READY_MULTI_HORIZON"
    backtest_allowed = pending == 0 and "BLOCKED" not in readiness.upper()
    weight_allowed = factor_allowed and "BLOCKED" not in readiness.upper()
    explicit_production_integration_present = metric_value(metrics, "EXPLICIT_PRODUCTION_INTEGRATION_PRESENT", "FALSE") == "TRUE"
    production_allowed = weight_allowed and explicit_production_integration_present
    staged_backfill_allowed = False
    daily_command_center_allowed = False

    gate_values = {
        "FACTOR_EFFECT_CLAIM_ALLOWED": truth(factor_allowed),
        "WEIGHT_CHANGE_ALLOWED": truth(weight_allowed),
        "PRODUCTION_PROMOTION_ALLOWED": truth(production_allowed),
        "BACKTEST_EXECUTION_ALLOWED": truth(backtest_allowed),
        "STAGED_BACKFILL_APPLY_ALLOWED": truth(staged_backfill_allowed),
        "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": truth(daily_command_center_allowed),
    }
    rows = [
        {
            "gate_name": "factor_effect_claim_allowed",
            "allowed": truth(factor_allowed),
            "status": "OPEN" if factor_allowed else "BLOCKED",
            "why_blocked": "" if factor_allowed else "Requires forward return filled count > 0, high-confidence forward match count > 0, and multi-horizon readiness not NOT_READY_MULTI_HORIZON.",
            "unlock_condition": "Filled forward returns, high-confidence matches, and multi-horizon readiness.",
            "operator_instruction": "Do not claim factor effectiveness today." if not factor_allowed else "Factor effect claim evidence gate is open.",
        },
        {
            "gate_name": "weight_change_allowed",
            "allowed": truth(weight_allowed),
            "status": "OPEN" if weight_allowed else "BLOCKED",
            "why_blocked": "" if weight_allowed else "Requires factor effect claim gate and non-blocked backtest execution readiness.",
            "unlock_condition": "Validated factor effect evidence plus unblocked backtest readiness.",
            "operator_instruction": "Do not change factor weights today." if not weight_allowed else "Weight-change evidence gate is open.",
        },
        {
            "gate_name": "production_promotion_allowed",
            "allowed": truth(production_allowed),
            "status": "OPEN" if production_allowed else "BLOCKED",
            "why_blocked": "" if production_allowed else "Requires weight-change gate plus explicit production integration that is present and safe.",
            "unlock_condition": "Weight-change allowed and explicit production integration approval/presence.",
            "operator_instruction": "Do not promote to production today." if not production_allowed else "Production promotion gate is open.",
        },
        {
            "gate_name": "backtest_execution_allowed",
            "allowed": truth(backtest_allowed),
            "status": "OPEN" if backtest_allowed else "BLOCKED",
            "why_blocked": "" if backtest_allowed else "Forward returns are pending or readiness contains BLOCKED.",
            "unlock_condition": "No pending forward returns and readiness not blocked.",
            "operator_instruction": "Do not execute backtests today." if not backtest_allowed else "Backtest gate is open.",
        },
        {
            "gate_name": "staged_backfill_apply_allowed",
            "allowed": truth(staged_backfill_allowed),
            "status": "REQUIRES_EXPLICIT_APPROVAL",
            "why_blocked": "Disabled by default for V18.22D; explicit approval required before staged fetch/import/apply.",
            "unlock_condition": "Explicit operator approval for staged backfill apply.",
            "operator_instruction": "Do not run staged backfill apply today without explicit approval.",
        },
        {
            "gate_name": "daily_command_center_integration_allowed",
            "allowed": truth(daily_command_center_allowed),
            "status": "BLOCKED",
            "why_blocked": "Disabled by default for this read-only operator homepage step.",
            "unlock_condition": "Separate approved integration step.",
            "operator_instruction": "Do not integrate V18.22D into the daily command center today.",
        },
    ]
    return gate_values, rows


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header, divider] + body)


def render_homepage(
    timestamp: str,
    values: Dict[str, str],
    gates: Sequence[Dict[str, object]],
    source_audit: Sequence[Dict[str, object]],
    missing_sources: Sequence[str],
    root: Path,
) -> str:
    output_paths = {key: rel(root / path, root) for key, path in OUTPUTS.items()}
    metric_rows = [(label, metric_value(values, key, "UNKNOWN")) for key, label in PRIMARY_METRICS.items()]
    blocked_rows = [
        (row["gate_name"], row["why_blocked"], row["unlock_condition"])
        for row in gates
        if row.get("allowed") != "TRUE"
    ]
    selected_sources = [row for row in source_audit if row.get("selected") == "TRUE"]
    source_rows = [
        (row["source_id"], row["relative_path"], row["candidate_role"], row["parse_status"])
        for row in selected_sources
    ]
    missing_text = ", ".join(missing_sources) if missing_sources else "None"
    return f"""# V18.22D Daily Research Operator Homepage

Generated: {timestamp}

## Overall operator status
Status: **{values['STATUS']}**

Mode: **{MODE}**

This homepage is read-only. It summarizes current V18 research readiness after V18.22C and does not change trading decisions, rankings, factor weights, price history, state, event calendars, simulations, forward trackers, broker/manual execution state, or existing stable snapshots.

## Read-first file list with exact relative paths
- {output_paths['read_first']}
- {output_paths['homepage']}
- {output_paths['gate_summary']}
- {output_paths['source_audit']}
- {output_paths['validation']}
- {output_paths['report']}

## Current system readiness summary
- Stable layers: {metric_value(values, 'STABLE_LAYER_OK_COUNT', 'UNKNOWN')}/{metric_value(values, 'STABLE_LAYER_COUNT', 'UNKNOWN')} OK
- Score-ready ratio: {metric_value(values, 'CURRENT_SCORE_READY_RATIO', 'UNKNOWN')}
- Full-history factor-ready count: {metric_value(values, 'CURRENT_FULL_HISTORY_FACTOR_READY_COUNT', 'UNKNOWN')}
- Missing history ticker count: {metric_value(values, 'CURRENT_MISSING_HISTORY_TICKER_COUNT', 'UNKNOWN')}
- Forward return filled: {metric_value(values, 'FORWARD_RETURN_FILLED_COUNT', 'UNKNOWN')}
- Forward return pending: {metric_value(values, 'FORWARD_RETURN_PENDING_COUNT', 'UNKNOWN')}
- High-confidence forward match count: {metric_value(values, 'HIGH_CONFIDENCE_FORWARD_MATCH_COUNT', 'UNKNOWN')}
- Multi-horizon readiness: {metric_value(values, 'MULTI_HORIZON_READINESS_STATUS', 'UNKNOWN')}
- Backtest execution readiness: {metric_value(values, 'BACKTEST_EXECUTION_READINESS_STATUS', 'UNKNOWN')}

## Key metrics table
{markdown_table(['Metric', 'Value'], metric_rows)}

## Research gates table
{markdown_table(['Gate', 'Allowed', 'Status', 'Operator instruction'], [(row['gate_name'], row['allowed'], row['status'], row['operator_instruction']) for row in gates])}

## Blocked reasons table
{markdown_table(['Blocked gate', 'Why blocked', 'Unlock condition'], blocked_rows)}

## What is allowed today
- Read the V18.22D READ_FIRST file and homepage.
- Review V18.22C research packets and current/stable source files listed in the source audit.
- Preserve the current research state and wait for approved future steps.
- Discuss or plan staged backfill, forward return filling, or integration work without running it.

## What is not allowed yet
- Do not claim factor effectiveness.
- Do not change factor weights.
- Do not promote to production.
- Do not run backtests.
- Do not apply staged backfill or fetch/import external data without explicit approval.
- Do not integrate this homepage into the daily command center in this step.
- Do not modify price cache, price history, rankings, signal snapshots, event calendars, simulation positions, forward trackers, price factors, technical timing, promotion/demotion files, manual state, or broker execution state.

## Recommended next action
{values['RECOMMENDED_NEXT_ACTION']}

## Source provenance and trust notes
Current source available: {values['SOURCE_CURRENT_AVAILABLE']}. Stable source available: {values['SOURCE_STABLE_AVAILABLE']}. Missing source candidate count: {values['SOURCE_MISSING_COUNT']}.

Missing source candidates: {missing_text}

{markdown_table(['Source', 'Selected path', 'Role', 'Parse status'], source_rows)}

## Safety invariants
{markdown_table(['Invariant', 'Value'], [(key, values[key]) for key in SAFETY_INVARIANTS])}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str], missing_sources: Sequence[str]) -> str:
    return f"""# V18.22D Daily Research Operator Homepage Report

## Summary
Status: {values['STATUS']}. V18.22D created a read-only operator homepage, gate summary, source audit, validation CSV, and READ_FIRST file.

## Gate Result
Factor effect claims: {values['FACTOR_EFFECT_CLAIM_ALLOWED']}. Weight changes: {values['WEIGHT_CHANGE_ALLOWED']}. Production promotion: {values['PRODUCTION_PROMOTION_ALLOWED']}. Staged backfill apply: {values['STAGED_BACKFILL_APPLY_ALLOWED']}. Daily command center integration: {values['DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED']}.

## Source Result
Current source available: {values['SOURCE_CURRENT_AVAILABLE']}. Stable source available: {values['SOURCE_STABLE_AVAILABLE']}. Missing source candidate count: {values['SOURCE_MISSING_COUNT']}.

Missing source candidates: {', '.join(missing_sources) if missing_sources else 'None'}.

## Safety Result
Official decision impact: {values['OFFICIAL_DECISION_IMPACT']}. External data fetched: {values['EXTERNAL_DATA_FETCHED']}. Backtest executed: {values['BACKTEST_EXECUTED']}. Backtest results applied: {values['BACKTEST_RESULTS_APPLIED']}.

## Validation Result
Validation fail count: {values['VALIDATION_FAIL_COUNT']}. Operator homepage ready: {values['OPERATOR_HOMEPAGE_READY']}.

## Recommended Next Step
{values['RECOMMENDED_NEXT_ACTION']}
"""


def build_values(root: Path, selected_sources: Dict[str, Path]) -> Dict[str, str]:
    current_path = root / "outputs/v18/ops/V18_22C_READ_FIRST.txt"
    stable_path = root / "outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt"
    metric_source = selected_sources.get("V18_22C_READ_FIRST")
    metrics = read_kv_text(metric_source) if metric_source else {}
    values = {key: metric_value(metrics, key, "UNKNOWN") for key in PRIMARY_METRICS}
    values.update(SAFETY_INVARIANTS)
    gate_values, _ = derive_gates(metrics)
    values.update(gate_values)
    values.update(
        {
            "STATUS": STATUS_WARN,
            "MODE": MODE,
            "OPERATOR_HOMEPAGE_READY": "FALSE",
            "SOURCE_CURRENT_AVAILABLE": truth(current_path.exists()),
            "SOURCE_STABLE_AVAILABLE": truth(stable_path.exists()),
            "SOURCE_MISSING_COUNT": "0",
            "VALIDATION_FAIL_COUNT": "0",
            "RECOMMENDED_NEXT_ACTION": "Read outputs/v18/ops/V18_22D_READ_FIRST.txt first; keep research gates blocked; do not run staged backfill, backtests, production promotion, or daily command center integration without a separate approved step.",
            "HOMEPAGE_PATH": str(root / OUTPUTS["homepage"]),
            "REPORT_PATH": str(root / OUTPUTS["report"]),
            "GATE_SUMMARY_PATH": str(root / OUTPUTS["gate_summary"]),
            "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source_audit"]),
            "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        }
    )
    return values


def build_validations(root: Path, values: Dict[str, str], source_audit: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    output_paths = [root / path for path in OUTPUTS.values()]
    validations = [
        validation_row("output_files_exist_and_non_empty", all(non_empty(path) for path in output_paths), 1, "All V18.22D output files must exist and be non-empty."),
        validation_row("validation_csv_has_rows", non_empty(root / OUTPUTS["validation"]), 1, "Validation CSV must contain PASS/FAIL rows."),
        validation_row("current_or_stable_source_available", values["SOURCE_CURRENT_AVAILABLE"] == "TRUE" or values["SOURCE_STABLE_AVAILABLE"] == "TRUE", 1, "At least one V18.22C current/stable source must be available."),
        validation_row("source_audit_reports_missing_sources", any(row.get("exists") == "FALSE" for row in source_audit) or values["SOURCE_MISSING_COUNT"] == "0", 1, "Missing source candidates are explicitly reported."),
    ]
    for key, expected in SAFETY_INVARIANTS.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    validations.extend(
        [
            validation_row("factor_effect_claim_gate_blocked", values["FACTOR_EFFECT_CLAIM_ALLOWED"] == "FALSE", 1, "Current metrics do not unlock factor effect claims."),
            validation_row("weight_change_gate_blocked", values["WEIGHT_CHANGE_ALLOWED"] == "FALSE", 1, "Weight changes remain blocked."),
            validation_row("production_promotion_gate_blocked", values["PRODUCTION_PROMOTION_ALLOWED"] == "FALSE", 1, "Production promotion remains blocked."),
            validation_row("staged_backfill_apply_gate_blocked", values["STAGED_BACKFILL_APPLY_ALLOWED"] == "FALSE", 1, "Explicit approval required."),
            validation_row("daily_command_center_integration_gate_blocked", values["DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED"] == "FALSE", 1, "Integration disabled by default for V18.22D."),
        ]
    )
    return validations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().isoformat(timespec="seconds")

    selected_sources, source_audit = select_sources(root)
    missing_sources = [str(row["relative_path"]) for row in source_audit if row.get("exists") == "FALSE"]
    values = build_values(root, selected_sources)
    values["SOURCE_MISSING_COUNT"] = str(len(missing_sources))
    selected_metric_path = selected_sources.get("V18_22C_READ_FIRST")
    metric_values = read_kv_text(selected_metric_path) if selected_metric_path else {}
    _, gate_rows = derive_gates(metric_values)

    write_csv(root / OUTPUTS["gate_summary"], gate_rows, GATE_FIELDS)
    write_csv(root / OUTPUTS["source_audit"], source_audit, SOURCE_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation file initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["homepage"], render_homepage(timestamp, values, gate_rows, source_audit, missing_sources, root))
    write_text(root / OUTPUTS["report"], render_report(values, missing_sources))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    validations = build_validations(root, values, source_audit)
    fail_count = sum(int(row["fail_count"]) for row in validations)
    all_gates_open = all(values[key] == "TRUE" for key in ["FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED"])
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    values["OPERATOR_HOMEPAGE_READY"] = truth(fail_count == 0 and all(non_empty(root / path) for path in OUTPUTS.values()))
    values["STATUS"] = STATUS_FAIL if fail_count else STATUS_OK if all_gates_open else STATUS_WARN

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["homepage"], render_homepage(timestamp, values, gate_rows, source_audit, missing_sources, root))
    write_text(root / OUTPUTS["report"], render_report(values, missing_sources))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
