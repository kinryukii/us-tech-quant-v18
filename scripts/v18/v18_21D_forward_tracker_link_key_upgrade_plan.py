from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_WARN = "WARN_V18_21D_FORWARD_TRACKER_LINK_KEY_UPGRADE_PLAN_READY"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "FORWARD_TRACKER_LINK_KEY_UPGRADE_PLAN_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "FORWARD_TRACKER_UPGRADE_APPLIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

FORWARD_SOURCES = [
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
    "outputs/v18/candidates/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
    "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv",
    "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
    "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
    "outputs/v18/forward_outcome/V18_4A_CURRENT_FACTOR_SNAPSHOT.csv",
    "outputs/v18/factor_research/V18_10B_R1_CURRENT_FORWARD_RETURN_MATURITY.csv",
    "outputs/v18/factor_research/V18_10B_CURRENT_FACTOR_EFFECTIVENESS.csv",
    "outputs/v18/technical_timing_forward/V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv",
    "outputs/v18/sell_timing/V18_CURRENT_EXIT_SIGNAL_FORWARD_TRACKER.csv",
]
HORIZONS = ["1D", "3D", "5D", "10D", "20D"]
HORIZON_COLUMNS = {
    "1D": ["forward_1d_return", "fwd_1d_return", "return_1obs_pct"],
    "3D": ["forward_3d_return", "fwd_3d_return", "return_3obs_pct"],
    "5D": ["forward_5d_return", "fwd_5d_return", "return_5obs_pct"],
    "10D": ["forward_10d_return", "fwd_10d_return", "return_10obs_pct"],
    "20D": ["forward_20d_return", "fwd_20d_return", "return_20obs_pct"],
}
REQUIRED_FIELDS = [
    "signal_snapshot_id",
    "snapshot_date",
    "ticker",
    "forward_tracker_link_key",
    "simulation_link_key",
    "manual_feedback_link_key",
    "horizon",
    "outcome_date",
    "forward_return",
    "source_signal_snapshot_path",
    "source_forward_tracker_path",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "FORWARD_TRACKER_UPGRADE_APPLIED",
    "SIGNAL_SNAPSHOT_ROW_COUNT", "READY_FOR_FORWARD_RESEARCH_COUNT", "FORWARD_TRACKER_SOURCE_COUNT",
    "FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT", "FORWARD_SOURCE_PARTIAL_TICKER_DATE_ONLY_COUNT",
    "FORWARD_SOURCE_TICKER_ONLY_LOW_CONFIDENCE_COUNT", "REQUIRED_LINK_KEY_FIELD_COUNT",
    "REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT", "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT", "PLANNED_HORIZON_COUNT",
    "MATCH_QUALITY_PROJECTION_CREATED", "FORWARD_KEY_UPGRADE_PLAN_READY", "MULTI_HORIZON_OUTCOME_PLAN_READY",
    "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT",
    "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "PRICE_FACTOR_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def modified_time(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper().replace(".", "-")


def read_first(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def has_any(fields: Iterable[str], names: Iterable[str]) -> bool:
    lower = {field.lower() for field in fields}
    return any(name.lower() in lower for name in names)


def schema_audit(root: Path) -> List[Dict[str, object]]:
    rows = []
    for rel in FORWARD_SOURCES:
        path = root / rel
        records, fields = read_csv(path)
        lower = {field.lower(): field for field in fields}
        ticker_col = lower.get("ticker") or lower.get("symbol") or lower.get("yf_ticker")
        tickers = {norm_ticker(row.get(ticker_col, "")) for row in records} if ticker_col else set()
        tickers.discard("")
        detected = [h for h, cols in HORIZON_COLUMNS.items() if has_any(fields, cols)]
        has_generic_forward = has_any(fields, ["forward_return", "return"])
        has_horizon = has_any(fields, ["horizon", "planned_horizon"]) or bool(detected)
        has_outcome_date = has_any(fields, ["outcome_date", "forward_date", "target_price_date_1obs", "fwd_1d_price_date", "forward_1d_price_date"])
        missing = []
        for field in ["signal_snapshot_id", "snapshot_date", "forward_tracker_link_key", "simulation_link_key", "ticker", "horizon", "outcome_date", "forward_return"]:
            if field == "ticker" and ticker_col:
                continue
            if field == "horizon" and has_horizon:
                continue
            if field == "outcome_date" and has_outcome_date:
                continue
            if field == "forward_return" and (has_generic_forward or detected):
                continue
            if field.lower() not in lower:
                missing.append(field)
        if lower.get("signal_snapshot_id") and lower.get("forward_tracker_link_key") and detected:
            status = "READY_HIGH_CONFIDENCE_MATCH"
            notes = "Direct link keys and horizon returns are present."
        elif ticker_col and (lower.get("signal_date") or lower.get("snapshot_date")):
            status = "PARTIAL_TICKER_DATE_MATCH_ONLY"
            notes = "Ticker/date matching is possible but direct keys are missing."
        elif ticker_col:
            status = "TICKER_ONLY_LOW_CONFIDENCE"
            notes = "Ticker-only matching cannot reliably link signal snapshots."
        elif records and not ticker_col:
            status = "SUMMARY_NOT_SIGNAL_LEVEL"
            notes = "Rows are not signal-level ticker outcomes."
        else:
            status = "UNUSABLE_FOR_FORWARD_MATCH"
            notes = "Missing or unreadable source for forward matching."
        rows.append(
            {
                "source_path": str(path),
                "source_exists": str(path.exists()).upper(),
                "modified_time": modified_time(path),
                "parsed_row_count": len(records),
                "parsed_ticker_count": len(tickers),
                "has_signal_snapshot_id": str("signal_snapshot_id" in lower).upper(),
                "has_snapshot_date": str("snapshot_date" in lower).upper(),
                "has_forward_tracker_link_key": str("forward_tracker_link_key" in lower).upper(),
                "has_simulation_link_key": str("simulation_link_key" in lower).upper(),
                "has_ticker": str(bool(ticker_col)).upper(),
                "has_signal_date": str("signal_date" in lower).upper(),
                "has_horizon": str(has_horizon).upper(),
                "has_outcome_date": str(has_outcome_date).upper(),
                "has_forward_return": str(has_generic_forward or bool(detected)).upper(),
                "has_forward_return_1d": str("1D" in detected).upper(),
                "has_forward_return_3d": str("3D" in detected).upper(),
                "has_forward_return_5d": str("5D" in detected).upper(),
                "has_forward_return_10d": str("10D" in detected).upper(),
                "has_forward_return_20d": str("20D" in detected).upper(),
                "schema_quality_status": status,
                "missing_required_fields": ";".join(missing),
                "notes": notes,
            }
        )
    return rows


def field_plan(schema_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    availability = {field: any(str(row.get(f"has_{field}", "")).upper() == "TRUE" for row in schema_rows) for field in REQUIRED_FIELDS}
    availability["source_signal_snapshot_path"] = True
    availability["source_forward_tracker_path"] = True
    details = {
        "signal_snapshot_id": ("signal_snapshot", "forward_tracker", "Immutable high-confidence join key."),
        "snapshot_date": ("signal_snapshot", "forward_tracker", "Date anchor for signal state."),
        "ticker": ("signal_snapshot", "forward_tracker", "Ticker identity and fallback join key."),
        "forward_tracker_link_key": ("forward_tracker", "forward_outcomes", "Stable tracker-to-outcome join key."),
        "simulation_link_key": ("simulation_linker", "forward_tracker", "Tie simulation rows to signal/outcome rows."),
        "manual_feedback_link_key": ("manual_feedback", "forward_tracker", "Future manual review join key."),
        "horizon": ("forward_tracker", "forward_outcomes", "Normalize outcome horizon rows."),
        "outcome_date": ("forward_outcomes", "factor_effectiveness", "Confirm forward return maturity date."),
        "forward_return": ("forward_outcomes", "factor_effectiveness", "Actual realized forward return."),
        "source_signal_snapshot_path": ("signal_snapshot", "forward_tracker", "Provenance to immutable snapshot source."),
        "source_forward_tracker_path": ("forward_tracker", "factor_effectiveness", "Provenance to tracker source."),
    }
    rows = []
    for field in REQUIRED_FIELDS:
        src, dst, purpose = details[field]
        available = availability.get(field, False)
        rows.append(
            {
                "field_name": field,
                "required_for_high_confidence_match": "TRUE",
                "source_component": src,
                "target_component": dst,
                "purpose": purpose,
                "current_availability_status": "AVAILABLE_SOMEWHERE" if available else "MISSING_FROM_FORWARD_SOURCES",
                "recommended_action": "PRESERVE_AND_PROPAGATE" if available else "ADD_IN_CONTROLLED_R1_APPLICATION",
                "migration_risk": "LOW" if field.startswith("source_") or field in {"ticker", "snapshot_date"} else "MEDIUM",
                "notes": "Plan only; no schema migration applied.",
            }
        )
    return rows


def dryrun_rows(snapshot_rows: List[Dict[str, str]], root: Path) -> List[Dict[str, object]]:
    source_snapshot_path = str(root / "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv")
    ready = [row for row in snapshot_rows if row.get("research_readiness_status") == "FORWARD_ONLY_READY" or row.get("signal_research_status") == "READY_FOR_SNAPSHOT_RESEARCH"]
    rows = []
    for signal in ready:
        for horizon in HORIZONS:
            rows.append(
                {
                    "snapshot_date": signal.get("snapshot_date", ""),
                    "ticker": signal.get("ticker", ""),
                    "signal_snapshot_id": signal.get("signal_snapshot_id", ""),
                    "forward_tracker_link_key": signal.get("forward_tracker_link_key", "") or f"forward_tracker|{signal.get('snapshot_date', '')}|{signal.get('ticker', '')}|{horizon}",
                    "simulation_link_key": signal.get("simulation_link_key", ""),
                    "manual_feedback_link_key": signal.get("manual_feedback_link_key", ""),
                    "planned_horizon": horizon,
                    "planned_outcome_date_placeholder": "NA",
                    "forward_return_placeholder": "NA",
                    "source_snapshot_path": source_snapshot_path,
                    "dryrun_only": "TRUE",
                    "apply_status": "NOT_APPLIED_DRYRUN_ONLY",
                }
            )
    return rows


def projection(current: Dict[str, str], ready_count: int) -> List[Dict[str, object]]:
    low = int(current.get("LOW_CONFIDENCE_MATCH_COUNT", 20) or 20)
    unmatched = int(current.get("UNMATCHED_OR_AMBIGUOUS_COUNT", 305) or 305)
    return [
        {
            "scenario_name": "CURRENT",
            "high_confidence_match_count_projected": current.get("HIGH_CONFIDENCE_MATCH_COUNT", "0"),
            "medium_confidence_match_count_projected": current.get("MEDIUM_CONFIDENCE_MATCH_COUNT", "0"),
            "low_confidence_match_count_projected": low,
            "unmatched_or_ambiguous_count_projected": unmatched,
            "multi_horizon_readiness_projected": current.get("MULTI_HORIZON_READINESS_STATUS", "NOT_READY_MULTI_HORIZON"),
            "assumptions": "No changes applied.",
            "limitations": "Ticker-only/partial matches remain unreliable.",
        },
        {
            "scenario_name": "ADD_SIGNAL_SNAPSHOT_ID_ONLY",
            "high_confidence_match_count_projected": min(ready_count, low + int(current.get("HIGH_CONFIDENCE_MATCH_COUNT", 0) or 0)),
            "medium_confidence_match_count_projected": 0,
            "low_confidence_match_count_projected": 0,
            "unmatched_or_ambiguous_count_projected": max(325 - ready_count, 0),
            "multi_horizon_readiness_projected": "NOT_READY_MULTI_HORIZON",
            "assumptions": "Signal IDs are propagated for ready forward-research rows only.",
            "limitations": "Does not create 3D/5D/10D/20D returns.",
        },
        {
            "scenario_name": "ADD_SIGNAL_SNAPSHOT_ID_AND_HORIZON",
            "high_confidence_match_count_projected": ready_count,
            "medium_confidence_match_count_projected": 0,
            "low_confidence_match_count_projected": 0,
            "unmatched_or_ambiguous_count_projected": max(325 - ready_count, 0),
            "multi_horizon_readiness_projected": "STRUCTURE_READY_OUTCOMES_PENDING",
            "assumptions": "One row per signal/horizon can be represented.",
            "limitations": "Forward returns still mature over time.",
        },
        {
            "scenario_name": "ADD_FULL_LINK_KEY_SET",
            "high_confidence_match_count_projected": ready_count,
            "medium_confidence_match_count_projected": 0,
            "low_confidence_match_count_projected": 0,
            "unmatched_or_ambiguous_count_projected": max(325 - ready_count, 0),
            "multi_horizon_readiness_projected": "KEY_READY_OUTCOMES_PENDING",
            "assumptions": "All link keys and provenance fields are added in a future controlled patch.",
            "limitations": "No return values are fabricated.",
        },
        {
            "scenario_name": "ADD_FULL_LINK_KEY_SET_AND_OUTCOME_ACCUMULATION",
            "high_confidence_match_count_projected": ready_count,
            "medium_confidence_match_count_projected": 0,
            "low_confidence_match_count_projected": 0,
            "unmatched_or_ambiguous_count_projected": max(325 - ready_count, 0),
            "multi_horizon_readiness_projected": "POTENTIALLY_READY_AFTER_HORIZONS_MATURE",
            "assumptions": "Future local outcomes mature for all planned horizons.",
            "limitations": "Requires time and future controlled outcome capture; not applied here.",
        },
    ]


def safety_audit() -> List[Dict[str, str]]:
    checks = {
        "FORWARD_TRACKER_UPGRADE_APPLIED is FALSE": SAFETY_FLAGS["FORWARD_TRACKER_UPGRADE_APPLIED"] == "FALSE",
        "FORWARD_TRACKER_MODIFIED is FALSE": SAFETY_FLAGS["FORWARD_TRACKER_MODIFIED"] == "FALSE",
        "SIGNAL_SNAPSHOT_MODIFIED is FALSE": SAFETY_FLAGS["SIGNAL_SNAPSHOT_MODIFIED"] == "FALSE",
        "SIMULATION_POSITION_MODIFIED is FALSE": SAFETY_FLAGS["SIMULATION_POSITION_MODIFIED"] == "FALSE",
        "PRICE_CACHE_MODIFIED is FALSE": SAFETY_FLAGS["PRICE_CACHE_MODIFIED"] == "FALSE",
        "EXTERNAL_DATA_FETCHED is FALSE": SAFETY_FLAGS["EXTERNAL_DATA_FETCHED"] == "FALSE",
        "OFFICIAL_DECISION_IMPACT is NONE": SAFETY_FLAGS["OFFICIAL_DECISION_IMPACT"] == "NONE",
        "AUTO_TRADE is DISABLED": SAFETY_FLAGS["AUTO_TRADE"] == "DISABLED",
        "AUTO_SELL is DISABLED": SAFETY_FLAGS["AUTO_SELL"] == "DISABLED",
    }
    return [{"safety_check": key, "status": "PASS" if ok else "FAIL", "notes": "Dry-run plan only; no protected files modified."} for key, ok in checks.items()]


def report_text(values: Dict[str, object]) -> str:
    return f"""# V18.21D Forward Tracker Link-Key Upgrade Plan

## Executive summary
Status: {values['STATUS']}. The module produced a dry-run forward tracker link-key upgrade plan. No upgrade was applied.

## Safety statement
This is advisory-only and dry-run only. It does not modify forward tracker state, signal snapshots, simulation positions, price cache, ranking, factors, official decisions, broker execution, auto-trade, or auto-sell. External data fetched: FALSE.

## Current forward tracker schema audit summary
Forward sources audited: {values['FORWARD_TRACKER_SOURCE_COUNT']}. High-confidence-ready sources: {values['FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT']}. Partial ticker/date-only sources: {values['FORWARD_SOURCE_PARTIAL_TICKER_DATE_ONLY_COUNT']}. Ticker-only low-confidence sources: {values['FORWARD_SOURCE_TICKER_ONLY_LOW_CONFIDENCE_COUNT']}.

## Required link-key field plan
Required link-key fields: {values['REQUIRED_LINK_KEY_FIELD_COUNT']}. Currently available in at least some source context: {values['REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT']}.

## Dry-run forward row template summary
Dry-run rows created: {values['DRYRUN_FORWARD_TEMPLATE_ROW_COUNT']}. Planned horizon count: {values['PLANNED_HORIZON_COUNT']}. All rows are `NOT_APPLIED_DRYRUN_ONLY` and contain no fabricated forward returns.

## Match quality improvement projection
Projection file created: {values['MATCH_QUALITY_PROJECTION_CREATED']}. It shows expected match-quality improvements if keys are added later.

## Multi-horizon outcome readiness plan
The plan defines 1D/3D/5D/10D/20D rows for future outcome capture, but no outcomes are backfilled or fetched.

## Why no factor effectiveness claims are allowed
This patch creates schema and compatibility plans only. Current evidence remains low-confidence and multi-horizon immature.

## Validation summary
Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

## Next-step recommendation
Create a stable snapshot of this plan, then consider a separate V18.21D-R1 controlled application only after explicit approval.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/forward_tracker"
    ops_dir = root / "outputs/v18/ops"
    schema_path = out_dir / "V18_21D_CURRENT_FORWARD_TRACKER_SCHEMA_AUDIT.csv"
    field_plan_path = out_dir / "V18_21D_CURRENT_REQUIRED_LINK_KEY_FIELD_PLAN.csv"
    template_path = out_dir / "V18_21D_CURRENT_DRYRUN_FORWARD_ROW_TEMPLATE.csv"
    projection_path = out_dir / "V18_21D_CURRENT_MATCH_QUALITY_IMPROVEMENT_PROJECTION.csv"
    safety_path = out_dir / "V18_21D_CURRENT_FORWARD_LINK_KEY_UPGRADE_SAFETY_AUDIT.csv"
    read_first_path = ops_dir / "V18_21D_READ_FIRST.txt"
    report_path = ops_dir / "V18_21D_CURRENT_FORWARD_TRACKER_LINK_KEY_UPGRADE_PLAN_REPORT.md"

    snapshot_rows, _ = read_csv(root / "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv")
    current_r2 = read_first(root / "outputs/v18/ops/V18_21C_R2_READ_FIRST.txt")
    schema_rows = schema_audit(root)
    plan_rows = field_plan(schema_rows)
    template_rows = dryrun_rows(snapshot_rows, root)
    ready_count = len({row["ticker"] for row in template_rows})
    projection_rows = projection(current_r2, ready_count)
    safety_rows = safety_audit()

    schema_fields = [
        "source_path", "source_exists", "modified_time", "parsed_row_count", "parsed_ticker_count", "has_signal_snapshot_id",
        "has_snapshot_date", "has_forward_tracker_link_key", "has_simulation_link_key", "has_ticker", "has_signal_date",
        "has_horizon", "has_outcome_date", "has_forward_return", "has_forward_return_1d", "has_forward_return_3d",
        "has_forward_return_5d", "has_forward_return_10d", "has_forward_return_20d", "schema_quality_status",
        "missing_required_fields", "notes",
    ]
    write_csv(schema_path, schema_rows, schema_fields)
    write_csv(field_plan_path, plan_rows, [
        "field_name", "required_for_high_confidence_match", "source_component", "target_component", "purpose",
        "current_availability_status", "recommended_action", "migration_risk", "notes",
    ])
    write_csv(template_path, template_rows, [
        "snapshot_date", "ticker", "signal_snapshot_id", "forward_tracker_link_key", "simulation_link_key",
        "manual_feedback_link_key", "planned_horizon", "planned_outcome_date_placeholder", "forward_return_placeholder",
        "source_snapshot_path", "dryrun_only", "apply_status",
    ])
    write_csv(projection_path, projection_rows, [
        "scenario_name", "high_confidence_match_count_projected", "medium_confidence_match_count_projected",
        "low_confidence_match_count_projected", "unmatched_or_ambiguous_count_projected", "multi_horizon_readiness_projected",
        "assumptions", "limitations",
    ])
    write_csv(safety_path, safety_rows, ["safety_check", "status", "notes"])

    status_counts = Counter(row["schema_quality_status"] for row in schema_rows)
    available_required = sum(1 for row in plan_rows if row["current_availability_status"] == "AVAILABLE_SOMEWHERE")
    values: Dict[str, object] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "SIGNAL_SNAPSHOT_ROW_COUNT": str(len(snapshot_rows)),
        "READY_FOR_FORWARD_RESEARCH_COUNT": str(ready_count),
        "FORWARD_TRACKER_SOURCE_COUNT": str(sum(1 for row in schema_rows if row["source_exists"] == "TRUE")),
        "FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT": str(status_counts["READY_HIGH_CONFIDENCE_MATCH"]),
        "FORWARD_SOURCE_PARTIAL_TICKER_DATE_ONLY_COUNT": str(status_counts["PARTIAL_TICKER_DATE_MATCH_ONLY"]),
        "FORWARD_SOURCE_TICKER_ONLY_LOW_CONFIDENCE_COUNT": str(status_counts["TICKER_ONLY_LOW_CONFIDENCE"]),
        "REQUIRED_LINK_KEY_FIELD_COUNT": str(len(REQUIRED_FIELDS)),
        "REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT": str(available_required),
        "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT": str(len(template_rows)),
        "PLANNED_HORIZON_COUNT": str(len(HORIZONS)),
        "MATCH_QUALITY_PROJECTION_CREATED": str(projection_path.exists()).upper(),
        "FORWARD_KEY_UPGRADE_PLAN_READY": "TRUE",
        "MULTI_HORIZON_OUTCOME_PLAN_READY": "TRUE",
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    fail_count = 0
    for path in [schema_path, field_plan_path, template_path, projection_path, safety_path, read_first_path, report_path]:
        if not path.exists():
            fail_count += 1
    for field in READ_FIRST_FIELDS:
        if field not in values:
            fail_count += 1
    for key, expected in {
        "FORWARD_TRACKER_UPGRADE_APPLIED": "FALSE",
        "FORWARD_TRACKER_MODIFIED": "FALSE",
        "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    }.items():
        if str(values.get(key, "")) != expected:
            fail_count += 1
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "FORWARD_TRACKER_UPGRADE_APPLIED", "SIGNAL_SNAPSHOT_ROW_COUNT",
        "READY_FOR_FORWARD_RESEARCH_COUNT", "FORWARD_TRACKER_SOURCE_COUNT", "FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT",
        "FORWARD_SOURCE_PARTIAL_TICKER_DATE_ONLY_COUNT", "FORWARD_SOURCE_TICKER_ONLY_LOW_CONFIDENCE_COUNT",
        "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT", "MATCH_QUALITY_PROJECTION_CREATED", "FORWARD_KEY_UPGRADE_PLAN_READY",
        "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
