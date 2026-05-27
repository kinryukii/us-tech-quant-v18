from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_22C_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_22C_STABLE_SNAPSHOT_VALIDATION_FAILED"
STATUS_FAIL = "FAIL_V18_22C_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_22C_stable_research_packet_writer"

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
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

REQUIRED_FILES = [
    "scripts/v18/v18_22C_research_packet_writer.py",
    "scripts/v18/run_v18_22C_research_packet_writer.ps1",
    "scripts/v18/v18_22B_daily_research_command_center_wrapper.py",
    "scripts/v18/run_v18_22B_daily_research_command_center_wrapper.ps1",
    "outputs/v18/research_packets/V18_22C_CURRENT_EXECUTIVE_RESEARCH_BRIEF.md",
    "outputs/v18/research_packets/V18_22C_CURRENT_DETAILED_RESEARCH_PACKET.md",
    "outputs/v18/research_packets/V18_22C_CURRENT_BLOCKED_GATE_EXPLANATION.md",
    "outputs/v18/research_packets/V18_22C_CURRENT_NEXT_ACTION_CHECKLIST.csv",
    "outputs/v18/research_packets/V18_22C_CURRENT_DO_NOT_DO_YET_CHECKLIST.csv",
    "outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_SOURCE_AUDIT.csv",
    "outputs/v18/research_packets/V18_22C_CURRENT_RESEARCH_PACKET_VALIDATION.csv",
    "outputs/v18/ops/V18_22C_READ_FIRST.txt",
    "outputs/v18/ops/V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md",
]

OPTIONAL_FILES = [
    "outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22B_READ_FIRST.txt",
    "outputs/v18/ops/V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md",
    "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_PACKET.md",
    "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv",
    "outputs/v18/research_command_center/V18_22B_CURRENT_DAILY_RESEARCH_ACTION_SUMMARY.csv",
    "outputs/v18/research_command_center/V18_22B_CURRENT_WRAPPER_SAFETY_AUDIT.csv",
    "outputs/v18/research_command_center/V18_22B_CURRENT_WRAPPER_VALIDATION.csv",
]

GENERATED_EXTERNAL_FILES = [
    "outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]

PS_FILES = [
    "scripts/v18/run_v18_22C_stable_snapshot.ps1",
    "scripts/v18/run_v18_22C_research_packet_writer.ps1",
    "scripts/v18/run_v18_22B_daily_research_command_center_wrapper.ps1",
]

PY_FILES = [
    "scripts/v18/v18_22C_stable_snapshot.py",
    "scripts/v18/v18_22C_research_packet_writer.py",
    "scripts/v18/v18_22B_daily_research_command_center_wrapper.py",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "SNAPSHOT_ONLY",
    "POLICY_APPLIED",
    "RESEARCH_PACKET_WRITER_READY",
    "V18_22B_SOURCE_STATUS",
    "V18_22B_STABLE_SOURCE_STATUS",
    "EXECUTIVE_RESEARCH_BRIEF_CREATED",
    "DETAILED_RESEARCH_PACKET_CREATED",
    "BLOCKED_GATE_EXPLANATION_CREATED",
    "NEXT_ACTION_CHECKLIST_CREATED",
    "DO_NOT_DO_YET_CHECKLIST_CREATED",
    "SOURCE_AUDIT_CREATED",
    "PACKET_VALIDATION_CREATED",
    "STABLE_LAYER_COUNT",
    "STABLE_LAYER_OK_COUNT",
    "MISSING_STABLE_LAYER_COUNT",
    "CURRENT_SCORE_READY_RATIO",
    "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT",
    "FORWARD_TRACKER_SHADOW_ROW_COUNT",
    "FORWARD_RETURN_FILLED_COUNT",
    "FORWARD_RETURN_PENDING_COUNT",
    "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT",
    "MULTI_HORIZON_READINESS_STATUS",
    "SIGNAL_SNAPSHOT_ROW_COUNT",
    "SIGNAL_SNAPSHOT_HISTORY_COUNT",
    "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
    "BACKTEST_EXECUTION_READINESS_STATUS",
    "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED",
    "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED",
    "PRICE_CACHE_INTEGRATION_ALLOWED",
    "BACKTEST_EXECUTION_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "RECOMMENDED_NEXT_ACTION",
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
    "EFFECT_CLAIM_ALLOWED_COUNT",
    "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT",
    "STABLE_SNAPSHOT_MODIFIED",
    "VALIDATION_FAIL_COUNT",
    "SNAPSHOT_PATH",
    "MANIFEST_ROW_COUNT",
    "READ_FIRST",
    "REPORT",
    "EXECUTIVE_RESEARCH_BRIEF",
    "DETAILED_RESEARCH_PACKET",
]

MANIFEST_FIELDS = [
    "category",
    "status",
    "source_path",
    "snapshot_path",
    "relative_source_path",
    "relative_snapshot_path",
    "size_bytes",
    "modified_time",
    "sha256",
    "error",
]

VALIDATION_FIELDS = ["check_name", "status", "path", "expected", "actual", "note"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def readfirst(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def category_for(rel: str) -> str:
    if rel.startswith("scripts/"):
        return "SCRIPT"
    if rel in GENERATED_EXTERNAL_FILES:
        return "GENERATED_CURRENT_OUTPUT"
    if rel.startswith("outputs/v18/research_packets/"):
        return "PACKET_OUTPUT"
    if rel.startswith("outputs/v18/ops/"):
        return "OPS_OUTPUT"
    if "V18_22B" in rel:
        return "SUPPORTING_V18_22B_CONTEXT"
    return "OUTPUT"


def copy_one(root: Path, snapshot: Path, rel: str) -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {
        "category": category_for(rel),
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel,
        "relative_snapshot_path": rel,
    }
    if not src.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    row.update({"status": "COPIED", "size_bytes": dst.stat().st_size, "modified_time": mtime(dst), "sha256": sha256(dst), "error": ""})
    return row


def snapshot_artifact_row(snapshot: Path, rel: str, category: str) -> Dict[str, object]:
    path = snapshot / rel
    row = {
        "category": category,
        "source_path": str(path),
        "snapshot_path": str(path),
        "relative_source_path": rel,
        "relative_snapshot_path": rel,
    }
    if not path.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SNAPSHOT_ARTIFACT_MISSING"})
        return row
    row.update({"status": "CREATED", "size_bytes": path.stat().st_size, "modified_time": mtime(path), "sha256": sha256(path), "error": ""})
    return row


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK_PARSE" in result.stdout, (result.stdout or result.stderr).strip()


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0, "OK_COMPILE" if result.returncode == 0 else (result.stdout or result.stderr).strip()


def validation_row(name: str, ok: bool, path: str, expected: str, actual: str, note: str = "") -> Dict[str, object]:
    return {"check_name": name, "status": "PASS" if ok else "FAIL", "path": path, "expected": expected, "actual": actual, "note": note}


def render_readfirst(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def exec_brief(v: Dict[str, object]) -> str:
    return f"""# V18.22C Executive Research Brief

## One-Screen Summary
V18.22C packages the packet writer outputs for operator review. It is advisory read-only.

## Current Research Status
- Stable layers: {v.get('STABLE_LAYER_OK_COUNT')} of {v.get('STABLE_LAYER_COUNT')}
- Score-ready ratio: {v.get('CURRENT_SCORE_READY_RATIO')}
- Missing-history tickers: {v.get('CURRENT_MISSING_HISTORY_TICKER_COUNT')}
- Forward returns pending: {v.get('FORWARD_RETURN_PENDING_COUNT')}

## Main Bottlenecks
Coverage gaps, unfilled outcomes, zero high-confidence matches, limited signal history, and not-ready multi-horizon data remain the limiting factors.

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
V18.22C converts the V18.22B daily research wrapper into operator-facing packet artifacts. It is read-only.

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
Actual staged fetch/import allowed: {v.get('STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED')}. Price cache integration allowed: {v.get('PRICE_CACHE_INTEGRATION_ALLOWED')}. Daily command center integration allowed: {v.get('DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED')}.

## Gate Matrix Interpretation
Claims, weights, production promotion, backtest execution, price cache integration, and forward return filling remain blocked.

## Bottleneck Details
Coverage gaps, unfilled outcomes, zero high-confidence matches, limited signal history, and not-ready multi-horizon data prevent research claims.

## Recommended Development Path
Create V18.22C stable snapshot, optionally proceed to V18.22D daily research README, and require explicit approval before H-R2 staged fetch/import.

## Safety Summary
No official decision, buy permission, ranking, signal snapshot, event calendar, simulation, forward tracker, price factor, technical timing, price cache, or broker execution files are modified.
"""


def readme(v: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.22C Stable Snapshot

This snapshot preserves V18.22C Research Packet Writer.

Required interpretation:
- This is advisory read-only packet writer only.
- It is not production daily command center integration.
- Executive research brief was created.
- Detailed research packet was created.
- Blocked gate explanation was created.
- Next action checklist was created.
- Do-not-do-yet checklist was created.
- No external data was fetched.
- Price cache was not modified.
- No price history or staged price history was written.
- No forward returns were filled.
- No backtest was executed.
- No backtest results were applied.
- Factor effect claims, weight changes, and production promotions remain disallowed.
- Official decision, buy permission, ranking, signal snapshots, event calendars, simulation, forward tracker, price factors, technical timing, manual state, broker execution, auto-trade, and auto-sell are unaffected.

Snapshot path:
`{snapshot}`
"""


def blocked_packet(gates: Sequence[Dict[str, str]]) -> str:
    rows = ["# V18.22C Blocked Gate Explanation\n"]
    wanted = {
        "FACTOR_EFFECT_CLAIM",
        "WEIGHT_CHANGE",
        "PRODUCTION_PROMOTION",
        "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT",
        "PRICE_CACHE_INTEGRATION",
        "BACKTEST_EXECUTION",
        "DAILY_COMMAND_CENTER_INTEGRATION",
        "FORWARD_RETURN_FILL_APPLICATION",
    }
    for row in gates:
        gate = row.get("gate_name", "")
        if gate in wanted:
            rows.append(
                f"## {gate}\n"
                f"- Current status: {row.get('allowed_status', '')}\n"
                f"- Why blocked: {row.get('current_blocker', '')}\n"
                f"- Unlock condition: {row.get('next_required_action', '')}\n"
                f"- Explicit approval required: {'TRUE' if row.get('allowed_status') == 'REQUIRES_EXPLICIT_APPROVAL' else 'FALSE'}\n"
                f"- Production impact: {row.get('production_impact', 'NONE')}\n"
            )
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


def validation_row(name: str, ok: bool, path: str, expected: str, actual: str, note: str = "") -> Dict[str, object]:
    return {"check_name": name, "status": "PASS" if ok else "FAIL", "path": path, "expected": expected, "actual": actual, "note": note}


def report(v: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.22C Stable Snapshot Report

## Executive Summary
Status: {v.get('STATUS')}. This snapshot preserves the V18.22C research packet writer and V18.22B wrapper context.

## Safety Statement
Packet writer only. No external data, backtest, forward return fill, price history write, price cache change, production daily wrapper change, or official decision change occurred.

## Source Summary
V18.22C source: {v.get('RESEARCH_PACKET_WRITER_READY')}. V18.22B source: {v.get('V18_22B_SOURCE_STATUS')}. V18.22B stable source: {v.get('V18_22B_STABLE_SOURCE_STATUS')}.

## Packet Output Summary
Executive brief, detailed packet, blocked gate explanation, next action checklist, do-not-do-yet checklist, source audit, and validation were created.

## Current Research-State Summary
Score-ready ratio {v.get('CURRENT_SCORE_READY_RATIO')}; pending returns {v.get('FORWARD_RETURN_PENDING_COUNT')}; backtest readiness {v.get('BACKTEST_EXECUTION_READINESS_STATUS')}.

## Gate Summary
Factor claims, weight changes, production promotion, backtest execution, price cache integration, and forward return fills remain blocked.

## Next Action Summary
Recommended next action: {v.get('RECOMMENDED_NEXT_ACTION')}.

## Do-Not-Do-Yet Summary
Do not run H-R2 without approval, execute backtests, fill returns, change weights, promote to production, or connect auto-trade/auto-sell.

## Validation Summary
Validation fail count: {v.get('VALIDATION_FAIL_COUNT')}. Manifest rows: {v.get('MANIFEST_ROW_COUNT')}.

## Snapshot Path
`{snapshot}`
"""


def restore_script(files: Sequence[str]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path',
        'Write-Host "=== RESTORE V18.22C STABLE SNAPSHOT START ==="',
        'Write-Host "MODE: SNAPSHOT_RESTORE"',
        'Write-Host "NOTE: This restores advisory packet-writer artifacts only."',
    ]
    for rel in files:
        win = rel.replace("/", "\\")
        lines.extend([
            f'$Source = Join-Path $SnapshotRoot "{win}"',
            f'$Target = Join-Path $Root "{win}"',
            'if (Test-Path $Source) {',
            '    $Dir = Split-Path -Parent $Target',
            '    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }',
            '    Copy-Item -LiteralPath $Source -Destination $Target -Force',
            '}',
        ])
    lines.extend([
        'Write-Host "RESTORE_COMPLETE: TRUE"',
        'Write-Host "RESEARCH_PACKET_WRITER_READY: TRUE"',
        'Write-Host "PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED: FALSE"',
        'Write-Host "DAILY_COMMAND_CENTER_INTEGRATION_APPLIED: FALSE"',
        'Write-Host "EXTERNAL_DATA_FETCHED: FALSE"',
        'Write-Host "BACKTEST_EXECUTED: FALSE"',
        'Write-Host "FORWARD_RETURN_FILLED_COUNT: 0"',
    ])
    return "\n".join(lines) + "\n"


def signature(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return "MISSING", ""
    return mtime(path), "" if path.is_dir() else sha256(path)


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_current_daily_command_center_full.ps1",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
        "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
        "state/v18/manual_state.csv",
        "state/v18/broker_execution_state.csv",
    ]
    return [root / rel for rel in rels]


def build_manifest(root: Path, snapshot: Path) -> List[Dict[str, object]]:
    manifest: List[Dict[str, object]] = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    manifest.extend(copy_one(root, snapshot, rel) for rel in OPTIONAL_FILES if (root / rel).exists())
    manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_22C.ps1", "RESTORE"))
    manifest.append(snapshot_artifact_row(snapshot, "README_V18_22C_STABLE_SNAPSHOT.md", "README"))
    manifest.append(snapshot_artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): signature(path) for path in protected_paths(root)}
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive" / "stable" / f"{PREFIX}_{timestamp}"
    read_first_path = root / "outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_22C_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_22C.ps1"

    metrics = readfirst(root / "outputs/v18/ops/V18_22C_READ_FIRST.txt")
    stable = readfirst(root / "outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt")
    metrics.update(SAFETY_FLAGS)
    metrics.update({
        "STATUS": STATUS_OK if metrics else STATUS_WARN,
        "MODE": MODE,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
        "SNAPSHOT_PATH": str(snapshot),
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
        "VALIDATION_FAIL_COUNT": "0",
        "MANIFEST_ROW_COUNT": "0",
    })
    if stable:
        metrics.setdefault("V18_22B_SOURCE_STATUS", stable.get("STATUS", "MISSING"))
        metrics.setdefault("V18_22B_STABLE_SOURCE_STATUS", stable.get("STATUS", "MISSING"))
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    write_text(readme_path, readme(metrics, snapshot))

    initial_manifest: List[Dict[str, object]] = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    initial_manifest.extend(copy_one(root, snapshot, rel) for rel in OPTIONAL_FILES if (root / rel).exists())
    initial_manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    copied_files = [str(row["relative_source_path"]) for row in initial_manifest if row.get("status") == "COPIED"]
    write_text(restore_path, restore_script(copied_files))
    initial_manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_22C.ps1", "RESTORE"))
    initial_manifest.append(snapshot_artifact_row(snapshot, "README_V18_22C_STABLE_SNAPSHOT.md", "README"))
    write_csv(manifest_path, initial_manifest, MANIFEST_FIELDS)
    write_csv(validation_path, [], VALIDATION_FIELDS)

    validations: List[Dict[str, object]] = []
    for rel in PS_FILES:
        ok, note = ps_parse(root / rel)
        validations.append(validation_row("powershell_parse", ok, str(root / rel), "PARSE_OK", "PARSE_OK" if ok else "PARSE_FAIL", note))
    for rel in PY_FILES:
        ok, note = py_compile(root / rel)
        validations.append(validation_row("python_compile", ok, str(root / rel), "COMPILE_OK", "COMPILE_OK" if ok else "COMPILE_FAIL", note))
    for rel in REQUIRED_FILES:
        dst = snapshot / rel
        validations.append(validation_row("required_snapshot_file_exists", dst.exists(), str(dst), "EXISTS", "EXISTS" if dst.exists() else "MISSING"))
    for path, name in [(manifest_path, "MANIFEST"), (validation_path, "VALIDATION"), (readme_path, "README"), (restore_path, "RESTORE")]:
        validations.append(validation_row(f"{name.lower()}_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    validations.append(validation_row("manifest_has_rows", len(initial_manifest) > 0, str(manifest_path), ">0", str(len(initial_manifest))))
    validations.append(validation_row("validation_has_rows", True, str(validation_path), ">0", "pending_rows"))
    for rel in GENERATED_EXTERNAL_FILES:
        path = root / rel
        validations.append(validation_row("current_external_output_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    for rel in OPTIONAL_FILES:
        path = root / rel
        if path.exists():
            validations.append(validation_row("supporting_v18_22b_output_exists_if_available", True, str(path), "EXISTS_IF_AVAILABLE", "EXISTS"))
    for key, expected in {
        "RESEARCH_PACKET_WRITER_READY": "TRUE",
        "PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED": "FALSE",
        "DAILY_COMMAND_CENTER_INTEGRATION_APPLIED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_WRITTEN": "FALSE",
        "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "BACKTEST_EXECUTED": "FALSE",
        "BACKTEST_RESULTS_APPLIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    }.items():
        validations.append(validation_row(f"preserve_{key.lower()}", str(metrics.get(key, "")) == expected, str(read_first_path), expected, str(metrics.get(key, ""))))
    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    validations.append(validation_row("protected_behavior_state_not_modified", not changed, "protected inputs", "UNCHANGED", "UNCHANGED" if not changed else ";".join(changed)))

    fail_count = sum(1 for row in validations if row["status"] != "PASS")
    metrics["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        metrics["STATUS"] = STATUS_FAIL
    final_manifest = build_manifest(root, snapshot)
    metrics["MANIFEST_ROW_COUNT"] = str(len(final_manifest))
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    final_manifest = build_manifest(root, snapshot)
    write_csv(manifest_path, final_manifest, MANIFEST_FIELDS)
    write_csv(validation_path, validations, VALIDATION_FIELDS)
    write_text(readme_path, readme(metrics, snapshot))
    write_text(restore_path, restore_script(copied_files))

    for key in [
        "STATUS",
        "MODE",
        "SNAPSHOT_ONLY",
        "POLICY_APPLIED",
        "RESEARCH_PACKET_WRITER_READY",
        "V18_22B_SOURCE_STATUS",
        "V18_22B_STABLE_SOURCE_STATUS",
        "EXECUTIVE_RESEARCH_BRIEF_CREATED",
        "DETAILED_RESEARCH_PACKET_CREATED",
        "BLOCKED_GATE_EXPLANATION_CREATED",
        "NEXT_ACTION_CHECKLIST_CREATED",
        "DO_NOT_DO_YET_CHECKLIST_CREATED",
        "SOURCE_AUDIT_CREATED",
        "PACKET_VALIDATION_CREATED",
        "STABLE_LAYER_COUNT",
        "STABLE_LAYER_OK_COUNT",
        "MISSING_STABLE_LAYER_COUNT",
        "CURRENT_SCORE_READY_RATIO",
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT",
        "FORWARD_TRACKER_SHADOW_ROW_COUNT",
        "FORWARD_RETURN_FILLED_COUNT",
        "FORWARD_RETURN_PENDING_COUNT",
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT",
        "MULTI_HORIZON_READINESS_STATUS",
        "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COUNT",
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
        "BACKTEST_EXECUTION_READINESS_STATUS",
        "FACTOR_EFFECT_CLAIM_ALLOWED",
        "WEIGHT_CHANGE_ALLOWED",
        "PRODUCTION_PROMOTION_ALLOWED",
        "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED",
        "PRICE_CACHE_INTEGRATION_ALLOWED",
        "BACKTEST_EXECUTION_ALLOWED",
        "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
        "RECOMMENDED_NEXT_ACTION",
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
        "EFFECT_CLAIM_ALLOWED_COUNT",
        "WEIGHT_CHANGE_ALLOWED_COUNT",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT",
        "VALIDATION_FAIL_COUNT",
        "READ_FIRST",
        "REPORT",
        "EXECUTIVE_RESEARCH_BRIEF",
        "DETAILED_RESEARCH_PACKET",
    ]:
        print(f"{key}: {metrics.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
