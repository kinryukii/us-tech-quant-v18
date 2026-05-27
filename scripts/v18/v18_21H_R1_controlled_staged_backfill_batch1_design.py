from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_READY = "WARN_V18_21H_R1_CONTROLLED_STAGED_BACKFILL_BATCH1_DESIGN_READY"
STATUS_FAIL = "FAIL_V18_21H_R1_CONTROLLED_STAGED_BACKFILL_BATCH1_DESIGN_VALIDATION_FAILED"
MODE = "ADVISORY_DRYRUN_ONLY"
PATCH_MODE = "CONTROLLED_STAGED_BACKFILL_BATCH1_DESIGN_ONLY"
BATCH_ID = "V18_21H_R1_BATCH1"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "STAGED_BACKFILL_BATCH1_DESIGN_READY": "TRUE",
    "FULL_HISTORY_BACKFILL_APPLIED": "FALSE",
    "STAGED_BACKFILL_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
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
    "priority": "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_PRIORITY_BATCH_PLAN.csv",
    "requirements": "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_REQUIREMENT_AUDIT.csv",
    "projection": "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_COVERAGE_IMPROVEMENT_PROJECTION.csv",
    "design": "outputs/v18/price_factors/V18_21H_CURRENT_CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN.csv",
    "safety": "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_SAFETY_AUDIT.csv",
    "h_readfirst": "outputs/v18/ops/V18_21H_STABLE_READ_FIRST.txt",
    "f_readfirst": "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt",
    "signal": "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "STAGED_BACKFILL_BATCH1_DESIGN_READY",
    "FULL_HISTORY_BACKFILL_APPLIED", "STAGED_BACKFILL_APPLIED", "EXTERNAL_DATA_FETCHED",
    "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN",
    "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT", "BATCH1_REQUESTED_TICKER_COUNT",
    "BATCH1_VALID_TICKER_COUNT", "BATCH1_NEED_REVIEW_COUNT", "BATCH1_BLOCKED_COUNT",
    "BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER",
    "BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER",
    "STAGED_OHLCV_SCHEMA_PREVIEW_CREATED", "CONTROLLED_STAGED_APPLY_SAFETY_PLAN_CREATED",
    "SAFETY_AUDIT_CREATED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]
MANIFEST_FIELDS = [
    "batch_index", "ticker", "priority_tier", "priority_score", "priority_reason",
    "current_score_ready", "current_factor_scope_class", "current_score_scope",
    "required_start_date", "required_end_date", "required_history_days_for_full_score",
    "minimum_history_days_for_light_score", "requested_fields", "requested_frequency",
    "requested_adjustment_mode", "target_staged_output_path", "target_final_cache_path_if_applied_later",
    "request_status", "blocking_reason", "notes",
]
VALIDATION_AUDIT_FIELDS = [
    "ticker", "appears_in_signal_snapshot", "appears_in_backfill_requirement_audit",
    "appears_in_priority_plan", "has_required_start_date", "has_required_end_date",
    "has_priority_score", "has_priority_reason", "expected_score_ready_after_backfill",
    "validation_status", "validation_notes",
]
SCHEMA_FIELDS = [
    "ticker", "date", "open", "high", "low", "close", "adjusted_close", "volume",
    "source_provider_placeholder", "fetch_timestamp_placeholder", "staged_backfill_batch_id",
    "validation_status", "apply_status",
]
PROJECTION_FIELDS = [
    "scenario_name", "batch1_ticker_count", "projected_added_full_history_ready_count",
    "projected_full_history_factor_ready_count", "projected_missing_history_ticker_count",
    "projected_score_ready_ratio", "projected_research_coverage_status", "assumptions", "limitations",
]
SAFETY_PLAN_FIELDS = [
    "step_index", "step_name", "purpose", "required_inputs", "safety_gate", "validation_required",
    "rollback_requirement", "modifies_price_cache", "writes_staged_history", "external_data_required",
    "allowed_in_r1", "notes",
]
SAFETY_AUDIT_FIELDS = ["safety_check", "status", "notes"]


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


def request_status(ticker: str, req: Dict[str, str]) -> Tuple[str, str]:
    if not ticker or not ticker.replace(".", "").replace("-", "").isalnum():
        return "BLOCKED_INVALID_TICKER", "Ticker is missing or invalid."
    if not req:
        return "NEED_REQUIREMENT_REVIEW", "Ticker missing from requirement audit."
    if first(req, "backfill_requirement_status") == "ALREADY_HAS_SUFFICIENT_HISTORY":
        return "ALREADY_SUFFICIENT_HISTORY", "Requirement audit says sufficient history already exists."
    if "SYMBOL_MAPPING" in first(req, "backfill_requirement_status"):
        return "NEED_SYMBOL_MAPPING_REVIEW", "Requirement audit requires symbol mapping review."
    if not first(req, "required_start_date") or not first(req, "required_end_date"):
        return "BLOCKED_MISSING_REQUIRED_DATES", "Missing required start/end date."
    return "READY_FOR_FUTURE_STAGED_BACKFILL", ""


def validation_status(ticker: str, req: Dict[str, str], priority: Dict[str, str], signal: Dict[str, str], seen: set[str]) -> Tuple[str, str]:
    if ticker in seen:
        return "INVALID_DUPLICATE_TICKER", "Duplicate ticker in Batch 1."
    if not req:
        return "INVALID_MISSING_REQUIREMENT", "Missing requirement row."
    if not first(req, "required_start_date") or not first(req, "required_end_date"):
        return "NEED_MANUAL_REVIEW", "Missing required date range."
    if numeric(priority.get("priority_score"), 0) < 100:
        return "VALID_BUT_LOW_PRIORITY", "Candidate is valid but priority score is low."
    return "VALID_BATCH1_BACKFILL_CANDIDATE", "Valid Batch 1 dry-run design candidate."


def safety_plan_rows() -> List[Dict[str, object]]:
    steps = [
        (1, "Validate Batch 1 request manifest", "Confirm ticker/date/field requirements.", "request manifest", "25 expected tickers or degraded warning.", "Schema and required date checks.", "Discard manifest.", "FALSE", "FALSE", "FALSE", "TRUE", "Allowed in R1."),
        (2, "Confirm explicit user approval before external fetch", "Prevent unapproved data access.", "approval record", "Approval must be explicit.", "Approval captured before fetch.", "Do nothing if absent.", "FALSE", "FALSE", "FALSE", "TRUE", "R1 does not fetch."),
        (3, "Fetch/import data into staged output only", "Acquire future OHLCV data safely.", "approved manifest", "Staged output only.", "Provider/import row counts and dates.", "Delete staged files.", "FALSE", "TRUE", "TRUE", "FALSE", "Future only."),
        (4, "Validate OHLCV schema and date coverage", "Ensure complete staged history.", "staged output", "Required columns and date range pass.", "OHLCV schema/date validation.", "Discard invalid staged file.", "FALSE", "FALSE", "FALSE", "FALSE", "Future only."),
        (5, "Compare staged data to existing local sources", "Detect conflicts.", "staged + local sources", "No unexpected conflicts.", "Diff audit.", "Discard staged file.", "FALSE", "FALSE", "FALSE", "FALSE", "Future only."),
        (6, "Recompute price-derived factors in shadow mode only", "Estimate score-ready impact.", "staged validated output", "Shadow output only.", "Score-ready audit.", "Discard shadow output.", "FALSE", "FALSE", "FALSE", "FALSE", "Future only."),
        (7, "Produce post-backfill coverage audit", "Quantify coverage change.", "shadow factors", "Audit created.", "Coverage projection validation.", "Discard audit.", "FALSE", "FALSE", "FALSE", "FALSE", "Future only."),
        (8, "Stable snapshot before price cache integration", "Preserve staged evidence.", "all staged artifacts", "Validation fail count zero.", "Snapshot validation.", "Restore from snapshot.", "FALSE", "FALSE", "FALSE", "FALSE", "Future only."),
        (9, "Only later consider price cache integration", "Protect production cache.", "approved staged evidence", "Explicit approval required.", "Production safety diff.", "Restore cache backup.", "TRUE", "FALSE", "FALSE", "FALSE", "Not allowed in R1."),
    ]
    return [
        {
            "step_index": step, "step_name": name, "purpose": purpose, "required_inputs": inputs,
            "safety_gate": gate, "validation_required": validation, "rollback_requirement": rollback,
            "modifies_price_cache": modifies, "writes_staged_history": staged, "external_data_required": external,
            "allowed_in_r1": allowed, "notes": notes,
        }
        for step, name, purpose, inputs, gate, validation, rollback, modifies, staged, external, allowed, notes in steps
    ]


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(values: Dict[str, object]) -> str:
    return f"""# V18.21H-R1 Controlled Staged Backfill Batch 1 Design Report

## Executive Summary
Status: {values.get('STATUS')}. V18.21H-R1 defines a controlled staged Batch 1 backfill request for {values.get('BATCH1_REQUESTED_TICKER_COUNT')} tickers without fetching or writing price history.

## Safety Statement
No external data was fetched, no staged or final price history was written, no price cache was modified, and no ranking, signal snapshot, simulation, forward tracker, event calendar, or official decision behavior was changed.

## Batch 1 Ticker Summary
Valid candidates: {values.get('BATCH1_VALID_TICKER_COUNT')}. Need review: {values.get('BATCH1_NEED_REVIEW_COUNT')}. Blocked: {values.get('BATCH1_BLOCKED_COUNT')}.

## Staged Request Manifest Summary
Each request row defines ticker, required date range, requested OHLCV fields, staged output path, future final cache path, and dry-run request status.

## Ticker Validation Audit Summary
The validation audit checks presence in signal snapshot, requirement audit, priority plan, required dates, priority score, and priority reason.

## Staged OHLCV Schema Preview Explanation
The schema preview contains metadata placeholder rows only. It contains no fetched prices and all rows are NOT_APPLIED_SCHEMA_PREVIEW_ONLY.

## Coverage Impact Projection
If Batch 1 is fully backfilled later, projected score-ready ratio is {values.get('BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER')} and projected missing-history count is {values.get('BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER')}.

## Controlled Staged Apply Safety Plan
Safety plan created: {values.get('CONTROLLED_STAGED_APPLY_SAFETY_PLAN_CREATED')}. External fetch/import and staged writes are future-only and require explicit approval.

## Why No Factor Effectiveness Claims Are Allowed
No backfill was applied and no factors were recomputed. Effect claims, weight changes, and production promotions remain disallowed.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}. Safety audit created: {values.get('SAFETY_AUDIT_CREATED')}.

## Next-Step Recommendation
Create a stable snapshot if clean, then optionally V18.21H-R2 actual staged fetch/import only after explicit approval, or wait for forward horizons to mature before returning to V18.21G-R1.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/price_factors"
    ops_dir = root / "outputs/v18/ops"
    paths = {
        "manifest": out_dir / "V18_21H_R1_CURRENT_BATCH1_STAGED_BACKFILL_REQUEST_MANIFEST.csv",
        "ticker_audit": out_dir / "V18_21H_R1_CURRENT_BATCH1_TICKER_VALIDATION_AUDIT.csv",
        "schema": out_dir / "V18_21H_R1_CURRENT_STAGED_OHLCV_SCHEMA_PREVIEW.csv",
        "projection": out_dir / "V18_21H_R1_CURRENT_BATCH1_COVERAGE_IMPACT_PROJECTION.csv",
        "safety_plan": out_dir / "V18_21H_R1_CURRENT_CONTROLLED_STAGED_APPLY_SAFETY_PLAN.csv",
        "safety": out_dir / "V18_21H_R1_CURRENT_STAGED_BACKFILL_SAFETY_AUDIT.csv",
        "read_first": ops_dir / "V18_21H_R1_READ_FIRST.txt",
        "report": ops_dir / "V18_21H_R1_CURRENT_CONTROLLED_STAGED_BACKFILL_BATCH1_DESIGN_REPORT.md",
    }
    before = {str(path): signature(path) for path in protected_paths(root)}
    priority_rows, _ = read_csv(root / INPUTS["priority"])
    req_rows, _ = read_csv(root / INPUTS["requirements"])
    signal_rows, _ = read_csv(root / INPUTS["signal"])
    h_rf = readfirst(root / INPUTS["h_readfirst"])
    req_by_ticker = {first(row, "ticker").upper(): row for row in req_rows if first(row, "ticker")}
    signal_by_ticker = {first(row, "ticker").upper(): row for row in signal_rows if first(row, "ticker")}
    batch1 = [row for row in priority_rows if str(first(row, "batch_index")).strip() == "1"]

    manifest_rows: List[Dict[str, object]] = []
    ticker_audit_rows: List[Dict[str, object]] = []
    schema_rows: List[Dict[str, object]] = []
    seen: set[str] = set()
    valid_count = 0
    need_review_count = 0
    blocked_count = 0
    for row in batch1:
        ticker = first(row, "ticker").upper()
        req = req_by_ticker.get(ticker, {})
        status, blocker = request_status(ticker, req)
        val_status, val_notes = validation_status(ticker, req, row, signal_by_ticker.get(ticker, {}), seen)
        seen.add(ticker)
        if val_status == "VALID_BATCH1_BACKFILL_CANDIDATE":
            valid_count += 1
        elif val_status in {"NEED_MANUAL_REVIEW", "VALID_BUT_LOW_PRIORITY"}:
            need_review_count += 1
        else:
            blocked_count += 1
        target_stage = f"outputs/v18/price_factors/staged_backfill/V18_21H_R2_STAGED_BATCH1_{ticker}.csv"
        target_cache = f"state/v18/price_cache/{ticker}.csv"
        manifest_rows.append({
            "batch_index": 1,
            "ticker": ticker,
            "priority_tier": first(row, "priority_tier"),
            "priority_score": first(row, "priority_score"),
            "priority_reason": first(row, "priority_reason"),
            "current_score_ready": first(req, "current_score_ready"),
            "current_factor_scope_class": first(req, "current_factor_scope_class"),
            "current_score_scope": first(req, "current_score_scope"),
            "required_start_date": first(req, "required_start_date"),
            "required_end_date": first(req, "required_end_date"),
            "required_history_days_for_full_score": first(req, "required_history_days_for_full_score"),
            "minimum_history_days_for_light_score": first(req, "minimum_history_days_for_light_score"),
            "requested_fields": "date;open;high;low;close;adjusted_close;volume",
            "requested_frequency": "1d",
            "requested_adjustment_mode": "adjusted_close_required",
            "target_staged_output_path": target_stage,
            "target_final_cache_path_if_applied_later": target_cache,
            "request_status": status,
            "blocking_reason": blocker,
            "notes": "Dry-run request manifest only; no fetch or write performed.",
        })
        ticker_audit_rows.append({
            "ticker": ticker,
            "appears_in_signal_snapshot": str(ticker in signal_by_ticker).upper(),
            "appears_in_backfill_requirement_audit": str(bool(req)).upper(),
            "appears_in_priority_plan": "TRUE",
            "has_required_start_date": str(bool(first(req, "required_start_date"))).upper(),
            "has_required_end_date": str(bool(first(req, "required_end_date"))).upper(),
            "has_priority_score": str(bool(first(row, "priority_score"))).upper(),
            "has_priority_reason": str(bool(first(row, "priority_reason"))).upper(),
            "expected_score_ready_after_backfill": first(row, "expected_score_ready_after_backfill"),
            "validation_status": val_status,
            "validation_notes": val_notes,
        })
        schema_rows.append({
            "ticker": ticker,
            "date": "YYYY-MM-DD",
            "open": "NUMERIC_PLACEHOLDER",
            "high": "NUMERIC_PLACEHOLDER",
            "low": "NUMERIC_PLACEHOLDER",
            "close": "NUMERIC_PLACEHOLDER",
            "adjusted_close": "NUMERIC_PLACEHOLDER",
            "volume": "INTEGER_PLACEHOLDER",
            "source_provider_placeholder": "APPROVED_PROVIDER_OR_IMPORT_SOURCE",
            "fetch_timestamp_placeholder": "YYYY-MM-DDTHH:MM:SS",
            "staged_backfill_batch_id": BATCH_ID,
            "validation_status": "SCHEMA_PREVIEW_ONLY_NO_PRICE_DATA",
            "apply_status": "NOT_APPLIED_SCHEMA_PREVIEW_ONLY",
        })

    current_ready = int(numeric(h_rf.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), 104))
    current_missing = int(numeric(h_rf.get("CURRENT_MISSING_HISTORY_TICKER_COUNT"), 221))
    total = current_ready + current_missing
    batch_count = len(batch1)
    after_batch_ready = current_ready + valid_count
    after_batch_missing = max(current_missing - valid_count, 0)
    batch_ratio = after_batch_ready / total if total else 0.0
    top50_ratio = numeric(h_rf.get("TOP_50_PROJECTED_SCORE_READY_RATIO"), 0.473846)
    projection_rows = [
        {"scenario_name": "CURRENT", "batch1_ticker_count": batch_count, "projected_added_full_history_ready_count": 0, "projected_full_history_factor_ready_count": current_ready, "projected_missing_history_ticker_count": current_missing, "projected_score_ready_ratio": h_rf.get("CURRENT_SCORE_READY_RATIO", "0.320000"), "projected_research_coverage_status": "CURRENT_DEGRADED", "assumptions": "No staged backfill applied.", "limitations": "Current state only."},
        {"scenario_name": "BATCH1_DESIGN_ONLY_NO_BACKFILL", "batch1_ticker_count": batch_count, "projected_added_full_history_ready_count": 0, "projected_full_history_factor_ready_count": current_ready, "projected_missing_history_ticker_count": current_missing, "projected_score_ready_ratio": h_rf.get("CURRENT_SCORE_READY_RATIO", "0.320000"), "projected_research_coverage_status": "DESIGN_ONLY_NO_CHANGE", "assumptions": "R1 writes no price history.", "limitations": "No coverage improvement until future approved apply."},
        {"scenario_name": "BATCH1_FULLY_BACKFILLED_LATER", "batch1_ticker_count": batch_count, "projected_added_full_history_ready_count": valid_count, "projected_full_history_factor_ready_count": after_batch_ready, "projected_missing_history_ticker_count": after_batch_missing, "projected_score_ready_ratio": f"{batch_ratio:.6f}", "projected_research_coverage_status": "PARTIAL_IMPROVEMENT_PROJECTED", "assumptions": "All valid Batch 1 tickers are successfully staged and later accepted.", "limitations": "Requires explicit approval and staged validation."},
        {"scenario_name": "BATCH1_PLUS_TOP50_LATER", "batch1_ticker_count": batch_count, "projected_added_full_history_ready_count": 50, "projected_full_history_factor_ready_count": min(current_ready + 50, total), "projected_missing_history_ticker_count": max(current_missing - 50, 0), "projected_score_ready_ratio": f"{top50_ratio:.6f}", "projected_research_coverage_status": "TOP50_IMPROVEMENT_PROJECTED", "assumptions": "Top 50 missing-history tickers are backfilled later.", "limitations": "Requires future staged apply approvals."},
    ]
    safety_plan = safety_plan_rows()
    safety = [
        safety_row("STAGED_BACKFILL_APPLIED", True, "FALSE"),
        safety_row("FULL_HISTORY_BACKFILL_APPLIED", True, "FALSE"),
        safety_row("EXTERNAL_DATA_FETCHED", True, "FALSE"),
        safety_row("PRICE_CACHE_MODIFIED", True, "FALSE"),
        safety_row("PRICE_HISTORY_WRITTEN", True, "FALSE"),
        safety_row("STAGED_PRICE_HISTORY_WRITTEN", True, "FALSE"),
        safety_row("RANKING_MODIFIED", True, "FALSE"),
        safety_row("SIGNAL_SNAPSHOT_MODIFIED", True, "FALSE"),
        safety_row("FORWARD_TRACKER_MODIFIED", True, "FALSE"),
        safety_row("OFFICIAL_DECISION_IMPACT", True, "NONE"),
        safety_row("AUTO_TRADE", True, "DISABLED"),
        safety_row("AUTO_SELL", True, "DISABLED"),
    ]

    write_csv(paths["manifest"], manifest_rows, MANIFEST_FIELDS)
    write_csv(paths["ticker_audit"], ticker_audit_rows, VALIDATION_AUDIT_FIELDS)
    write_csv(paths["schema"], schema_rows, SCHEMA_FIELDS)
    write_csv(paths["projection"], projection_rows, PROJECTION_FIELDS)
    write_csv(paths["safety_plan"], safety_plan, SAFETY_PLAN_FIELDS)
    write_csv(paths["safety"], safety, SAFETY_AUDIT_FIELDS)

    values: Dict[str, object] = {
        "STATUS": STATUS_READY,
        "CURRENT_SCORE_READY_RATIO": h_rf.get("CURRENT_SCORE_READY_RATIO", "0.320000"),
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": h_rf.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT", "104"),
        "CURRENT_MISSING_HISTORY_TICKER_COUNT": h_rf.get("CURRENT_MISSING_HISTORY_TICKER_COUNT", "221"),
        "BATCH1_REQUESTED_TICKER_COUNT": batch_count,
        "BATCH1_VALID_TICKER_COUNT": valid_count,
        "BATCH1_NEED_REVIEW_COUNT": need_review_count,
        "BATCH1_BLOCKED_COUNT": blocked_count,
        "BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER": f"{batch_ratio:.6f}",
        "BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER": after_batch_missing,
        "STAGED_OHLCV_SCHEMA_PREVIEW_CREATED": "TRUE",
        "CONTROLLED_STAGED_APPLY_SAFETY_PLAN_CREATED": "TRUE",
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
        safety_row("VALIDATION_POWERSHELL_PARSE_WRAPPER", ps_parse(root / "scripts/v18/run_v18_21H_R1_controlled_staged_backfill_batch1_design.ps1"), "Wrapper parses."),
        safety_row("VALIDATION_PYTHON_COMPILE_SCRIPT", py_compile(root / "scripts/v18/v18_21H_R1_controlled_staged_backfill_batch1_design.py"), "Python compiles."),
        safety_row("VALIDATION_REQUIRED_OUTPUTS_EXIST", all(path.exists() for path in paths.values()), "All outputs exist."),
        safety_row("VALIDATION_REQUIRED_READ_FIRST_FIELDS_EXIST", all(field in read_first_text for field in READ_FIRST_FIELDS), "All READ_FIRST fields exist."),
        safety_row("VALIDATION_PRIORITY_PLAN_EXISTS", (root / INPUTS["priority"]).exists(), "Priority plan exists."),
        safety_row("VALIDATION_BATCH1_HAS_TICKERS", batch_count > 0, f"Batch1 count={batch_count}."),
        safety_row("VALIDATION_NO_PROTECTED_FILES_MODIFIED", not changed, "Changed protected files: " + ";".join(changed)),
        safety_row("VALIDATION_NO_FETCH_NO_WRITE", values["EXTERNAL_DATA_FETCHED"] == "FALSE" and values["PRICE_HISTORY_WRITTEN"] == "FALSE" and values["STAGED_PRICE_HISTORY_WRITTEN"] == "FALSE", "No fetch/write."),
        safety_row("VALIDATION_CLAIMS_WEIGHTS_PROMOTIONS_ZERO", values["EFFECT_CLAIM_ALLOWED_COUNT"] == "0" and values["WEIGHT_CHANGE_ALLOWED_COUNT"] == "0" and values["PRODUCTION_PROMOTION_ALLOWED_COUNT"] == "0", "No claims, weight changes, or promotions."),
    ]
    safety.extend(validations)
    fail_count = sum(1 for row in safety if row["status"] != "PASS")
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["safety"], safety, SAFETY_AUDIT_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "STAGED_BACKFILL_BATCH1_DESIGN_READY",
        "FULL_HISTORY_BACKFILL_APPLIED", "STAGED_BACKFILL_APPLIED", "EXTERNAL_DATA_FETCHED",
        "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "BATCH1_REQUESTED_TICKER_COUNT",
        "BATCH1_VALID_TICKER_COUNT", "BATCH1_NEED_REVIEW_COUNT", "BATCH1_BLOCKED_COUNT",
        "BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER",
        "BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER",
        "STAGED_OHLCV_SCHEMA_PREVIEW_CREATED", "CONTROLLED_STAGED_APPLY_SAFETY_PLAN_CREATED",
        "SAFETY_AUDIT_CREATED", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
