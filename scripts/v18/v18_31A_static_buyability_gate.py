from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_31A_STATIC_BUYABILITY_GATE_DRY_RUN_READY"
STATUS_OK = "OK_V18_31A_STATIC_BUYABILITY_GATE_READY"
STATUS_WARN = "WARN_V18_31A_STATIC_BUYABILITY_GATE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31A_STATIC_BUYABILITY_GATE_FAILED"
MODE_LIVE = "STATIC_MANUAL_BUYABILITY_GATE"
MODE_DRY = "STATIC_MANUAL_BUYABILITY_GATE_DRY_RUN"
EXPECTED_ROWS = 252

RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
R30E_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"
R30A_SUMMARY = "outputs/v18/ops/V18_30A_OPERATOR_STATUS_SUMMARY.csv"

OUT_BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_BUYABILITY_GATE.md"
OUT_REPORT = "outputs/v18/read_center/V18_31A_STATIC_BUYABILITY_GATE_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_31A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31A_STATIC_BUYABILITY_GATE_SUMMARY.csv"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_31A_STATIC_BUYABILITY_GATE_ERROR.md"

OUTPUT_FIELDS = [
    "ticker",
    "rank",
    "composite_candidate_score",
    "primary_theme",
    "recommendation_tier",
    "manual_action",
    "risk_bucket",
    "technical_timing_status",
    "technical_timing_score",
    "overheat_flag",
    "buy_now_status",
    "buy_now_score",
    "buy_gate_result",
    "buy_block_reason",
    "entry_condition",
    "manual_operator_action",
    "gate_recommendation_pass",
    "gate_technical_pass",
    "gate_overheat_pass",
    "gate_risk_pass",
    "gate_operator_pass",
    "gate_data_quality_pass",
    "gate_summary",
    "source_recommendation_file",
    "source_technical_file",
    "generated_at",
    "run_id",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "TOP_N_REQUESTED",
    "SOURCE_RECOMMENDATION_FILE",
    "SOURCE_RECOMMENDATION_ROWS",
    "SOURCE_RANKED_CANDIDATE_FILE",
    "SOURCE_RANKED_CANDIDATE_ROWS",
    "SOURCE_TECHNICAL_FILE",
    "SOURCE_TECHNICAL_ROWS",
    "OUTPUT_BUYABILITY_ROWS",
    "BUY_NOW_ALLOWED_COUNT",
    "BUY_SMALL_ONLY_COUNT",
    "WATCH_FOR_ENTRY_COUNT",
    "WAIT_FOR_PULLBACK_COUNT",
    "REVIEW_FIRST_COUNT",
    "DO_NOT_BUY_NOW_COUNT",
    "BLOCKED_BY_RISK_COUNT",
    "BLOCKED_BY_OPERATOR_STATE_COUNT",
    "BLOCKED_BY_DATA_QUALITY_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "R30E_STATUS",
    "R30A_STATUS",
    "FORWARD_RETURN_FILLABLE_READY",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "mode",
    "generated_at",
    "source_recommendation_rows",
    "source_ranked_candidate_rows",
    "source_technical_rows",
    "output_rows",
    "buy_now_allowed_count",
    "buy_small_only_count",
    "watch_for_entry_count",
    "wait_for_pullback_count",
    "review_first_count",
    "do_not_buy_now_count",
    "blocked_count",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

PROTECTED_INPUTS = [
    RECOMMENDATIONS,
    RANKED,
    THEMES,
    TECHNICAL,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv",
]

TIER_BASE = {
    "CORE_CANDIDATE": 75,
    "WATCHLIST_STRONG": 65,
    "TACTICAL_ENTRY": 60,
    "SPECULATIVE_SATELLITE": 45,
    "DEFENSIVE_HEDGE": 50,
    "ETF_OR_MACRO_EXPOSURE": 45,
    "OVERHEATED_WAIT": 20,
    "DO_NOT_PRIORITIZE": 10,
}


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def upper(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm(value)
        return int(float(text)) if text else default
    except Exception:
        return default


def to_float(value: object, default: Optional[float] = None) -> Optional[float]:
    try:
        text = norm(value)
        return float(text) if text else default
    except Exception:
        return default


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    raise RuntimeError(f"Unable to read CSV: {path}")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def protected_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    return {rel: file_sig(root / rel) for rel in PROTECTED_INPUTS}


def field_map(fields: Sequence[str]) -> Dict[str, str]:
    return {field.strip().lower(): field for field in fields}


def alias_col(fields: Sequence[str], aliases: Sequence[str]) -> str:
    lower = field_map(fields)
    for alias in aliases:
        if alias.lower() in lower:
            return lower[alias.lower()]
    return ""


def val(row: Dict[str, str], fields: Sequence[str], aliases: Sequence[str]) -> str:
    col = alias_col(fields, aliases)
    return norm(row.get(col)) if col else ""


def ticker_value(row: Dict[str, str], fields: Sequence[str]) -> str:
    return val(row, fields, ["ticker", "symbol"]).upper()


def lookup_by_ticker(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = ticker_value(row, fields)
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def normalize_score(value: object) -> Optional[float]:
    score = to_float(value)
    if score is None:
        return None
    return score / 100.0 if score > 1.0 else score


def technical_class(status_text: str, score_value: object) -> str:
    text = upper(status_text)
    unfavorable = ["OVERHEAT", "EXTREME", "EXTENDED", "WAIT", "SELL", "AVOID", "BB_NEAR_UPPER", "RSI_EXTREME"]
    favorable = ["ENTRY", "BUY", "PULLBACK_OK", "NEUTRAL_OK", "SUPPORT", "OVERSOLD_BOUNCE"]
    caution = ["NEUTRAL", "WATCH", "MIXED"]
    if any(word in text for word in unfavorable):
        return "UNFAVORABLE"
    if any(word in text for word in favorable):
        return "FAVORABLE"
    if any(word in text for word in caution):
        return "CAUTION"
    score = normalize_score(score_value)
    if score is None:
        return "CAUTION"
    if score >= 0.60:
        return "FAVORABLE"
    if score >= 0.40:
        return "CAUTION"
    return "UNFAVORABLE"


def overheat_detected(row_text: str, score_penalty: object) -> bool:
    text = upper(row_text)
    hot_words = ["TRUE", "OVERHEATED", "OVERHEAT", "EXTREME", "RSI_EXTREME", "BB_NEAR_UPPER", "ABOVE_UPPER", "BREAKOUT_OVERHEAT"]
    if any(word in text for word in hot_words):
        return True
    penalty = to_float(score_penalty, 0.0) or 0.0
    return penalty > 0


def risk_class(risk_text: str) -> str:
    text = upper(risk_text)
    if "EXTREME" in text:
        return "EXTREME_RISK"
    if "HIGH" in text:
        return "HIGH_RISK"
    if "LOW" in text:
        return "LOW_RISK"
    if "MEDIUM" in text:
        return "MEDIUM_RISK"
    return text or "UNKNOWN_RISK"


def operator_context(root: Path, rec_count: int, ranked_count: int, theme_count: int, allow_r30a_warn: bool) -> Dict[str, object]:
    r30e = read_status_file(root / R30E_READ_FIRST)
    r30a = read_status_file(root / R30A_READ_FIRST)
    context = r30e if r30e else {}
    current_ranked = to_int(context.get("CURRENT_RANKED_CANDIDATE_ROWS"), ranked_count)
    current_recs = to_int(context.get("CURRENT_RECOMMENDATION_ROWS"), rec_count)
    current_themes = to_int(context.get("CURRENT_THEME_CLASSIFICATION_ROWS"), theme_count)
    latest_freeze = to_int(context.get("LATEST_FULL_FREEZE_TICKER_COUNT"), to_int(r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT"), 0))
    auto_trade = context.get("AUTO_TRADE") or r30a.get("AUTO_TRADE") or "DISABLED"
    auto_sell = context.get("AUTO_SELL") or r30a.get("AUTO_SELL") or "DISABLED"
    impact = context.get("OFFICIAL_DECISION_IMPACT") or r30a.get("OFFICIAL_DECISION_IMPACT") or "NONE"
    r30a_status = context.get("R30A_STATUS") or r30a.get("STATUS", "")
    r30e_status = context.get("STATUS", "")
    forward_total = sum(
        to_int(r30a.get(field))
        for field in [
            "FORWARD_1D_FILLABLE_COUNT",
            "FORWARD_3D_FILLABLE_COUNT",
            "FORWARD_5D_FILLABLE_COUNT",
            "FORWARD_10D_FILLABLE_COUNT",
            "FORWARD_20D_FILLABLE_COUNT",
        ]
    )
    forward_ready = forward_total > 0
    structural_ok = (
        current_ranked == EXPECTED_ROWS
        and current_recs == EXPECTED_ROWS
        and current_themes == EXPECTED_ROWS
        and latest_freeze == EXPECTED_ROWS
        and auto_trade == "DISABLED"
        and auto_sell == "DISABLED"
        and impact == "NONE"
    )
    r30_warn_only = (
        allow_r30a_warn
        and not forward_ready
        and structural_ok
        and (r30a_status.startswith("WARN_") or r30e_status.startswith("WARN_"))
    )
    return {
        "r30e_status": r30e_status,
        "r30a_status": r30a_status,
        "current_ranked": current_ranked,
        "current_recs": current_recs,
        "current_themes": current_themes,
        "latest_freeze": latest_freeze,
        "auto_trade": auto_trade,
        "auto_sell": auto_sell,
        "impact": impact,
        "structural_ok": structural_ok,
        "forward_ready": forward_ready,
        "r30_warn_only": r30_warn_only,
    }


def build_source_row(
    rec: Dict[str, str],
    rec_fields: Sequence[str],
    ranked: Dict[str, str],
    ranked_fields: Sequence[str],
    tech: Dict[str, str],
    tech_fields: Sequence[str],
) -> Dict[str, object]:
    ticker = ticker_value(rec, rec_fields) or ticker_value(ranked, ranked_fields) or ticker_value(tech, tech_fields)
    rank = val(rec, rec_fields, ["rank", "candidate_rank", "factor_pack_rank"]) or val(ranked, ranked_fields, ["rank", "candidate_rank", "factor_pack_rank"])
    score = val(rec, rec_fields, ["composite_candidate_score", "final_score", "score"]) or val(ranked, ranked_fields, ["composite_candidate_score", "final_score", "score"])
    theme = val(rec, rec_fields, ["primary_theme", "theme"]) or val(ranked, ranked_fields, ["primary_theme", "theme"])
    tier = val(rec, rec_fields, ["recommendation_tier", "tier"])
    manual_action = val(rec, rec_fields, ["manual_action", "recommended_action", "recommendation_action", "action"])
    risk = val(rec, rec_fields, ["risk_bucket", "risk_label", "volatility_bucket", "risk_level"]) or val(ranked, ranked_fields, ["risk_bucket", "risk_label", "volatility_bucket", "risk_level"])
    tech_status_parts = [
        val(rec, rec_fields, ["technical_timing_status", "timing_status", "technical_status", "technical_signal"]),
        val(rec, rec_fields, ["technical_warning_label"]),
        val(rec, rec_fields, ["bb_status"]),
        val(rec, rec_fields, ["rsi_status"]),
        val(tech, tech_fields, ["technical_timing_status", "timing_status", "technical_status", "technical_signal"]),
        val(tech, tech_fields, ["technical_warning_label"]),
        val(tech, tech_fields, ["bb_status"]),
        val(tech, tech_fields, ["rsi_status"]),
    ]
    tech_status = ";".join(part for part in tech_status_parts if part)
    tech_score = val(tech, tech_fields, ["technical_timing_score"]) or val(rec, rec_fields, ["technical_timing_score"])
    overheat_text = ";".join(
        part
        for part in [
            val(rec, rec_fields, ["overheat_flag", "overheat_status", "is_overheated", "rsi_status", "bb_status", "technical_warning_label"]),
            val(tech, tech_fields, ["overheat_flag", "overheat_status", "is_overheated", "rsi_status", "bb_status", "technical_warning_label"]),
        ]
        if part
    )
    overheat_penalty = val(rec, rec_fields, ["overheat_penalty"]) or val(tech, tech_fields, ["overheat_penalty"])
    return {
        "ticker": ticker,
        "rank": rank,
        "composite_candidate_score": score,
        "primary_theme": theme,
        "recommendation_tier": upper(tier),
        "manual_action": manual_action,
        "risk_bucket": risk_class(risk),
        "technical_timing_status": tech_status,
        "technical_timing_score": tech_score,
        "overheat_flag": bool_text(overheat_detected(overheat_text, overheat_penalty)),
    }


def classify_buyability(source: Dict[str, object], operator_ok: bool) -> Dict[str, object]:
    missing = [field for field in ["ticker", "rank", "recommendation_tier"] if not norm(source.get(field))]
    tier = upper(source.get("recommendation_tier"))
    risk = risk_class(norm(source.get("risk_bucket")))
    tech = technical_class(norm(source.get("technical_timing_status")), source.get("technical_timing_score"))
    overheated = source.get("overheat_flag") == "TRUE" or tier == "OVERHEATED_WAIT"
    reasons: List[str] = []
    score = TIER_BASE.get(tier, 40)
    if tech == "FAVORABLE":
        score += 10
    elif tech == "UNFAVORABLE":
        score -= 20
        reasons.append("TECHNICAL_UNFAVORABLE")
    else:
        reasons.append("TECHNICAL_CAUTION")
    if overheated:
        score -= 25
        reasons.append("OVERHEAT_OR_CHASE_RISK")
    if risk == "HIGH_RISK":
        score -= 10
        reasons.append("HIGH_RISK")
    elif risk == "EXTREME_RISK":
        score -= 20
        reasons.append("EXTREME_RISK")
    if missing:
        score -= 30
        reasons.append("MISSING_" + "_".join(missing).upper())
    score = clamp(score)

    gate_data = not missing
    gate_operator = operator_ok
    gate_recommendation = tier not in {"", "DO_NOT_PRIORITIZE"}
    gate_technical = tech != "UNFAVORABLE"
    gate_overheat = not overheated
    gate_risk = risk != "EXTREME_RISK"

    status = "REVIEW_FIRST"
    action = "REVIEW_FIRST"
    entry = "REVIEW_FUNDAMENTALS_AND_EVENT_RISK_FIRST"
    if not gate_data:
        status, action, entry = "BLOCKED_BY_DATA_QUALITY", "BLOCKED", "BLOCKED_DATA_QUALITY"
    elif not gate_operator:
        status, action, entry = "BLOCKED_BY_OPERATOR_STATE", "BLOCKED", "BLOCKED_OPERATOR_STATE"
    elif tier == "DO_NOT_PRIORITIZE":
        status, action, entry = "DO_NOT_BUY_NOW", "DO_NOT_BUY", "DO_NOT_BUY_LOW_PRIORITY"
    elif tier == "OVERHEATED_WAIT" or overheated:
        if tier == "SPECULATIVE_SATELLITE":
            status, action, entry = "DO_NOT_BUY_NOW", "DO_NOT_BUY", "WAIT_FOR_PULLBACK_OVERHEAT_CLEAR"
        else:
            status, action, entry = "WAIT_FOR_PULLBACK", "WAIT_FOR_PULLBACK", "WAIT_FOR_PULLBACK_OVERHEAT_CLEAR"
    elif risk == "EXTREME_RISK":
        if tier in {"SPECULATIVE_SATELLITE", "TACTICAL_ENTRY"} and tech == "FAVORABLE":
            status, action, entry = "BUY_SMALL_ONLY", "SMALL_SIZE_ONLY", "SMALL_SIZE_ONLY_HIGH_RISK"
        else:
            status, action, entry = "BLOCKED_BY_RISK", "BLOCKED", "REVIEW_FUNDAMENTALS_AND_EVENT_RISK_FIRST"
    elif tier == "SPECULATIVE_SATELLITE":
        if tech == "FAVORABLE" and score >= 45 and risk != "HIGH_RISK":
            status, action, entry = "BUY_SMALL_ONLY", "SMALL_SIZE_ONLY", "SMALL_SIZE_ONLY_HIGH_RISK"
        elif tech == "FAVORABLE" and score >= 35:
            status, action, entry = "BUY_SMALL_ONLY", "SMALL_SIZE_ONLY", "SMALL_SIZE_ONLY_HIGH_RISK"
        elif score < 35:
            status, action, entry = "DO_NOT_BUY_NOW", "DO_NOT_BUY", "WAIT_FOR_TECHNICAL_ENTRY_CONFIRMATION"
        else:
            status, action, entry = "WATCH_FOR_ENTRY", "WATCH_FOR_ENTRY", "WAIT_FOR_TECHNICAL_ENTRY_CONFIRMATION"
    elif tier == "WATCHLIST_STRONG":
        if tech == "FAVORABLE" and gate_overheat and score >= 75:
            status, action, entry = "BUY_NOW_ALLOWED", "CONSIDER_MANUAL_BUY", "TECHNICAL_OK_MANUAL_REVIEW_REQUIRED"
        else:
            status, action, entry = "WATCH_FOR_ENTRY", "WATCH_FOR_ENTRY", "WAIT_FOR_TECHNICAL_ENTRY_CONFIRMATION"
    elif tier == "TACTICAL_ENTRY":
        if tech == "FAVORABLE" and risk == "HIGH_RISK":
            status, action, entry = "BUY_SMALL_ONLY", "SMALL_SIZE_ONLY", "SMALL_SIZE_ONLY_HIGH_RISK"
        elif tech == "FAVORABLE" and score >= 75:
            status, action, entry = "BUY_NOW_ALLOWED", "CONSIDER_MANUAL_BUY", "TECHNICAL_OK_MANUAL_REVIEW_REQUIRED"
        else:
            status, action, entry = "WATCH_FOR_ENTRY", "WATCH_FOR_ENTRY", "WAIT_FOR_TECHNICAL_ENTRY_CONFIRMATION"
    elif tier == "CORE_CANDIDATE":
        if tech == "FAVORABLE" and risk == "HIGH_RISK":
            status, action, entry = "BUY_SMALL_ONLY", "SMALL_SIZE_ONLY", "SMALL_SIZE_ONLY_HIGH_RISK"
        elif tech == "FAVORABLE" and score >= 75:
            status, action, entry = "BUY_NOW_ALLOWED", "CONSIDER_MANUAL_BUY", "TECHNICAL_OK_MANUAL_REVIEW_REQUIRED"
        elif score >= 65:
            status, action, entry = "REVIEW_FIRST", "REVIEW_FIRST", "REVIEW_FUNDAMENTALS_AND_EVENT_RISK_FIRST"
        else:
            status, action, entry = "WATCH_FOR_ENTRY", "WATCH_FOR_ENTRY", "WAIT_FOR_TECHNICAL_ENTRY_CONFIRMATION"
    elif tier in {"DEFENSIVE_HEDGE", "ETF_OR_MACRO_EXPOSURE"}:
        status, action, entry = "REVIEW_FIRST", "REVIEW_FIRST", "REVIEW_FUNDAMENTALS_AND_EVENT_RISK_FIRST"
    else:
        status, action, entry = "REVIEW_FIRST", "REVIEW_FIRST", "REVIEW_FUNDAMENTALS_AND_EVENT_RISK_FIRST"

    if status in {"BUY_NOW_ALLOWED", "BUY_SMALL_ONLY", "REVIEW_FIRST"} and tech == "CAUTION":
        reasons.append("TECHNICAL_NOT_CLEAR")
    if not reasons:
        reasons.append("GATES_PASS_MANUAL_REVIEW_REQUIRED")

    buy_gate_result = "PASS" if status == "BUY_NOW_ALLOWED" else ("BLOCK" if status.startswith("BLOCKED") or status == "DO_NOT_BUY_NOW" else "CAUTION")
    source.update(
        {
            "buy_now_status": status,
            "buy_now_score": score,
            "buy_gate_result": buy_gate_result,
            "buy_block_reason": ";".join(dict.fromkeys(reasons)),
            "entry_condition": entry,
            "manual_operator_action": action,
            "gate_recommendation_pass": bool_text(gate_recommendation),
            "gate_technical_pass": bool_text(gate_technical),
            "gate_overheat_pass": bool_text(gate_overheat),
            "gate_risk_pass": bool_text(gate_risk),
            "gate_operator_pass": bool_text(gate_operator),
            "gate_data_quality_pass": bool_text(gate_data),
            "gate_summary": f"tier={tier};technical={tech};risk={risk};overheat={source.get('overheat_flag')};manual_only=TRUE",
        }
    )
    return source


def status_counts(rows: Sequence[Dict[str, object]]) -> Counter:
    return Counter(norm(row.get("buy_now_status")) for row in rows)


def validation_fail_count(values: Dict[str, object]) -> int:
    fails = 0
    if values.get("AUTO_TRADE") != "DISABLED":
        fails += 1
    if values.get("AUTO_SELL") != "DISABLED":
        fails += 1
    if values.get("OFFICIAL_DECISION_IMPACT") != "NONE":
        fails += 1
    if values.get("FORBIDDEN_MODIFIED") != "FALSE":
        fails += 1
    if to_int(values.get("OUTPUT_BUYABILITY_ROWS")) not in (0, EXPECTED_ROWS):
        fails += 1
    for field in ["CURRENT_RANKED_CANDIDATE_ROWS", "CURRENT_RECOMMENDATION_ROWS", "CURRENT_THEME_CLASSIFICATION_ROWS", "LATEST_FULL_FREEZE_TICKER_COUNT"]:
        if to_int(values.get(field)) not in (0, EXPECTED_ROWS):
            fails += 1
    return fails


def read_first_text(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def md_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 25) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    counts = [{"buy_now_status": key, "count": count} for key, count in status_counts(rows).most_common()]
    fields = ["rank", "ticker", "recommendation_tier", "risk_bucket", "technical_timing_score", "buy_now_score", "entry_condition", "buy_block_reason"]
    top_ranked_pullbacks = sorted(
        [row for row in rows if row.get("buy_now_status") == "WAIT_FOR_PULLBACK"],
        key=lambda row: to_int(row.get("rank"), 999999),
    )
    warnings = []
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        warnings.append("FORWARD_RETURN_NOT_READY_MANUAL_REVIEW_ONLY")
    if values.get("STATUS", "").startswith("WARN_"):
        warnings.append("R30A_OR_R30E_WARN_REVIEW_NEEDED")
    if not warnings:
        warnings.append("NONE")
    return "\n".join(
        [
            "# V18 Current Buyability Gate",
            "",
            f"STATUS: {values.get('STATUS', '')}",
            f"RUN_ID: {values.get('RUN_ID', '')}",
            f"GENERATED_AT: {values.get('_GENERATED_AT', '')}",
            "",
            "This is manual research guidance only. It does not place trades and does not override operator judgment.",
            "",
            "## Counts By Buy Now Status",
            md_table(counts, ["buy_now_status", "count"], 20),
            "## Top BUY_NOW_ALLOWED",
            md_table([row for row in rows if row.get("buy_now_status") == "BUY_NOW_ALLOWED"], fields, 25),
            "## Top BUY_SMALL_ONLY",
            md_table([row for row in rows if row.get("buy_now_status") == "BUY_SMALL_ONLY"], fields, 25),
            "## Top WATCH_FOR_ENTRY",
            md_table([row for row in rows if row.get("buy_now_status") == "WATCH_FOR_ENTRY"], fields, 25),
            "## WAIT_FOR_PULLBACK Among Top Ranked Names",
            md_table(top_ranked_pullbacks, fields, 30),
            "## Warnings And Safety Notes",
            "\n".join(f"- `{warning}`" for warning in warnings),
            "- `AUTO_TRADE: DISABLED`",
            "- `AUTO_SELL: DISABLED`",
            "- `OFFICIAL_DECISION_IMPACT: NONE`",
            "- `BROKER_API_CALLS: NOT_EXECUTED`",
            "- `ORDER_PLACEMENT: NOT_EXECUTED`",
        ]
    ) + "\n"


def build_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [
        {
            "run_id": values.get("RUN_ID", ""),
            "status": values.get("STATUS", ""),
            "mode": values.get("MODE", ""),
            "generated_at": values.get("_GENERATED_AT", ""),
            "source_recommendation_rows": values.get("SOURCE_RECOMMENDATION_ROWS", ""),
            "source_ranked_candidate_rows": values.get("SOURCE_RANKED_CANDIDATE_ROWS", ""),
            "source_technical_rows": values.get("SOURCE_TECHNICAL_ROWS", ""),
            "output_rows": values.get("OUTPUT_BUYABILITY_ROWS", ""),
            "buy_now_allowed_count": values.get("BUY_NOW_ALLOWED_COUNT", ""),
            "buy_small_only_count": values.get("BUY_SMALL_ONLY_COUNT", ""),
            "watch_for_entry_count": values.get("WATCH_FOR_ENTRY_COUNT", ""),
            "wait_for_pullback_count": values.get("WAIT_FOR_PULLBACK_COUNT", ""),
            "review_first_count": values.get("REVIEW_FIRST_COUNT", ""),
            "do_not_buy_now_count": values.get("DO_NOT_BUY_NOW_COUNT", ""),
            "blocked_count": (
                to_int(values.get("BLOCKED_BY_RISK_COUNT"))
                + to_int(values.get("BLOCKED_BY_OPERATOR_STATE_COUNT"))
                + to_int(values.get("BLOCKED_BY_DATA_QUALITY_COUNT"))
            ),
            "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
            "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
            "notes": notes,
        }
    ]


def write_outputs(root: Path, values: Dict[str, object], rows: Sequence[Dict[str, object]], dry_run: bool, notes: str) -> None:
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    if not dry_run:
        write_csv(root / OUT_BUYABILITY, rows, OUTPUT_FIELDS)
    report = build_report(values, rows)
    write_text(root / OUT_CURRENT_REPORT, report)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, notes), SUMMARY_FIELDS)


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31A_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    before = protected_sig(root)

    recs, rec_fields = read_csv(root / RECOMMENDATIONS)
    ranked, ranked_fields = read_csv(root / RANKED)
    themes, _theme_fields = read_csv(root / THEMES)
    tech_rows, tech_fields = read_csv(root / TECHNICAL)
    required_missing = [rel for rel in [RECOMMENDATIONS, RANKED, TECHNICAL] if not (root / rel).exists()]
    tech_lookup = lookup_by_ticker(tech_rows, tech_fields)
    ranked_lookup = lookup_by_ticker(ranked, ranked_fields)

    context = operator_context(root, len(recs), len(ranked), len(themes), args.allow_r30a_warn)
    operator_ok = bool(context["structural_ok"])
    output_rows: List[Dict[str, object]] = []
    if not required_missing:
        for rec in recs[: max(args.top_n, 0)]:
            ticker = ticker_value(rec, rec_fields)
            source = build_source_row(rec, rec_fields, ranked_lookup.get(ticker, {}), ranked_fields, tech_lookup.get(ticker, {}), tech_fields)
            output_rows.append(classify_buyability(source, operator_ok))
    counts = status_counts(output_rows)

    values: Dict[str, object] = {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "SOURCE_RECOMMENDATION_FILE": str(root / RECOMMENDATIONS),
        "SOURCE_RECOMMENDATION_ROWS": len(recs),
        "SOURCE_RANKED_CANDIDATE_FILE": str(root / RANKED),
        "SOURCE_RANKED_CANDIDATE_ROWS": len(ranked),
        "SOURCE_TECHNICAL_FILE": str(root / TECHNICAL),
        "SOURCE_TECHNICAL_ROWS": len(tech_rows),
        "OUTPUT_BUYABILITY_ROWS": len(output_rows) if not args.dry_run else 0,
        "BUY_NOW_ALLOWED_COUNT": counts.get("BUY_NOW_ALLOWED", 0),
        "BUY_SMALL_ONLY_COUNT": counts.get("BUY_SMALL_ONLY", 0),
        "WATCH_FOR_ENTRY_COUNT": counts.get("WATCH_FOR_ENTRY", 0),
        "WAIT_FOR_PULLBACK_COUNT": counts.get("WAIT_FOR_PULLBACK", 0),
        "REVIEW_FIRST_COUNT": counts.get("REVIEW_FIRST", 0),
        "DO_NOT_BUY_NOW_COUNT": counts.get("DO_NOT_BUY_NOW", 0),
        "BLOCKED_BY_RISK_COUNT": counts.get("BLOCKED_BY_RISK", 0),
        "BLOCKED_BY_OPERATOR_STATE_COUNT": counts.get("BLOCKED_BY_OPERATOR_STATE", 0),
        "BLOCKED_BY_DATA_QUALITY_COUNT": counts.get("BLOCKED_BY_DATA_QUALITY", 0),
        "CURRENT_RANKED_CANDIDATE_ROWS": context["current_ranked"],
        "CURRENT_RECOMMENDATION_ROWS": context["current_recs"],
        "CURRENT_THEME_CLASSIFICATION_ROWS": context["current_themes"],
        "LATEST_FULL_FREEZE_TICKER_COUNT": context["latest_freeze"],
        "R30E_STATUS": context["r30e_status"],
        "R30A_STATUS": context["r30a_status"],
        "FORWARD_RETURN_FILLABLE_READY": bool_text(bool(context["forward_ready"])),
        "AUTO_TRADE": context["auto_trade"],
        "AUTO_SELL": context["auto_sell"],
        "OFFICIAL_DECISION_IMPACT": context["impact"],
        "VALIDATION_FAIL_COUNT": 0,
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "",
        "_GENERATED_AT": generated_at,
    }

    notes = ""
    if required_missing:
        notes = "Missing required inputs: " + "; ".join(required_missing)
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Restore required inputs before generating buyability gate."
    elif args.dry_run:
        notes = "Dry run only; current buyability CSV not written."
        values["STATUS"] = STATUS_DRY
        values["NEXT_RECOMMENDED_STEP"] = "Run live R31A to generate current buyability gate."
    elif len(recs) != EXPECTED_ROWS or len(ranked) != EXPECTED_ROWS or len(themes) != EXPECTED_ROWS or len(output_rows) != args.top_n:
        notes = "Structural row count mismatch."
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Run R30E/R30A and inspect structural inputs before using buyability gate."
    elif not operator_ok:
        notes = "Operator state blocked all rows."
        values["STATUS"] = STATUS_FAIL if args.strict else STATUS_WARN
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R30E/R30A operator state before manual buy review."
    elif context["r30_warn_only"]:
        notes = "FORWARD_RETURN_NOT_READY_MANUAL_REVIEW_ONLY"
        values["STATUS"] = STATUS_WARN
        values["NEXT_RECOMMENDED_STEP"] = "Manual review only; do not run performance extraction until forward returns are fillable."
    else:
        notes = "Static buyability gate ready."
        values["STATUS"] = STATUS_OK
        values["NEXT_RECOMMENDED_STEP"] = "Use V18_CURRENT_BUYABILITY_GATE.md for manual research review only."

    after = protected_sig(root)
    values["FORBIDDEN_MODIFIED"] = bool_text(after != before)
    if values["FORBIDDEN_MODIFIED"] != "FALSE":
        values["STATUS"] = STATUS_FAIL
        notes = "Forbidden input modification detected."
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31A error report; do not trade from this run."

    write_outputs(root, values, output_rows, args.dry_run, notes)
    if values["STATUS"] == STATUS_FAIL:
        write_text(root / OUT_ERROR_REPORT, f"# V18.31A Static Buyability Gate Error\n\n```text\n{notes}\n```\n")
        return 1, values
    return 0, values


def write_failure(root: Path, error: BaseException, args: argparse.Namespace) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31A_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "SOURCE_RECOMMENDATION_FILE": str(root / RECOMMENDATIONS),
        "SOURCE_RECOMMENDATION_ROWS": 0,
        "SOURCE_RANKED_CANDIDATE_FILE": str(root / RANKED),
        "SOURCE_RANKED_CANDIDATE_ROWS": 0,
        "SOURCE_TECHNICAL_FILE": str(root / TECHNICAL),
        "SOURCE_TECHNICAL_ROWS": 0,
        "OUTPUT_BUYABILITY_ROWS": 0,
        "BUY_NOW_ALLOWED_COUNT": 0,
        "BUY_SMALL_ONLY_COUNT": 0,
        "WATCH_FOR_ENTRY_COUNT": 0,
        "WAIT_FOR_PULLBACK_COUNT": 0,
        "REVIEW_FIRST_COUNT": 0,
        "DO_NOT_BUY_NOW_COUNT": 0,
        "BLOCKED_BY_RISK_COUNT": 0,
        "BLOCKED_BY_OPERATOR_STATE_COUNT": 0,
        "BLOCKED_BY_DATA_QUALITY_COUNT": 0,
        "CURRENT_RANKED_CANDIDATE_ROWS": 0,
        "CURRENT_RECOMMENDATION_ROWS": 0,
        "CURRENT_THEME_CLASSIFICATION_ROWS": 0,
        "LATEST_FULL_FREEZE_TICKER_COUNT": 0,
        "R30E_STATUS": "",
        "R30A_STATUS": "",
        "FORWARD_RETURN_FILLABLE_READY": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 1,
        "FORBIDDEN_MODIFIED": "UNKNOWN",
        "NEXT_RECOMMENDED_STEP": "Inspect R31A error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    }
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, str(error)), SUMMARY_FIELDS)
    write_text(root / OUT_ERROR_REPORT, f"# V18.31A Static Buyability Gate Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31A static manual buyability gate.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--allow-r30a-warn", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Compatibility flag; no files are opened by this script.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        code, values = run(root, args)
        print(f"STATUS: {values.get('STATUS', '')}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return code
    except Exception as exc:
        values = write_failure(root, exc, args)
        print(f"STATUS: {values.get('STATUS', STATUS_FAIL)}")
        print(f"ERROR: {exc}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
