from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "ADVISORY_ONLY"
PATCH_MODE = "FORWARD_MATCH_KEY_QUALITY_AND_MULTI_HORIZON_PLAN_ONLY"
STATUS_WARN = "WARN_V18_21C_R2_FORWARD_MATCH_KEY_QUALITY_PLAN_READY"
MINIMUM_SAMPLE_REQUIRED = 20

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
}

FORWARD_SOURCES = [
    ("current_ranked_candidate_forward_tracker", "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"),
    ("v18_14c_ranked_candidate_forward_tracker", "outputs/v18/candidates/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"),
    ("v18_14d_forward_price_filler", "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv"),
    ("sim_candidate_tracker", "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"),
    ("sim_candidate_tracker_today", "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv"),
    ("v18_4a_factor_snapshot", "outputs/v18/forward_outcome/V18_4A_CURRENT_FACTOR_SNAPSHOT.csv"),
]
HORIZON_COLUMNS = {
    "1D": ["forward_1d_return", "fwd_1d_return", "return_1obs_pct"],
    "3D": ["forward_3d_return", "fwd_3d_return", "return_3obs_pct"],
    "5D": ["forward_5d_return", "fwd_5d_return", "return_5obs_pct"],
    "10D": ["forward_10d_return", "fwd_10d_return", "return_10obs_pct"],
    "20D": ["forward_20d_return", "fwd_20d_return", "return_20obs_pct"],
}
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "SIGNAL_SNAPSHOT_ROW_COUNT", "SIGNAL_SNAPSHOT_HISTORY_COUNT",
    "FORWARD_OUTCOME_SOURCE_COUNT", "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT", "HIGH_CONFIDENCE_MATCH_COUNT",
    "MEDIUM_CONFIDENCE_MATCH_COUNT", "LOW_CONFIDENCE_MATCH_COUNT", "UNMATCHED_OR_AMBIGUOUS_COUNT",
    "HIGH_QUALITY_FORWARD_SOURCE_COUNT", "MEDIUM_QUALITY_FORWARD_SOURCE_COUNT", "TICKER_DATE_ONLY_SOURCE_COUNT",
    "TICKER_ONLY_LOW_CONFIDENCE_SOURCE_COUNT", "UNUSABLE_FORWARD_SOURCE_COUNT", "HORIZON_1D_USABLE_COUNT",
    "HORIZON_3D_USABLE_COUNT", "HORIZON_5D_USABLE_COUNT", "HORIZON_10D_USABLE_COUNT", "HORIZON_20D_USABLE_COUNT",
    "MULTI_HORIZON_READINESS_STATUS", "FORWARD_KEY_UPGRADE_PLAN_READY", "EFFECT_CLAIM_ALLOWED_COUNT",
    "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT", "RESEARCH_CONCLUSION_STATUS",
    "EFFECTIVENESS_EVIDENCE_STATUS", "TRUE_5DAY_UNIQUE_COVERAGE_MET", "COVERAGE_WINDOW_COMPLETE", "DAILY_TRUST_LEVEL",
    "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "PRICE_FACTOR_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED", "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT",
    "READ_FIRST", "REPORT",
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


def read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def modified_time(path: Path) -> str:
    if not path.exists():
        return ""
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper().replace(".", "-")


def first_value(row: Dict[str, str], names: Iterable[str]) -> str:
    for name in names:
        value = row.get(name, "")
        if str(value).strip() != "":
            return str(value).strip()
    return ""


def to_float(value: object):
    text = str(value or "").strip().replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def source_key_audit(root: Path):
    rows = []
    for _name, rel in FORWARD_SOURCES:
        path = root / rel
        records, fields = read_csv(path)
        lower = {field.lower(): field for field in fields}
        horizons = []
        for horizon, cols in HORIZON_COLUMNS.items():
            if any(col in fields for col in cols):
                horizons.append(horizon)
        ticker_col = lower.get("ticker") or lower.get("symbol") or lower.get("yf_ticker")
        tickers = {norm_ticker(row.get(ticker_col, "")) for row in records} if ticker_col else set()
        tickers.discard("")
        has_signal_id = "signal_snapshot_id" in lower
        has_forward_key = "forward_tracker_link_key" in lower
        has_sim_key = "simulation_link_key" in lower
        has_ticker = bool(ticker_col)
        has_signal_date = "signal_date" in lower
        has_snapshot_date = "snapshot_date" in lower
        has_entry_date = "entry_date" in lower
        has_asof_date = "asof_date" in lower or "as_of_date" in lower
        has_date = has_signal_date or has_snapshot_date or has_entry_date or has_asof_date
        if has_signal_id or has_forward_key:
            status = "HIGH_QUALITY_KEYS_PRESENT"
            notes = "Direct signal or forward link key is available."
        elif has_sim_key:
            status = "MEDIUM_QUALITY_KEYS_PRESENT"
            notes = "Simulation link key is available but not direct signal_snapshot_id."
        elif has_ticker and has_date:
            status = "TICKER_DATE_ONLY"
            notes = "Ticker plus date can support medium-confidence matching if dates align."
        elif has_ticker:
            status = "TICKER_ONLY_LOW_CONFIDENCE"
            notes = "Ticker-only matching is low confidence."
        else:
            status = "UNUSABLE_FOR_SIGNAL_MATCHING"
            notes = "No usable ticker or signal key."
        rows.append(
            {
                "source_path": str(path),
                "source_exists": str(path.exists()).upper(),
                "modified_time": modified_time(path),
                "parsed_row_count": len(records),
                "parsed_ticker_count": len(tickers),
                "has_signal_snapshot_id": str(has_signal_id).upper(),
                "has_forward_tracker_link_key": str(has_forward_key).upper(),
                "has_simulation_link_key": str(has_sim_key).upper(),
                "has_ticker": str(has_ticker).upper(),
                "has_signal_date": str(has_signal_date).upper(),
                "has_snapshot_date": str(has_snapshot_date).upper(),
                "has_entry_date": str(has_entry_date).upper(),
                "has_asof_date": str(has_asof_date).upper(),
                "has_horizon_column": str(bool(horizons)).upper(),
                "detected_horizons": ";".join(horizons),
                "has_forward_return_1d": str("1D" in horizons).upper(),
                "has_forward_return_3d": str("3D" in horizons).upper(),
                "has_forward_return_5d": str("5D" in horizons).upper(),
                "has_forward_return_10d": str("10D" in horizons).upper(),
                "has_forward_return_20d": str("20D" in horizons).upper(),
                "key_quality_status": status,
                "notes": notes,
            }
        )
    return rows


def failure_rows(snapshot_rows, match_rows):
    match_by_id = {row.get("signal_snapshot_id", ""): row for row in match_rows}
    out = []
    for row in snapshot_rows:
        sid = row.get("signal_snapshot_id", "")
        match = match_by_id.get(sid, {})
        status = match.get("match_quality_status", "UNMATCHED_OR_AMBIGUOUS")
        horizons = []
        for horizon in ["1d", "3d", "5d", "10d", "20d"]:
            if match.get(f"forward_return_{horizon}_available") == "TRUE":
                horizons.append(horizon.upper())
        if status == "HIGH_CONFIDENCE_MATCH":
            required = ""
            resolution = "WAIT_FOR_FORWARD_HORIZON_MATURITY" if len(horizons) < 5 else "NO_ACTION_DATA_DEGRADED"
            reason = ""
        elif status == "MEDIUM_CONFIDENCE_MATCH":
            required = "signal_snapshot_id"
            resolution = "ADD_SIGNAL_SNAPSHOT_ID_TO_FORWARD_TRACKER"
            reason = "Matched without direct signal_snapshot_id."
        elif status == "LOW_CONFIDENCE_MATCH":
            required = "signal_snapshot_id_or_forward_tracker_link_key"
            resolution = "ALREADY_MATCHED_LOW_CONFIDENCE"
            reason = "Ticker-only forward outcome match; date/link key absent or not aligned."
        else:
            required = "ticker_and_signal_date_or_signal_snapshot_id"
            resolution = "ADD_SIGNAL_DATE_TO_FORWARD_OUTCOMES"
            reason = "No usable local forward outcome matched this signal row."
        if status != "UNMATCHED_OR_AMBIGUOUS" and not horizons:
            resolution = "ADD_HORIZON_COLUMNS"
            reason = "Matched source has no usable horizon return columns."
        out.append(
            {
                "signal_snapshot_id": sid,
                "ticker": row.get("ticker", ""),
                "snapshot_date": row.get("snapshot_date", ""),
                "simulation_link_key": row.get("simulation_link_key", ""),
                "forward_tracker_link_key": row.get("forward_tracker_link_key", ""),
                "best_available_match_method": match.get("match_method", "none"),
                "best_match_confidence": status,
                "matched_forward_source_path": match.get("forward_source_path", ""),
                "matched_horizons": ";".join(horizons),
                "unmatched_reason": reason,
                "required_key_to_improve_match": required,
                "recommended_resolution": resolution,
            }
        )
    return out


def multi_horizon_plan(horizon_rows):
    by_h = {row["horizon"]: row for row in horizon_rows}
    out = []
    for horizon in ["1D", "3D", "5D", "10D", "20D"]:
        row = by_h.get(horizon, {})
        current = int(float(row.get("usable_forward_return_count", 0) or 0))
        status = row.get("maturity_status", "NO_USABLE_FORWARD_RETURNS")
        needed = max(MINIMUM_SAMPLE_REQUIRED - current, 0)
        if current >= MINIMUM_SAMPLE_REQUIRED and row.get("unique_snapshot_date_count") == "1":
            block = "NEEDS_MORE_SNAPSHOT_DATE_DIVERSITY"
            earliest = "PRELIMINARY_SMALL_SAMPLE"
        elif needed:
            block = "NEEDS_MORE_FORWARD_RETURN_SAMPLES"
            earliest = "INSUFFICIENT_SAMPLE"
        else:
            block = "READY_FOR_PRELIMINARY_READ_ONLY"
            earliest = "MATURE_ENOUGH_FOR_PRELIMINARY_READ"
        out.append(
            {
                "horizon": horizon,
                "current_usable_count": current,
                "target_minimum_count": MINIMUM_SAMPLE_REQUIRED,
                "current_maturity_status": status,
                "required_additional_samples": needed,
                "earliest_possible_maturity_status": earliest,
                "blocking_reason": block,
                "recommended_next_step": "Preserve signal IDs and wait for this horizon to mature." if horizon != "1D" else "Add direct keys and collect another snapshot date before effect claims.",
            }
        )
    return out


def key_upgrade_plan():
    return [
        {
            "target_component": "signal_snapshot",
            "current_key_status": "signal_snapshot_id exists and is unique",
            "required_new_field": "none",
            "expected_benefit": "Stable source of truth for research joins.",
            "implementation_scope": "plan_only_no_change",
            "safety_requirement": "Do not modify existing snapshots in this patch.",
            "recommended_priority": "LOW",
        },
        {
            "target_component": "forward_tracker",
            "current_key_status": "ticker/date fields present but signal_snapshot_id absent",
            "required_new_field": "signal_snapshot_id",
            "expected_benefit": "Convert low-confidence ticker-only matches to high-confidence signal matches.",
            "implementation_scope": "future_controlled_patch",
            "safety_requirement": "Must not alter historical returns without explicit approval.",
            "recommended_priority": "HIGH",
        },
        {
            "target_component": "simulation_linker",
            "current_key_status": "simulation_link_key present for subset",
            "required_new_field": "signal_snapshot_id passthrough",
            "expected_benefit": "Tie simulation rows to immutable signal snapshots.",
            "implementation_scope": "future_controlled_patch",
            "safety_requirement": "Must not modify simulation positions.",
            "recommended_priority": "MEDIUM",
        },
        {
            "target_component": "factor_effectiveness_read_center",
            "current_key_status": "read-only ticker/date fallback",
            "required_new_field": "match_confidence_threshold",
            "expected_benefit": "Exclude low-confidence matches from effect claims by default.",
            "implementation_scope": "future_read_center_patch",
            "safety_requirement": "Research outputs only.",
            "recommended_priority": "HIGH",
        },
        {
            "target_component": "manual_feedback",
            "current_key_status": "no populated manual feedback link keys",
            "required_new_field": "signal_snapshot_id optional reference",
            "expected_benefit": "Enable later manual outcome review by signal.",
            "implementation_scope": "future_optional_patch",
            "safety_requirement": "Must not modify manual state in this patch.",
            "recommended_priority": "LOW",
        },
    ]


def conclusions(values):
    areas = [
        "FORWARD_MATCH_KEY_QUALITY", "MULTI_HORIZON_MATURITY", "FACTOR_PACK_EFFECTIVENESS",
        "TECHNICAL_TIMING_EFFECTIVENESS", "PRICE_DERIVED_EFFECTIVENESS", "SIMULATION_RESEARCH_READINESS",
        "NEXT_INFRASTRUCTURE_STEP",
    ]
    out = []
    for area in areas:
        if area == "FORWARD_MATCH_KEY_QUALITY":
            summary = f"{values['LOW_CONFIDENCE_MATCH_COUNT']} low-confidence matches and {values['HIGH_CONFIDENCE_MATCH_COUNT']} high-confidence matches."
            next_step = "Add signal_snapshot_id or forward_tracker_link_key to forward outcome rows."
        elif area == "MULTI_HORIZON_MATURITY":
            summary = "Only 1D currently has usable returns; 3D/5D/10D/20D are not mature."
            next_step = "Wait for multi-horizon returns to mature and retain direct keys."
        elif area == "NEXT_INFRASTRUCTURE_STEP":
            summary = "Plan is ready; no data or state changes applied."
            next_step = "Implement a separate controlled key propagation patch only if explicitly approved."
        else:
            summary = "Effectiveness evidence remains preliminary and cannot support factor claims."
            next_step = "Use the maturity and key-quality filters before any future analysis."
        out.append(
            {
                "conclusion_area": area,
                "conclusion_status": "PLAN_READY_NO_EFFECT_CLAIMS",
                "evidence_level": "LOW",
                "match_quality_status": "LOW_CONFIDENCE_DOMINANT",
                "horizon_maturity_status": values["MULTI_HORIZON_READINESS_STATUS"],
                "effect_claim_allowed": "FALSE",
                "weight_change_allowed": "FALSE",
                "production_change_allowed": "FALSE",
                "summary": summary,
                "recommended_next_step": next_step,
            }
        )
    return out


def report_text(values: Dict[str, object]) -> str:
    return f"""# V18.21C-R2 Forward Match Key Quality Report

## Executive summary
Status: {values['STATUS']}. R2 diagnoses low-confidence forward matching and creates a multi-horizon readiness/key-upgrade plan.

## Safety statement
This is advisory-only and plan-only. It does not modify signal snapshots, forward tracker files, simulation positions, prices, ranking, promotion/demotion, official decisions, auto-trade, or auto-sell. External data fetched: FALSE.

## Forward source key availability summary
High-quality sources: {values['HIGH_QUALITY_FORWARD_SOURCE_COUNT']}; medium-quality: {values['MEDIUM_QUALITY_FORWARD_SOURCE_COUNT']}; ticker/date-only: {values['TICKER_DATE_ONLY_SOURCE_COUNT']}; ticker-only low confidence: {values['TICKER_ONLY_LOW_CONFIDENCE_SOURCE_COUNT']}; unusable: {values['UNUSABLE_FORWARD_SOURCE_COUNT']}.

## Match failure reason summary
High-confidence matches: {values['HIGH_CONFIDENCE_MATCH_COUNT']}; medium: {values['MEDIUM_CONFIDENCE_MATCH_COUNT']}; low: {values['LOW_CONFIDENCE_MATCH_COUNT']}; unmatched/ambiguous: {values['UNMATCHED_OR_AMBIGUOUS_COUNT']}.

## Multi-horizon readiness plan
1D usable count: {values['HORIZON_1D_USABLE_COUNT']}. 3D/5D/10D/20D usable counts: {values['HORIZON_3D_USABLE_COUNT']}/{values['HORIZON_5D_USABLE_COUNT']}/{values['HORIZON_10D_USABLE_COUNT']}/{values['HORIZON_20D_USABLE_COUNT']}. Status: {values['MULTI_HORIZON_READINESS_STATUS']}.

## Forward research key upgrade plan
The plan recommends future direct key propagation, especially `signal_snapshot_id` into forward tracker/outcome rows. This patch does not apply it.

## Conservative research conclusion
No factor effectiveness claims are allowed. Weight changes and production promotions remain disallowed.

## Why no factor effectiveness claims are allowed
The current evidence is dominated by low-confidence ticker-only matches and a single usable horizon.

## Validation summary
Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

## Next-step recommendation
Run a separate, explicitly approved key propagation implementation later; then let additional horizons mature before re-evaluating factors.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/factor_effectiveness"
    ops_dir = root / "outputs/v18/ops"

    source_path = out_dir / "V18_21C_R2_CURRENT_FORWARD_SOURCE_KEY_AVAILABILITY_AUDIT.csv"
    failure_path = out_dir / "V18_21C_R2_CURRENT_MATCH_FAILURE_REASON_AUDIT.csv"
    horizon_plan_path = out_dir / "V18_21C_R2_CURRENT_MULTI_HORIZON_READINESS_PLAN.csv"
    upgrade_path = out_dir / "V18_21C_R2_CURRENT_FORWARD_RESEARCH_KEY_UPGRADE_PLAN.csv"
    conclusion_path = out_dir / "V18_21C_R2_CURRENT_RESEARCH_CONCLUSION_SUMMARY.csv"
    read_first_path = ops_dir / "V18_21C_R2_READ_FIRST.txt"
    report_path = ops_dir / "V18_21C_R2_CURRENT_FORWARD_MATCH_KEY_QUALITY_REPORT.md"

    base_rf = read_first(root / "outputs/v18/ops/V18_21C_R1_READ_FIRST.txt")
    signal_rows, _ = read_csv(root / "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv")
    match_rows, _ = read_csv(root / "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_FORWARD_MATCH_QUALITY_AUDIT.csv")
    maturity_rows, _ = read_csv(root / "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_HORIZON_MATURITY_AUDIT.csv")

    source_rows = source_key_audit(root)
    failure = failure_rows(signal_rows, match_rows)
    horizon_plan = multi_horizon_plan(maturity_rows)
    upgrade = key_upgrade_plan()

    source_counts = Counter(row["key_quality_status"] for row in source_rows)
    multi_status = "NOT_READY_MULTI_HORIZON" if any(row["current_usable_count"] == 0 for row in horizon_plan if row["horizon"] != "1D") else "PRELIMINARY_MULTI_HORIZON_READY"
    values: Dict[str, object] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "POLICY_APPLIED": "FALSE",
        "SIGNAL_SNAPSHOT_ROW_COUNT": base_rf.get("SIGNAL_SNAPSHOT_ROW_COUNT", str(len(signal_rows))),
        "SIGNAL_SNAPSHOT_HISTORY_COUNT": base_rf.get("SIGNAL_SNAPSHOT_HISTORY_COUNT", ""),
        "FORWARD_OUTCOME_SOURCE_COUNT": base_rf.get("FORWARD_OUTCOME_SOURCE_COUNT", str(len(source_rows))),
        "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT": base_rf.get("FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT", ""),
        "HIGH_CONFIDENCE_MATCH_COUNT": base_rf.get("HIGH_CONFIDENCE_MATCH_COUNT", "0"),
        "MEDIUM_CONFIDENCE_MATCH_COUNT": base_rf.get("MEDIUM_CONFIDENCE_MATCH_COUNT", "0"),
        "LOW_CONFIDENCE_MATCH_COUNT": base_rf.get("LOW_CONFIDENCE_MATCH_COUNT", "0"),
        "UNMATCHED_OR_AMBIGUOUS_COUNT": base_rf.get("UNMATCHED_OR_AMBIGUOUS_COUNT", "0"),
        "HIGH_QUALITY_FORWARD_SOURCE_COUNT": str(source_counts["HIGH_QUALITY_KEYS_PRESENT"]),
        "MEDIUM_QUALITY_FORWARD_SOURCE_COUNT": str(source_counts["MEDIUM_QUALITY_KEYS_PRESENT"]),
        "TICKER_DATE_ONLY_SOURCE_COUNT": str(source_counts["TICKER_DATE_ONLY"]),
        "TICKER_ONLY_LOW_CONFIDENCE_SOURCE_COUNT": str(source_counts["TICKER_ONLY_LOW_CONFIDENCE"]),
        "UNUSABLE_FORWARD_SOURCE_COUNT": str(source_counts["UNUSABLE_FOR_SIGNAL_MATCHING"]),
        "HORIZON_1D_USABLE_COUNT": base_rf.get("HORIZON_1D_USABLE_COUNT", "0"),
        "HORIZON_3D_USABLE_COUNT": base_rf.get("HORIZON_3D_USABLE_COUNT", "0"),
        "HORIZON_5D_USABLE_COUNT": base_rf.get("HORIZON_5D_USABLE_COUNT", "0"),
        "HORIZON_10D_USABLE_COUNT": base_rf.get("HORIZON_10D_USABLE_COUNT", "0"),
        "HORIZON_20D_USABLE_COUNT": base_rf.get("HORIZON_20D_USABLE_COUNT", "0"),
        "MULTI_HORIZON_READINESS_STATUS": multi_status,
        "FORWARD_KEY_UPGRADE_PLAN_READY": "TRUE",
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
        "RESEARCH_CONCLUSION_STATUS": "PLAN_READY_NO_EFFECT_CLAIMS",
        "EFFECTIVENESS_EVIDENCE_STATUS": "KEY_QUALITY_LOW_AND_MULTI_HORIZON_IMMATURE",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": base_rf.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", ""),
        "COVERAGE_WINDOW_COMPLETE": base_rf.get("COVERAGE_WINDOW_COMPLETE", ""),
        "DAILY_TRUST_LEVEL": base_rf.get("DAILY_TRUST_LEVEL", ""),
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }
    conclusion_rows = conclusions(values)

    write_csv(source_path, source_rows, [
        "source_path", "source_exists", "modified_time", "parsed_row_count", "parsed_ticker_count", "has_signal_snapshot_id",
        "has_forward_tracker_link_key", "has_simulation_link_key", "has_ticker", "has_signal_date", "has_snapshot_date",
        "has_entry_date", "has_asof_date", "has_horizon_column", "detected_horizons", "has_forward_return_1d",
        "has_forward_return_3d", "has_forward_return_5d", "has_forward_return_10d", "has_forward_return_20d",
        "key_quality_status", "notes",
    ])
    write_csv(failure_path, failure, [
        "signal_snapshot_id", "ticker", "snapshot_date", "simulation_link_key", "forward_tracker_link_key",
        "best_available_match_method", "best_match_confidence", "matched_forward_source_path", "matched_horizons",
        "unmatched_reason", "required_key_to_improve_match", "recommended_resolution",
    ])
    write_csv(horizon_plan_path, horizon_plan, [
        "horizon", "current_usable_count", "target_minimum_count", "current_maturity_status", "required_additional_samples",
        "earliest_possible_maturity_status", "blocking_reason", "recommended_next_step",
    ])
    write_csv(upgrade_path, upgrade, [
        "target_component", "current_key_status", "required_new_field", "expected_benefit", "implementation_scope",
        "safety_requirement", "recommended_priority",
    ])
    write_csv(conclusion_path, conclusion_rows, [
        "conclusion_area", "conclusion_status", "evidence_level", "match_quality_status", "horizon_maturity_status",
        "effect_claim_allowed", "weight_change_allowed", "production_change_allowed", "summary", "recommended_next_step",
    ])

    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))
    fail_count = 0
    for path in [source_path, failure_path, horizon_plan_path, upgrade_path, conclusion_path, read_first_path, report_path]:
        if not path.exists():
            fail_count += 1
    for field in READ_FIRST_FIELDS:
        if field not in values:
            fail_count += 1
    if values["WEIGHT_CHANGE_ALLOWED_COUNT"] != "0" or values["PRODUCTION_PROMOTION_ALLOWED_COUNT"] != "0":
        fail_count += 1
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT", "HIGH_CONFIDENCE_MATCH_COUNT",
        "MEDIUM_CONFIDENCE_MATCH_COUNT", "LOW_CONFIDENCE_MATCH_COUNT", "UNMATCHED_OR_AMBIGUOUS_COUNT",
        "HIGH_QUALITY_FORWARD_SOURCE_COUNT", "TICKER_DATE_ONLY_SOURCE_COUNT", "MULTI_HORIZON_READINESS_STATUS",
        "FORWARD_KEY_UPGRADE_PLAN_READY", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
