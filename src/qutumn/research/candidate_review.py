from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json

from qutumn.common.paths import OUTPUTS_V16, STATE_V16, ensure_dir


@dataclass
class CandidateReviewRow:
    ticker: str
    review_status: str
    execution_action: str
    trigger_level: str
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
    event_gate_status: str
    event_adjusted_action: str
    event_ids: str
    behavior_status: str
    blocker_summary: str
    risk_notes: str
    final_instruction: str


def _read_csv(path: Path) -> list[dict]:
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


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _safe_int(value: object, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text in {"true", "1", "yes", "y"}:
        return True

    return False


def _index_by_ticker(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}

    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if ticker:
            result[ticker] = row

    return result


def _behavior_summary() -> dict:
    payload = _read_json(OUTPUTS_V16 / "risk" / "V16_BEHAVIOR_GUARD.json")
    summary = payload.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _event_summary() -> dict:
    payload = _read_json(OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.json")
    summary = payload.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _trade_feedback_summary() -> dict:
    payload = _read_json(OUTPUTS_V16 / "feedback" / "V16_TRADE_FEEDBACK.json")
    summary = payload.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _build_risk_notes(exec_row: dict, event_row: dict, behavior: dict, event_summary: dict, trade_feedback: dict) -> str:
    notes: list[str] = []

    role = str(exec_row.get("role", ""))
    ticker = str(exec_row.get("ticker", "")).upper()
    event_status = str(event_summary.get("status", "UNKNOWN"))
    valid_trades = int(trade_feedback.get("valid_trade_count", 0) or 0)
    open_positions = int(trade_feedback.get("open_position_count", 0) or 0)

    if "SINGLE" in role.upper():
        notes.append("single-stock satellite risk")

    if ticker in {"TQQQ", "SOXL"}:
        notes.append("leveraged ETF blocked")

    if event_status == "READY_NO_EVENTS":
        notes.append("event calendar is empty; manual event check required")

    if valid_trades == 0 and open_positions == 0:
        notes.append("no real trade feedback and no real position yet")

    if str(behavior.get("status", "")) == "RESTRICTED":
        notes.append("behavior guard restricted; review-only")

    if str(event_row.get("event_gate_status", "")) != "NO_EVENT_LOCK":
        notes.append("event gate adjustment exists")

    if not notes:
        notes.append("no extra risk note detected")

    return "; ".join(notes)


def _final_instruction(exec_row: dict, event_row: dict, behavior: dict, risk_notes: str) -> tuple[str, str, str]:
    ticker = str(exec_row.get("ticker", "")).upper()
    action = str(exec_row.get("best_action_status", ""))
    freshness = str(exec_row.get("price_freshness_status", ""))
    role = str(exec_row.get("role", ""))
    event_action = str(event_row.get("event_adjusted_action", action))
    behavior_status = str(behavior.get("status", "UNKNOWN"))

    blockers: list[str] = []

    if freshness != "FRESH":
        blockers.append("price_not_fresh")

    if action != "PLAN_ONLY_TRIGGERED":
        blockers.append("not_plan_only_triggered")

    if event_action.startswith("EVENT_BLOCKED") or event_action == "EVENT_OBSERVE_ONLY":
        blockers.append("event_gate_block")

    if ticker in {"TQQQ", "SOXL"} or "LEVERAGED" in role.upper():
        blockers.append("leveraged_etf_scope_block")

    if blockers:
        return "REJECT_FOR_NOW", ";".join(blockers), "Do not trade. Keep on watchlist only."

    if behavior_status in {"HARD_BLOCK"}:
        return "REJECT_FOR_NOW", "global_behavior_hard_block", "Do not trade. Behavior Guard is global hard block."

    return (
        "REVIEW_ONLY_CANDIDATE",
        "no_global_block_detected",
        "Review only. This is not a buy instruction. Confirm events, liquidity, earnings, account cash, and manual discipline before any real action.",
    )


def build_candidate_review() -> tuple[list[CandidateReviewRow], dict]:
    execution_rows = _read_csv(OUTPUTS_V16 / "execution" / "V16_EXECUTION_TICKER_SUMMARY.csv")
    event_rows = _index_by_ticker(_read_csv(OUTPUTS_V16 / "risk" / "V16_EVENT_ADJUSTED_EXECUTION.csv"))

    behavior = _behavior_summary()
    event_s = _event_summary()
    trade_feedback = _trade_feedback_summary()

    candidates = [
        row for row in execution_rows
        if str(row.get("best_action_status", "")) == "PLAN_ONLY_TRIGGERED"
    ]

    review_rows: list[CandidateReviewRow] = []

    for row in candidates:
        ticker = str(row.get("ticker", "")).strip().upper()
        event_row = event_rows.get(ticker, {})

        risk_notes = _build_risk_notes(
            exec_row=row,
            event_row=event_row,
            behavior=behavior,
            event_summary=event_s,
            trade_feedback=trade_feedback,
        )

        review_status, blocker_summary, final_instruction = _final_instruction(
            exec_row=row,
            event_row=event_row,
            behavior=behavior,
            risk_notes=risk_notes,
        )

        review_rows.append(
            CandidateReviewRow(
                ticker=ticker,
                review_status=review_status,
                execution_action=str(row.get("best_action_status", "")),
                trigger_level=str(row.get("best_triggered_level", "")),
                current_price_usd=_safe_float(row.get("current_price_usd")),
                last_price_date=str(row.get("last_price_date", "")),
                price_freshness_status=str(row.get("price_freshness_status", "")),
                trial_price_usd=_safe_float(row.get("trial_price_usd")),
                normal_price_usd=_safe_float(row.get("normal_price_usd")),
                deep_price_usd=_safe_float(row.get("deep_price_usd")),
                affordable_1_share=_safe_bool(row.get("affordable_1_share")),
                one_share_cost_jpy=_safe_float(row.get("one_share_cost_jpy")),
                suggested_shares_trial=_safe_int(row.get("suggested_shares_trial")),
                suggested_cash_jpy_trial=_safe_float(row.get("suggested_cash_jpy_trial")) or 0.0,
                strategies=str(row.get("strategies", "")),
                role=str(row.get("role", "")),
                event_gate_status=str(event_row.get("event_gate_status", "NO_EVENT_ROW")),
                event_adjusted_action=str(event_row.get("event_adjusted_action", row.get("best_action_status", ""))),
                event_ids=str(event_row.get("active_event_ids", "")),
                behavior_status=str(behavior.get("status", "UNKNOWN")),
                blocker_summary=blocker_summary,
                risk_notes=risk_notes,
                final_instruction=final_instruction,
            )
        )

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "candidate_count": len(review_rows),
        "review_only_count": sum(1 for r in review_rows if r.review_status == "REVIEW_ONLY_CANDIDATE"),
        "reject_for_now_count": sum(1 for r in review_rows if r.review_status == "REJECT_FOR_NOW"),
        "behavior_status": str(behavior.get("status", "UNKNOWN")),
        "event_gate_status": str(event_s.get("status", "UNKNOWN")),
        "trade_feedback_status": str(trade_feedback.get("status", "UNKNOWN")),
    }

    return review_rows, summary


def write_candidate_review(rows: list[CandidateReviewRow], summary: dict) -> tuple[Path, Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "review")
    md_path = out_dir / "V16_CANDIDATE_REVIEW.md"
    csv_path = out_dir / "V16_CANDIDATE_REVIEW.csv"
    json_path = out_dir / "V16_CANDIDATE_REVIEW.json"

    fieldnames = list(CandidateReviewRow.__dataclass_fields__.keys())

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row.__dict__)

    review_rows = [r for r in rows if r.review_status == "REVIEW_ONLY_CANDIDATE"]
    rejected_rows = [r for r in rows if r.review_status == "REJECT_FOR_NOW"]

    lines: list[str] = []
    lines.append("# V16 Candidate Review")
    lines.append("")
    lines.append(f"生成时间：`{summary.get('generated_at')}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    if review_rows:
        tickers = ";".join(r.ticker for r in review_rows)
        lines.append(f"当前有 REVIEW_ONLY 候选：`{tickers}`。")
    else:
        lines.append("当前没有可进入 REVIEW_ONLY 的候选。")
    lines.append("")
    lines.append("重要限制：Candidate Review 不是买入建议，不是下单指令，只是人工复核页。")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---:|")
    lines.append(f"| candidate_count | `{summary.get('candidate_count')}` |")
    lines.append(f"| review_only_count | `{summary.get('review_only_count')}` |")
    lines.append(f"| reject_for_now_count | `{summary.get('reject_for_now_count')}` |")
    lines.append(f"| behavior_status | `{summary.get('behavior_status')}` |")
    lines.append(f"| event_gate_status | `{summary.get('event_gate_status')}` |")
    lines.append(f"| trade_feedback_status | `{summary.get('trade_feedback_status')}` |")

    lines.append("")
    lines.append("## 3. REVIEW_ONLY 候选")
    lines.append("")
    if review_rows:
        lines.append("| ticker | level | price | date | trial | normal | deep | shares | cash_jpy | strategies | risk_notes |")
        lines.append("|---|---|---:|---|---:|---:|---:|---:|---:|---|---|")
        for r in review_rows:
            lines.append(
                f"| `{r.ticker}` | `{r.trigger_level}` | `{r.current_price_usd}` | `{r.last_price_date}` | "
                f"`{r.trial_price_usd}` | `{r.normal_price_usd}` | `{r.deep_price_usd}` | "
                f"`{r.suggested_shares_trial}` | `{r.suggested_cash_jpy_trial}` | `{r.strategies}` | {r.risk_notes} |"
            )
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 4. 暂不通过候选")
    lines.append("")
    if rejected_rows:
        lines.append("| ticker | blocker | instruction |")
        lines.append("|---|---|---|")
        for r in rejected_rows:
            lines.append(f"| `{r.ticker}` | `{r.blocker_summary}` | {r.final_instruction} |")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 5. 每个候选的复核问题")
    lines.append("")
    if review_rows:
        for r in review_rows:
            lines.append(f"### {r.ticker}")
            lines.append("")
            lines.append(f"- 触发层级：`{r.trigger_level}`")
            lines.append(f"- 当前价格：`{r.current_price_usd}`")
            lines.append(f"- 价格日期：`{r.last_price_date}`")
            lines.append(f"- 事件闸门：`{r.event_gate_status}` / `{r.event_adjusted_action}`")
            lines.append(f"- 行为纪律：`{r.behavior_status}`")
            lines.append(f"- 小账户约束：1 股可买 = `{r.affordable_1_share}`，计划股数 = `{r.suggested_shares_trial}`")
            lines.append("")
            lines.append("人工复核必须回答：")
            lines.append("")
            lines.append("1. 今天是否有 CPI / NFP / FOMC / 财报 / 公司重大事件？")
            lines.append("2. 这个下跌是普通回撤，还是基本面恶化？")
            lines.append("3. 小账户买 1 股后，是否会让单一股票风险过高？")
            lines.append("4. 是否只是因为空仓焦虑而想买？")
            lines.append("5. 是否可以接受继续下跌后的心理压力？")
            lines.append("")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 6. 最终纪律")
    lines.append("")
    lines.append("当前最多允许 REVIEW_ONLY。")
    lines.append("")
    lines.append("不允许：")
    lines.append("")
    lines.append("- 自动下单")
    lines.append("- 把 PLAN_ONLY 当成买入指令")
    lines.append("- 买入 TQQQ / SOXL")
    lines.append("- 跳过事件日历检查")
    lines.append("- 在没有真实成交反馈闭环前进入 MAIN_EXECUTION")
    lines.append("")
    lines.append("## 7. 下一步")
    lines.append("")
    lines.append("下一步进入 V16.9D：把 Candidate Review 接入 Daily README 和 Health Check 核心阅读文件。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "summary": summary,
        "rows": [r.__dict__ for r in rows],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, json_path


def run_candidate_review() -> int:
    rows, summary = build_candidate_review()
    md_path, csv_path, json_path = write_candidate_review(rows, summary)

    print("")
    print("V16 candidate review completed.")
    print(f"- candidates: {summary.get('candidate_count')}")
    print(f"- review_only: {summary.get('review_only_count')}")
    print(f"- rejected: {summary.get('reject_for_now_count')}")
    print(f"- report: {md_path}")
    print(f"- csv: {csv_path}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_candidate_review())
