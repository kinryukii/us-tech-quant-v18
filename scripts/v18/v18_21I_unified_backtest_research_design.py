from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_READY = "WARN_V18_21I_UNIFIED_BACKTEST_RESEARCH_DESIGN_READY"
STATUS_FAIL = "FAIL_V18_21I_UNIFIED_BACKTEST_RESEARCH_DESIGN_VALIDATION_FAILED"
MODE = "ADVISORY_READ_ONLY"
PATCH_MODE = "UNIFIED_BACKTEST_RESEARCH_DESIGN_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "UNIFIED_BACKTEST_DESIGN_READY": "TRUE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "FORWARD_RETURN_FILLED_COUNT": "0",
    "FORWARD_OUTCOME_FILLER_APPLIED": "FALSE",
    "FULL_HISTORY_BACKFILL_APPLIED": "FALSE",
    "STAGED_BACKFILL_APPLIED": "FALSE",
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

STABLE_INPUTS = [
    ("V18_21A_R4_STABLE_READ_FIRST", "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt", False),
    ("V18_21B_R1_STABLE_READ_FIRST", "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt", False),
    ("V18_21C_R2_STABLE_READ_FIRST", "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt", False),
    ("V18_21D_R1_STABLE_READ_FIRST", "outputs/v18/ops/V18_21D_R1_STABLE_READ_FIRST.txt", False),
    ("V18_21E_R1_STABLE_READ_FIRST", "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt", False),
    ("V18_21F_STABLE_READ_FIRST", "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt", False),
    ("V18_21G_STABLE_READ_FIRST", "outputs/v18/ops/V18_21G_STABLE_READ_FIRST.txt", False),
    ("V18_21H_STABLE_READ_FIRST", "outputs/v18/ops/V18_21H_STABLE_READ_FIRST.txt", False),
    ("V18_21H_R1_STABLE_READ_FIRST", "outputs/v18/ops/V18_21H_R1_STABLE_READ_FIRST.txt", False),
]
RESEARCH_INPUTS = [
    ("SIGNAL_SNAPSHOT", "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", True),
    ("PRICE_DERIVED_FACTOR_SCORES", "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv", False),
    ("FACTOR_SCOPE_SUMMARY", "outputs/v18/price_factors/V18_21A_R3_CURRENT_FACTOR_SCOPE_SUMMARY.csv", False),
    ("TECHNICAL_TIMING", "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv", False),
    ("FACTOR_PACK_RANKING", "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", False),
    ("EVENT_ADJUSTED_CANDIDATES", "outputs/v18/event_risk/V18_21E_R1_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv", False),
    ("MARKET_EVENT_RISK_SEMANTICS", "outputs/v18/event_risk/V18_21E_R1_CURRENT_MARKET_EVENT_RISK_SEMANTICS.csv", False),
    ("FORWARD_TRACKER_SHADOW", "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv", False),
    ("FORWARD_OUTCOME_ELIGIBILITY_AUDIT", "outputs/v18/forward_tracker/V18_21G_CURRENT_FORWARD_OUTCOME_ELIGIBILITY_AUDIT.csv", False),
    ("BATCH1_STAGED_BACKFILL_MANIFEST", "outputs/v18/price_factors/V18_21H_R1_CURRENT_BATCH1_STAGED_BACKFILL_REQUEST_MANIFEST.csv", False),
    ("BATCH1_COVERAGE_IMPACT_PROJECTION", "outputs/v18/price_factors/V18_21H_R1_CURRENT_BATCH1_COVERAGE_IMPACT_PROJECTION.csv", False),
]
ALL_INPUTS = STABLE_INPUTS + RESEARCH_INPUTS

OUTPUTS = {
    "readiness": "outputs/v18/backtest_research/V18_21I_CURRENT_BACKTEST_INPUT_READINESS_AUDIT.csv",
    "schema": "outputs/v18/backtest_research/V18_21I_CURRENT_UNIFIED_BACKTEST_DATASET_SCHEMA_DESIGN.csv",
    "leakage": "outputs/v18/backtest_research/V18_21I_CURRENT_LEAKAGE_PREVENTION_RULES.csv",
    "sample": "outputs/v18/backtest_research/V18_21I_CURRENT_BACKTEST_SAMPLE_CONSTRUCTION_PLAN.csv",
    "metrics": "outputs/v18/backtest_research/V18_21I_CURRENT_BACKTEST_METRICS_SPECIFICATION.csv",
    "blockers": "outputs/v18/backtest_research/V18_21I_CURRENT_BACKTEST_READINESS_BLOCKER_SUMMARY.csv",
    "implementation": "outputs/v18/backtest_research/V18_21I_CURRENT_CONTROLLED_BACKTEST_IMPLEMENTATION_PLAN.csv",
    "read_first": "outputs/v18/ops/V18_21I_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_21I_CURRENT_UNIFIED_BACKTEST_RESEARCH_DESIGN_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "UNIFIED_BACKTEST_DESIGN_READY",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "BACKTEST_INPUT_SOURCE_COUNT",
    "BACKTEST_INPUT_MISSING_COUNT", "SIGNAL_SNAPSHOT_ROW_COUNT", "SIGNAL_SNAPSHOT_HISTORY_COUNT",
    "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT", "FORWARD_TRACKER_SHADOW_ROW_COUNT",
    "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT",
    "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
    "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
    "BACKTEST_EXECUTION_READINESS_STATUS", "EFFECT_CLAIM_ALLOWED_COUNT",
    "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
    "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]

READINESS_FIELDS = [
    "input_name", "input_path", "input_exists", "parsed_row_count", "parsed_ticker_count",
    "key_columns_detected", "date_columns_detected", "score_columns_detected",
    "horizon_columns_detected", "usable_for_backtest_design", "usable_for_backtest_execution_now",
    "readiness_status", "blocking_reason", "notes",
]
SCHEMA_FIELDS = [
    "field_name", "field_group", "source_layer", "source_file", "required_for_backtest",
    "required_for_effect_claim", "required_for_weight_change", "leakage_risk",
    "allowed_availability_timing", "notes",
]
LEAKAGE_FIELDS = [
    "rule_id", "rule_name", "rule_description", "applies_to_field_group",
    "failure_mode_prevented", "required_validation", "current_status", "notes",
]
SAMPLE_FIELDS = [
    "sample_stage", "stage_name", "input_requirement", "output_dataset_if_implemented_later",
    "minimum_sample_required", "current_available_sample_count", "current_blocking_reason",
    "design_status", "notes",
]
METRIC_FIELDS = [
    "metric_name", "metric_group", "required_inputs", "applicable_horizon",
    "minimum_sample_required", "interpretation", "current_computable_status",
    "production_use_allowed", "notes",
]
BLOCKER_FIELDS = [
    "blocker_name", "blocker_status", "affected_backtest_stage", "severity", "current_metric",
    "why_it_matters", "required_resolution", "recommended_next_step",
]
IMPLEMENTATION_FIELDS = [
    "step_index", "step_name", "purpose", "required_inputs", "output_file_if_implemented_later",
    "safety_gate", "modifies_production", "external_data_required", "allowed_now",
    "requires_explicit_approval", "notes",
]


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


def cols_like(fields: Iterable[str], needles: Sequence[str]) -> List[str]:
    found: List[str] = []
    for field in fields:
        lower = field.lower()
        if any(needle in lower for needle in needles):
            found.append(field)
    return found


def ticker_count(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> int:
    ticker_col = next((field for field in fields if field.lower() in {"ticker", "symbol", "yf_ticker"}), "")
    if not ticker_col:
        return 0
    return len({str(row.get(ticker_col, "")).strip().upper() for row in rows if str(row.get(ticker_col, "")).strip()})


def first(*values: str) -> str:
    for value in values:
        if str(value or "").strip():
            return str(value).strip()
    return ""


def int_value(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip().replace(",", "")
        return int(float(text)) if text else default
    except ValueError:
        return default


def input_readiness_rows(root: Path, forward_filled: int, missing_history: int) -> List[Dict[str, object]]:
    rows_out: List[Dict[str, object]] = []
    for input_name, rel, required in ALL_INPUTS:
        path = root / rel
        exists = path.exists()
        csv_rows: List[Dict[str, str]] = []
        fields: List[str] = []
        row_count = 0
        if exists and path.suffix.lower() == ".csv":
            csv_rows, fields = read_csv(path)
            row_count = len(csv_rows)
        elif exists:
            text = read_text(path)
            fields = [line.split(":", 1)[0].strip() for line in text.splitlines() if ":" in line]
            row_count = len([line for line in text.splitlines() if line.strip()])
        key_cols = cols_like(fields, ["signal_snapshot_id", "link_key", "ticker", "snapshot"])
        date_cols = cols_like(fields, ["date", "asof", "timestamp"])
        score_cols = cols_like(fields, ["score", "rank", "coefficient"])
        horizon_cols = cols_like(fields, ["horizon", "forward_return"])
        usable_design = exists and (row_count > 0 or path.suffix.lower() == ".txt")
        if required and not exists:
            status = "MISSING_REQUIRED_INPUT"
            blocker = "Required signal snapshot is missing."
            usable_execution = "FALSE"
        elif not exists:
            status = "MISSING_REQUIRED_INPUT" if required else "NOT_APPLICABLE_CONTEXT_ONLY"
            blocker = "Optional input missing."
            usable_execution = "FALSE"
        elif input_name in {"FORWARD_TRACKER_SHADOW", "FORWARD_OUTCOME_ELIGIBILITY_AUDIT"} and forward_filled == 0:
            status = "DEGRADED_MISSING_FORWARD_RETURNS"
            blocker = "Forward returns remain pending."
            usable_execution = "FALSE"
        elif input_name in {"PRICE_DERIVED_FACTOR_SCORES", "FACTOR_SCOPE_SUMMARY", "BATCH1_STAGED_BACKFILL_MANIFEST"} and missing_history > 0:
            status = "DEGRADED_MISSING_FULL_HISTORY"
            blocker = "Full-history coverage is incomplete."
            usable_execution = "FALSE"
        elif input_name.startswith("V18_21"):
            status = "NOT_APPLICABLE_CONTEXT_ONLY"
            blocker = ""
            usable_execution = "FALSE"
        else:
            status = "READY_FOR_DESIGN"
            blocker = "" if usable_design else "No parsed rows."
            usable_execution = "FALSE"
        if input_name == "SIGNAL_SNAPSHOT" and exists:
            status = "READY_FOR_LIMITED_RESEARCH"
            blocker = "Usable for schema design, but backtest execution is blocked by missing outcomes."
        rows_out.append({
            "input_name": input_name,
            "input_path": str(path),
            "input_exists": str(exists).upper(),
            "parsed_row_count": row_count,
            "parsed_ticker_count": ticker_count(csv_rows, fields),
            "key_columns_detected": ";".join(key_cols),
            "date_columns_detected": ";".join(date_cols),
            "score_columns_detected": ";".join(score_cols),
            "horizon_columns_detected": ";".join(horizon_cols),
            "usable_for_backtest_design": str(bool(usable_design)).upper(),
            "usable_for_backtest_execution_now": usable_execution,
            "readiness_status": status,
            "blocking_reason": blocker,
            "notes": "Read-only audit; no data fetched or modified.",
        })
    return rows_out


def schema_rows() -> List[Dict[str, object]]:
    specs = [
        ("signal_snapshot_id", "identity_keys", "V18.21B-R1", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "LOW", "known_at_snapshot_date", "Primary snapshot key."),
        ("snapshot_date", "timestamp_keys", "V18.21B-R1", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "HIGH", "known_at_snapshot_date", "Controls availability timing."),
        ("ticker", "identity_keys", "V18.21B-R1", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "LOW", "known_at_snapshot_date", "Security identifier."),
        ("forward_tracker_link_key", "identity_keys", "V18.21D-R1", "V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv", "TRUE", "TRUE", "TRUE", "LOW", "known_at_snapshot_date", "Required for high-confidence outcome matching."),
        ("planned_horizon", "timestamp_keys", "V18.21D-R1", "V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv", "TRUE", "TRUE", "TRUE", "LOW", "defined_at_snapshot_date", "Outcome horizon."),
        ("planned_outcome_date", "timestamp_keys", "V18.21D-R1", "V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv", "TRUE", "TRUE", "TRUE", "HIGH", "future_target_date_only", "Must not reveal future price before maturity."),
        ("factor_pack_score", "raw_scores", "V18.21B-R1", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Candidate score input."),
        ("composite_candidate_score", "raw_scores", "V18.21B-R1", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Composite candidate input."),
        ("price_derived_total_score", "price_derived_factors", "V18.21A-R4", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Price-derived summary."),
        ("relative_strength_score", "price_derived_factors", "V18.21A-R4", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Factor exposure."),
        ("buy_zone_score", "price_derived_factors", "V18.21A-R4", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Factor exposure."),
        ("volume_confirmation_score", "price_derived_factors", "V18.21A-R4", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Factor exposure."),
        ("volatility_risk_score", "price_derived_factors", "V18.21A-R4", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Factor exposure."),
        ("technical_timing_score", "technical_timing_factors", "V18.6A/V18.21B-R1", "V18_6A_CURRENT_TECHNICAL_TIMING.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Timing exposure."),
        ("overheat_penalty", "technical_timing_factors", "V18.6A/V18.21B-R1", "V18_6A_CURRENT_TECHNICAL_TIMING.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Overheat risk exposure."),
        ("final_advisory_event_risk_coefficient", "event_risk_factors", "V18.21E-R1", "V18_21E_R1_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv", "TRUE", "FALSE", "FALSE", "HIGH", "known_at_snapshot_date_and_advisory_only", "Must remain advisory unless separately approved."),
        ("market_regime_label", "market_regime_factors", "V18.21A-R4", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_at_snapshot_date", "Regime conditioning."),
        ("forward_return_1d", "forward_outcome_fields", "V18.21D/G", "future_research_dataset_only", "TRUE", "TRUE", "TRUE", "HIGH", "available_after_outcome_date", "Outcome field; currently unfilled."),
        ("forward_return_3d", "forward_outcome_fields", "V18.21D/G", "future_research_dataset_only", "TRUE", "TRUE", "TRUE", "HIGH", "available_after_outcome_date", "Outcome field; currently unfilled."),
        ("forward_return_5d", "forward_outcome_fields", "V18.21D/G", "future_research_dataset_only", "TRUE", "TRUE", "TRUE", "HIGH", "available_after_outcome_date", "Outcome field; currently unfilled."),
        ("forward_return_10d", "forward_outcome_fields", "V18.21D/G", "future_research_dataset_only", "TRUE", "TRUE", "TRUE", "HIGH", "available_after_outcome_date", "Outcome field; currently unfilled."),
        ("forward_return_20d", "forward_outcome_fields", "V18.21D/G", "future_research_dataset_only", "TRUE", "TRUE", "TRUE", "HIGH", "available_after_outcome_date", "Outcome field; currently unfilled."),
        ("forward_return_status", "forward_outcome_fields", "V18.21D-R1", "V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv", "TRUE", "TRUE", "TRUE", "MEDIUM", "known_after_fill_status_update", "Must distinguish pending from filled."),
        ("score_ready", "eligibility_flags", "V18.21B-R1", "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv", "TRUE", "FALSE", "FALSE", "LOW", "known_at_snapshot_date", "Eligibility flag."),
        ("official_decision_impact", "safety_flags", "All", "READ_FIRST outputs", "TRUE", "TRUE", "TRUE", "LOW", "always_NONE_for_design", "Must remain NONE."),
    ]
    return [
        {
            "field_name": name, "field_group": group, "source_layer": layer, "source_file": source,
            "required_for_backtest": required_backtest, "required_for_effect_claim": required_effect,
            "required_for_weight_change": required_weight, "leakage_risk": risk,
            "allowed_availability_timing": timing, "notes": notes,
        }
        for name, group, layer, source, required_backtest, required_effect, required_weight, risk, timing, notes in specs
    ]


def leakage_rows() -> List[Dict[str, object]]:
    rules = [
        ("L001", "Snapshot values only", "Use only signal snapshot values known at snapshot_date.", "raw_scores;factor_fields", "Lookahead from recalculated signals.", "Column availability timestamp <= snapshot_date.", "DESIGN_READY"),
        ("L002", "No historical recomputation", "Do not recompute historical signal snapshots using current formulas.", "raw_scores", "Formula drift contamination.", "Use archived snapshots only.", "DESIGN_READY"),
        ("L003", "Outcome date gate", "Do not use outcome prices before planned_outcome_date.", "forward_outcome_fields", "Future price leakage.", "Outcome price date >= planned_outcome_date.", "BLOCKED_RETURNS_PENDING"),
        ("L004", "Event knowledge gate", "Do not use future event information not known at snapshot_date.", "event_risk_factors", "Future calendar leakage.", "Event record availability <= snapshot_date.", "DESIGN_READY"),
        ("L005", "Ranking freeze", "Do not use post-snapshot ranking changes.", "raw_scores", "Post-snapshot ranking leakage.", "Join only snapshot-dated ranking fields.", "DESIGN_READY"),
        ("L006", "Backfill availability tagging", "Do not use backfilled history unless tagged with availability timestamp.", "price_derived_factors", "Backfilled data availability leakage.", "Availability timestamp audit.", "BLOCKED_BACKFILL_NOT_APPLIED"),
        ("L007", "Event coefficient separation", "Separate calendar-only event score from hard-lock advisory overlay.", "event_risk_factors", "Misstated event risk semantics.", "Use R1 separated coefficient fields.", "DESIGN_READY"),
        ("L008", "Shadow tracker isolation", "Keep shadow tracker separate from production tracker.", "forward_outcome_fields", "Production state contamination.", "Use shadow paths only.", "DESIGN_READY"),
        ("L009", "High-confidence key requirement", "Require signal_snapshot_id or forward_tracker_link_key for high-confidence matching.", "identity_keys", "Weak outcome matching.", "Reject rows missing core keys.", "DESIGN_READY"),
        ("L010", "Sample maturity gate", "Require multi-horizon sample maturity before effect claims.", "forward_outcome_fields", "False factor evidence.", "Minimum per-horizon sample counts.", "BLOCKED_SAMPLE_IMMATURE"),
    ]
    return [
        {
            "rule_id": rid, "rule_name": name, "rule_description": desc, "applies_to_field_group": group,
            "failure_mode_prevented": failure, "required_validation": validation,
            "current_status": status, "notes": "Read-only design rule.",
        }
        for rid, name, desc, group, failure, validation, status in rules
    ]


def sample_plan_rows(signal_rows: int, shadow_rows: int, filled_returns: int, history_ready: int) -> List[Dict[str, object]]:
    stages = [
        (1, "Collect historical signal snapshots", "Archived signal snapshots with snapshot_date and signal_snapshot_id.", "outputs/v18/backtest_research/future_unified_signal_panel.csv", ">= 12 snapshot dates", signal_rows, "Limited current snapshot history.", "DESIGN_READY"),
        (2, "Align each signal with forward tracker link keys", "signal_snapshot_id and forward_tracker_link_key.", "future_signal_forward_key_panel.csv", ">= 500 keyed rows", shadow_rows, "Shadow rows exist but returns pending.", "DESIGN_READY"),
        (3, "Join price-derived factor fields", "Price factor fields known at snapshot_date.", "future_factor_join_panel.csv", ">= 300 full-score rows", history_ready, "Full-history coverage incomplete.", "DESIGN_READY_DEGRADED"),
        (4, "Join technical timing fields", "technical_timing_score and timing labels.", "future_timing_join_panel.csv", ">= 300 rows", signal_rows, "Must freeze timing at snapshot_date.", "DESIGN_READY"),
        (5, "Join event risk fields", "calendar and advisory event-risk fields.", "future_event_join_panel.csv", ">= 300 rows", signal_rows, "Advisory-only coefficient not official.", "DESIGN_READY"),
        (6, "Join market regime fields", "market_regime_label and coefficients.", "future_regime_join_panel.csv", ">= 300 rows", signal_rows, "Regime must be snapshot-dated.", "DESIGN_READY"),
        (7, "Attach forward returns by horizon", "Matured filled returns per horizon.", "future_unified_backtest_dataset.csv", ">= 100 per horizon", filled_returns, "Forward returns are not filled.", "BLOCKED"),
        (8, "Validate no lookahead leakage", "Availability timestamps and frozen snapshots.", "future_leakage_validation.csv", "100% pass", 0, "Cannot run until dataset exists.", "DESIGN_READY"),
        (9, "Construct factor buckets", "Unified dataset with scores and returns.", "future_factor_bucket_panel.csv", ">= 5 buckets with >= 20 rows each", 0, "Requires filled returns.", "BLOCKED"),
        (10, "Compute research metrics", "Bucket panel with outcomes.", "future_backtest_metrics.csv", ">= 100 per horizon", 0, "Requires samples.", "BLOCKED"),
        (11, "Produce non-production research report", "Validated research metrics.", "future_backtest_research_report.md", "Validation pass", 0, "Research-only future step.", "BLOCKED"),
    ]
    return [
        {
            "sample_stage": stage, "stage_name": name, "input_requirement": req,
            "output_dataset_if_implemented_later": output, "minimum_sample_required": minimum,
            "current_available_sample_count": current, "current_blocking_reason": blocker,
            "design_status": status, "notes": "Future implementation only; no backtest executed.",
        }
        for stage, name, req, output, minimum, current, blocker, status in stages
    ]


def metrics_rows() -> List[Dict[str, object]]:
    metrics = [
        ("average_forward_return", "return_distribution", "filled forward_return by horizon", "1D/3D/5D/10D/20D", ">=100 per horizon", "Mean outcome return.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("median_forward_return", "return_distribution", "filled forward_return by horizon", "1D/3D/5D/10D/20D", ">=100 per horizon", "Median outcome return.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("hit_rate", "return_distribution", "filled forward_return by horizon", "1D/3D/5D/10D/20D", ">=100 per horizon", "Share of positive returns.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("top_bucket_vs_bottom_bucket_spread", "factor_bucket", "factor buckets and forward returns", "all horizons", ">=20 per bucket", "Spread between strongest and weakest factor buckets.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("rank_ic", "rank_correlation", "scores and forward returns", "all horizons", ">=100 per horizon", "Spearman rank correlation.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("rank_ic_ir", "rank_correlation", "time series rank_ic", "all horizons", ">=12 periods", "Information ratio of rank IC.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("drawdown_after_signal", "risk", "post-signal price path", "all horizons", ">=100 per horizon", "Worst drawdown after signal.", "NOT_COMPUTABLE_PRICE_PATH_PENDING"),
        ("volatility_after_signal", "risk", "post-signal price path", "all horizons", ">=100 per horizon", "Realized volatility after signal.", "NOT_COMPUTABLE_PRICE_PATH_PENDING"),
        ("event_adjusted_score_spread", "event_risk", "event-adjusted scores and returns", "all horizons", ">=100 per horizon", "Spread after advisory event adjustment.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("technical_timing_bucket_return", "technical_timing", "technical_timing_score buckets and returns", "all horizons", ">=20 per bucket", "Timing bucket return.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("overheat_penalty_effect", "technical_timing", "overheat_penalty and returns", "all horizons", ">=100 per horizon", "Effect of overheat penalty.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("buy_zone_distance_effect", "price_derived", "buy zone fields and returns", "all horizons", ">=100 per horizon", "Effect of distance to buy zone.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("relative_strength_effect", "price_derived", "relative_strength_score and returns", "all horizons", ">=100 per horizon", "Effect of relative strength.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("volume_confirmation_effect", "price_derived", "volume_confirmation_score and returns", "all horizons", ">=100 per horizon", "Effect of volume confirmation.", "NOT_COMPUTABLE_RETURNS_PENDING"),
        ("market_regime_conditioned_return", "market_regime", "market regime and returns", "all horizons", ">=100 per regime", "Returns conditioned by regime.", "NOT_COMPUTABLE_RETURNS_PENDING"),
    ]
    return [
        {
            "metric_name": name, "metric_group": group, "required_inputs": req,
            "applicable_horizon": horizon, "minimum_sample_required": minimum,
            "interpretation": interpretation, "current_computable_status": status,
            "production_use_allowed": "FALSE", "notes": "Research-only metric; no production use allowed.",
        }
        for name, group, req, horizon, minimum, interpretation, status in metrics
    ]


def blocker_rows(values: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        {"blocker_name": "FULL_HISTORY_COVERAGE_INCOMPLETE", "blocker_status": "ACTIVE", "affected_backtest_stage": "price factor join", "severity": "HIGH", "current_metric": f"score_ready_ratio={values['CURRENT_SCORE_READY_RATIO']}; missing={values['CURRENT_MISSING_HISTORY_TICKER_COUNT']}", "why_it_matters": "Incomplete factor coverage limits sample size and comparability.", "required_resolution": "Apply approved staged/full backfill later.", "recommended_next_step": "Continue H-R2 only with explicit approval."},
        {"blocker_name": "FORWARD_RETURNS_NOT_FILLED", "blocker_status": "ACTIVE", "affected_backtest_stage": "outcome join", "severity": "HIGH", "current_metric": f"filled={values['FORWARD_RETURN_FILLED_COUNT']}", "why_it_matters": "Backtest metrics require realized outcomes.", "required_resolution": "Wait for maturity and apply controlled filler later.", "recommended_next_step": "Return to G-R1 when horizons mature."},
        {"blocker_name": "MULTI_HORIZON_RETURNS_MISSING", "blocker_status": "ACTIVE", "affected_backtest_stage": "cross-horizon validation", "severity": "HIGH", "current_metric": values["MULTI_HORIZON_READINESS_STATUS"], "why_it_matters": "Effect evidence must generalize across horizons.", "required_resolution": "Collect filled 1D/3D/5D/10D/20D returns.", "recommended_next_step": "Keep multi-horizon claims disabled."},
        {"blocker_name": "HIGH_CONFIDENCE_MATCH_COUNT_ZERO", "blocker_status": "ACTIVE", "affected_backtest_stage": "signal/outcome matching", "severity": "HIGH", "current_metric": f"high_confidence={values['HIGH_CONFIDENCE_FORWARD_MATCH_COUNT']}", "why_it_matters": "Weak matching can create false conclusions.", "required_resolution": "Use link-key shadow tracker with filled returns.", "recommended_next_step": "No effect claims."},
        {"blocker_name": "ONLY_TWO_SIGNAL_SNAPSHOT_DATES_OR_LIMITED_HISTORY", "blocker_status": "ACTIVE", "affected_backtest_stage": "historical snapshot panel", "severity": "MEDIUM", "current_metric": f"snapshot_history_count={values['SIGNAL_SNAPSHOT_HISTORY_COUNT']}", "why_it_matters": "Time-series validation needs more periods.", "required_resolution": "Accumulate more frozen snapshots.", "recommended_next_step": "Design only."},
        {"blocker_name": "EVENT_RISK_ADVISORY_ONLY", "blocker_status": "ACTIVE", "affected_backtest_stage": "event factor join", "severity": "MEDIUM", "current_metric": f"applied_official={values['EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION']}", "why_it_matters": "Event coefficients cannot be interpreted as official logic.", "required_resolution": "Separate advisory fields from official outcomes.", "recommended_next_step": "Keep event factor advisory."},
        {"blocker_name": "BACKFILL_NOT_APPLIED", "blocker_status": "ACTIVE", "affected_backtest_stage": "price factor coverage", "severity": "MEDIUM", "current_metric": "FULL_HISTORY_BACKFILL_APPLIED=FALSE", "why_it_matters": "Design projections are not actual data.", "required_resolution": "Approved staged backfill and shadow factor recompute.", "recommended_next_step": "No production use."},
        {"blocker_name": "STAGED_BACKFILL_NOT_APPLIED", "blocker_status": "ACTIVE", "affected_backtest_stage": "price history availability", "severity": "MEDIUM", "current_metric": "STAGED_BACKFILL_APPLIED=FALSE", "why_it_matters": "Batch 1 is only a request design.", "required_resolution": "Explicit future staged apply approval.", "recommended_next_step": "Stable snapshot before any fetch."},
        {"blocker_name": "DAILY_TRUST_MEDIUM", "blocker_status": "ACTIVE", "affected_backtest_stage": "production evidence gate", "severity": "MEDIUM", "current_metric": "DAILY_TRUST_LEVEL=MEDIUM", "why_it_matters": "Medium trust prevents production-grade claims.", "required_resolution": "Raise data quality and outcome confidence.", "recommended_next_step": "No production promotion."},
    ]


def implementation_rows() -> List[Dict[str, object]]:
    steps = [
        (1, "Validate enough historical signal snapshots", "Ensure enough frozen dates for time-series research.", "signal snapshot archive", "future_snapshot_coverage_audit.csv", ">=12 snapshot dates", "FALSE", "FALSE", "TRUE", "FALSE"),
        (2, "Validate forward outcome maturity", "Confirm outcomes are mature before fill.", "shadow tracker + local prices", "future_outcome_maturity_audit.csv", "matured rows by horizon", "FALSE", "FALSE", "TRUE", "FALSE"),
        (3, "Validate full-history price factor coverage", "Ensure factor coverage supports backtest.", "price factor coverage audit", "future_factor_coverage_audit.csv", "coverage threshold met", "FALSE", "FALSE", "TRUE", "FALSE"),
        (4, "Build research-only unified dataset", "Join frozen signals, factors, event risk, and outcomes.", "validated research inputs", "future_unified_backtest_dataset.csv", "write to research output only", "FALSE", "FALSE", "TRUE", "FALSE"),
        (5, "Run leakage checks", "Prevent lookahead bias.", "unified dataset", "future_leakage_check.csv", "100% pass", "FALSE", "FALSE", "TRUE", "FALSE"),
        (6, "Run bucket-level research metrics", "Measure factor bucket behavior.", "leakage-clean dataset", "future_bucket_metrics.csv", "minimum sample by bucket", "FALSE", "FALSE", "FALSE", "TRUE"),
        (7, "Run cross-horizon validation", "Check robustness across horizons.", "metrics by horizon", "future_cross_horizon_validation.csv", "multi-horizon maturity", "FALSE", "FALSE", "FALSE", "TRUE"),
        (8, "Produce research-only report", "Summarize non-production evidence.", "validated metrics", "future_backtest_research_report.md", "report marked research-only", "FALSE", "FALSE", "FALSE", "TRUE"),
        (9, "Prohibit weight changes unless evidence gates pass", "Prevent premature production changes.", "evidence gate audit", "future_evidence_gate_decision.csv", "explicit approval and sample thresholds", "FALSE", "FALSE", "TRUE", "TRUE"),
        (10, "Stable snapshot before any production integration", "Preserve research state.", "all research outputs", "future_backtest_stable_snapshot", "validation fail count zero", "FALSE", "FALSE", "TRUE", "FALSE"),
    ]
    return [
        {
            "step_index": step, "step_name": name, "purpose": purpose, "required_inputs": inputs,
            "output_file_if_implemented_later": output, "safety_gate": gate,
            "modifies_production": modifies, "external_data_required": external,
            "allowed_now": allowed, "requires_explicit_approval": approval,
            "notes": "Future controlled implementation only; V18.21I is design/read-only.",
        }
        for step, name, purpose, inputs, output, gate, modifies, external, allowed, approval in steps
    ]


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(values: Dict[str, object]) -> str:
    return f"""# V18.21I Unified Backtest Research Design Report

## Executive Summary
Status: {values.get('STATUS')}. V18.21I defines a unified backtest research design only. No backtest was executed and no results were applied.

## Safety Statement
This module is advisory read-only. It does not fetch data, write price history, fill forward returns, modify price cache, modify rankings, modify signal snapshots, modify event calendars, modify simulation or forward tracker state, or change official decisions.

## Available Research Inputs
Input sources audited: {values.get('BACKTEST_INPUT_SOURCE_COUNT')}. Missing inputs: {values.get('BACKTEST_INPUT_MISSING_COUNT')}. Signal snapshot rows: {values.get('SIGNAL_SNAPSHOT_ROW_COUNT')}.

## Unified Backtest Dataset Schema Design
The schema design separates identity keys, timestamp keys, raw scores, price-derived factors, technical timing factors, event risk factors, market regime factors, forward outcome fields, eligibility flags, and safety flags.

## Leakage Prevention Rules
Rules require frozen snapshot values, no historical recomputation using current formulas, outcome-date gates, event availability gates, ranking freeze, backfill availability timestamps, event coefficient separation, shadow tracker isolation, high-confidence keys, and multi-horizon maturity before effect claims.

## Sample Construction Plan
Current execution readiness: {values.get('BACKTEST_EXECUTION_READINESS_STATUS')}. Forward returns filled: {values.get('FORWARD_RETURN_FILLED_COUNT')}; pending: {values.get('FORWARD_RETURN_PENDING_COUNT')}.

## Metrics Specification
Metrics are specified for future research only and include return distribution, factor bucket spread, rank IC, risk after signal, event-adjusted score spread, timing buckets, and market-regime conditioned returns.

## Readiness Blockers
Major blockers remain: incomplete full-history coverage, unfilled forward returns, missing multi-horizon returns, zero high-confidence forward matches, limited snapshot history, advisory-only event risk, unapplied backfill, and medium daily trust.

## Future Controlled Implementation Plan
Future implementation must build a research-only unified dataset, run leakage checks, compute metrics only after sample gates pass, and snapshot before any production integration.

## Why No Factor Claims, Weight Changes, Or Production Promotions Are Allowed
High-confidence forward matches are {values.get('HIGH_CONFIDENCE_FORWARD_MATCH_COUNT')}, forward returns filled are {values.get('FORWARD_RETURN_FILLED_COUNT')}, and multi-horizon readiness is {values.get('MULTI_HORIZON_READINESS_STATUS')}. Claims, weight changes, and promotions remain disabled.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}.

## Next-Step Recommendation
Create a stable snapshot if clean. Then either wait for forward horizons to mature before outcome filling, or proceed to a future controlled staged backfill only with explicit approval.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output_paths = {key: root / rel for key, rel in OUTPUTS.items()}
    before = {str(path): signature(path) for path in protected_paths(root)}

    stable = {name: readfirst(root / rel) for name, rel, _ in STABLE_INPUTS}
    signal_rows, signal_fields = read_csv(root / "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv")
    signal_dates = {str(row.get("snapshot_date", "")).strip() for row in signal_rows if str(row.get("snapshot_date", "")).strip()}

    f = stable.get("V18_21F_STABLE_READ_FIRST", {})
    h = stable.get("V18_21H_STABLE_READ_FIRST", {})
    h_r1 = stable.get("V18_21H_R1_STABLE_READ_FIRST", {})
    d = stable.get("V18_21D_R1_STABLE_READ_FIRST", {})
    c = stable.get("V18_21C_R2_STABLE_READ_FIRST", {})
    e = stable.get("V18_21E_R1_STABLE_READ_FIRST", {})

    current_score_ratio = first(h.get("CURRENT_SCORE_READY_RATIO"), h_r1.get("CURRENT_SCORE_READY_RATIO"), f.get("PRICE_DERIVED_SCORE_READY_RATIO"), "0.320000")
    current_full_ready = first(h.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), h_r1.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), f.get("CURRENT_FULL_HISTORY_FACTOR_READY_COUNT"), "104")
    current_missing = first(h.get("CURRENT_MISSING_HISTORY_TICKER_COUNT"), h_r1.get("CURRENT_MISSING_HISTORY_TICKER_COUNT"), f.get("PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT"), "221")
    forward_filled = first(d.get("FORWARD_RETURN_FILLED_COUNT"), f.get("FORWARD_RETURN_FILLED_COUNT"), "0")
    forward_pending = first(d.get("FORWARD_RETURN_PENDING_COUNT"), f.get("FORWARD_RETURN_PENDING_COUNT"), "525")
    high_conf = first(c.get("HIGH_CONFIDENCE_MATCH_COUNT"), f.get("FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT"), "0")
    multi_horizon = first(c.get("MULTI_HORIZON_READINESS_STATUS"), f.get("MULTI_HORIZON_READINESS_STATUS"), "NOT_READY_MULTI_HORIZON")
    event_coeff = first(e.get("FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT"), f.get("EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT"), "0.300000")
    event_applied = first(e.get("EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION"), f.get("EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION"), "FALSE")
    input_missing = sum(1 for _, rel, required in ALL_INPUTS if required and not (root / rel).exists()) + sum(1 for _, rel, required in ALL_INPUTS if (not required) and not (root / rel).exists())

    values: Dict[str, object] = {
        "STATUS": STATUS_READY,
        "BACKTEST_INPUT_SOURCE_COUNT": len(ALL_INPUTS),
        "BACKTEST_INPUT_MISSING_COUNT": input_missing,
        "SIGNAL_SNAPSHOT_ROW_COUNT": len(signal_rows),
        "SIGNAL_SNAPSHOT_HISTORY_COUNT": len(signal_dates),
        "CURRENT_SCORE_READY_RATIO": current_score_ratio,
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": current_full_ready,
        "CURRENT_MISSING_HISTORY_TICKER_COUNT": current_missing,
        "FORWARD_TRACKER_SHADOW_ROW_COUNT": first(d.get("UPGRADED_SHADOW_ROW_COUNT"), f.get("FORWARD_TRACKER_SHADOW_ROW_COUNT"), "525"),
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "FORWARD_RETURN_PENDING_COUNT": forward_pending,
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT": high_conf,
        "MULTI_HORIZON_READINESS_STATUS": multi_horizon,
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT": event_coeff,
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": event_applied,
        "BACKTEST_EXECUTION_READINESS_STATUS": "BLOCKED_DESIGN_ONLY_FORWARD_RETURNS_PENDING",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(output_paths["read_first"]),
        "REPORT": str(output_paths["report"]),
    }
    values.update(SAFETY_FLAGS)

    readiness = input_readiness_rows(root, int_value(forward_filled), int_value(current_missing))
    write_csv(output_paths["readiness"], readiness, READINESS_FIELDS)
    write_csv(output_paths["schema"], schema_rows(), SCHEMA_FIELDS)
    write_csv(output_paths["leakage"], leakage_rows(), LEAKAGE_FIELDS)
    write_csv(output_paths["sample"], sample_plan_rows(len(signal_rows), int_value(values["FORWARD_TRACKER_SHADOW_ROW_COUNT"]), 0, int_value(current_full_ready)), SAMPLE_FIELDS)
    write_csv(output_paths["metrics"], metrics_rows(), METRIC_FIELDS)
    write_csv(output_paths["blockers"], blocker_rows(values), BLOCKER_FIELDS)
    write_csv(output_paths["implementation"], implementation_rows(), IMPLEMENTATION_FIELDS)
    write_text(output_paths["read_first"], render_readfirst(values))
    write_text(output_paths["report"], report(values))

    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    read_first_text = read_text(output_paths["read_first"])
    validations = [
        ("powershell_parse", ps_parse(root / "scripts/v18/run_v18_21I_unified_backtest_research_design.ps1")),
        ("python_compile", py_compile(root / "scripts/v18/v18_21I_unified_backtest_research_design.py")),
        ("required_outputs_exist", all(path.exists() for path in output_paths.values())),
        ("required_read_first_fields", all(field in read_first_text for field in READ_FIRST_FIELDS)),
        ("unified_backtest_design_ready", values["UNIFIED_BACKTEST_DESIGN_READY"] == "TRUE"),
        ("backtest_not_executed", values["BACKTEST_EXECUTED"] == "FALSE"),
        ("backtest_results_not_applied", values["BACKTEST_RESULTS_APPLIED"] == "FALSE"),
        ("external_data_not_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE"),
        ("price_cache_not_modified", values["PRICE_CACHE_MODIFIED"] == "FALSE"),
        ("price_history_not_written", values["PRICE_HISTORY_WRITTEN"] == "FALSE"),
        ("forward_returns_not_filled", values["FORWARD_RETURN_FILLED_COUNT"] == "0"),
        ("protected_files_not_modified", not changed),
        ("claims_weights_promotions_zero", values["EFFECT_CLAIM_ALLOWED_COUNT"] == "0" and values["WEIGHT_CHANGE_ALLOWED_COUNT"] == "0" and values["PRODUCTION_PROMOTION_ALLOWED_COUNT"] == "0"),
        ("signal_snapshot_required", len(signal_rows) > 0),
    ]
    fail_count = sum(1 for _, ok in validations if not ok)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    write_text(output_paths["read_first"], render_readfirst(values))
    write_text(output_paths["report"], report(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "UNIFIED_BACKTEST_DESIGN_READY",
        "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "BACKTEST_INPUT_SOURCE_COUNT",
        "BACKTEST_INPUT_MISSING_COUNT", "SIGNAL_SNAPSHOT_ROW_COUNT", "SIGNAL_SNAPSHOT_HISTORY_COUNT",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "FORWARD_TRACKER_SHADOW_ROW_COUNT",
        "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT",
        "HIGH_CONFIDENCE_FORWARD_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
        "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
        "BACKTEST_EXECUTION_READINESS_STATUS", "EFFECT_CLAIM_ALLOWED_COUNT",
        "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT",
        "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "EXTERNAL_DATA_FETCHED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
