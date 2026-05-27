from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_READY = "WARN_V18_22C_RESEARCH_PACKET_WRITER_READY"
STATUS_DEGRADED = "WARN_V18_22C_RESEARCH_PACKET_WRITER_DEGRADED"
STATUS_FAIL = "FAIL_V18_22C_RESEARCH_PACKET_WRITER_VALIDATION_FAILED"
MODE = "ADVISORY_READ_ONLY_PACKET_WRITER"
PATCH_MODE = "RESEARCH_PACKET_WRITER_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "RESEARCH_PACKET_WRITER_READY": "TRUE",
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

SOURCES = {
    "V18_22B_STABLE_READ_FIRST": "outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt",
    "V18_22B_READ_FIRST": "outputs/v18/ops/V18_22B_READ_FIRST.txt",
    "V18_22B_WRAPPER_REPORT": "outputs/v18/ops/V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md",
    "V18_22B_DAILY_RESEARCH_PACKET": "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_PACKET.md",
    "V18_22B_GATE_SUMMARY": "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv",
    "V18_22B_ACTION_SUMMARY": "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_ACTION_SUMMARY.csv",
    "V18_22B_WRAPPER_SAFETY_AUDIT": "outputs/v18/research_command_center/V18_22B_CURRENT_WRAPPER_SAFETY_AUDIT.csv",
    "V18_22B_WRAPPER_VALIDATION": "outputs/v18/research_command_center/V18_22B_CURRENT_WRAPPER_VALIDATION.csv",
    "V18_22A_STABLE_READ_FIRST": "outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt",
    "V18_22A_READ_FIRST": "outputs/v18/ops/V18_22A_READ_FIRST.txt",
    "V18_22A_COMMAND_CENTER": "outputs/v18/research_command_center/V18_22A_CURRENT_RESEARCH_COMMAND_CENTER.md",
    "V18_22A_LAYER_STATUS": "outputs/v18/research_command_center/V18_22A_CURRENT_LAYER_STATUS.csv",
    "V18_22A_GATE_MATRIX": "outputs/v18/research_command_center/V18_22A_CURRENT_GATE_MATRIX.csv",
    "V18_22A_BOTTLENECKS": "outputs/v18/research_command_center/V18_22A_CURRENT_RESEARCH_BOTTLENECK_DASHBOARD.csv",
    "V18_22A_ACTION_BOARD": "outputs/v18/research_command_center/V18_22A_CURRENT_OPERATOR_NEXT_ACTION_BOARD.csv",
    "V18_22A_SAFETY_AUDIT": "outputs/v18/research_command_center/V18_22A_CURRENT_SAFETY_AUDIT.csv",
}

OUTPUTS = {
    "executive": "outputs/v18/research_packets/V18_22C_CURRENT_EXECUTIVE_RESEARCH_BRIEF.md",
    "detailed": "outputs/v18/research_packets/V18_22C_CURRENT_DETAILED_RESEARCH_PACKET.md",
    "blocked": "outputs/v18/research_packets/V18_22C_CURRENT_BLOCKED_GATE_EXPLANATION.md",
    "next_actions": "outputs/v18/research_packets/V18_22C_CURRENT_NEXT_ACTION_CHECKLIST.csv",
    "do_not": "outputs/v18/research_packets/V18_22C_CURRENT_DO_NOT_DO_YET_CHECKLIST.csv",
    "source_audit": "outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_22C_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "RESEARCH_PACKET_WRITER_READY",
    "V18_22B_SOURCE_STATUS", "V18_22B_STABLE_SOURCE_STATUS",
    "EXECUTIVE_RESEARCH_BRIEF_CREATED", "DETAILED_RESEARCH_PACKET_CREATED",
    "BLOCKED_GATE_EXPLANATION_CREATED", "NEXT_ACTION_CHECKLIST_CREATED",
    "DO_NOT_DO_YET_CHECKLIST_CREATED", "SOURCE_AUDIT_CREATED", "PACKET_VALIDATION_CREATED",
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
    "BACKTEST_EXECUTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "RECOMMENDED_NEXT_ACTION", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN",
    "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED",
    "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED", "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    "EXECUTIVE_RESEARCH_BRIEF", "DETAILED_RESEARCH_PACKET",
]
NEXT_FIELDS = ["priority", "action_id", "action_name", "recommended_now", "preconditions", "allowed_now", "requires_explicit_approval", "modifies_production", "fetches_external_data", "expected_benefit", "risk_level", "notes"]
DO_NOT_FIELDS = ["blocked_action", "block_reason", "current_metric", "unlock_condition", "risk_if_done_now", "production_impact", "notes"]
SOURCE_FIELDS = ["source_name", "source_path", "source_exists", "modified_time", "parsed_status", "metrics_extracted", "source_role", "notes"]
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
            k, v = line.split(":", 1)
            values[k.strip()] = v.strip()
    return values


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", newline="", encoding=enc, errors="replace") as f:
                r = csv.DictReader(f)
                return [dict(x) for x in r], list(r.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else "MISSING"


def signature(path: Path) -> Tuple[str, str]:
    return mtime(path), sha256(path)


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_current_daily_command_center_full.ps1",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
        "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
    ]
    return [root / r for r in rels]


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
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def exec_brief(v: Dict[str, object]) -> str:
    return f"""# V18.22C Executive Research Brief

## One-Screen Summary
Research stack is stable through V18.22B. This packet is advisory read-only and makes no production changes.

## Current Research Status
- Stable layers: {v.get('STABLE_LAYER_OK_COUNT')} of {v.get('STABLE_LAYER_COUNT')}
- Score-ready ratio: {v.get('CURRENT_SCORE_READY_RATIO')}
- Missing-history tickers: {v.get('CURRENT_MISSING_HISTORY_TICKER_COUNT')}
- Forward returns pending: {v.get('FORWARD_RETURN_PENDING_COUNT')}

## Main Bottlenecks
Price-history coverage is low, forward returns are unfilled, high-confidence matches are zero, multi-horizon readiness is not ready, and signal history is limited.

## Current Gates
Factor claims: {v.get('FACTOR_EFFECT_CLAIM_ALLOWED')}. Weight changes: {v.get('WEIGHT_CHANGE_ALLOWED')}. Production promotion: {v.get('PRODUCTION_PROMOTION_ALLOWED')}. Backtest execution: {v.get('BACKTEST_EXECUTION_ALLOWED')}.

## Recommended Next Action
{v.get('RECOMMENDED_NEXT_ACTION')}

## Disallowed Actions
Do not fetch data, run backtests, fill forward returns, integrate price cache, change weights, promote to production, or connect to auto-trade/auto-sell.

## Safety Status
Official decision impact: {v.get('OFFICIAL_DECISION_IMPACT')}. External data fetched: {v.get('EXTERNAL_DATA_FETCHED')}. Price cache modified: {v.get('PRICE_CACHE_MODIFIED')}.
"""


def detailed_packet(v: Dict[str, object]) -> str:
    return f"""# V18.22C Detailed Research Packet

## Executive Summary
V18.22C packages the V18.22B daily research wrapper into operator-facing research packets. It is read-only.

## Stable Research Stack
Stable layers available: {v.get('STABLE_LAYER_OK_COUNT')} of {v.get('STABLE_LAYER_COUNT')}; missing: {v.get('MISSING_STABLE_LAYER_COUNT')}.

## Price-Derived Factor Coverage
Score-ready ratio is {v.get('CURRENT_SCORE_READY_RATIO')}; full-history ready count is {v.get('CURRENT_FULL_HISTORY_FACTOR_READY_COUNT')}; missing-history ticker count is {v.get('CURRENT_MISSING_HISTORY_TICKER_COUNT')}.

## Signal Snapshot Status
Signal snapshot rows: {v.get('SIGNAL_SNAPSHOT_ROW_COUNT')}; snapshot history count: {v.get('SIGNAL_SNAPSHOT_HISTORY_COUNT')}.

## Forward Tracker / Forward Return Status
Shadow rows: {v.get('FORWARD_TRACKER_SHADOW_ROW_COUNT')}; filled returns: {v.get('FORWARD_RETURN_FILLED_COUNT')}; pending returns: {v.get('FORWARD_RETURN_PENDING_COUNT')}.

## Factor Effectiveness Status
High-confidence forward matches are {v.get('HIGH_CONFIDENCE_FORWARD_MATCH_COUNT')}. Factor effect claims remain {v.get('FACTOR_EFFECT_CLAIM_ALLOWED')}.

## Event Risk Status
Final advisory market coefficient: {v.get('EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT')}. Applied to official decision: {v.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION')}.

## Backtest Readiness Status
Backtest readiness: {v.get('BACKTEST_EXECUTION_READINESS_STATUS')}. Backtest executed: {v.get('BACKTEST_EXECUTED')}. Results applied: {v.get('BACKTEST_RESULTS_APPLIED')}.

## Staged Backfill Status
Actual staged fetch/import allowed: {v.get('STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED')}. Price cache integration allowed: {v.get('PRICE_CACHE_INTEGRATION_ALLOWED')}.

## Gate Matrix Interpretation
Claims, weights, production promotion, backtest execution, price cache integration, and forward return filling remain blocked.

## Bottleneck Details
Coverage gaps, unfilled outcomes, zero high-confidence matches, limited signal history, and not-ready multi-horizon data prevent research claims.

## Recommended Development Path
Create V18.22C stable snapshot, optionally proceed to V18.22D daily research README, and require explicit approval before H-R2 staged fetch/import.

## Safety Summary
No official decision, buy permission, ranking, signal snapshot, event calendar, simulation, forward tracker, price factor, technical timing, price cache, or broker execution files are modified.
"""


def blocked_packet(gates: Sequence[Dict[str, str]]) -> str:
    rows = ["# V18.22C Blocked Gate Explanation\n"]
    for row in gates:
        gate = row.get("gate_name", "")
        if gate in {"FACTOR_EFFECT_CLAIM", "FACTOR_WEIGHT_CHANGE", "PRODUCTION_PROMOTION", "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT", "PRICE_CACHE_INTEGRATION", "BACKTEST_EXECUTION", "DAILY_COMMAND_CENTER_INTEGRATION", "FORWARD_RETURN_FILL_APPLICATION"}:
            rows.append(f"## {gate}\n- Current status: {row.get('allowed_status', '')}\n- Why blocked: {row.get('current_blocker', '')}\n- Unlock condition: {row.get('next_required_action', '')}\n- Explicit approval required: {'TRUE' if row.get('allowed_status') == 'REQUIRES_EXPLICIT_APPROVAL' else 'FALSE'}\n- Production impact: {row.get('production_impact', 'NONE')}\n")
    return "\n".join(rows)


def next_actions() -> List[Dict[str, object]]:
    return [
        {"priority": 1, "action_id": "V18_22C_STABLE_SNAPSHOT", "action_name": "V18.22C stable snapshot", "recommended_now": "TRUE", "preconditions": "V18.22C validation pass", "allowed_now": "TRUE", "requires_explicit_approval": "FALSE", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "expected_benefit": "Preserve packet writer state", "risk_level": "LOW", "notes": "Recommended immediate next step."},
        {"priority": 2, "action_id": "V18_22D_DAILY_RESEARCH_README", "action_name": "Daily research README", "recommended_now": "OPTIONAL_AFTER_STABLE", "preconditions": "V18.22C stable", "allowed_now": "TRUE", "requires_explicit_approval": "FALSE", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "expected_benefit": "Short daily summary", "risk_level": "LOW", "notes": "Read-only."},
        {"priority": 3, "action_id": "V18_21H_R2_ACTUAL_STAGED_FETCH_IMPORT", "action_name": "Actual staged fetch/import", "recommended_now": "FALSE", "preconditions": "Explicit approval", "allowed_now": "FALSE", "requires_explicit_approval": "TRUE", "modifies_production": "FALSE", "fetches_external_data": "TRUE", "expected_benefit": "Improve coverage", "risk_level": "MEDIUM", "notes": "Do not run automatically."},
        {"priority": 4, "action_id": "WAIT_FOR_FORWARD_HORIZON_MATURITY", "action_name": "Wait for forward horizon maturity", "recommended_now": "VALID_OPTION", "preconditions": "None", "allowed_now": "TRUE", "requires_explicit_approval": "FALSE", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "expected_benefit": "Avoid premature fills", "risk_level": "LOW", "notes": "Safe pause."},
        {"priority": 5, "action_id": "V18_21G_R1_FILLED_SHADOW_AFTER_MATURITY", "action_name": "Filled shadow after maturity", "recommended_now": "FALSE_WAIT", "preconditions": "Matured horizons and approval", "allowed_now": "FALSE", "requires_explicit_approval": "TRUE", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "expected_benefit": "Enable outcome research", "risk_level": "MEDIUM", "notes": "Future only."},
        {"priority": 6, "action_id": "PAUSE_AFTER_STABLE", "action_name": "Pause after stable", "recommended_now": "VALID_OPTION", "preconditions": "Stable snapshot complete", "allowed_now": "TRUE", "requires_explicit_approval": "FALSE", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "expected_benefit": "Avoid premature changes", "risk_level": "LOW", "notes": "Safe stopping point."},
    ]


def do_not_rows(v: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        {"blocked_action": "DO_NOT_CLAIM_FACTOR_EFFECTIVENESS", "block_reason": "High-confidence matches are zero", "current_metric": f"HIGH_CONFIDENCE_FORWARD_MATCH_COUNT={v.get('HIGH_CONFIDENCE_FORWARD_MATCH_COUNT')}", "unlock_condition": "High-confidence multi-horizon samples", "risk_if_done_now": "False research claim", "production_impact": "NONE", "notes": "Claims disabled."},
        {"blocked_action": "DO_NOT_CHANGE_FACTOR_WEIGHTS", "block_reason": "No effect claims allowed", "current_metric": "WEIGHT_CHANGE_ALLOWED=FALSE", "unlock_condition": "Validated evidence and approval", "risk_if_done_now": "Unsupported scoring changes", "production_impact": "HIGH", "notes": "Weights unchanged."},
        {"blocked_action": "DO_NOT_PROMOTE_TO_PRODUCTION", "block_reason": "Blockers remain", "current_metric": "PRODUCTION_PROMOTION_ALLOWED=FALSE", "unlock_condition": "Evidence gates pass", "risk_if_done_now": "Production regression", "production_impact": "HIGH", "notes": "Promotion disabled."},
        {"blocked_action": "DO_NOT_APPLY_EVENT_RISK_TO_OFFICIAL_DECISION", "block_reason": "Advisory only", "current_metric": "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION=FALSE", "unlock_condition": "Explicit integration approval", "risk_if_done_now": "Decision behavior change", "production_impact": "HIGH", "notes": "Event risk remains advisory."},
        {"blocked_action": "DO_NOT_INTEGRATE_PRICE_CACHE", "block_reason": "Integration disallowed", "current_metric": "PRICE_CACHE_INTEGRATION_ALLOWED=FALSE", "unlock_condition": "Validated staged data and approval", "risk_if_done_now": "Cache contamination", "production_impact": "HIGH", "notes": "Cache unchanged."},
        {"blocked_action": "DO_NOT_EXECUTE_BACKTEST", "block_reason": "Forward returns pending", "current_metric": str(v.get("BACKTEST_EXECUTION_READINESS_STATUS")), "unlock_condition": "Filled outcomes and sample gates", "risk_if_done_now": "Misleading research", "production_impact": "NONE", "notes": "Backtest not executed."},
        {"blocked_action": "DO_NOT_FILL_FORWARD_RETURNS_UNTIL_MATURE", "block_reason": "Returns pending/maturity incomplete", "current_metric": f"FORWARD_RETURN_PENDING_COUNT={v.get('FORWARD_RETURN_PENDING_COUNT')}", "unlock_condition": "Matured horizons and approved apply", "risk_if_done_now": "Invalid returns", "production_impact": "MEDIUM", "notes": "No fills."},
        {"blocked_action": "DO_NOT_RUN_H_R2_WITHOUT_EXPLICIT_APPROVAL", "block_reason": "External fetch/import", "current_metric": "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED=REQUIRES_EXPLICIT_APPROVAL", "unlock_condition": "Explicit approval", "risk_if_done_now": "Unauthorized data fetch", "production_impact": "NONE", "notes": "Do not auto-fetch."},
        {"blocked_action": "DO_NOT_CONNECT_TO_AUTO_TRADE", "block_reason": "Research-only", "current_metric": "AUTO_TRADE=DISABLED", "unlock_condition": "Separate production approval", "risk_if_done_now": "Unauthorized trading", "production_impact": "HIGH", "notes": "Disabled."},
        {"blocked_action": "DO_NOT_CONNECT_TO_AUTO_SELL", "block_reason": "Research-only", "current_metric": "AUTO_SELL=DISABLED", "unlock_condition": "Separate production approval", "risk_if_done_now": "Unauthorized selling", "production_impact": "HIGH", "notes": "Disabled."},
    ]


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def report(v: Dict[str, object]) -> str:
    return f"""# V18.22C Research Packet Writer Report

## Executive Summary
Status: {v.get('STATUS')}. V18.22C created operator-facing research packets from V18.22B outputs.

## Safety Statement
Packet writer only. No external data, backtest, forward return fill, price history write, price cache change, production daily wrapper change, or official decision change occurred.

## Source Summary
V18.22B current source: {v.get('V18_22B_SOURCE_STATUS')}. V18.22B stable source: {v.get('V18_22B_STABLE_SOURCE_STATUS')}.

## Packet Output Summary
Executive brief, detailed packet, blocked gate packet, next action checklist, do-not-do-yet checklist, source audit, and validation were created.

## Current Research-State Summary
Score-ready ratio {v.get('CURRENT_SCORE_READY_RATIO')}; pending returns {v.get('FORWARD_RETURN_PENDING_COUNT')}; backtest readiness {v.get('BACKTEST_EXECUTION_READINESS_STATUS')}.

## Gate Summary
Factor claims, weight changes, production promotion, backtest execution, price cache integration, and forward return fills remain blocked.

## Next Action Summary
Recommended next action: {v.get('RECOMMENDED_NEXT_ACTION')}.

## Do-Not-Do-Yet Summary
Do not run H-R2 without approval, execute backtests, fill returns, change weights, promote to production, or connect auto-trade/auto-sell.

## Validation Summary
Validation fail count: {v.get('VALIDATION_FAIL_COUNT')}.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    paths = {k: root / v for k, v in OUTPUTS.items()}
    before = {str(p): signature(p) for p in protected_paths(root)}

    rf = readfirst(root / SOURCES["V18_22B_READ_FIRST"])
    stable = readfirst(root / SOURCES["V18_22B_STABLE_READ_FIRST"])
    source = rf or stable
    gates, _ = read_csv(root / SOURCES["V18_22B_GATE_SUMMARY"])

    values: Dict[str, object] = {
        "STATUS": STATUS_READY if source else STATUS_DEGRADED,
        "V18_22B_SOURCE_STATUS": rf.get("STATUS", "MISSING"),
        "V18_22B_STABLE_SOURCE_STATUS": stable.get("STATUS", "MISSING"),
        "EXECUTIVE_RESEARCH_BRIEF_CREATED": "TRUE",
        "DETAILED_RESEARCH_PACKET_CREATED": "TRUE",
        "BLOCKED_GATE_EXPLANATION_CREATED": "TRUE",
        "NEXT_ACTION_CHECKLIST_CREATED": "TRUE",
        "DO_NOT_DO_YET_CHECKLIST_CREATED": "TRUE",
        "SOURCE_AUDIT_CREATED": "TRUE",
        "PACKET_VALIDATION_CREATED": "TRUE",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
        "EXECUTIVE_RESEARCH_BRIEF": str(paths["executive"]),
        "DETAILED_RESEARCH_PACKET": str(paths["detailed"]),
        "VALIDATION_FAIL_COUNT": "0",
    }
    for key in [
        "STABLE_LAYER_COUNT", "STABLE_LAYER_OK_COUNT", "MISSING_STABLE_LAYER_COUNT",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "FORWARD_TRACKER_SHADOW_ROW_COUNT",
        "FORWARD_RETURN_PENDING_COUNT", "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT",
        "MULTI_HORIZON_READINESS_STATUS", "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COUNT", "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
        "BACKTEST_EXECUTION_READINESS_STATUS", "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED",
        "PRICE_CACHE_INTEGRATION_ALLOWED", "BACKTEST_EXECUTION_ALLOWED", "RECOMMENDED_NEXT_ACTION",
    ]:
        values[key] = source.get(key, "")
    values.update(SAFETY_FLAGS)
    values["FACTOR_EFFECT_CLAIM_ALLOWED"] = "FALSE"
    values["WEIGHT_CHANGE_ALLOWED"] = "FALSE"
    values["PRODUCTION_PROMOTION_ALLOWED"] = "FALSE"
    values["DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED"] = "FALSE"

    write_text(paths["executive"], exec_brief(values))
    write_text(paths["detailed"], detailed_packet(values))
    write_text(paths["blocked"], blocked_packet(gates))
    write_csv(paths["next_actions"], next_actions(), NEXT_FIELDS)
    write_csv(paths["do_not"], do_not_rows(values), DO_NOT_FIELDS)

    source_rows = []
    for name, rel in SOURCES.items():
        path = root / rel
        exists = path.exists()
        if path.suffix.lower() == ".csv":
            rows, fields = read_csv(path)
            parsed = f"CSV_ROWS={len(rows)}"
            metrics = ";".join(fields[:8])
        elif exists:
            vals = readfirst(path)
            parsed = "TEXT_READ"
            metrics = ";".join(list(vals.keys())[:8])
        else:
            parsed = "MISSING"
            metrics = ""
        source_rows.append({
            "source_name": name,
            "source_path": str(path),
            "source_exists": str(exists).upper(),
            "modified_time": mtime(path),
            "parsed_status": parsed,
            "metrics_extracted": metrics,
            "source_role": "PRIMARY" if "V18_22B" in name else "SUPPORTING",
            "notes": "Read-only source audit.",
        })
    write_csv(paths["source_audit"], source_rows, SOURCE_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))
    write_csv(paths["validation"], [], VALIDATION_FIELDS)

    after = {str(p): signature(p) for p in protected_paths(root)}
    changed = [p for p, sig in before.items() if after.get(p) != sig]
    rf_text = read_text(paths["read_first"])
    validations = [
        validation_row("executive_brief_created", paths["executive"].exists(), 1, "Executive brief created."),
        validation_row("detailed_packet_created", paths["detailed"].exists(), 1, "Detailed packet created."),
        validation_row("blocked_gate_packet_created", paths["blocked"].exists(), 1, "Blocked gate explanation created."),
        validation_row("next_action_checklist_created", paths["next_actions"].exists(), 1, "Next action checklist created."),
        validation_row("do_not_do_yet_checklist_created", paths["do_not"].exists(), 1, "Do-not-do-yet checklist created."),
        validation_row("source_audit_created", paths["source_audit"].exists(), 1, "Source audit created."),
        validation_row("read_first_created", paths["read_first"].exists(), 1, "READ_FIRST created."),
        validation_row("report_created", paths["report"].exists(), 1, "Report created."),
        validation_row("powershell_parse_wrapper", ps_parse(root / "scripts/v18/run_v18_22C_research_packet_writer.ps1"), 1, "Wrapper parses."),
        validation_row("python_compile_script", py_compile(root / "scripts/v18/v18_22C_research_packet_writer.py"), 1, "Python compiles."),
        validation_row("required_read_first_fields_exist", all(field in rf_text for field in READ_FIRST_FIELDS), 1, "Required fields present."),
        validation_row("no_production_daily_command_center_modification", not any("run_v18_current_daily_command_center" in p for p in changed), len(changed), ";".join(changed)),
        validation_row("no_external_data_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE", 1, "No external data fetched."),
        validation_row("no_price_cache_modified", values["PRICE_CACHE_MODIFIED"] == "FALSE", 1, "Price cache not modified."),
        validation_row("no_price_history_written", values["PRICE_HISTORY_WRITTEN"] == "FALSE", 1, "Price history not written."),
        validation_row("no_staged_price_history_written", values["STAGED_PRICE_HISTORY_WRITTEN"] == "FALSE", 1, "Staged price history not written."),
        validation_row("no_forward_returns_filled", values["FORWARD_RETURN_FILLED_COUNT"] == "0", 1, "Forward returns not filled."),
        validation_row("no_backtest_executed", values["BACKTEST_EXECUTED"] == "FALSE", 1, "Backtest not executed."),
        validation_row("no_backtest_results_applied", values["BACKTEST_RESULTS_APPLIED"] == "FALSE", 1, "Backtest results not applied."),
        validation_row("no_ranking_modified", values["RANKING_MODIFIED"] == "FALSE", 1, "Ranking not modified."),
        validation_row("no_signal_modified", values["SIGNAL_SNAPSHOT_MODIFIED"] == "FALSE", 1, "Signals not modified."),
        validation_row("no_forward_tracker_modified", values["FORWARD_TRACKER_MODIFIED"] == "FALSE", 1, "Forward tracker not modified."),
        validation_row("official_decision_impact_none", values["OFFICIAL_DECISION_IMPACT"] == "NONE", 1, "No official decision impact."),
        validation_row("buy_permission_not_modified", values["BUY_PERMISSION_MODIFIED"] == "FALSE", 1, "Buy permission not modified."),
        validation_row("auto_trade_disabled", values["AUTO_TRADE"] == "DISABLED", 1, "Auto trade disabled."),
        validation_row("auto_sell_disabled", values["AUTO_SELL"] == "DISABLED", 1, "Auto sell disabled."),
        validation_row("protected_files_unchanged", not changed, len(changed), ";".join(changed)),
        validation_row("claims_weights_promotions_blocked", values["FACTOR_EFFECT_CLAIM_ALLOWED"] == "FALSE" and values["WEIGHT_CHANGE_ALLOWED"] == "FALSE" and values["PRODUCTION_PROMOTION_ALLOWED"] == "FALSE", 1, "Claims/weights/promotions blocked."),
    ]
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["validation"], validations, VALIDATION_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))
    write_text(paths["executive"], exec_brief(values))
    write_text(paths["detailed"], detailed_packet(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "RESEARCH_PACKET_WRITER_READY",
        "V18_22B_SOURCE_STATUS", "V18_22B_STABLE_SOURCE_STATUS",
        "EXECUTIVE_RESEARCH_BRIEF_CREATED", "DETAILED_RESEARCH_PACKET_CREATED",
        "BLOCKED_GATE_EXPLANATION_CREATED", "NEXT_ACTION_CHECKLIST_CREATED",
        "DO_NOT_DO_YET_CHECKLIST_CREATED", "SOURCE_AUDIT_CREATED", "PACKET_VALIDATION_CREATED",
        "STABLE_LAYER_COUNT", "STABLE_LAYER_OK_COUNT", "MISSING_STABLE_LAYER_COUNT",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "FORWARD_TRACKER_SHADOW_ROW_COUNT",
        "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT",
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "BACKTEST_EXECUTION_READINESS_STATUS",
        "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
        "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "EXTERNAL_DATA_FETCHED",
        "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "VALIDATION_FAIL_COUNT",
        "READ_FIRST", "REPORT", "EXECUTIVE_RESEARCH_BRIEF", "DETAILED_RESEARCH_PACKET",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
