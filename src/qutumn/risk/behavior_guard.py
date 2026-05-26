from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json

from qutumn.common.paths import CONFIGS_V16, OUTPUTS_V16, ensure_dir
from qutumn.common.config_io import load_yaml_like


@dataclass
class GuardRow:
    guard_name: str
    severity: str
    status: str
    affected_tickers: str
    evidence_count: int
    instruction: str
    reason: str


def _load_behavior_config() -> dict:
    path = CONFIGS_V16 / "behavior" / "behavior_guard_config.yaml"
    if not path.exists():
        return {}
    cfg = load_yaml_like(path)
    return cfg if isinstance(cfg, dict) else {}


def _read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows: list[dict] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _rule_message(cfg: dict, rule_name: str, default: str) -> str:
    rules = cfg.get("rules", {})
    if not isinstance(rules, dict):
        return default

    rule = rules.get(rule_name, {})
    if not isinstance(rule, dict):
        return default

    return str(rule.get("message", default))


def _rule_severity(cfg: dict, rule_name: str, default: str) -> str:
    rules = cfg.get("rules", {})
    if not isinstance(rules, dict):
        return default

    rule = rules.get(rule_name, {})
    if not isinstance(rule, dict):
        return default

    return str(rule.get("severity", default))


def _tickers(rows: list[dict], key: str = "ticker") -> str:
    values = sorted(set(str(row.get(key, "")).strip().upper() for row in rows if str(row.get(key, "")).strip()))
    return ";".join(values)


def _build_guard_rows() -> tuple[list[GuardRow], dict]:
    cfg = _load_behavior_config()

    ticker_summary_rows = _read_csv_rows(OUTPUTS_V16 / "execution" / "V16_EXECUTION_TICKER_SUMMARY.csv")
    position_rows = _read_csv_rows(OUTPUTS_V16 / "positions" / "V16_POSITION_REVIEW.csv")
    event_adjusted_rows = _read_csv_rows(OUTPUTS_V16 / "risk" / "V16_EVENT_ADJUSTED_EXECUTION.csv")
    event_payload = _read_json(OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.json")
    feedback_payload = _read_json(OUTPUTS_V16 / "feedback" / "V16_TRADE_FEEDBACK.json")

    guard_rows: list[GuardRow] = []

    stale_trigger_rows = [
        row for row in ticker_summary_rows
        if str(row.get("best_action_status", "")) == "STALE_REVIEW_TRIGGERED"
    ]

    if stale_trigger_rows:
        guard_rows.append(
            GuardRow(
                guard_name="stale_trigger_block",
                severity="GLOBAL_HARD_BLOCK",
                status="TRIGGERED",
                affected_tickers=_tickers(stale_trigger_rows),
                evidence_count=len(stale_trigger_rows),
                instruction=_rule_message(cfg, "stale_trigger_block", "Old-price triggers are observation only."),
                reason="At least one ticker is triggered only under stale price data.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="stale_trigger_block",
                severity="GLOBAL_HARD_BLOCK",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="No stale trigger is currently present.",
                reason="No ticker has STALE_REVIEW_TRIGGERED status.",
            )
        )

    fresh_trigger_rows = [
        row for row in ticker_summary_rows
        if str(row.get("best_action_status", "")) == "PLAN_ONLY_TRIGGERED"
    ]

    wait_or_stale_rows = [
        row for row in ticker_summary_rows
        if str(row.get("best_action_status", "")) in {"WAIT_TRIGGER", "STALE_REVIEW_ONLY", "STALE_REVIEW_TRIGGERED"}
    ]

    if wait_or_stale_rows and not fresh_trigger_rows:
        guard_rows.append(
            GuardRow(
                guard_name="fomo_chase_block",
                severity="GLOBAL_HARD_BLOCK",
                status="TRIGGERED",
                affected_tickers=_tickers(wait_or_stale_rows),
                evidence_count=len(wait_or_stale_rows),
                instruction=_rule_message(cfg, "fomo_chase_block", "Do not override non-trigger status into manual chase-buy."),
                reason="There is no fresh executable trigger. Manual chase-buy is blocked.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="fomo_chase_block",
                severity="GLOBAL_HARD_BLOCK",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="Fresh PLAN_ONLY trigger exists or no watch rows exist. Non-trigger tickers still cannot be chased.",
                reason="FOMO block is not global because at least one fresh trigger exists.",
            )
        )

    feedback_summary = feedback_payload.get("summary", {}) if isinstance(feedback_payload, dict) else {}
    valid_trade_count = int(feedback_summary.get("valid_trade_count", 0) or 0)
    open_position_count = int(feedback_summary.get("open_position_count", 0) or 0)

    if valid_trade_count == 0 and open_position_count == 0:
        guard_rows.append(
            GuardRow(
                guard_name="empty_cash_anxiety",
                severity="CAUTION",
                status="TRIGGERED",
                affected_tickers="",
                evidence_count=0,
                instruction=_rule_message(cfg, "empty_cash_anxiety", "Do not buy merely because cash is unused."),
                reason="No valid trades and no open positions. Empty-cash anxiety risk exists.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="empty_cash_anxiety",
                severity="CAUTION",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="Cash anxiety guard clear.",
                reason="Trade log or open position exists.",
            )
        )

    leveraged_rows = [
        row for row in ticker_summary_rows
        if str(row.get("ticker", "")).upper() in {"TQQQ", "SOXL"} or "LEVERAGED" in str(row.get("role", "")).upper()
    ]

    leveraged_not_allowed = [
        row for row in leveraged_rows
        if str(row.get("best_action_status", "")) != "PLAN_ONLY_TRIGGERED"
        or str(row.get("price_freshness_status", "")) != "FRESH"
    ]

    if leveraged_not_allowed:
        guard_rows.append(
            GuardRow(
                guard_name="leveraged_etf_guard",
                severity="SCOPED_HARD_BLOCK",
                status="TRIGGERED",
                affected_tickers=_tickers(leveraged_not_allowed),
                evidence_count=len(leveraged_not_allowed),
                instruction=_rule_message(cfg, "leveraged_etf_guard", "Do not buy leveraged ETF without fresh clearance."),
                reason="Leveraged ETF rows are blocked, but this does not globally block non-leveraged tickers.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="leveraged_etf_guard",
                severity="SCOPED_HARD_BLOCK",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="No leveraged ETF block from current rows.",
                reason="No leveraged ETF row exists or all pass fresh trigger condition.",
            )
        )

    event_summary = event_payload.get("summary", {}) if isinstance(event_payload, dict) else {}
    event_status = str(event_summary.get("status", "NOT_RUN"))
    event_lock_count = int(event_summary.get("event_lock_count", 0) or 0)

    event_locked_rows = [
        row for row in event_adjusted_rows
        if str(row.get("event_gate_status", "")) != "NO_EVENT_LOCK"
    ]

    if event_status == "EVENT_LOCK_ACTIVE" or event_lock_count > 0 or event_locked_rows:
        guard_rows.append(
            GuardRow(
                guard_name="event_lock_guard",
                severity="GLOBAL_HARD_BLOCK",
                status="TRIGGERED",
                affected_tickers=_tickers(event_locked_rows),
                evidence_count=max(event_lock_count, len(event_locked_rows)),
                instruction=_rule_message(cfg, "event_lock_guard", "Do not override active Event Gate."),
                reason="Event Gate indicates active lock or adjusted execution rows.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="event_lock_guard",
                severity="GLOBAL_HARD_BLOCK",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="Event lock guard clear.",
                reason=f"Event Gate status is {event_status}.",
            )
        )

    add_review_rows = [
        row for row in position_rows
        if str(row.get("review_action", "")) == "ADD_REVIEW_ONLY"
    ]

    unsafe_add_rows = [
        row for row in position_rows
        if (
            str(row.get("position_status", "")) == "OPEN"
            and (
                str(row.get("review_action", "")).startswith("HOLD_LOSS")
                or str(row.get("price_freshness_status", "")) != "FRESH"
            )
        )
    ]

    if unsafe_add_rows and not add_review_rows:
        guard_rows.append(
            GuardRow(
                guard_name="add_without_fresh_trigger",
                severity="GLOBAL_HARD_BLOCK",
                status="TRIGGERED",
                affected_tickers=_tickers(unsafe_add_rows),
                evidence_count=len(unsafe_add_rows),
                instruction=_rule_message(cfg, "add_without_fresh_trigger", "Do not add without fresh trigger and review permission."),
                reason="Open position exists without fresh add-review permission.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="add_without_fresh_trigger",
                severity="GLOBAL_HARD_BLOCK",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="No unsafe add-to-position condition detected.",
                reason="No open position requiring add block, or add review is explicitly present.",
            )
        )

    take_profit_rows = [
        row for row in position_rows
        if str(row.get("review_action", "")).startswith("TAKE_PROFIT")
    ]

    if take_profit_rows:
        guard_rows.append(
            GuardRow(
                guard_name="profit_panic_guard",
                severity="CAUTION",
                status="TRIGGERED",
                affected_tickers=_tickers(take_profit_rows),
                evidence_count=len(take_profit_rows),
                instruction=_rule_message(cfg, "profit_panic_guard", "Do not sell solely due to small profit."),
                reason="Take-profit review exists. Manual confirmation is required.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="profit_panic_guard",
                severity="CAUTION",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="No profit-panic condition detected.",
                reason="No take-profit review row exists.",
            )
        )

    stop_or_loss_rows = [
        row for row in position_rows
        if str(row.get("review_action", "")).startswith("STOP")
        or str(row.get("review_action", "")).startswith("RISK_REVIEW")
        or str(row.get("review_action", "")).startswith("HOLD_LOSS")
    ]

    if stop_or_loss_rows:
        guard_rows.append(
            GuardRow(
                guard_name="loss_revenge_guard",
                severity="GLOBAL_HARD_BLOCK",
                status="TRIGGERED",
                affected_tickers=_tickers(stop_or_loss_rows),
                evidence_count=len(stop_or_loss_rows),
                instruction=_rule_message(cfg, "loss_revenge_guard", "Do not average down without predefined approval."),
                reason="Loss or stop-review condition exists. Revenge add is blocked.",
            )
        )
    else:
        guard_rows.append(
            GuardRow(
                guard_name="loss_revenge_guard",
                severity="GLOBAL_HARD_BLOCK",
                status="CLEAR",
                affected_tickers="",
                evidence_count=0,
                instruction="No revenge-add condition detected.",
                reason="No loss/stop review row exists.",
            )
        )

    global_hard_blocks = sum(1 for row in guard_rows if row.status == "TRIGGERED" and row.severity == "GLOBAL_HARD_BLOCK")
    scoped_hard_blocks = sum(1 for row in guard_rows if row.status == "TRIGGERED" and row.severity == "SCOPED_HARD_BLOCK")
    cautions = sum(1 for row in guard_rows if row.status == "TRIGGERED" and row.severity == "CAUTION")
    triggered = sum(1 for row in guard_rows if row.status == "TRIGGERED")

    fresh_plan_tickers = _tickers(fresh_trigger_rows)

    if global_hard_blocks > 0:
        status = "HARD_BLOCK"
        discipline = "Do not manually place new buy orders. Only observe, update data, or update event/trade logs."
    elif scoped_hard_blocks > 0:
        status = "RESTRICTED"
        discipline = "Scoped block is active. Leveraged ETF actions are blocked, while fresh non-leveraged PLAN_ONLY candidates remain review-only."
    elif cautions > 0:
        status = "CAUTION"
        discipline = "Manual action requires extra confirmation. Do not act from emotion or boredom."
    else:
        status = "CLEAR"
        discipline = "No behavior guard is currently triggered, but execution remains plan-only until live approval."

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "triggered_guard_count": triggered,
        "global_hard_block_count": global_hard_blocks,
        "scoped_hard_block_count": scoped_hard_blocks,
        "hard_block_count": global_hard_blocks + scoped_hard_blocks,
        "caution_count": cautions,
        "fresh_plan_tickers": fresh_plan_tickers,
        "discipline": discipline,
    }

    return guard_rows, summary


def write_behavior_guard_outputs(rows: list[GuardRow], summary: dict) -> tuple[Path, Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "risk")
    md_path = out_dir / "V16_BEHAVIOR_GUARD.md"
    csv_path = out_dir / "V16_BEHAVIOR_GUARD.csv"
    json_path = out_dir / "V16_BEHAVIOR_GUARD.json"

    fieldnames = list(GuardRow.__dataclass_fields__.keys())

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)

    triggered_rows = [row for row in rows if row.status == "TRIGGERED"]
    global_hard_rows = [row for row in triggered_rows if row.severity == "GLOBAL_HARD_BLOCK"]
    scoped_hard_rows = [row for row in triggered_rows if row.severity == "SCOPED_HARD_BLOCK"]
    caution_rows = [row for row in triggered_rows if row.severity == "CAUTION"]

    lines: list[str] = []
    lines.append("# V16 Behavior Guard")
    lines.append("")
    lines.append(f"生成时间：`{summary.get('generated_at')}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append(f"状态：**{summary.get('status')}**")
    lines.append("")
    lines.append(str(summary.get("discipline")))
    lines.append("")
    lines.append("重要限制：Behavior Guard 是心理纪律层，不是市场预测模型，也不是实盘下单指令。")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---:|")
    lines.append(f"| triggered_guard_count | `{summary.get('triggered_guard_count')}` |")
    lines.append(f"| global_hard_block_count | `{summary.get('global_hard_block_count')}` |")
    lines.append(f"| scoped_hard_block_count | `{summary.get('scoped_hard_block_count')}` |")
    lines.append(f"| caution_count | `{summary.get('caution_count')}` |")
    lines.append(f"| fresh_plan_tickers | `{summary.get('fresh_plan_tickers')}` |")

    lines.append("")
    lines.append("## 3. Global Hard Blocks")
    lines.append("")
    if global_hard_rows:
        lines.append("| guard | affected | instruction | reason |")
        lines.append("|---|---|---|---|")
        for row in global_hard_rows:
            lines.append(f"| `{row.guard_name}` | `{row.affected_tickers}` | {row.instruction} | {row.reason} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 4. Scoped Hard Blocks")
    lines.append("")
    if scoped_hard_rows:
        lines.append("| guard | affected | instruction | reason |")
        lines.append("|---|---|---|---|")
        for row in scoped_hard_rows:
            lines.append(f"| `{row.guard_name}` | `{row.affected_tickers}` | {row.instruction} | {row.reason} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 5. Cautions")
    lines.append("")
    if caution_rows:
        lines.append("| guard | affected | instruction | reason |")
        lines.append("|---|---|---|---|")
        for row in caution_rows:
            lines.append(f"| `{row.guard_name}` | `{row.affected_tickers}` | {row.instruction} | {row.reason} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 6. Full Guard Table")
    lines.append("")
    lines.append("| guard | severity | status | affected | evidence |")
    lines.append("|---|---|---|---|---:|")
    for row in rows:
        lines.append(f"| `{row.guard_name}` | `{row.severity}` | `{row.status}` | `{row.affected_tickers}` | `{row.evidence_count}` |")

    lines.append("")
    lines.append("## 7. 今日纪律")
    lines.append("")
    if summary.get("status") == "HARD_BLOCK":
        lines.append("今天不允许把旧价格触发、等待触发、事件风险或持仓风险，人工改写成买入理由。")
    elif summary.get("status") == "RESTRICTED":
        lines.append("今天只允许对 FRESH 的非杠杆 PLAN_ONLY 候选做人工复核。TQQQ / SOXL 等杠杆 ETF 继续禁止。")
    elif summary.get("status") == "CAUTION":
        lines.append("今天允许继续观察，但任何手动动作都必须有新价格、事件检查和持仓审查支持。")
    else:
        lines.append("纪律层未触发，但 V16 当前仍处于观察/复核阶段，不进入实盘自动执行。")

    lines.append("")
    lines.append("## 8. 下一步")
    lines.append("")
    lines.append("下一步进入 V16.9C：把 Daily README 更新为 Price Freshness 后的新状态，并把 BE / CRWV 标记为 review-only candidates。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "summary": summary,
        "rows": [row.__dict__ for row in rows],
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, json_path


def run_behavior_guard() -> int:
    rows, summary = _build_guard_rows()
    md_path, csv_path, json_path = write_behavior_guard_outputs(rows, summary)

    print("")
    print("V16 behavior guard completed.")
    print(f"- status: {summary.get('status')}")
    print(f"- triggered: {summary.get('triggered_guard_count')}")
    print(f"- global_hard_blocks: {summary.get('global_hard_block_count')}")
    print(f"- scoped_hard_blocks: {summary.get('scoped_hard_block_count')}")
    print(f"- cautions: {summary.get('caution_count')}")
    print(f"- fresh_plan_tickers: {summary.get('fresh_plan_tickers')}")
    print(f"- report: {md_path}")
    print(f"- csv: {csv_path}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_behavior_guard())
