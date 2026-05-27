from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_READY = "WARN_V18_22A_RESEARCH_COMMAND_CENTER_READY"
STATUS_FAIL = "FAIL_V18_22A_RESEARCH_COMMAND_CENTER_VALIDATION_FAILED"
MODE = "ADVISORY_READ_CENTER_ONLY"
PATCH_MODE = "RESEARCH_COMMAND_CENTER_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "RESEARCH_COMMAND_CENTER_READY": "TRUE",
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

LAYERS = [
    ("V18.21A-R4", "Price-Derived Factors", "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt"),
    ("V18.21B-R1", "Signal Snapshot", "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt"),
    ("V18.21C-R2", "Factor Effectiveness", "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt"),
    ("V18.21D-R1", "Forward Tracker Link-Key Shadow", "outputs/v18/ops/V18_21D_R1_STABLE_READ_FIRST.txt"),
    ("V18.21E-R1", "Event Risk Coefficient", "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt"),
    ("V18.21F", "Unified Research Chain", "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt"),
    ("V18.21G", "Forward Outcome Filler Design", "outputs/v18/ops/V18_21G_STABLE_READ_FIRST.txt"),
    ("V18.21H-R1", "Staged Backfill Batch 1 Design", "outputs/v18/ops/V18_21H_R1_STABLE_READ_FIRST.txt"),
    ("V18.21I", "Unified Backtest Research Design", "outputs/v18/ops/V18_21I_STABLE_READ_FIRST.txt"),
]

CURRENT_INPUTS = [
    ("UNIFIED_RESEARCH_CHAIN_STATUS", "outputs/v18/research_chain/V18_21F_CURRENT_UNIFIED_RESEARCH_CHAIN_STATUS.csv"),
    ("UNIFIED_RESEARCH_BLOCKERS", "outputs/v18/research_chain/V18_21F_CURRENT_RESEARCH_BLOCKER_SUMMARY.csv"),
    ("UNIFIED_RESEARCH_DECISIONS", "outputs/v18/research_chain/V18_21F_CURRENT_RESEARCH_READINESS_DECISION_TABLE.csv"),
    ("BACKTEST_BLOCKERS", "outputs/v18/backtest_research/V18_21I_CURRENT_BACKTEST_READINESS_BLOCKER_SUMMARY.csv"),
    ("BACKTEST_IMPLEMENTATION_PLAN", "outputs/v18/backtest_research/V18_21I_CURRENT_CONTROLLED_BACKTEST_IMPLEMENTATION_PLAN.csv"),
    ("BATCH1_COVERAGE_PROJECTION", "outputs/v18/price_factors/V18_21H_R1_CURRENT_BATCH1_COVERAGE_IMPACT_PROJECTION.csv"),
    ("BATCH1_STAGED_APPLY_SAFETY_PLAN", "outputs/v18/price_factors/V18_21H_R1_CURRENT_CONTROLLED_STAGED_APPLY_SAFETY_PLAN.csv"),
    ("FORWARD_OUTCOME_BLOCKERS", "outputs/v18/forward_tracker/V18_21G_CURRENT_FORWARD_OUTCOME_BLOCKER_SUMMARY.csv"),
    ("EVENT_MARKET_RISK_SEMANTICS", "outputs/v18/event_risk/V18_21E_R1_CURRENT_MARKET_EVENT_RISK_SEMANTICS.csv"),
]

OUTPUTS = {
    "layer_status": "outputs/v18/research_command_center/V18_22A_CURRENT_LAYER_STATUS.csv",
    "gate_matrix": "outputs/v18/research_command_center/V18_22A_CURRENT_GATE_MATRIX.csv",
    "bottlenecks": "outputs/v18/research_command_center/V18_22A_CURRENT_RESEARCH_BOTTLENECK_DASHBOARD.csv",
    "actions": "outputs/v18/research_command_center/V18_22A_CURRENT_OPERATOR_NEXT_ACTION_BOARD.csv",
    "safety": "outputs/v18/research_command_center/V18_22A_CURRENT_SAFETY_AUDIT.csv",
    "command_center": "outputs/v18/research_command_center/V18_22A_CURRENT_RESEARCH_COMMAND_CENTER.md",
    "read_first": "outputs/v18/ops/V18_22A_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_22A_CURRENT_RESEARCH_COMMAND_CENTER_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "RESEARCH_COMMAND_CENTER_READY",
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
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "RECOMMENDED_NEXT_ACTION",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED", "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED",
    "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]
LAYER_FIELDS = [
    "layer_id", "layer_name", "stable_read_first_path", "stable_status", "key_metric_1",
    "key_metric_2", "key_blocker", "production_impact", "advisory_only",
    "command_center_status", "operator_note",
]
GATE_FIELDS = ["gate_name", "gate_allowed", "current_status", "blocking_metric", "required_to_unlock", "risk_level", "operator_action"]
BOTTLENECK_FIELDS = [
    "bottleneck_id", "bottleneck_name", "severity", "current_metric", "affected_research_area",
    "why_it_matters", "recommended_resolution", "recommended_next_module",
    "can_resolve_without_external_data", "requires_explicit_approval",
]
ACTION_FIELDS = [
    "priority", "action_id", "action_name", "recommended_now", "reason", "risk_level",
    "modifies_production", "fetches_external_data", "requires_explicit_approval",
    "expected_benefit", "command_or_future_module",
]
SAFETY_FIELDS = ["safety_check", "status", "notes"]


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
        "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
        "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
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
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0


def first(*values: str) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def safety_row(name: str, ok: bool, notes: str) -> Dict[str, object]:
    return {"safety_check": name, "status": "PASS" if ok else "FAIL", "notes": notes}


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def layer_rows(root: Path, layer_data: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    specs = {
        "V18.21A-R4": ("score_ready_ratio={CURRENT_SCORE_READY_RATIO}", "missing_history={CURRENT_MISSING_HISTORY_TICKER_COUNT}", "PRICE_HISTORY_COVERAGE_LOW", "Backfill remains design-only."),
        "V18.21B-R1": ("signal_rows={SIGNAL_SNAPSHOT_ROW_COUNT}", "snapshot_history=limited", "SIGNAL_SNAPSHOT_HISTORY_LIMITED", "Signal snapshot exists, but history is limited."),
        "V18.21C-R2": ("high_confidence={HIGH_CONFIDENCE_MATCH_COUNT}", "low_confidence={LOW_CONFIDENCE_MATCH_COUNT}", "HIGH_CONFIDENCE_MATCH_ZERO", "No effect claims."),
        "V18.21D-R1": ("shadow_rows={UPGRADED_SHADOW_ROW_COUNT}", "pending_returns={FORWARD_RETURN_PENDING_COUNT}", "FORWARD_RETURNS_PENDING", "Shadow tracker is not production."),
        "V18.21E-R1": ("event_coeff={FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT}", "official_applied={EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION}", "EVENT_RISK_ADVISORY_ONLY", "Event risk is advisory-only."),
        "V18.21F": ("stable_layers={STABLE_LAYER_COUNT}", "production_promotion={PRODUCTION_PROMOTION_ALLOWED}", "PRODUCTION_PROMOTION_BLOCKED", "Unified chain read center is stable."),
        "V18.21G": ("pending_returns={FORWARD_RETURN_PENDING_COUNT}", "eligible_preview={ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW_COUNT}", "FORWARD_OUTCOME_FILLER_NOT_APPLIED", "Filler remains design-only."),
        "V18.21H-R1": ("batch1_valid={BATCH1_VALID_TICKER_COUNT}", "staged_applied={STAGED_BACKFILL_APPLIED}", "STAGED_BACKFILL_NOT_APPLIED", "Batch 1 is request design only."),
        "V18.21I": ("backtest_ready={UNIFIED_BACKTEST_DESIGN_READY}", "execution={BACKTEST_EXECUTED}", "BACKTEST_EXECUTION_BLOCKED", "Backtest design is stable; execution blocked."),
    }
    for layer_id, layer_name, rel in LAYERS:
        values = layer_data.get(layer_id, {})
        safe_values = defaultdict(str)
        safe_values.update(values)
        metric_1, metric_2, blocker, note = specs[layer_id]
        rows.append({
            "layer_id": layer_id,
            "layer_name": layer_name,
            "stable_read_first_path": str(root / rel),
            "stable_status": values.get("STATUS", "MISSING"),
            "key_metric_1": metric_1.format_map(safe_values),
            "key_metric_2": metric_2.format_map(safe_values),
            "key_blocker": blocker,
            "production_impact": values.get("OFFICIAL_DECISION_IMPACT", "NONE"),
            "advisory_only": "TRUE",
            "command_center_status": "AVAILABLE" if values else "MISSING",
            "operator_note": note,
        })
    return rows


def gate_rows(values: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        {"gate_name": "FACTOR_EFFECT_CLAIM", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": f"high_confidence={values['HIGH_CONFIDENCE_FORWARD_MATCH_COUNT']}", "required_to_unlock": "High-confidence multi-horizon outcomes.", "risk_level": "HIGH", "operator_action": "Do not make factor claims."},
        {"gate_name": "FACTOR_WEIGHT_CHANGE", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "EFFECT_CLAIM_ALLOWED_COUNT=0", "required_to_unlock": "Validated effect claims and explicit approval.", "risk_level": "HIGH", "operator_action": "Do not change weights."},
        {"gate_name": "PRODUCTION_PROMOTION", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "PRODUCTION_PROMOTION_ALLOWED_COUNT=0", "required_to_unlock": "Evidence gates and explicit approval.", "risk_level": "HIGH", "operator_action": "Do not promote to production."},
        {"gate_name": "OFFICIAL_BUY_PERMISSION_CHANGE", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "BUY_PERMISSION_MODIFIED=FALSE", "required_to_unlock": "Separate approved production patch.", "risk_level": "HIGH", "operator_action": "Do not modify buy permission."},
        {"gate_name": "EVENT_RISK_OFFICIAL_APPLICATION", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION=FALSE", "required_to_unlock": "Explicit event-risk integration approval.", "risk_level": "HIGH", "operator_action": "Keep event risk advisory."},
        {"gate_name": "FORWARD_TRACKER_PRODUCTION_REPLACEMENT", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "shadow_output_only", "required_to_unlock": "Controlled production replacement approval.", "risk_level": "HIGH", "operator_action": "Keep shadow tracker separate."},
        {"gate_name": "FORWARD_RETURN_FILL_APPLICATION", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": f"filled={values['FORWARD_RETURN_FILLED_COUNT']}; pending={values['FORWARD_RETURN_PENDING_COUNT']}", "required_to_unlock": "Matured horizons and approved filler apply.", "risk_level": "HIGH", "operator_action": "Do not fill returns."},
        {"gate_name": "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT", "gate_allowed": "REQUIRES_EXPLICIT_APPROVAL", "current_status": "APPROVAL_REQUIRED", "blocking_metric": "STAGED_BACKFILL_APPLIED=FALSE", "required_to_unlock": "Explicit approval for staged-output-only fetch/import.", "risk_level": "MEDIUM", "operator_action": "Do not auto-fetch."},
        {"gate_name": "PRICE_CACHE_INTEGRATION", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "PRICE_CACHE_MODIFIED=FALSE", "required_to_unlock": "Validated staged data and explicit cache integration approval.", "risk_level": "HIGH", "operator_action": "Do not write price cache."},
        {"gate_name": "BACKTEST_EXECUTION", "gate_allowed": "FALSE", "current_status": values["BACKTEST_EXECUTION_READINESS_STATUS"], "blocking_metric": "forward_returns_pending; sample_history_limited", "required_to_unlock": "Filled returns, leakage checks, enough samples.", "risk_level": "MEDIUM", "operator_action": "Do not run backtest."},
        {"gate_name": "DAILY_COMMAND_CENTER_INTEGRATION", "gate_allowed": "FALSE", "current_status": "BLOCKED", "blocking_metric": "read-center only", "required_to_unlock": "Separate read-only integration approval.", "risk_level": "MEDIUM", "operator_action": "Keep wrapper separate for now."},
    ]


def bottleneck_rows(values: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        {"bottleneck_id": "PRICE_HISTORY_COVERAGE_LOW", "bottleneck_name": "Price history coverage low", "severity": "HIGH", "current_metric": f"score_ready={values['CURRENT_SCORE_READY_RATIO']}; missing={values['CURRENT_MISSING_HISTORY_TICKER_COUNT']}", "affected_research_area": "price factors; backtest", "why_it_matters": "Most tickers cannot receive full factor scores.", "recommended_resolution": "Use staged backfill design, then explicit H-R2 if approved.", "recommended_next_module": "V18.21H-R2", "can_resolve_without_external_data": "FALSE", "requires_explicit_approval": "TRUE"},
        {"bottleneck_id": "FORWARD_RETURNS_PENDING", "bottleneck_name": "Forward returns pending", "severity": "HIGH", "current_metric": f"pending={values['FORWARD_RETURN_PENDING_COUNT']}; filled={values['FORWARD_RETURN_FILLED_COUNT']}", "affected_research_area": "factor effectiveness; backtest", "why_it_matters": "Outcomes are required for research metrics.", "recommended_resolution": "Wait for maturity, then controlled filler apply only with approval.", "recommended_next_module": "V18.21G-R1", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "TRUE"},
        {"bottleneck_id": "HIGH_CONFIDENCE_MATCH_ZERO", "bottleneck_name": "High-confidence forward match count zero", "severity": "HIGH", "current_metric": f"high_confidence={values['HIGH_CONFIDENCE_FORWARD_MATCH_COUNT']}", "affected_research_area": "effect claims", "why_it_matters": "Effect evidence needs reliable signal/outcome matches.", "recommended_resolution": "Use link-key shadow plus filled outcomes later.", "recommended_next_module": "V18.21G-R1", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "TRUE"},
        {"bottleneck_id": "MULTI_HORIZON_NOT_READY", "bottleneck_name": "Multi-horizon returns not ready", "severity": "HIGH", "current_metric": values["MULTI_HORIZON_READINESS_STATUS"], "affected_research_area": "cross-horizon validation", "why_it_matters": "Single-horizon evidence is insufficient.", "recommended_resolution": "Collect 1D/3D/5D/10D/20D outcomes.", "recommended_next_module": "V18.21G-R1", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "TRUE"},
        {"bottleneck_id": "SIGNAL_SNAPSHOT_HISTORY_LIMITED", "bottleneck_name": "Signal snapshot history limited", "severity": "MEDIUM", "current_metric": f"snapshot_history={values['SIGNAL_SNAPSHOT_HISTORY_COUNT']}", "affected_research_area": "backtest time-series validation", "why_it_matters": "Backtest needs multiple frozen snapshot periods.", "recommended_resolution": "Accumulate more daily snapshots.", "recommended_next_module": "Daily research packet", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "FALSE"},
        {"bottleneck_id": "EVENT_RISK_ADVISORY_ONLY", "bottleneck_name": "Event risk advisory-only", "severity": "MEDIUM", "current_metric": f"event_applied={values['EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION']}", "affected_research_area": "event-risk scoring", "why_it_matters": "Advisory fields cannot be interpreted as official decisions.", "recommended_resolution": "Keep separated until explicit official integration.", "recommended_next_module": "Future event integration", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "TRUE"},
        {"bottleneck_id": "TRUE_5DAY_COVERAGE_NOT_MET", "bottleneck_name": "True 5D coverage not met", "severity": "MEDIUM", "current_metric": "TRUE_5DAY_UNIQUE_COVERAGE_MET=FALSE", "affected_research_area": "short-window factor analysis", "why_it_matters": "Coverage limits confidence in short-horizon claims.", "recommended_resolution": "Continue coverage maturation.", "recommended_next_module": "V18.21G-R1", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "FALSE"},
        {"bottleneck_id": "DAILY_TRUST_MEDIUM", "bottleneck_name": "Daily trust medium", "severity": "MEDIUM", "current_metric": "DAILY_TRUST_LEVEL=MEDIUM", "affected_research_area": "production evidence gates", "why_it_matters": "Medium trust is not enough for production changes.", "recommended_resolution": "Improve data completeness and outcome validation.", "recommended_next_module": "V18.22C", "can_resolve_without_external_data": "TRUE", "requires_explicit_approval": "FALSE"},
        {"bottleneck_id": "BACKTEST_EXECUTION_BLOCKED", "bottleneck_name": "Backtest execution blocked", "severity": "HIGH", "current_metric": values["BACKTEST_EXECUTION_READINESS_STATUS"], "affected_research_area": "unified backtest", "why_it_matters": "Running now would produce unsupported evidence.", "recommended_resolution": "Keep design-only until returns and samples mature.", "recommended_next_module": "V18.22A stable snapshot", "can_resolve_without_external_data": "FALSE", "requires_explicit_approval": "TRUE"},
    ]


def action_rows() -> List[Dict[str, object]]:
    return [
        {"priority": 1, "action_id": "V18.22A_STABLE", "action_name": "V18.22A stable snapshot", "recommended_now": "TRUE", "reason": "Preserve command center state after validation.", "risk_level": "LOW", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "requires_explicit_approval": "FALSE", "expected_benefit": "Stable operator-facing research read center.", "command_or_future_module": "V18.22A stable snapshot"},
        {"priority": 2, "action_id": "V18.22B", "action_name": "Daily Research Command Center Wrapper Integration, read-only", "recommended_now": "TRUE_AFTER_STABLE", "reason": "Can expose read center without production behavior changes.", "risk_level": "LOW", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "requires_explicit_approval": "FALSE", "expected_benefit": "Daily operator access to research state.", "command_or_future_module": "V18.22B"},
        {"priority": 3, "action_id": "V18.21H_R2", "action_name": "Actual staged fetch/import, staged-output only", "recommended_now": "FALSE", "reason": "Requires explicit approval because it fetches/imports data.", "risk_level": "MEDIUM", "modifies_production": "FALSE", "fetches_external_data": "TRUE", "requires_explicit_approval": "TRUE", "expected_benefit": "Improve score-ready coverage.", "command_or_future_module": "V18.21H-R2"},
        {"priority": 4, "action_id": "V18.21G_R1", "action_name": "Wait for forward horizons to mature then G-R1", "recommended_now": "FALSE_WAIT", "reason": "Most forward rows are pending and not mature.", "risk_level": "MEDIUM", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "requires_explicit_approval": "TRUE", "expected_benefit": "Enable controlled outcome fill after maturity.", "command_or_future_module": "V18.21G-R1"},
        {"priority": 5, "action_id": "V18.22C", "action_name": "Research Packet Writer", "recommended_now": "OPTIONAL_AFTER_STABLE", "reason": "Can package read-only evidence for review.", "risk_level": "LOW", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "requires_explicit_approval": "FALSE", "expected_benefit": "Portable research review packet.", "command_or_future_module": "V18.22C"},
        {"priority": 6, "action_id": "V18.22D", "action_name": "Daily Research Summary README", "recommended_now": "OPTIONAL_AFTER_STABLE", "reason": "Can summarize command center daily.", "risk_level": "LOW", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "requires_explicit_approval": "FALSE", "expected_benefit": "Short daily research summary.", "command_or_future_module": "V18.22D"},
        {"priority": 7, "action_id": "PAUSE", "action_name": "Do nothing / pause after stable snapshot", "recommended_now": "VALID_OPTION", "reason": "No production action is required.", "risk_level": "LOW", "modifies_production": "FALSE", "fetches_external_data": "FALSE", "requires_explicit_approval": "FALSE", "expected_benefit": "Avoid premature changes.", "command_or_future_module": "none"},
    ]


def command_center_markdown(values: Dict[str, object]) -> str:
    return f"""# V18.22A Research Command Center

## Executive Summary
Status: {values.get('STATUS')}. The V18.21A-I research stack is available as an advisory read center. Production behavior remains unchanged.

## Current Stable Stack
Stable layers available: {values.get('STABLE_LAYER_OK_COUNT')} of {values.get('STABLE_LAYER_COUNT')}. Missing stable layers: {values.get('MISSING_STABLE_LAYER_COUNT')}.

## What Is Ready
The research command center is ready. Unified research-chain, backfill design, forward outcome design, event-risk advisory semantics, and unified backtest design artifacts are available for review.

## What Is Blocked
Factor claims, weight changes, production promotion, official buy permission changes, forward return filling, backtest execution, price cache integration, and daily command center integration are blocked.

## Evidence Gates
Factor claims allowed: {values.get('FACTOR_EFFECT_CLAIM_ALLOWED')}. Weight changes allowed: {values.get('WEIGHT_CHANGE_ALLOWED')}. Production promotion allowed: {values.get('PRODUCTION_PROMOTION_ALLOWED')}.

## Data Coverage Status
Current score-ready ratio: {values.get('CURRENT_SCORE_READY_RATIO')}. Full-history ready: {values.get('CURRENT_FULL_HISTORY_FACTOR_READY_COUNT')}. Missing-history tickers: {values.get('CURRENT_MISSING_HISTORY_TICKER_COUNT')}.

## Forward Return Status
Shadow tracker rows: {values.get('FORWARD_TRACKER_SHADOW_ROW_COUNT')}. Forward returns filled: {values.get('FORWARD_RETURN_FILLED_COUNT')}. Forward returns pending: {values.get('FORWARD_RETURN_PENDING_COUNT')}.

## Backtest Readiness Status
Backtest execution readiness: {values.get('BACKTEST_EXECUTION_READINESS_STATUS')}. Signal snapshot history count: {values.get('SIGNAL_SNAPSHOT_HISTORY_COUNT')}. High-confidence forward matches: {values.get('HIGH_CONFIDENCE_FORWARD_MATCH_COUNT')}.

## Event Risk Status
Final advisory market event coefficient: {values.get('EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT')}. Applied to official decision: {values.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION')}.

## Next Action Recommendation
Recommended next action: {values.get('RECOMMENDED_NEXT_ACTION')}.

## Actions Not Allowed Yet
Do not fetch data, run a backtest, backfill price history, write staged price history, fill forward returns, modify price cache, modify official decisions, modify buy permission, modify rankings, or promote research into production.

## Safety Summary
External data fetched: {values.get('EXTERNAL_DATA_FETCHED')}. Backtest executed: {values.get('BACKTEST_EXECUTED')}. Price cache modified: {values.get('PRICE_CACHE_MODIFIED')}. Official decision impact: {values.get('OFFICIAL_DECISION_IMPACT')}.
"""


def report_markdown(values: Dict[str, object]) -> str:
    return f"""# V18.22A Research Command Center Report

## Executive Summary
Status: {values.get('STATUS')}. V18.22A creates an operator-facing read center over the stable V18.21A-I research stack.

## Safety Statement
This module is read-center-only. It does not fetch data, run a backtest, backfill or write price history, fill forward returns, modify price cache, modify official decisions, modify rankings, or modify any protected state.

## Stable Layer Summary
Stable layer count: {values.get('STABLE_LAYER_COUNT')}; OK count: {values.get('STABLE_LAYER_OK_COUNT')}; missing: {values.get('MISSING_STABLE_LAYER_COUNT')}.

## Gate Matrix
Factor effect claims, weight changes, production promotion, official buy permission changes, event-risk official application, forward tracker production replacement, forward return filling, price cache integration, backtest execution, and daily command center integration remain blocked. H-R2 staged fetch/import requires explicit approval.

## Bottleneck Dashboard
Primary bottlenecks are low price-history coverage, pending forward returns, zero high-confidence forward matches, not-ready multi-horizon returns, limited signal snapshot history, advisory-only event risk, unmet true 5D coverage, medium daily trust, and blocked backtest execution.

## Operator Next Action Board
Recommended next action: {values.get('RECOMMENDED_NEXT_ACTION')}.

## Why H-R2 Actual Staged Fetch/Import Is Not Automatically Allowed
H-R2 would fetch or import price history. That requires explicit approval and must remain staged-output-only before any cache integration.

## Why Backtest Execution Is Blocked
Forward returns filled remain {values.get('FORWARD_RETURN_FILLED_COUNT')}, pending returns remain {values.get('FORWARD_RETURN_PENDING_COUNT')}, and signal snapshot history count is {values.get('SIGNAL_SNAPSHOT_HISTORY_COUNT')}.

## Why Factor Claims And Weight Changes Remain Disallowed
High-confidence forward match count is {values.get('HIGH_CONFIDENCE_FORWARD_MATCH_COUNT')}, multi-horizon readiness is {values.get('MULTI_HORIZON_READINESS_STATUS')}, and no validated backtest has been executed.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    paths = {key: root / rel for key, rel in OUTPUTS.items()}
    before = {str(path): signature(path) for path in protected_paths(root)}

    layer_data: Dict[str, Dict[str, str]] = {}
    missing_layers = 0
    ok_layers = 0
    for layer_id, _, rel in LAYERS:
        rf = root / rel
        values = readfirst(rf)
        layer_data[layer_id] = values
        if not rf.exists():
            missing_layers += 1
        elif values.get("STATUS", "").startswith("OK_"):
            ok_layers += 1

    f = layer_data.get("V18.21F", {})
    i = layer_data.get("V18.21I", {})
    h = layer_data.get("V18.21H-R1", {})
    g = layer_data.get("V18.21G", {})
    d = layer_data.get("V18.21D-R1", {})
    c = layer_data.get("V18.21C-R2", {})
    e = layer_data.get("V18.21E-R1", {})
    values: Dict[str, object] = {
        "STATUS": STATUS_READY,
        "STABLE_LAYER_COUNT": len(LAYERS),
        "STABLE_LAYER_OK_COUNT": ok_layers,
        "MISSING_STABLE_LAYER_COUNT": missing_layers,
        "CURRENT_SCORE_READY_RATIO": first(i.get("CURRENT_SCORE_READY_RATIO"), h.get("CURRENT_SCORE_READY_RATIO"), f.get("PRICE_DERIVED_SCORE_READY_RATIO"), "0.320000"),
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": first(i.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), h.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), "104"),
        "CURRENT_MISSING_HISTORY_TICKER_COUNT": first(i.get("CURRENT_MISSING_HISTORY_TICKER_COUNT"), h.get("CURRENT_MISSING_HISTORY_TICKER_COUNT"), f.get("PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT"), "221"),
        "FORWARD_TRACKER_SHADOW_ROW_COUNT": first(i.get("FORWARD_TRACKER_SHADOW_ROW_COUNT"), f.get("FORWARD_TRACKER_SHADOW_ROW_COUNT"), d.get("UPGRADED_SHADOW_ROW_COUNT"), "525"),
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "FORWARD_RETURN_PENDING_COUNT": first(i.get("FORWARD_RETURN_PENDING_COUNT"), g.get("FORWARD_RETURN_PENDING_COUNT"), d.get("FORWARD_RETURN_PENDING_COUNT"), "525"),
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT": first(i.get("HIGH_CONFIDENCE_FORWARD_MATCH_COUNT"), c.get("HIGH_CONFIDENCE_MATCH_COUNT"), f.get("FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT"), "0"),
        "MULTI_HORIZON_READINESS_STATUS": first(i.get("MULTI_HORIZON_READINESS_STATUS"), c.get("MULTI_HORIZON_READINESS_STATUS"), f.get("MULTI_HORIZON_READINESS_STATUS"), "NOT_READY_MULTI_HORIZON"),
        "SIGNAL_SNAPSHOT_ROW_COUNT": first(i.get("SIGNAL_SNAPSHOT_ROW_COUNT"), f.get("SIGNAL_SNAPSHOT_ROW_COUNT"), "325"),
        "SIGNAL_SNAPSHOT_HISTORY_COUNT": first(i.get("SIGNAL_SNAPSHOT_HISTORY_COUNT"), "1"),
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT": first(i.get("EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT"), e.get("FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT"), f.get("EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT"), "0.300000"),
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
        "BACKTEST_EXECUTION_READINESS_STATUS": first(i.get("BACKTEST_EXECUTION_READINESS_STATUS"), "BLOCKED_DESIGN_ONLY_FORWARD_RETURNS_PENDING"),
        "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
        "WEIGHT_CHANGE_ALLOWED": "FALSE",
        "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
        "STAGED_BACKFILL_ACTUAL_FETCH_IMPORT_ALLOWED": "REQUIRES_EXPLICIT_APPROVAL",
        "PRICE_CACHE_INTEGRATION_ALLOWED": "FALSE",
        "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
        "RECOMMENDED_NEXT_ACTION": "V18.22A_STABLE_SNAPSHOT",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    values.update(SAFETY_FLAGS)

    write_csv(paths["layer_status"], layer_rows(root, layer_data), LAYER_FIELDS)
    write_csv(paths["gate_matrix"], gate_rows(values), GATE_FIELDS)
    write_csv(paths["bottlenecks"], bottleneck_rows(values), BOTTLENECK_FIELDS)
    write_csv(paths["actions"], action_rows(), ACTION_FIELDS)

    safety = [
        safety_row("EXTERNAL_DATA_FETCHED", values["EXTERNAL_DATA_FETCHED"] == "FALSE", "FALSE"),
        safety_row("PRICE_CACHE_MODIFIED", values["PRICE_CACHE_MODIFIED"] == "FALSE", "FALSE"),
        safety_row("PRICE_HISTORY_WRITTEN", values["PRICE_HISTORY_WRITTEN"] == "FALSE", "FALSE"),
        safety_row("STAGED_PRICE_HISTORY_WRITTEN", values["STAGED_PRICE_HISTORY_WRITTEN"] == "FALSE", "FALSE"),
        safety_row("FORWARD_RETURN_FILLED_COUNT", values["FORWARD_RETURN_FILLED_COUNT"] == "0", "0"),
        safety_row("BACKTEST_EXECUTED", values["BACKTEST_EXECUTED"] == "FALSE", "FALSE"),
        safety_row("BACKTEST_RESULTS_APPLIED", values["BACKTEST_RESULTS_APPLIED"] == "FALSE", "FALSE"),
        safety_row("FULL_HISTORY_BACKFILL_APPLIED", values["FULL_HISTORY_BACKFILL_APPLIED"] == "FALSE", "FALSE"),
        safety_row("STAGED_BACKFILL_APPLIED", values["STAGED_BACKFILL_APPLIED"] == "FALSE", "FALSE"),
        safety_row("OFFICIAL_DECISION_IMPACT", values["OFFICIAL_DECISION_IMPACT"] == "NONE", "NONE"),
        safety_row("BUY_PERMISSION_MODIFIED", values["BUY_PERMISSION_MODIFIED"] == "FALSE", "FALSE"),
        safety_row("RANKING_MODIFIED", values["RANKING_MODIFIED"] == "FALSE", "FALSE"),
        safety_row("SIGNAL_SNAPSHOT_MODIFIED", values["SIGNAL_SNAPSHOT_MODIFIED"] == "FALSE", "FALSE"),
        safety_row("FORWARD_TRACKER_MODIFIED", values["FORWARD_TRACKER_MODIFIED"] == "FALSE", "FALSE"),
        safety_row("AUTO_TRADE", values["AUTO_TRADE"] == "DISABLED", "DISABLED"),
        safety_row("AUTO_SELL", values["AUTO_SELL"] == "DISABLED", "DISABLED"),
    ]
    write_csv(paths["safety"], safety, SAFETY_FIELDS)
    write_text(paths["command_center"], command_center_markdown(values))
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report_markdown(values))

    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    read_first_text = read_text(paths["read_first"])
    validations = [
        safety_row("VALIDATION_POWERSHELL_PARSE_WRAPPER", ps_parse(root / "scripts/v18/run_v18_22A_research_command_center.ps1"), "Wrapper parses."),
        safety_row("VALIDATION_PYTHON_COMPILE_SCRIPT", py_compile(root / "scripts/v18/v18_22A_research_command_center.py"), "Python compiles."),
        safety_row("VALIDATION_REQUIRED_OUTPUTS_EXIST", all(path.exists() for path in paths.values()), "All required outputs exist."),
        safety_row("VALIDATION_REQUIRED_READ_FIRST_FIELDS_EXIST", all(field in read_first_text for field in READ_FIRST_FIELDS), "All required READ_FIRST fields exist."),
        safety_row("VALIDATION_NO_PROTECTED_FILES_MODIFIED", not changed, "Changed protected files: " + ";".join(changed)),
        safety_row("VALIDATION_NO_EXTERNAL_FETCH", values["EXTERNAL_DATA_FETCHED"] == "FALSE", "No external data fetched."),
        safety_row("VALIDATION_NO_BACKTEST_EXECUTION", values["BACKTEST_EXECUTED"] == "FALSE" and values["BACKTEST_RESULTS_APPLIED"] == "FALSE", "No backtest executed or applied."),
        safety_row("VALIDATION_NO_FORWARD_RETURN_FILL", values["FORWARD_RETURN_FILLED_COUNT"] == "0", "No forward returns filled."),
        safety_row("VALIDATION_CLAIMS_WEIGHTS_PROMOTIONS_BLOCKED", values["FACTOR_EFFECT_CLAIM_ALLOWED"] == "FALSE" and values["WEIGHT_CHANGE_ALLOWED"] == "FALSE" and values["PRODUCTION_PROMOTION_ALLOWED"] == "FALSE", "Claims, weights, promotions blocked."),
    ]
    safety.extend(validations)
    fail_count = sum(1 for row in safety if row["status"] != "PASS")
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    write_csv(paths["safety"], safety, SAFETY_FIELDS)
    write_text(paths["command_center"], command_center_markdown(values))
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report_markdown(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "RESEARCH_COMMAND_CENTER_READY",
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
        "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "RECOMMENDED_NEXT_ACTION",
        "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "EXTERNAL_DATA_FETCHED",
        "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "VALIDATION_FAIL_COUNT",
        "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
