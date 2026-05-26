from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRY = "OK_V18_31D_ACCOUNT_AWARE_MANUAL_PLAN_DRY_RUN_READY"
STATUS_OK = "OK_V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_READY"
STATUS_WARN = "WARN_V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_FAILED"
MODE_LIVE = "ACCOUNT_AWARE_MANUAL_TRADE_PLAN_LAYER"
MODE_DRY = "ACCOUNT_AWARE_MANUAL_TRADE_PLAN_DRY_RUN"
EXPECTED_ROWS = 252
MIN_EFFECTIVE_TRADE_NOTIONAL_USD = 50.0

COST_ADJUSTED = "outputs/v18/execution/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.csv"
POSITION_POLICY = "outputs/v18/execution/V18_CURRENT_POSITION_SIZING_POLICY.csv"
BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
ACCOUNT_STATE = "state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE.csv"
ACCOUNT_TEMPLATE = "state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE_TEMPLATE.csv"

R31C_READ_FIRST = "outputs/v18/ops/V18_31C_READ_FIRST.txt"
R31C_R1_READ_FIRST = "outputs/v18/ops/V18_31C_R1_READ_FIRST.txt"
R31B_READ_FIRST = "outputs/v18/ops/V18_31B_READ_FIRST.txt"
R31A_READ_FIRST = "outputs/v18/ops/V18_31A_READ_FIRST.txt"
R30E_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"

OUT_PLAN = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md"
OUT_REPORT = "outputs/v18/read_center/V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_31D_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_SUMMARY.csv"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_ERROR.md"

ACCOUNT_NOTE = "Manual account state is operator-maintained and must be updated before relying on account-aware constraints."

ACCOUNT_FIELDS = [
    "account_id",
    "as_of_date",
    "account_total_value_usd",
    "cash_usd",
    "ticker",
    "shares",
    "avg_cost_usd",
    "current_price_usd",
    "market_value_usd",
    "position_pct",
    "primary_theme",
    "position_type",
    "notes",
]

OUTPUT_FIELDS = [
    "ticker",
    "rank",
    "composite_candidate_score",
    "primary_theme",
    "recommendation_tier",
    "buy_now_status",
    "position_policy_status",
    "cost_adjusted_trade_status",
    "risk_bucket",
    "suggested_initial_notional_usd",
    "suggested_max_notional_usd",
    "estimated_total_roundtrip_cost_pct",
    "minimum_required_expected_return_pct",
    "account_trade_status",
    "account_trade_action",
    "account_gate_result",
    "account_block_reason",
    "current_position_notional_usd",
    "current_position_pct",
    "current_shares",
    "current_avg_cost_usd",
    "current_unrealized_pnl_pct",
    "current_theme_exposure_pct",
    "projected_theme_exposure_pct_after_trade",
    "current_high_risk_exposure_pct",
    "projected_high_risk_exposure_pct_after_trade",
    "account_total_value_usd",
    "cash_usd",
    "cash_reserve_required_usd",
    "available_cash_after_reserve_usd",
    "suggested_account_initial_notional_usd",
    "max_additional_notional_usd",
    "cash_after_suggested_trade_usd",
    "would_exceed_cash_reserve_flag",
    "would_exceed_single_position_cap_flag",
    "would_exceed_theme_exposure_cap_flag",
    "would_exceed_high_risk_exposure_cap_flag",
    "would_exceed_active_position_limit_flag",
    "would_exceed_speculative_position_limit_flag",
    "would_exceed_new_buys_per_day_flag",
    "existing_position_flag",
    "add_allowed_flag",
    "new_buy_allowed_flag",
    "trim_review_flag",
    "manual_account_state_mode",
    "account_state_quality_flag",
    "account_plan_reason",
    "source_cost_adjusted_file",
    "source_account_state_file",
    "generated_at",
    "run_id",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "TOP_N_REQUESTED",
    "ACCOUNT_STATE_FILE",
    "ACCOUNT_STATE_MODE",
    "ACCOUNT_STATE_QUALITY_FLAG",
    "ACCOUNT_TOTAL_VALUE_USD",
    "CASH_USD",
    "CASH_RESERVE_PCT",
    "CASH_RESERVE_REQUIRED_USD",
    "AVAILABLE_CASH_AFTER_RESERVE_USD",
    "MAX_ACTIVE_POSITIONS",
    "MAX_SPECULATIVE_POSITIONS",
    "MAX_SINGLE_POSITION_PCT",
    "MAX_THEME_EXPOSURE_PCT",
    "MAX_HIGH_RISK_TOTAL_EXPOSURE_PCT",
    "MAX_NEW_BUYS_PER_DAY",
    "SOURCE_COST_ADJUSTED_FILE",
    "SOURCE_COST_ADJUSTED_ROWS",
    "SOURCE_POSITION_POLICY_FILE",
    "SOURCE_POSITION_POLICY_ROWS",
    "SOURCE_BUYABILITY_FILE",
    "SOURCE_BUYABILITY_ROWS",
    "OUTPUT_ACCOUNT_AWARE_ROWS",
    "ACCOUNT_TRADE_ALLOWED_COUNT",
    "ACCOUNT_TRADE_SMALL_ONLY_COUNT",
    "ACCOUNT_WATCH_ONLY_COUNT",
    "ACCOUNT_WAIT_PULLBACK_COUNT",
    "ACCOUNT_REVIEW_FIRST_COUNT",
    "BLOCKED_BY_CASH_COUNT",
    "BLOCKED_BY_CASH_RESERVE_COUNT",
    "BLOCKED_BY_EXISTING_POSITION_COUNT",
    "BLOCKED_BY_SINGLE_POSITION_CAP_COUNT",
    "BLOCKED_BY_THEME_EXPOSURE_COUNT",
    "BLOCKED_BY_HIGH_RISK_EXPOSURE_COUNT",
    "BLOCKED_BY_ACTIVE_POSITION_LIMIT_COUNT",
    "BLOCKED_BY_SPECULATIVE_POSITION_LIMIT_COUNT",
    "BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT",
    "BLOCKED_BY_COST_PLAN_COUNT",
    "BLOCKED_BY_ACCOUNT_STATE_QUALITY_COUNT",
    "BLOCKED_BY_OPERATOR_STATE_COUNT",
    "BLOCKED_BY_DATA_QUALITY_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "R31C_STATUS",
    "R31C_R1_STATUS",
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
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "account_state_mode",
    "account_state_quality_flag",
    "account_total_value_usd",
    "cash_usd",
    "available_cash_after_reserve_usd",
    "source_cost_adjusted_rows",
    "source_position_policy_rows",
    "source_buyability_rows",
    "output_rows",
    "account_trade_allowed_count",
    "account_trade_small_only_count",
    "account_watch_only_count",
    "account_wait_pullback_count",
    "account_review_first_count",
    "blocked_by_cash_count",
    "blocked_by_cash_reserve_count",
    "blocked_by_single_position_cap_count",
    "blocked_by_theme_exposure_count",
    "blocked_by_high_risk_exposure_count",
    "blocked_by_active_position_limit_count",
    "blocked_by_speculative_position_limit_count",
    "blocked_by_daily_new_buy_limit_count",
    "blocked_by_cost_plan_count",
    "blocked_by_account_state_quality_count",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

PROTECTED_INPUTS = [
    COST_ADJUSTED,
    POSITION_POLICY,
    BUYABILITY,
    RECOMMENDATIONS,
    RANKED,
    THEMES,
    TECHNICAL,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv",
]


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


def ensure_account_files(root: Path, args: argparse.Namespace, today: str) -> Tuple[str, bool]:
    template_path = root / ACCOUNT_TEMPLATE
    state_path = root / ACCOUNT_STATE
    template_created = False
    if not template_path.exists():
        write_csv(template_path, [], ACCOUNT_FIELDS)
        template_created = True
    if not state_path.exists():
        cash = args.cash_usd if args.cash_usd is not None else args.account_size_usd
        starter = {
            "account_id": "MANUAL_DEFAULT",
            "as_of_date": today,
            "account_total_value_usd": money(args.account_size_usd),
            "cash_usd": money(cash),
            "ticker": "CASH_USD",
            "shares": "0",
            "avg_cost_usd": "0",
            "current_price_usd": "1",
            "market_value_usd": "0",
            "position_pct": "0",
            "primary_theme": "CASH",
            "position_type": "CASH",
            "notes": "TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA",
        }
        write_csv(state_path, [starter], ACCOUNT_FIELDS)
        return "TEMPLATE_OR_EMPTY_ACCOUNT_ASSUMPTION", True
    return "MANUAL_ACCOUNT_STATE_FILE", template_created


def is_cash_row(row: Dict[str, str]) -> bool:
    return upper(row.get("ticker")) == "CASH_USD" or upper(row.get("position_type")) == "CASH"


def is_high_risk(row: Dict[str, object]) -> bool:
    risk = upper(row.get("risk_bucket"))
    tier = upper(row.get("recommendation_tier"))
    theme = upper(row.get("primary_theme"))
    buy_status = upper(row.get("buy_now_status"))
    return "HIGH_RISK" in risk or "EXTREME_RISK" in risk or tier == "SPECULATIVE_SATELLITE" or theme == "CRYPTO_BETA" or buy_status == "BUY_SMALL_ONLY"


def theme_cap_applies(theme: str) -> bool:
    theme = upper(theme)
    return bool(theme and theme not in {"CASH", "DEFENSIVE_HEDGE", "ETF_OR_MACRO_EXPOSURE", "MACRO_OR_ETF_REVIEW"})


def parse_account_state(root: Path, args: argparse.Namespace, plan_by_ticker: Dict[str, Dict[str, str]], generated_at: str) -> Dict[str, object]:
    mode, created_starter = ensure_account_files(root, args, generated_at[:10])
    rows, _fields = read_csv(root / ACCOUNT_STATE)
    starter_assumption = any("TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA" in upper(row.get("notes")) for row in rows)
    if starter_assumption or (rows and all(is_cash_row(row) for row in rows)):
        mode = "TEMPLATE_OR_EMPTY_ACCOUNT_ASSUMPTION"
    valid_account_rows = [row for row in rows if to_float(row.get("account_total_value_usd"), -1) > 0 and to_float(row.get("cash_usd"), -1) >= 0]
    first = valid_account_rows[0] if valid_account_rows else (rows[0] if rows else {})
    account_total = to_float(first.get("account_total_value_usd"), args.account_size_usd if created_starter else 0.0)
    cash_default = args.cash_usd if args.cash_usd is not None else account_total
    cash = to_float(first.get("cash_usd"), cash_default if created_starter else -1.0)
    quality = "OK"
    warnings: List[str] = []
    if account_total <= 0:
        quality = "FAIL_INVALID_ACCOUNT_TOTAL_VALUE"
    elif cash < 0:
        quality = "FAIL_INVALID_CASH"
    elif created_starter or all(is_cash_row(row) for row in rows):
        quality = "WARN_TEMPLATE_EMPTY_ACCOUNT"
        warnings.append("TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA")
    positions: Dict[str, Dict[str, object]] = {}
    theme_exposure = defaultdict(float)
    high_risk_notional = 0.0
    missing_market_values = False
    for row in rows:
        ticker = upper(row.get("ticker"))
        if not ticker or is_cash_row(row):
            continue
        shares = to_float(row.get("shares"))
        price = to_float(row.get("current_price_usd"))
        market_value = to_float(row.get("market_value_usd"), -1.0)
        if market_value < 0:
            if shares and price:
                market_value = shares * price
                missing_market_values = True
            else:
                market_value = 0.0
                missing_market_values = True
        avg_cost = to_float(row.get("avg_cost_usd"))
        position_pct = (market_value / account_total * 100.0) if account_total > 0 else 0.0
        theme = upper(row.get("primary_theme")) or upper(plan_by_ticker.get(ticker, {}).get("primary_theme")) or "UNKNOWN"
        plan_row = plan_by_ticker.get(ticker, {})
        unrealized = ((price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 and price > 0 else 0.0
        positions[ticker] = {
            "ticker": ticker,
            "shares": shares,
            "avg_cost": avg_cost,
            "price": price,
            "market_value": market_value,
            "position_pct": position_pct,
            "primary_theme": theme,
            "unrealized_pnl_pct": unrealized,
        }
        theme_exposure[theme] += position_pct
        risk_row = {
            "risk_bucket": plan_row.get("risk_bucket") or row.get("position_type"),
            "recommendation_tier": plan_row.get("recommendation_tier"),
            "primary_theme": theme,
            "buy_now_status": plan_row.get("buy_now_status"),
        }
        if is_high_risk(risk_row):
            high_risk_notional += market_value
    if quality == "OK" and missing_market_values:
        quality = "WARN_MISSING_POSITION_MARKET_VALUES"
        warnings.append("MISSING_POSITION_MARKET_VALUES")
    reserve = account_total * args.cash_reserve_pct / 100.0
    available = max(0.0, cash - reserve)
    return {
        "mode": mode,
        "quality": quality,
        "warnings": warnings,
        "rows": rows,
        "positions": positions,
        "theme_exposure": dict(theme_exposure),
        "high_risk_exposure_pct": (high_risk_notional / account_total * 100.0) if account_total > 0 else 0.0,
        "account_total": account_total,
        "cash": cash,
        "reserve": reserve,
        "available": available,
        "active_positions": sum(1 for pos in positions.values() if to_float(pos.get("market_value")) > 0),
        "speculative_positions": sum(
            1 for ticker, pos in positions.items()
            if is_high_risk({
                "risk_bucket": plan_by_ticker.get(ticker, {}).get("risk_bucket"),
                "recommendation_tier": plan_by_ticker.get(ticker, {}).get("recommendation_tier"),
                "primary_theme": pos.get("primary_theme"),
                "buy_now_status": plan_by_ticker.get(ticker, {}).get("buy_now_status"),
            })
        ),
    }


def status_counts(rows: Sequence[Dict[str, object]]) -> Counter:
    return Counter(norm(row.get("account_trade_status")) for row in rows)


def md_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 25) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def context_values(root: Path, cost_rows: int, pos_rows: int, buy_rows: int, rec_rows: int, ranked_rows: int, theme_rows: int) -> Dict[str, object]:
    r31c = read_status_file(root / R31C_READ_FIRST)
    r31c_r1 = read_status_file(root / R31C_R1_READ_FIRST)
    r31b = read_status_file(root / R31B_READ_FIRST)
    r31a = read_status_file(root / R31A_READ_FIRST)
    r30e = read_status_file(root / R30E_READ_FIRST)
    r30a = read_status_file(root / R30A_READ_FIRST)
    latest_freeze = to_int(r31c.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r31b.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r31a.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r30e.get("LATEST_FULL_FREEZE_TICKER_COUNT") or r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT"), 0)
    current_ranked = to_int(r31c.get("CURRENT_RANKED_CANDIDATE_ROWS") or r31b.get("CURRENT_RANKED_CANDIDATE_ROWS") or r31a.get("CURRENT_RANKED_CANDIDATE_ROWS"), ranked_rows)
    current_recs = to_int(r31c.get("CURRENT_RECOMMENDATION_ROWS") or r31b.get("CURRENT_RECOMMENDATION_ROWS") or r31a.get("CURRENT_RECOMMENDATION_ROWS"), rec_rows)
    current_themes = to_int(r31c.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r31b.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r31a.get("CURRENT_THEME_CLASSIFICATION_ROWS") or r30a.get("THEME_CLASSIFICATION_ROW_COUNT"), theme_rows)
    forward_ready = (r31c.get("FORWARD_RETURN_FILLABLE_READY") == "TRUE") or (r31b.get("FORWARD_RETURN_FILLABLE_READY") == "TRUE") or (r31a.get("FORWARD_RETURN_FILLABLE_READY") == "TRUE")
    auto_trade = r31c.get("AUTO_TRADE") or r31b.get("AUTO_TRADE") or r31a.get("AUTO_TRADE") or "DISABLED"
    auto_sell = r31c.get("AUTO_SELL") or r31b.get("AUTO_SELL") or r31a.get("AUTO_SELL") or "DISABLED"
    impact = r31c.get("OFFICIAL_DECISION_IMPACT") or r31b.get("OFFICIAL_DECISION_IMPACT") or r31a.get("OFFICIAL_DECISION_IMPACT") or "NONE"
    structural_ok = (
        cost_rows == EXPECTED_ROWS
        and pos_rows == EXPECTED_ROWS
        and buy_rows == EXPECTED_ROWS
        and rec_rows == EXPECTED_ROWS
        and ranked_rows == EXPECTED_ROWS
        and theme_rows == EXPECTED_ROWS
        and current_ranked == EXPECTED_ROWS
        and current_recs == EXPECTED_ROWS
        and current_themes == EXPECTED_ROWS
        and latest_freeze in (0, EXPECTED_ROWS)
        and auto_trade == "DISABLED"
        and auto_sell == "DISABLED"
        and impact == "NONE"
    )
    return {
        "r31c_status": r31c.get("STATUS", ""),
        "r31c_r1_status": r31c.get("R31C_R1_STATUS") or r31c_r1.get("STATUS", ""),
        "r31b_status": r31b.get("STATUS", ""),
        "r31a_status": r31a.get("STATUS", ""),
        "r30e_status": r30e.get("STATUS", ""),
        "r30a_status": r30a.get("STATUS", ""),
        "current_ranked": current_ranked,
        "current_recs": current_recs,
        "current_themes": current_themes,
        "latest_freeze": latest_freeze,
        "forward_ready": forward_ready,
        "auto_trade": auto_trade,
        "auto_sell": auto_sell,
        "impact": impact,
        "structural_ok": structural_ok,
    }


def cost_plan_mapping(row: Dict[str, str]) -> Tuple[str, str, str, str]:
    status = upper(row.get("cost_adjusted_trade_status"))
    substatus = upper(row.get("cost_review_substatus"))
    initial = to_float(row.get("suggested_initial_notional_usd"))
    if status == "COST_WATCH_ONLY":
        return "ACCOUNT_WATCH_ONLY", "WATCH_ONLY", "CAUTION", "PRESERVED_COST_WATCH_ONLY"
    if status == "COST_WAIT_PULLBACK":
        return "ACCOUNT_WAIT_PULLBACK", "WAIT_FOR_PULLBACK", "CAUTION", "PRESERVED_COST_WAIT_PULLBACK"
    if status == "COST_REVIEW_REQUIRED":
        reason = "TRUE_COST_REVIEW_REQUIRED" if substatus == "TRUE_COST_REVIEW" and initial > 0 else "PRESERVED_REVIEW_FIRST_NO_CURRENT_TRADE"
        return "ACCOUNT_REVIEW_FIRST", "REVIEW_FIRST", "CAUTION", reason
    if status in {"BLOCKED_BY_MIN_NOTIONAL", "BLOCKED_BY_COST", "BLOCKED_BY_POSITION_POLICY"}:
        return "BLOCKED_BY_COST_PLAN", "DO_NOT_BUY_COST_PLAN", "BLOCK", status
    if status == "BLOCKED_BY_OPERATOR_STATE":
        return "BLOCKED_BY_OPERATOR_STATE", "BLOCKED", "BLOCK", status
    if status == "BLOCKED_BY_DATA_QUALITY":
        return "BLOCKED_BY_DATA_QUALITY", "BLOCKED", "BLOCK", status
    return "", "", "", ""


def plan_rows(root: Path, args: argparse.Namespace, cost_rows: Sequence[Dict[str, str]], account: Dict[str, object], run_id: str, generated_at: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    positions: Dict[str, Dict[str, object]] = account["positions"]  # type: ignore[assignment]
    theme_exposure: Dict[str, float] = dict(account["theme_exposure"])  # type: ignore[arg-type]
    high_risk_exposure = float(account["high_risk_exposure_pct"])
    remaining_cash = float(account["cash"])
    new_buys_used = 0
    active_positions = int(account["active_positions"])
    speculative_positions = int(account["speculative_positions"])
    quality = str(account["quality"])
    account_total = float(account["account_total"])
    reserve = float(account["reserve"])
    source_cost = str(root / COST_ADJUSTED)
    source_account = str(root / ACCOUNT_STATE)

    for source in sorted(cost_rows[: max(args.top_n, 0)], key=lambda row: (to_int(row.get("rank"), 999999), upper(row.get("ticker")))):
        ticker = upper(source.get("ticker"))
        theme = upper(source.get("primary_theme")) or "UNKNOWN"
        cost_status = upper(source.get("cost_adjusted_trade_status"))
        base_notional = to_float(source.get("suggested_initial_notional_usd"))
        max_notional = to_float(source.get("suggested_max_notional_usd"))
        pos = positions.get(ticker, {})
        current_mv = float(pos.get("market_value", 0.0))
        current_pct = float(pos.get("position_pct", 0.0))
        existing = current_mv > 0
        current_theme = float(theme_exposure.get(theme, 0.0))
        current_high = high_risk_exposure
        suggested = 0.0
        max_additional = 0.0
        reasons: List[str] = []
        flags = {
            "cash_reserve": False,
            "single": False,
            "theme": False,
            "high": False,
            "active": False,
            "spec": False,
            "daily": False,
        }
        trim_review = current_pct > args.max_single_position_pct

        status, action, gate, mapped_reason = cost_plan_mapping(source)
        if quality.startswith("FAIL_"):
            status, action, gate = "BLOCKED_BY_ACCOUNT_STATE_QUALITY", "BLOCKED", "BLOCK"
            reasons.append(quality)
        elif status:
            reasons.append(mapped_reason)
        elif cost_status in {"COST_OK", "COST_OK_SMALL_ONLY"}:
            available_after_reserve = max(0.0, remaining_cash - reserve)
            desired = base_notional
            max_cash = max(0.0, available_after_reserve)
            single_allowed = max(0.0, (args.max_single_position_pct - current_pct) / 100.0 * account_total)
            theme_allowed = 10**9
            if theme_cap_applies(theme):
                theme_allowed = max(0.0, (args.max_theme_exposure_pct - current_theme) / 100.0 * account_total)
            high_allowed = 10**9
            if is_high_risk(source):
                high_allowed = max(0.0, (args.max_high_risk_total_exposure_pct - current_high) / 100.0 * account_total)
            max_additional = max(0.0, min(max_cash, single_allowed, theme_allowed, high_allowed))
            suggested = min(desired, max_additional)
            if suggested < desired:
                suggested = max_additional
            if existing and trim_review:
                flags["single"] = True
                status, action, gate = "BLOCKED_BY_SINGLE_POSITION_CAP", "DO_NOT_BUY_EXPOSURE", "BLOCK"
                reasons.append("EXISTING_POSITION_EXCEEDS_SINGLE_POSITION_CAP")
                suggested = 0.0
            elif desired > 0 and remaining_cash < args.min_cash_after_trade_usd:
                status, action, gate = "BLOCKED_BY_CASH", "DO_NOT_BUY_CASH", "BLOCK"
                reasons.append("CASH_BELOW_MIN_CASH_AFTER_TRADE")
                suggested = 0.0
            elif desired > 0 and available_after_reserve <= 0:
                flags["cash_reserve"] = True
                status, action, gate = "BLOCKED_BY_CASH_RESERVE", "DO_NOT_BUY_CASH", "BLOCK"
                reasons.append("NO_AVAILABLE_CASH_AFTER_RESERVE")
                suggested = 0.0
            elif desired > 0 and single_allowed <= 0:
                flags["single"] = True
                status, action, gate = "BLOCKED_BY_SINGLE_POSITION_CAP", "DO_NOT_BUY_EXPOSURE", "BLOCK"
                reasons.append("SINGLE_POSITION_CAP_FULL")
                suggested = 0.0
            elif desired > 0 and theme_allowed <= 0:
                flags["theme"] = True
                status, action, gate = "BLOCKED_BY_THEME_EXPOSURE", "DO_NOT_BUY_EXPOSURE", "BLOCK"
                reasons.append("THEME_EXPOSURE_CAP_FULL")
                suggested = 0.0
            elif desired > 0 and high_allowed <= 0:
                flags["high"] = True
                status, action, gate = "BLOCKED_BY_HIGH_RISK_EXPOSURE", "DO_NOT_BUY_EXPOSURE", "BLOCK"
                reasons.append("HIGH_RISK_EXPOSURE_CAP_FULL")
                suggested = 0.0
            elif not existing and active_positions >= args.max_active_positions:
                flags["active"] = True
                status, action, gate = "BLOCKED_BY_ACTIVE_POSITION_LIMIT", "DO_NOT_BUY_EXPOSURE", "BLOCK"
                reasons.append("MAX_ACTIVE_POSITIONS_REACHED")
                suggested = 0.0
            elif not existing and upper(source.get("recommendation_tier")) == "SPECULATIVE_SATELLITE" and speculative_positions >= args.max_speculative_positions:
                flags["spec"] = True
                status, action, gate = "BLOCKED_BY_SPECULATIVE_POSITION_LIMIT", "DO_NOT_BUY_EXPOSURE", "BLOCK"
                reasons.append("MAX_SPECULATIVE_POSITIONS_REACHED")
                suggested = 0.0
            elif not existing and new_buys_used >= args.max_new_buys_per_day:
                flags["daily"] = True
                status, action, gate = "BLOCKED_BY_DAILY_NEW_BUY_LIMIT", "BLOCKED", "BLOCK"
                reasons.append("DAILY_NEW_BUY_LIMIT")
                suggested = 0.0
            elif suggested >= MIN_EFFECTIVE_TRADE_NOTIONAL_USD:
                if cost_status == "COST_OK_SMALL_ONLY" or suggested < desired:
                    status, action, gate = "ACCOUNT_TRADE_SMALL_ONLY", "CONSIDER_SMALL_MANUAL_BUY", "PASS"
                    reasons.append("ACCOUNT_CONSTRAINTS_ALLOW_SMALL_ONLY")
                else:
                    status, action, gate = "ACCOUNT_TRADE_ALLOWED", "CONSIDER_MANUAL_BUY", "PASS"
                    reasons.append("ACCOUNT_CONSTRAINTS_PASS")
                if not existing:
                    new_buys_used += 1
                    active_positions += 1
                    if upper(source.get("recommendation_tier")) == "SPECULATIVE_SATELLITE":
                        speculative_positions += 1
                remaining_cash -= suggested
                added_pct = suggested / account_total * 100.0 if account_total > 0 else 0.0
                theme_exposure[theme] = current_theme + added_pct
                if is_high_risk(source):
                    high_risk_exposure += added_pct
            else:
                flags["cash_reserve"] = desired > 0 and max_cash < MIN_EFFECTIVE_TRADE_NOTIONAL_USD
                status = "BLOCKED_BY_CASH_RESERVE" if flags["cash_reserve"] else "BLOCKED_BY_CASH"
                action, gate = "DO_NOT_BUY_CASH", "BLOCK"
                reasons.append("AVAILABLE_ACCOUNT_NOTIONAL_BELOW_MIN_EFFECTIVE_TRADE")
                suggested = 0.0
        else:
            status, action, gate = "BLOCKED_BY_COST_PLAN", "DO_NOT_BUY_COST_PLAN", "BLOCK"
            reasons.append("UNKNOWN_COST_PLAN_STATUS")

        projected_theme = current_theme + (suggested / account_total * 100.0 if account_total > 0 and theme_cap_applies(theme) else 0.0)
        projected_high = current_high + (suggested / account_total * 100.0 if account_total > 0 and is_high_risk(source) else 0.0)
        cash_after = remaining_cash if suggested > 0 and status in {"ACCOUNT_TRADE_ALLOWED", "ACCOUNT_TRADE_SMALL_ONLY"} else max(0.0, remaining_cash - suggested)
        if suggested > 0 and cash_after < reserve:
            flags["cash_reserve"] = True
        if suggested > 0 and current_pct + suggested / account_total * 100.0 > args.max_single_position_pct:
            flags["single"] = True
        if suggested > 0 and theme_cap_applies(theme) and projected_theme > args.max_theme_exposure_pct:
            flags["theme"] = True
        if suggested > 0 and is_high_risk(source) and projected_high > args.max_high_risk_total_exposure_pct:
            flags["high"] = True
        row = {
            "ticker": ticker,
            "rank": source.get("rank", ""),
            "composite_candidate_score": source.get("composite_candidate_score", ""),
            "primary_theme": theme,
            "recommendation_tier": source.get("recommendation_tier", ""),
            "buy_now_status": source.get("buy_now_status", ""),
            "position_policy_status": source.get("position_policy_status", ""),
            "cost_adjusted_trade_status": cost_status,
            "risk_bucket": source.get("risk_bucket", ""),
            "suggested_initial_notional_usd": source.get("suggested_initial_notional_usd", ""),
            "suggested_max_notional_usd": source.get("suggested_max_notional_usd", ""),
            "estimated_total_roundtrip_cost_pct": source.get("estimated_total_roundtrip_cost_pct", ""),
            "minimum_required_expected_return_pct": source.get("minimum_required_expected_return_pct", ""),
            "account_trade_status": status,
            "account_trade_action": action,
            "account_gate_result": gate,
            "account_block_reason": ";".join(dict.fromkeys(reasons)),
            "current_position_notional_usd": money(current_mv),
            "current_position_pct": pct(current_pct),
            "current_shares": pct(float(pos.get("shares", 0.0))),
            "current_avg_cost_usd": money(float(pos.get("avg_cost", 0.0))),
            "current_unrealized_pnl_pct": pct(float(pos.get("unrealized_pnl_pct", 0.0))),
            "current_theme_exposure_pct": pct(current_theme),
            "projected_theme_exposure_pct_after_trade": pct(projected_theme),
            "current_high_risk_exposure_pct": pct(current_high),
            "projected_high_risk_exposure_pct_after_trade": pct(projected_high),
            "account_total_value_usd": money(account_total),
            "cash_usd": money(float(account["cash"])),
            "cash_reserve_required_usd": money(reserve),
            "available_cash_after_reserve_usd": money(max(0.0, remaining_cash - reserve)),
            "suggested_account_initial_notional_usd": money(suggested),
            "max_additional_notional_usd": money(max_additional),
            "cash_after_suggested_trade_usd": money(cash_after),
            "would_exceed_cash_reserve_flag": bool_text(flags["cash_reserve"]),
            "would_exceed_single_position_cap_flag": bool_text(flags["single"]),
            "would_exceed_theme_exposure_cap_flag": bool_text(flags["theme"]),
            "would_exceed_high_risk_exposure_cap_flag": bool_text(flags["high"]),
            "would_exceed_active_position_limit_flag": bool_text(flags["active"]),
            "would_exceed_speculative_position_limit_flag": bool_text(flags["spec"]),
            "would_exceed_new_buys_per_day_flag": bool_text(flags["daily"]),
            "existing_position_flag": bool_text(existing),
            "add_allowed_flag": bool_text(existing and status in {"ACCOUNT_TRADE_ALLOWED", "ACCOUNT_TRADE_SMALL_ONLY"}),
            "new_buy_allowed_flag": bool_text((not existing) and status in {"ACCOUNT_TRADE_ALLOWED", "ACCOUNT_TRADE_SMALL_ONLY"}),
            "trim_review_flag": bool_text(trim_review),
            "manual_account_state_mode": account["mode"],
            "account_state_quality_flag": quality,
            "account_plan_reason": ";".join(dict.fromkeys(reasons)),
            "source_cost_adjusted_file": source_cost,
            "source_account_state_file": source_account,
            "generated_at": generated_at,
            "run_id": run_id,
        }
        rows.append(row)
    rows.sort(key=lambda row: (to_int(row.get("rank"), 999999), upper(row.get("ticker"))))
    return rows


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
    if to_int(values.get("OUTPUT_ACCOUNT_AWARE_ROWS")) not in (0, EXPECTED_ROWS):
        fails += 1
    if str(values.get("ACCOUNT_STATE_QUALITY_FLAG", "")).startswith("FAIL_"):
        fails += 1
    for field in ["SOURCE_COST_ADJUSTED_ROWS", "SOURCE_POSITION_POLICY_ROWS", "SOURCE_BUYABILITY_ROWS", "CURRENT_RANKED_CANDIDATE_ROWS", "CURRENT_RECOMMENDATION_ROWS", "CURRENT_THEME_CLASSIFICATION_ROWS"]:
        if to_int(values.get(field)) not in (0, EXPECTED_ROWS):
            fails += 1
    latest_freeze = to_int(values.get("LATEST_FULL_FREEZE_TICKER_COUNT"))
    if latest_freeze not in (0, EXPECTED_ROWS):
        fails += 1
    return fails


def read_first_text(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def build_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [{
        "run_id": values.get("RUN_ID", ""),
        "status": values.get("STATUS", ""),
        "generated_at": values.get("_GENERATED_AT", ""),
        "account_state_mode": values.get("ACCOUNT_STATE_MODE", ""),
        "account_state_quality_flag": values.get("ACCOUNT_STATE_QUALITY_FLAG", ""),
        "account_total_value_usd": values.get("ACCOUNT_TOTAL_VALUE_USD", ""),
        "cash_usd": values.get("CASH_USD", ""),
        "available_cash_after_reserve_usd": values.get("AVAILABLE_CASH_AFTER_RESERVE_USD", ""),
        "source_cost_adjusted_rows": values.get("SOURCE_COST_ADJUSTED_ROWS", ""),
        "source_position_policy_rows": values.get("SOURCE_POSITION_POLICY_ROWS", ""),
        "source_buyability_rows": values.get("SOURCE_BUYABILITY_ROWS", ""),
        "output_rows": values.get("OUTPUT_ACCOUNT_AWARE_ROWS", ""),
        "account_trade_allowed_count": values.get("ACCOUNT_TRADE_ALLOWED_COUNT", ""),
        "account_trade_small_only_count": values.get("ACCOUNT_TRADE_SMALL_ONLY_COUNT", ""),
        "account_watch_only_count": values.get("ACCOUNT_WATCH_ONLY_COUNT", ""),
        "account_wait_pullback_count": values.get("ACCOUNT_WAIT_PULLBACK_COUNT", ""),
        "account_review_first_count": values.get("ACCOUNT_REVIEW_FIRST_COUNT", ""),
        "blocked_by_cash_count": values.get("BLOCKED_BY_CASH_COUNT", ""),
        "blocked_by_cash_reserve_count": values.get("BLOCKED_BY_CASH_RESERVE_COUNT", ""),
        "blocked_by_single_position_cap_count": values.get("BLOCKED_BY_SINGLE_POSITION_CAP_COUNT", ""),
        "blocked_by_theme_exposure_count": values.get("BLOCKED_BY_THEME_EXPOSURE_COUNT", ""),
        "blocked_by_high_risk_exposure_count": values.get("BLOCKED_BY_HIGH_RISK_EXPOSURE_COUNT", ""),
        "blocked_by_active_position_limit_count": values.get("BLOCKED_BY_ACTIVE_POSITION_LIMIT_COUNT", ""),
        "blocked_by_speculative_position_limit_count": values.get("BLOCKED_BY_SPECULATIVE_POSITION_LIMIT_COUNT", ""),
        "blocked_by_daily_new_buy_limit_count": values.get("BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT", ""),
        "blocked_by_cost_plan_count": values.get("BLOCKED_BY_COST_PLAN_COUNT", ""),
        "blocked_by_account_state_quality_count": values.get("BLOCKED_BY_ACCOUNT_STATE_QUALITY_COUNT", ""),
        "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
        "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
        "notes": notes,
    }]


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]], account: Dict[str, object]) -> str:
    counts = [{"account_trade_status": key, "count": count} for key, count in status_counts(rows).most_common()]
    candidate_fields = ["rank", "ticker", "recommendation_tier", "primary_theme", "current_position_pct", "suggested_account_initial_notional_usd", "cash_after_suggested_trade_usd", "account_plan_reason"]
    block_fields = ["rank", "ticker", "account_trade_status", "recommendation_tier", "primary_theme", "suggested_account_initial_notional_usd", "account_block_reason"]
    theme_rows = [{"primary_theme": key, "current_theme_exposure_pct": pct(value)} for key, value in sorted(dict(account.get("theme_exposure", {})).items())]
    warnings: List[str] = []
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        warnings.append("FORWARD_RETURN_NOT_READY_ACCOUNT_PLAN_ONLY")
    if str(values.get("ACCOUNT_STATE_QUALITY_FLAG", "")).startswith("WARN_"):
        warnings.append(str(values.get("ACCOUNT_STATE_QUALITY_FLAG")))
    if values.get("ACCOUNT_STATE_MODE") == "TEMPLATE_OR_EMPTY_ACCOUNT_ASSUMPTION":
        warnings.append("TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA")
    if not warnings:
        warnings.append("NONE")
    blocked_statuses = {
        "BLOCKED_BY_CASH",
        "BLOCKED_BY_CASH_RESERVE",
        "BLOCKED_BY_EXISTING_POSITION",
        "BLOCKED_BY_SINGLE_POSITION_CAP",
        "BLOCKED_BY_THEME_EXPOSURE",
        "BLOCKED_BY_HIGH_RISK_EXPOSURE",
        "BLOCKED_BY_ACTIVE_POSITION_LIMIT",
        "BLOCKED_BY_SPECULATIVE_POSITION_LIMIT",
        "BLOCKED_BY_DAILY_NEW_BUY_LIMIT",
    }
    return "\n".join([
        "# V18 Current Account-Aware Manual Trade Plan",
        "",
        "## 1. Final Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Run Id / Timestamp",
        f"RUN_ID: {values.get('RUN_ID', '')}",
        f"GENERATED_AT: {values.get('_GENERATED_AT', '')}",
        "",
        "## 3. Account State Mode And Quality",
        f"- ACCOUNT_STATE_MODE: `{values.get('ACCOUNT_STATE_MODE', '')}`",
        f"- ACCOUNT_STATE_QUALITY_FLAG: `{values.get('ACCOUNT_STATE_QUALITY_FLAG', '')}`",
        f"- {ACCOUNT_NOTE}",
        "",
        "## 4. Account Assumptions",
        f"- Account total value USD: `{values.get('ACCOUNT_TOTAL_VALUE_USD', '')}`",
        f"- Cash USD: `{values.get('CASH_USD', '')}`",
        f"- Reserve required USD: `{values.get('CASH_RESERVE_REQUIRED_USD', '')}`",
        f"- Available cash after reserve USD: `{values.get('AVAILABLE_CASH_AFTER_RESERVE_USD', '')}`",
        f"- Max active positions: `{values.get('MAX_ACTIVE_POSITIONS', '')}`",
        f"- Max speculative positions: `{values.get('MAX_SPECULATIVE_POSITIONS', '')}`",
        f"- Max theme exposure pct: `{values.get('MAX_THEME_EXPOSURE_PCT', '')}`",
        f"- Max high-risk exposure pct: `{values.get('MAX_HIGH_RISK_TOTAL_EXPOSURE_PCT', '')}`",
        "",
        "## 5. Account-Aware Status Counts",
        md_table(counts, ["account_trade_status", "count"], 30),
        "## 6. Today's Account-Eligible Manual Buy Candidates",
        md_table([row for row in rows if row.get("account_trade_status") in {"ACCOUNT_TRADE_ALLOWED", "ACCOUNT_TRADE_SMALL_ONLY"}], candidate_fields, 25),
        "## 7. Blocked By Account Constraints",
        md_table([row for row in rows if row.get("account_trade_status") in blocked_statuses], block_fields, 40),
        "## 8. Preserved Non-Trade Groups",
        "### Watch-Only",
        md_table([row for row in rows if row.get("account_trade_status") == "ACCOUNT_WATCH_ONLY"], block_fields, 20),
        "### Wait-Pullback",
        md_table([row for row in rows if row.get("account_trade_status") == "ACCOUNT_WAIT_PULLBACK"], block_fields, 20),
        "### Review-First",
        md_table([row for row in rows if row.get("account_trade_status") == "ACCOUNT_REVIEW_FIRST"], block_fields, 20),
        "### Cost-Plan Blocked",
        md_table([row for row in rows if row.get("account_trade_status") == "BLOCKED_BY_COST_PLAN"], block_fields, 20),
        "## 9. Current Theme Exposure Summary",
        md_table(theme_rows, ["primary_theme", "current_theme_exposure_pct"], 40),
        "## 10. Safety",
        "- Manual research guidance only.",
        "- No broker connection.",
        "- No order placement.",
        "- Manual account file must be updated by operator.",
        "- `AUTO_TRADE: DISABLED`",
        "- `AUTO_SELL: DISABLED`",
        "- `OFFICIAL_DECISION_IMPACT: NONE`",
        "",
        "## 11. Warnings",
        "\n".join(f"- `{warning}`" for warning in warnings),
        "",
        "## 12. Next Step Recommendation",
        "- R31E Daily Trade Plan Snapshot Ledger.",
        "- R29D/R33A forward validation when future price data exists.",
    ]) + "\n"


def write_outputs(root: Path, values: Dict[str, object], rows: Sequence[Dict[str, object]], account: Dict[str, object], dry_run: bool, notes: str) -> None:
    counts = status_counts(rows)
    for status in [
        "ACCOUNT_TRADE_ALLOWED",
        "ACCOUNT_TRADE_SMALL_ONLY",
        "ACCOUNT_WATCH_ONLY",
        "ACCOUNT_WAIT_PULLBACK",
        "ACCOUNT_REVIEW_FIRST",
        "BLOCKED_BY_CASH",
        "BLOCKED_BY_CASH_RESERVE",
        "BLOCKED_BY_EXISTING_POSITION",
        "BLOCKED_BY_SINGLE_POSITION_CAP",
        "BLOCKED_BY_THEME_EXPOSURE",
        "BLOCKED_BY_HIGH_RISK_EXPOSURE",
        "BLOCKED_BY_ACTIVE_POSITION_LIMIT",
        "BLOCKED_BY_SPECULATIVE_POSITION_LIMIT",
        "BLOCKED_BY_DAILY_NEW_BUY_LIMIT",
        "BLOCKED_BY_COST_PLAN",
        "BLOCKED_BY_ACCOUNT_STATE_QUALITY",
        "BLOCKED_BY_OPERATOR_STATE",
        "BLOCKED_BY_DATA_QUALITY",
    ]:
        values[f"{status}_COUNT"] = counts.get(status, 0)
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    if not dry_run:
        write_csv(root / OUT_PLAN, rows, OUTPUT_FIELDS)
    report = build_report(values, rows, account)
    write_text(root / OUT_CURRENT_REPORT, report)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, notes), SUMMARY_FIELDS)


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31D_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    before = protected_sig(root)

    cost_rows, _cost_fields = read_csv(root / COST_ADJUSTED)
    pos_rows, _pos_fields = read_csv(root / POSITION_POLICY)
    buy_rows, _buy_fields = read_csv(root / BUYABILITY)
    rec_rows, _rec_fields = read_csv(root / RECOMMENDATIONS)
    ranked_rows, _ranked_fields = read_csv(root / RANKED)
    theme_rows, _theme_fields = read_csv(root / THEMES)
    required_missing = [rel for rel in [COST_ADJUSTED, POSITION_POLICY, BUYABILITY, RECOMMENDATIONS, RANKED] if not (root / rel).exists()]
    plan_by_ticker = {upper(row.get("ticker")): row for row in cost_rows}
    account = parse_account_state(root, args, plan_by_ticker, generated_at)
    context = context_values(root, len(cost_rows), len(pos_rows), len(buy_rows), len(rec_rows), len(ranked_rows), len(theme_rows))
    output_rows = [] if required_missing else plan_rows(root, args, cost_rows, account, run_id, generated_at)
    output_rows_for_read_first = len(output_rows) if not args.dry_run else 0
    values: Dict[str, object] = {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "ACCOUNT_STATE_FILE": str(root / ACCOUNT_STATE),
        "ACCOUNT_STATE_MODE": account["mode"],
        "ACCOUNT_STATE_QUALITY_FLAG": account["quality"],
        "ACCOUNT_TOTAL_VALUE_USD": money(float(account["account_total"])),
        "CASH_USD": money(float(account["cash"])),
        "CASH_RESERVE_PCT": pct(args.cash_reserve_pct),
        "CASH_RESERVE_REQUIRED_USD": money(float(account["reserve"])),
        "AVAILABLE_CASH_AFTER_RESERVE_USD": money(float(account["available"])),
        "MAX_ACTIVE_POSITIONS": args.max_active_positions,
        "MAX_SPECULATIVE_POSITIONS": args.max_speculative_positions,
        "MAX_SINGLE_POSITION_PCT": pct(args.max_single_position_pct),
        "MAX_THEME_EXPOSURE_PCT": pct(args.max_theme_exposure_pct),
        "MAX_HIGH_RISK_TOTAL_EXPOSURE_PCT": pct(args.max_high_risk_total_exposure_pct),
        "MAX_NEW_BUYS_PER_DAY": args.max_new_buys_per_day,
        "SOURCE_COST_ADJUSTED_FILE": str(root / COST_ADJUSTED),
        "SOURCE_COST_ADJUSTED_ROWS": len(cost_rows),
        "SOURCE_POSITION_POLICY_FILE": str(root / POSITION_POLICY),
        "SOURCE_POSITION_POLICY_ROWS": len(pos_rows),
        "SOURCE_BUYABILITY_FILE": str(root / BUYABILITY),
        "SOURCE_BUYABILITY_ROWS": len(buy_rows),
        "OUTPUT_ACCOUNT_AWARE_ROWS": output_rows_for_read_first,
        "CURRENT_RANKED_CANDIDATE_ROWS": context["current_ranked"],
        "CURRENT_RECOMMENDATION_ROWS": context["current_recs"],
        "CURRENT_THEME_CLASSIFICATION_ROWS": context["current_themes"],
        "LATEST_FULL_FREEZE_TICKER_COUNT": context["latest_freeze"],
        "R31C_STATUS": context["r31c_status"],
        "R31C_R1_STATUS": context["r31c_r1_status"],
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
    quality = str(account["quality"])
    if required_missing:
        notes = "Missing required inputs: " + "; ".join(required_missing)
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Restore required R31A/R31B/R31C inputs before account-aware planning."
    elif args.dry_run:
        notes = "Dry run only; current account-aware plan CSV not written."
        values["STATUS"] = STATUS_DRY
        values["NEXT_RECOMMENDED_STEP"] = "Run live R31D to generate the account-aware manual plan."
    elif len(cost_rows) != EXPECTED_ROWS or len(pos_rows) != EXPECTED_ROWS or len(buy_rows) != EXPECTED_ROWS or len(output_rows) != args.top_n or not context["structural_ok"]:
        notes = "Structural row count mismatch."
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31A/R31B/R31C structural inputs before using account-aware plan."
    elif quality.startswith("FAIL_"):
        notes = quality
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Fix manual account total value and cash before using account-aware plan."
    elif quality.startswith("WARN_") or values["FORWARD_RETURN_FILLABLE_READY"] == "FALSE":
        notes = ";".join(dict.fromkeys([quality if quality.startswith("WARN_") else "", "FORWARD_RETURN_NOT_READY_ACCOUNT_PLAN_ONLY"])).strip(";")
        values["STATUS"] = STATUS_WARN
        values["NEXT_RECOMMENDED_STEP"] = "Update manual account state before relying on account-aware constraints."
    else:
        notes = "Account-aware manual trade plan ready."
        values["STATUS"] = STATUS_OK
        values["NEXT_RECOMMENDED_STEP"] = "Review account-aware candidates; next planned layer is R31E daily trade plan snapshot ledger."

    after = protected_sig(root)
    values["FORBIDDEN_MODIFIED"] = bool_text(after != before)
    if values["FORBIDDEN_MODIFIED"] != "FALSE":
        values["STATUS"] = STATUS_FAIL
        notes = "Forbidden input modification detected."
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31D error report; do not trade from this run."

    write_outputs(root, values, output_rows, account, args.dry_run, notes)
    if values["STATUS"] == STATUS_FAIL:
        write_text(root / OUT_ERROR_REPORT, f"# V18.31D Account-Aware Manual Trade Plan Error\n\n```text\n{notes}\n```\n")
        return 1, values
    return 0, values


def write_failure(root: Path, error: BaseException, args: argparse.Namespace) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31D_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "ACCOUNT_STATE_FILE": str(root / ACCOUNT_STATE),
        "ACCOUNT_STATE_MODE": "UNKNOWN",
        "ACCOUNT_STATE_QUALITY_FLAG": "FAIL_INVALID_ACCOUNT_TOTAL_VALUE",
        "ACCOUNT_TOTAL_VALUE_USD": money(args.account_size_usd),
        "CASH_USD": money(args.cash_usd if args.cash_usd is not None else args.account_size_usd),
        "CASH_RESERVE_PCT": pct(args.cash_reserve_pct),
        "CASH_RESERVE_REQUIRED_USD": money(0.0),
        "AVAILABLE_CASH_AFTER_RESERVE_USD": money(0.0),
        "MAX_ACTIVE_POSITIONS": args.max_active_positions,
        "MAX_SPECULATIVE_POSITIONS": args.max_speculative_positions,
        "MAX_SINGLE_POSITION_PCT": pct(args.max_single_position_pct),
        "MAX_THEME_EXPOSURE_PCT": pct(args.max_theme_exposure_pct),
        "MAX_HIGH_RISK_TOTAL_EXPOSURE_PCT": pct(args.max_high_risk_total_exposure_pct),
        "MAX_NEW_BUYS_PER_DAY": args.max_new_buys_per_day,
        "SOURCE_COST_ADJUSTED_FILE": str(root / COST_ADJUSTED),
        "SOURCE_COST_ADJUSTED_ROWS": 0,
        "SOURCE_POSITION_POLICY_FILE": str(root / POSITION_POLICY),
        "SOURCE_POSITION_POLICY_ROWS": 0,
        "SOURCE_BUYABILITY_FILE": str(root / BUYABILITY),
        "SOURCE_BUYABILITY_ROWS": 0,
        "OUTPUT_ACCOUNT_AWARE_ROWS": 0,
        "CURRENT_RANKED_CANDIDATE_ROWS": 0,
        "CURRENT_RECOMMENDATION_ROWS": 0,
        "CURRENT_THEME_CLASSIFICATION_ROWS": 0,
        "LATEST_FULL_FREEZE_TICKER_COUNT": 0,
        "R31C_STATUS": "",
        "R31C_R1_STATUS": "",
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
        "NEXT_RECOMMENDED_STEP": "Inspect R31D error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    }
    for status in [
        "ACCOUNT_TRADE_ALLOWED",
        "ACCOUNT_TRADE_SMALL_ONLY",
        "ACCOUNT_WATCH_ONLY",
        "ACCOUNT_WAIT_PULLBACK",
        "ACCOUNT_REVIEW_FIRST",
        "BLOCKED_BY_CASH",
        "BLOCKED_BY_CASH_RESERVE",
        "BLOCKED_BY_EXISTING_POSITION",
        "BLOCKED_BY_SINGLE_POSITION_CAP",
        "BLOCKED_BY_THEME_EXPOSURE",
        "BLOCKED_BY_HIGH_RISK_EXPOSURE",
        "BLOCKED_BY_ACTIVE_POSITION_LIMIT",
        "BLOCKED_BY_SPECULATIVE_POSITION_LIMIT",
        "BLOCKED_BY_DAILY_NEW_BUY_LIMIT",
        "BLOCKED_BY_COST_PLAN",
        "BLOCKED_BY_ACCOUNT_STATE_QUALITY",
        "BLOCKED_BY_OPERATOR_STATE",
        "BLOCKED_BY_DATA_QUALITY",
    ]:
        values[f"{status}_COUNT"] = 0
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    write_csv(root / OUT_SUMMARY, build_summary(values, str(error)), SUMMARY_FIELDS)
    write_text(root / OUT_ERROR_REPORT, f"# V18.31D Account-Aware Manual Trade Plan Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31D account-aware manual trade plan.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--account-size-usd", type=float, default=2000.0)
    parser.add_argument("--cash-usd", type=float, default=None)
    parser.add_argument("--cash-reserve-pct", type=float, default=15.0)
    parser.add_argument("--max-active-positions", type=int, default=8)
    parser.add_argument("--max-speculative-positions", type=int, default=2)
    parser.add_argument("--max-single-position-pct", type=float, default=12.0)
    parser.add_argument("--max-theme-exposure-pct", type=float, default=35.0)
    parser.add_argument("--max-high-risk-total-exposure-pct", type=float, default=25.0)
    parser.add_argument("--max-new-buys-per-day", type=int, default=3)
    parser.add_argument("--min-cash-after-trade-usd", type=float, default=100.0)
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
