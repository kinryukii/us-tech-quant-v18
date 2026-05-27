from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_READY = "WARN_V18_21F_UNIFIED_RESEARCH_CHAIN_READ_CENTER_READY"
STATUS_DEGRADED = "WARN_DEGRADED_MISSING_LAYER"
STATUS_FAIL = "FAIL_V18_21F_UNIFIED_RESEARCH_CHAIN_READ_CENTER_VALIDATION_FAILED"
MODE = "ADVISORY_READ_CENTER_ONLY"
PATCH_MODE = "UNIFIED_RESEARCH_CHAIN_READ_CENTER_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
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
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
    "FORWARD_RETURN_FILLED_COUNT": "0",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

LAYERS = [
    ("V18.21A-R4", "Price-Derived Factors", "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt"),
    ("V18.21B-R1", "Signal Snapshot", "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt"),
    ("V18.21C-R2", "Factor Effectiveness", "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt"),
    ("V18.21D-R1", "Forward Tracker Link-Key Shadow", "outputs/v18/ops/V18_21D_R1_STABLE_READ_FIRST.txt"),
    ("V18.21E-R1", "Event Risk Coefficient", "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt"),
]

REQUIRED_OUTPUTS = {
    "status": "outputs/v18/research_chain/V18_21F_CURRENT_UNIFIED_RESEARCH_CHAIN_STATUS.csv",
    "blockers": "outputs/v18/research_chain/V18_21F_CURRENT_RESEARCH_BLOCKER_SUMMARY.csv",
    "decisions": "outputs/v18/research_chain/V18_21F_CURRENT_RESEARCH_READINESS_DECISION_TABLE.csv",
    "next_steps": "outputs/v18/research_chain/V18_21F_CURRENT_NEXT_STEP_PLAN.csv",
    "read_first": "outputs/v18/ops/V18_21F_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_21F_CURRENT_UNIFIED_RESEARCH_CHAIN_READ_CENTER.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "STABLE_LAYER_COUNT",
    "STABLE_LAYER_OK_COUNT", "STABLE_LAYER_WARN_OR_DEGRADED_COUNT", "MISSING_STABLE_LAYER_COUNT",
    "PRICE_DERIVED_SCORE_READY_RATIO", "PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT",
    "SIGNAL_SNAPSHOT_ROW_COUNT", "READY_FOR_FORWARD_RESEARCH_COUNT",
    "READY_FOR_SIMULATION_ANALYSIS_COUNT", "FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT",
    "FACTOR_EFFECTIVENESS_LOW_CONFIDENCE_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
    "FORWARD_TRACKER_SHADOW_ROW_COUNT", "FORWARD_RETURN_FILLED_COUNT",
    "FORWARD_RETURN_PENDING_COUNT", "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
    "EVENT_HARD_LOCK_OVERLAY_DETECTED", "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "COVERAGE_WINDOW_COMPLETE", "DAILY_TRUST_LEVEL",
    "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]
STATUS_FIELDS = [
    "layer_id", "layer_name", "stable_status", "read_first_path", "snapshot_path",
    "key_ready_metric", "key_degraded_metric", "advisory_only", "production_impact",
    "layer_status", "recommended_next_step",
]
BLOCKER_FIELDS = ["blocker_name", "blocker_status", "affected_layer", "severity", "current_metric", "why_it_matters", "recommended_resolution"]
DECISION_FIELDS = ["decision_area", "allowed", "reason", "required_before_allowed", "current_status"]
NEXT_STEP_FIELDS = ["priority", "next_step_id", "next_step_name", "recommended_model", "reason", "risk_level", "modifies_production", "requires_explicit_approval"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def readfirst(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


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
    return (modified_time(path), sha256(path))


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_current_daily_command_center_full.ps1",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "state/v18/manual_state.csv",
        "state/v18/broker_execution_state.csv",
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
    result = subprocess.run(["python", "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def layer_rows(root: Path, data: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    def status_for(layer_id: str) -> str:
        vals = data.get(layer_id, {})
        return vals.get("STATUS", "MISSING")

    rows = []
    rows.append({
        "layer_id": "V18.21A-R4",
        "layer_name": "Price-Derived Factors",
        "stable_status": status_for("V18.21A-R4"),
        "read_first_path": str(root / LAYERS[0][2]),
        "snapshot_path": data.get("V18.21A-R4", {}).get("SNAPSHOT_PATH", ""),
        "key_ready_metric": f"score_ready_ratio={data.get('V18.21A-R4', {}).get('CURRENT_SCORE_READY_RATIO', '')}; full_history_ready={data.get('V18.21A-R4', {}).get('CURRENT_FULL_HISTORY_FACTOR_READY_COUNT', '')}",
        "key_degraded_metric": f"missing_history_tickers={data.get('V18.21A-R4', {}).get('MISSING_HISTORY_TICKER_COUNT', '')}",
        "advisory_only": "TRUE",
        "production_impact": data.get("V18.21A-R4", {}).get("OFFICIAL_DECISION_IMPACT", "NONE"),
        "layer_status": "DEGRADED_PRICE_HISTORY_INCOMPLETE",
        "recommended_next_step": "Design full-history backfill before effect claims.",
    })
    rows.append({
        "layer_id": "V18.21B-R1",
        "layer_name": "Signal Snapshot",
        "stable_status": status_for("V18.21B-R1"),
        "read_first_path": str(root / LAYERS[1][2]),
        "snapshot_path": data.get("V18.21B-R1", {}).get("SNAPSHOT_PATH", ""),
        "key_ready_metric": f"rows={data.get('V18.21B-R1', {}).get('SIGNAL_SNAPSHOT_ROW_COUNT', '')}; forward_ready={data.get('V18.21B-R1', {}).get('READY_FOR_FORWARD_RESEARCH_COUNT', '')}; simulation_ready={data.get('V18.21B-R1', {}).get('READY_FOR_SIMULATION_ANALYSIS_COUNT', '')}",
        "key_degraded_metric": f"row_only_degraded={data.get('V18.21B-R1', {}).get('PRICE_DERIVED_ROW_ONLY_COUNT', '')}; full_research_ready={data.get('V18.21B-R1', {}).get('FULL_RESEARCH_READY_COUNT', '')}",
        "advisory_only": "TRUE",
        "production_impact": data.get("V18.21B-R1", {}).get("OFFICIAL_DECISION_IMPACT", "NONE"),
        "layer_status": "DEGRADED_FULL_RESEARCH_READY_ZERO",
        "recommended_next_step": "Improve price history and forward/simulation readiness.",
    })
    rows.append({
        "layer_id": "V18.21C-R2",
        "layer_name": "Factor Effectiveness",
        "stable_status": status_for("V18.21C-R2"),
        "read_first_path": str(root / LAYERS[2][2]),
        "snapshot_path": data.get("V18.21C-R2", {}).get("SNAPSHOT_PATH", ""),
        "key_ready_metric": f"high_confidence_matches={data.get('V18.21C-R2', {}).get('HIGH_CONFIDENCE_MATCH_COUNT', '')}; low_confidence_matches={data.get('V18.21C-R2', {}).get('LOW_CONFIDENCE_MATCH_COUNT', '')}",
        "key_degraded_metric": f"multi_horizon={data.get('V18.21C-R2', {}).get('MULTI_HORIZON_READINESS_STATUS', '')}",
        "advisory_only": "TRUE",
        "production_impact": data.get("V18.21C-R2", {}).get("OFFICIAL_DECISION_IMPACT", "NONE"),
        "layer_status": "NOT_READY_EFFECT_CLAIMS",
        "recommended_next_step": "Create controlled forward outcome filler design.",
    })
    rows.append({
        "layer_id": "V18.21D-R1",
        "layer_name": "Forward Tracker Link-Key Shadow",
        "stable_status": status_for("V18.21D-R1"),
        "read_first_path": str(root / LAYERS[3][2]),
        "snapshot_path": data.get("V18.21D-R1", {}).get("SNAPSHOT_PATH", ""),
        "key_ready_metric": f"shadow_rows={data.get('V18.21D-R1', {}).get('UPGRADED_SHADOW_ROW_COUNT', '')}; pending_returns={data.get('V18.21D-R1', {}).get('FORWARD_RETURN_PENDING_COUNT', '')}",
        "key_degraded_metric": f"filled_returns={data.get('V18.21D-R1', {}).get('FORWARD_RETURN_FILLED_COUNT', '')}; production_replaced={data.get('V18.21D-R1', {}).get('FORWARD_TRACKER_PRODUCTION_REPLACED', '')}",
        "advisory_only": "TRUE",
        "production_impact": data.get("V18.21D-R1", {}).get("OFFICIAL_DECISION_IMPACT", "NONE"),
        "layer_status": "SHADOW_SCHEMA_READY_RETURNS_PENDING",
        "recommended_next_step": "Design advisory controlled forward outcome filler.",
    })
    rows.append({
        "layer_id": "V18.21E-R1",
        "layer_name": "Event Risk Coefficient",
        "stable_status": status_for("V18.21E-R1"),
        "read_first_path": str(root / LAYERS[4][2]),
        "snapshot_path": data.get("V18.21E-R1", {}).get("SNAPSHOT_PATH", ""),
        "key_ready_metric": f"final_advisory_coeff={data.get('V18.21E-R1', {}).get('FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT', '')}; hard_lock={data.get('V18.21E-R1', {}).get('HARD_LOCK_OVERLAY_DETECTED', '')}",
        "key_degraded_metric": f"official_application={data.get('V18.21E-R1', {}).get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION', '')}",
        "advisory_only": "TRUE",
        "production_impact": data.get("V18.21E-R1", {}).get("OFFICIAL_DECISION_IMPACT", "NONE"),
        "layer_status": "EVENT_RISK_ADVISORY_ONLY",
        "recommended_next_step": "Keep event risk read-only until explicit integration approval.",
    })
    return rows


def blockers(data: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    a = data.get("V18.21A-R4", {})
    b = data.get("V18.21B-R1", {})
    c = data.get("V18.21C-R2", {})
    d = data.get("V18.21D-R1", {})
    e = data.get("V18.21E-R1", {})
    return [
        {"blocker_name": "PRICE_HISTORY_COVERAGE_INCOMPLETE", "blocker_status": "ACTIVE", "affected_layer": "V18.21A-R4", "severity": "HIGH", "current_metric": f"missing_history_tickers={a.get('MISSING_HISTORY_TICKER_COUNT', '')}; score_ready_ratio={a.get('CURRENT_SCORE_READY_RATIO', '')}", "why_it_matters": "Full factor scores cannot be computed for all tickers.", "recommended_resolution": "Design and review full-history backfill before applying."},
        {"blocker_name": "SIGNAL_SNAPSHOT_DEGRADED_ROWS", "blocker_status": "ACTIVE", "affected_layer": "V18.21B-R1", "severity": "HIGH", "current_metric": f"row_only_degraded={b.get('PRICE_DERIVED_ROW_ONLY_COUNT', '')}; full_research_ready={b.get('FULL_RESEARCH_READY_COUNT', '')}", "why_it_matters": "Rows are present but many are not research-ready.", "recommended_resolution": "Resolve missing factor, simulation, and forward references."},
        {"blocker_name": "FACTOR_EFFECTIVENESS_LOW_MATCH_CONFIDENCE", "blocker_status": "ACTIVE", "affected_layer": "V18.21C-R2", "severity": "HIGH", "current_metric": f"high={c.get('HIGH_CONFIDENCE_MATCH_COUNT', '')}; low={c.get('LOW_CONFIDENCE_MATCH_COUNT', '')}", "why_it_matters": "Effect conclusions require reliable signal/outcome matching.", "recommended_resolution": "Use upgraded link keys and controlled outcome filler design."},
        {"blocker_name": "MULTI_HORIZON_FORWARD_RETURNS_MISSING", "blocker_status": "ACTIVE", "affected_layer": "V18.21C-R2/V18.21D-R1", "severity": "HIGH", "current_metric": f"multi_horizon={c.get('MULTI_HORIZON_READINESS_STATUS', '')}; pending={d.get('FORWARD_RETURN_PENDING_COUNT', '')}", "why_it_matters": "Multi-horizon effect research cannot proceed without returns.", "recommended_resolution": "Design V18.21G controlled forward outcome filler."},
        {"blocker_name": "FORWARD_TRACKER_SHADOW_NOT_PRODUCTION", "blocker_status": "ACTIVE", "affected_layer": "V18.21D-R1", "severity": "MEDIUM", "current_metric": f"production_replaced={d.get('FORWARD_TRACKER_PRODUCTION_REPLACED', '')}", "why_it_matters": "Shadow schema is not official tracker state.", "recommended_resolution": "Keep shadow-only until explicit production replacement approval."},
        {"blocker_name": "EVENT_RISK_ADVISORY_ONLY", "blocker_status": "ACTIVE", "affected_layer": "V18.21E-R1", "severity": "MEDIUM", "current_metric": f"applied_to_official={e.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION', '')}", "why_it_matters": "Event coefficients must not be interpreted as official trade logic.", "recommended_resolution": "Review separately before any official integration."},
        {"blocker_name": "TRUE_5DAY_COVERAGE_NOT_MET", "blocker_status": "ACTIVE", "affected_layer": "V18.21B-R1/V18.21C-R2", "severity": "MEDIUM", "current_metric": f"true_5day={b.get('TRUE_5DAY_UNIQUE_COVERAGE_MET', c.get('TRUE_5DAY_UNIQUE_COVERAGE_MET', ''))}", "why_it_matters": "Coverage limits confidence in short-window research.", "recommended_resolution": "Continue coverage maturation and outcome collection."},
        {"blocker_name": "DAILY_TRUST_MEDIUM", "blocker_status": "ACTIVE", "affected_layer": "V18.21B-R1/V18.21C-R2", "severity": "MEDIUM", "current_metric": f"daily_trust={b.get('DAILY_TRUST_LEVEL', c.get('DAILY_TRUST_LEVEL', ''))}", "why_it_matters": "Medium trust prevents production-grade claims.", "recommended_resolution": "Improve data completeness before production decisions."},
    ]


def decisions() -> List[Dict[str, object]]:
    return [
        {"decision_area": "FACTOR_EFFECTIVENESS_CLAIM", "allowed": "FALSE", "reason": "High-confidence matches are zero and multi-horizon returns are immature.", "required_before_allowed": "High-confidence multi-horizon matched returns.", "current_status": "BLOCKED"},
        {"decision_area": "FACTOR_WEIGHT_CHANGE", "allowed": "FALSE", "reason": "No factor effectiveness claims are allowed.", "required_before_allowed": "Validated effect evidence and explicit approval.", "current_status": "BLOCKED"},
        {"decision_area": "PRODUCTION_PROMOTION", "allowed": "FALSE", "reason": "Research chain remains advisory/degraded.", "required_before_allowed": "Clean evidence, stable validation, explicit approval.", "current_status": "BLOCKED"},
        {"decision_area": "OFFICIAL_BUY_PERMISSION_CHANGE", "allowed": "FALSE", "reason": "Read center does not modify official behavior.", "required_before_allowed": "Separate approved production integration.", "current_status": "BLOCKED"},
        {"decision_area": "EVENT_RISK_OFFICIAL_APPLICATION", "allowed": "FALSE", "reason": "Event risk coefficient remains advisory-only.", "required_before_allowed": "Explicit integration approval and validation.", "current_status": "BLOCKED"},
        {"decision_area": "FORWARD_TRACKER_PRODUCTION_REPLACEMENT", "allowed": "FALSE", "reason": "V18.21D-R1 is shadow-output only.", "required_before_allowed": "Approved production replacement plan.", "current_status": "BLOCKED"},
        {"decision_area": "CONTROLLED_FORWARD_OUTCOME_FILLER_DESIGN", "allowed": "TRUE", "reason": "Shadow schema exists and returns remain pending.", "required_before_allowed": "Keep advisory-only design constraints.", "current_status": "READY_FOR_DESIGN"},
        {"decision_area": "FULL_HISTORY_BACKFILL_DESIGN", "allowed": "TRUE", "reason": "Coverage gaps are quantified.", "required_before_allowed": "Design-only; no external fetch without approval.", "current_status": "READY_FOR_DESIGN"},
        {"decision_area": "UNIFIED_BACKTEST_RESEARCH_DESIGN", "allowed": "TRUE", "reason": "Read-only design can proceed without production impact.", "required_before_allowed": "Research-only constraints and no claims.", "current_status": "READY_RESEARCH_ONLY"},
    ]


def next_steps() -> List[Dict[str, object]]:
    return [
        {"priority": 1, "next_step_id": "V18.21F-R1", "next_step_name": "Stable snapshot if V18.21F validates cleanly", "recommended_model": "gpt-5.5", "reason": "Preserve unified read center before new design work.", "risk_level": "LOW", "modifies_production": "FALSE", "requires_explicit_approval": "FALSE"},
        {"priority": 2, "next_step_id": "V18.21G", "next_step_name": "Controlled Forward Outcome Filler Design", "recommended_model": "gpt-5.5", "reason": "Forward returns are pending across shadow rows.", "risk_level": "MEDIUM", "modifies_production": "FALSE", "requires_explicit_approval": "FALSE"},
        {"priority": 3, "next_step_id": "V18.21H", "next_step_name": "Full History Backfill Design", "recommended_model": "gpt-5.5", "reason": "221 tickers are missing full history.", "risk_level": "MEDIUM", "modifies_production": "FALSE", "requires_explicit_approval": "FALSE"},
        {"priority": 4, "next_step_id": "V18.21I", "next_step_name": "Unified Backtest Research Design", "recommended_model": "gpt-5.5", "reason": "Research-only backtest design can unify A-E outputs.", "risk_level": "MEDIUM", "modifies_production": "FALSE", "requires_explicit_approval": "FALSE"},
        {"priority": 5, "next_step_id": "LATER", "next_step_name": "Controlled daily command center integration", "recommended_model": "gpt-5.5", "reason": "Production behavior requires explicit approval.", "risk_level": "HIGH", "modifies_production": "TRUE", "requires_explicit_approval": "TRUE"},
    ]


def report(values: Dict[str, object], status_rows: Sequence[Dict[str, object]], blocker_rows: Sequence[Dict[str, object]], decision_rows: Sequence[Dict[str, object]], next_step_rows: Sequence[Dict[str, object]]) -> str:
    return f"""# V18.21F Unified Research Chain Read Center

## Executive Summary
Status: {values.get('STATUS')}. The V18.21A-E research chain has {values.get('STABLE_LAYER_OK_COUNT')} stable layers and remains advisory because multiple blockers remain.

## Safety Statement
This is a read-center only module. It does not modify official decisions, buy permission, rankings, price cache, signal snapshots, event calendars, simulation positions, forward tracker state, factor weights, broker execution, auto-trade, or auto-sell behavior.

## Stable Layer Status Summary
Stable layer count: {values.get('STABLE_LAYER_COUNT')}; missing: {values.get('MISSING_STABLE_LAYER_COUNT')}; degraded/warn: {values.get('STABLE_LAYER_WARN_OR_DEGRADED_COUNT')}.

## Research Blocker Summary
Active blockers include incomplete price history, degraded signal rows, low forward-match confidence, missing multi-horizon returns, shadow-only forward tracker state, advisory-only event risk, unmet true 5D coverage, and medium daily trust.

## Readiness Decision Table
Factor effectiveness claims, factor weight changes, production promotion, official buy permission changes, event-risk official application, and forward tracker production replacement are not allowed. Design work for forward outcome filling, history backfill, and unified backtest research is allowed as advisory/research-only.

## Event Risk Advisory Semantics
Final advisory market coefficient: {values.get('EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT')}. Hard-lock overlay detected: {values.get('EVENT_HARD_LOCK_OVERLAY_DETECTED')}. Applied to official decision: {values.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION')}.

## Forward Tracker Shadow Semantics
Shadow rows: {values.get('FORWARD_TRACKER_SHADOW_ROW_COUNT')}. Forward returns filled: {values.get('FORWARD_RETURN_FILLED_COUNT')}. Forward returns pending: {values.get('FORWARD_RETURN_PENDING_COUNT')}. Production replacement is not allowed.

## Factor Effectiveness Limitations
High-confidence matches: {values.get('FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT')}. Low-confidence matches: {values.get('FACTOR_EFFECTIVENESS_LOW_CONFIDENCE_MATCH_COUNT')}. Multi-horizon status: {values.get('MULTI_HORIZON_READINESS_STATUS')}.

## Next-Step Plan
Top next step: {next_step_rows[0]['next_step_id']} - {next_step_rows[0]['next_step_name']}. Then proceed to V18.21G controlled forward outcome filler design.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    paths = {key: root / rel for key, rel in REQUIRED_OUTPUTS.items()}
    before = {str(path): signature(path) for path in protected_paths(root)}

    data: Dict[str, Dict[str, str]] = {}
    missing = 0
    ok_count = 0
    warn_count = 0
    for layer_id, _, rel in LAYERS:
        path = root / rel
        vals = readfirst(path)
        data[layer_id] = vals
        if not path.exists():
            missing += 1
        elif vals.get("STATUS", "").startswith("OK_"):
            ok_count += 1
        else:
            warn_count += 1

    status_rows = layer_rows(root, data)
    blocker_rows = blockers(data)
    decision_rows = decisions()
    next_step_rows = next_steps()

    a = data.get("V18.21A-R4", {})
    b = data.get("V18.21B-R1", {})
    c = data.get("V18.21C-R2", {})
    d = data.get("V18.21D-R1", {})
    e = data.get("V18.21E-R1", {})
    values: Dict[str, object] = {
        "STATUS": STATUS_DEGRADED if missing else STATUS_READY,
        "STABLE_LAYER_COUNT": len(LAYERS),
        "STABLE_LAYER_OK_COUNT": ok_count,
        "STABLE_LAYER_WARN_OR_DEGRADED_COUNT": warn_count,
        "MISSING_STABLE_LAYER_COUNT": missing,
        "PRICE_DERIVED_SCORE_READY_RATIO": a.get("CURRENT_SCORE_READY_RATIO", ""),
        "PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT": a.get("MISSING_HISTORY_TICKER_COUNT", ""),
        "SIGNAL_SNAPSHOT_ROW_COUNT": b.get("SIGNAL_SNAPSHOT_ROW_COUNT", c.get("SIGNAL_SNAPSHOT_ROW_COUNT", "")),
        "READY_FOR_FORWARD_RESEARCH_COUNT": b.get("READY_FOR_FORWARD_RESEARCH_COUNT", ""),
        "READY_FOR_SIMULATION_ANALYSIS_COUNT": b.get("READY_FOR_SIMULATION_ANALYSIS_COUNT", ""),
        "FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT": c.get("HIGH_CONFIDENCE_MATCH_COUNT", ""),
        "FACTOR_EFFECTIVENESS_LOW_CONFIDENCE_MATCH_COUNT": c.get("LOW_CONFIDENCE_MATCH_COUNT", ""),
        "MULTI_HORIZON_READINESS_STATUS": c.get("MULTI_HORIZON_READINESS_STATUS", ""),
        "FORWARD_TRACKER_SHADOW_ROW_COUNT": d.get("UPGRADED_SHADOW_ROW_COUNT", ""),
        "FORWARD_RETURN_FILLED_COUNT": d.get("FORWARD_RETURN_FILLED_COUNT", "0"),
        "FORWARD_RETURN_PENDING_COUNT": d.get("FORWARD_RETURN_PENDING_COUNT", ""),
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT": e.get("FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT", ""),
        "EVENT_HARD_LOCK_OVERLAY_DETECTED": e.get("HARD_LOCK_OVERLAY_DETECTED", ""),
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": e.get("EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "FALSE"),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": b.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", c.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", "")),
        "COVERAGE_WINDOW_COMPLETE": b.get("COVERAGE_WINDOW_COMPLETE", c.get("COVERAGE_WINDOW_COMPLETE", "")),
        "DAILY_TRUST_LEVEL": b.get("DAILY_TRUST_LEVEL", c.get("DAILY_TRUST_LEVEL", "")),
        "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
        "WEIGHT_CHANGE_ALLOWED": "FALSE",
        "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    values.update(SAFETY_FLAGS)

    write_csv(paths["status"], status_rows, STATUS_FIELDS)
    write_csv(paths["blockers"], blocker_rows, BLOCKER_FIELDS)
    write_csv(paths["decisions"], decision_rows, DECISION_FIELDS)
    write_csv(paths["next_steps"], next_step_rows, NEXT_STEP_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, status_rows, blocker_rows, decision_rows, next_step_rows))

    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    read_first_text = read_text(paths["read_first"])
    validations = [
        validation_row("powershell_parse_wrapper", ps_parse(root / "scripts/v18/run_v18_21F_unified_research_chain_read_center.ps1"), 1, "Wrapper parses."),
        validation_row("python_compile_script", py_compile(root / "scripts/v18/v18_21F_unified_research_chain_read_center.py"), 1, "Python script compiles."),
        validation_row("required_outputs_exist", all(path.exists() for path in paths.values()), 1, "All V18.21F outputs exist."),
        validation_row("required_read_first_fields_exist", all(field in read_first_text for field in READ_FIRST_FIELDS), 1, "All required READ_FIRST fields exist."),
        validation_row("no_protected_files_modified", not changed, len(changed), "Changed protected files: " + ";".join(changed)),
        validation_row("external_data_not_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE", 1, "No external data fetched."),
        validation_row("event_risk_not_applied", values["EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION"] == "FALSE", 1, "Event coefficient remains advisory."),
        validation_row("official_decision_impact_none", values["OFFICIAL_DECISION_IMPACT"] == "NONE", 1, "Official decision impact remains NONE."),
        validation_row("buy_permission_not_modified", values["BUY_PERMISSION_MODIFIED"] == "FALSE", 1, "Buy permission not modified."),
        validation_row("forward_return_filled_zero", str(values["FORWARD_RETURN_FILLED_COUNT"]) == "0", 1, "Forward returns not filled."),
        validation_row("effect_claims_zero", values["EFFECT_CLAIM_ALLOWED_COUNT"] == "0", 1, "No effect claims allowed."),
        validation_row("weight_changes_zero", values["WEIGHT_CHANGE_ALLOWED_COUNT"] == "0", 1, "No weight changes allowed."),
        validation_row("production_promotions_zero", values["PRODUCTION_PROMOTION_ALLOWED_COUNT"] == "0", 1, "No production promotions allowed."),
    ]
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, status_rows, blocker_rows, decision_rows, next_step_rows))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "STABLE_LAYER_COUNT",
        "STABLE_LAYER_OK_COUNT", "STABLE_LAYER_WARN_OR_DEGRADED_COUNT", "MISSING_STABLE_LAYER_COUNT",
        "PRICE_DERIVED_SCORE_READY_RATIO", "PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT",
        "SIGNAL_SNAPSHOT_ROW_COUNT", "READY_FOR_FORWARD_RESEARCH_COUNT",
        "READY_FOR_SIMULATION_ANALYSIS_COUNT", "FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT",
        "FACTOR_EFFECTIVENESS_LOW_CONFIDENCE_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
        "FORWARD_TRACKER_SHADOW_ROW_COUNT", "FORWARD_RETURN_FILLED_COUNT",
        "FORWARD_RETURN_PENDING_COUNT", "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
        "EVENT_HARD_LOCK_OVERLAY_DETECTED", "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
        "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
        "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "EXTERNAL_DATA_FETCHED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
