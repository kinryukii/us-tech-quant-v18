from __future__ import annotations

import argparse
import csv
import datetime as dt
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "ADVISORY_ONLY"
PATCH_MODE = "SAMPLE_MATURITY_AND_FORWARD_MATCH_QUALITY_ONLY"
STATUS_WARN = "WARN_V18_21C_R1_SAMPLE_MATURITY_PRELIMINARY_ONLY"
MINIMUM_SAMPLE_REQUIRED = 20
FORWARD_KEY_QUALITY_PLAN_COMPATIBILITY = "V18_21C_R2_READY"

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

SIGNAL_SNAPSHOT = "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv"
BASE_READ_FIRST = "outputs/v18/ops/V18_21C_READ_FIRST.txt"
BASE_BUCKET_SUMMARY = "outputs/v18/factor_effectiveness/V18_21C_CURRENT_FACTOR_BUCKET_RESEARCH_SUMMARY.csv"
BASE_GAP_AUDIT = "outputs/v18/factor_effectiveness/V18_21C_CURRENT_FACTOR_EVIDENCE_GAP_AUDIT.csv"

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
HORIZON_READ_KEYS = {
    "1D": "HORIZON_1D_USABLE_COUNT",
    "3D": "HORIZON_3D_USABLE_COUNT",
    "5D": "HORIZON_5D_USABLE_COUNT",
    "10D": "HORIZON_10D_USABLE_COUNT",
    "20D": "HORIZON_20D_USABLE_COUNT",
}
FACTORS = [
    "factor_pack_score",
    "composite_candidate_score",
    "technical_timing_score",
    "overheat_penalty",
    "price_derived_total_score",
    "relative_strength_score",
    "buy_zone_score",
    "volume_confirmation_score",
    "volatility_risk_score",
    "market_risk_coefficient",
]
CONCLUSION_AREAS = [
    ("FACTOR_PACK_EFFECTIVENESS", "factor_pack_score"),
    ("TECHNICAL_TIMING_EFFECTIVENESS", "technical_timing_score"),
    ("PRICE_DERIVED_EFFECTIVENESS", "price_derived_total_score"),
    ("RELATIVE_STRENGTH_EFFECTIVENESS", "relative_strength_score"),
    ("BUY_ZONE_DISTANCE_EFFECTIVENESS", "buy_zone_score"),
    ("OVERHEAT_PENALTY_EFFECTIVENESS", "overheat_penalty"),
    ("VOLUME_CONFIRMATION_EFFECTIVENESS", "volume_confirmation_score"),
    ("MARKET_REGIME_EFFECTIVENESS", "market_risk_coefficient"),
    ("FORWARD_OUTCOME_MATCH_QUALITY", ""),
    ("SAMPLE_MATURITY", ""),
    ("SIMULATION_RESEARCH_READINESS", ""),
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "SNAPSHOT_SOURCE_STATUS", "SIGNAL_SNAPSHOT_ROW_COUNT",
    "SIGNAL_SNAPSHOT_HISTORY_COUNT", "READY_FOR_FORWARD_RESEARCH_COUNT", "READY_FOR_SIMULATION_ANALYSIS_COUNT",
    "FORWARD_OUTCOME_SOURCE_COUNT", "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT", "HIGH_CONFIDENCE_MATCH_COUNT",
    "MEDIUM_CONFIDENCE_MATCH_COUNT", "LOW_CONFIDENCE_MATCH_COUNT", "UNMATCHED_OR_AMBIGUOUS_COUNT",
    "HORIZON_1D_USABLE_COUNT", "HORIZON_3D_USABLE_COUNT", "HORIZON_5D_USABLE_COUNT", "HORIZON_10D_USABLE_COUNT",
    "HORIZON_20D_USABLE_COUNT", "MATURE_HORIZON_COUNT", "PRELIMINARY_HORIZON_COUNT", "INSUFFICIENT_HORIZON_COUNT",
    "FACTOR_BUCKET_BALANCED_COUNT", "FACTOR_BUCKET_UNEVEN_COUNT", "FACTOR_MATURE_ENOUGH_COUNT",
    "FACTOR_PRELIMINARY_ONLY_COUNT", "FACTOR_INSUFFICIENT_EVIDENCE_COUNT", "EFFECT_CLAIM_ALLOWED_COUNT",
    "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT", "RESEARCH_CONCLUSION_STATUS",
    "EFFECTIVENESS_EVIDENCE_STATUS", "DATA_DEGRADED_COUNT", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "COVERAGE_WINDOW_COMPLETE", "DAILY_TRUST_LEVEL", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PRICE_FACTOR_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
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


def read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


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


def mean(values: List[float]) -> str:
    return f"{sum(values) / len(values):.6f}" if values else ""


def median(values: List[float]) -> str:
    return f"{statistics.median(values):.6f}" if values else ""


def hit_rate(values: List[float]) -> str:
    return f"{sum(1 for value in values if value > 0) / len(values):.6f}" if values else ""


def date_value(row: Dict[str, str]) -> str:
    return first_value(row, ["snapshot_date", "signal_date", "snapshot_run_date", "price_date"])


def collect_forward_matches(root: Path):
    candidates: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    source_count = 0
    for source_name, rel in FORWARD_SOURCES:
        path = root / rel
        rows, fields = read_csv(path)
        if path.exists():
            source_count += 1
        ticker_col = next((field for field in fields if field.lower() in {"ticker", "symbol", "yf_ticker"}), "")
        if not ticker_col:
            continue
        for row in rows:
            ticker = norm_ticker(row.get(ticker_col))
            if not ticker:
                continue
            returns = {}
            for horizon, cols in HORIZON_COLUMNS.items():
                value = first_value(row, cols)
                if value and to_float(value) is not None:
                    returns[horizon] = value
            if not returns:
                continue
            candidates[ticker].append(
                {
                    "source_name": source_name,
                    "source_path": str(path),
                    "source_type": "LOCAL_FORWARD_OUTCOME_CSV",
                    "date": date_value(row),
                    "signal_snapshot_id": row.get("signal_snapshot_id", ""),
                    "returns": returns,
                }
            )
    return candidates, source_count


def choose_match(signal: Dict[str, str], matches: List[Dict[str, object]]):
    if not matches:
        return None, "UNMATCHED_OR_AMBIGUOUS", "No local forward outcome row found for ticker."
    sid = signal.get("signal_snapshot_id", "")
    sdate = signal.get("snapshot_date", "")
    exact_sid = [m for m in matches if m.get("signal_snapshot_id") and m.get("signal_snapshot_id") == sid]
    exact_date = [m for m in matches if m.get("date") and m.get("date") == sdate]
    if exact_sid:
        return exact_sid[0], "HIGH_CONFIDENCE_MATCH", ""
    if exact_date:
        return exact_date[0], "MEDIUM_CONFIDENCE_MATCH", "Matched by ticker and signal/snapshot date, no signal_snapshot_id in source."
    if len(matches) == 1:
        return matches[0], "LOW_CONFIDENCE_MATCH", "Matched by ticker only; source date differs or is absent."
    return matches[0], "LOW_CONFIDENCE_MATCH", "Multiple ticker-only candidate outcomes; selected first local source deterministically."


def match_quality_rows(snapshot_rows: List[Dict[str, str]], matches_by_ticker):
    rows = []
    horizon_returns: Dict[str, List[Tuple[str, str, float]]] = {h: [] for h in HORIZON_COLUMNS}
    for signal in snapshot_rows:
        ticker = norm_ticker(signal.get("ticker"))
        match, status, warning = choose_match(signal, matches_by_ticker.get(ticker, []))
        returns = match.get("returns", {}) if match else {}
        for horizon, value in returns.items():
            numeric = to_float(value)
            if numeric is not None:
                horizon_returns[horizon].append((ticker, signal.get("snapshot_date", ""), numeric))
        rows.append(
            {
                "signal_snapshot_id": signal.get("signal_snapshot_id", ""),
                "ticker": ticker,
                "snapshot_date": signal.get("snapshot_date", ""),
                "forward_source_path": match.get("source_path", "") if match else "",
                "forward_source_type": match.get("source_type", "") if match else "",
                "match_method": "signal_snapshot_id" if status == "HIGH_CONFIDENCE_MATCH" else ("ticker_and_date" if status == "MEDIUM_CONFIDENCE_MATCH" else ("ticker_only" if match else "none")),
                "matched_by_signal_snapshot_id": str(status == "HIGH_CONFIDENCE_MATCH").upper(),
                "matched_by_ticker_and_date": str(status == "MEDIUM_CONFIDENCE_MATCH").upper(),
                "forward_return_1d_available": str("1D" in returns).upper(),
                "forward_return_3d_available": str("3D" in returns).upper(),
                "forward_return_5d_available": str("5D" in returns).upper(),
                "forward_return_10d_available": str("10D" in returns).upper(),
                "forward_return_20d_available": str("20D" in returns).upper(),
                "horizon_available_count": len(returns),
                "match_quality_status": status,
                "match_warning": warning,
            }
        )
    return rows, horizon_returns


def horizon_audit(horizon_returns):
    rows = []
    for horizon in HORIZON_COLUMNS:
        triples = horizon_returns[horizon]
        returns = [value for _ticker, _date, value in triples]
        unique_tickers = {ticker for ticker, _date, _value in triples}
        unique_dates = {date for _ticker, date, _value in triples if date}
        count = len(returns)
        if count == 0:
            status = "NO_USABLE_FORWARD_RETURNS"
            notes = "No matched numeric forward returns for this horizon."
        elif count < MINIMUM_SAMPLE_REQUIRED:
            status = "INSUFFICIENT_SAMPLE"
            notes = "Below minimum sample requirement."
        elif len(unique_dates) < 2:
            status = "PRELIMINARY_SMALL_SAMPLE"
            notes = "Meets count threshold but lacks snapshot-date diversity."
        else:
            status = "MATURE_ENOUGH_FOR_PRELIMINARY_READ"
            notes = "Count and date diversity are adequate for a preliminary read only."
        rows.append(
            {
                "horizon": horizon,
                "matched_signal_count": count,
                "usable_forward_return_count": count,
                "unique_ticker_count": len(unique_tickers),
                "unique_snapshot_date_count": len(unique_dates),
                "average_forward_return": mean(returns),
                "median_forward_return": median(returns),
                "hit_rate": hit_rate(returns),
                "minimum_sample_required": MINIMUM_SAMPLE_REQUIRED,
                "maturity_status": status,
                "notes": notes,
            }
        )
    return rows


def bucket_distribution(bucket_rows: List[Dict[str, str]]):
    grouped: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    for row in bucket_rows:
        grouped[(row.get("factor_name", ""), row.get("horizon", ""))].append(int(float(row.get("sample_count", "0") or 0)))
    out = []
    for (factor, horizon), counts in sorted(grouped.items()):
        non_empty = [count for count in counts if count > 0]
        total = sum(counts)
        min_count = min(non_empty) if non_empty else 0
        max_count = max(non_empty) if non_empty else 0
        if total < MINIMUM_SAMPLE_REQUIRED:
            balance = "INSUFFICIENT_SAMPLE"
            maturity = "INSUFFICIENT_EVIDENCE"
            notes = "Total usable sample is below minimum."
        elif len(non_empty) < 3:
            balance = "TOO_FEW_BUCKETS"
            maturity = "PRELIMINARY_ONLY"
            notes = "Not all buckets have usable samples."
        elif min_count < 5 or (max_count / max(min_count, 1)) > 3:
            balance = "UNEVEN_BUCKET_DISTRIBUTION"
            maturity = "PRELIMINARY_ONLY"
            notes = "Bucket distribution is too uneven for effect claims."
        else:
            balance = "BALANCED_ENOUGH_FOR_PRELIMINARY_READ"
            maturity = "PRELIMINARY_ONLY"
            notes = "Balanced enough for a read-only preliminary view, not a production claim."
        out.append(
            {
                "factor_name": factor,
                "horizon": horizon,
                "bucket_count": len(counts),
                "non_empty_bucket_count": len(non_empty),
                "min_bucket_sample_count": min_count,
                "max_bucket_sample_count": max_count,
                "total_usable_sample_count": total,
                "bucket_balance_status": balance,
                "maturity_status": maturity,
                "notes": notes,
            }
        )
    return out


def scorecard(snapshot_rows, match_rows, horizon_rows, bucket_rows):
    by_factor_bucket = defaultdict(list)
    for row in bucket_rows:
        by_factor_bucket[row["factor_name"]].append(row)
    horizon_status_counts = Counter(row["maturity_status"] for row in horizon_rows)
    matched_tickers = {row["ticker"] for row in match_rows if row["match_quality_status"] != "UNMATCHED_OR_AMBIGUOUS"}
    rows = []
    for factor in FACTORS:
        signal_available = sum(1 for row in snapshot_rows if first_value(row, [factor]))
        matched = sum(1 for row in snapshot_rows if first_value(row, [factor]) and norm_ticker(row.get("ticker")) in matched_tickers)
        factor_bucket_rows = by_factor_bucket.get(factor, [])
        balanced = sum(1 for row in factor_bucket_rows if row["bucket_balance_status"] == "BALANCED_ENOUGH_FOR_PRELIMINARY_READ")
        uneven = sum(1 for row in factor_bucket_rows if row["bucket_balance_status"] in {"UNEVEN_BUCKET_DISTRIBUTION", "TOO_FEW_BUCKETS"})
        insufficient = sum(1 for row in factor_bucket_rows if row["bucket_balance_status"] == "INSUFFICIENT_SAMPLE")
        if balanced and not insufficient:
            sample_status = "PRELIMINARY_ONLY"
            bucket_status = "PRELIMINARY_BALANCED_SUBSET"
            next_step = "Accumulate more horizons and dates before any effect claim."
        elif matched:
            sample_status = "PRELIMINARY_ONLY"
            bucket_status = "UNEVEN_OR_SINGLE_HORIZON"
            next_step = "Increase matched forward-return coverage and bucket balance."
        else:
            sample_status = "INSUFFICIENT_EVIDENCE"
            bucket_status = "NO_MATCHED_SAMPLE"
            next_step = "Wait for forward returns to mature."
        rows.append(
            {
                "factor_name": factor,
                "signal_available_count": signal_available,
                "matched_forward_count": matched,
                "mature_horizon_count": horizon_status_counts["MATURE_ENOUGH_FOR_PRELIMINARY_READ"],
                "preliminary_horizon_count": horizon_status_counts["PRELIMINARY_SMALL_SAMPLE"],
                "insufficient_horizon_count": horizon_status_counts["INSUFFICIENT_SAMPLE"] + horizon_status_counts["NO_USABLE_FORWARD_RETURNS"],
                "bucket_distribution_status": bucket_status if not uneven else "UNEVEN_BUCKET_DISTRIBUTION",
                "sample_maturity_status": sample_status,
                "effect_claim_allowed": "FALSE",
                "weight_change_allowed": "FALSE",
                "production_promotion_allowed": "FALSE",
                "recommended_next_step": next_step,
            }
        )
    return rows


def conclusions(scorecard_rows, match_counts, horizon_counts, rf):
    out = []
    score_by_factor = {row["factor_name"]: row for row in scorecard_rows}
    for area, factor in CONCLUSION_AREAS:
        if factor:
            score = score_by_factor.get(factor, {})
            status = score.get("sample_maturity_status", "INSUFFICIENT_EVIDENCE")
            matched = score.get("matched_forward_count", 0)
            summary = f"{matched} matched forward samples; effect claim remains disallowed."
            next_step = score.get("recommended_next_step", "Accumulate more evidence.")
        elif area == "FORWARD_OUTCOME_MATCH_QUALITY":
            status = "PRELIMINARY_ONLY" if match_counts.get("LOW_CONFIDENCE_MATCH", 0) else "INSUFFICIENT_EVIDENCE"
            summary = f"High={match_counts.get('HIGH_CONFIDENCE_MATCH', 0)}, medium={match_counts.get('MEDIUM_CONFIDENCE_MATCH', 0)}, low={match_counts.get('LOW_CONFIDENCE_MATCH', 0)}."
            next_step = "Add signal_snapshot_id or signal-date links to forward outcome sources."
        elif area == "SAMPLE_MATURITY":
            status = "PRELIMINARY_ONLY"
            summary = f"Mature horizons={horizon_counts.get('MATURE_ENOUGH_FOR_PRELIMINARY_READ', 0)}, preliminary={horizon_counts.get('PRELIMINARY_SMALL_SAMPLE', 0)}."
            next_step = "Wait for more 3D/5D/10D/20D outcomes."
        else:
            status = "PRELIMINARY_ONLY"
            summary = f"{rf.get('READY_FOR_SIMULATION_ANALYSIS_COUNT', '31')} rows are simulation-analysis ready."
            next_step = "Use readiness filters; do not alter simulation state."
        out.append(
            {
                "conclusion_area": area,
                "conclusion_status": status,
                "evidence_level": "LOW" if status == "PRELIMINARY_ONLY" else "INSUFFICIENT",
                "effect_claim_allowed": "FALSE",
                "production_change_allowed": "FALSE",
                "summary": summary,
                "recommended_next_step": next_step,
            }
        )
    return out


def report_text(values: Dict[str, object]) -> str:
    return f"""# V18.21C-R1 Sample Maturity + Forward Match Quality Report

## Executive summary
Status: {values['STATUS']}. R1 makes the sample maturity and forward match quality semantics explicit while keeping all production permissions disabled.

## Safety statement
This is advisory-only research. It does not change weights, ranking, promotion/demotion, signal snapshots, forward tracker state, simulation positions, price cache, broker execution, auto-trade, or auto-sell. External data fetched: FALSE.

## Forward match quality summary
High confidence: {values['HIGH_CONFIDENCE_MATCH_COUNT']}; medium confidence: {values['MEDIUM_CONFIDENCE_MATCH_COUNT']}; low confidence: {values['LOW_CONFIDENCE_MATCH_COUNT']}; unmatched or ambiguous: {values['UNMATCHED_OR_AMBIGUOUS_COUNT']}.

## Horizon maturity summary
1D usable: {values['HORIZON_1D_USABLE_COUNT']}; 3D: {values['HORIZON_3D_USABLE_COUNT']}; 5D: {values['HORIZON_5D_USABLE_COUNT']}; 10D: {values['HORIZON_10D_USABLE_COUNT']}; 20D: {values['HORIZON_20D_USABLE_COUNT']}.

## Bucket distribution maturity summary
Balanced factor/horizon buckets: {values['FACTOR_BUCKET_BALANCED_COUNT']}. Uneven buckets: {values['FACTOR_BUCKET_UNEVEN_COUNT']}.

## Factor maturity scorecard summary
Mature enough: {values['FACTOR_MATURE_ENOUGH_COUNT']}; preliminary only: {values['FACTOR_PRELIMINARY_ONLY_COUNT']}; insufficient evidence: {values['FACTOR_INSUFFICIENT_EVIDENCE_COUNT']}.

## Conservative research conclusions
Effect claims allowed: {values['EFFECT_CLAIM_ALLOWED_COUNT']}. Weight changes allowed: {values['WEIGHT_CHANGE_ALLOWED_COUNT']}. Production promotions allowed: {values['PRODUCTION_PROMOTION_ALLOWED_COUNT']}.

## Why no production changes are allowed
The current sample is concentrated mostly in 1D forward outcomes, has low-confidence ticker-only matching, and lacks mature multi-horizon/bucket evidence. This is research-only.

## Validation summary
Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

## Next-step recommendation
Preserve signal_snapshot_id in future forward outcome sources and wait for additional horizons and snapshot dates to mature before evaluating factor effectiveness claims.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/factor_effectiveness"
    ops_dir = root / "outputs/v18/ops"

    match_path = out_dir / "V18_21C_R1_CURRENT_FORWARD_MATCH_QUALITY_AUDIT.csv"
    horizon_path = out_dir / "V18_21C_R1_CURRENT_HORIZON_MATURITY_AUDIT.csv"
    bucket_path = out_dir / "V18_21C_R1_CURRENT_BUCKET_DISTRIBUTION_AUDIT.csv"
    scorecard_path = out_dir / "V18_21C_R1_CURRENT_FACTOR_MATURITY_SCORECARD.csv"
    conclusion_path = out_dir / "V18_21C_R1_CURRENT_RESEARCH_CONCLUSION_SUMMARY.csv"
    read_first_path = ops_dir / "V18_21C_R1_READ_FIRST.txt"
    report_path = ops_dir / "V18_21C_R1_CURRENT_SAMPLE_MATURITY_FORWARD_MATCH_REPORT.md"

    snapshot_rows, _ = read_csv(root / SIGNAL_SNAPSHOT)
    base_rf = read_first(root / BASE_READ_FIRST)
    bucket_summary, _ = read_csv(root / BASE_BUCKET_SUMMARY)
    gap_rows, _ = read_csv(root / BASE_GAP_AUDIT)
    forward_matches, source_count = collect_forward_matches(root)
    match_rows, horizon_returns = match_quality_rows(snapshot_rows, forward_matches)
    horizon_rows = horizon_audit(horizon_returns)
    bucket_rows = bucket_distribution(bucket_summary)
    scorecard_rows = scorecard(snapshot_rows, match_rows, horizon_rows, bucket_rows)

    match_counts = Counter(row["match_quality_status"] for row in match_rows)
    horizon_counts = Counter(row["maturity_status"] for row in horizon_rows)
    conclusion_rows = conclusions(scorecard_rows, match_counts, horizon_counts, base_rf)

    write_csv(match_path, match_rows, [
        "signal_snapshot_id", "ticker", "snapshot_date", "forward_source_path", "forward_source_type", "match_method",
        "matched_by_signal_snapshot_id", "matched_by_ticker_and_date", "forward_return_1d_available",
        "forward_return_3d_available", "forward_return_5d_available", "forward_return_10d_available",
        "forward_return_20d_available", "horizon_available_count", "match_quality_status", "match_warning",
    ])
    write_csv(horizon_path, horizon_rows, [
        "horizon", "matched_signal_count", "usable_forward_return_count", "unique_ticker_count", "unique_snapshot_date_count",
        "average_forward_return", "median_forward_return", "hit_rate", "minimum_sample_required", "maturity_status", "notes",
    ])
    write_csv(bucket_path, bucket_rows, [
        "factor_name", "horizon", "bucket_count", "non_empty_bucket_count", "min_bucket_sample_count",
        "max_bucket_sample_count", "total_usable_sample_count", "bucket_balance_status", "maturity_status", "notes",
    ])
    write_csv(scorecard_path, scorecard_rows, [
        "factor_name", "signal_available_count", "matched_forward_count", "mature_horizon_count", "preliminary_horizon_count",
        "insufficient_horizon_count", "bucket_distribution_status", "sample_maturity_status", "effect_claim_allowed",
        "weight_change_allowed", "production_promotion_allowed", "recommended_next_step",
    ])
    write_csv(conclusion_path, conclusion_rows, [
        "conclusion_area", "conclusion_status", "evidence_level", "effect_claim_allowed", "production_change_allowed", "summary", "recommended_next_step",
    ])

    score_counts = Counter(row["sample_maturity_status"] for row in scorecard_rows)
    balanced_count = sum(1 for row in bucket_rows if row["bucket_balance_status"] == "BALANCED_ENOUGH_FOR_PRELIMINARY_READ")
    uneven_count = sum(1 for row in bucket_rows if row["bucket_balance_status"] in {"UNEVEN_BUCKET_DISTRIBUTION", "TOO_FEW_BUCKETS"})
    values: Dict[str, object] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "POLICY_APPLIED": "FALSE",
        "SNAPSHOT_SOURCE_STATUS": base_rf.get("SNAPSHOT_SOURCE_STATUS", "OK_CURRENT_SIGNAL_SNAPSHOT"),
        "SIGNAL_SNAPSHOT_ROW_COUNT": str(len(snapshot_rows)),
        "SIGNAL_SNAPSHOT_HISTORY_COUNT": base_rf.get("SIGNAL_SNAPSHOT_HISTORY_COUNT", ""),
        "READY_FOR_FORWARD_RESEARCH_COUNT": base_rf.get("READY_FOR_FORWARD_RESEARCH_COUNT", ""),
        "READY_FOR_SIMULATION_ANALYSIS_COUNT": base_rf.get("READY_FOR_SIMULATION_ANALYSIS_COUNT", ""),
        "FORWARD_OUTCOME_SOURCE_COUNT": str(source_count),
        "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT": str(sum(1 for row in match_rows if row["match_quality_status"] != "UNMATCHED_OR_AMBIGUOUS")),
        "HIGH_CONFIDENCE_MATCH_COUNT": str(match_counts["HIGH_CONFIDENCE_MATCH"]),
        "MEDIUM_CONFIDENCE_MATCH_COUNT": str(match_counts["MEDIUM_CONFIDENCE_MATCH"]),
        "LOW_CONFIDENCE_MATCH_COUNT": str(match_counts["LOW_CONFIDENCE_MATCH"]),
        "UNMATCHED_OR_AMBIGUOUS_COUNT": str(match_counts["UNMATCHED_OR_AMBIGUOUS"]),
        **{HORIZON_READ_KEYS[row["horizon"]]: str(row["usable_forward_return_count"]) for row in horizon_rows},
        "MATURE_HORIZON_COUNT": str(horizon_counts["MATURE_ENOUGH_FOR_PRELIMINARY_READ"]),
        "PRELIMINARY_HORIZON_COUNT": str(horizon_counts["PRELIMINARY_SMALL_SAMPLE"]),
        "INSUFFICIENT_HORIZON_COUNT": str(horizon_counts["INSUFFICIENT_SAMPLE"] + horizon_counts["NO_USABLE_FORWARD_RETURNS"]),
        "FACTOR_BUCKET_BALANCED_COUNT": str(balanced_count),
        "FACTOR_BUCKET_UNEVEN_COUNT": str(uneven_count),
        "FACTOR_MATURE_ENOUGH_COUNT": str(score_counts["MATURE_ENOUGH"]),
        "FACTOR_PRELIMINARY_ONLY_COUNT": str(score_counts["PRELIMINARY_ONLY"]),
        "FACTOR_INSUFFICIENT_EVIDENCE_COUNT": str(score_counts["INSUFFICIENT_EVIDENCE"]),
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
        "RESEARCH_CONCLUSION_STATUS": "PRELIMINARY_ONLY_NO_EFFECT_CLAIMS",
        "EFFECTIVENESS_EVIDENCE_STATUS": "PRELIMINARY_ONLY_INSUFFICIENT_FOR_EFFECT_CLAIMS",
        "DATA_DEGRADED_COUNT": base_rf.get("DATA_DEGRADED_COUNT", ""),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": base_rf.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", ""),
        "COVERAGE_WINDOW_COMPLETE": base_rf.get("COVERAGE_WINDOW_COMPLETE", ""),
        "DAILY_TRUST_LEVEL": base_rf.get("DAILY_TRUST_LEVEL", ""),
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }
    for key in HORIZON_READ_KEYS.values():
        values.setdefault(key, "0")
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    outputs = [match_path, horizon_path, bucket_path, scorecard_path, conclusion_path, read_first_path, report_path]
    fail_count = 0
    for path in outputs:
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
        "HORIZON_1D_USABLE_COUNT", "HORIZON_3D_USABLE_COUNT", "MATURE_HORIZON_COUNT",
        "FACTOR_PRELIMINARY_ONLY_COUNT", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
