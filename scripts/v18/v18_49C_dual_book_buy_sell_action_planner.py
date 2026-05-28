from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


PATCH_VERSION = "V18.49C"
PATCH_NAME = "DUAL_BOOK_BUY_SELL_ACTION_PLANNER"

SIMULATION_COLUMNS = [
    "run_date", "ticker", "rank", "source_policy_style", "primary_policy_id",
    "policy_confidence", "simulation_book_found", "owned_in_simulation",
    "event_risk", "options_risk", "technical_status", "pullback_status",
    "freshness_status", "simulation_action", "action_priority", "reason",
    "max_policy_cap_applied",
]

REAL_COLUMNS = [
    "run_date", "ticker", "rank", "real_position_book_found", "owned_real",
    "real_shares", "avg_cost", "event_risk", "options_risk", "technical_status",
    "pullback_status", "freshness_status", "real_position_advice",
    "advice_priority", "reason", "advice_only", "broker_api_used",
    "order_execution_used",
]

SUMMARY_COLUMNS = [
    "run_date", "simulation_policy_style", "primary_policy_id", "policy_confidence",
    "simulation_action_row_count", "paper_buy_candidate_count",
    "paper_add_review_count", "paper_reduce_review_count", "paper_exit_review_count",
    "real_position_book_found", "real_advice_row_count", "real_new_buy_review_count",
    "real_add_review_count", "real_reduce_review_count", "real_sell_review_count",
    "official_ranking_changed", "factor_weights_changed", "real_trade_execution_allowed",
    "broker_api_used", "order_execution_used",
]

REAL_POSITION_TEMPLATE_COLUMNS = [
    "ticker", "account", "shares", "avg_cost", "current_position_usd",
    "max_position_usd", "target_weight_pct", "do_not_buy", "do_not_sell",
    "notes", "last_review_date",
]


def clean(value: object, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


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
        for row in rows:
            writer.writerow({column: clean(row.get(column), "") for column in fieldnames})


def row_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = clean(row.get("ticker"), "")
        if ticker:
            out[ticker.upper()] = row
    return out


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def parse_int(value: object, default: int = 0) -> int:
    try:
        return int(float(clean(value, str(default))))
    except ValueError:
        return default


def is_true(value: object) -> bool:
    return clean(value, "").upper() == "TRUE"


def risk_level(value: object) -> str:
    text = clean(value, "UNKNOWN").upper()
    if "EXTREME" in text:
        return "EXTREME"
    if "HIGH" in text:
        return "HIGH"
    if "MEDIUM" in text:
        return "MEDIUM"
    if "LOW" in text:
        return "LOW"
    return text


def is_high_risk(value: object) -> bool:
    return risk_level(value) in {"HIGH", "EXTREME"}


def is_stale(row: dict[str, str]) -> bool:
    if clean(row.get("stale_price_data_flag"), "FALSE").upper() == "TRUE":
        return True
    if clean(row.get("actionable_allowed_by_freshness"), "TRUE").upper() == "FALSE":
        return True
    freshness = clean(row.get("freshness_status"), "")
    return "STALE" in freshness.upper() or "MISSING" in freshness.upper()


def technical_deteriorated(technical_status: str) -> bool:
    text = technical_status.upper()
    return any(token in text for token in ["WEAK", "NEGATIVE", "SELL", "DANGER", "BREAKDOWN"])


def get_rank(row: dict[str, str]) -> str:
    return clean(row.get("rank") or row.get("latest_rank") or row.get("freshness_eligible_rank"), "")


def load_policy(path: Path) -> tuple[dict[str, str], bool]:
    rows = read_csv(path)
    return (rows[0], True) if rows else ({}, False)


def load_simulation_book(root: Path) -> tuple[set[str], bool]:
    paths = [
        root / "state/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        root / "state/v18/paper_trading/V18_PAPER_POSITIONS.csv",
        root / "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        root / "outputs/v18/paper_trading/V18_36A_PAPER_POSITIONS_PREVIEW.csv",
    ]
    path = first_existing(paths)
    if path is None:
        return set(), False
    tickers = set()
    for row in read_csv(path):
        ticker = clean(row.get("ticker"), "")
        if ticker:
            tickers.add(ticker.upper())
    return tickers, True


def load_real_book(path: Path) -> tuple[list[dict[str, str]], bool]:
    if not path.exists():
        return [], False
    return read_csv(path), True


def create_real_position_template(path: Path) -> None:
    if path.exists():
        return
    write_csv(path, [], REAL_POSITION_TEMPLATE_COLUMNS)


def build_simulation_plan(
    run_ts: str,
    policy: dict[str, str],
    top_rows: list[dict[str, str]],
    event_by_ticker: dict[str, dict[str, str]],
    options_by_ticker: dict[str, dict[str, str]],
    technical_by_ticker: dict[str, dict[str, str]],
    simulation_tickers: set[str],
    simulation_book_found: bool,
) -> list[dict[str, str]]:
    style = clean(policy.get("simulation_policy_style"), "SIM_DEFENSIVE")
    primary = clean(policy.get("primary_policy_id"), "NONE")
    confidence = clean(policy.get("policy_confidence"), "LOW")
    exit_aggr = clean(policy.get("exit_aggressiveness"), "ACTIVE_REVIEW")
    allow_buys = is_true(policy.get("allow_new_paper_buys"))
    allow_adds = is_true(policy.get("allow_paper_adds"))
    max_buy = parse_int(policy.get("max_paper_buy_count"), 0)
    max_add = parse_int(policy.get("max_paper_add_count"), 0)
    max_reduce = parse_int(policy.get("max_paper_reduce_count"), 0)

    buy_count = 0
    add_count = 0
    reduce_count = 0
    rows: list[dict[str, str]] = []

    for top in top_rows[:20]:
        ticker = clean(top.get("ticker"), "").upper()
        if not ticker:
            continue
        owned = ticker in simulation_tickers
        event = event_by_ticker.get(ticker, {})
        options = options_by_ticker.get(ticker, {})
        technical = technical_by_ticker.get(ticker, {})
        event_risk = risk_level(event.get("final_event_risk_level") or top.get("event_risk_status"))
        options_risk = risk_level(options.get("overall_options_risk_level"))
        technical_status = clean(technical.get("technical_signal") or top.get("technical_status"))
        pullback_status = clean(top.get("pullback_status") or technical.get("bb_status"))
        freshness = clean(top.get("freshness_status") or event.get("freshness_status"))
        reason_parts = [f"INHERITED_POLICY={style}", f"CONFIDENCE={confidence}"]
        cap_applied = "NONE"
        priority = "LOW"

        if is_stale(top):
            action = "PAPER_SKIP_DATA_STALE"
            priority = "LOW"
            reason_parts.append("FRESHNESS_STALE_OR_MISSING")
        elif owned and is_high_risk(event_risk) and reduce_count < max_reduce:
            action = "PAPER_REDUCE_REVIEW"
            reduce_count += 1
            priority = "HIGH"
            cap_applied = f"MAX_PAPER_REDUCE_COUNT={max_reduce}"
            reason_parts.append("EVENT_RISK_HIGH_OR_EXTREME")
        elif owned and is_high_risk(event_risk):
            action = "PAPER_SKIP_POLICY_LIMIT"
            priority = "MEDIUM"
            cap_applied = f"MAX_PAPER_REDUCE_COUNT={max_reduce}"
            reason_parts.append("PAPER_REDUCE_CAP_REACHED")
        elif owned and technical_deteriorated(technical_status) and exit_aggr == "ACTIVE_REVIEW" and reduce_count < max_reduce:
            action = "PAPER_REDUCE_REVIEW"
            reduce_count += 1
            priority = "MEDIUM"
            cap_applied = f"MAX_PAPER_REDUCE_COUNT={max_reduce}"
            reason_parts.append("TECHNICAL_DETERIORATION_ACTIVE_REVIEW")
        elif owned and technical_deteriorated(technical_status) and exit_aggr == "ACTIVE_REVIEW":
            action = "PAPER_EXIT_REVIEW"
            priority = "MEDIUM"
            cap_applied = f"MAX_PAPER_REDUCE_COUNT={max_reduce}"
            reason_parts.append("TECHNICAL_EXIT_REVIEW_CAP_REACHED")
        elif owned and allow_adds and add_count < max_add and not is_high_risk(event_risk):
            action = "PAPER_ADD_REVIEW"
            add_count += 1
            priority = "MEDIUM"
            cap_applied = f"MAX_PAPER_ADD_COUNT={max_add}"
            reason_parts.append("EXISTING_SIM_POSITION_ADD_REVIEW")
        elif owned:
            action = "PAPER_HOLD"
            priority = "LOW"
            reason_parts.append("EXISTING_SIM_POSITION_HOLD")
        elif is_high_risk(event_risk):
            action = "PAPER_SKIP_RISK"
            priority = "LOW"
            reason_parts.append("EVENT_RISK_HIGH_OR_EXTREME")
        elif allow_buys and buy_count < max_buy:
            action = "PAPER_BUY_CANDIDATE"
            buy_count += 1
            priority = "MEDIUM"
            cap_applied = f"MAX_PAPER_BUY_COUNT={max_buy}"
            reason_parts.append("TOP20_CANDIDATE_WITHIN_POLICY_CAP")
        else:
            action = "PAPER_SKIP_POLICY_LIMIT"
            priority = "LOW"
            cap_applied = f"MAX_PAPER_BUY_COUNT={max_buy}"
            reason_parts.append("PAPER_BUY_CAP_REACHED_OR_BUYS_DISABLED")

        if is_high_risk(options_risk):
            reason_parts.append("OPTIONS_RISK_CAUTION_ONLY_NOT_PROMOTED_BY_V18_49B_R1")

        rows.append({
            "run_date": run_ts,
            "ticker": ticker,
            "rank": get_rank(top),
            "source_policy_style": style,
            "primary_policy_id": primary,
            "policy_confidence": confidence,
            "simulation_book_found": "TRUE" if simulation_book_found else "FALSE",
            "owned_in_simulation": "TRUE" if owned else "FALSE",
            "event_risk": event_risk,
            "options_risk": options_risk,
            "technical_status": technical_status,
            "pullback_status": pullback_status,
            "freshness_status": freshness,
            "simulation_action": action,
            "action_priority": priority,
            "reason": ";".join(reason_parts),
            "max_policy_cap_applied": cap_applied,
        })
    return rows


def real_position_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = clean(row.get("ticker"), "").upper()
        if ticker:
            out[ticker] = row
    return out


def build_real_plan(
    run_ts: str,
    top_rows: list[dict[str, str]],
    real_rows: list[dict[str, str]],
    real_book_found: bool,
    event_by_ticker: dict[str, dict[str, str]],
    options_by_ticker: dict[str, dict[str, str]],
    technical_by_ticker: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    real_by_ticker = real_position_lookup(real_rows)
    top_by_ticker = row_by_ticker(top_rows)
    tickers = list(dict.fromkeys([clean(row.get("ticker"), "").upper() for row in top_rows[:20] if clean(row.get("ticker"), "")]))
    for ticker in real_by_ticker:
        if ticker not in tickers:
            tickers.append(ticker)

    rows: list[dict[str, str]] = []
    for ticker in tickers:
        top = top_by_ticker.get(ticker, {})
        real = real_by_ticker.get(ticker, {})
        owned = bool(real)
        event = event_by_ticker.get(ticker, {})
        options = options_by_ticker.get(ticker, {})
        technical = technical_by_ticker.get(ticker, {})
        event_risk = risk_level(event.get("final_event_risk_level") or top.get("event_risk_status"))
        options_risk = risk_level(options.get("overall_options_risk_level"))
        technical_status = clean(technical.get("technical_signal") or top.get("technical_status"))
        pullback_status = clean(top.get("pullback_status") or technical.get("bb_status"))
        freshness = clean(top.get("freshness_status") or event.get("freshness_status"))
        reason = ["ADVICE_ONLY_NO_BROKER_NO_ORDER", "REAL_BOOK_SEPARATED_FROM_SIMULATION"]
        priority = "LOW"

        if not real_book_found:
            advice = "REAL_POSITION_DATA_MISSING"
            reason.append("REAL_POSITION_BOOK_MISSING")
        elif is_stale(top):
            advice = "REAL_NO_ACTION_DATA_STALE"
            reason.append("FRESHNESS_STALE_OR_MISSING")
        elif owned and is_true(real.get("do_not_sell")):
            advice = "REAL_HOLD_ADVICE"
            reason.append("USER_DO_NOT_SELL_FLAG")
        elif owned and is_high_risk(event_risk):
            advice = "REAL_NO_ACTION_EVENT_RISK"
            priority = "HIGH"
            reason.append("EVENT_RISK_HIGH_OR_EXTREME_MANUAL_REVIEW")
        elif owned and is_high_risk(options_risk):
            advice = "REAL_NO_ACTION_OPTIONS_RISK"
            priority = "MEDIUM"
            reason.append("OPTIONS_RISK_HIGH_OR_EXTREME_CAUTION_ONLY")
        elif owned and technical_deteriorated(technical_status):
            advice = "REAL_REDUCE_REVIEW"
            priority = "MEDIUM"
            reason.append("TECHNICAL_DETERIORATION_REVIEW_ONLY")
        elif owned:
            advice = "REAL_HOLD_ADVICE"
            reason.append("OWNED_REAL_HOLD_REVIEW_ONLY")
        elif is_true(real.get("do_not_buy")):
            advice = "REAL_MANUAL_REVIEW_REQUIRED"
            reason.append("USER_DO_NOT_BUY_FLAG")
        elif is_high_risk(event_risk):
            advice = "REAL_NO_ACTION_EVENT_RISK"
            reason.append("EVENT_RISK_HIGH_OR_EXTREME")
        elif is_high_risk(options_risk):
            advice = "REAL_NO_ACTION_OPTIONS_RISK"
            reason.append("OPTIONS_RISK_HIGH_OR_EXTREME_CAUTION_ONLY")
        else:
            advice = "REAL_NEW_BUY_REVIEW"
            priority = "MEDIUM"
            reason.append("NON_HELD_TOP20_REVIEW_ONLY_NOT_BUY_INSTRUCTION")

        rows.append({
            "run_date": run_ts,
            "ticker": ticker,
            "rank": get_rank(top),
            "real_position_book_found": "TRUE" if real_book_found else "FALSE",
            "owned_real": "TRUE" if owned else "FALSE",
            "real_shares": clean(real.get("shares"), "0") if owned else "0",
            "avg_cost": clean(real.get("avg_cost"), "") if owned else "",
            "event_risk": event_risk,
            "options_risk": options_risk,
            "technical_status": technical_status,
            "pullback_status": pullback_status,
            "freshness_status": freshness,
            "real_position_advice": advice,
            "advice_priority": priority,
            "reason": ";".join(reason),
            "advice_only": "TRUE",
            "broker_api_used": "FALSE",
            "order_execution_used": "FALSE",
        })
    return rows


def count(rows: list[dict[str, str]], column: str, value: str) -> int:
    return sum(1 for row in rows if row.get(column) == value)


def status_for(source_found: bool, top_found: bool, policy: dict[str, str], simulation_book_found: bool, real_book_found: bool) -> str:
    if not source_found or not top_found:
        return "FAIL_V18_49C_CRITICAL_SOURCE_MISSING"
    if clean(policy.get("policy_confidence")) == "LOW":
        return "WARN_V18_49C_SOURCE_POLICY_LOW_CONFIDENCE"
    if not real_book_found:
        return "WARN_V18_49C_REAL_POSITION_BOOK_MISSING"
    if not simulation_book_found:
        return "WARN_V18_49C_SIMULATION_BOOK_MISSING"
    return "PASS"


def build_report(summary: dict[str, str], sim_rows: list[dict[str, str]], real_rows: list[dict[str, str]], real_book_found: bool) -> str:
    sim_preview = sim_rows[:10]
    real_preview = real_rows[:10]
    return "\n".join([
        "# V18.49C Dual-Book Buy/Sell Action Planner",
        "",
        "V18.49C is a read-only sidecar. It inherits V18.49B-R1 simulation policy and keeps simulation-paper actions strictly separate from real-position advice.",
        "",
        "## Source Policy",
        f"- Simulation policy style: {summary['simulation_policy_style']}",
        f"- Primary policy: {summary['primary_policy_id']}",
        f"- Policy confidence: {summary['policy_confidence']}",
        "",
        "## Simulation / Paper Book",
        f"- Rows: {summary['simulation_action_row_count']}",
        f"- Buy candidates: {summary['paper_buy_candidate_count']}",
        f"- Add reviews: {summary['paper_add_review_count']}",
        f"- Reduce reviews: {summary['paper_reduce_review_count']}",
        f"- Exit reviews: {summary['paper_exit_review_count']}",
        "",
        markdown_table(sim_preview, ["ticker", "rank", "simulation_action", "event_risk", "options_risk", "reason"]) if sim_preview else "No simulation rows generated.",
        "",
        "## Real-Position Advice Only",
        f"- Real position book found: {'TRUE' if real_book_found else 'FALSE'}",
        f"- Advice rows: {summary['real_advice_row_count']}",
        "This is advice only. No broker API used. No order generated. User must manually decide.",
        "",
        markdown_table(real_preview, ["ticker", "rank", "real_position_advice", "event_risk", "options_risk", "reason"]) if real_preview else "No real advice rows generated.",
        "",
        "## Safety",
        "Official ranking, factor weights, Top20 selection, candidate scoring, official buy/sell permissions, real positions, broker APIs, and order execution are unchanged.",
        "",
    ]) + "\n"


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
    return "\n".join(lines)


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "SOURCE_V18_49B_FOUND",
        "SOURCE_SIMULATION_POLICY_STYLE", "SOURCE_PRIMARY_POLICY_ID", "SOURCE_SECONDARY_POLICY_ID",
        "SOURCE_POLICY_CONFIDENCE", "SOURCE_ENTRY_AGGRESSIVENESS", "SOURCE_EXIT_AGGRESSIVENESS",
        "SOURCE_MAX_PAPER_BUY_COUNT", "SOURCE_MAX_PAPER_ADD_COUNT", "SOURCE_MAX_PAPER_REDUCE_COUNT",
        "CURRENT_TOP20_FOUND", "SIMULATION_BOOK_FOUND", "REAL_POSITION_BOOK_FOUND",
        "REAL_POSITION_TEMPLATE_CREATED", "SIMULATION_ACTION_ROW_COUNT", "PAPER_BUY_CANDIDATE_COUNT",
        "PAPER_ADD_REVIEW_COUNT", "PAPER_REDUCE_REVIEW_COUNT", "PAPER_EXIT_REVIEW_COUNT",
        "REAL_POSITION_ADVICE_ROW_COUNT", "REAL_NEW_BUY_REVIEW_COUNT", "REAL_ADD_REVIEW_COUNT",
        "REAL_REDUCE_REVIEW_COUNT", "REAL_SELL_REVIEW_COUNT", "CURRENT_ALIAS_WRITTEN",
        "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED",
        "OFFICIAL_SELL_PERMISSION_CHANGED", "REAL_TRADE_EXECUTION_ALLOWED",
        "OPTIONS_TRADE_EXECUTION_ALLOWED", "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE",
        "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only V18.49C dual-book action planner.")
    parser.add_argument("--root", "--project-root", dest="root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--create-real-position-template", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_ts = datetime.now().astimezone().isoformat(timespec="seconds")

    policy, source_found = load_policy(root / "outputs/v18/action_plan/V18_49B_SIMULATION_POLICY_DECISION.csv")
    top_rows = read_csv(root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv")
    top_found = bool(top_rows)
    event_by_ticker = row_by_ticker(read_csv(root / "outputs/v18/event_risk/V18_47C_TOP20_EVENT_EARNINGS_RISK.csv"))
    options_by_ticker = row_by_ticker(read_csv(root / "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_RADAR.csv"))
    technical_path = first_existing([
        root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        root / "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv",
    ])
    technical_by_ticker = row_by_ticker(read_csv(technical_path)) if technical_path else {}
    simulation_tickers, simulation_book_found = load_simulation_book(root)
    real_book_path = root / "state/v18/manual/V18_REAL_POSITION_BOOK.csv"
    real_rows, real_book_found = load_real_book(real_book_path)

    template_created = False
    if args.create_real_position_template:
        template_path = root / "state/v18/manual/V18_REAL_POSITION_BOOK_TEMPLATE.csv"
        existed = template_path.exists()
        create_real_position_template(template_path)
        template_created = not existed and template_path.exists()

    sim_rows = build_simulation_plan(
        run_ts, policy, top_rows, event_by_ticker, options_by_ticker,
        technical_by_ticker, simulation_tickers, simulation_book_found,
    ) if source_found and top_found else []
    real_plan_rows = build_real_plan(
        run_ts, top_rows, real_rows, real_book_found, event_by_ticker,
        options_by_ticker, technical_by_ticker,
    ) if top_found else []

    summary = {
        "run_date": run_ts,
        "simulation_policy_style": clean(policy.get("simulation_policy_style")),
        "primary_policy_id": clean(policy.get("primary_policy_id")),
        "policy_confidence": clean(policy.get("policy_confidence")),
        "simulation_action_row_count": str(len(sim_rows)),
        "paper_buy_candidate_count": str(count(sim_rows, "simulation_action", "PAPER_BUY_CANDIDATE")),
        "paper_add_review_count": str(count(sim_rows, "simulation_action", "PAPER_ADD_REVIEW")),
        "paper_reduce_review_count": str(count(sim_rows, "simulation_action", "PAPER_REDUCE_REVIEW")),
        "paper_exit_review_count": str(count(sim_rows, "simulation_action", "PAPER_EXIT_REVIEW")),
        "real_position_book_found": "TRUE" if real_book_found else "FALSE",
        "real_advice_row_count": str(len(real_plan_rows)),
        "real_new_buy_review_count": str(count(real_plan_rows, "real_position_advice", "REAL_NEW_BUY_REVIEW")),
        "real_add_review_count": str(count(real_plan_rows, "real_position_advice", "REAL_ADD_REVIEW")),
        "real_reduce_review_count": str(count(real_plan_rows, "real_position_advice", "REAL_REDUCE_REVIEW")),
        "real_sell_review_count": str(count(real_plan_rows, "real_position_advice", "REAL_SELL_REVIEW")),
        "official_ranking_changed": "FALSE",
        "factor_weights_changed": "FALSE",
        "real_trade_execution_allowed": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }

    out_dir = root / "outputs/v18/action_plan"
    write_csv(out_dir / "V18_49C_SIMULATION_ACTION_PLAN.csv", sim_rows, SIMULATION_COLUMNS)
    write_csv(out_dir / "V18_49C_REAL_POSITION_ADVICE_PLAN.csv", real_plan_rows, REAL_COLUMNS)
    write_csv(out_dir / "V18_49C_DUAL_BOOK_ACTION_SUMMARY.csv", [summary], SUMMARY_COLUMNS)

    report = build_report(summary, sim_rows, real_plan_rows, real_book_found)
    report_path = root / "outputs/v18/read_center/V18_49C_DUAL_BOOK_ACTION_PLAN_REPORT.md"
    current_path = root / "outputs/v18/read_center/V18_CURRENT_DUAL_BOOK_ACTION_PLAN.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_written = False
    if args.write_current:
        current_path.write_text(report, encoding="utf-8")
        current_written = True

    status = status_for(source_found, top_found, policy, simulation_book_found, real_book_found)
    notes = [
        "READ_ONLY_DUAL_BOOK_PLANNER",
        "SIMULATION_AND_REAL_ADVICE_SEPARATED",
        "NO_BACKTEST_NO_RANKING_WEIGHT_PERMISSION_POSITION_BROKER_ORDER_OR_TRADING_CHANGES",
    ]
    if not real_book_found:
        notes.append("REAL_POSITION_BOOK_MISSING")
    if clean(policy.get("policy_confidence")) == "LOW":
        notes.append("SOURCE_POLICY_LOW_CONFIDENCE")

    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "SOURCE_V18_49B_FOUND": "TRUE" if source_found else "FALSE",
        "SOURCE_SIMULATION_POLICY_STYLE": clean(policy.get("simulation_policy_style")),
        "SOURCE_PRIMARY_POLICY_ID": clean(policy.get("primary_policy_id")),
        "SOURCE_SECONDARY_POLICY_ID": clean(policy.get("secondary_policy_id")),
        "SOURCE_POLICY_CONFIDENCE": clean(policy.get("policy_confidence")),
        "SOURCE_ENTRY_AGGRESSIVENESS": clean(policy.get("entry_aggressiveness")),
        "SOURCE_EXIT_AGGRESSIVENESS": clean(policy.get("exit_aggressiveness")),
        "SOURCE_MAX_PAPER_BUY_COUNT": clean(policy.get("max_paper_buy_count"), "0"),
        "SOURCE_MAX_PAPER_ADD_COUNT": clean(policy.get("max_paper_add_count"), "0"),
        "SOURCE_MAX_PAPER_REDUCE_COUNT": clean(policy.get("max_paper_reduce_count"), "0"),
        "CURRENT_TOP20_FOUND": "TRUE" if top_found else "FALSE",
        "SIMULATION_BOOK_FOUND": "TRUE" if simulation_book_found else "FALSE",
        "REAL_POSITION_BOOK_FOUND": "TRUE" if real_book_found else "FALSE",
        "REAL_POSITION_TEMPLATE_CREATED": "TRUE" if template_created else "FALSE",
        "SIMULATION_ACTION_ROW_COUNT": str(len(sim_rows)),
        "PAPER_BUY_CANDIDATE_COUNT": summary["paper_buy_candidate_count"],
        "PAPER_ADD_REVIEW_COUNT": summary["paper_add_review_count"],
        "PAPER_REDUCE_REVIEW_COUNT": summary["paper_reduce_review_count"],
        "PAPER_EXIT_REVIEW_COUNT": summary["paper_exit_review_count"],
        "REAL_POSITION_ADVICE_ROW_COUNT": str(len(real_plan_rows)),
        "REAL_NEW_BUY_REVIEW_COUNT": summary["real_new_buy_review_count"],
        "REAL_ADD_REVIEW_COUNT": summary["real_add_review_count"],
        "REAL_REDUCE_REVIEW_COUNT": summary["real_reduce_review_count"],
        "REAL_SELL_REVIEW_COUNT": summary["real_sell_review_count"],
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
        "VALIDATION_NOTES": ";".join(notes),
    }
    write_read_first(root / "outputs/v18/ops/V18_49C_READ_FIRST.txt", values)

    print(f"STATUS: {status}")
    print(f"SIMULATION_POLICY_STYLE: {values['SOURCE_SIMULATION_POLICY_STYLE']}")
    print(f"PRIMARY_POLICY_ID: {values['SOURCE_PRIMARY_POLICY_ID']}")
    print(f"POLICY_CONFIDENCE: {values['SOURCE_POLICY_CONFIDENCE']}")
    print(f"SIMULATION_ACTION_ROW_COUNT: {values['SIMULATION_ACTION_ROW_COUNT']}")
    print(f"REAL_POSITION_ADVICE_ROW_COUNT: {values['REAL_POSITION_ADVICE_ROW_COUNT']}")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
