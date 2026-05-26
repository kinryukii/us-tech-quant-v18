from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_31B_POSITION_SIZING_POLICY_DRY_RUN_READY"
STATUS_OK = "OK_V18_31B_MANUAL_POSITION_SIZING_POLICY_READY"
STATUS_WARN = "WARN_V18_31B_MANUAL_POSITION_SIZING_POLICY_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31B_MANUAL_POSITION_SIZING_POLICY_FAILED"
MODE_LIVE = "MANUAL_POSITION_SIZING_POLICY_LAYER"
MODE_DRY = "MANUAL_POSITION_SIZING_POLICY_DRY_RUN"
EXPECTED_ROWS = 252
MIN_EFFECTIVE_TRADE_NOTIONAL_USD = 50.0

BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
R31A_READ_FIRST = "outputs/v18/ops/V18_31A_READ_FIRST.txt"
R30E_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"
R30A_SUMMARY = "outputs/v18/ops/V18_30A_OPERATOR_STATUS_SUMMARY.csv"

OUT_POLICY = "outputs/v18/execution/V18_CURRENT_POSITION_SIZING_POLICY.csv"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_POSITION_SIZING_POLICY.md"
OUT_REPORT = "outputs/v18/read_center/V18_31B_MANUAL_POSITION_SIZING_POLICY_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_31B_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31B_POSITION_SIZING_POLICY_SUMMARY.csv"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_31B_MANUAL_POSITION_SIZING_POLICY_ERROR.md"

OUTPUT_FIELDS = [
    "ticker",
    "rank",
    "composite_candidate_score",
    "primary_theme",
    "recommendation_tier",
    "buy_now_status",
    "buy_now_score",
    "manual_operator_action",
    "risk_bucket",
    "technical_timing_status",
    "overheat_flag",
    "position_policy_status",
    "position_policy_action",
    "risk_budget_pct_of_account",
    "stop_review_pct",
    "take_profit_review_pct",
    "suggested_initial_position_pct",
    "suggested_max_position_pct",
    "suggested_initial_notional_usd",
    "suggested_max_notional_usd",
    "max_loss_usd_at_stop",
    "min_effective_trade_notional_usd",
    "below_min_effective_trade_flag",
    "concentration_caution",
    "position_size_reason",
    "sizing_formula",
    "account_size_usd",
    "cash_reserve_pct",
    "max_active_positions",
    "max_speculative_positions",
    "source_buyability_file",
    "generated_at",
    "run_id",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "TOP_N_REQUESTED",
    "ACCOUNT_SIZE_USD",
    "CASH_RESERVE_PCT",
    "MAX_ACTIVE_POSITIONS",
    "MAX_SPECULATIVE_POSITIONS",
    "SOURCE_BUYABILITY_FILE",
    "SOURCE_BUYABILITY_ROWS",
    "SOURCE_RECOMMENDATION_FILE",
    "SOURCE_RECOMMENDATION_ROWS",
    "SOURCE_RANKED_CANDIDATE_FILE",
    "SOURCE_RANKED_CANDIDATE_ROWS",
    "OUTPUT_POSITION_POLICY_ROWS",
    "POSITION_ALLOWED_COUNT",
    "POSITION_SMALL_ONLY_COUNT",
    "POSITION_WATCH_ONLY_COUNT",
    "POSITION_WAIT_PULLBACK_COUNT",
    "POSITION_REVIEW_FIRST_COUNT",
    "POSITION_BLOCKED_COUNT",
    "POSITION_OPERATOR_BLOCKED_COUNT",
    "POSITION_DATA_QUALITY_BLOCKED_COUNT",
    "TOTAL_INITIAL_NOTIONAL_USD_IF_ALL_ALLOWED",
    "TOTAL_INITIAL_POSITION_PCT_IF_ALL_ALLOWED",
    "TOTAL_MAX_NOTIONAL_USD_POLICY_CAP",
    "TOTAL_MAX_POSITION_PCT_POLICY_CAP",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "R31A_STATUS",
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
    "account_size_usd",
    "source_buyability_rows",
    "source_recommendation_rows",
    "source_ranked_candidate_rows",
    "output_rows",
    "position_allowed_count",
    "position_small_only_count",
    "position_watch_only_count",
    "position_wait_pullback_count",
    "position_review_first_count",
    "position_blocked_count",
    "operator_blocked_count",
    "data_quality_blocked_count",
    "total_initial_notional_usd_if_all_allowed",
    "total_initial_position_pct_if_all_allowed",
    "total_max_notional_usd_policy_cap",
    "total_max_position_pct_policy_cap",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

PROTECTED_INPUTS = [
    BUYABILITY,
    RECOMMENDATIONS,
    RANKED,
    THEMES,
    TECHNICAL,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv",
]

POLICY = {
    "CORE_CANDIDATE": (0.75, -7.0, 15.0, 6.0, 12.0),
    "WATCHLIST_STRONG": (0.50, -6.0, 10.0, 4.0, 8.0),
    "TACTICAL_ENTRY": (0.40, -5.0, 8.0, 3.0, 6.0),
    "SPECULATIVE_SATELLITE": (0.25, -10.0, 15.0, 1.5, 3.0),
    "DEFENSIVE_HEDGE": (0.50, -6.0, 8.0, 4.0, 10.0),
    "ETF_OR_MACRO_EXPOSURE": (0.40, -5.0, 7.0, 3.0, 8.0),
    "OVERHEATED_WAIT": (0.0, 0.0, 0.0, 0.0, 0.0),
    "DO_NOT_PRIORITIZE": (0.0, 0.0, 0.0, 0.0, 0.0),
}

CONCENTRATION_THEMES = {
    "SEMICONDUCTOR",
    "SEMICONDUCTOR_EQUIPMENT",
    "AI_INFRASTRUCTURE",
    "DATA_INFRASTRUCTURE",
    "CRYPTO_BETA",
    "POWER_INFRASTRUCTURE",
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


def to_float(value: object, default: float = 0.0) -> float:
    try:
        text = norm(value)
        return float(text) if text else default
    except Exception:
        return default


def money(value: float) -> str:
    return f"{value:.2f}"


def pct(value: float) -> str:
    return f"{value:.2f}"


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


def lookup(rows: Sequence[Dict[str, str]], key: str = "ticker") -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = upper(row.get(key))
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def risk_class(value: object) -> str:
    text = upper(value)
    if "EXTREME" in text:
        return "EXTREME_RISK"
    if "HIGH" in text:
        return "HIGH_RISK"
    if "LOW" in text:
        return "LOW_RISK"
    if "MEDIUM" in text:
        return "MEDIUM_RISK"
    return text or "UNKNOWN_RISK"


def technical_favorable(value: object) -> bool:
    text = upper(value)
    favorable = ["ENTRY", "BUY", "PULLBACK_OK", "NEUTRAL_OK", "SUPPORT", "OVERSOLD_BOUNCE", "WATCH_POSITIVE"]
    unfavorable = ["OVERHEAT", "EXTREME", "EXTENDED", "WAIT", "SELL", "AVOID", "BB_NEAR_UPPER", "RSI_EXTREME"]
    if any(word in text for word in unfavorable):
        return False
    if any(word in text for word in favorable):
        return True
    return False


def operator_context(root: Path, buy_rows: int, rec_rows: int, ranked_rows: int, theme_rows: int) -> Dict[str, object]:
    r31a = read_status_file(root / R31A_READ_FIRST)
    r30e = read_status_file(root / R30E_READ_FIRST)
    r30a = read_status_file(root / R30A_READ_FIRST)
    current_ranked = to_int(r31a.get("CURRENT_RANKED_CANDIDATE_ROWS") or r30e.get("CURRENT_RANKED_CANDIDATE_ROWS"), ranked_rows)
    current_recs = to_int(r31a.get("CURRENT_RECOMMENDATION_ROWS") or r30e.get("CURRENT_RECOMMENDATION_ROWS"), rec_rows)
    current_themes = to_int(r31a.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r30e.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r30a.get("THEME_CLASSIFICATION_ROW_COUNT"), theme_rows)
    latest_freeze = to_int(r31a.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r30e.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT"), 0)
    auto_trade = r31a.get("AUTO_TRADE") or r30e.get("AUTO_TRADE") or r30a.get("AUTO_TRADE") or "DISABLED"
    auto_sell = r31a.get("AUTO_SELL") or r30e.get("AUTO_SELL") or r30a.get("AUTO_SELL") or "DISABLED"
    impact = r31a.get("OFFICIAL_DECISION_IMPACT") or r30e.get("OFFICIAL_DECISION_IMPACT") or r30a.get("OFFICIAL_DECISION_IMPACT") or "NONE"
    forward_ready = (r31a.get("FORWARD_RETURN_FILLABLE_READY") == "TRUE") or any(
        to_int(r30a.get(field)) > 0
        for field in [
            "FORWARD_1D_FILLABLE_COUNT",
            "FORWARD_3D_FILLABLE_COUNT",
            "FORWARD_5D_FILLABLE_COUNT",
            "FORWARD_10D_FILLABLE_COUNT",
            "FORWARD_20D_FILLABLE_COUNT",
        ]
    )
    latest_freeze_ok = latest_freeze == EXPECTED_ROWS if latest_freeze else True
    structural_ok = (
        buy_rows == EXPECTED_ROWS
        and current_ranked == EXPECTED_ROWS
        and current_recs == EXPECTED_ROWS
        and current_themes == EXPECTED_ROWS
        and latest_freeze_ok
        and auto_trade == "DISABLED"
        and auto_sell == "DISABLED"
        and impact == "NONE"
    )
    warn_only = (
        not forward_ready
        and structural_ok
        and (
            r31a.get("STATUS", "").startswith("WARN_")
            or r30e.get("STATUS", "").startswith("WARN_")
            or r30a.get("STATUS", "").startswith("WARN_")
        )
    )
    return {
        "r31a_status": r31a.get("STATUS", ""),
        "r30e_status": r30e.get("STATUS", ""),
        "r30a_status": r30a.get("STATUS", ""),
        "current_ranked": current_ranked,
        "current_recs": current_recs,
        "current_themes": current_themes,
        "latest_freeze": latest_freeze,
        "auto_trade": auto_trade,
        "auto_sell": auto_sell,
        "impact": impact,
        "forward_ready": forward_ready,
        "structural_ok": structural_ok,
        "warn_only": warn_only,
    }


def theme_concentration(rows: Sequence[Dict[str, str]]) -> Dict[str, int]:
    top_rows = [row for row in rows if to_int(row.get("rank"), 999999) <= 50]
    counts = Counter(upper(row.get("primary_theme")) for row in top_rows)
    return {theme: count for theme, count in counts.items() if theme in CONCENTRATION_THEMES and count >= 5}


def policy_for_tier(tier: str) -> Tuple[float, float, float, float, float]:
    return POLICY.get(upper(tier), (0.0, 0.0, 0.0, 0.0, 0.0))


def risk_adjust(
    tier: str,
    risk: str,
    buy_status: str,
    technical_status: str,
    risk_budget: float,
    initial_cap: float,
    max_cap: float,
) -> Tuple[float, float, float, List[str]]:
    reasons: List[str] = []
    risk = risk_class(risk)
    if risk == "EXTREME_RISK":
        risk_budget = min(risk_budget, 0.20)
        initial_cap = min(initial_cap, 1.0)
        max_cap = min(max_cap, 2.0)
        reasons.append("EXTREME_RISK_CAP_APPLIED")
    elif risk == "HIGH_RISK":
        risk_budget = min(risk_budget, 0.35)
        initial_cap = min(initial_cap, 1.5 if buy_status == "BUY_SMALL_ONLY" else initial_cap)
        max_cap = min(max_cap, 5.0)
        reasons.append("HIGH_RISK_CAP_APPLIED")
    if buy_status == "BUY_SMALL_ONLY":
        initial_cap = min(initial_cap, 1.5)
        max_cap = min(max_cap, 3.0 if risk != "EXTREME_RISK" else 2.0)
        reasons.append("BUY_SMALL_ONLY_CAP_APPLIED")
    if risk == "HIGH_RISK" and buy_status == "BUY_NOW_ALLOWED" and not (upper(tier) == "CORE_CANDIDATE" and technical_favorable(technical_status)):
        reasons.append("BUY_NOW_DOWNGRADED_HIGH_RISK")
    return risk_budget, initial_cap, max_cap, reasons


def compute_pct(risk_budget: float, stop_pct: float, cap_pct: float) -> float:
    if risk_budget <= 0 or stop_pct == 0 or cap_pct <= 0:
        return 0.0
    return min(cap_pct, risk_budget / abs(stop_pct) * 100.0)


def classify_position(row: Dict[str, str], operator_ok: bool, account_size: float, cash_reserve_pct: float, max_active: int, max_speculative: int, concentration: Dict[str, int], run_id: str, generated_at: str, source_file: str) -> Dict[str, object]:
    ticker = upper(row.get("ticker"))
    tier = upper(row.get("recommendation_tier"))
    buy_status = upper(row.get("buy_now_status"))
    risk = risk_class(row.get("risk_bucket"))
    technical_status = norm(row.get("technical_timing_status"))
    missing = [field for field in ["ticker", "rank", "recommendation_tier", "buy_now_status"] if not norm(row.get(field))]
    risk_budget, stop_pct, take_profit_pct, initial_cap, max_cap = policy_for_tier(tier)
    risk_budget, initial_cap, max_cap, risk_reasons = risk_adjust(tier, risk, buy_status, technical_status, risk_budget, initial_cap, max_cap)

    status = "POSITION_REVIEW_FIRST"
    action = "REVIEW_FIRST"
    initial_pct = 0.0
    max_pct = 0.0
    reasons: List[str] = []
    if missing:
        status, action = "POSITION_DATA_QUALITY_BLOCKED", "BLOCKED"
        reasons.append("MISSING_" + "_".join(missing).upper())
    elif not operator_ok:
        status, action = "POSITION_OPERATOR_BLOCKED", "BLOCKED"
        reasons.append("OPERATOR_STATE_BLOCKED")
    elif buy_status == "BLOCKED_BY_OPERATOR_STATE":
        status, action = "POSITION_OPERATOR_BLOCKED", "BLOCKED"
        reasons.append("BUYABILITY_OPERATOR_BLOCKED")
    elif buy_status == "BLOCKED_BY_DATA_QUALITY":
        status, action = "POSITION_DATA_QUALITY_BLOCKED", "BLOCKED"
        reasons.append("BUYABILITY_DATA_QUALITY_BLOCKED")
    elif buy_status in {"DO_NOT_BUY_NOW", "BLOCKED_BY_RISK"}:
        status, action = "POSITION_BLOCKED", "DO_NOT_POSITION"
        reasons.append(buy_status)
    elif buy_status == "WAIT_FOR_PULLBACK":
        status, action = "POSITION_WAIT_PULLBACK", "WAIT_FOR_PULLBACK"
        max_pct = 0.0
        reasons.append("WAIT_FOR_PULLBACK_NO_INITIAL_POSITION")
    elif buy_status == "WATCH_FOR_ENTRY":
        status, action = "POSITION_WATCH_ONLY", "WATCH_ONLY"
        max_pct = compute_pct(risk_budget, stop_pct, max_cap)
        reasons.append("WATCH_ONLY_THEORETICAL_FUTURE_CAP")
    elif buy_status == "REVIEW_FIRST":
        status, action = "POSITION_REVIEW_FIRST", "REVIEW_FIRST"
        max_pct = compute_pct(risk_budget, stop_pct, max_cap)
        reasons.append("REVIEW_FIRST_THEORETICAL_FUTURE_CAP")
    elif buy_status == "BUY_SMALL_ONLY":
        status, action = "POSITION_SMALL_ONLY", "SMALL_SIZE_ONLY"
        initial_pct = compute_pct(risk_budget, stop_pct, initial_cap)
        max_pct = compute_pct(risk_budget, stop_pct, max_cap)
        reasons.append("SMALL_SIZE_ONLY_POLICY")
    elif buy_status == "BUY_NOW_ALLOWED":
        if risk == "EXTREME_RISK":
            status, action = "POSITION_BLOCKED", "DO_NOT_POSITION"
            reasons.append("EXTREME_RISK_BLOCKS_NORMAL_POSITION")
        elif risk == "HIGH_RISK" and not (tier == "CORE_CANDIDATE" and technical_favorable(technical_status)):
            status, action = "POSITION_SMALL_ONLY", "SMALL_SIZE_ONLY"
            initial_pct = compute_pct(risk_budget, stop_pct, min(initial_cap, 1.5))
            max_pct = compute_pct(risk_budget, stop_pct, min(max_cap, 3.0))
            reasons.append("HIGH_RISK_DOWNGRADED_TO_SMALL_ONLY")
        else:
            status, action = "POSITION_ALLOWED", "ALLOW_INITIAL_POSITION"
            initial_pct = compute_pct(risk_budget, stop_pct, initial_cap)
            max_pct = compute_pct(risk_budget, stop_pct, max_cap)
            reasons.append("RISK_BUDGET_POSITION_ALLOWED")
    else:
        status, action = "POSITION_REVIEW_FIRST", "REVIEW_FIRST"
        reasons.append("UNKNOWN_BUYABILITY_STATUS")

    if tier in {"OVERHEATED_WAIT", "DO_NOT_PRIORITIZE", ""}:
        if buy_status not in {"WATCH_FOR_ENTRY", "REVIEW_FIRST"}:
            initial_pct = 0.0
            max_pct = 0.0
        if tier == "":
            status = "POSITION_DATA_QUALITY_BLOCKED" if missing else "POSITION_REVIEW_FIRST"
            action = "BLOCKED" if missing else "REVIEW_FIRST"
            reasons.append("UNKNOWN_TIER")

    initial_notional = account_size * initial_pct / 100.0
    max_notional = account_size * max_pct / 100.0
    max_loss = max_notional * abs(stop_pct) / 100.0 if stop_pct else 0.0
    below_min = initial_notional > 0 and initial_notional < MIN_EFFECTIVE_TRADE_NOTIONAL_USD
    if below_min:
        reasons.append("BELOW_MIN_EFFECTIVE_TRADE_NOTIONAL")
        if status == "POSITION_ALLOWED":
            status, action = "POSITION_REVIEW_FIRST", "REVIEW_FIRST"
        elif status == "POSITION_SMALL_ONLY":
            action = "SMALL_SIZE_ONLY"

    theme = upper(row.get("primary_theme"))
    concentration_caution = ""
    if theme in concentration:
        concentration_caution = f"STATIC_THEME_CONCENTRATION_CAUTION_{theme}_TOP50_COUNT_{concentration[theme]}"

    formula = "min(tier_max_position_pct, risk_budget_pct_of_account / abs(stop_review_pct) * 100)"
    reasons = list(dict.fromkeys(risk_reasons + reasons))
    return {
        "ticker": ticker,
        "rank": row.get("rank", ""),
        "composite_candidate_score": row.get("composite_candidate_score", ""),
        "primary_theme": row.get("primary_theme", ""),
        "recommendation_tier": tier,
        "buy_now_status": buy_status,
        "buy_now_score": row.get("buy_now_score", ""),
        "manual_operator_action": row.get("manual_operator_action", ""),
        "risk_bucket": risk,
        "technical_timing_status": technical_status,
        "overheat_flag": row.get("overheat_flag", ""),
        "position_policy_status": status,
        "position_policy_action": action,
        "risk_budget_pct_of_account": pct(risk_budget),
        "stop_review_pct": pct(stop_pct),
        "take_profit_review_pct": pct(take_profit_pct),
        "suggested_initial_position_pct": pct(initial_pct),
        "suggested_max_position_pct": pct(max_pct),
        "suggested_initial_notional_usd": money(initial_notional),
        "suggested_max_notional_usd": money(max_notional),
        "max_loss_usd_at_stop": money(max_loss),
        "min_effective_trade_notional_usd": money(MIN_EFFECTIVE_TRADE_NOTIONAL_USD),
        "below_min_effective_trade_flag": bool_text(below_min),
        "concentration_caution": concentration_caution,
        "position_size_reason": ";".join(reasons),
        "sizing_formula": formula,
        "account_size_usd": money(account_size),
        "cash_reserve_pct": pct(cash_reserve_pct),
        "max_active_positions": max_active,
        "max_speculative_positions": max_speculative,
        "source_buyability_file": source_file,
        "generated_at": generated_at,
        "run_id": run_id,
    }


def status_counts(rows: Sequence[Dict[str, object]]) -> Counter:
    return Counter(norm(row.get("position_policy_status")) for row in rows)


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
    if to_int(values.get("OUTPUT_POSITION_POLICY_ROWS")) not in (0, EXPECTED_ROWS):
        fails += 1
    for field in ["CURRENT_RANKED_CANDIDATE_ROWS", "CURRENT_RECOMMENDATION_ROWS", "CURRENT_THEME_CLASSIFICATION_ROWS"]:
        if to_int(values.get(field)) not in (0, EXPECTED_ROWS):
            fails += 1
    latest_freeze = to_int(values.get("LATEST_FULL_FREEZE_TICKER_COUNT"))
    if latest_freeze not in (0, EXPECTED_ROWS):
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


def policy_table() -> List[Dict[str, object]]:
    rows = []
    for tier, values in POLICY.items():
        risk_budget, stop_pct, take_profit, initial_cap, max_cap = values
        rows.append(
            {
                "recommendation_tier": tier,
                "risk_budget_pct": pct(risk_budget),
                "stop_review_pct": pct(stop_pct),
                "take_profit_review_pct": pct(take_profit),
                "initial_cap_pct": pct(initial_cap),
                "max_cap_pct": pct(max_cap),
            }
        )
    return rows


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    counts = [{"position_policy_status": key, "count": count} for key, count in status_counts(rows).most_common()]
    fields = ["rank", "ticker", "recommendation_tier", "risk_bucket", "suggested_initial_position_pct", "suggested_initial_notional_usd", "suggested_max_position_pct", "position_size_reason"]
    watch_wait = [row for row in rows if row.get("position_policy_status") in {"POSITION_WATCH_ONLY", "POSITION_WAIT_PULLBACK"}]
    warnings = []
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        warnings.append("FORWARD_RETURN_NOT_READY_STATIC_POLICY_ONLY")
    if values.get("STATUS", "").startswith("WARN_"):
        warnings.append("R30A_R30E_OR_R31A_WARN_REVIEW_NEEDED")
    if not warnings:
        warnings.append("NONE")
    return "\n".join(
        [
            "# V18 Current Position Sizing Policy",
            "",
            f"STATUS: {values.get('STATUS', '')}",
            f"RUN_ID: {values.get('RUN_ID', '')}",
            f"GENERATED_AT: {values.get('_GENERATED_AT', '')}",
            "",
            "## Account-Size Assumptions",
            f"- Account size USD: `{values.get('ACCOUNT_SIZE_USD', '')}`",
            f"- Cash reserve pct: `{values.get('CASH_RESERVE_PCT', '')}`",
            f"- Max active positions: `{values.get('MAX_ACTIVE_POSITIONS', '')}`",
            f"- Max speculative positions: `{values.get('MAX_SPECULATIVE_POSITIONS', '')}`",
            "",
            "## Position Status Counts",
            md_table(counts, ["position_policy_status", "count"], 20),
            "## Top POSITION_ALLOWED",
            md_table([row for row in rows if row.get("position_policy_status") == "POSITION_ALLOWED"], fields, 25),
            "## Top POSITION_SMALL_ONLY",
            md_table([row for row in rows if row.get("position_policy_status") == "POSITION_SMALL_ONLY"], fields, 25),
            "## WATCH_ONLY / WAIT_PULLBACK Summary",
            md_table(watch_wait, ["rank", "ticker", "position_policy_status", "recommendation_tier", "risk_bucket", "suggested_max_position_pct", "position_size_reason"], 40),
            "## Risk Budget Policy Table",
            md_table(policy_table(), ["recommendation_tier", "risk_budget_pct", "stop_review_pct", "take_profit_review_pct", "initial_cap_pct", "max_cap_pct"], 20),
            "## Safety",
            "- Manual research guidance only.",
            "- No broker connection.",
            "- No order placement.",
            "- Does not override operator judgment.",
            "- `AUTO_TRADE: DISABLED`",
            "- `AUTO_SELL: DISABLED`",
            "- `OFFICIAL_DECISION_IMPACT: NONE`",
            "",
            "## Warnings",
            "\n".join(f"- `{warning}`" for warning in warnings),
            "",
            "## Next Step Recommendation",
            "- R31C Moomoo cost/slippage model.",
            "- R31D account-aware manual plan later.",
        ]
    ) + "\n"


def build_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [
        {
            "run_id": values.get("RUN_ID", ""),
            "status": values.get("STATUS", ""),
            "mode": values.get("MODE", ""),
            "generated_at": values.get("_GENERATED_AT", ""),
            "account_size_usd": values.get("ACCOUNT_SIZE_USD", ""),
            "source_buyability_rows": values.get("SOURCE_BUYABILITY_ROWS", ""),
            "source_recommendation_rows": values.get("SOURCE_RECOMMENDATION_ROWS", ""),
            "source_ranked_candidate_rows": values.get("SOURCE_RANKED_CANDIDATE_ROWS", ""),
            "output_rows": values.get("OUTPUT_POSITION_POLICY_ROWS", ""),
            "position_allowed_count": values.get("POSITION_ALLOWED_COUNT", ""),
            "position_small_only_count": values.get("POSITION_SMALL_ONLY_COUNT", ""),
            "position_watch_only_count": values.get("POSITION_WATCH_ONLY_COUNT", ""),
            "position_wait_pullback_count": values.get("POSITION_WAIT_PULLBACK_COUNT", ""),
            "position_review_first_count": values.get("POSITION_REVIEW_FIRST_COUNT", ""),
            "position_blocked_count": values.get("POSITION_BLOCKED_COUNT", ""),
            "operator_blocked_count": values.get("POSITION_OPERATOR_BLOCKED_COUNT", ""),
            "data_quality_blocked_count": values.get("POSITION_DATA_QUALITY_BLOCKED_COUNT", ""),
            "total_initial_notional_usd_if_all_allowed": values.get("TOTAL_INITIAL_NOTIONAL_USD_IF_ALL_ALLOWED", ""),
            "total_initial_position_pct_if_all_allowed": values.get("TOTAL_INITIAL_POSITION_PCT_IF_ALL_ALLOWED", ""),
            "total_max_notional_usd_policy_cap": values.get("TOTAL_MAX_NOTIONAL_USD_POLICY_CAP", ""),
            "total_max_position_pct_policy_cap": values.get("TOTAL_MAX_POSITION_PCT_POLICY_CAP", ""),
            "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
            "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
            "notes": notes,
        }
    ]


def write_outputs(root: Path, values: Dict[str, object], rows: Sequence[Dict[str, object]], dry_run: bool, notes: str) -> None:
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    if not dry_run:
        write_csv(root / OUT_POLICY, rows, OUTPUT_FIELDS)
    report = build_report(values, rows)
    write_text(root / OUT_CURRENT_REPORT, report)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, notes), SUMMARY_FIELDS)


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31B_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    before = protected_sig(root)

    buy_rows, _buy_fields = read_csv(root / BUYABILITY)
    rec_rows, _rec_fields = read_csv(root / RECOMMENDATIONS)
    ranked_rows, _ranked_fields = read_csv(root / RANKED)
    theme_rows, _theme_fields = read_csv(root / THEMES)
    required_missing = [rel for rel in [BUYABILITY, RECOMMENDATIONS, RANKED] if not (root / rel).exists()]
    context = operator_context(root, len(buy_rows), len(rec_rows), len(ranked_rows), len(theme_rows))
    operator_ok = bool(context["structural_ok"])
    concentration = theme_concentration(buy_rows)
    source_file = str(root / BUYABILITY)

    output_rows: List[Dict[str, object]] = []
    if not required_missing:
        for row in buy_rows[: max(args.top_n, 0)]:
            output_rows.append(
                classify_position(
                    row=row,
                    operator_ok=operator_ok,
                    account_size=float(args.account_size_usd),
                    cash_reserve_pct=float(args.cash_reserve_pct),
                    max_active=int(args.max_active_positions),
                    max_speculative=int(args.max_speculative_positions),
                    concentration=concentration,
                    run_id=run_id,
                    generated_at=generated_at,
                    source_file=source_file,
                )
            )

    counts = status_counts(output_rows)
    total_initial_notional = sum(to_float(row.get("suggested_initial_notional_usd")) for row in output_rows)
    total_initial_pct = sum(to_float(row.get("suggested_initial_position_pct")) for row in output_rows)
    total_max_notional = sum(to_float(row.get("suggested_max_notional_usd")) for row in output_rows)
    total_max_pct = sum(to_float(row.get("suggested_max_position_pct")) for row in output_rows)

    values: Dict[str, object] = {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "ACCOUNT_SIZE_USD": money(float(args.account_size_usd)),
        "CASH_RESERVE_PCT": pct(float(args.cash_reserve_pct)),
        "MAX_ACTIVE_POSITIONS": args.max_active_positions,
        "MAX_SPECULATIVE_POSITIONS": args.max_speculative_positions,
        "SOURCE_BUYABILITY_FILE": source_file,
        "SOURCE_BUYABILITY_ROWS": len(buy_rows),
        "SOURCE_RECOMMENDATION_FILE": str(root / RECOMMENDATIONS),
        "SOURCE_RECOMMENDATION_ROWS": len(rec_rows),
        "SOURCE_RANKED_CANDIDATE_FILE": str(root / RANKED),
        "SOURCE_RANKED_CANDIDATE_ROWS": len(ranked_rows),
        "OUTPUT_POSITION_POLICY_ROWS": len(output_rows) if not args.dry_run else 0,
        "POSITION_ALLOWED_COUNT": counts.get("POSITION_ALLOWED", 0),
        "POSITION_SMALL_ONLY_COUNT": counts.get("POSITION_SMALL_ONLY", 0),
        "POSITION_WATCH_ONLY_COUNT": counts.get("POSITION_WATCH_ONLY", 0),
        "POSITION_WAIT_PULLBACK_COUNT": counts.get("POSITION_WAIT_PULLBACK", 0),
        "POSITION_REVIEW_FIRST_COUNT": counts.get("POSITION_REVIEW_FIRST", 0),
        "POSITION_BLOCKED_COUNT": counts.get("POSITION_BLOCKED", 0),
        "POSITION_OPERATOR_BLOCKED_COUNT": counts.get("POSITION_OPERATOR_BLOCKED", 0),
        "POSITION_DATA_QUALITY_BLOCKED_COUNT": counts.get("POSITION_DATA_QUALITY_BLOCKED", 0),
        "TOTAL_INITIAL_NOTIONAL_USD_IF_ALL_ALLOWED": money(total_initial_notional),
        "TOTAL_INITIAL_POSITION_PCT_IF_ALL_ALLOWED": pct(total_initial_pct),
        "TOTAL_MAX_NOTIONAL_USD_POLICY_CAP": money(total_max_notional),
        "TOTAL_MAX_POSITION_PCT_POLICY_CAP": pct(total_max_pct),
        "CURRENT_RANKED_CANDIDATE_ROWS": context["current_ranked"],
        "CURRENT_RECOMMENDATION_ROWS": context["current_recs"],
        "CURRENT_THEME_CLASSIFICATION_ROWS": context["current_themes"],
        "LATEST_FULL_FREEZE_TICKER_COUNT": context["latest_freeze"],
        "R31A_STATUS": context["r31a_status"],
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
        values["NEXT_RECOMMENDED_STEP"] = "Restore required R31A/R28B inputs before generating position sizing policy."
    elif args.dry_run:
        notes = "Dry run only; current position sizing CSV not written."
        values["STATUS"] = STATUS_DRY
        values["NEXT_RECOMMENDED_STEP"] = "Run live R31B to generate current position sizing policy."
    elif len(buy_rows) != EXPECTED_ROWS or len(rec_rows) != EXPECTED_ROWS or len(ranked_rows) != EXPECTED_ROWS or len(output_rows) != args.top_n:
        notes = "Structural row count mismatch."
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Run R31A/R30E and inspect structural inputs before using position sizing policy."
    elif not operator_ok:
        notes = "Operator state blocked all rows."
        values["STATUS"] = STATUS_FAIL if args.strict else STATUS_WARN
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31A/R30E/R30A operator state before manual position review."
    elif context["warn_only"]:
        notes = "FORWARD_RETURN_NOT_READY_STATIC_POLICY_ONLY"
        values["STATUS"] = STATUS_WARN
        values["NEXT_RECOMMENDED_STEP"] = "Static policy only; do not treat this as account-aware execution guidance."
    else:
        notes = "Manual position sizing policy ready."
        values["STATUS"] = STATUS_OK
        values["NEXT_RECOMMENDED_STEP"] = "Review V18_CURRENT_POSITION_SIZING_POLICY.md; next planned layer is R31C cost/slippage."

    after = protected_sig(root)
    values["FORBIDDEN_MODIFIED"] = bool_text(after != before)
    if values["FORBIDDEN_MODIFIED"] != "FALSE":
        values["STATUS"] = STATUS_FAIL
        notes = "Forbidden input modification detected."
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31B error report; do not trade from this run."

    write_outputs(root, values, output_rows, args.dry_run, notes)
    if values["STATUS"] == STATUS_FAIL:
        write_text(root / OUT_ERROR_REPORT, f"# V18.31B Manual Position Sizing Policy Error\n\n```text\n{notes}\n```\n")
        return 1, values
    return 0, values


def write_failure(root: Path, error: BaseException, args: argparse.Namespace) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31B_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "ACCOUNT_SIZE_USD": money(float(args.account_size_usd)),
        "CASH_RESERVE_PCT": pct(float(args.cash_reserve_pct)),
        "MAX_ACTIVE_POSITIONS": args.max_active_positions,
        "MAX_SPECULATIVE_POSITIONS": args.max_speculative_positions,
        "SOURCE_BUYABILITY_FILE": str(root / BUYABILITY),
        "SOURCE_BUYABILITY_ROWS": 0,
        "SOURCE_RECOMMENDATION_FILE": str(root / RECOMMENDATIONS),
        "SOURCE_RECOMMENDATION_ROWS": 0,
        "SOURCE_RANKED_CANDIDATE_FILE": str(root / RANKED),
        "SOURCE_RANKED_CANDIDATE_ROWS": 0,
        "OUTPUT_POSITION_POLICY_ROWS": 0,
        "POSITION_ALLOWED_COUNT": 0,
        "POSITION_SMALL_ONLY_COUNT": 0,
        "POSITION_WATCH_ONLY_COUNT": 0,
        "POSITION_WAIT_PULLBACK_COUNT": 0,
        "POSITION_REVIEW_FIRST_COUNT": 0,
        "POSITION_BLOCKED_COUNT": 0,
        "POSITION_OPERATOR_BLOCKED_COUNT": 0,
        "POSITION_DATA_QUALITY_BLOCKED_COUNT": 0,
        "TOTAL_INITIAL_NOTIONAL_USD_IF_ALL_ALLOWED": "0.00",
        "TOTAL_INITIAL_POSITION_PCT_IF_ALL_ALLOWED": "0.00",
        "TOTAL_MAX_NOTIONAL_USD_POLICY_CAP": "0.00",
        "TOTAL_MAX_POSITION_PCT_POLICY_CAP": "0.00",
        "CURRENT_RANKED_CANDIDATE_ROWS": 0,
        "CURRENT_RECOMMENDATION_ROWS": 0,
        "CURRENT_THEME_CLASSIFICATION_ROWS": 0,
        "LATEST_FULL_FREEZE_TICKER_COUNT": 0,
        "R31A_STATUS": "",
        "R30E_STATUS": "",
        "R30A_STATUS": "",
        "FORWARD_RETURN_FILLABLE_READY": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 1,
        "FORBIDDEN_MODIFIED": "UNKNOWN",
        "NEXT_RECOMMENDED_STEP": "Inspect R31B error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    }
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, str(error)), SUMMARY_FIELDS)
    write_text(root / OUT_ERROR_REPORT, f"# V18.31B Manual Position Sizing Policy Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31B manual position sizing policy layer.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--account-size-usd", type=float, default=2000.0)
    parser.add_argument("--cash-reserve-pct", type=float, default=15.0)
    parser.add_argument("--max-active-positions", type=int, default=8)
    parser.add_argument("--max-speculative-positions", type=int, default=2)
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
