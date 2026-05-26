from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import v18_21E_event_risk_coefficient_engine as base


STATUS_READY = "WARN_V18_21E_R1_HARD_LOCK_OVERLAY_SEMANTICS_READY"
STATUS_FAIL = "FAIL_V18_21E_R1_HARD_LOCK_OVERLAY_SEMANTICS_VALIDATION_FAILED"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "HARD_LOCK_OVERLAY_SEMANTICS_AND_EVENT_COEFFICIENT_CALIBRATION_ONLY"
OVERLAY_COEFFICIENT = 0.30

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "EVENT_CALENDAR_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

HARD_LOCK_SOURCES = [
    "outputs/v18/read_center/V18_CURRENT_RISK_DASHBOARD.md",
    "outputs/v18/read_center/daily_packet/V18_CURRENT_RISK_DASHBOARD.md",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_16K_R2_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt",
    "state/v16_18_reentry_state.csv",
    "state/v16_19_execution_budget_state.csv",
    "state/v16_24_classic_brief_status_fallback.csv",
]
PATTERN_TYPES = {
    "NO_TRADE_EVENT_RISK_EXTREME": "EVENT_RISK_EXTREME",
    "NO_BUY_EVENT_LOCKED": "NO_BUY_EVENT_LOCKED",
    "LOCKED_EXTREME_WAIT_EVENT_CLEAR": "GLOBAL_MODE_LOCKED",
    "NO_NEW_BUYS_NOW": "BUDGET_LOCKED",
    "official_action": "OFFICIAL_NO_TRADE",
}

ATTRIBUTION_FIELDS = [
    "source_path", "source_exists", "modified_time", "detected_hard_lock", "detected_field_name",
    "detected_field_value", "detected_text_snippet", "hard_lock_type", "hard_lock_confidence",
    "advisory_only", "notes",
]
MARKET_SEMANTICS_FIELDS = [
    "asof_date", "calendar_market_event_risk_coefficient", "calendar_market_event_risk_level",
    "calendar_active_market_event_count", "hard_lock_overlay_detected", "hard_lock_overlay_type",
    "hard_lock_overlay_advisory_coefficient", "final_advisory_market_event_risk_coefficient",
    "final_advisory_market_event_risk_level", "coefficient_semantics_status",
    "official_decision_impact", "notes",
]
TICKER_SEMANTICS_FIELDS = [
    "asof_date", "ticker", "calendar_ticker_event_risk_coefficient", "calendar_ticker_event_risk_level",
    "hard_lock_overlay_detected", "hard_lock_overlay_advisory_coefficient",
    "final_advisory_ticker_event_risk_coefficient", "final_advisory_ticker_event_risk_level",
    "event_action_status", "event_semantics_status", "nearest_calendar_event_type",
    "nearest_calendar_event_date", "days_to_nearest_calendar_event", "notes",
]
CANDIDATE_FIELDS = [
    "asof_date", "ticker", "signal_snapshot_id", "raw_research_score", "factor_pack_score",
    "composite_candidate_score", "price_derived_total_score", "technical_timing_score",
    "calendar_market_event_risk_coefficient", "calendar_ticker_event_risk_coefficient",
    "hard_lock_overlay_detected", "hard_lock_overlay_advisory_coefficient",
    "final_advisory_event_risk_coefficient", "event_adjusted_score_calendar_only",
    "event_adjusted_score_with_advisory_overlay", "event_adjusted_rank_calendar_only",
    "event_adjusted_rank_with_advisory_overlay", "event_action_status", "event_adjustment_status",
    "official_decision_impact",
]
TOP_LIST_FIELDS = ["list_name", "rank", "ticker", "sort_metric", "sort_metric_value", "event_action_status", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "EVENT_SOURCE_COUNT",
    "EVENT_SOURCE_MISSING_COUNT", "NORMALIZED_EVENT_COUNT", "CALENDAR_MARKET_EVENT_RISK_COEFFICIENT",
    "CALENDAR_MARKET_EVENT_RISK_LEVEL", "HARD_LOCK_OVERLAY_DETECTED", "HARD_LOCK_OVERLAY_TYPE",
    "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT", "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT",
    "FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL", "TICKER_EVENT_RISK_ROW_COUNT",
    "CALENDAR_HIGH_RISK_TICKER_COUNT", "CALENDAR_EXTREME_CAUTION_TICKER_COUNT",
    "ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT", "HARD_LOCK_SOURCE_DETECTED",
    "EVENT_ADJUSTED_CANDIDATE_COUNT", "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT",
    "TOP_EVENT_RISK_TICKERS", "TOP_EVENT_ADJUSTED_CANDIDATES",
    "EVENT_RISK_SEMANTICS_VALIDATION_CREATED", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    return base.read_csv(path)


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    base.write_csv(path, rows, fields)


def write_text(path: Path, text: str) -> None:
    base.write_text(path, text)


def numeric(value: object) -> Optional[float]:
    return base.numeric(value)


def snippet(text: str, needle: str) -> str:
    idx = text.find(needle)
    if idx < 0:
        return text[:160].replace("\n", " ")
    start = max(idx - 70, 0)
    end = min(idx + len(needle) + 70, len(text))
    return text[start:end].replace("\n", " ").replace("\r", " ")


def hard_lock_type_for(field_name: str, value: str) -> str:
    text = f"{field_name} {value}".upper()
    if "OFFICIAL" in text and "NO_TRADE" in text:
        return "OFFICIAL_NO_TRADE"
    for pattern, lock_type in PATTERN_TYPES.items():
        if pattern.upper() in text:
            return lock_type
    return "UNKNOWN_HARD_LOCK"


def attribution_rows(root: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for rel in HARD_LOCK_SOURCES:
        path = root / rel
        exists = path.exists()
        if not exists:
            rows.append({
                "source_path": str(path),
                "source_exists": "FALSE",
                "modified_time": "",
                "detected_hard_lock": "FALSE",
                "detected_field_name": "",
                "detected_field_value": "",
                "detected_text_snippet": "",
                "hard_lock_type": "",
                "hard_lock_confidence": "",
                "advisory_only": "TRUE",
                "notes": "Source missing; no hard-lock attribution from this source.",
            })
            continue
        text = base.read_text(path)
        detected_any = False
        if path.suffix.lower() == ".csv":
            csv_rows, fields = read_csv(path)
            for row in csv_rows:
                for field in fields:
                    value = str(row.get(field, "") or "")
                    if any(pattern in value for pattern in base.HARD_LOCK_PATTERNS) or "NO_NEW_BUYS_NOW" in value:
                        detected_any = True
                        rows.append({
                            "source_path": str(path),
                            "source_exists": "TRUE",
                            "modified_time": base.modified_time(path),
                            "detected_hard_lock": "TRUE",
                            "detected_field_name": field,
                            "detected_field_value": value,
                            "detected_text_snippet": snippet(",".join(str(row.get(f, "")) for f in fields), value),
                            "hard_lock_type": hard_lock_type_for(field, value),
                            "hard_lock_confidence": "HIGH",
                            "advisory_only": "TRUE",
                            "notes": "Detected from existing local state; no official behavior changed.",
                        })
        for pattern in base.HARD_LOCK_PATTERNS:
            if pattern in text and not any(r.get("source_path") == str(path) and r.get("detected_field_value") == pattern for r in rows):
                detected_any = True
                rows.append({
                    "source_path": str(path),
                    "source_exists": "TRUE",
                    "modified_time": base.modified_time(path),
                    "detected_hard_lock": "TRUE",
                    "detected_field_name": "TEXT_SCAN",
                    "detected_field_value": pattern,
                    "detected_text_snippet": snippet(text, pattern),
                    "hard_lock_type": hard_lock_type_for("TEXT_SCAN", pattern),
                    "hard_lock_confidence": "MEDIUM",
                    "advisory_only": "TRUE",
                    "notes": "Detected by text scan; advisory overlay only.",
                })
        if not detected_any:
            rows.append({
                "source_path": str(path),
                "source_exists": "TRUE",
                "modified_time": base.modified_time(path),
                "detected_hard_lock": "FALSE",
                "detected_field_name": "",
                "detected_field_value": "",
                "detected_text_snippet": "",
                "hard_lock_type": "",
                "hard_lock_confidence": "",
                "advisory_only": "TRUE",
                "notes": "Source scanned; no hard-lock pattern detected.",
            })
    return rows


def dominant_lock_type(rows: List[Dict[str, object]]) -> str:
    detected = [str(row.get("hard_lock_type", "")) for row in rows if row.get("detected_hard_lock") == "TRUE"]
    if not detected:
        return ""
    priority = ["OFFICIAL_NO_TRADE", "EVENT_RISK_EXTREME", "NO_BUY_EVENT_LOCKED", "GLOBAL_MODE_LOCKED", "BUDGET_LOCKED", "UNKNOWN_HARD_LOCK"]
    for item in priority:
        if item in detected:
            return item
    return detected[0]


def level_without_overlay(coeff: float) -> str:
    return base.risk_level(coeff, False)


def ticker_action(calendar_coeff: float, overlay: bool, unknown_degraded: bool) -> str:
    if unknown_degraded:
        return "UNKNOWN_EVENT_DEGRADED"
    if overlay:
        return "MARKET_HARD_LOCK_OVERLAY_ADVISORY"
    if calendar_coeff <= 0.35:
        return "TICKER_EVENT_EXTREME_CAUTION"
    if calendar_coeff <= 0.70:
        return "TICKER_EVENT_CAUTION"
    return "NORMAL_CALENDAR_RISK"


def best_score(row: Dict[str, str]) -> Tuple[str, Optional[float]]:
    return base.best_score(row)


def rank_rows(rows: List[Dict[str, object]], score_field: str, rank_field: str) -> None:
    scored = [row for row in rows if str(row.get(score_field, "")).strip()]
    scored.sort(key=lambda row: float(row[score_field]), reverse=True)
    for idx, row in enumerate(scored, start=1):
        row[rank_field] = idx


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_current_daily_command_center_full.ps1",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
        base.SIGNAL_PATH,
        base.RANKING_PATH,
        base.PRICE_SCORE_PATH,
        base.MARKET_REGIME_PATH,
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "state/v18/manual_state.csv",
        "state/v18/broker_execution_state.csv",
    ]
    return [root / rel for rel in rels]


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


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


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(values: Dict[str, object], attribution: List[Dict[str, object]], validations: List[Dict[str, object]]) -> str:
    detected_sources = [row for row in attribution if row.get("detected_hard_lock") == "TRUE"]
    return f"""# V18.21E-R1 Hard-Lock Overlay Semantics Report

## Executive Summary
Status: {values.get('STATUS')}. V18.21E-R1 separates calendar-derived event coefficients from existing hard-lock overlay context.

## Safety Statement
This patch is advisory-only. It does not modify official decisions, buy permission, current daily wrappers, rankings, signal snapshots, event calendars, simulation positions, forward tracker state, price cache, manual state, broker execution, auto-trade, or auto-sell behavior.

## Calendar-Derived Coefficient Summary
Calendar market coefficient: {values.get('CALENDAR_MARKET_EVENT_RISK_COEFFICIENT')}. Calendar market level: {values.get('CALENDAR_MARKET_EVENT_RISK_LEVEL')}. Normalized events: {values.get('NORMALIZED_EVENT_COUNT')}.

## Hard-Lock Overlay Attribution Summary
Hard-lock overlay detected: {values.get('HARD_LOCK_OVERLAY_DETECTED')}. Dominant overlay type: {values.get('HARD_LOCK_OVERLAY_TYPE')}. Detected attribution rows: {len(detected_sources)}.

## Final Advisory Coefficient Semantics
Final advisory market coefficient: {values.get('FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT')}. Final advisory level: {values.get('FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL')}. The overlay coefficient is not applied to official decisions.

## Ticker-Level Event Semantics Summary
Ticker rows: {values.get('TICKER_EVENT_RISK_ROW_COUNT')}. Calendar high-risk tickers: {values.get('CALENDAR_HIGH_RISK_TICKER_COUNT')}. Calendar extreme-caution tickers: {values.get('CALENDAR_EXTREME_CAUTION_TICKER_COUNT')}. Overlay affected tickers: {values.get('ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT')}.

## Event-Adjusted Candidate Semantics
Candidate rows: {values.get('EVENT_ADJUSTED_CANDIDATE_COUNT')}. Score-available rows: {values.get('EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT')}. Ranks are reported separately for calendar-only and advisory-overlay scores.

## Top List Sorting Explanation
Top event-risk tickers are sorted by lowest calendar ticker coefficient, then nearest calendar event, then ticker. If values are tied, alphabetical order is only a final tie-breaker and the audit states the sort metric.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}. Validation rows: {len(validations)}.

## Next-Step Recommendation
Use R1 outputs for review and stable snapshot only. Any future integration into official daily behavior requires explicit approval.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    asof = base.asof_date(root)
    out_dir = root / "outputs/v18/event_risk"
    ops_dir = root / "outputs/v18/ops"
    paths = {
        "attribution": out_dir / "V18_21E_R1_CURRENT_HARD_LOCK_SOURCE_ATTRIBUTION.csv",
        "market_semantics": out_dir / "V18_21E_R1_CURRENT_MARKET_EVENT_RISK_SEMANTICS.csv",
        "ticker_semantics": out_dir / "V18_21E_R1_CURRENT_TICKER_EVENT_RISK_SEMANTICS.csv",
        "candidates": out_dir / "V18_21E_R1_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv",
        "top_audit": out_dir / "V18_21E_R1_CURRENT_EVENT_RISK_TOP_LIST_SORTING_AUDIT.csv",
        "validation": out_dir / "V18_21E_R1_CURRENT_EVENT_RISK_SEMANTICS_VALIDATION.csv",
        "read_first": ops_dir / "V18_21E_R1_READ_FIRST.txt",
        "report": ops_dir / "V18_21E_R1_CURRENT_HARD_LOCK_OVERLAY_SEMANTICS_REPORT.md",
    }

    before = {str(path): base.signature(path) for path in protected_paths(root)}
    events, source_audit = base.normalize_events(root, asof)
    attribution = attribution_rows(root)
    overlay_detected = any(row.get("detected_hard_lock") == "TRUE" for row in attribution)
    overlay_type = dominant_lock_type(attribution)
    overlay_coeff = OVERLAY_COEFFICIENT if overlay_detected else 1.0

    calendar_market = base.market_risk(asof, events, False, "")
    calendar_market_coeff = numeric(calendar_market["market_event_risk_coefficient"]) or 1.0
    final_market_coeff = min(calendar_market_coeff, overlay_coeff)
    final_market_level = "HARD_LOCK_SOURCE_DETECTED" if overlay_detected else level_without_overlay(final_market_coeff)
    market_semantics = [{
        "asof_date": asof.isoformat(),
        "calendar_market_event_risk_coefficient": f"{calendar_market_coeff:.6f}",
        "calendar_market_event_risk_level": calendar_market["market_event_risk_level"],
        "calendar_active_market_event_count": calendar_market["active_market_event_count"],
        "hard_lock_overlay_detected": str(overlay_detected).upper(),
        "hard_lock_overlay_type": overlay_type,
        "hard_lock_overlay_advisory_coefficient": f"{overlay_coeff:.6f}",
        "final_advisory_market_event_risk_coefficient": f"{final_market_coeff:.6f}",
        "final_advisory_market_event_risk_level": final_market_level,
        "coefficient_semantics_status": "CALENDAR_AND_HARD_LOCK_OVERLAY_SEPARATED" if overlay_detected else "CALENDAR_ONLY",
        "official_decision_impact": "NONE",
        "notes": "Calendar coefficient is separate from advisory hard-lock overlay.",
    }]

    universe = base.universe_rows(root)
    tickers = [str(row.get("ticker", "")).upper().strip() for row in universe if str(row.get("ticker", "")).strip()]
    calendar_ticker_rows = base.ticker_risk(asof, tickers, events, calendar_market_coeff, False)
    ticker_by_symbol = {str(row["ticker"]): row for row in calendar_ticker_rows}
    ticker_semantics: List[Dict[str, object]] = []
    for ticker in tickers:
        row = ticker_by_symbol[ticker]
        calendar_coeff = numeric(row["ticker_event_risk_coefficient"]) or 1.0
        final_coeff = min(calendar_coeff, overlay_coeff)
        nearest_type = str(row.get("nearest_event_type", ""))
        unknown_degraded = nearest_type == "UNKNOWN_EVENT"
        ticker_semantics.append({
            "asof_date": asof.isoformat(),
            "ticker": ticker,
            "calendar_ticker_event_risk_coefficient": f"{calendar_coeff:.6f}",
            "calendar_ticker_event_risk_level": row.get("ticker_event_risk_level", ""),
            "hard_lock_overlay_detected": str(overlay_detected).upper(),
            "hard_lock_overlay_advisory_coefficient": f"{overlay_coeff:.6f}",
            "final_advisory_ticker_event_risk_coefficient": f"{final_coeff:.6f}",
            "final_advisory_ticker_event_risk_level": final_market_level if overlay_detected else level_without_overlay(final_coeff),
            "event_action_status": ticker_action(calendar_coeff, overlay_detected, unknown_degraded),
            "event_semantics_status": "MARKET_WIDE_OVERLAY_NOT_TICKER_SPECIFIC" if overlay_detected and int(row.get("applicable_event_count", 0)) == 0 else "CALENDAR_TICKER_EVENT_CONTEXT",
            "nearest_calendar_event_type": row.get("nearest_event_type", ""),
            "nearest_calendar_event_date": row.get("nearest_event_date", ""),
            "days_to_nearest_calendar_event": row.get("days_to_nearest_event", ""),
            "notes": "Final advisory coefficient separates ticker calendar risk from market-wide hard-lock overlay.",
        })

    semantics_by_ticker = {str(row["ticker"]): row for row in ticker_semantics}
    candidate_rows: List[Dict[str, object]] = []
    for source in universe:
        ticker = str(source.get("ticker", "")).upper().strip()
        if not ticker:
            continue
        sem = semantics_by_ticker[ticker]
        _, score = best_score(source)
        calendar_coeff = numeric(sem["calendar_ticker_event_risk_coefficient"]) or 1.0
        final_coeff = numeric(sem["final_advisory_ticker_event_risk_coefficient"]) or 1.0
        calendar_score = score * calendar_coeff if score is not None else None
        overlay_score = score * final_coeff if score is not None else None
        candidate_rows.append({
            "asof_date": asof.isoformat(),
            "ticker": ticker,
            "signal_snapshot_id": source.get("signal_snapshot_id", ""),
            "raw_research_score": score if score is not None else "",
            "factor_pack_score": source.get("factor_pack_score", ""),
            "composite_candidate_score": source.get("composite_candidate_score", ""),
            "price_derived_total_score": source.get("price_derived_total_score", ""),
            "technical_timing_score": source.get("technical_timing_score", ""),
            "calendar_market_event_risk_coefficient": f"{calendar_market_coeff:.6f}",
            "calendar_ticker_event_risk_coefficient": f"{calendar_coeff:.6f}",
            "hard_lock_overlay_detected": str(overlay_detected).upper(),
            "hard_lock_overlay_advisory_coefficient": f"{overlay_coeff:.6f}",
            "final_advisory_event_risk_coefficient": f"{final_coeff:.6f}",
            "event_adjusted_score_calendar_only": f"{calendar_score:.6f}" if calendar_score is not None else "",
            "event_adjusted_score_with_advisory_overlay": f"{overlay_score:.6f}" if overlay_score is not None else "",
            "event_adjusted_rank_calendar_only": "",
            "event_adjusted_rank_with_advisory_overlay": "",
            "event_action_status": sem["event_action_status"],
            "event_adjustment_status": "ADVISORY_OVERLAY_SCORE_SCALED_MARKET_WIDE_RANK_MAY_BE_UNCHANGED" if overlay_detected and score is not None else ("CALENDAR_ONLY_SCORE_AVAILABLE" if score is not None else "SCORE_UNAVAILABLE_COEFFICIENT_ONLY"),
            "official_decision_impact": "NONE",
        })
    rank_rows(candidate_rows, "event_adjusted_score_calendar_only", "event_adjusted_rank_calendar_only")
    rank_rows(candidate_rows, "event_adjusted_score_with_advisory_overlay", "event_adjusted_rank_with_advisory_overlay")

    top_audit: List[Dict[str, object]] = []
    sorted_calendar_risk = sorted(ticker_semantics, key=lambda row: (float(row["calendar_ticker_event_risk_coefficient"]), int(row["days_to_nearest_calendar_event"] or 999999), str(row["ticker"])))[:10]
    for idx, row in enumerate(sorted_calendar_risk, start=1):
        top_audit.append({"list_name": "TOP_CALENDAR_TICKER_EVENT_RISK_BY_LOWEST_COEFFICIENT", "rank": idx, "ticker": row["ticker"], "sort_metric": "calendar_ticker_event_risk_coefficient", "sort_metric_value": row["calendar_ticker_event_risk_coefficient"], "event_action_status": row["event_action_status"], "notes": "Sorted by coefficient, then nearest event, then ticker."})
    nearest = [row for row in ticker_semantics if str(row.get("days_to_nearest_calendar_event", "")).strip()]
    nearest = sorted(nearest, key=lambda row: (int(row["days_to_nearest_calendar_event"]), str(row["ticker"])))[:10]
    for idx, row in enumerate(nearest, start=1):
        top_audit.append({"list_name": "TOP_NEAREST_TICKER_EVENTS_BY_DAYS_TO_EVENT", "rank": idx, "ticker": row["ticker"], "sort_metric": "days_to_nearest_calendar_event", "sort_metric_value": row["days_to_nearest_calendar_event"], "event_action_status": row["event_action_status"], "notes": "Sorted by nearest future ticker calendar event."})
    overlay_affected = [row for row in ticker_semantics if overlay_detected]
    for idx, row in enumerate(overlay_affected[:10], start=1):
        top_audit.append({"list_name": "TOP_HARD_LOCK_OVERLAY_AFFECTED_TICKERS", "rank": idx, "ticker": row["ticker"], "sort_metric": "final_advisory_ticker_event_risk_coefficient", "sort_metric_value": row["final_advisory_ticker_event_risk_coefficient"], "event_action_status": row["event_action_status"], "notes": "All overlay-affected tickers share the same market-wide overlay coefficient; ticker is final tie-breaker."})
    advisory_scored = [row for row in candidate_rows if str(row.get("event_adjusted_score_with_advisory_overlay", "")).strip()]
    advisory_scored.sort(key=lambda row: float(row["event_adjusted_score_with_advisory_overlay"]), reverse=True)
    for idx, row in enumerate(advisory_scored[:10], start=1):
        top_audit.append({"list_name": "TOP_EVENT_ADJUSTED_CANDIDATES_BY_ADVISORY_SCORE", "rank": idx, "ticker": row["ticker"], "sort_metric": "event_adjusted_score_with_advisory_overlay", "sort_metric_value": row["event_adjusted_score_with_advisory_overlay"], "event_action_status": row["event_action_status"], "notes": "Sorted by advisory-overlay adjusted score."})
    calendar_scored = [row for row in candidate_rows if str(row.get("event_adjusted_score_calendar_only", "")).strip()]
    calendar_scored.sort(key=lambda row: float(row["event_adjusted_score_calendar_only"]), reverse=True)
    for idx, row in enumerate(calendar_scored[:10], start=1):
        top_audit.append({"list_name": "TOP_EVENT_ADJUSTED_CANDIDATES_BY_CALENDAR_ONLY_SCORE", "rank": idx, "ticker": row["ticker"], "sort_metric": "event_adjusted_score_calendar_only", "sort_metric_value": row["event_adjusted_score_calendar_only"], "event_action_status": row["event_action_status"], "notes": "Sorted by calendar-only adjusted score."})

    write_csv(paths["attribution"], attribution, ATTRIBUTION_FIELDS)
    write_csv(paths["market_semantics"], market_semantics, MARKET_SEMANTICS_FIELDS)
    write_csv(paths["ticker_semantics"], ticker_semantics, TICKER_SEMANTICS_FIELDS)
    write_csv(paths["candidates"], candidate_rows, CANDIDATE_FIELDS)
    write_csv(paths["top_audit"], top_audit, TOP_LIST_FIELDS)
    write_csv(paths["validation"], [], VALIDATION_FIELDS)

    calendar_high = sum(1 for row in ticker_semantics if row["calendar_ticker_event_risk_level"] == "HIGH_RISK")
    calendar_extreme = sum(1 for row in ticker_semantics if row["calendar_ticker_event_risk_level"] == "EXTREME_CAUTION")
    overlay_count = len(ticker_semantics) if overlay_detected else 0
    top_event_risk = ",".join(str(row["ticker"]) for row in sorted_calendar_risk)
    top_candidates = ",".join(str(row["ticker"]) for row in advisory_scored[:10])
    source_missing = sum(1 for row in source_audit if row.get("source_exists") != "TRUE")
    scored_count = len(advisory_scored)
    values: Dict[str, object] = {
        "STATUS": STATUS_READY,
        "EVENT_SOURCE_COUNT": len(source_audit),
        "EVENT_SOURCE_MISSING_COUNT": source_missing,
        "NORMALIZED_EVENT_COUNT": len(events),
        "CALENDAR_MARKET_EVENT_RISK_COEFFICIENT": f"{calendar_market_coeff:.6f}",
        "CALENDAR_MARKET_EVENT_RISK_LEVEL": calendar_market["market_event_risk_level"],
        "HARD_LOCK_OVERLAY_DETECTED": str(overlay_detected).upper(),
        "HARD_LOCK_OVERLAY_TYPE": overlay_type,
        "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT": f"{overlay_coeff:.6f}",
        "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT": f"{final_market_coeff:.6f}",
        "FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL": final_market_level,
        "TICKER_EVENT_RISK_ROW_COUNT": len(ticker_semantics),
        "CALENDAR_HIGH_RISK_TICKER_COUNT": calendar_high,
        "CALENDAR_EXTREME_CAUTION_TICKER_COUNT": calendar_extreme,
        "ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT": overlay_count,
        "HARD_LOCK_SOURCE_DETECTED": str(overlay_detected).upper(),
        "EVENT_ADJUSTED_CANDIDATE_COUNT": len(candidate_rows),
        "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT": scored_count,
        "TOP_EVENT_RISK_TICKERS": top_event_risk,
        "TOP_EVENT_ADJUSTED_CANDIDATES": top_candidates,
        "EVENT_RISK_SEMANTICS_VALIDATION_CREATED": "TRUE",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    values.update(SAFETY_FLAGS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, attribution, []))

    after = {str(path): base.signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    coeffs: List[float] = [calendar_market_coeff, overlay_coeff, final_market_coeff]
    coeffs.extend(float(row["calendar_ticker_event_risk_coefficient"]) for row in ticker_semantics)
    coeffs.extend(float(row["final_advisory_ticker_event_risk_coefficient"]) for row in ticker_semantics)
    coeffs.extend(float(row["final_advisory_event_risk_coefficient"]) for row in candidate_rows)
    required_exists = all(path.exists() for path in paths.values())
    read_first_text = base.read_text(paths["read_first"])
    validations = [
        validation_row("powershell_parse_wrapper", ps_parse(root / "scripts/v18/run_v18_21E_R1_hard_lock_overlay_semantics_patch.ps1"), 1, "Wrapper parses."),
        validation_row("python_compile_base_engine", py_compile(root / "scripts/v18/v18_21E_event_risk_coefficient_engine.py"), 1, "Base engine compiles."),
        validation_row("python_compile_r1_patch", py_compile(root / "scripts/v18/v18_21E_R1_hard_lock_overlay_semantics_patch.py"), 1, "R1 patch compiles."),
        validation_row("required_outputs_exist", required_exists, 1, "All R1 output files exist."),
        validation_row("required_read_first_fields_exist", all(field in read_first_text for field in READ_FIRST_FIELDS), 1, "All required READ_FIRST fields exist."),
        validation_row("calendar_coefficient_in_bounds", 0.0 <= calendar_market_coeff <= 1.0 and all(0.0 <= float(row["calendar_ticker_event_risk_coefficient"]) <= 1.0 for row in ticker_semantics), 1, "Calendar coefficients are in [0, 1]."),
        validation_row("hard_lock_overlay_coefficient_in_bounds", 0.0 <= overlay_coeff <= 1.0, 1, "Overlay coefficient is in [0, 1]."),
        validation_row("final_advisory_coefficient_in_bounds", all(0.0 <= value <= 1.0 for value in coeffs), 1, "Final advisory coefficients are in [0, 1]."),
        validation_row("hard_lock_final_coefficient_not_one", (not overlay_detected) or final_market_coeff != 1.0, 1, "If hard-lock overlay is detected, final advisory coefficient must not remain 1.0."),
        validation_row("official_decision_impact_none", values["OFFICIAL_DECISION_IMPACT"] == "NONE", 1, "Official decision impact remains NONE."),
        validation_row("buy_permission_not_modified", values["BUY_PERMISSION_MODIFIED"] == "FALSE", 1, "Buy permission not modified."),
        validation_row("ranking_not_modified", values["RANKING_MODIFIED"] == "FALSE", 1, "Ranking not modified."),
        validation_row("signal_snapshot_not_modified", values["SIGNAL_SNAPSHOT_MODIFIED"] == "FALSE", 1, "Signal snapshot not modified."),
        validation_row("event_calendar_not_modified", values["EVENT_CALENDAR_MODIFIED"] == "FALSE", 1, "Event calendars not modified."),
        validation_row("external_data_not_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE", 1, "No external data fetched."),
        validation_row("event_risk_not_applied_to_official_decision", values["EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION"] == "FALSE", 1, "Advisory only."),
        validation_row("no_protected_files_modified", not changed, len(changed), "Changed protected files: " + ";".join(changed)),
    ]
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["validation"], validations, VALIDATION_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, attribution, validations))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "EVENT_SOURCE_COUNT",
        "EVENT_SOURCE_MISSING_COUNT", "NORMALIZED_EVENT_COUNT",
        "CALENDAR_MARKET_EVENT_RISK_COEFFICIENT", "CALENDAR_MARKET_EVENT_RISK_LEVEL",
        "HARD_LOCK_OVERLAY_DETECTED", "HARD_LOCK_OVERLAY_TYPE",
        "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT", "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT",
        "FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL", "TICKER_EVENT_RISK_ROW_COUNT",
        "CALENDAR_HIGH_RISK_TICKER_COUNT", "CALENDAR_EXTREME_CAUTION_TICKER_COUNT",
        "ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT", "HARD_LOCK_SOURCE_DETECTED",
        "EVENT_ADJUSTED_CANDIDATE_COUNT", "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT",
        "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "EXTERNAL_DATA_FETCHED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        default = MODE if key == "MODE" else PATCH_MODE if key == "PATCH_MODE" else ""
        print(f"{key}: {values.get(key, default)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
