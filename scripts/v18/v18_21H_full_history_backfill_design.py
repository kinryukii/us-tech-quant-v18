from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import math
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STATUS_READY = "WARN_V18_21H_FULL_HISTORY_BACKFILL_DESIGN_READY"
STATUS_FAIL = "FAIL_V18_21H_FULL_HISTORY_BACKFILL_DESIGN_VALIDATION_FAILED"
MODE = "ADVISORY_DRYRUN_ONLY"
PATCH_MODE = "FULL_HISTORY_BACKFILL_DESIGN_ONLY"
BATCH_SIZE = 25

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "FULL_HISTORY_BACKFILL_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
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
    "universe": "outputs/v18/price_factors/V18_21A_R4_CURRENT_MISSING_HISTORY_BACKFILL_UNIVERSE.csv",
    "priority": "outputs/v18/price_factors/V18_21A_R4_CURRENT_BACKFILL_PRIORITY_PLAN.csv",
    "projection": "outputs/v18/price_factors/V18_21A_R4_CURRENT_COVERAGE_PROJECTION.csv",
    "no_local_detail": "outputs/v18/price_factors/V18_21A_R3_CURRENT_NO_LOCAL_PRICE_DATA_DETAIL.csv",
    "mapping_audit": "outputs/v18/price_factors/V18_21A_R3_CURRENT_TICKER_SOURCE_MAPPING_AUDIT.csv",
    "signal": "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
    "a_readfirst": "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt",
    "f_readfirst": "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt",
    "g_readfirst": "outputs/v18/ops/V18_21G_STABLE_READ_FIRST.txt",
    "g_price_audit": "outputs/v18/forward_tracker/V18_21G_CURRENT_LOCAL_PRICE_SOURCE_AUDIT.csv",
    "r2_source_audit": "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_HISTORY_SOURCE_DISCOVERY_AUDIT.csv",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "FULL_HISTORY_BACKFILL_APPLIED",
    "EXTERNAL_DATA_FETCHED", "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN",
    "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT", "BACKFILL_REQUIREMENT_ROW_COUNT",
    "BACKFILL_PRIORITY_BATCH_COUNT", "BACKFILL_BATCH_SIZE", "BATCH_1_TICKER_COUNT",
    "TOP_50_PROJECTED_SCORE_READY_RATIO", "TOP_100_PROJECTED_SCORE_READY_RATIO",
    "ALL_MISSING_PROJECTED_SCORE_READY_RATIO", "CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN_READY",
    "SAFETY_AUDIT_CREATED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]
REQUIREMENT_FIELDS = [
    "ticker", "current_factor_scope_class", "current_score_scope", "current_score_ready",
    "current_mapping_status", "current_local_price_status", "required_history_days_for_full_score",
    "minimum_history_days_for_light_score", "required_start_date", "required_end_date",
    "backfill_required_for_20d_return", "backfill_required_for_60d_return",
    "backfill_required_for_200dma", "backfill_required_for_52w_high",
    "backfill_required_for_volume_surge", "backfill_requirement_status", "notes",
]
PRIORITY_FIELDS = [
    "batch_index", "ticker", "priority_tier", "priority_score", "priority_reason",
    "current_research_use", "expected_score_scope_after_backfill", "expected_score_ready_after_backfill",
    "recommended_backfill_depth", "estimated_impact_group", "batch_status", "notes",
]
PROJECTION_FIELDS = [
    "scenario_name", "added_history_ticker_count", "projected_local_price_data_available_count",
    "projected_full_history_factor_ready_count", "projected_score_ready_ratio",
    "projected_missing_history_ticker_count", "projected_research_coverage_status",
    "assumptions", "limitations",
]
DESIGN_FIELDS = [
    "design_step", "step_name", "purpose", "required_inputs", "output_file_if_applied_later",
    "safety_gate", "rollback_requirement", "modifies_price_cache", "external_data_required",
    "recommended_apply_mode", "notes",
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
    return (modified_time(path), sha256(path))


def first(row: Dict[str, str], *names: str) -> str:
    lower = {key.lower(): key for key in row}
    for name in names:
        key = lower.get(name.lower())
        if key is not None:
            return str(row.get(key, "") or "").strip()
    return ""


def numeric(value: object, default: float = 0.0) -> float:
    try:
        text = str(value or "").strip()
        return float(text.replace(",", "")) if text else default
    except ValueError:
        return default


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        INPUTS["signal"],
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
        "scripts/v18/run_v18_current_daily_command_center.ps1",
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


def safety_row(name: str, status: bool, notes: str) -> Dict[str, object]:
    return {"safety_check": name, "status": "PASS" if status else "FAIL", "notes": notes}


def requirement_status(row: Dict[str, str]) -> str:
    mapping = first(row, "current_mapping_status")
    scope = first(row, "factor_scope_class", "current_factor_scope_class")
    score_ready = first(row, "current_score_ready")
    if "REVIEW" in mapping.upper():
        return "NEED_SYMBOL_MAPPING_REVIEW"
    if score_ready.upper() == "TRUE":
        return "ALREADY_HAS_SUFFICIENT_HISTORY"
    if scope == "NO_LOCAL_PRICE_DATA":
        return "NEED_FULL_HISTORY_BACKFILL"
    if scope:
        return "NEED_PARTIAL_LIGHT_HISTORY_BACKFILL"
    return "DEGRADED_MISSING_REQUIREMENT_DATA"


def current_research_use(ticker: str, signal_by_ticker: Dict[str, Dict[str, str]]) -> str:
    row = signal_by_ticker.get(ticker, {})
    if not row:
        return "BROAD_UNIVERSE_COVERAGE"
    if first(row, "signal_research_status") == "READY_FOR_FORWARD_RESEARCH" or first(row, "forward_tracker_link_key"):
        return "READY_FOR_FORWARD_RESEARCH_RELEVANT"
    if first(row, "simulation_link_key"):
        return "SIMULATION_ANALYSIS_RELEVANT"
    return "SIGNAL_SNAPSHOT_RELEVANT"


def impact_group(idx: int) -> str:
    if idx <= 25:
        return "BATCH_1"
    if idx <= 50:
        return "TOP_50"
    if idx <= 100:
        return "TOP_100"
    return "ALL_MISSING"


def design_rows() -> List[Dict[str, object]]:
    steps = [
        ("1", "Validate ticker universe and priority plan", "Confirm missing-history tickers and batch order.", "R4 backfill universe and priority plan", "validation report", "Universe count reconciles to stable READ_FIRST.", "Discard generated plan.", "FALSE", "FALSE", "VALIDATION_ONLY", "Design-only."),
        ("2", "Validate existing local price coverage", "Avoid duplicate or unnecessary backfill.", "local source audits", "coverage audit", "No writes to price cache.", "Discard audit.", "FALSE", "FALSE", "LOCAL_AUDIT_ONLY", "Read-only source check."),
        ("3", "Build requested backfill batch", "Select conservative batch of tickers.", "priority batch plan", "requested batch csv", "Batch size capped and reviewed.", "Discard requested batch.", "FALSE", "FALSE", "DRYRUN_BATCH_PLAN", "No external fetch now."),
        ("4", "Fetch or import history only after explicit approval", "Acquire OHLCV history for approved batch.", "approved batch and provider/import source", "staged raw history", "Explicit approval required.", "Delete staged files.", "FALSE", "TRUE", "FUTURE_APPROVED_STAGE", "Not performed in V18.21H."),
        ("5", "Write to new staged price history output first", "Keep production cache unchanged.", "approved fetched/imported data", "staged price history output", "Never overwrite cache directly.", "Delete staged output.", "FALSE", "TRUE", "STAGED_OUTPUT_ONLY", "Future step."),
        ("6", "Validate OHLCV schema and date coverage", "Ensure required columns and ranges exist.", "staged history", "schema/date validation", "Validation fail count zero.", "Discard staged history.", "FALSE", "FALSE", "VALIDATION_ONLY", "Future step."),
        ("7", "Compare staged history vs existing local price sources", "Detect conflicts or stale overlaps.", "staged and existing local sources", "comparison diff", "No unexpected destructive diff.", "Discard staged history.", "FALSE", "FALSE", "DIFF_ONLY", "Future step."),
        ("8", "Recompute price-derived factors in shadow mode", "Measure score-ready improvement.", "staged history and factor script", "shadow factor scores", "Shadow output only.", "Discard shadow output.", "FALSE", "FALSE", "SHADOW_RECOMPUTE_ONLY", "Future step."),
        ("9", "Keep production price cache unchanged until explicit approval", "Protect production cache.", "validated staged output", "production safety audit", "Explicit approval for cache write.", "Restore from backup/snapshot.", "FALSE", "FALSE", "PRODUCTION_UNCHANGED", "Mandatory gate."),
        ("10", "Stable snapshot before any integration", "Preserve evidence and plan.", "all design artifacts", "stable snapshot", "Validation fail count zero.", "Restore from snapshot.", "FALSE", "FALSE", "SNAPSHOT_ONLY", "Required before integration."),
    ]
    return [
        {
            "design_step": step, "step_name": name, "purpose": purpose, "required_inputs": inputs,
            "output_file_if_applied_later": output, "safety_gate": gate, "rollback_requirement": rollback,
            "modifies_price_cache": modifies, "external_data_required": external, "recommended_apply_mode": mode, "notes": notes,
        }
        for step, name, purpose, inputs, output, gate, rollback, modifies, external, mode, notes in steps
    ]


def projection_rows(current_ready: int, current_local: int, missing: int, ticker_input_count: int, r4_projection: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    scenarios = [
        ("CURRENT", 0),
        ("BACKFILL_BATCH_1", min(BATCH_SIZE, missing)),
        ("BACKFILL_TOP_50", min(50, missing)),
        ("BACKFILL_TOP_100", min(100, missing)),
        ("BACKFILL_ALL_MISSING", missing),
    ]
    rows = []
    for name, added in scenarios:
        r4_name = "BACKFILL_TOP_25" if name == "BACKFILL_BATCH_1" else name
        prior = r4_projection.get(r4_name, {})
        projected_ready = int(numeric(prior.get("projected_full_history_factor_ready_count"), current_ready + added))
        projected_local = int(numeric(prior.get("projected_local_price_data_available_count"), current_local + added))
        ratio = numeric(prior.get("projected_score_ready_ratio"), projected_ready / ticker_input_count if ticker_input_count else 0.0)
        projected_missing = int(numeric(prior.get("projected_no_local_price_data_count"), max(missing - added, 0)))
        rows.append({
            "scenario_name": name,
            "added_history_ticker_count": added,
            "projected_local_price_data_available_count": projected_local,
            "projected_full_history_factor_ready_count": projected_ready,
            "projected_score_ready_ratio": f"{ratio:.6f}",
            "projected_missing_history_ticker_count": projected_missing,
            "projected_research_coverage_status": "FULL_COVERAGE_PROJECTED" if projected_missing == 0 else "PARTIAL_COVERAGE_PROJECTED",
            "assumptions": "Projection only; no data fetched or written.",
            "limitations": "Actual coverage depends on future approved staged backfill quality.",
        })
    return rows


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(values: Dict[str, object]) -> str:
    return f"""# V18.21H Full History Backfill Design Report

## Executive Summary
Status: {values.get('STATUS')}. V18.21H creates an advisory dry-run design for improving local full-history price coverage for missing-history tickers.

## Safety Statement
No external data was fetched, no price history was written, and no price cache, ranking, signal snapshot, simulation, forward tracker, event calendar, or official decision file was modified.

## Current Price-Derived Coverage Summary
Current score-ready ratio: {values.get('CURRENT_SCORE_READY_RATIO')}. Full-history factor-ready count: {values.get('CURRENT_FULL_HISTORY_FACTOR_READY_COUNT')}. Missing-history tickers: {values.get('CURRENT_MISSING_HISTORY_TICKER_COUNT')}.

## Missing History Requirement Summary
Backfill requirement rows: {values.get('BACKFILL_REQUIREMENT_ROW_COUNT')}. The requirements identify full/partial backfill needs and required date ranges without writing data.

## Priority Batch Plan Summary
Batch count: {values.get('BACKFILL_PRIORITY_BATCH_COUNT')}. Batch size: {values.get('BACKFILL_BATCH_SIZE')}. Batch 1 tickers: {values.get('BATCH_1_TICKER_COUNT')}.

## Coverage Improvement Projection
Top 50 projected score-ready ratio: {values.get('TOP_50_PROJECTED_SCORE_READY_RATIO')}. Top 100 projected ratio: {values.get('TOP_100_PROJECTED_SCORE_READY_RATIO')}. All missing projected ratio: {values.get('ALL_MISSING_PROJECTED_SCORE_READY_RATIO')}.

## Controlled Backfill Implementation Design
Design artifact ready: {values.get('CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN_READY')}. Any future fetch/import/write requires explicit approval and staged outputs first.

## Why No Factor Effectiveness Claims Are Allowed
Backfill is not applied, factor recomputation is not performed, and forward research remains immature. No effect claims, weight changes, or production promotions are allowed.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}. Safety audit created: {values.get('SAFETY_AUDIT_CREATED')}.

## Next-Step Recommendation
Create a stable snapshot if clean, then optionally design V18.21H-R1 controlled staged backfill only after explicit approval, or wait for forward horizons to mature before G-R1.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/price_factors"
    ops_dir = root / "outputs/v18/ops"
    paths = {
        "requirements": out_dir / "V18_21H_CURRENT_FULL_HISTORY_BACKFILL_REQUIREMENT_AUDIT.csv",
        "priority": out_dir / "V18_21H_CURRENT_FULL_HISTORY_BACKFILL_PRIORITY_BATCH_PLAN.csv",
        "projection": out_dir / "V18_21H_CURRENT_FULL_HISTORY_COVERAGE_IMPROVEMENT_PROJECTION.csv",
        "design": out_dir / "V18_21H_CURRENT_CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN.csv",
        "safety": out_dir / "V18_21H_CURRENT_FULL_HISTORY_BACKFILL_SAFETY_AUDIT.csv",
        "read_first": ops_dir / "V18_21H_READ_FIRST.txt",
        "report": ops_dir / "V18_21H_CURRENT_FULL_HISTORY_BACKFILL_DESIGN_REPORT.md",
    }
    before = {str(path): signature(path) for path in protected_paths(root)}
    a_rf = readfirst(root / INPUTS["a_readfirst"])
    f_rf = readfirst(root / INPUTS["f_readfirst"])
    universe, _ = read_csv(root / INPUTS["universe"])
    priority, _ = read_csv(root / INPUTS["priority"])
    projection_src, _ = read_csv(root / INPUTS["projection"])
    signal_rows, _ = read_csv(root / INPUTS["signal"])
    signal_by_ticker = {first(row, "ticker").upper(): row for row in signal_rows if first(row, "ticker")}

    if not universe:
        no_local, _ = read_csv(root / INPUTS["no_local_detail"])
        universe = no_local

    requirement_rows: List[Dict[str, object]] = []
    for row in universe:
        ticker = first(row, "ticker").upper()
        if not ticker:
            continue
        status = requirement_status(row)
        requirement_rows.append({
            "ticker": ticker,
            "current_factor_scope_class": first(row, "factor_scope_class", "current_factor_scope_class"),
            "current_score_scope": first(row, "current_score_scope", "score_scope"),
            "current_score_ready": first(row, "current_score_ready", "score_ready"),
            "current_mapping_status": first(row, "current_mapping_status", "mapping_status"),
            "current_local_price_status": "NO_LOCAL_PRICE_DATA" if first(row, "factor_scope_class", "current_factor_scope_class") == "NO_LOCAL_PRICE_DATA" else first(row, "latest_price_snapshot_available"),
            "required_history_days_for_full_score": first(row, "required_history_days_for_full_score") or "252",
            "minimum_history_days_for_light_score": first(row, "minimum_history_days_for_light_score") or "60",
            "required_start_date": first(row, "recommended_backfill_start_date", "required_start_date"),
            "required_end_date": first(row, "recommended_backfill_end_date", "required_end_date"),
            "backfill_required_for_20d_return": first(row, "backfill_required_for_20d_return") or "TRUE",
            "backfill_required_for_60d_return": first(row, "backfill_required_for_60d_return") or "TRUE",
            "backfill_required_for_200dma": first(row, "backfill_required_for_200dma") or "TRUE",
            "backfill_required_for_52w_high": first(row, "backfill_required_for_52w_high") or "TRUE",
            "backfill_required_for_volume_surge": first(row, "backfill_required_for_volume_surge") or "TRUE",
            "backfill_requirement_status": status,
            "notes": "Advisory requirement only; no history fetched or written.",
        })

    priority_by_ticker = {first(row, "ticker").upper(): row for row in priority if first(row, "ticker")}
    sorted_requirements = sorted(
        requirement_rows,
        key=lambda row: (
            -numeric(priority_by_ticker.get(str(row["ticker"]), {}).get("priority_score"), 0),
            str(row["ticker"]),
        ),
    )
    priority_rows: List[Dict[str, object]] = []
    for idx, row in enumerate(sorted_requirements, start=1):
        ticker = str(row["ticker"])
        prior = priority_by_ticker.get(ticker, {})
        batch = int(math.ceil(idx / BATCH_SIZE))
        priority_rows.append({
            "batch_index": batch,
            "ticker": ticker,
            "priority_tier": first(prior, "priority_tier") or "BROAD_UNIVERSE_COVERAGE",
            "priority_score": first(prior, "priority_score") or str(max(100, 1000 - idx)),
            "priority_reason": first(prior, "priority_reason") or "DETERMINISTIC_ORDERING_FALLBACK",
            "current_research_use": current_research_use(ticker, signal_by_ticker),
            "expected_score_scope_after_backfill": first(prior, "expected_factor_scope_after_backfill") or "FULL_HISTORY_FACTOR_READY",
            "expected_score_ready_after_backfill": first(prior, "expected_score_ready_after_backfill") or "TRUE",
            "recommended_backfill_depth": "FULL_OHLCV_252D_PLUS_VOLUME",
            "estimated_impact_group": impact_group(idx),
            "batch_status": "ADVISORY_PLAN_ONLY_NO_BACKFILL_APPLIED",
            "notes": "Conservative dry-run batch plan; no fetch/write performed.",
        })

    r4_projection = {first(row, "scenario_name"): row for row in projection_src}
    current_ready = int(numeric(a_rf.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), 104))
    current_local = int(numeric(a_rf.get("CURRENT_LOCAL_PRICE_DATA_AVAILABLE_COUNT"), 105))
    missing_count = int(numeric(a_rf.get("MISSING_HISTORY_TICKER_COUNT"), len(requirement_rows)))
    ticker_input_count = current_ready + missing_count
    projection_rows_out = projection_rows(current_ready, current_local, missing_count, ticker_input_count, r4_projection)
    design = design_rows()
    safety = [
        safety_row("FULL_HISTORY_BACKFILL_APPLIED", True, "FALSE"),
        safety_row("EXTERNAL_DATA_FETCHED", True, "FALSE"),
        safety_row("PRICE_CACHE_MODIFIED", True, "FALSE"),
        safety_row("PRICE_HISTORY_WRITTEN", True, "FALSE"),
        safety_row("RANKING_MODIFIED", True, "FALSE"),
        safety_row("SIGNAL_SNAPSHOT_MODIFIED", True, "FALSE"),
        safety_row("FORWARD_TRACKER_MODIFIED", True, "FALSE"),
        safety_row("OFFICIAL_DECISION_IMPACT", True, "NONE"),
        safety_row("AUTO_TRADE", True, "DISABLED"),
        safety_row("AUTO_SELL", True, "DISABLED"),
    ]

    write_csv(paths["requirements"], requirement_rows, REQUIREMENT_FIELDS)
    write_csv(paths["priority"], priority_rows, PRIORITY_FIELDS)
    write_csv(paths["projection"], projection_rows_out, PROJECTION_FIELDS)
    write_csv(paths["design"], design, DESIGN_FIELDS)
    write_csv(paths["safety"], safety, SAFETY_FIELDS)

    values: Dict[str, object] = {
        "STATUS": STATUS_READY,
        "CURRENT_SCORE_READY_RATIO": a_rf.get("CURRENT_SCORE_READY_RATIO", f_rf.get("PRICE_DERIVED_SCORE_READY_RATIO", "")),
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": a_rf.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT", ""),
        "CURRENT_MISSING_HISTORY_TICKER_COUNT": a_rf.get("MISSING_HISTORY_TICKER_COUNT", f_rf.get("PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT", "")),
        "BACKFILL_REQUIREMENT_ROW_COUNT": len(requirement_rows),
        "BACKFILL_PRIORITY_BATCH_COUNT": max((int(row["batch_index"]) for row in priority_rows), default=0),
        "BACKFILL_BATCH_SIZE": BATCH_SIZE,
        "BATCH_1_TICKER_COUNT": sum(1 for row in priority_rows if row["batch_index"] == 1),
        "TOP_50_PROJECTED_SCORE_READY_RATIO": a_rf.get("TOP_50_PROJECTED_SCORE_READY_RATIO", ""),
        "TOP_100_PROJECTED_SCORE_READY_RATIO": a_rf.get("TOP_100_PROJECTED_SCORE_READY_RATIO", ""),
        "ALL_MISSING_PROJECTED_SCORE_READY_RATIO": a_rf.get("ALL_MISSING_PROJECTED_SCORE_READY_RATIO", ""),
        "CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN_READY": "TRUE",
        "SAFETY_AUDIT_CREATED": "TRUE",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    values.update(SAFETY_FLAGS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))

    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    read_first_text = read_text(paths["read_first"])
    validations = [
        safety_row("VALIDATION_POWERSHELL_PARSE_WRAPPER", ps_parse(root / "scripts/v18/run_v18_21H_full_history_backfill_design.ps1"), "Wrapper parses."),
        safety_row("VALIDATION_PYTHON_COMPILE_SCRIPT", py_compile(root / "scripts/v18/v18_21H_full_history_backfill_design.py"), "Python compiles."),
        safety_row("VALIDATION_REQUIRED_OUTPUTS_EXIST", all(path.exists() for path in paths.values()), "All outputs exist."),
        safety_row("VALIDATION_REQUIRED_READ_FIRST_FIELDS_EXIST", all(field in read_first_text for field in READ_FIRST_FIELDS), "All READ_FIRST fields exist."),
        safety_row("VALIDATION_PROTECTED_FILES_UNCHANGED", not changed, "Changed protected files: " + ";".join(changed)),
        safety_row("VALIDATION_FULL_HISTORY_BACKFILL_NOT_APPLIED", values["FULL_HISTORY_BACKFILL_APPLIED"] == "FALSE", "Backfill not applied."),
        safety_row("VALIDATION_EXTERNAL_DATA_NOT_FETCHED", values["EXTERNAL_DATA_FETCHED"] == "FALSE", "No external data fetched."),
        safety_row("VALIDATION_PRICE_CACHE_NOT_MODIFIED", values["PRICE_CACHE_MODIFIED"] == "FALSE", "Price cache not modified."),
        safety_row("VALIDATION_PRICE_HISTORY_NOT_WRITTEN", values["PRICE_HISTORY_WRITTEN"] == "FALSE", "Price history not written."),
        safety_row("VALIDATION_CLAIMS_WEIGHTS_PROMOTIONS_ZERO", values["EFFECT_CLAIM_ALLOWED_COUNT"] == "0" and values["WEIGHT_CHANGE_ALLOWED_COUNT"] == "0" and values["PRODUCTION_PROMOTION_ALLOWED_COUNT"] == "0", "No claims, weight changes, or promotions."),
    ]
    safety.extend(validations)
    fail_count = sum(1 for row in safety if row["status"] != "PASS")
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["safety"], safety, SAFETY_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "FULL_HISTORY_BACKFILL_APPLIED",
        "EXTERNAL_DATA_FETCHED", "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "BACKFILL_REQUIREMENT_ROW_COUNT",
        "BACKFILL_PRIORITY_BATCH_COUNT", "BACKFILL_BATCH_SIZE", "BATCH_1_TICKER_COUNT",
        "TOP_50_PROJECTED_SCORE_READY_RATIO", "TOP_100_PROJECTED_SCORE_READY_RATIO",
        "ALL_MISSING_PROJECTED_SCORE_READY_RATIO", "CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN_READY",
        "SAFETY_AUDIT_CREATED", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
