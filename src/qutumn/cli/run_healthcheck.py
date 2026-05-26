from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from qutumn.common.paths import ROOT, CONFIGS_V16, STATE_V16, OUTPUTS_V16, ensure_dir


REQUIRED_DIRS = [
    CONFIGS_V16,
    CONFIGS_V16 / "account",
    CONFIGS_V16 / "universe",
    CONFIGS_V16 / "strategies",
    CONFIGS_V16 / "backtest",
    CONFIGS_V16 / "execution",
    CONFIGS_V16 / "feedback",
    CONFIGS_V16 / "position_review",
    CONFIGS_V16 / "event",
    CONFIGS_V16 / "behavior",
    CONFIGS_V16 / "data",
    ROOT / "src" / "qutumn" / "common",
    ROOT / "src" / "qutumn" / "data",
    ROOT / "src" / "qutumn" / "backtest",
    ROOT / "src" / "qutumn" / "execution",
    ROOT / "src" / "qutumn" / "portfolio",
    ROOT / "src" / "qutumn" / "risk",
    ROOT / "src" / "qutumn" / "research",
    ROOT / "src" / "qutumn" / "cli",
    STATE_V16,
    OUTPUTS_V16,
    OUTPUTS_V16 / "data",
    OUTPUTS_V16 / "backtest",
    OUTPUTS_V16 / "execution",
    OUTPUTS_V16 / "feedback",
    OUTPUTS_V16 / "positions",
    OUTPUTS_V16 / "risk",
    OUTPUTS_V16 / "review",
    OUTPUTS_V16 / "daily",
    OUTPUTS_V16 / "health",
    OUTPUTS_V16 / "stable",
]

REQUIRED_FILES = [
    CONFIGS_V16 / "account" / "rakuten_us.yaml",
    CONFIGS_V16 / "account" / "sbi_korea.yaml",
    CONFIGS_V16 / "account" / "cash_policy.yaml",
    CONFIGS_V16 / "universe" / "us_etf_core.yaml",
    CONFIGS_V16 / "universe" / "us_leveraged_etf.yaml",
    CONFIGS_V16 / "universe" / "us_ai_stocks.yaml",
    CONFIGS_V16 / "strategies" / "strategy_pullback_balanced.yaml",
    CONFIGS_V16 / "strategies" / "strategy_momentum_core.yaml",
    CONFIGS_V16 / "strategies" / "strategy_leveraged_tactical.yaml",
    CONFIGS_V16 / "strategies" / "strategy_defensive_cash.yaml",
    CONFIGS_V16 / "strategies" / "strategy_event_locked.yaml",
    CONFIGS_V16 / "backtest" / "backtest_config.yaml",
    CONFIGS_V16 / "execution" / "execution_config.yaml",
    CONFIGS_V16 / "feedback" / "trade_feedback_config.yaml",
    CONFIGS_V16 / "position_review" / "position_review_config.yaml",
    CONFIGS_V16 / "event" / "event_gate_config.yaml",
    CONFIGS_V16 / "event" / "event_practicality.yaml",
    CONFIGS_V16 / "behavior" / "behavior_guard_config.yaml",
    CONFIGS_V16 / "data" / "price_refresh.yaml",
    STATE_V16 / "manual_trade_log.csv",
    STATE_V16 / "real_positions.csv",
    STATE_V16 / "real_cash_state.yaml",
    STATE_V16 / "strategy_registry.yaml",
    STATE_V16 / "event_calendar.csv",
    STATE_V16 / "event_confirmation_log.csv",
    STATE_V16 / "event_confirmation_pending.csv",
    STATE_V16 / "event_confirmation_to_fill.csv",
    OUTPUTS_V16 / "data" / "V16_PRICE_REFRESH_AUDIT.md",
    OUTPUTS_V16 / "backtest" / "V16_STRATEGY_SCOREBOARD.md",
    OUTPUTS_V16 / "backtest" / "V16_BACKTEST_REPORT.md",
    OUTPUTS_V16 / "backtest" / "V16_STRATEGY_GRADE.md",
    OUTPUTS_V16 / "execution" / "V16_EXECUTION_PLAN.md",
    OUTPUTS_V16 / "execution" / "V16_EXECUTION_TICKER_SUMMARY.md",
    OUTPUTS_V16 / "feedback" / "V16_TRADE_FEEDBACK.md",
    OUTPUTS_V16 / "positions" / "V16_POSITION_REVIEW.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_PRACTICALITY.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.md",
    OUTPUTS_V16 / "risk" / "V16_BEHAVIOR_GUARD.md",
    OUTPUTS_V16 / "review" / "V16_CANDIDATE_REVIEW.md",
    ROOT / "V16_DAILY_README.md",
]

CORE_READING_FILES = [
    ROOT / "V16_DAILY_README.md",
    OUTPUTS_V16 / "data" / "V16_PRICE_REFRESH_AUDIT.md",
    OUTPUTS_V16 / "execution" / "V16_EXECUTION_TICKER_SUMMARY.md",
    OUTPUTS_V16 / "review" / "V16_CANDIDATE_REVIEW.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_PRACTICALITY.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.md",
    OUTPUTS_V16 / "positions" / "V16_POSITION_REVIEW.md",
    OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.md",
    OUTPUTS_V16 / "risk" / "V16_BEHAVIOR_GUARD.md",
    OUTPUTS_V16 / "feedback" / "V16_TRADE_FEEDBACK.md",
]


def _status(path: Path) -> str:
    return "OK" if path.exists() else "MISSING"


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


def _runtime() -> dict:
    price = _summary(OUTPUTS_V16 / "data" / "V16_PRICE_REFRESH_AUDIT.json")
    feedback = _summary(OUTPUTS_V16 / "feedback" / "V16_TRADE_FEEDBACK.json")
    position_payload = _read_json(OUTPUTS_V16 / "positions" / "V16_POSITION_REVIEW.json")
    event_gate = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.json")
    event_practicality = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_PRACTICALITY.json")
    event_helper = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.json")
    event_workflow = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json")
    behavior = _summary(OUTPUTS_V16 / "risk" / "V16_BEHAVIOR_GUARD.json")
    candidate = _summary(OUTPUTS_V16 / "review" / "V16_CANDIDATE_REVIEW.json")

    return {
        "price_refreshed_count": price.get("refreshed_count", 0),
        "price_failed_count": price.get("failed_count", 0),
        "feedback_status": feedback.get("status", "UNKNOWN"),
        "position_review_status": position_payload.get("status", "UNKNOWN"),
        "event_gate_status": event_gate.get("status", "UNKNOWN"),
        "event_practicality_status": event_practicality.get("status", "UNKNOWN"),
        "event_unconfirmed_count": event_practicality.get("event_unconfirmed_count", 0),
        "event_confirmed_review_only_count": event_practicality.get("event_confirmed_review_only_count", 0),
        "small_real_trial_candidate_count": event_practicality.get("small_real_trial_candidate_count", 0),
        "event_confirmation_helper_status": event_helper.get("status", "UNKNOWN"),
        "pending_confirmation_count": event_helper.get("pending_confirmation_count", 0),
        "existing_confirmed_count": event_helper.get("existing_confirmed_count", 0),
        "event_confirmation_workflow_status": event_workflow.get("status", "UNKNOWN"),
        "event_confirmation_to_fill_count": event_workflow.get("to_fill_count", 0),
        "behavior_guard_status": behavior.get("status", "UNKNOWN"),
        "behavior_global_hard_block_count": behavior.get("global_hard_block_count", 0),
        "behavior_scoped_hard_block_count": behavior.get("scoped_hard_block_count", 0),
        "candidate_count": candidate.get("candidate_count", 0),
        "candidate_review_only_count": candidate.get("review_only_count", 0),
        "candidate_reject_for_now_count": candidate.get("reject_for_now_count", 0),
    }


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    health_dir = ensure_dir(OUTPUTS_V16 / "health")
    report_path = health_dir / "V16_HEALTH_CHECK.md"
    json_path = health_dir / "V16_HEALTH_CHECK.json"

    dir_rows = [(str(p.relative_to(ROOT)), _status(p)) for p in REQUIRED_DIRS]
    file_rows = [(str(p.relative_to(ROOT)), _status(p)) for p in REQUIRED_FILES]
    core_rows = [(str(p.relative_to(ROOT)), _status(p)) for p in CORE_READING_FILES]

    missing_dirs = [p for p, s in dir_rows if s != "OK"]
    missing_files = [p for p, s in file_rows if s != "OK"]
    missing_core = [p for p, s in core_rows if s != "OK"]

    status = "OK"
    if missing_dirs or missing_files or missing_core:
        status = "FAIL"

    runtime = _runtime()

    lines = []
    lines.append("# V16 Health Check")
    lines.append("")
    lines.append(f"生成时间：`{generated_at}`")
    lines.append("")
    lines.append(f"总体状态：**{status}**")
    lines.append("")
    lines.append("## 1. Runtime Status")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---|")
    for key, value in runtime.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.append("")
    lines.append("## 2. 核心阅读文件")
    lines.append("")
    lines.append("| 路径 | 状态 |")
    lines.append("|---|---|")
    for path, s in core_rows:
        lines.append(f"| `{path}` | `{s}` |")

    lines.append("")
    lines.append("## 3. 目录检查")
    lines.append("")
    lines.append("| 路径 | 状态 |")
    lines.append("|---|---|")
    for path, s in dir_rows:
        lines.append(f"| `{path}` | `{s}` |")

    lines.append("")
    lines.append("## 4. 核心文件检查")
    lines.append("")
    lines.append("| 路径 | 状态 |")
    lines.append("|---|---|")
    for path, s in file_rows:
        lines.append(f"| `{path}` | `{s}` |")

    lines.append("")
    lines.append("## 5. 当前结论")
    lines.append("")
    if status == "OK":
        lines.append("V16.10F 的价格刷新、候选复核、事件实用化、事件确认模板、事件确认工作流、执行计划、事件闸门、行为纪律和核心阅读文件完整。")
    else:
        lines.append("V16.10F 仍有缺失项，请先修复 MISSING。")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "status": status,
        "runtime": runtime,
        "missing_dirs": missing_dirs,
        "missing_files": missing_files,
        "missing_core": missing_core,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("")
    print("V16 enhanced health check completed.")
    print(f"- status: {status}")
    print(f"- report: {report_path}")
    print(f"- json: {json_path}")
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
