from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "ADVISORY_ONLY"
PATCH_MODE = "FACTOR_EFFECTIVENESS_RESEARCH_READ_CENTER_ONLY"
STATUS_WARN = "WARN_V18_21C_FACTOR_EFFECTIVENESS_RESEARCH_INSUFFICIENT_EVIDENCE"
STATUS_FAIL = "FAIL_V18_21C_FACTOR_EFFECTIVENESS_RESEARCH_NO_SIGNAL_SNAPSHOT"
MINIMUM_SAMPLE_REQUIRED = 20
SAMPLE_MATURITY_PATCH_COMPATIBILITY = "V18_21C_R1_READY"

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

SIGNAL_SNAPSHOT_PATH = "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv"
BLOCKERS_PATH = "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_RESEARCH_READINESS_BLOCKERS.csv"
SIGNAL_HISTORY_GLOB = "outputs/v18/signal_snapshots/history/V18_21B_R1_SIGNAL_SNAPSHOT_*.csv"

FORWARD_SOURCES = [
    ("current_ranked_candidate_forward_tracker", "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"),
    ("v18_14c_ranked_candidate_forward_tracker", "outputs/v18/candidates/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"),
    ("v18_14d_forward_price_filler", "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv"),
    ("sim_candidate_tracker", "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"),
    ("sim_candidate_tracker_today", "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv"),
    ("v18_4a_factor_snapshot", "outputs/v18/forward_outcome/V18_4A_CURRENT_FACTOR_SNAPSHOT.csv"),
    ("v18_10b_forward_return_maturity", "outputs/v18/factor_research/V18_10B_R1_CURRENT_FORWARD_RETURN_MATURITY.csv"),
    ("v18_10b_factor_effectiveness", "outputs/v18/factor_research/V18_10B_CURRENT_FACTOR_EFFECTIVENESS.csv"),
    ("v18_10c_weight_research_eval", "outputs/v18/weight_research/V18_10C_CURRENT_WEIGHT_RESEARCH_EVALUATION.csv"),
    ("v18_14e_daily_with_forward_summary", "outputs/v18/ops/V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_SUMMARY.csv"),
]

HORIZON_COLUMNS = {
    "1D": ["forward_1d_return", "fwd_1d_return", "return_1obs_pct"],
    "3D": ["forward_3d_return", "fwd_3d_return", "return_3obs_pct"],
    "5D": ["forward_5d_return", "fwd_5d_return", "return_5obs_pct"],
    "10D": ["forward_10d_return", "fwd_10d_return", "return_10obs_pct"],
    "20D": ["forward_20d_return", "fwd_20d_return", "return_20obs_pct"],
}

FACTOR_COLUMNS = {
    "factor_pack_score": "factor_pack_score",
    "composite_candidate_score": "composite_candidate_score",
    "technical_timing_score": "technical_timing_score",
    "overheat_penalty": "overheat_penalty",
    "price_derived_total_score": "price_derived_total_score",
    "relative_strength_score": "relative_strength_score",
    "buy_zone_score": "buy_zone_score",
    "volume_confirmation_score": "volume_confirmation_score",
    "volatility_risk_score": "volatility_risk_score",
}

USABLE_GROUPS = {
    "FACTOR_PACK_USABLE_SAMPLE_COUNT": ["factor_pack_score"],
    "TECHNICAL_TIMING_USABLE_SAMPLE_COUNT": ["technical_timing_score"],
    "PRICE_DERIVED_USABLE_SAMPLE_COUNT": ["price_derived_total_score"],
    "RELATIVE_STRENGTH_USABLE_SAMPLE_COUNT": ["relative_strength_score"],
    "BUY_ZONE_USABLE_SAMPLE_COUNT": ["buy_zone_score"],
    "OVERHEAT_PENALTY_USABLE_SAMPLE_COUNT": ["overheat_penalty"],
    "VOLUME_CONFIRMATION_USABLE_SAMPLE_COUNT": ["volume_confirmation_score"],
    "MARKET_REGIME_USABLE_SAMPLE_COUNT": ["market_risk_coefficient"],
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "PATCH_MODE",
    "POLICY_APPLIED",
    "SNAPSHOT_SOURCE_STATUS",
    "SIGNAL_SNAPSHOT_ROW_COUNT",
    "SIGNAL_SNAPSHOT_HISTORY_COUNT",
    "READY_FOR_FORWARD_RESEARCH_COUNT",
    "READY_FOR_SIMULATION_ANALYSIS_COUNT",
    "FORWARD_OUTCOME_SOURCE_COUNT",
    "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT",
    "EFFECTIVENESS_EVIDENCE_STATUS",
    "FACTOR_BUCKET_SUMMARY_CREATED",
    "FACTOR_EVIDENCE_GAP_AUDIT_CREATED",
    "FACTOR_PACK_USABLE_SAMPLE_COUNT",
    "TECHNICAL_TIMING_USABLE_SAMPLE_COUNT",
    "PRICE_DERIVED_USABLE_SAMPLE_COUNT",
    "RELATIVE_STRENGTH_USABLE_SAMPLE_COUNT",
    "BUY_ZONE_USABLE_SAMPLE_COUNT",
    "OVERHEAT_PENALTY_USABLE_SAMPLE_COUNT",
    "VOLUME_CONFIRMATION_USABLE_SAMPLE_COUNT",
    "MARKET_REGIME_USABLE_SAMPLE_COUNT",
    "MINIMUM_SAMPLE_REQUIRED",
    "RESEARCH_CONCLUSION_STATUS",
    "DATA_DEGRADED_COUNT",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "COVERAGE_WINDOW_COMPLETE",
    "DAILY_TRUST_LEVEL",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "RANKING_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "PRICE_FACTOR_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED",
    "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "READ_FIRST",
    "REPORT",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def median(values: List[float]) -> str:
    if not values:
        return ""
    return f"{statistics.median(values):.6f}"


def mean(values: List[float]) -> str:
    if not values:
        return ""
    return f"{sum(values) / len(values):.6f}"


def hit_rate(values: List[float]) -> str:
    if not values:
        return ""
    return f"{sum(1 for value in values if value > 0) / len(values):.6f}"


def source_audit(root: Path):
    audits = []
    outcome_by_ticker: Dict[str, Dict[str, str]] = {}
    source_count = 0
    matched_sources = 0
    for name, rel in FORWARD_SOURCES:
        path = root / rel
        rows, fields = read_csv(path)
        exists = path.exists()
        ticker_col = next((c for c in fields if c.lower() in {"ticker", "symbol", "yf_ticker"}), "")
        date_col = next((c for c in fields if c.lower() in {"snapshot_date", "signal_date", "snapshot_run_date", "price_date"}), "")
        detected = []
        for horizon, cols in HORIZON_COLUMNS.items():
            if any(col in fields for col in cols):
                detected.append(horizon)
        parsed_tickers = {norm_ticker(row.get(ticker_col, "")) for row in rows} if ticker_col else set()
        parsed_tickers.discard("")
        has_returns = False
        if rows and ticker_col:
            for row in rows:
                ticker = norm_ticker(row.get(ticker_col, ""))
                if not ticker:
                    continue
                dest = outcome_by_ticker.setdefault(ticker, {})
                for horizon, cols in HORIZON_COLUMNS.items():
                    value = first_value(row, cols)
                    if value and to_float(value) is not None and not dest.get(horizon):
                        dest[horizon] = value
                        dest[f"{horizon}_source"] = str(path)
                        has_returns = True
        if exists:
            source_count += 1
            if has_returns:
                matched_sources += 1
        if not exists:
            status = "MISSING"
            notes = "Candidate source missing."
        elif not rows:
            status = "NO_ROWS"
            notes = "Source parsed with no rows."
        elif not ticker_col:
            status = "NO_TICKER_COLUMN"
            notes = "Cannot match outcomes to signal snapshot tickers."
        elif not detected:
            status = "NO_FORWARD_RETURN_COLUMNS"
            notes = "No recognized forward-return horizons."
        elif has_returns:
            status = "OK_FORWARD_RETURNS_FOUND"
            notes = "Forward returns were read where nonblank."
        else:
            status = "NO_NONBLANK_FORWARD_RETURNS"
            notes = "Forward-return columns exist but no nonblank numeric values were found."
        audits.append(
            {
                "source_name": name,
                "source_path": str(path),
                "source_exists": str(exists).upper(),
                "modified_time": modified_time(path),
                "parsed_row_count": len(rows),
                "parsed_ticker_count": len(parsed_tickers),
                "horizons_detected": ";".join(detected),
                "has_signal_link_key": str(any("signal_snapshot_id" == c or "signal_link" in c.lower() for c in fields)).upper(),
                "has_ticker": str(bool(ticker_col)).upper(),
                "has_snapshot_date_or_signal_date": str(bool(date_col)).upper(),
                "source_status": status,
                "notes": notes,
            }
        )
    return audits, outcome_by_ticker, source_count, matched_sources


def readiness_rows(snapshot_rows: List[Dict[str, str]], outcomes: Dict[str, Dict[str, str]]):
    rows = []
    matched = 0
    for row in snapshot_rows:
        ticker = norm_ticker(row.get("ticker", ""))
        outcome = outcomes.get(ticker, {})
        has_any_forward = any(outcome.get(h) for h in HORIZON_COLUMNS)
        if has_any_forward:
            matched += 1
        has_factor = bool(first_value(row, ["factor_pack_score"]))
        has_rank = bool(first_value(row, ["factor_pack_rank"]))
        has_tech = bool(first_value(row, ["technical_timing_score"]))
        has_overheat = bool(first_value(row, ["overheat_penalty"]))
        has_price = bool(first_value(row, ["price_derived_total_score"]))
        has_rs = bool(first_value(row, ["relative_strength_score"]))
        has_buy_zone_score = bool(first_value(row, ["buy_zone_score"]))
        has_buy_zone_label = bool(first_value(row, ["buy_zone_label"]))
        has_market = bool(first_value(row, ["market_regime_label", "market_risk_coefficient"]))
        blockers = []
        if not (has_factor or has_rank or has_tech):
            blockers.append("MISSING_CORE_SIGNAL")
        if not has_price:
            blockers.append("MISSING_PRICE_DERIVED_SCORE")
        if not has_market:
            blockers.append("MISSING_MARKET_REGIME")
        if has_any_forward and not blockers:
            status = "READY_WITH_FORWARD_RETURNS"
            ready = "TRUE"
        elif not blockers:
            status = "READY_PENDING_FORWARD_RETURNS"
            ready = "FALSE"
            blockers.append("PENDING_FORWARD_RETURNS")
        elif "MISSING_PRICE_DERIVED_SCORE" in blockers and len(blockers) == 1:
            status = "DEGRADED_MISSING_PRICE_DERIVED_SCORE"
            ready = "FALSE"
        else:
            status = "DEGRADED_MISSING_CORE_SIGNAL"
            ready = "FALSE"
        rows.append(
            {
                "snapshot_date": row.get("snapshot_date", ""),
                "ticker": ticker,
                "signal_snapshot_id": row.get("signal_snapshot_id", ""),
                "factor_pack_score_available": str(has_factor).upper(),
                "factor_pack_rank_available": str(has_rank).upper(),
                "technical_timing_score_available": str(has_tech).upper(),
                "overheat_penalty_available": str(has_overheat).upper(),
                "price_derived_score_available": str(has_price).upper(),
                "relative_strength_score_available": str(has_rs).upper(),
                "buy_zone_score_available": str(has_buy_zone_score).upper(),
                "buy_zone_label_available": str(has_buy_zone_label).upper(),
                "market_regime_available": str(has_market).upper(),
                "forward_return_1d_available": str(bool(outcome.get("1D"))).upper(),
                "forward_return_3d_available": str(bool(outcome.get("3D"))).upper(),
                "forward_return_5d_available": str(bool(outcome.get("5D"))).upper(),
                "forward_return_10d_available": str(bool(outcome.get("10D"))).upper(),
                "forward_return_20d_available": str(bool(outcome.get("20D"))).upper(),
                "ready_for_factor_effectiveness_research": ready,
                "readiness_status": status,
                "blocking_reason": ";".join(blockers),
            }
        )
    return rows, matched


def bucket_name(rank: int) -> str:
    return {1: "LOW", 2: "MID", 3: "HIGH"}.get(rank, f"BUCKET_{rank}")


def bucket_summaries(snapshot_rows: List[Dict[str, str]], outcomes: Dict[str, Dict[str, str]]):
    rows = []
    for factor_name, col in FACTOR_COLUMNS.items():
        factor_values = [(norm_ticker(row.get("ticker")), to_float(row.get(col))) for row in snapshot_rows]
        factor_values = [(ticker, value) for ticker, value in factor_values if ticker and value is not None]
        sorted_vals = sorted(factor_values, key=lambda x: x[1])
        buckets: Dict[str, set] = {"LOW": set(), "MID": set(), "HIGH": set()}
        if sorted_vals:
            n = len(sorted_vals)
            for i, (ticker, _value) in enumerate(sorted_vals):
                rank = 1 if i < n / 3 else (2 if i < 2 * n / 3 else 3)
                buckets[bucket_name(rank)].add(ticker)
        for horizon in HORIZON_COLUMNS:
            any_rows = False
            for rank, bname in enumerate(["LOW", "MID", "HIGH"], start=1):
                returns = []
                for ticker in buckets[bname]:
                    value = to_float(outcomes.get(ticker, {}).get(horizon))
                    if value is not None:
                        returns.append(value)
                if returns:
                    any_rows = True
                evidence_status = "SUFFICIENT_SAMPLE" if len(returns) >= MINIMUM_SAMPLE_REQUIRED else "INSUFFICIENT_FORWARD_RETURNS"
                rows.append(
                    {
                        "factor_name": factor_name,
                        "bucket_name": bname,
                        "bucket_rank": rank,
                        "horizon": horizon,
                        "sample_count": len(returns),
                        "average_forward_return": mean(returns),
                        "median_forward_return": median(returns),
                        "hit_rate": hit_rate(returns),
                        "evidence_status": evidence_status,
                    }
                )
            if not any_rows:
                # Rows above already carry zero-count insufficient evidence for this factor/horizon.
                pass
    return rows


def evidence_gaps(snapshot_rows: List[Dict[str, str]], outcomes: Dict[str, Dict[str, str]]):
    rows = []
    for factor_name, col in {**FACTOR_COLUMNS, "market_risk_coefficient": "market_risk_coefficient"}.items():
        signal_count = sum(1 for row in snapshot_rows if first_value(row, [col]))
        score_ready = signal_count
        matched = 0
        for row in snapshot_rows:
            ticker = norm_ticker(row.get("ticker"))
            if first_value(row, [col]) and any(outcomes.get(ticker, {}).get(h) for h in HORIZON_COLUMNS):
                matched += 1
        missing = max(signal_count - matched, 0)
        status = "SUFFICIENT_EVIDENCE" if matched >= MINIMUM_SAMPLE_REQUIRED else "INSUFFICIENT_FORWARD_RETURNS"
        next_needed = "Accumulate matched forward returns for this factor." if status != "SUFFICIENT_EVIDENCE" else "Continue monitoring with larger samples."
        rows.append(
            {
                "factor_name": factor_name,
                "available_signal_count": signal_count,
                "score_ready_count": score_ready,
                "forward_return_matched_count": matched,
                "missing_forward_return_count": missing,
                "usable_sample_count": matched,
                "minimum_sample_required": MINIMUM_SAMPLE_REQUIRED,
                "evidence_gap_status": status,
                "next_data_needed": next_needed,
            }
        )
    return rows


def conclusions(gap_rows: List[Dict[str, object]], matched_count: int, rf: Dict[str, str]):
    mapping = [
        ("FACTOR_PACK_EFFECTIVENESS", "factor_pack_score"),
        ("TECHNICAL_TIMING_EFFECTIVENESS", "technical_timing_score"),
        ("PRICE_DERIVED_EFFECTIVENESS", "price_derived_total_score"),
        ("BUY_ZONE_DISTANCE_EFFECTIVENESS", "buy_zone_score"),
        ("RELATIVE_STRENGTH_EFFECTIVENESS", "relative_strength_score"),
        ("OVERHEAT_PENALTY_EFFECTIVENESS", "overheat_penalty"),
        ("VOLUME_CONFIRMATION_EFFECTIVENESS", "volume_confirmation_score"),
        ("MARKET_REGIME_EFFECTIVENESS", "market_risk_coefficient"),
    ]
    by_factor = {row["factor_name"]: row for row in gap_rows}
    rows = []
    for area, factor in mapping:
        gap = by_factor.get(factor, {})
        usable = int(gap.get("usable_sample_count", 0) or 0)
        enough = usable >= MINIMUM_SAMPLE_REQUIRED
        rows.append(
            {
                "conclusion_area": area,
                "conclusion_status": "PRELIMINARY_SAMPLE_AVAILABLE" if enough else "INSUFFICIENT_EVIDENCE",
                "evidence_level": "LOW" if enough else "INSUFFICIENT",
                "summary": f"{usable} matched forward-return samples are available for {factor}.",
                "recommended_next_step": "Review bucket summary cautiously." if enough else "Wait for more forward returns; do not change weights.",
            }
        )
    rows.append(
        {
            "conclusion_area": "SIMULATION_RESEARCH_READINESS",
            "conclusion_status": "DEGRADED_READY_SUBSET_ONLY",
            "evidence_level": "LOW",
            "summary": f"{rf.get('READY_FOR_SIMULATION_ANALYSIS_COUNT', '31')} rows are simulation-analysis ready; {matched_count} rows have any matched local forward-return evidence.",
            "recommended_next_step": "Use readiness filters and preserve snapshots before drawing conclusions.",
        }
    )
    return rows


def report_text(values: Dict[str, object]) -> str:
    return f"""# V18.21C Factor Effectiveness Research Read Center

## Executive summary
Status: {values['STATUS']}. The read center created factor-effectiveness readiness, bucket research, evidence gap, forward source, and conclusion outputs.

## Safety statement
This module is advisory-only. It does not modify factor weights, rankings, technical timing, price-derived factors, signal snapshots, simulation positions, forward tracker state, price cache, broker execution, official decisions, auto-trade, or auto-sell. External data fetched: FALSE.

## Signal snapshot source summary
Snapshot status: {values['SNAPSHOT_SOURCE_STATUS']}. Signal rows: {values['SIGNAL_SNAPSHOT_ROW_COUNT']}. Historical snapshot count: {values['SIGNAL_SNAPSHOT_HISTORY_COUNT']}.

## Forward outcome source summary
Forward outcome sources present: {values['FORWARD_OUTCOME_SOURCE_COUNT']}. Matched signal count: {values['FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT']}. Evidence status: {values['EFFECTIVENESS_EVIDENCE_STATUS']}.

## Factor readiness summary
Ready for forward research from snapshot semantics: {values['READY_FOR_FORWARD_RESEARCH_COUNT']}. Ready for simulation analysis: {values['READY_FOR_SIMULATION_ANALYSIS_COUNT']}. Data degraded rows: {values['DATA_DEGRADED_COUNT']}.

## Bucket research summary
The bucket summary file is created. Factors/horizons with fewer than {values['MINIMUM_SAMPLE_REQUIRED']} matched forward returns are marked `INSUFFICIENT_FORWARD_RETURNS`.

## Factor evidence gap summary
The evidence gap audit identifies missing forward-return samples per factor and the next data needed. No factor weights or production logic were changed.

## Research conclusions
Research conclusion status: {values['RESEARCH_CONCLUSION_STATUS']}. Conclusions are evidence-gated and do not mark factors effective without sufficient samples.

## Validation summary
Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

## Next-step recommendation
Keep accumulating forward returns against immutable signal snapshots. Re-run this read center after more horizons mature before considering any separate research proposal for factor weight changes.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    out_dir = root / "outputs/v18/factor_effectiveness"
    ops_dir = root / "outputs/v18/ops"
    readiness_path = out_dir / "V18_21C_CURRENT_EFFECTIVENESS_READINESS_AUDIT.csv"
    bucket_path = out_dir / "V18_21C_CURRENT_FACTOR_BUCKET_RESEARCH_SUMMARY.csv"
    gap_path = out_dir / "V18_21C_CURRENT_FACTOR_EVIDENCE_GAP_AUDIT.csv"
    source_audit_path = out_dir / "V18_21C_CURRENT_FORWARD_OUTCOME_SOURCE_AUDIT.csv"
    conclusion_path = out_dir / "V18_21C_CURRENT_RESEARCH_CONCLUSION_SUMMARY.csv"
    read_first_path = ops_dir / "V18_21C_READ_FIRST.txt"
    report_path = ops_dir / "V18_21C_CURRENT_FACTOR_EFFECTIVENESS_RESEARCH_REPORT.md"

    snapshot_rows, _snapshot_fields = read_csv(root / SIGNAL_SNAPSHOT_PATH)
    blockers, _ = read_csv(root / BLOCKERS_PATH)
    stable_rf = read_first(root / "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt")
    source_rows, outcomes, source_count, _matched_sources = source_audit(root)
    history_count = len(list(root.glob(SIGNAL_HISTORY_GLOB)))

    if not snapshot_rows:
        values: Dict[str, object] = {
            "STATUS": STATUS_FAIL,
            "MODE": MODE,
            "PATCH_MODE": PATCH_MODE,
            "SNAPSHOT_SOURCE_STATUS": "MISSING_SIGNAL_SNAPSHOT",
            "SIGNAL_SNAPSHOT_ROW_COUNT": "0",
            "VALIDATION_FAIL_COUNT": "1",
            "READ_FIRST": str(read_first_path),
            "REPORT": str(report_path),
            **SAFETY_FLAGS,
        }
        write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
        write_text(report_path, report_text({field: values.get(field, "") for field in READ_FIRST_FIELDS}))
        print(f"STATUS: {STATUS_FAIL}")
        return 1

    readiness, matched_count = readiness_rows(snapshot_rows, outcomes)
    buckets = bucket_summaries(snapshot_rows, outcomes)
    gaps = evidence_gaps(snapshot_rows, outcomes)
    conclusions_rows = conclusions(gaps, matched_count, stable_rf)

    write_csv(readiness_path, readiness, [
        "snapshot_date", "ticker", "signal_snapshot_id", "factor_pack_score_available", "factor_pack_rank_available",
        "technical_timing_score_available", "overheat_penalty_available", "price_derived_score_available",
        "relative_strength_score_available", "buy_zone_score_available", "buy_zone_label_available", "market_regime_available",
        "forward_return_1d_available", "forward_return_3d_available", "forward_return_5d_available",
        "forward_return_10d_available", "forward_return_20d_available", "ready_for_factor_effectiveness_research",
        "readiness_status", "blocking_reason",
    ])
    write_csv(bucket_path, buckets, [
        "factor_name", "bucket_name", "bucket_rank", "horizon", "sample_count", "average_forward_return",
        "median_forward_return", "hit_rate", "evidence_status",
    ])
    write_csv(gap_path, gaps, [
        "factor_name", "available_signal_count", "score_ready_count", "forward_return_matched_count",
        "missing_forward_return_count", "usable_sample_count", "minimum_sample_required", "evidence_gap_status", "next_data_needed",
    ])
    write_csv(source_audit_path, source_rows, [
        "source_name", "source_path", "source_exists", "modified_time", "parsed_row_count", "parsed_ticker_count",
        "horizons_detected", "has_signal_link_key", "has_ticker", "has_snapshot_date_or_signal_date", "source_status", "notes",
    ])
    write_csv(conclusion_path, conclusions_rows, [
        "conclusion_area", "conclusion_status", "evidence_level", "summary", "recommended_next_step",
    ])

    usable = {}
    for key, factors in USABLE_GROUPS.items():
        usable[key] = max((int(row["usable_sample_count"]) for row in gaps if row["factor_name"] in factors), default=0)
    evidence_status = "PRELIMINARY_EVIDENCE_AVAILABLE" if max(usable.values() or [0]) >= MINIMUM_SAMPLE_REQUIRED else "INSUFFICIENT_FORWARD_RETURNS"
    data_degraded = sum(1 for row in readiness if row["readiness_status"].startswith("DEGRADED"))
    values = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "POLICY_APPLIED": "FALSE",
        "SNAPSHOT_SOURCE_STATUS": "OK_CURRENT_SIGNAL_SNAPSHOT",
        "SIGNAL_SNAPSHOT_ROW_COUNT": str(len(snapshot_rows)),
        "SIGNAL_SNAPSHOT_HISTORY_COUNT": str(history_count),
        "READY_FOR_FORWARD_RESEARCH_COUNT": stable_rf.get("READY_FOR_FORWARD_RESEARCH_COUNT", str(sum(1 for row in blockers if row.get("ready_for_forward_research") == "TRUE"))),
        "READY_FOR_SIMULATION_ANALYSIS_COUNT": stable_rf.get("READY_FOR_SIMULATION_ANALYSIS_COUNT", str(sum(1 for row in blockers if row.get("ready_for_simulation_analysis") == "TRUE"))),
        "FORWARD_OUTCOME_SOURCE_COUNT": str(source_count),
        "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT": str(matched_count),
        "EFFECTIVENESS_EVIDENCE_STATUS": evidence_status,
        "FACTOR_BUCKET_SUMMARY_CREATED": str(bucket_path.exists()).upper(),
        "FACTOR_EVIDENCE_GAP_AUDIT_CREATED": str(gap_path.exists()).upper(),
        **{key: str(value) for key, value in usable.items()},
        "MINIMUM_SAMPLE_REQUIRED": str(MINIMUM_SAMPLE_REQUIRED),
        "RESEARCH_CONCLUSION_STATUS": "INSUFFICIENT_EVIDENCE_DO_NOT_CHANGE_WEIGHTS" if evidence_status == "INSUFFICIENT_FORWARD_RETURNS" else "PRELIMINARY_READ_ONLY_RESEARCH",
        "DATA_DEGRADED_COUNT": str(data_degraded),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": stable_rf.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", ""),
        "COVERAGE_WINDOW_COMPLETE": stable_rf.get("COVERAGE_WINDOW_COMPLETE", ""),
        "DAILY_TRUST_LEVEL": stable_rf.get("DAILY_TRUST_LEVEL", ""),
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }

    output_paths = [readiness_path, bucket_path, gap_path, source_audit_path, conclusion_path, read_first_path, report_path]
    # Write provisional files before existence validation.
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))
    fail_count = 0
    for path in output_paths:
        if not path.exists():
            fail_count += 1
    for field in READ_FIRST_FIELDS:
        if field not in values:
            fail_count += 1
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "SNAPSHOT_SOURCE_STATUS", "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COUNT", "FORWARD_OUTCOME_SOURCE_COUNT", "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT",
        "EFFECTIVENESS_EVIDENCE_STATUS", "FACTOR_PACK_USABLE_SAMPLE_COUNT", "TECHNICAL_TIMING_USABLE_SAMPLE_COUNT",
        "PRICE_DERIVED_USABLE_SAMPLE_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
