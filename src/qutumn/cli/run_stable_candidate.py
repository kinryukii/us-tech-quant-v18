from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import shutil
import zipfile

from qutumn.common.paths import ROOT, OUTPUTS_V16, ensure_dir


CORE_FILES = [
    "V16_DAILY_README.md",
    "V16_DEVELOPMENT_ROADMAP.md",
    "V16_OPERATION_README.md",

    "configs/v16/account/rakuten_us.yaml",
    "configs/v16/account/sbi_korea.yaml",
    "configs/v16/account/cash_policy.yaml",
    "configs/v16/backtest/backtest_config.yaml",
    "configs/v16/execution/execution_config.yaml",
    "configs/v16/feedback/trade_feedback_config.yaml",
    "configs/v16/position_review/position_review_config.yaml",
    "configs/v16/event/event_gate_config.yaml",
    "configs/v16/behavior/behavior_guard_config.yaml",

    "state/v16/manual_trade_log.csv",
    "state/v16/real_positions.csv",
    "state/v16/real_cash_state.yaml",
    "state/v16/strategy_registry.yaml",
    "state/v16/event_calendar.csv",

    "outputs/v16/backtest/V16_STRATEGY_GRADE.md",
    "outputs/v16/execution/V16_EXECUTION_TICKER_SUMMARY.md",
    "outputs/v16/feedback/V16_TRADE_FEEDBACK.md",
    "outputs/v16/positions/V16_POSITION_REVIEW.md",
    "outputs/v16/risk/V16_EVENT_GATE.md",
    "outputs/v16/risk/V16_BEHAVIOR_GUARD.md",
    "outputs/v16/health/V16_HEALTH_CHECK.md",
]


def _remove_pycache() -> list[str]:
    removed: list[str] = []
    for path in ROOT.rglob("__pycache__"):
        try:
            shutil.rmtree(path)
            removed.append(str(path.relative_to(ROOT)))
        except Exception:
            pass
    return removed


def _write_operation_readme() -> Path:
    path = ROOT / "V16_OPERATION_README.md"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = f"""# Qutumn V16 Operation README

生成时间：`{generated_at}`

## 1. V16 当前定位

V16 是从 V15.39-stable 开始的新架构版本。

当前 V16.8 stable candidate 已完成：

- Strategy Lab
- Backtest Runner
- Cost-aware Strategy Grade
- Execution Plan
- Price provenance audit
- Trade Feedback
- Position Review
- Event Gate
- Behavior Guard
- Enhanced Health Check

## 2. 当前交易权限

当前不产生实盘交易建议。

允许：

- 观察
- 更新价格数据
- 更新事件日历
- 回填真实成交
- 复核持仓
- 跑 daily flow

不允许：

- 把旧价格触发当作买入
- 把 WAIT_TRIGGER 人工改成追买
- 在 Behavior Guard HARD_BLOCK 下买入
- 把 PLAN_ONLY 当成下单指令
- 进入 PAPER_TRADING / SMALL_REAL_TRIAL / MAIN_EXECUTION

## 3. 每天一键运行

PowerShell:

    cd D:\\us-tech-quant
    .\\scripts\\run_v16_daily.ps1

## 4. 每天优先阅读文件

1. V16_DAILY_README.md
2. outputs\\v16\\execution\\V16_EXECUTION_TICKER_SUMMARY.md
3. outputs\\v16\\positions\\V16_POSITION_REVIEW.md
4. outputs\\v16\\risk\\V16_EVENT_GATE.md
5. outputs\\v16\\risk\\V16_BEHAVIOR_GUARD.md
6. outputs\\v16\\feedback\\V16_TRADE_FEEDBACK.md

## 5. 手动成交回填

文件：

    state\\v16\\manual_trade_log.csv

字段：

    trade_id,trade_datetime,broker,market,ticker,side,quantity,price,trade_currency,fx_rate_to_jpy,commission_jpy,notes

示例：

    T20260509_001,2026-05-09 23:35:00,rakuten_us,US,NVDA,BUY,1,196.50,USD,155.00,0,trial entry

## 6. 手动事件日历

文件：

    state\\v16\\event_calendar.csv

字段：

    event_id,event_date,event_time_jst,event_type,ticker,market,importance,lock_scope,days_before,days_after,restriction,notes

常用 restriction：

- OBSERVE_ONLY
- FREEZE_NEW_BUYS
- TRIAL_ONLY
- DISABLE_LEVERAGED
- DISABLE_SINGLE_STOCK

## 7. 当前稳定版本判断

V16.8 stable candidate 是结构稳定候选，不是实盘批准版本。

下一阶段应进入：

- V16.8 stable freeze
- V17 Korea / SBI watch-only extension
- 或先继续强化 V16 数据更新和事件输入
"""

    path.write_text(text, encoding="utf-8")
    return path


def _create_snapshot() -> tuple[Path, Path, list[str]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = ensure_dir(ROOT / "archive" / "v16_stable" / f"v16_8_stable_candidate_{stamp}")
    copied: list[str] = []

    for rel in CORE_FILES:
        src = ROOT / rel
        if not src.exists():
            continue

        dst = archive_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel)

    zip_path = archive_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in archive_dir.rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(archive_dir))

    return archive_dir, zip_path, copied


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stable_dir = ensure_dir(OUTPUTS_V16 / "stable")
    cleanup_dir = ensure_dir(OUTPUTS_V16 / "cleanup")

    operation_readme = _write_operation_readme()
    removed_pycache = _remove_pycache()
    archive_dir, zip_path, copied = _create_snapshot()

    report_path = stable_dir / "V16_8_STABLE_CANDIDATE_REPORT.md"
    cleanup_path = cleanup_dir / "V16_8_CLEANUP_REPORT.md"
    json_path = stable_dir / "V16_8_STABLE_CANDIDATE_REPORT.json"

    lines: list[str] = []
    lines.append("# V16.8 Stable Candidate Report")
    lines.append("")
    lines.append(f"生成时间：`{generated_at}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append("V16.8 stable candidate 已生成。")
    lines.append("")
    lines.append("这是结构稳定候选，不是实盘批准版本。")
    lines.append("")
    lines.append("## 2. 核心产物")
    lines.append("")
    lines.append(f"- Operation README：`{operation_readme.relative_to(ROOT)}`")
    lines.append(f"- Snapshot directory：`{archive_dir.relative_to(ROOT)}`")
    lines.append(f"- Snapshot zip：`{zip_path.relative_to(ROOT)}`")
    lines.append("")
    lines.append("## 3. Snapshot 文件数量")
    lines.append("")
    lines.append(f"- copied_files：`{len(copied)}`")
    lines.append("")
    lines.append("## 4. 每日核心阅读文件")
    lines.append("")
    lines.append("1. `V16_DAILY_README.md`")
    lines.append("2. `outputs\\v16\\execution\\V16_EXECUTION_TICKER_SUMMARY.md`")
    lines.append("3. `outputs\\v16\\positions\\V16_POSITION_REVIEW.md`")
    lines.append("4. `outputs\\v16\\risk\\V16_EVENT_GATE.md`")
    lines.append("5. `outputs\\v16\\risk\\V16_BEHAVIOR_GUARD.md`")
    lines.append("6. `outputs\\v16\\feedback\\V16_TRADE_FEEDBACK.md`")
    lines.append("")
    lines.append("## 5. 当前限制")
    lines.append("")
    lines.append("- 不自动下单")
    lines.append("- 不产生实盘买入指令")
    lines.append("- Event Gate 仍依赖手动事件日历")
    lines.append("- Trade Feedback 仍依赖手动成交回填")
    lines.append("- 价格数据必须先更新到 FRESH 才能进入 PLAN_ONLY_TRIGGERED")
    lines.append("")
    lines.append("## 6. 下一步建议")
    lines.append("")
    lines.append("如果 V16.8 health check 为 OK，可以冻结为 V16.8-stable-candidate。")
    lines.append("下一阶段再决定是继续做 V16.8-stable freeze，还是进入 V17 韩国市场观察模块。")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    cleanup_lines: list[str] = []
    cleanup_lines.append("# V16.8 Cleanup Report")
    cleanup_lines.append("")
    cleanup_lines.append(f"生成时间：`{generated_at}`")
    cleanup_lines.append("")
    cleanup_lines.append("## 清理内容")
    cleanup_lines.append("")
    cleanup_lines.append("本次只清理 Python __pycache__，不删除源码、配置、状态、数据或输出报告。")
    cleanup_lines.append("")
    cleanup_lines.append("| removed |")
    cleanup_lines.append("|---|")
    if removed_pycache:
        for item in removed_pycache:
            cleanup_lines.append(f"| `{item}` |")
    else:
        cleanup_lines.append("| 无 |")
    cleanup_lines.append("")

    cleanup_path.write_text("\n".join(cleanup_lines), encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "operation_readme": str(operation_readme.relative_to(ROOT)),
        "archive_dir": str(archive_dir.relative_to(ROOT)),
        "zip_path": str(zip_path.relative_to(ROOT)),
        "copied_files": copied,
        "removed_pycache": removed_pycache,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("")
    print("V16 stable candidate completed.")
    print(f"- operation_readme: {operation_readme}")
    print(f"- report: {report_path}")
    print(f"- cleanup: {cleanup_path}")
    print(f"- snapshot: {archive_dir}")
    print(f"- zip: {zip_path}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
