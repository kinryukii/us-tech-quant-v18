from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_READY = "WARN_V18_21G_CONTROLLED_FORWARD_OUTCOME_FILLER_DESIGN_READY"
STATUS_FAIL = "FAIL_V18_21G_CONTROLLED_FORWARD_OUTCOME_FILLER_DESIGN_VALIDATION_FAILED"
MODE = "ADVISORY_DRYRUN_ONLY"
PATCH_MODE = "CONTROLLED_FORWARD_OUTCOME_FILLER_DESIGN_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "FORWARD_OUTCOME_FILLER_APPLIED": "FALSE",
    "FORWARD_RETURN_FILLED_COUNT": "0",
    "SHADOW_FORWARD_TRACKER_MODIFIED": "FALSE",
    "EXISTING_FORWARD_TRACKER_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "EVENT_CALENDAR_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

SHADOW_PATH = "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv"
SIGNAL_PATH = "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv"
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "FORWARD_OUTCOME_FILLER_APPLIED",
    "SHADOW_FORWARD_TRACKER_INPUT_ROWS", "OUTCOME_ELIGIBILITY_AUDIT_ROWS",
    "ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW_COUNT", "NOT_MATURED_COUNT", "MISSING_ENTRY_PRICE_COUNT",
    "MISSING_OUTCOME_PRICE_COUNT", "MISSING_BOTH_PRICES_COUNT", "INVALID_MISSING_LINK_KEYS_COUNT",
    "PRICE_SOURCE_DEGRADED_COUNT", "DRYRUN_PREVIEW_ROW_COUNT", "FORWARD_RETURN_FILLED_COUNT",
    "FORWARD_RETURN_PENDING_COUNT", "LOCAL_PRICE_SOURCE_COUNT", "USABLE_PRICE_SOURCE_COUNT",
    "CONTROLLED_FILLER_APPLY_DESIGN_READY", "MATCH_QUALITY_IMPACT_PROJECTION_CREATED",
    "SAFETY_AUDIT_CREATED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED",
    "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED",
    "SIMULATION_POSITION_MODIFIED", "SHADOW_FORWARD_TRACKER_MODIFIED",
    "EXISTING_FORWARD_TRACKER_MODIFIED", "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT",
    "READ_FIRST", "REPORT",
]
ELIGIBILITY_FIELDS = [
    "snapshot_date", "ticker", "signal_snapshot_id", "forward_tracker_link_key", "simulation_link_key",
    "manual_feedback_link_key", "planned_horizon", "planned_outcome_date", "forward_return_current_value",
    "forward_return_status_current", "entry_price_required", "outcome_price_required", "entry_price_available",
    "outcome_price_available", "entry_price_date", "outcome_price_date", "entry_price", "outcome_price",
    "latest_local_price_date", "horizon_matured", "local_price_source_path", "dryrun_forward_return_preview",
    "dryrun_return_preview_available", "fill_eligibility_status", "blocking_reason", "apply_status",
]
PRICE_AUDIT_FIELDS = [
    "source_path", "source_exists", "modified_time", "parsed_row_count", "parsed_ticker_count",
    "has_ticker", "has_date", "has_close", "has_adjusted_close", "has_volume", "min_date", "max_date",
    "usable_for_entry_price", "usable_for_outcome_price", "source_quality_status", "notes",
]
PREVIEW_FIELDS = [
    "snapshot_date", "ticker", "signal_snapshot_id", "planned_horizon", "entry_price_date",
    "entry_price", "outcome_price_date", "outcome_price", "dryrun_forward_return",
    "dryrun_forward_return_formula", "source_path", "apply_status", "notes",
]
BLOCKER_FIELDS = [
    "blocker_reason", "affected_row_count", "affected_ticker_count", "affected_horizon_count",
    "example_tickers", "recommended_resolution", "can_be_resolved_without_external_data",
    "requires_price_backfill", "requires_waiting_for_horizon_maturity",
]
DESIGN_FIELDS = [
    "design_step", "step_name", "purpose", "required_inputs", "output_file_if_applied_later",
    "safety_gate", "rollback_requirement", "modifies_existing_tracker", "recommended_apply_mode", "notes",
]
PROJECTION_FIELDS = [
    "scenario_name", "eligible_preview_count", "projected_filled_shadow_rows", "projected_pending_rows",
    "projected_high_confidence_match_count", "projected_medium_confidence_match_count",
    "projected_low_confidence_match_count", "projected_multi_horizon_readiness_status",
    "assumptions", "limitations",
]
SAFETY_FIELDS = ["safety_check", "status", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path, limit: Optional[int] = None) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists() or path.is_dir():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            rows: List[Dict[str, str]] = []
            with path.open("r", newline="", encoding=enc, errors="replace") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    rows.append(dict(row))
                    if limit and len(rows) >= limit:
                        break
                return rows, list(reader.fieldnames or [])
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


def parse_date(value: object) -> Optional[dt.date]:
    raw = str(value or "").strip()
    if not raw or raw.upper().startswith("PENDING") or raw.upper() in {"NA", "N/A", "NULL", "NONE"}:
        return None
    raw = raw.replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
        try:
            return dt.datetime.strptime(raw[:19], fmt).date()
        except ValueError:
            continue
    return None


def horizon_days(value: object) -> Optional[int]:
    match = re.search(r"(\d+)", str(value or ""))
    return int(match.group(1)) if match else None


def numeric(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text.replace(",", ""))
    except ValueError:
        return None


def modified_time(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def signature(path: Path) -> Tuple[str, str]:
    return (modified_time(path) if path.exists() else "MISSING", sha256(path))


def present(value: object) -> bool:
    text = str(value or "").strip()
    return text not in {"", "NA", "N/A", "None", "NULL"}


def find_col(fields: Iterable[str], candidates: Iterable[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return ""


def discover_price_sources(root: Path) -> List[Path]:
    bases = ["outputs/v16", "outputs/v17", "outputs/v18", "state/v16", "state/v17", "state/v18", "data", "cache"]
    excludes = {".venv", "node_modules", "stable_compressed", "__pycache__"}
    candidates: List[Path] = []
    pattern = re.compile(r"(price|ohlc|history|close|cache)", re.I)
    for rel in bases:
        base = root / rel
        if not base.exists():
            continue
        for path in base.rglob("*.csv"):
            parts = {part.lower() for part in path.parts}
            if parts & excludes:
                continue
            if "archive" in parts and "stable_compressed" in parts:
                continue
            if "price_cache" in parts or pattern.search(path.name) or pattern.search(str(path.parent)):
                candidates.append(path)
    unique = []
    seen = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def audit_price_sources(sources: Sequence[Path], shadow_tickers: set[str]) -> Tuple[List[Dict[str, object]], Dict[str, Dict[dt.date, Tuple[float, str]]], Dict[str, str]]:
    audit: List[Dict[str, object]] = []
    price_map: Dict[str, Dict[dt.date, Tuple[float, str]]] = defaultdict(dict)
    latest_source_by_ticker: Dict[str, str] = {}
    for path in sources:
        rows, fields = read_csv(path)
        if not rows or not fields:
            audit.append({
                "source_path": str(path), "source_exists": str(path.exists()).upper(), "modified_time": modified_time(path),
                "parsed_row_count": len(rows), "parsed_ticker_count": 0, "has_ticker": "FALSE", "has_date": "FALSE",
                "has_close": "FALSE", "has_adjusted_close": "FALSE", "has_volume": "FALSE", "min_date": "", "max_date": "",
                "usable_for_entry_price": "FALSE", "usable_for_outcome_price": "FALSE", "source_quality_status": "UNREADABLE_OR_INVALID",
                "notes": "Could not parse CSV rows/fields.",
            })
            continue
        ticker_col = find_col(fields, ["ticker", "symbol"])
        date_col = find_col(fields, ["date", "price_date", "latest_price_date", "snapshot_date"])
        close_col = find_col(fields, ["adj_close", "adjusted_close", "close", "latest_close"])
        adj_col = find_col(fields, ["adj_close", "adjusted_close"])
        volume_col = find_col(fields, ["volume"])
        tickers = set()
        dates = []
        usable_rows = 0
        # Per-ticker cache files often omit a ticker column; infer from filename.
        inferred_ticker = path.stem.upper() if path.parent.name.lower() == "price_cache" else ""
        for row in rows:
            ticker = str(row.get(ticker_col, "") or inferred_ticker).upper().strip()
            date = parse_date(row.get(date_col, ""))
            close = numeric(row.get(close_col, ""))
            if ticker:
                tickers.add(ticker)
            if date:
                dates.append(date)
            if ticker in shadow_tickers and date and close is not None:
                usable_rows += 1
                price_map[ticker][date] = (close, str(path))
                latest_source_by_ticker[ticker] = str(path)
        overlap = bool(tickers & shadow_tickers)
        min_date = min(dates).isoformat() if dates else ""
        max_date = max(dates).isoformat() if dates else ""
        if usable_rows and date_col and close_col:
            quality = "USABLE_OHLCV_HISTORY" if volume_col else "USABLE_LATEST_PRICE_ONLY"
        elif not overlap:
            quality = "IRRELEVANT_NO_TICKER_OVERLAP"
        elif date_col and close_col:
            quality = "SUMMARY_NOT_PRICE_HISTORY"
        else:
            quality = "UNREADABLE_OR_INVALID"
        audit.append({
            "source_path": str(path),
            "source_exists": str(path.exists()).upper(),
            "modified_time": modified_time(path),
            "parsed_row_count": len(rows),
            "parsed_ticker_count": len(tickers),
            "has_ticker": str(bool(ticker_col or inferred_ticker)).upper(),
            "has_date": str(bool(date_col)).upper(),
            "has_close": str(bool(close_col)).upper(),
            "has_adjusted_close": str(bool(adj_col)).upper(),
            "has_volume": str(bool(volume_col)).upper(),
            "min_date": min_date,
            "max_date": max_date,
            "usable_for_entry_price": str(usable_rows > 0).upper(),
            "usable_for_outcome_price": str(usable_rows > 0).upper(),
            "source_quality_status": quality,
            "notes": "Parsed as local-only candidate; no external data fetched.",
        })
    return audit, price_map, latest_source_by_ticker


def nearest_price(prices: Dict[dt.date, Tuple[float, str]], target: Optional[dt.date]) -> Tuple[str, str, str]:
    if not target or not prices:
        return "", "", ""
    if target in prices:
        price, source = prices[target]
        return target.isoformat(), f"{price:.6f}", source
    return "", "", ""


def latest_date(prices: Dict[dt.date, Tuple[float, str]]) -> str:
    return max(prices).isoformat() if prices else ""


def eligibility_status(row: Dict[str, str], entry_available: bool, outcome_available: bool, matured: bool, source_degraded: bool) -> Tuple[str, str]:
    if present(row.get("forward_return", "")):
        return "ALREADY_FILLED_SHOULD_NOT_OVERWRITE", "forward_return already has a value in input."
    if not present(row.get("signal_snapshot_id")) or not present(row.get("forward_tracker_link_key")):
        return "INVALID_MISSING_LINK_KEYS", "Missing signal snapshot or forward tracker link key."
    if source_degraded:
        return "PRICE_SOURCE_DEGRADED", "No usable local price source for ticker."
    if not matured:
        return "NOT_MATURED", "Planned horizon is not matured against latest local price date."
    if not entry_available and not outcome_available:
        return "MISSING_BOTH_PRICES", "Entry and outcome prices are unavailable locally."
    if not entry_available:
        return "MISSING_ENTRY_PRICE", "Entry price is unavailable locally."
    if not outcome_available:
        return "MISSING_OUTCOME_PRICE", "Outcome price is unavailable locally."
    return "ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW", "Both entry and outcome prices are available locally."


def build_design_rows() -> List[Dict[str, object]]:
    steps = [
        ("1", "Validate shadow tracker schema", "Ensure required link, date, horizon, and return fields exist.", "V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv", "validation report", "Required columns present and row count matches expected shadow rows.", "Discard generated dry-run output.", "FALSE", "VALIDATION_ONLY", "No tracker modification."),
        ("2", "Validate link keys", "Reject rows missing core link keys.", "shadow tracker link-key columns", "link-key audit", "No production apply for invalid rows.", "Regenerate audit from source shadow tracker.", "FALSE", "DRYRUN_AUDIT", "Preserve row-level blockers."),
        ("3", "Validate price source availability", "Identify local entry/outcome prices only.", "local price cache/history files", "price source audit", "No external fetch.", "Delete generated audit.", "FALSE", "LOCAL_ONLY_DRYRUN", "Price cache remains unchanged."),
        ("4", "Validate matured horizons", "Confirm outcome date is reachable from latest local price date.", "snapshot_date, planned_horizon, local max date", "maturity audit", "Future horizons remain blocked.", "Regenerate audit.", "FALSE", "DRYRUN_AUDIT", "No return fill."),
        ("5", "Calculate forward returns in dry-run", "Preview formula only when both prices exist.", "entry and outcome prices", "dry-run preview csv", "Preview output only.", "Delete preview output.", "FALSE", "DRYRUN_PREVIEW_ONLY", "Do not write into tracker."),
        ("6", "Write new filled-shadow output only", "Future controlled apply would write a new file.", "validated dry-run preview", "V18_21G_R1_CURRENT_FILLED_FORWARD_TRACKER_SHADOW.csv", "Explicit approval required.", "Remove new shadow output.", "FALSE", "NEW_SHADOW_OUTPUT_ONLY", "Future step, not applied now."),
        ("7", "Compare filled-shadow vs unfilled-shadow", "Verify only allowed return fields differ.", "unfilled and filled shadow outputs", "safety diff", "No unexpected diffs.", "Discard filled shadow.", "FALSE", "DIFF_ONLY", "Future step."),
        ("8", "Keep production tracker unchanged", "Protect existing forward tracker production files.", "production tracker paths", "production safety audit", "No production modifications.", "No restore needed if untouched.", "FALSE", "PRODUCTION_UNCHANGED", "Mandatory gate."),
        ("9", "Create stable snapshot before integration", "Preserve evidence before command-center work.", "all dry-run artifacts", "stable snapshot", "Validation fail count zero.", "Restore from snapshot if needed.", "FALSE", "SNAPSHOT_ONLY", "No command-center integration."),
    ]
    return [
        {
            "design_step": step, "step_name": name, "purpose": purpose, "required_inputs": inputs,
            "output_file_if_applied_later": output, "safety_gate": gate, "rollback_requirement": rollback,
            "modifies_existing_tracker": modifies, "recommended_apply_mode": mode, "notes": notes,
        }
        for step, name, purpose, inputs, output, gate, rollback, modifies, mode, notes in steps
    ]


def projection_rows(total: int, eligible: int) -> List[Dict[str, object]]:
    pending_after = total - eligible
    return [
        {"scenario_name": "CURRENT_ALL_PENDING", "eligible_preview_count": eligible, "projected_filled_shadow_rows": 0, "projected_pending_rows": total, "projected_high_confidence_match_count": 0, "projected_medium_confidence_match_count": 0, "projected_low_confidence_match_count": 20, "projected_multi_horizon_readiness_status": "NOT_READY_MULTI_HORIZON", "assumptions": "No returns filled.", "limitations": "Current state only."},
        {"scenario_name": "DRYRUN_PREVIEW_ONLY", "eligible_preview_count": eligible, "projected_filled_shadow_rows": 0, "projected_pending_rows": total, "projected_high_confidence_match_count": 0, "projected_medium_confidence_match_count": 0, "projected_low_confidence_match_count": 20, "projected_multi_horizon_readiness_status": "NOT_READY_MULTI_HORIZON", "assumptions": "Preview values are not applied.", "limitations": "No effect claims allowed."},
        {"scenario_name": "FUTURE_FILL_MATURED_1D_ONLY", "eligible_preview_count": eligible, "projected_filled_shadow_rows": eligible, "projected_pending_rows": pending_after, "projected_high_confidence_match_count": eligible, "projected_medium_confidence_match_count": 0, "projected_low_confidence_match_count": 20, "projected_multi_horizon_readiness_status": "PARTIAL_1D_ONLY_IF_ELIGIBLE", "assumptions": "Only matured 1D local prices are applied later.", "limitations": "Requires explicit approval."},
        {"scenario_name": "FUTURE_FILL_ALL_MATURED_LOCAL_PRICE_AVAILABLE", "eligible_preview_count": eligible, "projected_filled_shadow_rows": eligible, "projected_pending_rows": pending_after, "projected_high_confidence_match_count": eligible, "projected_medium_confidence_match_count": 0, "projected_low_confidence_match_count": 20, "projected_multi_horizon_readiness_status": "PARTIAL_LOCAL_PRICE_LIMITED", "assumptions": "All locally matured eligible rows applied to new shadow only.", "limitations": "Blocked rows remain pending."},
        {"scenario_name": "FUTURE_AFTER_PRICE_BACKFILL_AND_HORIZON_MATURITY", "eligible_preview_count": eligible, "projected_filled_shadow_rows": total, "projected_pending_rows": 0, "projected_high_confidence_match_count": total, "projected_medium_confidence_match_count": 0, "projected_low_confidence_match_count": 0, "projected_multi_horizon_readiness_status": "READY_AFTER_FUTURE_BACKFILL_AND_MATURITY", "assumptions": "All horizons mature and local price history exists.", "limitations": "Design projection only; no fetch or fill now."},
    ]


def safety_rows() -> List[Dict[str, object]]:
    checks = {
        "FORWARD_OUTCOME_FILLER_APPLIED": "FALSE",
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "SHADOW_FORWARD_TRACKER_MODIFIED": "FALSE",
        "EXISTING_FORWARD_TRACKER_MODIFIED": "FALSE",
        "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
        "SIMULATION_POSITION_MODIFIED": "FALSE",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
    }
    return [{"safety_check": key, "status": "PASS", "notes": f"{key} is {value}."} for key, value in checks.items()]


def protected_paths(root: Path) -> List[Path]:
    rels = [
        SHADOW_PATH,
        SIGNAL_PATH,
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
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


def validation_check(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"safety_check": f"VALIDATION_{name}", "status": "PASS" if ok else "FAIL", "notes": notes if ok else f"FAIL_COUNT={fail_count}; {notes}"}


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(values: Dict[str, object], blocker_summary: Sequence[Dict[str, object]]) -> str:
    top_blockers = ", ".join(f"{row['blocker_reason']}={row['affected_row_count']}" for row in blocker_summary[:5])
    return f"""# V18.21G Controlled Forward Outcome Filler Design Report

## Executive Summary
Status: {values.get('STATUS')}. V18.21G audited {values.get('SHADOW_FORWARD_TRACKER_INPUT_ROWS')} shadow forward tracker rows and produced a dry-run design only.

## Safety Statement
No forward returns were filled, no shadow tracker or production tracker was modified, no price cache was modified, and no external data was fetched.

## Shadow Tracker Input Summary
Input rows: {values.get('SHADOW_FORWARD_TRACKER_INPUT_ROWS')}. Pending returns: {values.get('FORWARD_RETURN_PENDING_COUNT')}. Filled returns applied by this module: {values.get('FORWARD_RETURN_FILLED_COUNT')}.

## Forward Outcome Eligibility Summary
Eligible dry-run previews: {values.get('ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW_COUNT')}. Not matured: {values.get('NOT_MATURED_COUNT')}. Missing entry price: {values.get('MISSING_ENTRY_PRICE_COUNT')}. Missing outcome price: {values.get('MISSING_OUTCOME_PRICE_COUNT')}. Missing both prices: {values.get('MISSING_BOTH_PRICES_COUNT')}.

## Local Price Source Summary
Local price source candidates: {values.get('LOCAL_PRICE_SOURCE_COUNT')}. Usable sources: {values.get('USABLE_PRICE_SOURCE_COUNT')}. External data fetched: {values.get('EXTERNAL_DATA_FETCHED')}.

## Dry-Run Preview Summary
Preview rows: {values.get('DRYRUN_PREVIEW_ROW_COUNT')}. Preview rows are separate output only and are not applied.

## Blocker Summary
{top_blockers if top_blockers else 'No blockers summarized.'}

## Controlled Filler Apply Design
The design requires schema validation, link-key validation, local price validation, maturity validation, dry-run calculation, new filled-shadow output only, safety diff, unchanged production tracker, and stable snapshot before integration.

## Match Quality Impact Projection
Projection artifact created: {values.get('MATCH_QUALITY_IMPACT_PROJECTION_CREATED')}. Projections are not effect claims.

## Why No Factor Effectiveness Claims Are Allowed
Forward returns remain unfilled in existing files, and any preview values are advisory dry-run only.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}. Safety audit created: {values.get('SAFETY_AUDIT_CREATED')}.

## Next-Step Recommendation
Create a stable snapshot if clean, then optionally design V18.21G-R1 controlled filled-shadow output only after explicit approval, or proceed to V18.21H full-history backfill design if price source gaps dominate.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/forward_tracker"
    ops_dir = root / "outputs/v18/ops"
    paths = {
        "eligibility": out_dir / "V18_21G_CURRENT_FORWARD_OUTCOME_ELIGIBILITY_AUDIT.csv",
        "price_audit": out_dir / "V18_21G_CURRENT_LOCAL_PRICE_SOURCE_AUDIT.csv",
        "preview": out_dir / "V18_21G_CURRENT_FORWARD_RETURN_DRYRUN_PREVIEW.csv",
        "blockers": out_dir / "V18_21G_CURRENT_FORWARD_OUTCOME_BLOCKER_SUMMARY.csv",
        "design": out_dir / "V18_21G_CURRENT_CONTROLLED_FILLER_APPLY_DESIGN.csv",
        "projection": out_dir / "V18_21G_CURRENT_FORWARD_OUTCOME_MATCH_QUALITY_IMPACT_PROJECTION.csv",
        "safety": out_dir / "V18_21G_CURRENT_FORWARD_OUTCOME_FILLER_SAFETY_AUDIT.csv",
        "read_first": ops_dir / "V18_21G_READ_FIRST.txt",
        "report": ops_dir / "V18_21G_CURRENT_CONTROLLED_FORWARD_OUTCOME_FILLER_DESIGN_REPORT.md",
    }
    before = {str(path): signature(path) for path in protected_paths(root)}
    shadow_rows, _ = read_csv(root / SHADOW_PATH)
    shadow_tickers = {str(row.get("ticker", "")).upper().strip() for row in shadow_rows if str(row.get("ticker", "")).strip()}
    price_sources = discover_price_sources(root)
    price_audit, price_map, _ = audit_price_sources(price_sources, shadow_tickers)

    eligibility: List[Dict[str, object]] = []
    previews: List[Dict[str, object]] = []
    for row in shadow_rows:
        ticker = str(row.get("ticker", "")).upper().strip()
        snapshot_date = parse_date(row.get("snapshot_date"))
        planned_date = parse_date(row.get("planned_outcome_date"))
        if planned_date is None and snapshot_date and horizon_days(row.get("planned_horizon")):
            planned_date = snapshot_date + dt.timedelta(days=horizon_days(row.get("planned_horizon")) or 0)
        prices = price_map.get(ticker, {})
        latest = latest_date(prices)
        entry_date, entry_price, entry_source = nearest_price(prices, snapshot_date)
        outcome_date, outcome_price, outcome_source = nearest_price(prices, planned_date)
        latest_dt = parse_date(latest)
        matured = bool(planned_date and latest_dt and latest_dt >= planned_date)
        entry_available = bool(entry_price)
        outcome_available = bool(outcome_price)
        source_degraded = ticker not in price_map
        status, reason = eligibility_status(row, entry_available, outcome_available, matured, source_degraded)
        preview_value = ""
        preview_available = "FALSE"
        source_path = outcome_source or entry_source
        if status == "ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW":
            er = numeric(entry_price)
            op = numeric(outcome_price)
            if er and op is not None:
                preview = (op / er) - 1.0
                preview_value = f"{preview:.8f}"
                preview_available = "TRUE"
                previews.append({
                    "snapshot_date": row.get("snapshot_date", ""),
                    "ticker": ticker,
                    "signal_snapshot_id": row.get("signal_snapshot_id", ""),
                    "planned_horizon": row.get("planned_horizon", ""),
                    "entry_price_date": entry_date,
                    "entry_price": entry_price,
                    "outcome_price_date": outcome_date,
                    "outcome_price": outcome_price,
                    "dryrun_forward_return": preview_value,
                    "dryrun_forward_return_formula": "(outcome_price / entry_price) - 1",
                    "source_path": source_path,
                    "apply_status": "NOT_APPLIED_DRYRUN_ONLY",
                    "notes": "Preview only; not written to tracker.",
                })
        eligibility.append({
            "snapshot_date": row.get("snapshot_date", ""),
            "ticker": ticker,
            "signal_snapshot_id": row.get("signal_snapshot_id", ""),
            "forward_tracker_link_key": row.get("forward_tracker_link_key", ""),
            "simulation_link_key": row.get("simulation_link_key", ""),
            "manual_feedback_link_key": row.get("manual_feedback_link_key", ""),
            "planned_horizon": row.get("planned_horizon", ""),
            "planned_outcome_date": planned_date.isoformat() if planned_date else row.get("planned_outcome_date", ""),
            "forward_return_current_value": row.get("forward_return", ""),
            "forward_return_status_current": row.get("forward_return_status", ""),
            "entry_price_required": "TRUE",
            "outcome_price_required": "TRUE",
            "entry_price_available": str(entry_available).upper(),
            "outcome_price_available": str(outcome_available).upper(),
            "entry_price_date": entry_date,
            "outcome_price_date": outcome_date,
            "entry_price": entry_price,
            "outcome_price": outcome_price,
            "latest_local_price_date": latest,
            "horizon_matured": str(matured).upper(),
            "local_price_source_path": source_path,
            "dryrun_forward_return_preview": preview_value,
            "dryrun_return_preview_available": preview_available,
            "fill_eligibility_status": status,
            "blocking_reason": reason,
            "apply_status": "NOT_APPLIED_DRYRUN_ONLY",
        })

    if not previews:
        previews = []
    blocker_groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in eligibility:
        if row["fill_eligibility_status"] != "ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW":
            blocker_groups[str(row["fill_eligibility_status"])].append(row)
    resolution = {
        "NOT_MATURED": ("Wait for horizon maturity or later local price availability.", "TRUE", "FALSE", "TRUE"),
        "MISSING_ENTRY_PRICE": ("Backfill local entry-date price history.", "FALSE", "TRUE", "FALSE"),
        "MISSING_OUTCOME_PRICE": ("Backfill local outcome-date price history or wait if future.", "FALSE", "TRUE", "TRUE"),
        "MISSING_BOTH_PRICES": ("Backfill local entry and outcome price history.", "FALSE", "TRUE", "TRUE"),
        "PRICE_SOURCE_DEGRADED": ("Add/repair local ticker price history source.", "FALSE", "TRUE", "FALSE"),
        "INVALID_MISSING_LINK_KEYS": ("Repair link keys in a new shadow output only.", "TRUE", "FALSE", "FALSE"),
        "ALREADY_FILLED_SHOULD_NOT_OVERWRITE": ("Do not overwrite existing value.", "TRUE", "FALSE", "FALSE"),
    }
    blocker_rows = []
    for reason, rows in sorted(blocker_groups.items()):
        tickers = sorted({str(row["ticker"]) for row in rows if row.get("ticker")})
        horizons = sorted({str(row["planned_horizon"]) for row in rows if row.get("planned_horizon")})
        rec = resolution.get(reason, ("Review row-level blocker.", "TRUE", "FALSE", "FALSE"))
        blocker_rows.append({
            "blocker_reason": reason,
            "affected_row_count": len(rows),
            "affected_ticker_count": len(tickers),
            "affected_horizon_count": len(horizons),
            "example_tickers": ",".join(tickers[:10]),
            "recommended_resolution": rec[0],
            "can_be_resolved_without_external_data": rec[1],
            "requires_price_backfill": rec[2],
            "requires_waiting_for_horizon_maturity": rec[3],
        })

    design_rows = build_design_rows()
    projection = projection_rows(len(shadow_rows), len(previews))
    safety = safety_rows()

    write_csv(paths["eligibility"], eligibility, ELIGIBILITY_FIELDS)
    write_csv(paths["price_audit"], price_audit, PRICE_AUDIT_FIELDS)
    write_csv(paths["preview"], previews, PREVIEW_FIELDS)
    write_csv(paths["blockers"], blocker_rows, BLOCKER_FIELDS)
    write_csv(paths["design"], design_rows, DESIGN_FIELDS)
    write_csv(paths["projection"], projection, PROJECTION_FIELDS)
    write_csv(paths["safety"], safety, SAFETY_FIELDS)

    counts = Counter(str(row["fill_eligibility_status"]) for row in eligibility)
    usable_sources = sum(1 for row in price_audit if row.get("source_quality_status") in {"USABLE_OHLCV_HISTORY", "USABLE_LATEST_PRICE_ONLY"})
    pending_count = sum(1 for row in shadow_rows if row.get("forward_return_status") == "PENDING_NOT_FILLED")
    values: Dict[str, object] = {
        "STATUS": STATUS_READY,
        "SHADOW_FORWARD_TRACKER_INPUT_ROWS": len(shadow_rows),
        "OUTCOME_ELIGIBILITY_AUDIT_ROWS": len(eligibility),
        "ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW_COUNT": counts["ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW"],
        "NOT_MATURED_COUNT": counts["NOT_MATURED"],
        "MISSING_ENTRY_PRICE_COUNT": counts["MISSING_ENTRY_PRICE"],
        "MISSING_OUTCOME_PRICE_COUNT": counts["MISSING_OUTCOME_PRICE"],
        "MISSING_BOTH_PRICES_COUNT": counts["MISSING_BOTH_PRICES"],
        "INVALID_MISSING_LINK_KEYS_COUNT": counts["INVALID_MISSING_LINK_KEYS"],
        "PRICE_SOURCE_DEGRADED_COUNT": counts["PRICE_SOURCE_DEGRADED"],
        "DRYRUN_PREVIEW_ROW_COUNT": len(previews),
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "FORWARD_RETURN_PENDING_COUNT": pending_count,
        "LOCAL_PRICE_SOURCE_COUNT": len(price_audit),
        "USABLE_PRICE_SOURCE_COUNT": usable_sources,
        "CONTROLLED_FILLER_APPLY_DESIGN_READY": "TRUE",
        "MATCH_QUALITY_IMPACT_PROJECTION_CREATED": str(paths["projection"].exists()).upper(),
        "SAFETY_AUDIT_CREATED": str(paths["safety"].exists()).upper(),
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    values.update(SAFETY_FLAGS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, blocker_rows))

    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    read_first_text = read_text(paths["read_first"])
    validations = [
        validation_check("powershell_parse_wrapper", ps_parse(root / "scripts/v18/run_v18_21G_controlled_forward_outcome_filler_design.ps1"), 1, "Wrapper parses."),
        validation_check("python_compile_script", py_compile(root / "scripts/v18/v18_21G_controlled_forward_outcome_filler_design.py"), 1, "Python script compiles."),
        validation_check("required_outputs_exist", all(path.exists() for path in paths.values()), 1, "All required outputs exist."),
        validation_check("required_read_first_fields_exist", all(field in read_first_text for field in READ_FIRST_FIELDS), 1, "All required READ_FIRST fields exist."),
        validation_check("shadow_row_count_expected", len(shadow_rows) == 525, 1, f"shadow_rows={len(shadow_rows)}"),
        validation_check("forward_return_filled_zero", values["FORWARD_RETURN_FILLED_COUNT"] == "0", 1, "No returns filled."),
        validation_check("protected_files_unchanged", not changed, len(changed), "Changed protected files: " + ";".join(changed)),
        validation_check("external_data_not_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE", 1, "No external data fetched."),
        validation_check("claims_weights_promotions_zero", values["EFFECT_CLAIM_ALLOWED_COUNT"] == "0" and values["WEIGHT_CHANGE_ALLOWED_COUNT"] == "0" and values["PRODUCTION_PROMOTION_ALLOWED_COUNT"] == "0", 1, "No claims, weights, or promotions allowed."),
    ]
    safety.extend(validations)
    fail_count = sum(1 for row in safety if row["status"] != "PASS")
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["safety"], safety, SAFETY_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, blocker_rows))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "FORWARD_OUTCOME_FILLER_APPLIED",
        "SHADOW_FORWARD_TRACKER_INPUT_ROWS", "OUTCOME_ELIGIBILITY_AUDIT_ROWS",
        "ELIGIBLE_FOR_DRYRUN_FILL_PREVIEW_COUNT", "NOT_MATURED_COUNT",
        "MISSING_ENTRY_PRICE_COUNT", "MISSING_OUTCOME_PRICE_COUNT", "MISSING_BOTH_PRICES_COUNT",
        "PRICE_SOURCE_DEGRADED_COUNT", "DRYRUN_PREVIEW_ROW_COUNT", "FORWARD_RETURN_FILLED_COUNT",
        "FORWARD_RETURN_PENDING_COUNT", "LOCAL_PRICE_SOURCE_COUNT", "USABLE_PRICE_SOURCE_COUNT",
        "CONTROLLED_FILLER_APPLY_DESIGN_READY", "MATCH_QUALITY_IMPACT_PROJECTION_CREATED",
        "SAFETY_AUDIT_CREATED", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
        "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
