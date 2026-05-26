from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
import json
from pathlib import Path

import pandas as pd

from qutumn.common.paths import CONFIGS_V16, OUTPUTS_V16, ensure_dir
from qutumn.common.config_io import load_yaml_like
from qutumn.backtest.strategy_lab import collect_strategy_records
from qutumn.data.historical_prices import load_price_matrix


@dataclass
class ExecutionRow:
    ticker: str
    strategy_name: str
    research_decision: str
    permission: str
    role: str
    current_price_usd: float | None
    last_price_date: str
    price_freshness_status: str
    anchor_high_60d: float | None
    trial_price_usd: float | None
    normal_price_usd: float | None
    deep_price_usd: float | None
    triggered_level: str
    one_share_cost_jpy: float | None
    affordable_1_share: bool
    suggested_shares_trial: int
    suggested_cash_jpy_trial: float
    action_status: str
    reason: str


@dataclass
class TickerSummaryRow:
    ticker: str
    best_action_status: str
    best_triggered_level: str
    current_price_usd: float | None
    last_price_date: str
    price_freshness_status: str
    trial_price_usd: float | None
    normal_price_usd: float | None
    deep_price_usd: float | None
    affordable_1_share: bool
    one_share_cost_jpy: float | None
    suggested_shares_trial: int
    suggested_cash_jpy_trial: float
    strategies: str
    role: str
    reason: str


def _safe_float(value: object, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: object, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _round_price(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _load_execution_config() -> dict:
    path = CONFIGS_V16 / "execution" / "execution_config.yaml"
    if not path.exists():
        return {}
    return load_yaml_like(path)


def _load_grade_rows() -> list[dict]:
    path = OUTPUTS_V16 / "backtest" / "V16_STRATEGY_GRADE.csv"
    if not path.exists():
        return []

    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _strategy_role(strategy_name: str, ticker: str) -> str:
    leveraged = {"TQQQ", "SOXL"}
    core_etf = {"QQQ", "XLK", "SMH", "SOXX"}

    if ticker in leveraged:
        return "TACTICAL_LEVERAGED_ETF"

    if ticker in core_etf:
        if strategy_name in {"pullback_balanced", "defensive_cash", "momentum_core"}:
            return "CORE_ETF"
        return "CORE_OR_EVENT_ETF"

    return "SINGLE_STOCK_SATELLITE"


def _permission_from_decision(decision: str) -> str:
    if decision == "BACKTEST_PASS_CANDIDATE":
        return "PLAN_ALLOWED"
    if decision.startswith("WATCH"):
        return "WATCH_ONLY"
    if decision.startswith("REJECTED"):
        return "DISABLED"
    return "WATCH_ONLY"


def _price_freshness_status(last_price_date: str) -> str:
    if not last_price_date:
        return "NO_PRICE"

    try:
        d = pd.to_datetime(last_price_date).date()
        today = datetime.now().date()
        age_days = (today - d).days

        if age_days <= 2:
            return "FRESH"
        if age_days <= 5:
            return "STALE_REVIEW"
        return "STALE_BLOCK"
    except Exception:
        return "UNKNOWN"


def _triggered_level(current: float | None, trial: float | None, normal: float | None, deep: float | None) -> str:
    if current is None:
        return "NO_PRICE"

    if deep is not None and current <= deep:
        return "DEEP"
    if normal is not None and current <= normal:
        return "NORMAL"
    if trial is not None and current <= trial:
        return "TRIAL"

    return "NONE"


def _build_price_record_map(price_records: list) -> dict[str, object]:
    result: dict[str, object] = {}

    for record in price_records:
        ticker = str(getattr(record, "ticker", "")).upper()
        if ticker:
            result[ticker] = record

    return result


def _build_price_stats(
    prices: pd.DataFrame,
    ticker: str,
    anchor_window: int,
    price_record_map: dict[str, object],
) -> tuple[float | None, str, float | None, str]:
    ticker = ticker.upper()

    if ticker not in prices.columns:
        return None, "", None, "NO_COLUMN"

    s = prices[ticker].dropna().sort_index()

    if s.empty:
        return None, "", None, "EMPTY_SERIES"

    record = price_record_map.get(ticker)
    true_last_date = str(getattr(record, "last_date", "")) if record is not None else ""

    provenance_status = "MATRIX_DATE"

    if true_last_date:
        try:
            cutoff = pd.to_datetime(true_last_date)
            trimmed = s[s.index <= cutoff]

            if not trimmed.empty:
                s = trimmed
                provenance_status = "TRUE_SOURCE_DATE"
        except Exception:
            provenance_status = "TRUE_DATE_PARSE_FAILED"

    current = float(s.iloc[-1])
    last_date = str(s.index[-1].date())
    anchor_high = float(s.tail(anchor_window).max()) if len(s) > 0 else None

    return current, last_date, anchor_high, provenance_status


def _estimate_one_share_cost_jpy(price_usd: float | None, fx: float, safety_buffer_pct: float, cash_buffer_jpy: float) -> float | None:
    if price_usd is None:
        return None

    return round(float(price_usd) * fx * (1.0 + safety_buffer_pct) + cash_buffer_jpy, 2)


def _suggest_trial_shares(
    permission: str,
    freshness: str,
    triggered: str,
    affordable: bool,
    one_share_cost_jpy: float | None,
    planning_cash_jpy: float,
) -> tuple[int, float]:
    if permission != "PLAN_ALLOWED":
        return 0, 0.0

    if freshness != "FRESH":
        return 0, 0.0

    if triggered not in {"TRIAL", "NORMAL", "DEEP"}:
        return 0, 0.0

    if not affordable or one_share_cost_jpy is None:
        return 0, 0.0

    max_trial_budget = planning_cash_jpy * 0.10

    if triggered == "NORMAL":
        max_trial_budget = planning_cash_jpy * 0.15
    elif triggered == "DEEP":
        max_trial_budget = planning_cash_jpy * 0.20

    shares = int(max_trial_budget // one_share_cost_jpy)

    if shares < 1:
        shares = 1 if one_share_cost_jpy <= planning_cash_jpy * 0.25 else 0

    cash = round(shares * one_share_cost_jpy, 2)

    return shares, cash


def _action_status(permission: str, freshness: str, triggered: str, affordable: bool, shares: int) -> tuple[str, str]:
    if permission == "DISABLED":
        return "DISABLED", "Strategy is disabled by research decision."

    if permission == "WATCH_ONLY":
        return "WATCH_ONLY", "Strategy is not allowed to generate execution plan yet."

    if freshness == "STALE_BLOCK":
        return "BLOCKED_STALE_PRICE", "Price data is too stale for execution planning."

    if freshness == "STALE_REVIEW":
        if triggered in {"TRIAL", "NORMAL", "DEEP"}:
            return "STALE_REVIEW_TRIGGERED", "Trigger reached only on stale true-source price. Observation only, not executable."
        return "STALE_REVIEW_ONLY", "True-source price is stale. Observation only."

    if freshness in {"NO_PRICE", "UNKNOWN"}:
        return "BLOCKED_NO_PRICE", "No usable true-source price data."

    if triggered == "NONE":
        return "WAIT_TRIGGER", "No trial/normal/deep trigger is reached."

    if not affordable:
        return "BLOCKED_TOO_EXPENSIVE", "One share is not affordable under small-account constraints."

    if shares <= 0:
        return "PLAN_ONLY_NO_SIZE", "Trigger reached but no valid trial size under current budget rules."

    return "PLAN_ONLY_TRIGGERED", "Fresh true-source price trigger reached. Plan-only candidate, not live order approval."


def _action_rank(action: str) -> int:
    rank = {
        "PLAN_ONLY_TRIGGERED": 100,
        "STALE_REVIEW_TRIGGERED": 80,
        "WAIT_TRIGGER": 60,
        "STALE_REVIEW_ONLY": 50,
        "WATCH_ONLY": 40,
        "PLAN_ONLY_NO_SIZE": 30,
        "BLOCKED_TOO_EXPENSIVE": 20,
        "BLOCKED_STALE_PRICE": 10,
        "BLOCKED_NO_PRICE": 5,
        "DISABLED": 0,
    }
    return rank.get(action, 0)


def _role_rank(role: str) -> int:
    rank = {
        "CORE_ETF": 100,
        "CORE_OR_EVENT_ETF": 80,
        "SINGLE_STOCK_SATELLITE": 60,
        "TACTICAL_LEVERAGED_ETF": 40,
    }
    return rank.get(role, 0)


def build_execution_plan() -> tuple[list[ExecutionRow], list, dict[str, str]]:
    cfg = _load_execution_config()

    capital = cfg.get("capital", {})
    if not isinstance(capital, dict):
        capital = {}

    rakuten_rules = cfg.get("rakuten_rules", {})
    if not isinstance(rakuten_rules, dict):
        rakuten_rules = {}

    trigger_policy = cfg.get("trigger_policy", {})
    if not isinstance(trigger_policy, dict):
        trigger_policy = {}

    planning_cash_jpy = _safe_float(capital.get("planning_cash_jpy"), 200000.0)
    fx_rate = _safe_float(capital.get("fx_rate_jpy_per_usd"), 155.0)

    cash_buffer_jpy = _safe_float(rakuten_rules.get("cash_buffer_jpy"), 500.0)
    safety_buffer_pct = _safe_float(rakuten_rules.get("price_safety_buffer_pct"), 0.02)

    anchor_window = _safe_int(trigger_policy.get("anchor_window_days"), 60)
    trial_pct = _safe_float(trigger_policy.get("default_trial_pullback_pct"), 0.03)
    normal_pct = _safe_float(trigger_policy.get("default_normal_pullback_pct"), 0.06)
    deep_pct = _safe_float(trigger_policy.get("default_deep_pullback_pct"), 0.10)

    grade_rows = _load_grade_rows()
    grade_by_strategy = {row.get("strategy_name", ""): row for row in grade_rows}

    strategy_records = collect_strategy_records()

    all_tickers: list[str] = []
    for record in strategy_records:
        all_tickers.extend(record.tickers)
    all_tickers = list(dict.fromkeys([ticker.upper() for ticker in all_tickers]))

    price_result = load_price_matrix(
        tickers=all_tickers,
        lookback_days=max(260, anchor_window + 10),
        allow_yfinance_download=True,
    )

    price_record_map = _build_price_record_map(price_result.records)
    provenance_by_ticker: dict[str, str] = {}

    rows: list[ExecutionRow] = []

    for record in strategy_records:
        grade = grade_by_strategy.get(record.strategy_name, {})
        decision = str(grade.get("research_decision", "WATCH"))
        permission = _permission_from_decision(decision)

        for ticker in record.tickers:
            ticker = ticker.upper()

            current, last_date, anchor_high, provenance_status = _build_price_stats(
                prices=price_result.prices,
                ticker=ticker,
                anchor_window=anchor_window,
                price_record_map=price_record_map,
            )

            provenance_by_ticker[ticker] = provenance_status

            freshness = _price_freshness_status(last_date)

            trial = anchor_high * (1.0 - trial_pct) if anchor_high is not None else None
            normal = anchor_high * (1.0 - normal_pct) if anchor_high is not None else None
            deep = anchor_high * (1.0 - deep_pct) if anchor_high is not None else None

            triggered = _triggered_level(current, trial, normal, deep)
            one_share_cost = _estimate_one_share_cost_jpy(current, fx_rate, safety_buffer_pct, cash_buffer_jpy)

            affordable = False
            if one_share_cost is not None:
                affordable = one_share_cost <= planning_cash_jpy * 0.25

            shares, cash = _suggest_trial_shares(
                permission=permission,
                freshness=freshness,
                triggered=triggered,
                affordable=affordable,
                one_share_cost_jpy=one_share_cost,
                planning_cash_jpy=planning_cash_jpy,
            )

            action, reason = _action_status(permission, freshness, triggered, affordable, shares)

            rows.append(
                ExecutionRow(
                    ticker=ticker,
                    strategy_name=record.strategy_name,
                    research_decision=decision,
                    permission=permission,
                    role=_strategy_role(record.strategy_name, ticker),
                    current_price_usd=_round_price(current),
                    last_price_date=last_date,
                    price_freshness_status=freshness,
                    anchor_high_60d=_round_price(anchor_high),
                    trial_price_usd=_round_price(trial),
                    normal_price_usd=_round_price(normal),
                    deep_price_usd=_round_price(deep),
                    triggered_level=triggered,
                    one_share_cost_jpy=one_share_cost,
                    affordable_1_share=affordable,
                    suggested_shares_trial=shares,
                    suggested_cash_jpy_trial=cash,
                    action_status=action,
                    reason=reason,
                )
            )

    return rows, price_result.records, provenance_by_ticker


def build_ticker_summary(rows: list[ExecutionRow]) -> list[TickerSummaryRow]:
    by_ticker: dict[str, list[ExecutionRow]] = {}

    for row in rows:
        by_ticker.setdefault(row.ticker, []).append(row)

    summary: list[TickerSummaryRow] = []

    for ticker, ticker_rows in sorted(by_ticker.items()):
        best = sorted(
            ticker_rows,
            key=lambda r: (_action_rank(r.action_status), _role_rank(r.role)),
            reverse=True,
        )[0]

        strategies = sorted(set(r.strategy_name for r in ticker_rows))
        roles = sorted(set(r.role for r in ticker_rows), key=lambda role: _role_rank(role), reverse=True)

        summary.append(
            TickerSummaryRow(
                ticker=ticker,
                best_action_status=best.action_status,
                best_triggered_level=best.triggered_level,
                current_price_usd=best.current_price_usd,
                last_price_date=best.last_price_date,
                price_freshness_status=best.price_freshness_status,
                trial_price_usd=best.trial_price_usd,
                normal_price_usd=best.normal_price_usd,
                deep_price_usd=best.deep_price_usd,
                affordable_1_share=best.affordable_1_share,
                one_share_cost_jpy=best.one_share_cost_jpy,
                suggested_shares_trial=best.suggested_shares_trial,
                suggested_cash_jpy_trial=best.suggested_cash_jpy_trial,
                strategies=";".join(strategies),
                role=roles[0] if roles else "",
                reason=best.reason,
            )
        )

    return summary


def _write_csv(path: Path, rows: list, fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_execution_plan(rows: list[ExecutionRow], price_records: list, provenance_by_ticker: dict[str, str]) -> tuple[Path, Path, Path, Path, Path, Path]:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_dir = ensure_dir(OUTPUTS_V16 / "execution")

    csv_path = out_dir / "V16_EXECUTION_PLAN.csv"
    md_path = out_dir / "V16_EXECUTION_PLAN.md"
    audit_path = out_dir / "V16_EXECUTION_AUDIT.md"
    json_path = out_dir / "V16_EXECUTION_PLAN.json"
    summary_csv_path = out_dir / "V16_EXECUTION_TICKER_SUMMARY.csv"
    summary_md_path = out_dir / "V16_EXECUTION_TICKER_SUMMARY.md"

    _write_csv(csv_path, rows, list(ExecutionRow.__dataclass_fields__.keys()))

    ticker_summary = build_ticker_summary(rows)
    _write_csv(summary_csv_path, ticker_summary, list(TickerSummaryRow.__dataclass_fields__.keys()))

    action_counts: dict[str, int] = {}
    freshness_counts: dict[str, int] = {}

    for row in rows:
        action_counts[row.action_status] = action_counts.get(row.action_status, 0) + 1
        freshness_counts[row.price_freshness_status] = freshness_counts.get(row.price_freshness_status, 0) + 1

    fresh_triggered_rows = [row for row in rows if row.action_status == "PLAN_ONLY_TRIGGERED"]
    stale_triggered_rows = [row for row in rows if row.action_status == "STALE_REVIEW_TRIGGERED"]
    wait_rows = [row for row in rows if row.action_status == "WAIT_TRIGGER"]
    blocked_rows = [row for row in rows if row.action_status.startswith("BLOCKED")]

    lines: list[str] = []
    lines.append("# V16 Execution Plan")
    lines.append("")
    lines.append(f"生成时间：`{generated_at}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append("V16.3C 已经修正价格日期溯源问题。")
    lines.append("")
    lines.append("现在 Execution Plan 使用每个 ticker 的真实 source last_date，不再被 price matrix 的 ffill 日期污染。")
    lines.append("")
    lines.append("只有价格状态为 FRESH 的触发，才允许显示为 PLAN_ONLY_TRIGGERED。")
    lines.append("STALE_REVIEW 下的触发全部降级为 STALE_REVIEW_TRIGGERED，只能观察，不能下单。")
    lines.append("")
    lines.append("重要限制：当前仍然是 PLAN_ONLY，不是实盘下单指令。")
    lines.append("")
    lines.append("## 2. Action Summary")
    lines.append("")
    lines.append("| action_status | count |")
    lines.append("|---|---:|")
    for key in sorted(action_counts):
        lines.append(f"| `{key}` | `{action_counts[key]}` |")

    lines.append("")
    lines.append("## 3. FRESH 已触发计划候选")
    lines.append("")
    if fresh_triggered_rows:
        lines.append("| ticker | strategy | level | price | trial | normal | deep | shares | cash_jpy | reason |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
        for row in fresh_triggered_rows:
            lines.append(f"| `{row.ticker}` | `{row.strategy_name}` | `{row.triggered_level}` | `{row.current_price_usd}` | `{row.trial_price_usd}` | `{row.normal_price_usd}` | `{row.deep_price_usd}` | `{row.suggested_shares_trial}` | `{row.suggested_cash_jpy_trial}` | {row.reason} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 4. STALE_REVIEW 旧价格触发，仅观察")
    lines.append("")
    if stale_triggered_rows:
        lines.append("| ticker | strategy | level | true_price_date | price | trial | normal | deep | reason |")
        lines.append("|---|---|---|---|---:|---:|---:|---:|---|")
        for row in stale_triggered_rows:
            lines.append(f"| `{row.ticker}` | `{row.strategy_name}` | `{row.triggered_level}` | `{row.last_price_date}` | `{row.current_price_usd}` | `{row.trial_price_usd}` | `{row.normal_price_usd}` | `{row.deep_price_usd}` | {row.reason} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 5. 等待触发")
    lines.append("")
    if wait_rows:
        lines.append("| ticker | strategy | price | true_price_date | trial | normal | deep | freshness |")
        lines.append("|---|---|---:|---|---:|---:|---:|---|")
        for row in wait_rows[:30]:
            lines.append(f"| `{row.ticker}` | `{row.strategy_name}` | `{row.current_price_usd}` | `{row.last_price_date}` | `{row.trial_price_usd}` | `{row.normal_price_usd}` | `{row.deep_price_usd}` | `{row.price_freshness_status}` |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 6. 被阻止项目")
    lines.append("")
    if blocked_rows:
        lines.append("| ticker | strategy | action | true_price_date | freshness | affordable | reason |")
        lines.append("|---|---|---|---|---|---:|---|")
        for row in blocked_rows:
            lines.append(f"| `{row.ticker}` | `{row.strategy_name}` | `{row.action_status}` | `{row.last_price_date}` | `{row.price_freshness_status}` | `{row.affordable_1_share}` | {row.reason} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 7. 下一步")
    lines.append("")
    lines.append("下一步进入 V16.4 Trade Feedback：读取 manual_trade_log.csv，开始建立真实成交反馈和真实持仓闭环。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    summary_lines: list[str] = []
    summary_lines.append("# V16 Execution Ticker Summary")
    summary_lines.append("")
    summary_lines.append(f"生成时间：`{generated_at}`")
    summary_lines.append("")
    summary_lines.append("## 1. 聚合说明")
    summary_lines.append("")
    summary_lines.append("本表按 ticker 聚合多个策略的重复输出，使用真实 source last_date。")
    summary_lines.append("")
    summary_lines.append("| ticker | best_action | level | price | true_date | trial | normal | deep | affordable | strategies | reason |")
    summary_lines.append("|---|---|---|---:|---|---:|---:|---:|---:|---|---|")

    for row in ticker_summary:
        summary_lines.append(f"| `{row.ticker}` | `{row.best_action_status}` | `{row.best_triggered_level}` | `{row.current_price_usd}` | `{row.last_price_date}` | `{row.trial_price_usd}` | `{row.normal_price_usd}` | `{row.deep_price_usd}` | `{row.affordable_1_share}` | `{row.strategies}` | {row.reason} |")

    summary_lines.append("")
    summary_md_path.write_text("\n".join(summary_lines), encoding="utf-8")

    audit_lines: list[str] = []
    audit_lines.append("# V16 Execution Audit")
    audit_lines.append("")
    audit_lines.append(f"生成时间：`{generated_at}`")
    audit_lines.append("")
    audit_lines.append("## 1. Price Freshness Summary")
    audit_lines.append("")
    audit_lines.append("| freshness | count |")
    audit_lines.append("|---|---:|")
    for key in sorted(freshness_counts):
        audit_lines.append(f"| `{key}` | `{freshness_counts[key]}` |")

    audit_lines.append("")
    audit_lines.append("## 2. Price Provenance Summary")
    audit_lines.append("")
    audit_lines.append("| ticker | provenance_status |")
    audit_lines.append("|---|---|")
    for ticker in sorted(provenance_by_ticker):
        audit_lines.append(f"| `{ticker}` | `{provenance_by_ticker[ticker]}` |")

    audit_lines.append("")
    audit_lines.append("## 3. Price Load Records")
    audit_lines.append("")
    audit_lines.append("| ticker | status | rows | first_date | last_date | source |")
    audit_lines.append("|---|---|---:|---|---|---|")
    for record in price_records:
        audit_lines.append(f"| `{record.ticker}` | `{record.status}` | `{record.rows}` | `{record.first_date}` | `{record.last_date}` | `{record.source}` |")

    audit_lines.append("")
    audit_lines.append("## 4. 审计说明")
    audit_lines.append("")
    audit_lines.append("TRUE_SOURCE_DATE：Execution Plan 使用该 ticker 原始数据源的真实 last_date。")
    audit_lines.append("FRESH：可以用于 PLAN_ONLY 触发判断。")
    audit_lines.append("STALE_REVIEW：只能观察，所有触发降级为 STALE_REVIEW_TRIGGERED。")
    audit_lines.append("STALE_BLOCK：不能作为任何执行计划参考。")
    audit_lines.append("")

    audit_path.write_text("\n".join(audit_lines), encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "rows": [row.__dict__ for row in rows],
        "ticker_summary": [row.__dict__ for row in ticker_summary],
        "action_counts": action_counts,
        "freshness_counts": freshness_counts,
        "provenance_by_ticker": provenance_by_ticker,
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, audit_path, json_path, summary_md_path, summary_csv_path


def run_execution_plan() -> int:
    rows, price_records, provenance_by_ticker = build_execution_plan()
    md_path, csv_path, audit_path, json_path, summary_md_path, summary_csv_path = write_execution_plan(rows, price_records, provenance_by_ticker)

    print("")
    print("V16 execution plan completed.")
    print(f"- rows: {len(rows)}")
    print(f"- markdown: {md_path}")
    print(f"- csv: {csv_path}")
    print(f"- audit: {audit_path}")
    print(f"- ticker_summary_md: {summary_md_path}")
    print(f"- ticker_summary_csv: {summary_csv_path}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_execution_plan())
