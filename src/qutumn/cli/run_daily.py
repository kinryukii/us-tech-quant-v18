from __future__ import annotations

from datetime import datetime
import csv
import json
from pathlib import Path

from qutumn.common.paths import ROOT, OUTPUTS_V16, STATE_V16, ensure_dir


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _summary(path: Path) -> dict:
    payload = _read_json(path)
    summary = payload.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _count_rows(path: Path, key: str | None = None, value: str | None = None) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if key is None:
                count += 1
            elif str(row.get(key, "")) == str(value):
                count += 1
    return count


def _count_grade_prefix(prefix: str) -> int:
    path = OUTPUTS_V16 / "backtest" / "V16_STRATEGY_GRADE.csv"
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            decision = str(row.get("research_decision", ""))
            if decision.startswith(prefix):
                count += 1
    return count


def _position_status() -> tuple[str, int, int, int]:
    path = OUTPUTS_V16 / "positions" / "V16_POSITION_REVIEW.json"
    payload = _read_json(path)
    if not payload:
        return "NOT_RUN", 0, 0, 0
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    return (
        str(payload.get("status", "UNKNOWN")),
        int(summary.get("open_position_count", 0) or 0),
        int(summary.get("review_row_count", 0) or 0),
        int(summary.get("no_action_watchlist_count", 0) or 0),
    )


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    daily_dir = ensure_dir(OUTPUTS_V16 / "daily")
    report_path = daily_dir / "V16_DAILY_README.md"
    root_readme = ROOT / "V16_DAILY_README.md"

    price_summary = _summary(OUTPUTS_V16 / "data" / "V16_PRICE_REFRESH_AUDIT.json")
    feedback_summary = _summary(OUTPUTS_V16 / "feedback" / "V16_TRADE_FEEDBACK.json")
    event_gate_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.json")
    event_practicality_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_PRACTICALITY.json")
    event_helper_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.json")
    event_workflow_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json")
    behavior_summary = _summary(OUTPUTS_V16 / "risk" / "V16_BEHAVIOR_GUARD.json")
    candidate_summary = _summary(OUTPUTS_V16 / "review" / "V16_CANDIDATE_REVIEW.json")

    scoreboard_path = OUTPUTS_V16 / "backtest" / "V16_STRATEGY_SCOREBOARD.csv"
    metrics_path = OUTPUTS_V16 / "backtest" / "V16_BACKTEST_METRICS.csv"
    execution_path = OUTPUTS_V16 / "execution" / "V16_EXECUTION_PLAN.csv"
    ticker_summary_path = OUTPUTS_V16 / "execution" / "V16_EXECUTION_TICKER_SUMMARY.csv"
    positions_path = STATE_V16 / "real_positions.csv"

    strategy_total = _count_rows(scoreboard_path)
    backtest_total = _count_rows(metrics_path)
    backtest_available = _count_rows(metrics_path, "status", "METRICS_AVAILABLE")

    pass_candidate = _count_grade_prefix("BACKTEST_PASS_CANDIDATE")
    watch_count = _count_grade_prefix("WATCH")
    rejected_count = _count_grade_prefix("REJECTED")

    execution_total = _count_rows(execution_path)
    ticker_total = _count_rows(ticker_summary_path)
    fresh_triggered = _count_rows(execution_path, "action_status", "PLAN_ONLY_TRIGGERED")
    blocked_too_expensive = _count_rows(execution_path, "action_status", "BLOCKED_TOO_EXPENSIVE")
    wait_trigger = _count_rows(execution_path, "action_status", "WAIT_TRIGGER")
    stale_triggered = _count_rows(execution_path, "action_status", "STALE_REVIEW_TRIGGERED")
    stale_review_only = _count_rows(execution_path, "action_status", "STALE_REVIEW_ONLY")
    watch_only = _count_rows(execution_path, "action_status", "WATCH_ONLY")

    position_review_status, reviewed_open_positions, review_rows, no_action_watchlist = _position_status()

    behavior_status = str(behavior_summary.get("status", "NOT_RUN"))
    discipline = str(behavior_summary.get("discipline", ""))
    fresh_plan_tickers = str(behavior_summary.get("fresh_plan_tickers", ""))

    text = f"""# V16 Daily README

生成时间：`{generated_at}`

## 今日状态

**V16.10F Event Confirmation Workflow Integration 已完成。**

当前 V16 已经完成：

- V16.8-stable freeze
- V16.8C legacy archive
- V16.9 price refresh
- V16.9B Behavior Guard 分域封锁修复
- V16.9C Candidate Review
- V16.9D Candidate Review 接入 Daily / Health Check
- V16.10 Event Calendar Practicalization
- V16.10B Event Practicality 接入 Daily / Health Check
- V16.10C Event Confirmation Helper
- V16.10D Event Confirmation Helper 接入 Daily / Health Check
- V16.10E Event Confirmation Workflow
- V16.10F Event Confirmation Workflow 接入 Daily / Health Check

## 当前交易结论

**不产生实盘交易建议。**

当前 Behavior Guard 状态：**{behavior_status}**

{discipline}

当前 REVIEW_ONLY 候选：`{fresh_plan_tickers or "无"}`

事件实用化状态：**{event_practicality_summary.get("status", "NOT_RUN")}**

事件确认模板状态：**{event_helper_summary.get("status", "NOT_RUN")}**

事件确认工作流状态：**{event_workflow_summary.get("status", "NOT_RUN")}**

由于事件确认仍为 pending，当前候选不能升级到 SMALL_REAL_TRIAL_CANDIDATE。

## Candidate Review 状态

- candidate_count：`{candidate_summary.get("candidate_count", 0)}`
- review_only_count：`{candidate_summary.get("review_only_count", 0)}`
- reject_for_now_count：`{candidate_summary.get("reject_for_now_count", 0)}`
- 当前候选：`{fresh_plan_tickers or "无"}`

## Event Practicality 状态

- event_practicality_status：`{event_practicality_summary.get("status", "NOT_RUN")}`
- event_unconfirmed_count：`{event_practicality_summary.get("event_unconfirmed_count", 0)}`
- event_confirmed_review_only_count：`{event_practicality_summary.get("event_confirmed_review_only_count", 0)}`
- small_real_trial_candidate_count：`{event_practicality_summary.get("small_real_trial_candidate_count", 0)}`

## Event Confirmation Helper 状态

- event_confirmation_helper_status：`{event_helper_summary.get("status", "NOT_RUN")}`
- pending_confirmation_count：`{event_helper_summary.get("pending_confirmation_count", 0)}`
- existing_confirmed_count：`{event_helper_summary.get("existing_confirmed_count", 0)}`
- workflow_status：`{event_workflow_summary.get("status", "NOT_RUN")}`
- to_fill_count：`{event_workflow_summary.get("to_fill_count", 0)}`
- pending file：`state\\v16\\event_confirmation_pending.csv`
- to-fill file：`state\\v16\\event_confirmation_to_fill.csv`
- confirmation log：`state\\v16\\event_confirmation_log.csv`

## Price Freshness 状态

- refreshed_count：`{price_summary.get("refreshed_count", 0)}`
- failed_count：`{price_summary.get("failed_count", 0)}`
- 当前价格已刷新到：`2026-05-08`
- stale trigger：`{stale_triggered}`
- stale review only：`{stale_review_only}`

## Strategy Lab 状态

- 策略数量：`{strategy_total}`
- 回测策略数量：`{backtest_total}`
- 已生成基础指标：`{backtest_available}`

## Strategy Grade 状态

- BACKTEST_PASS_CANDIDATE：`{pass_candidate}`
- WATCH：`{watch_count}`
- REJECTED：`{rejected_count}`

## Execution Plan 状态

- 明细计划行数：`{execution_total}`
- ticker 聚合数量：`{ticker_total}`
- FRESH 已触发 PLAN_ONLY：`{fresh_triggered}`
- BLOCKED_TOO_EXPENSIVE：`{blocked_too_expensive}`
- WAIT_TRIGGER：`{wait_trigger}`
- STALE_REVIEW 旧价格触发：`{stale_triggered}`
- STALE_REVIEW 仅观察：`{stale_review_only}`
- WATCH_ONLY：`{watch_only}`

## Trade Feedback 状态

- feedback_status：`{feedback_summary.get("status", "NOT_RUN")}`
- 有效成交数量：`{feedback_summary.get("valid_trade_count", 0)}`
- 当前开放持仓数量：`{feedback_summary.get("open_position_count", 0)}`
- real_positions 行数：`{_count_rows(positions_path)}`

## Position Review 状态

- position_review_status：`{position_review_status}`
- 审查开放持仓数量：`{reviewed_open_positions}`
- 审查行数：`{review_rows}`
- 无持仓观察行数：`{no_action_watchlist}`

## Event Gate 状态

- event_gate_status：`{event_gate_summary.get("status", "NOT_RUN")}`
- 事件数量：`{event_gate_summary.get("event_count", 0)}`
- 今日活跃事件：`{event_gate_summary.get("active_event_count", 0)}`
- 受事件影响行数：`{event_gate_summary.get("event_lock_count", 0)}`

## Behavior Guard 状态

- behavior_status：`{behavior_status}`
- triggered_guard_count：`{behavior_summary.get("triggered_guard_count", 0)}`
- global_hard_block_count：`{behavior_summary.get("global_hard_block_count", 0)}`
- scoped_hard_block_count：`{behavior_summary.get("scoped_hard_block_count", 0)}`
- caution_count：`{behavior_summary.get("caution_count", 0)}`

## 当前最高允许阶段

当前最高允许阶段：REVIEW_ONLY_EVENT_CONFIRMATION_PENDING。

允许：

- 观察 BE / CRWV
- 人工检查 CPI / NFP / FOMC / 财报 / 公司新闻 / 地缘风险
- 填写 event_confirmation_log.csv
- 更新事件日历
- 回填真实成交
- 复核持仓

不允许：

- 自动下单
- 把 PLAN_ONLY 当成下单指令
- 买入 TQQQ / SOXL
- 跳过事件确认
- 把 BE / CRWV 升级为 SMALL_REAL_TRIAL_CANDIDATE
- 在没有真实成交反馈前进入 MAIN_EXECUTION

## 每日核心阅读文件

1. `V16_DAILY_README.md`
2. `outputs\\v16\\data\\V16_PRICE_REFRESH_AUDIT.md`
3. `outputs\\v16\\execution\\V16_EXECUTION_TICKER_SUMMARY.md`
4. `outputs\\v16\\review\\V16_CANDIDATE_REVIEW.md`
5. `outputs\\v16\\risk\\V16_EVENT_PRACTICALITY.md`
6. `outputs\\v16\\risk\\V16_EVENT_CONFIRMATION_HELPER.md`
7. `outputs\\v16\\risk\\V16_EVENT_CONFIRMATION_WORKFLOW.md`
8. `outputs\\v16\\positions\\V16_POSITION_REVIEW.md`
9. `outputs\\v16\\risk\\V16_EVENT_GATE.md`
10. `outputs\\v16\\risk\\V16_BEHAVIOR_GUARD.md`
11. `outputs\\v16\\feedback\\V16_TRADE_FEEDBACK.md`
12. `outputs\\v16\\health\\V16_HEALTH_CHECK.md`

## 下一步

进入人工事件确认：

1. 打开 `state\\v16\\event_confirmation_to_fill.csv`
2. 人工检查 CPI / NFP / FOMC / 财报 / 公司新闻 / 地缘风险
3. 把确认后的行复制到 `state\\v16\\event_confirmation_log.csv`
4. 修改 conclusion / restriction
5. 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\run_v16_after_event_confirmation.ps1`
6. 检查 BE / CRWV 是否仍只能 REVIEW_ONLY，或被事件风险 BLOCK
"""

    report_path.write_text(text, encoding="utf-8")
    root_readme.write_text(text, encoding="utf-8")

    print("")
    print("V16 daily report completed.")
    print(f"- report: {report_path}")
    print(f"- root_readme: {root_readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
