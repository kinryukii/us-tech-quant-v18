from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


PATCH_VERSION = "V18.49A-R1"
PATCH_NAME = "POINT_IN_TIME_EVIDENCE_AND_EXIT_DATE_REPAIR"

POLICY_GRID_COLUMNS = [
    "policy_id", "policy_name", "entry_rule", "exit_rule", "position_size_rule",
    "factor_weight_description", "technical_weight_description", "event_risk_rule",
    "options_risk_rule", "official_ranking_changed", "factor_weights_changed",
    "real_trade_execution_allowed",
]

BACKTEST_COLUMNS = [
    "run_date", "signal_date", "policy_id", "ticker", "entry_rank", "entry_score", "entry_price",
    "entry_price_date", "simulated_entry_action", "simulated_exit_rule", "simulated_position_size_label",
    "event_risk", "options_risk", "technical_status", "pullback_status", "forward_5d_return",
    "forward_10d_return", "forward_20d_return", "forward_60d_return", "forward_5d_date",
    "forward_10d_date", "forward_20d_date", "forward_60d_date", "selected_forward_horizon",
    "selected_forward_date", "selected_forward_return_source", "factor_point_in_time_status",
    "technical_point_in_time_status", "event_risk_point_in_time_status",
    "options_risk_point_in_time_status", "event_options_history_status", "comparison_basis_status",
    "forward_status", "exit_date", "exit_price", "realized_policy_return", "data_quality_flag", "reason",
]

SUMMARY_COLUMNS = [
    "policy_id", "selected_trade_count", "completed_trade_count", "pending_trade_count",
    "win_rate_5d", "win_rate_10d", "win_rate_20d", "avg_return_5d", "avg_return_10d",
    "avg_return_20d", "median_return_5d", "median_return_10d", "median_return_20d",
    "worst_return_20d", "max_drawdown_proxy", "large_loss_count", "event_risk_loss_count",
    "options_risk_loss_count", "technical_exit_success_count", "evidence_quality",
    "point_in_time_filter_coverage_pct", "event_options_history_coverage_pct",
    "matched_signal_date_count", "matched_completed_5d_count", "matched_completed_10d_count",
    "matched_completed_20d_count", "min_completed_threshold_met", "comparison_basis_status",
    "recommendation_cap_reason", "recommendation_label", "recommendation_reason",
]

RECOMMENDATION_COLUMNS = [
    "recommended_for_simulation", "recommended_policy_id", "recommended_sim_style",
    "confidence_level", "evidence_quality", "reason", "not_for_official_ranking_reason",
    "not_for_real_trading_reason",
]

DIAG_COLUMNS = ["source_name", "source_path", "found", "usable", "row_count", "notes"]


def clean(value: object, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def norm_ticker(value: object) -> str:
    text = clean(value, "").upper().strip("'\"")
    return text[1:] if text.startswith("$") else text


def parse_float(value: object) -> float | None:
    try:
        text = clean(value, "")
        if not text or text.upper() in {"UNKNOWN", "NONE", "NAN", "PENDING"}:
            return None
        out = float(text)
        return None if math.isnan(out) else out
    except (TypeError, ValueError):
        return None


def parse_int(value: object, default: int = 0) -> int:
    try:
        text = clean(value, "")
        if not text or text.upper() in {"UNKNOWN", "NONE", "NAN"}:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    text = clean(value, "")
    if not text or text.upper() in {"UNKNOWN", "NONE", "NAN", "PENDING"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def fmt(value: float | None, digits: int = 6) -> str:
    return "UNKNOWN" if value is None else f"{value:.{digits}f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def discover(root: Path) -> tuple[dict[str, Path | None], list[dict[str, str]]]:
    paths = {
        "current_top20": first_existing([
            root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
            root / "outputs/v18/ranked_candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        ]),
        "ranked_candidates": first_existing([
            root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
            root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv",
        ]),
        "candidate_forward_tracker": first_existing([
            root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
            root / "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv",
            root / "outputs/v18/candidates/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
        ]),
        "factor_forward_tracker": first_existing([
            root / "state/v18/forward_outcome/V18_4A_FACTOR_FORWARD_TRACKER.csv",
            root / "outputs/v18/forward_outcome/V18_4A_CURRENT_FACTOR_SNAPSHOT.csv",
        ]),
        "factor_pack": first_existing([
            root / "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv",
            root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        ]),
        "technical_timing": first_existing([
            root / "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv",
            root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        ]),
        "event_risk": root / "outputs/v18/event_risk/V18_47C_TOP20_EVENT_EARNINGS_RISK.csv",
        "options_risk": root / "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_RADAR.csv",
        "priority_tracker": root / "outputs/v18/tracking/V18_47B_TOP20_PRIORITY_TRACKER.csv",
        "factor_shadow_outcome": root / "state/v18/factor_shadow_outcome_tracker.csv",
    }
    diagnostics = []
    for name, path in paths.items():
        rows = read_csv(path) if path and path.exists() else []
        diagnostics.append({
            "source_name": name,
            "source_path": str(path) if path else "NONE",
            "found": "TRUE" if path and path.exists() else "FALSE",
            "usable": "TRUE" if rows else "FALSE",
            "row_count": str(len(rows)),
            "notes": "LOCAL_SOURCE_ONLY_NO_NETWORK",
        })
    return paths, diagnostics


def by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {norm_ticker(row.get("ticker")): row for row in rows if norm_ticker(row.get("ticker"))}


def source_date(row: dict[str, str]) -> date | None:
    for column in ("snapshot_date", "latest_price_date", "price_date", "snapshot_run_date", "snapshot_price_date"):
        parsed = parse_date(row.get(column))
        if parsed:
            return parsed
    return None


def point_in_time_lookup(rows: list[dict[str, str]]) -> dict[str, list[tuple[date, dict[str, str]]]]:
    out: dict[str, list[tuple[date, dict[str, str]]]] = defaultdict(list)
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        dt = source_date(row)
        if ticker and dt:
            out[ticker].append((dt, row))
    for ticker in out:
        out[ticker].sort(key=lambda item: item[0])
    return out


def nearest_point_in_time(index: dict[str, list[tuple[date, dict[str, str]]]], ticker: str, signal_date: date | None) -> tuple[dict[str, str], str]:
    if not index:
        return {}, "SOURCE_MISSING"
    if signal_date is None:
        return {}, "UNKNOWN_POINT_IN_TIME_UNAVAILABLE"
    rows = index.get(ticker, [])
    if not rows:
        return {}, "UNKNOWN_POINT_IN_TIME_UNAVAILABLE"
    prior = [(dt, row) for dt, row in rows if dt <= signal_date]
    if not prior:
        return {}, "UNKNOWN_POINT_IN_TIME_UNAVAILABLE"
    dt, row = prior[-1]
    return row, "POINT_IN_TIME_MATCHED" if dt == signal_date else "POINT_IN_TIME_PRIOR_MATCHED"


def normalize_signal_rows(rows: list[dict[str, str]], source_name: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        normalized = dict(row)
        if "snapshot_run_date" in row:
            normalized["signal_date"] = clean(row.get("snapshot_run_date"), "")
            normalized["price_date"] = clean(row.get("snapshot_price_date"), "")
            normalized["rank"] = clean(row.get("rank_overall"), "")
            normalized["score"] = clean(row.get("composite_score"), "")
            normalized["price_at_signal"] = clean(row.get("latest_close"), "")
            if parse_float(row.get("return_5obs_pct")) is not None:
                normalized["forward_5d_return"] = fmt((parse_float(row.get("return_5obs_pct")) or 0) / 100)
                normalized["forward_5d_price"] = clean(row.get("target_close_5obs"), "")
                normalized["forward_5d_date"] = clean(row.get("target_price_date_5obs"), "UNKNOWN")
            if parse_float(row.get("return_10obs_pct")) is not None:
                normalized["forward_10d_return"] = fmt((parse_float(row.get("return_10obs_pct")) or 0) / 100)
                normalized["forward_10d_price"] = clean(row.get("target_close_10obs"), "")
                normalized["forward_10d_date"] = clean(row.get("target_price_date_10obs"), "UNKNOWN")
            if parse_float(row.get("return_20obs_pct")) is not None:
                normalized["forward_20d_return"] = fmt((parse_float(row.get("return_20obs_pct")) or 0) / 100)
                normalized["forward_20d_price"] = clean(row.get("target_close_20obs"), "")
                normalized["forward_20d_date"] = clean(row.get("target_price_date_20obs"), "UNKNOWN")
            if parse_float(row.get("return_60obs_pct")) is not None:
                normalized["forward_60d_return"] = fmt((parse_float(row.get("return_60obs_pct")) or 0) / 100)
                normalized["forward_60d_price"] = clean(row.get("target_close_60obs"), "")
                normalized["forward_60d_date"] = clean(row.get("target_price_date_60obs"), "UNKNOWN")
        for horizon in ("5d", "10d", "20d", "60d"):
            date_key = f"forward_{horizon}_date"
            if date_key not in normalized:
                normalized[date_key] = clean(normalized.get(date_key), "UNKNOWN")
        normalized["_source_name"] = source_name
        out.append(normalized)
    return out


def policy_grid() -> list[dict[str, str]]:
    base = [
        ("BASELINE_TOP20", "Baseline Top20", "Official Top20/current ranking order", "FIXED_HOLD_20D_PLUS_RANK_DETERIORATION_IF_AVAILABLE", "EQUAL_WEIGHT", "Current baseline score order only", "Current technical fields only", "No extra event filter", "No extra options filter"),
        ("FACTOR_HEAVY", "Factor Heavy", "Prefer factor_pack_score/factor_score", "RANK_DETERIORATION_EXIT_PLUS_FIXED_HOLD_20D", "EQUAL_WEIGHT", "Higher simulated emphasis on factor score", "Secondary technical tie-breaker", "No extra event filter", "No extra options filter"),
        ("TECHNICAL_HEAVY", "Technical Heavy", "Prefer technical_timing_score/positive labels", "TECHNICAL_DETERIORATION_EXIT_PLUS_FIXED_HOLD_10D", "EQUAL_WEIGHT", "Secondary factor tie-breaker", "Higher simulated emphasis on technical timing", "No extra event filter", "No extra options filter"),
        ("PULLBACK_ENTRY", "Pullback Entry", "Prefer BB_BELOW_LOWER/BB_LOWER_HALF/pullback labels", "OVERHEAT_EXIT_PLUS_FIXED_HOLD_20D", "EQUAL_WEIGHT", "Baseline factor context", "Pullback labels preferred", "No extra event filter", "No extra options filter"),
        ("EVENT_FILTERED", "Event Filtered", "Penalize or skip HIGH/EXTREME/UNKNOWN event risk", "EVENT_RISK_WORSEN_EXIT_PLUS_FIXED_HOLD_20D", "SMALL_SIZE_ONLY", "Baseline factor context", "Baseline technical context", "Skip HIGH/EXTREME/UNKNOWN event risk when available", "No extra options filter"),
        ("OPTIONS_RISK_FILTERED", "Options Risk Filtered", "Penalize or skip HIGH/EXTREME options risk", "OPTIONS_RISK_WORSEN_EXIT_PLUS_FIXED_HOLD_20D", "SMALL_SIZE_ONLY", "Baseline factor context", "Baseline technical context", "Baseline event context", "Skip HIGH/EXTREME options risk when available"),
        ("DEFENSIVE", "Defensive", "Fewer names with stricter event/options/technical filters", "EARLY_DETERIORATION_EXIT_PLUS_FIXED_HOLD_10D", "DEFENSIVE_HALF_SIZE", "Require acceptable rank/factor context", "Avoid weak technical labels when available", "Skip HIGH/EXTREME/UNKNOWN event risk", "Skip HIGH/EXTREME/UNKNOWN options risk"),
        ("AGGRESSIVE_TEST", "Aggressive Test", "More names with looser filters", "LATE_RISK_WORSEN_EXIT_PLUS_FIXED_HOLD_20D", "AGGRESSIVE_TEST_SIZE", "Looser score/rank inclusion", "Accept neutral/positive technical context", "Do not skip unless EXTREME", "Do not skip unless EXTREME"),
    ]
    return [{
        "policy_id": p[0], "policy_name": p[1], "entry_rule": p[2], "exit_rule": p[3],
        "position_size_rule": p[4], "factor_weight_description": p[5],
        "technical_weight_description": p[6], "event_risk_rule": p[7], "options_risk_rule": p[8],
        "official_ranking_changed": "FALSE", "factor_weights_changed": "FALSE",
        "real_trade_execution_allowed": "FALSE",
    } for p in base]


def enrich_signal(
    row: dict[str, str],
    factor_index: dict[str, list[tuple[date, dict[str, str]]]],
    tech_index: dict[str, list[tuple[date, dict[str, str]]]],
    event_index: dict[str, list[tuple[date, dict[str, str]]]],
    option_index: dict[str, list[tuple[date, dict[str, str]]]],
) -> dict[str, str]:
    ticker = norm_ticker(row.get("ticker"))
    signal_dt = parse_date(row.get("signal_date") or row.get("latest_price_date") or row.get("price_date"))
    factor_row, factor_status = nearest_point_in_time(factor_index, ticker, signal_dt)
    tech_row, tech_status = nearest_point_in_time(tech_index, ticker, signal_dt)
    event_row, event_status = nearest_point_in_time(event_index, ticker, signal_dt)
    option_row, option_status = nearest_point_in_time(option_index, ticker, signal_dt)
    if row.get("_source_name") == "factor_forward_tracker":
        factor_status = "POINT_IN_TIME_MATCHED"
    if row.get("_source_name") == "candidate_forward_tracker" and clean(row.get("risk_label"), ""):
        tech_status = "POINT_IN_TIME_MATCHED"
    out = dict(row)
    out["_ticker"] = ticker
    out["_rank"] = clean(row.get("rank") or row.get("entry_rank"), "999999")
    out["_score"] = clean(row.get("score") or row.get("composite_candidate_score") or row.get("entry_score"), "UNKNOWN")
    out["_factor_score"] = clean(row.get("factor_score") or row.get("composite_score") or factor_row.get("factor_pack_score"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_technical_score"] = clean(row.get("technical_score") or tech_row.get("technical_timing_score"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_event_risk"] = clean(event_row.get("final_event_risk_level") or row.get("event_risk_status"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_options_risk"] = clean(option_row.get("overall_options_risk_level"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_technical_status"] = clean(row.get("technical_status") or row.get("risk_label") or tech_row.get("technical_signal") or tech_row.get("technical_warning_label"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_pullback_status"] = clean(row.get("pullback_status") or tech_row.get("bb_status") or factor_row.get("shadow_side_hint"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_overheat_status"] = clean(row.get("overheat_status") or tech_row.get("rsi_status"), "UNKNOWN_POINT_IN_TIME_UNAVAILABLE")
    out["_factor_point_in_time_status"] = factor_status
    out["_technical_point_in_time_status"] = tech_status
    out["_event_risk_point_in_time_status"] = event_status
    out["_options_risk_point_in_time_status"] = option_status
    event_ok = event_status in {"POINT_IN_TIME_MATCHED", "POINT_IN_TIME_PRIOR_MATCHED"}
    options_ok = option_status in {"POINT_IN_TIME_MATCHED", "POINT_IN_TIME_PRIOR_MATCHED"}
    out["_event_options_history_status"] = "POINT_IN_TIME_EVENT_OPTIONS_HISTORY_AVAILABLE" if event_ok and options_ok else "LIMITED_EVENT_OPTIONS_HISTORY"
    return out


def bad_risk(label: str, include_unknown: bool = False) -> bool:
    upper = label.upper()
    return "HIGH" in upper or "EXTREME" in upper or (include_unknown and "UNKNOWN" in upper)


def usable_event_options_history(row: dict[str, str]) -> bool:
    return row.get("_event_options_history_status") == "POINT_IN_TIME_EVENT_OPTIONS_HISTORY_AVAILABLE"


def technical_positive(label: str) -> bool:
    upper = label.upper()
    return "POSITIVE" in upper or "WATCH" in upper or "RECOMPUTE" in upper


def pullback_positive(label: str) -> bool:
    upper = label.upper()
    return "BB_BELOW_LOWER" in upper or "BB_LOWER_HALF" in upper or "PULLBACK" in upper or "BB_LOW" in upper


def policy_score(policy_id: str, row: dict[str, str]) -> float:
    rank = parse_int(row.get("_rank"), 999999)
    base = 1000 - rank
    factor = parse_float(row.get("_factor_score")) or 0
    technical = parse_float(row.get("_technical_score")) or 0
    score = parse_float(row.get("_score")) or 0
    if policy_id == "BASELINE_TOP20":
        return base
    if policy_id == "FACTOR_HEAVY":
        return factor * 2.0 + score + base * 0.05
    if policy_id == "TECHNICAL_HEAVY":
        return technical * 2.0 + score + (30 if technical_positive(row["_technical_status"]) else 0)
    if policy_id == "PULLBACK_ENTRY":
        return score + base * 0.05 + (75 if pullback_positive(row["_pullback_status"]) else -50)
    if policy_id == "EVENT_FILTERED":
        return score + base * 0.05 - (200 if bad_risk(row["_event_risk"], True) else 0)
    if policy_id == "OPTIONS_RISK_FILTERED":
        return score + base * 0.05 - (200 if bad_risk(row["_options_risk"], False) else 0)
    if policy_id == "DEFENSIVE":
        penalty = 0
        if bad_risk(row["_event_risk"], True):
            penalty += 300
        if bad_risk(row["_options_risk"], True):
            penalty += 300
        if "NEGATIVE" in row["_technical_status"].upper():
            penalty += 100
        return score + factor + technical + base * 0.05 - penalty
    if policy_id == "AGGRESSIVE_TEST":
        penalty = 150 if "EXTREME" in row["_event_risk"].upper() or "EXTREME" in row["_options_risk"].upper() else 0
        return score + factor * 0.5 + technical * 0.5 + base * 0.03 - penalty
    return score


def select_for_policy(policy_id: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    limits = {
        "BASELINE_TOP20": 20, "FACTOR_HEAVY": 15, "TECHNICAL_HEAVY": 15, "PULLBACK_ENTRY": 12,
        "EVENT_FILTERED": 15, "OPTIONS_RISK_FILTERED": 15, "DEFENSIVE": 8, "AGGRESSIVE_TEST": 25,
    }
    candidates = []
    for row in rows:
        if policy_id == "PULLBACK_ENTRY" and not pullback_positive(row["_pullback_status"]):
            continue
        if policy_id == "EVENT_FILTERED" and bad_risk(row["_event_risk"], True):
            continue
        if policy_id == "OPTIONS_RISK_FILTERED" and bad_risk(row["_options_risk"], False):
            continue
        if policy_id in {"EVENT_FILTERED", "OPTIONS_RISK_FILTERED", "DEFENSIVE"} and not usable_event_options_history(row):
            continue
        if policy_id == "DEFENSIVE" and (bad_risk(row["_event_risk"], True) or bad_risk(row["_options_risk"], True)):
            continue
        if policy_id == "AGGRESSIVE_TEST" and ("EXTREME" in row["_event_risk"].upper() or "EXTREME" in row["_options_risk"].upper()):
            continue
        candidates.append(row)
    candidates.sort(key=lambda row: policy_score(policy_id, row), reverse=True)
    return candidates[:limits[policy_id]]


def best_return(row: dict[str, str], preferred: str) -> tuple[float | None, str, str, str]:
    order = [preferred, "forward_20d_return", "forward_10d_return", "forward_5d_return"]
    for column in order:
        value = parse_float(row.get(column))
        if value is not None:
            horizon = column.replace("forward_", "").replace("_return", "")
            forward_date = clean(row.get(f"forward_{horizon}_date"), "UNKNOWN_ACTUAL_EXIT_DATE")
            return value, horizon, forward_date, clean(row.get("_source_name"), "LOCAL_FORWARD_TRACKER")
    return None, "PENDING_FORWARD_PRICE", "UNKNOWN_ACTUAL_EXIT_DATE", "NONE"


def build_backtest_rows(run_date: str, signals: list[dict[str, str]], policies: list[dict[str, str]]) -> list[dict[str, str]]:
    by_date: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in signals:
        signal_date = clean(row.get("signal_date") or row.get("latest_price_date") or row.get("price_date"), "")
        if signal_date and norm_ticker(row.get("_ticker") or row.get("ticker")):
            by_date[signal_date].append(row)
    out = []
    for signal_date, rows in sorted(by_date.items()):
        for policy in policies:
            policy_id = policy["policy_id"]
            for row in select_for_policy(policy_id, rows):
                preferred = "forward_10d_return" if policy_id in {"TECHNICAL_HEAVY", "DEFENSIVE"} else "forward_20d_return"
                realized, exit_horizon, selected_forward_date, return_source = best_return(row, preferred)
                forward_status = "COMPLETED_FORWARD_RETURN" if realized is not None else "PENDING_FORWARD_PRICE"
                exit_price = None
                exit_date = "UNKNOWN_ACTUAL_EXIT_DATE"
                if exit_horizon != "PENDING_FORWARD_PRICE":
                    exit_price = parse_float(row.get(f"forward_{exit_horizon}_price"))
                    exit_date = selected_forward_date if parse_date(selected_forward_date) else "UNKNOWN_ACTUAL_EXIT_DATE"
                data_quality = "COMPLETE" if parse_float(row.get("forward_20d_return")) is not None else "PARTIAL_FORWARD_RETURN" if realized is not None else "PENDING_FORWARD_PRICE"
                comparison_basis = "COMPARISON_BASIS_LIMITED" if realized is not None and exit_horizon == "5d" else "MATCHED_BASIS_OK" if realized is not None else "INSUFFICIENT_MATCHED_EVIDENCE"
                out.append({
                    "run_date": run_date,
                    "signal_date": signal_date,
                    "policy_id": policy_id,
                    "ticker": row["_ticker"],
                    "entry_rank": clean(row.get("_rank")),
                    "entry_score": clean(row.get("_score")),
                    "entry_price": clean(row.get("price_at_signal") or row.get("latest_close") or row.get("close")),
                    "entry_price_date": clean(row.get("price_date") or row.get("latest_price_date") or signal_date),
                    "simulated_entry_action": "SIMULATED_ENTRY_RESEARCH_ONLY",
                    "simulated_exit_rule": policy["exit_rule"],
                    "simulated_position_size_label": policy["position_size_rule"],
                    "event_risk": row["_event_risk"],
                    "options_risk": row["_options_risk"],
                    "technical_status": row["_technical_status"],
                    "pullback_status": row["_pullback_status"],
                    "forward_5d_return": clean(row.get("forward_5d_return"), "UNKNOWN"),
                    "forward_10d_return": clean(row.get("forward_10d_return"), "UNKNOWN"),
                    "forward_20d_return": clean(row.get("forward_20d_return"), "UNKNOWN"),
                    "forward_60d_return": clean(row.get("forward_60d_return"), "UNKNOWN"),
                    "forward_5d_date": clean(row.get("forward_5d_date"), "UNKNOWN"),
                    "forward_10d_date": clean(row.get("forward_10d_date"), "UNKNOWN"),
                    "forward_20d_date": clean(row.get("forward_20d_date"), "UNKNOWN"),
                    "forward_60d_date": clean(row.get("forward_60d_date"), "UNKNOWN"),
                    "selected_forward_horizon": exit_horizon,
                    "selected_forward_date": selected_forward_date,
                    "selected_forward_return_source": return_source,
                    "factor_point_in_time_status": row["_factor_point_in_time_status"],
                    "technical_point_in_time_status": row["_technical_point_in_time_status"],
                    "event_risk_point_in_time_status": row["_event_risk_point_in_time_status"],
                    "options_risk_point_in_time_status": row["_options_risk_point_in_time_status"],
                    "event_options_history_status": row["_event_options_history_status"],
                    "comparison_basis_status": comparison_basis,
                    "forward_status": forward_status,
                    "exit_date": exit_date,
                    "exit_price": fmt(exit_price),
                    "realized_policy_return": fmt(realized),
                    "data_quality_flag": data_quality,
                    "reason": "SIMULATION_ONLY_POLICY_ATTRIBUTION_NO_REAL_TRADE_INSTRUCTION",
                })
    return out


def numeric(rows: list[dict[str, str]], column: str) -> list[float]:
    return [v for v in (parse_float(row.get(column)) for row in rows) if v is not None]


def win_rate(values: list[float]) -> str:
    return "UNKNOWN" if not values else f"{sum(1 for v in values if v > 0) / len(values):.4f}"


def evidence_quality(completed: int) -> str:
    if completed >= 100:
        return "HIGH"
    if completed >= 40:
        return "MEDIUM"
    if completed >= 10:
        return "LOW"
    return "INSUFFICIENT"


def comparison_status(matched_5d: int, matched_10d: int, matched_20d: int) -> str:
    if matched_20d >= 10 or matched_10d >= 10:
        return "MATCHED_BASIS_OK"
    if matched_5d >= 10:
        return "COMPARISON_BASIS_LIMITED"
    return "INSUFFICIENT_MATCHED_EVIDENCE"


def summarize(backtest_rows: list[dict[str, str]], policies: list[dict[str, str]]) -> list[dict[str, str]]:
    by_policy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in backtest_rows:
        by_policy[row["policy_id"]].append(row)
    out = []
    for policy in policies:
        pid = policy["policy_id"]
        rows = by_policy.get(pid, [])
        completed = [row for row in rows if parse_float(row.get("realized_policy_return")) is not None]
        r5, r10, r20 = numeric(rows, "forward_5d_return"), numeric(rows, "forward_10d_return"), numeric(rows, "forward_20d_return")
        realized = numeric(rows, "realized_policy_return")
        eq = evidence_quality(len(completed))
        pit_rows = [
            row for row in rows
            if row["factor_point_in_time_status"] in {"POINT_IN_TIME_MATCHED", "POINT_IN_TIME_PRIOR_MATCHED"}
            or row["technical_point_in_time_status"] in {"POINT_IN_TIME_MATCHED", "POINT_IN_TIME_PRIOR_MATCHED"}
        ]
        event_options_rows = [row for row in rows if row["event_options_history_status"] == "POINT_IN_TIME_EVENT_OPTIONS_HISTORY_AVAILABLE"]
        signal_dates = {row["signal_date"] for row in completed}
        matched_5d = sum(1 for row in rows if parse_float(row.get("forward_5d_return")) is not None and parse_date(row.get("forward_5d_date")))
        matched_10d = sum(1 for row in rows if parse_float(row.get("forward_10d_return")) is not None and parse_date(row.get("forward_10d_date")))
        matched_20d = sum(1 for row in rows if parse_float(row.get("forward_20d_return")) is not None and parse_date(row.get("forward_20d_date")))
        basis_status = comparison_status(matched_5d, matched_10d, matched_20d)
        threshold_met = "TRUE" if basis_status != "INSUFFICIENT_MATCHED_EVIDENCE" else "FALSE"
        avg20 = sum(r20) / len(r20) if r20 else None
        worst20 = min(r20) if r20 else None
        eval_avg = avg20 if avg20 is not None else (sum(r10) / len(r10) if r10 else (sum(r5) / len(r5) if r5 else None))
        label = "INSUFFICIENT_EVIDENCE"
        cap_reason = "NONE"
        if eq != "INSUFFICIENT":
            if eval_avg is not None and eval_avg > 0.02:
                label = "SIMULATION_CANDIDATE_STRONG"
            elif pid == "DEFENSIVE":
                label = "SIMULATION_CANDIDATE_DEFENSIVE"
            elif pid in {"TECHNICAL_HEAVY", "PULLBACK_ENTRY"}:
                label = "SIMULATION_EXIT_VALIDATION_ONLY"
            elif eval_avg is not None and eval_avg > 0:
                label = "SIMULATION_CANDIDATE_BALANCED"
            else:
                label = "DO_NOT_USE"
        if eq == "LOW" and label == "SIMULATION_CANDIDATE_STRONG":
            label = "SIMULATION_CANDIDATE_BALANCED_LOW_EVIDENCE"
            cap_reason = "LOW_EVIDENCE_NOT_READY_FOR_POLICY_WEIGHTING"
        if pid in {"EVENT_FILTERED", "OPTIONS_RISK_FILTERED", "DEFENSIVE"} and not event_options_rows:
            label = "INSUFFICIENT_EVIDENCE"
            cap_reason = "LIMITED_EVENT_OPTIONS_HISTORY"
        out.append({
            "policy_id": pid,
            "selected_trade_count": str(len(rows)),
            "completed_trade_count": str(len(completed)),
            "pending_trade_count": str(len(rows) - len(completed)),
            "win_rate_5d": win_rate(r5),
            "win_rate_10d": win_rate(r10),
            "win_rate_20d": win_rate(r20),
            "avg_return_5d": fmt(sum(r5) / len(r5) if r5 else None),
            "avg_return_10d": fmt(sum(r10) / len(r10) if r10 else None),
            "avg_return_20d": fmt(avg20),
            "median_return_5d": fmt(statistics.median(r5) if r5 else None),
            "median_return_10d": fmt(statistics.median(r10) if r10 else None),
            "median_return_20d": fmt(statistics.median(r20) if r20 else None),
            "worst_return_20d": fmt(worst20),
            "max_drawdown_proxy": fmt(min(realized) if realized else None),
            "large_loss_count": str(sum(1 for v in realized if v <= -0.08)),
            "event_risk_loss_count": str(sum(1 for row in rows if bad_risk(row["event_risk"], True) and (parse_float(row.get("realized_policy_return")) or 0) < 0)),
            "options_risk_loss_count": str(sum(1 for row in rows if bad_risk(row["options_risk"], True) and (parse_float(row.get("realized_policy_return")) or 0) < 0)),
            "technical_exit_success_count": str(sum(1 for row in rows if "TECHNICAL" in row["simulated_exit_rule"] and (parse_float(row.get("realized_policy_return")) or -1) > 0)),
            "evidence_quality": eq,
            "point_in_time_filter_coverage_pct": fmt(len(pit_rows) / len(rows) if rows else None, 4),
            "event_options_history_coverage_pct": fmt(len(event_options_rows) / len(rows) if rows else None, 4),
            "matched_signal_date_count": str(len(signal_dates)),
            "matched_completed_5d_count": str(matched_5d),
            "matched_completed_10d_count": str(matched_10d),
            "matched_completed_20d_count": str(matched_20d),
            "min_completed_threshold_met": threshold_met,
            "comparison_basis_status": basis_status,
            "recommendation_cap_reason": cap_reason,
            "recommendation_label": label,
            "recommendation_reason": "Read-only simulation evidence; not approved for official ranking or real trading.",
        })
    return out


def choose_recommendation(summary_rows: list[dict[str, str]]) -> dict[str, str]:
    candidates = [
        row for row in summary_rows
        if row["evidence_quality"] != "INSUFFICIENT"
        and row["recommendation_label"] not in {"DO_NOT_USE", "INSUFFICIENT_EVIDENCE"}
        and row["comparison_basis_status"] != "INSUFFICIENT_MATCHED_EVIDENCE"
    ]
    if not candidates:
        return {
            "recommended_for_simulation": "FALSE", "recommended_policy_id": "NONE",
            "recommended_sim_style": "SIM_EXIT_VALIDATION", "confidence_level": "LOW",
            "evidence_quality": "INSUFFICIENT", "reason": "Insufficient completed local forward-return evidence.",
            "not_for_official_ranking_reason": "V18.49A is research-only and does not modify official factor weights or ranking logic.",
            "not_for_real_trading_reason": "V18.49A produces simulation attribution only and no executable trade instructions.",
        }
    def best_available_avg(row: dict[str, str]) -> float:
        for column in ("avg_return_20d", "avg_return_10d", "avg_return_5d"):
            value = parse_float(row.get(column))
            if value is not None:
                return value
        return -999
    def key(row: dict[str, str]) -> tuple[float, float]:
        return (best_available_avg(row), parse_float(row.get("avg_return_5d")) or -999)
    matched = [row for row in candidates if row["comparison_basis_status"] == "MATCHED_BASIS_OK"]
    best = max(matched or candidates, key=key)
    if best["recommendation_label"] == "SIMULATION_EXIT_VALIDATION_ONLY":
        style = "SIM_EXIT_VALIDATION"
    elif best["policy_id"] == "DEFENSIVE":
        style = "SIM_DEFENSIVE"
    elif best["policy_id"] == "AGGRESSIVE_TEST":
        style = "SIM_AGGRESSIVE_TEST"
    elif best["policy_id"] == "EVENT_FILTERED":
        style = "SIM_EVENT_LOCK_TEST"
    else:
        style = "SIM_BALANCED"
    return {
        "recommended_for_simulation": "TRUE", "recommended_policy_id": best["policy_id"],
        "recommended_sim_style": style,
        "confidence_level": "MEDIUM" if best["evidence_quality"] in {"MEDIUM", "HIGH"} and best["comparison_basis_status"] == "MATCHED_BASIS_OK" else "LOW",
        "evidence_quality": best["evidence_quality"],
        "reason": f"Best available completed-horizon average return among eligible research policies: {best_available_avg(best):.6f}; {best['comparison_basis_status']}; {best['recommendation_cap_reason']}. Cautious simulation policy testing only.",
        "not_for_official_ranking_reason": "Research sidecar only; official ranking logic and factor weights remain unchanged.",
        "not_for_real_trading_reason": "Simulation-cabin candidate only; no broker/order path and no real trade execution allowed.",
    }


def markdown_table(rows: list[dict[str, str]], columns: list[str], limit: int | None = None) -> str:
    rows = rows[:limit] if limit else rows
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
    return "\n".join(lines)


def build_report(diag: list[dict[str, str]], policies: list[dict[str, str]], summary: list[dict[str, str]], recommendation: dict[str, str], missing: list[str]) -> str:
    return "\n".join([
        "# V18.49A Factor Weight Buy/Sell Policy Backtest",
        "",
        "V18.49A is a read-only research sidecar that compares a small policy grid for simulation-cabin evidence.",
        "",
        "## Safety Statement",
        "No official ranking weights, buy/sell permissions, real positions, broker APIs, orders, or trading execution are changed.",
        "",
        "## Source Availability",
        markdown_table(diag, ["source_name", "found", "usable", "row_count", "source_path"]),
        "",
        "## Policy Grid",
        markdown_table(policies, ["policy_id", "entry_rule", "exit_rule", "position_size_rule"]),
        "",
        "## Performance Summary",
        markdown_table(summary, ["policy_id", "selected_trade_count", "completed_trade_count", "avg_return_5d", "avg_return_20d", "evidence_quality", "comparison_basis_status", "recommendation_label"]),
        "",
        "## Best Policy / Simulation Style",
        markdown_table([recommendation], ["recommended_for_simulation", "recommended_policy_id", "recommended_sim_style", "confidence_level", "evidence_quality", "reason"]),
        "",
        "## Evidence Limitations",
        "Missing or limited sources: " + ("; ".join(missing) if missing else "NONE") + ". Forward returns use local cached forward tracker data when available; missing forward prices are not fabricated.",
        "",
        "## Why Official Ranking Is Unchanged",
        "The policy scores are local research attribution only. They are written to factor_backtest outputs and are not fed into official ranking, candidate scoring, buy permission, sell permission, final_action, broker, or order code.",
        "",
        "## Next Step",
        "V18.49B Simulation Policy Weight Engine.",
        "",
    ]) + "\n"


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "POINT_IN_TIME_ENRICHMENT_REPAIRED",
        "SYNTHETIC_EXIT_DATE_REMOVED", "LOW_EVIDENCE_RECOMMENDATION_CAPPED",
        "CURRENT_ONLY_RISK_SOURCES_HISTORICAL_USE_BLOCKED", "COMPARISON_BASIS_STATUS",
        "POLICY_GRID_COUNT", "BACKTEST_ROW_COUNT",
        "COMPLETED_BACKTEST_ROW_COUNT", "PENDING_FORWARD_ROW_COUNT", "SOURCE_DIAGNOSTICS_ROW_COUNT",
        "USABLE_CANDIDATE_HISTORY_FOUND", "USABLE_PRICE_HISTORY_FOUND", "USABLE_FACTOR_SOURCE_FOUND",
        "USABLE_TECHNICAL_SOURCE_FOUND", "USABLE_EVENT_RISK_SOURCE_FOUND", "USABLE_OPTIONS_RISK_SOURCE_FOUND",
        "BEST_POLICY_ID", "BEST_POLICY_RECOMMENDATION_LABEL", "RECOMMENDED_SIM_STYLE", "EVIDENCE_QUALITY",
        "CURRENT_ALIAS_WRITTEN", "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED",
        "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED", "REAL_TRADE_EXECUTION_ALLOWED",
        "OPTIONS_TRADE_EXECUTION_ALLOWED", "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL",
        "BROKER_API_USED", "ORDER_EXECUTION_USED", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only V18.49A factor weight buy/sell policy backtest.")
    parser.add_argument("--root", "--project-root", dest="root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_date = date.today().isoformat()
    paths, diagnostics = discover(root)
    policies = policy_grid()

    forward_rows = normalize_signal_rows(read_csv(paths["candidate_forward_tracker"]) if paths["candidate_forward_tracker"] else [], "candidate_forward_tracker")
    factor_forward_rows = normalize_signal_rows(read_csv(paths["factor_forward_tracker"]) if paths["factor_forward_tracker"] else [], "factor_forward_tracker")
    current_rows = read_csv(paths["current_top20"]) if paths["current_top20"] else []
    candidate_rows = forward_rows + factor_forward_rows
    if not candidate_rows:
        candidate_rows = normalize_signal_rows(current_rows, "current_top20")
    factor_rows = read_csv(paths["factor_pack"]) if paths["factor_pack"] else []
    tech_rows = read_csv(paths["technical_timing"]) if paths["technical_timing"] else []
    event_rows = read_csv(paths["event_risk"]) if paths["event_risk"] and paths["event_risk"].exists() else []
    option_rows = read_csv(paths["options_risk"]) if paths["options_risk"] and paths["options_risk"].exists() else []
    factor_index = point_in_time_lookup(factor_rows)
    tech_index = point_in_time_lookup(tech_rows)
    event_index = point_in_time_lookup(event_rows)
    option_index = point_in_time_lookup(option_rows)
    signals = [enrich_signal(row, factor_index, tech_index, event_index, option_index) for row in candidate_rows if norm_ticker(row.get("ticker"))]

    backtest_rows = build_backtest_rows(run_date, signals, policies) if signals else []
    summary_rows = summarize(backtest_rows, policies)
    recommendation = choose_recommendation(summary_rows)
    missing = [row["source_name"] for row in diagnostics if row["usable"] != "TRUE"]

    out_dir = root / "outputs/v18/factor_backtest"
    grid_path = out_dir / "V18_49A_POLICY_GRID.csv"
    backtest_path = out_dir / "V18_49A_BUY_SELL_POLICY_BACKTEST.csv"
    summary_path = out_dir / "V18_49A_POLICY_PERFORMANCE_SUMMARY.csv"
    rec_path = out_dir / "V18_49A_POLICY_RECOMMENDATION.csv"
    diag_path = out_dir / "V18_49A_SOURCE_DIAGNOSTICS.csv"
    report_path = root / "outputs/v18/read_center/V18_49A_FACTOR_WEIGHT_BUY_SELL_POLICY_BACKTEST_REPORT.md"
    current_path = root / "outputs/v18/read_center/V18_CURRENT_FACTOR_WEIGHT_BUY_SELL_POLICY_BACKTEST.md"
    read_first_path = root / "outputs/v18/ops/V18_49A_READ_FIRST.txt"

    write_csv(grid_path, policies, POLICY_GRID_COLUMNS)
    write_csv(backtest_path, backtest_rows, BACKTEST_COLUMNS)
    write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
    write_csv(rec_path, [recommendation], RECOMMENDATION_COLUMNS)
    write_csv(diag_path, diagnostics, DIAG_COLUMNS)
    report = build_report(diagnostics, policies, summary_rows, recommendation, missing)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_written = False
    if args.write_current:
        current_path.write_text(report, encoding="utf-8")
        current_written = True

    usable_candidate = bool(signals)
    usable_price = any(parse_float(row.get("forward_5d_return")) is not None or parse_float(row.get("forward_10d_return")) is not None or parse_float(row.get("forward_20d_return")) is not None for row in candidate_rows)
    completed = sum(1 for row in backtest_rows if parse_float(row.get("realized_policy_return")) is not None)
    pending = len(backtest_rows) - completed
    basis_counts = Counter(row.get("comparison_basis_status", "INSUFFICIENT_MATCHED_EVIDENCE") for row in summary_rows)
    overall_basis = "MATCHED_BASIS_OK" if basis_counts.get("MATCHED_BASIS_OK", 0) else "COMPARISON_BASIS_LIMITED" if basis_counts.get("COMPARISON_BASIS_LIMITED", 0) else "INSUFFICIENT_MATCHED_EVIDENCE"
    limited_pit = any(row.get("point_in_time_filter_coverage_pct") in {"0.0000", "UNKNOWN"} for row in summary_rows)
    if not usable_candidate and usable_price:
        status = "WARN_V18_49A_MISSING_CANDIDATE_HISTORY"
    elif usable_candidate and not usable_price:
        status = "WARN_V18_49A_MISSING_PRICE_HISTORY"
    elif completed < 10:
        status = "WARN_V18_49A_INSUFFICIENT_BACKTEST_EVIDENCE"
    elif limited_pit or overall_basis != "MATCHED_BASIS_OK":
        status = "WARN_V18_49A_R1_LIMITED_POINT_IN_TIME_EVIDENCE"
    else:
        status = "PASS"

    best_summary = next((row for row in summary_rows if row["policy_id"] == recommendation["recommended_policy_id"]), {})
    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "POINT_IN_TIME_ENRICHMENT_REPAIRED": "TRUE",
        "SYNTHETIC_EXIT_DATE_REMOVED": "TRUE",
        "LOW_EVIDENCE_RECOMMENDATION_CAPPED": "TRUE",
        "CURRENT_ONLY_RISK_SOURCES_HISTORICAL_USE_BLOCKED": "TRUE",
        "COMPARISON_BASIS_STATUS": overall_basis,
        "POLICY_GRID_COUNT": str(len(policies)),
        "BACKTEST_ROW_COUNT": str(len(backtest_rows)),
        "COMPLETED_BACKTEST_ROW_COUNT": str(completed),
        "PENDING_FORWARD_ROW_COUNT": str(pending),
        "SOURCE_DIAGNOSTICS_ROW_COUNT": str(len(diagnostics)),
        "USABLE_CANDIDATE_HISTORY_FOUND": "TRUE" if usable_candidate else "FALSE",
        "USABLE_PRICE_HISTORY_FOUND": "TRUE" if usable_price else "FALSE",
        "USABLE_FACTOR_SOURCE_FOUND": "TRUE" if factor_rows else "FALSE",
        "USABLE_TECHNICAL_SOURCE_FOUND": "TRUE" if tech_rows else "FALSE",
        "USABLE_EVENT_RISK_SOURCE_FOUND": "TRUE" if event_rows else "FALSE",
        "USABLE_OPTIONS_RISK_SOURCE_FOUND": "TRUE" if option_rows else "FALSE",
        "BEST_POLICY_ID": recommendation["recommended_policy_id"],
        "BEST_POLICY_RECOMMENDATION_LABEL": clean(best_summary.get("recommendation_label"), "INSUFFICIENT_EVIDENCE"),
        "RECOMMENDED_SIM_STYLE": recommendation["recommended_sim_style"],
        "EVIDENCE_QUALITY": recommendation["evidence_quality"],
        "CURRENT_ALIAS_WRITTEN": "TRUE" if current_written else "FALSE",
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
        "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
        "REAL_TRADE_EXECUTION_ALLOWED": "FALSE",
        "OPTIONS_TRADE_EXECUTION_ALLOWED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "VALIDATION_NOTES": "READ_ONLY_RESEARCH_SIDECAR_NO_OFFICIAL_RANKING_WEIGHT_PERMISSION_POSITION_BROKER_ORDER_OR_TRADING_CHANGES",
    }
    write_read_first(read_first_path, values)
    print(f"STATUS: {status}")
    print(f"POLICY_GRID_COUNT: {len(policies)}")
    print(f"BACKTEST_ROW_COUNT: {len(backtest_rows)}")
    print(f"COMPLETED_BACKTEST_ROW_COUNT: {completed}")
    print(f"BEST_POLICY_ID: {recommendation['recommended_policy_id']}")
    print(f"RECOMMENDED_SIM_STYLE: {recommendation['recommended_sim_style']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
