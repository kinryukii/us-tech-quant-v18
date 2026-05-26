from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRY = "OK_V18_31C_MOOMOO_COST_SLIPPAGE_DRY_RUN_READY"
STATUS_OK = "OK_V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_READY"
STATUS_WARN = "WARN_V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_FAILED"
STATUS_R1_DRY = "OK_V18_31C_R1_COST_PLAN_READABILITY_PATCH_DRY_RUN_READY"
STATUS_R1_OK = "OK_V18_31C_R1_COST_PLAN_READABILITY_PATCH_READY"
STATUS_R1_WARN = "WARN_V18_31C_R1_COST_PLAN_READABILITY_PATCH_REVIEW_NEEDED"
STATUS_R1_FAIL = "FAIL_V18_31C_R1_COST_PLAN_READABILITY_PATCH_FAILED"
MODE_LIVE = "MOOMOO_COST_SLIPPAGE_CONSTRAINT_LAYER"
MODE_DRY = "MOOMOO_COST_SLIPPAGE_CONSTRAINT_DRY_RUN"
EXPECTED_ROWS = 252

POSITION_POLICY = "outputs/v18/execution/V18_CURRENT_POSITION_SIZING_POLICY.csv"
BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
R31B_READ_FIRST = "outputs/v18/ops/V18_31B_READ_FIRST.txt"
R31A_READ_FIRST = "outputs/v18/ops/V18_31A_READ_FIRST.txt"
R30E_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"

OUT_PLAN = "outputs/v18/execution/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.csv"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.md"
OUT_REPORT = "outputs/v18/read_center/V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_31C_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31C_COST_SLIPPAGE_CONSTRAINT_SUMMARY.csv"
OUT_PATCH_REPORT = "outputs/v18/read_center/V18_31C_R1_COST_PLAN_READABILITY_PATCH_REPORT.md"
OUT_PATCH_READ_FIRST = "outputs/v18/ops/V18_31C_R1_READ_FIRST.txt"
OUT_PATCH_SUMMARY = "outputs/v18/ops/V18_31C_R1_COST_PLAN_READABILITY_PATCH_SUMMARY.csv"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_31C_MOOMOO_COST_SLIPPAGE_CONSTRAINT_ERROR.md"

FEE_NOTE = "Moomoo fee assumptions are configurable and must be verified against the current broker fee schedule before live trading."

OUTPUT_FIELDS = [
    "ticker",
    "rank",
    "composite_candidate_score",
    "primary_theme",
    "recommendation_tier",
    "buy_now_status",
    "position_policy_status",
    "position_policy_action",
    "risk_bucket",
    "technical_timing_status",
    "overheat_flag",
    "suggested_initial_position_pct",
    "suggested_max_position_pct",
    "suggested_initial_notional_usd",
    "suggested_max_notional_usd",
    "broker_profile",
    "commission_rate_pct",
    "estimated_buy_commission_usd",
    "estimated_sell_commission_usd",
    "estimated_roundtrip_commission_usd",
    "estimated_roundtrip_commission_pct_of_initial_notional",
    "estimated_slippage_bps_one_way",
    "estimated_roundtrip_slippage_pct",
    "estimated_roundtrip_slippage_usd",
    "estimated_spread_bps_one_way",
    "estimated_roundtrip_spread_pct",
    "estimated_roundtrip_spread_usd",
    "estimated_fx_fee_usd",
    "estimated_total_roundtrip_cost_usd",
    "estimated_total_roundtrip_cost_pct",
    "minimum_required_expected_return_pct",
    "cost_adjusted_trade_status",
    "cost_adjusted_trade_action",
    "cost_review_substatus",
    "current_trade_candidate_flag",
    "no_current_trade_reason",
    "operator_readability_bucket",
    "cost_gate_result",
    "cost_block_reason",
    "below_min_effective_trade_flag",
    "minimum_effective_trade_notional_usd",
    "cost_model_reason",
    "fee_assumption_note",
    "source_position_policy_file",
    "generated_at",
    "run_id",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "TOP_N_REQUESTED",
    "BROKER_PROFILE",
    "COMMISSION_RATE_PCT",
    "COMMISSION_MIN_USD",
    "COMMISSION_CAP_USD",
    "FX_FEE_JPY_PER_USD",
    "CONSERVATIVE_FX_FEE_JPY_PER_USD",
    "MIN_EFFECTIVE_TRADE_NOTIONAL_USD",
    "COST_SAFETY_MULTIPLE",
    "SOURCE_POSITION_POLICY_FILE",
    "SOURCE_POSITION_POLICY_ROWS",
    "SOURCE_BUYABILITY_FILE",
    "SOURCE_BUYABILITY_ROWS",
    "OUTPUT_COST_ADJUSTED_ROWS",
    "COST_OK_COUNT",
    "COST_OK_SMALL_ONLY_COUNT",
    "COST_REVIEW_REQUIRED_COUNT",
    "COST_WATCH_ONLY_COUNT",
    "COST_WAIT_PULLBACK_COUNT",
    "BLOCKED_BY_COST_COUNT",
    "BLOCKED_BY_MIN_NOTIONAL_COUNT",
    "BLOCKED_BY_POSITION_POLICY_COUNT",
    "BLOCKED_BY_OPERATOR_STATE_COUNT",
    "BLOCKED_BY_DATA_QUALITY_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "R31B_STATUS",
    "R31A_STATUS",
    "R30E_STATUS",
    "R30A_STATUS",
    "FORWARD_RETURN_FILLABLE_READY",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "CURRENT_COST_OK_CANDIDATE_COUNT",
    "CURRENT_SMALL_ONLY_COST_OK_COUNT",
    "CURRENT_BLOCKED_MIN_NOTIONAL_COUNT",
    "REVIEW_FIRST_NO_CURRENT_TRADE_COUNT",
    "WATCH_ONLY_NO_CURRENT_TRADE_COUNT",
    "WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT",
    "TRUE_COST_REVIEW_REQUIRED_COUNT",
    "OPERATOR_READABILITY_PATCH_APPLIED",
    "R31C_R1_STATUS",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "mode",
    "generated_at",
    "broker_profile",
    "commission_rate_pct",
    "min_effective_trade_notional_usd",
    "source_position_policy_rows",
    "source_buyability_rows",
    "output_rows",
    "cost_ok_count",
    "cost_ok_small_only_count",
    "cost_review_required_count",
    "cost_watch_only_count",
    "cost_wait_pullback_count",
    "blocked_by_cost_count",
    "blocked_by_min_notional_count",
    "blocked_by_position_policy_count",
    "operator_blocked_count",
    "data_quality_blocked_count",
    "current_cost_ok_candidate_count",
    "current_small_only_cost_ok_count",
    "current_blocked_min_notional_count",
    "review_first_no_current_trade_count",
    "watch_only_no_current_trade_count",
    "wait_pullback_no_current_trade_count",
    "true_cost_review_required_count",
    "operator_readability_patch_applied",
    "r31c_r1_status",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

PATCH_READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "SOURCE_R31C_ROWS",
    "OUTPUT_COST_ADJUSTED_ROWS",
    "CURRENT_COST_OK_CANDIDATE_COUNT",
    "CURRENT_SMALL_ONLY_COST_OK_COUNT",
    "CURRENT_BLOCKED_MIN_NOTIONAL_COUNT",
    "REVIEW_FIRST_NO_CURRENT_TRADE_COUNT",
    "WATCH_ONLY_NO_CURRENT_TRADE_COUNT",
    "WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT",
    "TRUE_COST_REVIEW_REQUIRED_COUNT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

PATCH_SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "source_rows",
    "output_rows",
    "current_cost_ok_candidate_count",
    "current_small_only_cost_ok_count",
    "current_blocked_min_notional_count",
    "review_first_no_current_trade_count",
    "watch_only_no_current_trade_count",
    "wait_pullback_no_current_trade_count",
    "true_cost_review_required_count",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

PROTECTED_INPUTS = [
    POSITION_POLICY,
    BUYABILITY,
    RECOMMENDATIONS,
    RANKED,
    THEMES,
    TECHNICAL,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv",
]

RETURN_FLOORS = {
    "CORE_CANDIDATE": 1.50,
    "WATCHLIST_STRONG": 1.50,
    "TACTICAL_ENTRY": 2.00,
    "SPECULATIVE_SATELLITE": 3.00,
    "DEFENSIVE_HEDGE": 1.25,
    "ETF_OR_MACRO_EXPOSURE": 1.25,
    "OVERHEATED_WAIT": 999.00,
    "DO_NOT_PRIORITIZE": 999.00,
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
    return f"{value:.4f}"


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


def risk_class(value: object) -> str:
    text = upper(value)
    if "EXTREME" in text:
        return "EXTREME_RISK"
    if "HIGH" in text:
        return "HIGH_RISK"
    if "LOW" in text:
        return "LOW_RISK"
    if "DEFENSIVE" in text:
        return "DEFENSIVE_RISK"
    if "MEDIUM" in text:
        return "MEDIUM_RISK"
    return text or "UNKNOWN_RISK"


def operator_context(root: Path, pos_rows: int, buy_rows: int, rec_rows: int, ranked_rows: int, theme_rows: int) -> Dict[str, object]:
    r31b = read_status_file(root / R31B_READ_FIRST)
    r31a = read_status_file(root / R31A_READ_FIRST)
    r30e = read_status_file(root / R30E_READ_FIRST)
    r30a = read_status_file(root / R30A_READ_FIRST)
    current_ranked = to_int(r31b.get("CURRENT_RANKED_CANDIDATE_ROWS") or r31a.get("CURRENT_RANKED_CANDIDATE_ROWS") or r30e.get("CURRENT_RANKED_CANDIDATE_ROWS"), ranked_rows)
    current_recs = to_int(r31b.get("CURRENT_RECOMMENDATION_ROWS") or r31a.get("CURRENT_RECOMMENDATION_ROWS") or r30e.get("CURRENT_RECOMMENDATION_ROWS"), rec_rows)
    current_themes = to_int(r31b.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r31a.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r30e.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r30a.get("THEME_CLASSIFICATION_ROW_COUNT"), theme_rows)
    latest_freeze = to_int(r31b.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r31a.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r30e.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT"), 0)
    r31a_rows = to_int(r31a.get("OUTPUT_BUYABILITY_ROWS"), buy_rows)
    r31b_rows = to_int(r31b.get("OUTPUT_POSITION_POLICY_ROWS"), pos_rows)
    auto_trade = r31b.get("AUTO_TRADE") or r31a.get("AUTO_TRADE") or r30e.get("AUTO_TRADE") or r30a.get("AUTO_TRADE") or "DISABLED"
    auto_sell = r31b.get("AUTO_SELL") or r31a.get("AUTO_SELL") or r30e.get("AUTO_SELL") or r30a.get("AUTO_SELL") or "DISABLED"
    impact = r31b.get("OFFICIAL_DECISION_IMPACT") or r31a.get("OFFICIAL_DECISION_IMPACT") or r30e.get("OFFICIAL_DECISION_IMPACT") or r30a.get("OFFICIAL_DECISION_IMPACT") or "NONE"
    forward_ready = (r31b.get("FORWARD_RETURN_FILLABLE_READY") == "TRUE") or (r31a.get("FORWARD_RETURN_FILLABLE_READY") == "TRUE") or any(
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
        pos_rows == EXPECTED_ROWS
        and buy_rows == EXPECTED_ROWS
        and r31a_rows == EXPECTED_ROWS
        and r31b_rows == EXPECTED_ROWS
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
            r31b.get("STATUS", "").startswith("WARN_")
            or r31a.get("STATUS", "").startswith("WARN_")
            or r30e.get("STATUS", "").startswith("WARN_")
            or r30a.get("STATUS", "").startswith("WARN_")
        )
    )
    result = {
        "r31b_status": r31b.get("STATUS", ""),
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
    return result


def commission(notional: float, rate_pct: float, min_usd: float, cap_usd: float) -> float:
    if notional <= 0:
        return 0.0
    value = notional * rate_pct / 100.0
    if min_usd > 0:
        value = max(value, min_usd)
    if cap_usd > 0:
        value = min(value, cap_usd)
    return value


def slippage_bps(risk: str, tier: str) -> float:
    risk = risk_class(risk)
    base = {
        "LOW_RISK": 5.0,
        "DEFENSIVE_RISK": 5.0,
        "MEDIUM_RISK": 10.0,
        "HIGH_RISK": 25.0,
        "EXTREME_RISK": 50.0,
    }.get(risk, 20.0)
    tier = upper(tier)
    add = 0.0
    if tier == "SPECULATIVE_SATELLITE":
        add = 15.0
    elif tier == "TACTICAL_ENTRY":
        add = 5.0
    elif tier in {"DO_NOT_PRIORITIZE", "OVERHEATED_WAIT"}:
        add = 20.0
    return base + add


def spread_bps(risk: str) -> float:
    risk = risk_class(risk)
    result = {
        "LOW_RISK": 3.0,
        "DEFENSIVE_RISK": 3.0,
        "MEDIUM_RISK": 5.0,
        "HIGH_RISK": 12.0,
        "EXTREME_RISK": 25.0,
    }.get(risk, 10.0)
    return result


def return_floor(tier: str) -> float:
    return RETURN_FLOORS.get(upper(tier), 999.0)


def classify_cost(row: Dict[str, str], operator_ok: bool, args: argparse.Namespace, run_id: str, generated_at: str, source_file: str) -> Dict[str, object]:
    tier = upper(row.get("recommendation_tier"))
    pos_status = upper(row.get("position_policy_status"))
    risk = risk_class(row.get("risk_bucket"))
    initial = to_float(row.get("suggested_initial_notional_usd"))
    buy_comm = commission(initial, args.commission_rate_pct, args.commission_min_usd, args.commission_cap_usd)
    sell_comm = commission(initial, args.commission_rate_pct, args.commission_min_usd, args.commission_cap_usd)
    roundtrip_comm = buy_comm + sell_comm
    roundtrip_comm_pct = (roundtrip_comm / initial * 100.0) if initial > 0 else 0.0
    slip_bps = slippage_bps(risk, tier)
    slip_pct = slip_bps * 2.0 / 100.0
    slip_usd = initial * slip_pct / 100.0
    spr_bps = spread_bps(risk)
    spr_pct = spr_bps * 2.0 / 100.0
    spr_usd = initial * spr_pct / 100.0
    fx_usd = 0.0
    total_cost = roundtrip_comm + slip_usd + spr_usd + fx_usd
    total_cost_pct = total_cost / initial * 100.0 if initial > 0 else 0.0
    min_required_return = max(total_cost_pct * args.cost_safety_multiple, return_floor(tier))
    below_min = initial > 0 and initial < args.min_effective_trade_notional_usd
    reasons: List[str] = []

    if not operator_ok or pos_status == "POSITION_OPERATOR_BLOCKED":
        status, action = "BLOCKED_BY_OPERATOR_STATE", "BLOCKED"
        reasons.append("OPERATOR_STATE_BLOCKED")
    elif pos_status == "POSITION_DATA_QUALITY_BLOCKED":
        status, action = "BLOCKED_BY_DATA_QUALITY", "BLOCKED"
        reasons.append("POSITION_DATA_QUALITY_BLOCKED")
    elif pos_status == "POSITION_BLOCKED":
        status, action = "BLOCKED_BY_POSITION_POLICY", "BLOCKED"
        reasons.append("POSITION_POLICY_BLOCKED")
    elif pos_status == "POSITION_WAIT_PULLBACK":
        status, action = "COST_WAIT_PULLBACK", "WAIT_FOR_PULLBACK"
        reasons.append("POSITION_WAIT_PULLBACK_NO_CURRENT_TRADE")
    elif pos_status == "POSITION_WATCH_ONLY":
        status, action = "COST_WATCH_ONLY", "WATCH_ONLY"
        reasons.append("POSITION_WATCH_ONLY_NO_CURRENT_TRADE")
    elif pos_status == "POSITION_REVIEW_FIRST":
        status, action = "COST_REVIEW_REQUIRED", "REVIEW_COST_BEFORE_TRADE"
        reasons.append("POSITION_REVIEW_FIRST_NO_CURRENT_TRADE")
    elif initial <= 0:
        status, action = "BLOCKED_BY_POSITION_POLICY", "BLOCKED"
        reasons.append("ZERO_INITIAL_NOTIONAL")
    elif below_min:
        status, action = "BLOCKED_BY_MIN_NOTIONAL", "DO_NOT_TRADE_MIN_NOTIONAL"
        reasons.append("BELOW_MIN_EFFECTIVE_TRADE_NOTIONAL")
    elif total_cost_pct > 3.0:
        status, action = "BLOCKED_BY_COST", "DO_NOT_TRADE_COST_TOO_HIGH"
        reasons.append("TOTAL_ROUNDTRIP_COST_GT_3PCT")
    elif total_cost_pct > 1.5 or (tier == "SPECULATIVE_SATELLITE" and total_cost_pct > 1.0):
        status, action = "COST_REVIEW_REQUIRED", "REVIEW_COST_BEFORE_TRADE"
        reasons.append("TOTAL_ROUNDTRIP_COST_REVIEW_THRESHOLD")
    elif pos_status == "POSITION_SMALL_ONLY":
        status, action = "COST_OK_SMALL_ONLY", "ALLOW_SMALL_SIZE_ONLY_AFTER_COST"
        reasons.append("SMALL_ONLY_COST_ACCEPTABLE")
    elif pos_status == "POSITION_ALLOWED":
        status, action = "COST_OK", "ALLOW_COST_ADJUSTED_MANUAL_REVIEW"
        reasons.append("COST_ACCEPTABLE_FOR_MANUAL_REVIEW")
    else:
        status, action = "COST_REVIEW_REQUIRED", "REVIEW_COST_BEFORE_TRADE"
        reasons.append("UNKNOWN_POSITION_POLICY_STATUS")

    if total_cost_pct > 0:
        reasons.append(f"EST_TOTAL_COST_PCT_{total_cost_pct:.4f}")
    cost_gate = "PASS" if status in {"COST_OK", "COST_OK_SMALL_ONLY"} else ("CAUTION" if status in {"COST_REVIEW_REQUIRED", "COST_WATCH_ONLY", "COST_WAIT_PULLBACK"} else "BLOCK")
    result = {
        "ticker": upper(row.get("ticker")),
        "rank": row.get("rank", ""),
        "composite_candidate_score": row.get("composite_candidate_score", ""),
        "primary_theme": row.get("primary_theme", ""),
        "recommendation_tier": tier,
        "buy_now_status": row.get("buy_now_status", ""),
        "position_policy_status": pos_status,
        "position_policy_action": row.get("position_policy_action", ""),
        "risk_bucket": risk,
        "technical_timing_status": row.get("technical_timing_status", ""),
        "overheat_flag": row.get("overheat_flag", ""),
        "suggested_initial_position_pct": row.get("suggested_initial_position_pct", ""),
        "suggested_max_position_pct": row.get("suggested_max_position_pct", ""),
        "suggested_initial_notional_usd": row.get("suggested_initial_notional_usd", ""),
        "suggested_max_notional_usd": row.get("suggested_max_notional_usd", ""),
        "broker_profile": args.broker_profile,
        "commission_rate_pct": pct(args.commission_rate_pct),
        "estimated_buy_commission_usd": money(buy_comm),
        "estimated_sell_commission_usd": money(sell_comm),
        "estimated_roundtrip_commission_usd": money(roundtrip_comm),
        "estimated_roundtrip_commission_pct_of_initial_notional": pct(roundtrip_comm_pct),
        "estimated_slippage_bps_one_way": pct(slip_bps),
        "estimated_roundtrip_slippage_pct": pct(slip_pct),
        "estimated_roundtrip_slippage_usd": money(slip_usd),
        "estimated_spread_bps_one_way": pct(spr_bps),
        "estimated_roundtrip_spread_pct": pct(spr_pct),
        "estimated_roundtrip_spread_usd": money(spr_usd),
        "estimated_fx_fee_usd": money(fx_usd),
        "estimated_total_roundtrip_cost_usd": money(total_cost),
        "estimated_total_roundtrip_cost_pct": pct(total_cost_pct),
        "minimum_required_expected_return_pct": pct(min_required_return),
        "cost_adjusted_trade_status": status,
        "cost_adjusted_trade_action": action,
        "cost_review_substatus": "",
        "current_trade_candidate_flag": "",
        "no_current_trade_reason": "",
        "operator_readability_bucket": "",
        "cost_gate_result": cost_gate,
        "cost_block_reason": ";".join(dict.fromkeys(reasons)),
        "below_min_effective_trade_flag": bool_text(below_min),
        "minimum_effective_trade_notional_usd": money(args.min_effective_trade_notional_usd),
        "cost_model_reason": f"commission={roundtrip_comm:.4f};slippage_bps_one_way={slip_bps:.2f};spread_bps_one_way={spr_bps:.2f};base_fx_fee_usd=0",
        "fee_assumption_note": FEE_NOTE,
        "source_position_policy_file": source_file,
        "generated_at": generated_at,
        "run_id": run_id,
    }
    result["cost_review_substatus"] = cost_review_substatus(result)
    result["current_trade_candidate_flag"] = current_trade_candidate_flag(result)
    result["no_current_trade_reason"] = no_current_trade_reason(result)
    result["operator_readability_bucket"] = operator_readability_bucket(result)
    return result


def status_counts(rows: Sequence[Dict[str, object]]) -> Counter:
    return Counter(norm(row.get("cost_adjusted_trade_status")) for row in rows)


def readability_bucket_counts(rows: Sequence[Dict[str, object]]) -> Counter:
    return Counter(norm(row.get("operator_readability_bucket")) for row in rows)


def current_trade_candidate_flag(row: Dict[str, object]) -> str:
    status = upper(row.get("cost_adjusted_trade_status"))
    initial = to_float(row.get("suggested_initial_notional_usd"))
    return bool_text(status in {"COST_OK", "COST_OK_SMALL_ONLY"} and initial > 0)


def cost_review_substatus(row: Dict[str, object]) -> str:
    status = upper(row.get("cost_adjusted_trade_status"))
    initial = to_float(row.get("suggested_initial_notional_usd"))
    block_reason = upper(row.get("cost_block_reason"))
    if status in {"COST_OK", "COST_OK_SMALL_ONLY"}:
        return "COST_OK_CURRENT_TRADE"
    if status == "BLOCKED_BY_MIN_NOTIONAL":
        return "MIN_NOTIONAL_BLOCK"
    if status == "BLOCKED_BY_POSITION_POLICY":
        return "POSITION_POLICY_BLOCK"
    if status == "COST_WATCH_ONLY":
        return "WATCH_ONLY_NO_CURRENT_TRADE"
    if status == "COST_WAIT_PULLBACK":
        return "WAIT_PULLBACK_NO_CURRENT_TRADE"
    if status == "BLOCKED_BY_OPERATOR_STATE":
        return "OPERATOR_BLOCK"
    if status == "BLOCKED_BY_DATA_QUALITY":
        return "DATA_QUALITY_BLOCK"
    if status == "COST_REVIEW_REQUIRED":
        if initial <= 0 and "POSITION_REVIEW_FIRST_NO_CURRENT_TRADE" in block_reason:
            return "REVIEW_FIRST_NO_CURRENT_TRADE"
        if initial <= 0:
            return "REVIEW_FIRST_NO_CURRENT_TRADE"
        return "TRUE_COST_REVIEW"
    return "NOT_APPLICABLE"


def no_current_trade_reason(row: Dict[str, object]) -> str:
    status = upper(row.get("cost_adjusted_trade_status"))
    substatus = cost_review_substatus(row)
    if current_trade_candidate_flag(row) == "TRUE":
        return "NOT_APPLICABLE"
    if substatus == "REVIEW_FIRST_NO_CURRENT_TRADE":
        return "POSITION_REVIEW_FIRST_NO_CURRENT_TRADE"
    if substatus == "WATCH_ONLY_NO_CURRENT_TRADE":
        return "POSITION_WATCH_ONLY_NO_CURRENT_TRADE"
    if substatus == "WAIT_PULLBACK_NO_CURRENT_TRADE":
        return "POSITION_WAIT_PULLBACK_NO_CURRENT_TRADE"
    if substatus == "MIN_NOTIONAL_BLOCK":
        return "BELOW_MIN_EFFECTIVE_TRADE_NOTIONAL"
    if substatus == "POSITION_POLICY_BLOCK":
        return "POSITION_POLICY_BLOCKED"
    if substatus == "OPERATOR_BLOCK":
        return "OPERATOR_STATE_BLOCKED"
    if substatus == "DATA_QUALITY_BLOCK":
        return "POSITION_DATA_QUALITY_BLOCKED"
    if substatus == "TRUE_COST_REVIEW":
        return "TRUE_COST_REVIEW_REQUIRED"
    if status == "BLOCKED_BY_COST":
        return "TOTAL_ROUNDTRIP_COST_GT_3PCT"
    return "NOT_APPLICABLE"


def operator_readability_bucket(row: Dict[str, object]) -> str:
    status = upper(row.get("cost_adjusted_trade_status"))
    substatus = cost_review_substatus(row)
    if current_trade_candidate_flag(row) == "TRUE":
        if status == "COST_OK_SMALL_ONLY":
            return "CURRENT_SMALL_ONLY_COST_OK"
        return "CURRENT_COST_OK"
    if status == "BLOCKED_BY_MIN_NOTIONAL":
        return "CURRENT_BLOCKED_MIN_NOTIONAL"
    if substatus == "TRUE_COST_REVIEW":
        return "CURRENT_TRUE_COST_REVIEW"
    if substatus == "REVIEW_FIRST_NO_CURRENT_TRADE":
        return "REVIEW_FIRST_NOT_TRADE_NOW"
    if status == "COST_WATCH_ONLY":
        return "WATCH_ONLY_NOT_TRADE_NOW"
    if status == "COST_WAIT_PULLBACK":
        return "WAIT_PULLBACK_NOT_TRADE_NOW"
    if status in {"BLOCKED_BY_OPERATOR_STATE", "BLOCKED_BY_DATA_QUALITY"}:
        return "OPERATOR_OR_DATA_BLOCKED"
    return "BLOCKED_NOT_TRADE"


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
    if to_int(values.get("OUTPUT_COST_ADJUSTED_ROWS")) not in (0, EXPECTED_ROWS):
        fails += 1
    for field in ["CURRENT_RANKED_CANDIDATE_ROWS", "CURRENT_RECOMMENDATION_ROWS", "CURRENT_THEME_CLASSIFICATION_ROWS"]:
        if to_int(values.get(field)) not in (0, EXPECTED_ROWS):
            fails += 1
    latest_freeze = to_int(values.get("LATEST_FULL_FREEZE_TICKER_COUNT"))
    if latest_freeze not in (0, EXPECTED_ROWS):
        fails += 1
    return fails


def read_first_text(values: Dict[str, object], fields: Sequence[str] = READ_FIRST_FIELDS) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in fields) + "\n"


def md_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 25) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def assumption_rows(values: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        {"assumption": "broker_profile", "value": values.get("BROKER_PROFILE", "")},
        {"assumption": "commission_rate_pct", "value": values.get("COMMISSION_RATE_PCT", "")},
        {"assumption": "commission_min_usd", "value": values.get("COMMISSION_MIN_USD", "")},
        {"assumption": "commission_cap_usd", "value": values.get("COMMISSION_CAP_USD", "")},
        {"assumption": "fx_fee_jpy_per_usd", "value": values.get("FX_FEE_JPY_PER_USD", "")},
        {"assumption": "conservative_fx_fee_jpy_per_usd", "value": values.get("CONSERVATIVE_FX_FEE_JPY_PER_USD", "")},
        {"assumption": "min_effective_trade_notional_usd", "value": values.get("MIN_EFFECTIVE_TRADE_NOTIONAL_USD", "")},
        {"assumption": "cost_safety_multiple", "value": values.get("COST_SAFETY_MULTIPLE", "")},
    ]


def build_count_table(rows: Sequence[Dict[str, object]], field_name: str, field_order: Sequence[str]) -> List[Dict[str, object]]:
    counts = Counter(norm(row.get(field_name)) for row in rows)
    return [{field_name: field, "count": counts.get(field, 0)} for field in field_order]


def readability_rows(rows: Sequence[Dict[str, object]], statuses: Sequence[str] | None = None, substatuses: Sequence[str] | None = None, buckets: Sequence[str] | None = None) -> List[Dict[str, object]]:
    selected: List[Dict[str, object]] = []
    for row in rows:
        if statuses and upper(row.get("cost_adjusted_trade_status")) not in set(statuses):
            continue
        if substatuses and upper(row.get("cost_review_substatus")) not in set(substatuses):
            continue
        if buckets and upper(row.get("operator_readability_bucket")) not in set(buckets):
            continue
        selected.append(row)
    return selected


def report_section(rows: Sequence[Dict[str, object]], title: str, intro: str, fields: Sequence[str], limit: int = 25) -> List[str]:
    return [title, intro, md_table(rows, fields, limit)]


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]], title: str = "# V18 Current Cost-Adjusted Trade Plan") -> str:
    warnings = []
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        warnings.append("FORWARD_RETURN_NOT_READY_COST_MODEL_ONLY")
    if values.get("STATUS", "").startswith("WARN_"):
        warnings.append("R30A_R30E_R31A_OR_R31B_WARN_REVIEW_NEEDED")
    if not warnings:
        warnings.append("NONE")
    row_fields = [
        "rank",
        "ticker",
        "recommendation_tier",
        "risk_bucket",
        "suggested_initial_notional_usd",
        "estimated_total_roundtrip_cost_pct",
        "minimum_required_expected_return_pct",
        "cost_adjusted_trade_status",
        "cost_review_substatus",
        "current_trade_candidate_flag",
        "no_current_trade_reason",
        "operator_readability_bucket",
        "cost_block_reason",
    ]
    status_counts_rows = build_count_table(rows, "cost_adjusted_trade_status", [
        "COST_OK",
        "COST_OK_SMALL_ONLY",
        "COST_REVIEW_REQUIRED",
        "COST_WATCH_ONLY",
        "COST_WAIT_PULLBACK",
        "BLOCKED_BY_MIN_NOTIONAL",
        "BLOCKED_BY_POSITION_POLICY",
        "BLOCKED_BY_OPERATOR_STATE",
        "BLOCKED_BY_DATA_QUALITY",
        "BLOCKED_BY_COST",
    ])
    readability_counts_rows = build_count_table(rows, "operator_readability_bucket", [
        "CURRENT_COST_OK",
        "CURRENT_SMALL_ONLY_COST_OK",
        "CURRENT_BLOCKED_MIN_NOTIONAL",
        "CURRENT_TRUE_COST_REVIEW",
        "REVIEW_FIRST_NOT_TRADE_NOW",
        "WATCH_ONLY_NOT_TRADE_NOW",
        "WAIT_PULLBACK_NOT_TRADE_NOW",
        "BLOCKED_NOT_TRADE",
        "OPERATOR_OR_DATA_BLOCKED",
    ])
    current_ok_rows = readability_rows(rows, statuses=["COST_OK", "COST_OK_SMALL_ONLY"])
    blocked_min_rows = readability_rows(rows, statuses=["BLOCKED_BY_MIN_NOTIONAL"])
    review_first_rows = readability_rows(rows, substatuses=["REVIEW_FIRST_NO_CURRENT_TRADE"])
    watch_rows = readability_rows(rows, substatuses=["WATCH_ONLY_NO_CURRENT_TRADE"])
    wait_rows = readability_rows(rows, substatuses=["WAIT_PULLBACK_NO_CURRENT_TRADE"])
    true_cost_rows = readability_rows(rows, substatuses=["TRUE_COST_REVIEW"])
    lines = [
        title,
        "",
        "1. Final status / run id / timestamp.",
        f"STATUS: {values.get('STATUS', '')}",
        f"RUN_ID: {values.get('RUN_ID', '')}",
        f"GENERATED_AT: {values.get('_GENERATED_AT', '')}",
        "",
        "2. Broker profile and fee assumptions.",
        f"- Broker profile: `{values.get('BROKER_PROFILE', '')}`",
        f"- Commission rate pct: `{values.get('COMMISSION_RATE_PCT', '')}`",
        f"- Commission min USD: `{values.get('COMMISSION_MIN_USD', '')}`",
        f"- Commission cap USD: `{values.get('COMMISSION_CAP_USD', '')}`",
        f"- Conservative FX stress assumption JPY/USD: `{values.get('CONSERVATIVE_FX_FEE_JPY_PER_USD', '')}`",
        f"- {FEE_NOTE}",
        "",
        "3. Cost-adjusted status counts.",
        md_table(status_counts_rows, ["cost_adjusted_trade_status", "count"], 20),
        "4. Operator readability bucket counts.",
        md_table(readability_counts_rows, ["operator_readability_bucket", "count"], 20),
        "5. Today's Current Cost-OK Manual Review Candidates.",
        "- These are not automatic buy orders; they passed static buyability, position, and cost gates.",
        md_table(current_ok_rows, row_fields, 25),
        "6. Current Blocked By Minimum Notional.",
        "- The model may like these, but the current suggested trade size is too small for the configured minimum effective notional.",
        md_table(blocked_min_rows, row_fields, 25),
        "7. Review-First / No Current Trade.",
        "- These are not cost failures. They are review-first names with no current trade notional.",
        md_table(review_first_rows, row_fields, 25),
        "8. Watch-Only / No Current Trade.",
        "- These are not current trades.",
        md_table(watch_rows, row_fields, 25),
        "9. Wait-Pullback / No Current Trade.",
        "- These are not current trades.",
        md_table(wait_rows, row_fields, 25),
        "10. True Cost Review Required.",
        "- Only rows with suggested_initial_notional_usd > 0 are shown here.",
        md_table(true_cost_rows, row_fields, 25),
        "11. Cost model assumptions.",
        md_table(assumption_rows(values), ["assumption", "value"], 20),
        "12. Safety.",
        "- Manual research guidance only.",
        "- No broker connection.",
        "- No order placement.",
        "- Fee assumptions must be verified before live trading.",
        "- `AUTO_TRADE: DISABLED`",
        "- `AUTO_SELL: DISABLED`",
        "- `OFFICIAL_DECISION_IMPACT: NONE`",
        "",
        "13. Warnings.",
        "\n".join(f"- `{warning}`" for warning in warnings),
        "",
        "14. Next step recommendation.",
        "- Review the readability split and keep all trading decisions manual.",
        "- R31D account-aware manual plan later.",
        "- R29D/R33A forward validation when future price data exists.",
    ]
    return "\n".join(lines) + "\n"


def build_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [
        {
            "run_id": values.get("RUN_ID", ""),
            "status": values.get("STATUS", ""),
            "mode": values.get("MODE", ""),
            "generated_at": values.get("_GENERATED_AT", ""),
            "broker_profile": values.get("BROKER_PROFILE", ""),
            "commission_rate_pct": values.get("COMMISSION_RATE_PCT", ""),
            "min_effective_trade_notional_usd": values.get("MIN_EFFECTIVE_TRADE_NOTIONAL_USD", ""),
            "source_position_policy_rows": values.get("SOURCE_POSITION_POLICY_ROWS", ""),
            "source_buyability_rows": values.get("SOURCE_BUYABILITY_ROWS", ""),
            "output_rows": values.get("OUTPUT_COST_ADJUSTED_ROWS", ""),
            "cost_ok_count": values.get("COST_OK_COUNT", ""),
            "cost_ok_small_only_count": values.get("COST_OK_SMALL_ONLY_COUNT", ""),
            "cost_review_required_count": values.get("COST_REVIEW_REQUIRED_COUNT", ""),
            "cost_watch_only_count": values.get("COST_WATCH_ONLY_COUNT", ""),
            "cost_wait_pullback_count": values.get("COST_WAIT_PULLBACK_COUNT", ""),
            "blocked_by_cost_count": values.get("BLOCKED_BY_COST_COUNT", ""),
            "blocked_by_min_notional_count": values.get("BLOCKED_BY_MIN_NOTIONAL_COUNT", ""),
            "blocked_by_position_policy_count": values.get("BLOCKED_BY_POSITION_POLICY_COUNT", ""),
            "operator_blocked_count": values.get("BLOCKED_BY_OPERATOR_STATE_COUNT", ""),
            "data_quality_blocked_count": values.get("BLOCKED_BY_DATA_QUALITY_COUNT", ""),
            "current_cost_ok_candidate_count": values.get("CURRENT_COST_OK_CANDIDATE_COUNT", ""),
            "current_small_only_cost_ok_count": values.get("CURRENT_SMALL_ONLY_COST_OK_COUNT", ""),
            "current_blocked_min_notional_count": values.get("CURRENT_BLOCKED_MIN_NOTIONAL_COUNT", ""),
            "review_first_no_current_trade_count": values.get("REVIEW_FIRST_NO_CURRENT_TRADE_COUNT", ""),
            "watch_only_no_current_trade_count": values.get("WATCH_ONLY_NO_CURRENT_TRADE_COUNT", ""),
            "wait_pullback_no_current_trade_count": values.get("WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT", ""),
            "true_cost_review_required_count": values.get("TRUE_COST_REVIEW_REQUIRED_COUNT", ""),
            "operator_readability_patch_applied": values.get("OPERATOR_READABILITY_PATCH_APPLIED", ""),
            "r31c_r1_status": values.get("R31C_R1_STATUS", ""),
            "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
            "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
            "notes": notes,
        }
    ]


def build_patch_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [
        {
            "run_id": values.get("RUN_ID", ""),
            "status": values.get("R31C_R1_STATUS", ""),
            "generated_at": values.get("_GENERATED_AT", ""),
            "source_rows": values.get("SOURCE_POSITION_POLICY_ROWS", ""),
            "output_rows": values.get("OUTPUT_COST_ADJUSTED_ROWS", ""),
            "current_cost_ok_candidate_count": values.get("CURRENT_COST_OK_CANDIDATE_COUNT", ""),
            "current_small_only_cost_ok_count": values.get("CURRENT_SMALL_ONLY_COST_OK_COUNT", ""),
            "current_blocked_min_notional_count": values.get("CURRENT_BLOCKED_MIN_NOTIONAL_COUNT", ""),
            "review_first_no_current_trade_count": values.get("REVIEW_FIRST_NO_CURRENT_TRADE_COUNT", ""),
            "watch_only_no_current_trade_count": values.get("WATCH_ONLY_NO_CURRENT_TRADE_COUNT", ""),
            "wait_pullback_no_current_trade_count": values.get("WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT", ""),
            "true_cost_review_required_count": values.get("TRUE_COST_REVIEW_REQUIRED_COUNT", ""),
            "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
            "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
            "notes": notes,
        }
    ]
def patch_status(values: Dict[str, object], rows: Sequence[Dict[str, object]], dry_run: bool, required_missing: Sequence[str], operator_ok: bool) -> str:
    if dry_run:
        return STATUS_R1_DRY
    if values.get("STATUS") == STATUS_FAIL:
        return STATUS_R1_FAIL
    if values.get("FORBIDDEN_MODIFIED") != "FALSE":
        return STATUS_R1_FAIL
    if required_missing or len(rows) != EXPECTED_ROWS or not operator_ok:
        return STATUS_R1_FAIL
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        return STATUS_R1_WARN
    return STATUS_R1_OK


def write_outputs(root: Path, values: Dict[str, object], rows: Sequence[Dict[str, object]], dry_run: bool, notes: str, required_missing: Sequence[str], operator_ok: bool, readability_r1: bool) -> None:
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    values["CURRENT_COST_OK_CANDIDATE_COUNT"] = sum(1 for row in rows if upper(row.get("cost_adjusted_trade_status")) == "COST_OK")
    values["CURRENT_SMALL_ONLY_COST_OK_COUNT"] = sum(1 for row in rows if upper(row.get("cost_adjusted_trade_status")) == "COST_OK_SMALL_ONLY")
    values["CURRENT_BLOCKED_MIN_NOTIONAL_COUNT"] = sum(1 for row in rows if upper(row.get("cost_adjusted_trade_status")) == "BLOCKED_BY_MIN_NOTIONAL")
    values["REVIEW_FIRST_NO_CURRENT_TRADE_COUNT"] = sum(1 for row in rows if upper(row.get("cost_review_substatus")) == "REVIEW_FIRST_NO_CURRENT_TRADE")
    values["WATCH_ONLY_NO_CURRENT_TRADE_COUNT"] = sum(1 for row in rows if upper(row.get("cost_review_substatus")) == "WATCH_ONLY_NO_CURRENT_TRADE")
    values["WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT"] = sum(1 for row in rows if upper(row.get("cost_review_substatus")) == "WAIT_PULLBACK_NO_CURRENT_TRADE")
    values["TRUE_COST_REVIEW_REQUIRED_COUNT"] = sum(1 for row in rows if upper(row.get("cost_review_substatus")) == "TRUE_COST_REVIEW")
    values["SOURCE_R31C_ROWS"] = len(rows)
    values["OPERATOR_READABILITY_PATCH_APPLIED"] = bool_text(readability_r1)
    values["R31C_R1_STATUS"] = patch_status(values, rows, dry_run, required_missing, operator_ok)
    if not dry_run:
        write_csv(root / OUT_PLAN, rows, OUTPUT_FIELDS)
    report = build_report(values, rows)
    patch_report = build_report(values, rows, "# V18.31C-R1 Cost Plan Readability / Review Split Patch")
    write_text(root / OUT_CURRENT_REPORT, report)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, notes), SUMMARY_FIELDS)
    if readability_r1:
        write_text(root / OUT_PATCH_REPORT, patch_report)
        write_text(root / OUT_PATCH_READ_FIRST, read_first_text(values, PATCH_READ_FIRST_FIELDS))
        write_csv(root / OUT_PATCH_SUMMARY, build_patch_summary(values, notes), PATCH_SUMMARY_FIELDS)


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31C_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    before = protected_sig(root)

    pos_rows, _pos_fields = read_csv(root / POSITION_POLICY)
    buy_rows, _buy_fields = read_csv(root / BUYABILITY)
    rec_rows, _rec_fields = read_csv(root / RECOMMENDATIONS)
    ranked_rows, _ranked_fields = read_csv(root / RANKED)
    theme_rows, _theme_fields = read_csv(root / THEMES)
    required_missing = [rel for rel in [POSITION_POLICY, BUYABILITY, RECOMMENDATIONS, RANKED] if not (root / rel).exists()]
    context = operator_context(root, len(pos_rows), len(buy_rows), len(rec_rows), len(ranked_rows), len(theme_rows))
    operator_ok = bool(context["structural_ok"])
    source_file = str(root / POSITION_POLICY)

    output_rows: List[Dict[str, object]] = []
    if not required_missing:
        for row in pos_rows[: max(args.top_n, 0)]:
            output_rows.append(classify_cost(row, operator_ok, args, run_id, generated_at, source_file))

    counts = status_counts(output_rows)
    values: Dict[str, object] = {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "BROKER_PROFILE": args.broker_profile,
        "COMMISSION_RATE_PCT": pct(args.commission_rate_pct),
        "COMMISSION_MIN_USD": money(args.commission_min_usd),
        "COMMISSION_CAP_USD": money(args.commission_cap_usd),
        "FX_FEE_JPY_PER_USD": pct(args.fx_fee_jpy_per_usd),
        "CONSERVATIVE_FX_FEE_JPY_PER_USD": pct(args.conservative_fx_fee_jpy_per_usd),
        "MIN_EFFECTIVE_TRADE_NOTIONAL_USD": money(args.min_effective_trade_notional_usd),
        "COST_SAFETY_MULTIPLE": pct(args.cost_safety_multiple),
        "SOURCE_POSITION_POLICY_FILE": source_file,
        "SOURCE_POSITION_POLICY_ROWS": len(pos_rows),
        "SOURCE_BUYABILITY_FILE": str(root / BUYABILITY),
        "SOURCE_BUYABILITY_ROWS": len(buy_rows),
        "OUTPUT_COST_ADJUSTED_ROWS": len(output_rows) if not args.dry_run else 0,
        "COST_OK_COUNT": counts.get("COST_OK", 0),
        "COST_OK_SMALL_ONLY_COUNT": counts.get("COST_OK_SMALL_ONLY", 0),
        "COST_REVIEW_REQUIRED_COUNT": counts.get("COST_REVIEW_REQUIRED", 0),
        "COST_WATCH_ONLY_COUNT": counts.get("COST_WATCH_ONLY", 0),
        "COST_WAIT_PULLBACK_COUNT": counts.get("COST_WAIT_PULLBACK", 0),
        "BLOCKED_BY_COST_COUNT": counts.get("BLOCKED_BY_COST", 0),
        "BLOCKED_BY_MIN_NOTIONAL_COUNT": counts.get("BLOCKED_BY_MIN_NOTIONAL", 0),
        "BLOCKED_BY_POSITION_POLICY_COUNT": counts.get("BLOCKED_BY_POSITION_POLICY", 0),
        "BLOCKED_BY_OPERATOR_STATE_COUNT": counts.get("BLOCKED_BY_OPERATOR_STATE", 0),
        "BLOCKED_BY_DATA_QUALITY_COUNT": counts.get("BLOCKED_BY_DATA_QUALITY", 0),
        "CURRENT_RANKED_CANDIDATE_ROWS": context["current_ranked"],
        "CURRENT_RECOMMENDATION_ROWS": context["current_recs"],
        "CURRENT_THEME_CLASSIFICATION_ROWS": context["current_themes"],
        "LATEST_FULL_FREEZE_TICKER_COUNT": context["latest_freeze"],
        "R31B_STATUS": context["r31b_status"],
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
        values["NEXT_RECOMMENDED_STEP"] = "Restore required R31B/R31A inputs before generating cost-adjusted trade plan."
    elif args.dry_run:
        notes = "Dry run only; current cost-adjusted trade plan CSV not written."
        values["STATUS"] = STATUS_DRY
        values["NEXT_RECOMMENDED_STEP"] = "Run live R31C to generate current cost-adjusted trade plan."
    elif len(pos_rows) != EXPECTED_ROWS or len(buy_rows) != EXPECTED_ROWS or len(rec_rows) != EXPECTED_ROWS or len(ranked_rows) != EXPECTED_ROWS or len(output_rows) != args.top_n:
        notes = "Structural row count mismatch."
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Run R31B/R31A/R30E and inspect structural inputs before using cost-adjusted plan."
    elif not operator_ok:
        notes = "Operator state blocked all rows."
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31B/R31A/R30E/R30A operator state before manual cost review."
    elif context["warn_only"]:
        notes = "FORWARD_RETURN_NOT_READY_COST_MODEL_ONLY"
        values["STATUS"] = STATUS_WARN
        values["NEXT_RECOMMENDED_STEP"] = "Static cost model only; verify broker fee schedule before any live trading."
    else:
        notes = "Moomoo cost/slippage constraint ready."
        values["STATUS"] = STATUS_OK
        values["NEXT_RECOMMENDED_STEP"] = "Review V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.md; next planned layer is R31D account-aware manual plan."

    after = protected_sig(root)
    values["FORBIDDEN_MODIFIED"] = bool_text(after != before)
    if values["FORBIDDEN_MODIFIED"] != "FALSE":
        values["STATUS"] = STATUS_FAIL
        notes = "Forbidden input modification detected."
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31C error report; do not trade from this run."

    write_outputs(root, values, output_rows, args.dry_run, notes, required_missing, operator_ok, args.readability_r1)
    if values["STATUS"] == STATUS_FAIL:
        write_text(root / OUT_ERROR_REPORT, f"# V18.31C Moomoo Cost / Slippage Constraint Error\n\n```text\n{notes}\n```\n")
        return 1, values
    return 0, values


def write_failure(root: Path, error: BaseException, args: argparse.Namespace) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31C_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "BROKER_PROFILE": args.broker_profile,
        "COMMISSION_RATE_PCT": pct(args.commission_rate_pct),
        "COMMISSION_MIN_USD": money(args.commission_min_usd),
        "COMMISSION_CAP_USD": money(args.commission_cap_usd),
        "FX_FEE_JPY_PER_USD": pct(args.fx_fee_jpy_per_usd),
        "CONSERVATIVE_FX_FEE_JPY_PER_USD": pct(args.conservative_fx_fee_jpy_per_usd),
        "MIN_EFFECTIVE_TRADE_NOTIONAL_USD": money(args.min_effective_trade_notional_usd),
        "COST_SAFETY_MULTIPLE": pct(args.cost_safety_multiple),
        "SOURCE_POSITION_POLICY_FILE": str(root / POSITION_POLICY),
        "SOURCE_POSITION_POLICY_ROWS": 0,
        "SOURCE_BUYABILITY_FILE": str(root / BUYABILITY),
        "SOURCE_BUYABILITY_ROWS": 0,
        "OUTPUT_COST_ADJUSTED_ROWS": 0,
        "COST_OK_COUNT": 0,
        "COST_OK_SMALL_ONLY_COUNT": 0,
        "COST_REVIEW_REQUIRED_COUNT": 0,
        "COST_WATCH_ONLY_COUNT": 0,
        "COST_WAIT_PULLBACK_COUNT": 0,
        "BLOCKED_BY_COST_COUNT": 0,
        "BLOCKED_BY_MIN_NOTIONAL_COUNT": 0,
        "BLOCKED_BY_POSITION_POLICY_COUNT": 0,
        "BLOCKED_BY_OPERATOR_STATE_COUNT": 0,
        "BLOCKED_BY_DATA_QUALITY_COUNT": 0,
        "CURRENT_RANKED_CANDIDATE_ROWS": 0,
        "CURRENT_RECOMMENDATION_ROWS": 0,
        "CURRENT_THEME_CLASSIFICATION_ROWS": 0,
        "LATEST_FULL_FREEZE_TICKER_COUNT": 0,
        "R31B_STATUS": "",
        "R31A_STATUS": "",
        "R30E_STATUS": "",
        "R30A_STATUS": "",
        "FORWARD_RETURN_FILLABLE_READY": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 1,
        "FORBIDDEN_MODIFIED": "UNKNOWN",
        "NEXT_RECOMMENDED_STEP": "Inspect R31C error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    }
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, str(error)), SUMMARY_FIELDS)
    write_text(root / OUT_ERROR_REPORT, f"# V18.31C Moomoo Cost / Slippage Constraint Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31C Moomoo Japan cost/slippage constraint layer.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--broker-profile", default="MOOMOO_JP_US_STOCK_BASIC")
    parser.add_argument("--commission-rate-pct", type=float, default=0.132)
    parser.add_argument("--commission-min-usd", type=float, default=0.0)
    parser.add_argument("--commission-cap-usd", type=float, default=22.0)
    parser.add_argument("--fx-fee-jpy-per-usd", type=float, default=0.0)
    parser.add_argument("--conservative-fx-fee-jpy-per-usd", type=float, default=0.25)
    parser.add_argument("--min-effective-trade-notional-usd", type=float, default=50.0)
    parser.add_argument("--cost-safety-multiple", type=float, default=2.0)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--readability-r1", dest="readability_r1", action="store_true")
    parser.add_argument("--no-readability-r1", dest="readability_r1", action="store_false")
    parser.set_defaults(readability_r1=True)
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
