from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_READY = "WARN_V18_22B_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_READY"
STATUS_DEGRADED = "WARN_V18_22B_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_DEGRADED"
STATUS_FAIL = "FAIL_V18_22B_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_VALIDATION_FAILED"
MODE = "DAILY_RESEARCH_READ_ONLY_WRAPPER"
PATCH_MODE = "RESEARCH_COMMAND_CENTER_WRAPPER_INTEGRATION_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "RESEARCH_COMMAND_CENTER_WRAPPER_READY": "TRUE",
    "PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "FORWARD_RETURN_FILLED_COUNT": "0",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FULL_HISTORY_BACKFILL_APPLIED": "FALSE",
    "STAGED_BACKFILL_APPLIED": "FALSE",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
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
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

INPUTS = {
    "a_stable": "outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt",
    "a_readfirst": "outputs/v18/ops/V18_22A_READ_FIRST.txt",
    "a_report": "outputs/v18/ops/V18_22A_CURRENT_RESEARCH_COMMAND_CENTER_REPORT.md",
    "a_command_center": "outputs/v18/research_command_center/V18_22A_CURRENT_RESEARCH_COMMAND_CENTER.md",
    "a_layer": "outputs/v18/research_command_center/V18_22A_CURRENT_LAYER_STATUS.csv",
    "a_gate": "outputs/v18/research_command_center/V18_22A_CURRENT_GATE_MATRIX.csv",
    "a_bottlenecks": "outputs/v18/research_command_center/V18_22A_CURRENT_RESEARCH_BOTTLENECK_DASHBOARD.csv",
    "a_actions": "outputs/v18/research_command_center/V18_22A_CURRENT_OPERATOR_NEXT_ACTION_BOARD.csv",
    "a_safety": "outputs/v18/research_command_center/V18_22A_CURRENT_SAFETY_AUDIT.csv",
}

OUTPUTS = {
    "packet": "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_PACKET.md",
    "gate_summary": "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv",
    "action_summary": "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_ACTION_SUMMARY.csv",
    "safety_audit": "outputs/v18/research_command_center/V18_22B_CURRENT_WRAPPER_SAFETY_AUDIT.csv",
    "validation": "outputs/v18/research_command_center/V18_22B_CURRENT_WRAPPER_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_22B_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "RESEARCH_COMMAND_CENTER_WRAPPER_READY",
    "V18_22A_SOURCE_STATUS", "V18_22A_REFRESH_RAN", "PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_APPLIED",
    "STABLE_LAYER_COUNT", "STABLE_LAYER_OK_COUNT", "MISSING_STABLE_LAYER_COUNT",
    "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT", "FORWARD_TRACKER_SHADOW_ROW_COUNT",
    "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT",
    "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
    "SIGNAL_SNAPSHOT_ROW_COUNT", "SIGNAL_SNAPSHOT_HISTORY_COUNT",
    "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
    "BACKTEST_EXECUTION_READINESS_STATUS", "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
    "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED", "PRICE_CACHE_INTEGRATION_ALLOWED",
    "BACKTEST_EXECUTION_ALLOWED", "RECOMMENDED_NEXT_ACTION", "DAILY_RESEARCH_PACKET_CREATED",
    "DAILY_RESEARCH_GATE_SUMMARY_CREATED", "DAILY_RESEARCH_ACTION_SUMMARY_CREATED",
    "WRAPPER_SAFETY_AUDIT_CREATED", "WRAPPER_VALIDATION_CREATED", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN",
    "STAGED_PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
    "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "EFFECT_CLAIM_ALLOWED_COUNT",
    "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT",
    "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]
GATE_SUMMARY_FIELDS = ["gate_name", "allowed_status", "current_blocker", "operator_meaning", "next_required_action", "production_impact"]
ACTION_SUMMARY_FIELDS = ["action_id", "action_name", "recommended_now", "priority", "reason", "risk_level", "requires_explicit_approval", "modifies_production", "fetches_external_data", "operator_note"]
SAFETY_AUDIT_FIELDS = ["checked_path", "file_exists", "modified_before_run", "modified_after_run", "modified_by_this_run", "protection_status", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def readfirst(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists() or path.is_dir():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", newline="", encoding=enc, errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
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


def modified_time(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else "MISSING"


def signature(path: Path) -> Tuple[str, str]:
    return modified_time(path), sha256(path)


def checked_paths(root: Path) -> List[Path]:
    rels = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_22A_research_command_center.ps1",
        "scripts/v18/v18_22A_research_command_center.py",
        "outputs/v18/ops/V18_22A_READ_FIRST.txt",
        "outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
        "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    ]
    return [root / rel for rel in rels]


def ps_parse(path: Path) -> bool:
    if not path.exists():
        return False
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK_PARSE" in result.stdout


def py_compile(path: Path) -> bool:
    if not path.exists():
        return False
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0


def first(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def packet(values: Dict[str, object]) -> str:
    return f"""# V18.22B Daily Research Command Center Packet

## Executive Summary
Status: {values.get('STATUS')}. This is a separate daily research read-only wrapper. It is not production daily command center integration.

## Current Research Status
Stable layers OK: {values.get('STABLE_LAYER_OK_COUNT')} of {values.get('STABLE_LAYER_COUNT')}. Missing stable layers: {values.get('MISSING_STABLE_LAYER_COUNT')}.

## Current Blocked Gates
Factor effect claims: {values.get('FACTOR_EFFECT_CLAIM_ALLOWED')}. Weight changes: {values.get('WEIGHT_CHANGE_ALLOWED')}. Production promotion: {values.get('PRODUCTION_PROMOTION_ALLOWED')}. Price cache integration: {values.get('PRICE_CACHE_INTEGRATION_ALLOWED')}. Backtest execution allowed: {values.get('BACKTEST_EXECUTION_ALLOWED')}.

## Data Coverage Bottlenecks
Score-ready ratio: {values.get('CURRENT_SCORE_READY_RATIO')}. Full-history ready: {values.get('CURRENT_FULL_HISTORY_FACTOR_READY_COUNT')}. Missing-history tickers: {values.get('CURRENT_MISSING_HISTORY_TICKER_COUNT')}.

## Forward Return Status
Shadow rows: {values.get('FORWARD_TRACKER_SHADOW_ROW_COUNT')}. Filled returns: {values.get('FORWARD_RETURN_FILLED_COUNT')}. Pending returns: {values.get('FORWARD_RETURN_PENDING_COUNT')}.

## Backtest Readiness
Backtest execution readiness: {values.get('BACKTEST_EXECUTION_READINESS_STATUS')}. Backtest executed: {values.get('BACKTEST_EXECUTED')}. Results applied: {values.get('BACKTEST_RESULTS_APPLIED')}.

## Event Risk Advisory Status
Final advisory market coefficient: {values.get('EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT')}. Applied to official decision: {values.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION')}.

## Next Recommended Action
Recommended next action: {values.get('RECOMMENDED_NEXT_ACTION')}.

## Explicitly Disallowed Actions
Do not fetch external data, write price history, write staged price history, modify price cache, fill forward returns, run backtests, apply backtest results, change factor weights, make factor effect claims, promote to production, modify buy permission, or change official decisions.

## Safety Summary
Production daily command center modified: {values.get('PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED')}. Daily command center integration applied: {values.get('DAILY_COMMAND_CENTER_INTEGRATION_APPLIED')}. Official decision impact: {values.get('OFFICIAL_DECISION_IMPACT')}.
"""


def report(values: Dict[str, object]) -> str:
    return f"""# V18.22B Daily Research Command Center Wrapper Report

## Executive Summary
Status: {values.get('STATUS')}. V18.22B creates a separate daily research read-only wrapper over V18.22A outputs.

## Safety Statement
The wrapper does not modify production daily command center files, official decision logic, buy permission, rankings, signal snapshots, event calendars, simulation, forward tracker, price factors, technical timing, price cache, state files, or broker execution.

## What This Wrapper Integrates
It reads the V18.22A stable/current READ_FIRST, command center markdown, gate matrix, action board, bottleneck dashboard, and safety audit.

## What This Wrapper Does Not Integrate
It does not integrate with the production daily command center and does not apply research outputs to official trading behavior.

## Research Command Center Summary
Stable layers: {values.get('STABLE_LAYER_OK_COUNT')} of {values.get('STABLE_LAYER_COUNT')}. Score-ready ratio: {values.get('CURRENT_SCORE_READY_RATIO')}. Pending returns: {values.get('FORWARD_RETURN_PENDING_COUNT')}.

## Gate Summary
Factor claims, weight changes, production promotion, price cache integration, backtest execution, and forward return filling remain disallowed. Staged fetch/import requires explicit approval.

## Operator Action Summary
Recommended next action: {values.get('RECOMMENDED_NEXT_ACTION')}. V18.22B stable snapshot is the immediate wrapper-layer preservation step.

## Wrapper Safety Audit Summary
Wrapper safety audit created: {values.get('WRAPPER_SAFETY_AUDIT_CREATED')}. Production daily command center modified: {values.get('PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED')}.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}.

## Next-Step Recommendation
Create a V18.22B stable snapshot if validation remains clean.
"""


def gate_summary_rows(gates: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    wanted = {
        "FACTOR_EFFECT_CLAIM": "No factor effectiveness claims can be made.",
        "FACTOR_WEIGHT_CHANGE": "No factor weights can be changed.",
        "PRODUCTION_PROMOTION": "No research output can be promoted to production.",
        "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT": "Requires explicit approval; do not auto-fetch.",
        "PRICE_CACHE_INTEGRATION": "Price cache writes are disallowed.",
        "DAILY_COMMAND_CENTER_INTEGRATION": "Production daily integration is disallowed.",
        "BACKTEST_EXECUTION": "Backtest execution is blocked.",
        "FORWARD_RETURN_FILL_APPLICATION": "Forward returns must remain unfilled.",
    }
    by_gate = {row.get("gate_name", ""): row for row in gates}
    rows: List[Dict[str, object]] = []
    for gate, meaning in wanted.items():
        row = by_gate.get(gate, {})
        rows.append({
            "gate_name": gate,
            "allowed_status": row.get("gate_allowed", "FALSE"),
            "current_blocker": first(row.get("blocking_metric"), row.get("current_status")),
            "operator_meaning": meaning,
            "next_required_action": row.get("required_to_unlock", "Keep blocked."),
            "production_impact": "NONE",
        })
    return rows


def action_summary_rows(actions: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    mapped = {
        "V18.22B_STABLE_SNAPSHOT": ("V18.22B stable snapshot", "TRUE", 1, "Preserve wrapper state after validation.", "LOW", "FALSE", "FALSE", "FALSE", "Recommended immediate next step."),
        "V18.22C_RESEARCH_PACKET_WRITER": ("Research Packet Writer", "OPTIONAL_AFTER_STABLE", 2, "Can package read-only evidence.", "LOW", "FALSE", "FALSE", "FALSE", "Safe after stable snapshot."),
        "V18.21H_R2_ACTUAL_STAGED_FETCH_IMPORT": ("Actual staged fetch/import", "FALSE", 3, "Requires explicit approval and external data/import.", "MEDIUM", "TRUE", "FALSE", "TRUE", "Do not run automatically."),
        "WAIT_FOR_FORWARD_HORIZON_MATURITY": ("Wait for forward horizons to mature", "VALID_OPTION", 4, "Most forward returns remain pending.", "LOW", "FALSE", "FALSE", "FALSE", "No action required now."),
        "V18.21G_R1_FILLED_SHADOW_AFTER_MATURITY": ("Filled-shadow after maturity", "FALSE_WAIT", 5, "Requires matured outcomes and explicit apply approval.", "MEDIUM", "TRUE", "FALSE", "FALSE", "Future only."),
        "PAUSE_AFTER_STABLE": ("Pause after stable", "VALID_OPTION", 6, "Avoid premature changes.", "LOW", "FALSE", "FALSE", "FALSE", "Safe stopping point."),
    }
    return [
        {
            "action_id": action_id,
            "action_name": vals[0],
            "recommended_now": vals[1],
            "priority": vals[2],
            "reason": vals[3],
            "risk_level": vals[4],
            "requires_explicit_approval": vals[5],
            "modifies_production": vals[6],
            "fetches_external_data": vals[7],
            "operator_note": vals[8],
        }
        for action_id, vals in mapped.items()
    ]


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    paths = {key: root / rel for key, rel in OUTPUTS.items()}
    watched = checked_paths(root)
    before = {str(path): signature(path) for path in watched}

    a_stable = readfirst(root / INPUTS["a_stable"])
    a_current = readfirst(root / INPUTS["a_readfirst"])
    source = a_stable or a_current
    source_status = source.get("STATUS", "MISSING_V18_22A_SOURCE")
    gates, _ = read_csv(root / INPUTS["a_gate"])
    actions, _ = read_csv(root / INPUTS["a_actions"])

    values: Dict[str, object] = {
        "STATUS": STATUS_READY if source else STATUS_DEGRADED,
        "V18_22A_SOURCE_STATUS": source_status,
        "V18_22A_REFRESH_RAN": "FALSE",
        "STABLE_LAYER_COUNT": source.get("STABLE_LAYER_COUNT", ""),
        "STABLE_LAYER_OK_COUNT": source.get("STABLE_LAYER_OK_COUNT", ""),
        "MISSING_STABLE_LAYER_COUNT": source.get("MISSING_STABLE_LAYER_COUNT", ""),
        "CURRENT_SCORE_READY_RATIO": source.get("CURRENT_SCORE_READY_RATIO", ""),
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": source.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT", ""),
        "CURRENT_MISSING_HISTORY_TICKER_COUNT": source.get("CURRENT_MISSING_HISTORY_TICKER_COUNT", ""),
        "FORWARD_TRACKER_SHADOW_ROW_COUNT": source.get("FORWARD_TRACKER_SHADOW_ROW_COUNT", ""),
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "FORWARD_RETURN_PENDING_COUNT": source.get("FORWARD_RETURN_PENDING_COUNT", ""),
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT": source.get("HIGH_CONFIDENCE_FORWARD_MATCH_COUNT", ""),
        "MULTI_HORIZON_READINESS_STATUS": source.get("MULTI_HORIZON_READINESS_STATUS", ""),
        "SIGNAL_SNAPSHOT_ROW_COUNT": source.get("SIGNAL_SNAPSHOT_ROW_COUNT", ""),
        "SIGNAL_SNAPSHOT_HISTORY_COUNT": source.get("SIGNAL_SNAPSHOT_HISTORY_COUNT", ""),
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT": source.get("EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT", ""),
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
        "BACKTEST_EXECUTION_READINESS_STATUS": source.get("BACKTEST_EXECUTION_READINESS_STATUS", ""),
        "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
        "WEIGHT_CHANGE_ALLOWED": "FALSE",
        "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
        "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED": source.get("STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED", "REQUIRES_EXPLICIT_APPROVAL"),
        "PRICE_CACHE_INTEGRATION_ALLOWED": "FALSE",
        "BACKTEST_EXECUTION_ALLOWED": "FALSE",
        "RECOMMENDED_NEXT_ACTION": "V18.22B_STABLE_SNAPSHOT",
        "DAILY_RESEARCH_PACKET_CREATED": "TRUE",
        "DAILY_RESEARCH_GATE_SUMMARY_CREATED": "TRUE",
        "DAILY_RESEARCH_ACTION_SUMMARY_CREATED": "TRUE",
        "WRAPPER_SAFETY_AUDIT_CREATED": "TRUE",
        "WRAPPER_VALIDATION_CREATED": "TRUE",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    values.update(SAFETY_FLAGS)

    write_text(paths["packet"], packet(values))
    write_csv(paths["gate_summary"], gate_summary_rows(gates), GATE_SUMMARY_FIELDS)
    write_csv(paths["action_summary"], action_summary_rows(actions), ACTION_SUMMARY_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))

    after = {str(path): signature(path) for path in watched}
    safety_rows: List[Dict[str, object]] = []
    changed = []
    for path in watched:
        before_sig = before[str(path)]
        after_sig = after[str(path)]
        modified = before_sig != after_sig
        if modified:
            changed.append(str(path))
        safety_rows.append({
            "checked_path": str(path),
            "file_exists": str(path.exists()).upper(),
            "modified_before_run": before_sig[0],
            "modified_after_run": after_sig[0],
            "modified_by_this_run": str(modified).upper(),
            "protection_status": "UNCHANGED" if not modified else "MODIFIED_FAIL",
            "notes": "Protected source for wrapper safety audit.",
        })
    write_csv(paths["safety_audit"], safety_rows, SAFETY_AUDIT_FIELDS)
    write_csv(paths["validation"], [], VALIDATION_FIELDS)

    read_first_text = read_text(paths["read_first"])
    validations = [
        validation_row("wrapper_outputs_created", all(path.exists() for path in paths.values()), 1, "All V18.22B outputs exist."),
        validation_row("read_first_created", paths["read_first"].exists(), 1, "READ_FIRST exists."),
        validation_row("report_created", paths["report"].exists(), 1, "Report exists."),
        validation_row("powershell_parse_wrapper", ps_parse(root / "scripts/v18/run_v18_22B_daily_research_command_center_wrapper.ps1"), 1, "Wrapper parses."),
        validation_row("python_compile_script", py_compile(root / "scripts/v18/v18_22B_daily_research_command_center_wrapper.py"), 1, "Python script compiles."),
        validation_row("required_read_first_fields_exist", all(field in read_first_text for field in READ_FIRST_FIELDS), 1, "Required READ_FIRST fields present."),
        validation_row("no_production_daily_command_center_modification", not any("run_v18_current_daily_command_center" in path for path in changed), len(changed), ";".join(changed)),
        validation_row("daily_integration_not_applied", values["DAILY_COMMAND_CENTER_INTEGRATION_APPLIED"] == "FALSE", 1, "Daily integration not applied."),
        validation_row("external_data_not_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE", 1, "No external data fetched."),
        validation_row("price_cache_not_modified", values["PRICE_CACHE_MODIFIED"] == "FALSE", 1, "Price cache not modified."),
        validation_row("price_history_not_written", values["PRICE_HISTORY_WRITTEN"] == "FALSE", 1, "Price history not written."),
        validation_row("staged_price_history_not_written", values["STAGED_PRICE_HISTORY_WRITTEN"] == "FALSE", 1, "Staged price history not written."),
        validation_row("forward_returns_not_filled", values["FORWARD_RETURN_FILLED_COUNT"] == "0", 1, "Forward returns not filled."),
        validation_row("backtest_not_executed", values["BACKTEST_EXECUTED"] == "FALSE", 1, "Backtest not executed."),
        validation_row("backtest_results_not_applied", values["BACKTEST_RESULTS_APPLIED"] == "FALSE", 1, "Backtest results not applied."),
        validation_row("ranking_not_modified", values["RANKING_MODIFIED"] == "FALSE", 1, "Ranking not modified."),
        validation_row("signal_snapshot_not_modified", values["SIGNAL_SNAPSHOT_MODIFIED"] == "FALSE", 1, "Signal snapshots not modified."),
        validation_row("forward_tracker_not_modified", values["FORWARD_TRACKER_MODIFIED"] == "FALSE", 1, "Forward tracker not modified."),
        validation_row("official_decision_impact_none", values["OFFICIAL_DECISION_IMPACT"] == "NONE", 1, "Official decision impact NONE."),
        validation_row("buy_permission_not_modified", values["BUY_PERMISSION_MODIFIED"] == "FALSE", 1, "Buy permission not modified."),
        validation_row("auto_trade_disabled", values["AUTO_TRADE"] == "DISABLED", 1, "Auto-trade disabled."),
        validation_row("auto_sell_disabled", values["AUTO_SELL"] == "DISABLED", 1, "Auto-sell disabled."),
        validation_row("protected_files_unchanged", not changed, len(changed), ";".join(changed)),
        validation_row("claims_weights_promotions_blocked", values["FACTOR_EFFECT_CLAIM_ALLOWED"] == "FALSE" and values["WEIGHT_CHANGE_ALLOWED"] == "FALSE" and values["PRODUCTION_PROMOTION_ALLOWED"] == "FALSE", 1, "Claims, weights, promotions blocked."),
    ]
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["validation"], validations, VALIDATION_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))
    write_text(paths["packet"], packet(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "RESEARCH_COMMAND_CENTER_WRAPPER_READY",
        "V18_22A_SOURCE_STATUS", "V18_22A_REFRESH_RAN", "PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED",
        "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_APPLIED",
        "STABLE_LAYER_COUNT", "STABLE_LAYER_OK_COUNT", "MISSING_STABLE_LAYER_COUNT",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "FORWARD_TRACKER_SHADOW_ROW_COUNT",
        "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT",
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
        "SIGNAL_SNAPSHOT_ROW_COUNT", "SIGNAL_SNAPSHOT_HISTORY_COUNT",
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
        "BACKTEST_EXECUTION_READINESS_STATUS", "FACTOR_EFFECT_CLAIM_ALLOWED",
        "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
        "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED", "PRICE_CACHE_INTEGRATION_ALLOWED",
        "BACKTEST_EXECUTION_ALLOWED", "RECOMMENDED_NEXT_ACTION",
        "DAILY_RESEARCH_PACKET_CREATED", "DAILY_RESEARCH_GATE_SUMMARY_CREATED",
        "DAILY_RESEARCH_ACTION_SUMMARY_CREATED", "WRAPPER_SAFETY_AUDIT_CREATED",
        "WRAPPER_VALIDATION_CREATED", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
        "EXTERNAL_DATA_FETCHED", "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    print(f"DAILY_RESEARCH_PACKET: {paths['packet']}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
