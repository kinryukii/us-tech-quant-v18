from __future__ import annotations

from datetime import datetime
import csv
import json

from qutumn.common.paths import OUTPUTS_V16, ensure_dir
from qutumn.data.historical_prices import load_backtest_config


def _to_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _decide(row: dict, thresholds: dict) -> tuple[str, str]:
    status = row.get("status", "")

    if status != "METRICS_AVAILABLE":
        return "WATCH", "Metrics are not available."

    strategy = row.get("strategy_name", "")
    annual = _to_float(row.get("annual_return_pct"))
    dd = _to_float(row.get("max_drawdown_pct"))
    sharpe = _to_float(row.get("sharpe"))
    trades = _to_float(row.get("trade_count"))
    executable = _to_float(row.get("cap_constrained_executable_ratio_pct"))
    trading_days = _to_float(row.get("trading_days"))

    min_days = float(thresholds.get("min_trading_days", 500))
    min_sharpe = float(thresholds.get("min_sharpe_for_candidate", 0.5))
    max_dd_limit = float(thresholds.get("max_drawdown_limit_pct", -35))
    min_annual = float(thresholds.get("min_annual_return_pct", 3))
    min_executable = float(thresholds.get("min_executable_ratio_pct", 20))

    if trading_days is None or trading_days < min_days:
        return "WATCH", "Trading history is too short."

    if trades is None or trades <= 0:
        return "REJECTED_RULE_FIX_REQUIRED", "No trades were generated. Strategy rules need repair."

    if dd is not None and dd < max_dd_limit:
        return "WATCH_HIGH_DRAWDOWN", "Drawdown exceeds current research limit."

    if sharpe is None or sharpe < min_sharpe:
        return "WATCH_LOW_SHARPE", "Sharpe is below candidate threshold."

    if annual is None or annual < min_annual:
        return "WATCH_LOW_RETURN", "Annual return is below candidate threshold."

    if executable is not None and executable < min_executable:
        return "WATCH_EXECUTION_CONSTRAINT", "Small-account executability is weak."

    if strategy == "leveraged_tactical":
        return "WATCH_HIGH_RISK", "Leveraged ETF strategy requires Event Gate and Behavior Guard before any approval."

    return "BACKTEST_PASS_CANDIDATE", "Backtest metrics pass initial research thresholds, but not approved for live trading."


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_dir = ensure_dir(OUTPUTS_V16 / "backtest")
    metrics_path = out_dir / "V16_BACKTEST_METRICS.csv"
    grade_csv = out_dir / "V16_STRATEGY_GRADE.csv"
    grade_md = out_dir / "V16_STRATEGY_GRADE.md"
    approval_path = out_dir / "V16_STRATEGY_APPROVAL.md"

    cfg = load_backtest_config()
    thresholds = cfg.get("grading", {})
    if not isinstance(thresholds, dict):
        thresholds = {}

    rows: list[dict] = []

    if metrics_path.exists():
        with metrics_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                decision, reason = _decide(row, thresholds)
                row["research_decision"] = decision
                row["decision_reason"] = reason
                rows.append(row)

    fieldnames = [
        "strategy_name",
        "status",
        "research_decision",
        "decision_reason",
        "annual_return_pct",
        "benchmark_annual_return_pct",
        "max_drawdown_pct",
        "sharpe",
        "trade_count",
        "turnover_pct",
        "estimated_cost_drag_pct",
        "avg_exposure_pct",
        "cap_constrained_executable_ratio_pct",
    ]

    with grade_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    pass_count = sum(1 for row in rows if row.get("research_decision") == "BACKTEST_PASS_CANDIDATE")
    watch_count = sum(1 for row in rows if str(row.get("research_decision", "")).startswith("WATCH"))
    rejected_count = sum(1 for row in rows if str(row.get("research_decision", "")).startswith("REJECTED"))

    lines: list[str] = []
    lines.append("# V16 Strategy Grade")
    lines.append("")
    lines.append(f"生成时间：`{generated_at}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append("V16.2C 已经生成成本感知回测后的研究分级。")
    lines.append("")
    lines.append(f"- PASS_CANDIDATE：`{pass_count}`")
    lines.append(f"- WATCH：`{watch_count}`")
    lines.append(f"- REJECTED：`{rejected_count}`")
    lines.append("")
    lines.append("重要限制：PASS_CANDIDATE 不是实盘批准，只代表可以进入下一阶段研究。")
    lines.append("")
    lines.append("## 2. 策略分级表")
    lines.append("")
    lines.append("| 策略 | 决策 | 年化% | 最大回撤% | Sharpe | 交易次数 | 真实可执行率% | 原因 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")

    for row in rows:
        lines.append(
            f"| `{row.get('strategy_name')}` | `{row.get('research_decision')}` | "
            f"`{row.get('annual_return_pct')}` | `{row.get('max_drawdown_pct')}` | "
            f"`{row.get('sharpe')}` | `{row.get('trade_count')}` | "
            f"`{row.get('cap_constrained_executable_ratio_pct')}` | {row.get('decision_reason')} |"
        )

    lines.append("")
    lines.append("## 3. 下一步")
    lines.append("")
    lines.append("下一步进入 V16.3 Execution Plan：把候选策略转成乐天美股可执行计划。")
    lines.append("")

    grade_md.write_text("\n".join(lines), encoding="utf-8")

    status = "GRADED"

    approval_text = f"""# V16 Strategy Approval

生成时间：`{generated_at}`

状态：**{status}**

## 当前判断

V16.2C 已经完成：

- 策略结构检查
- 基础历史回测
- 交易成本与滑点估算
- leveraged_tactical 基准上下文修复
- 初版研究分级

## 当前分级

- BACKTEST_PASS_CANDIDATE：`{pass_count}`
- WATCH：`{watch_count}`
- REJECTED：`{rejected_count}`

## 重要限制

即使出现 BACKTEST_PASS_CANDIDATE，也不代表可以进入实盘。

还缺：

- Event Gate 真实事件日历
- Execution Plan 乐天真实可执行计划
- Trade Feedback 真实成交反馈
- Position Review 持仓生命周期
- Behavior Guard 心理纪律约束

## 当前最高允许阶段

当前最高允许阶段：BACKTEST_PASS_CANDIDATE。

不能进入：

- PAPER_TRADING
- SMALL_REAL_TRIAL
- MAIN_EXECUTION
"""

    approval_path.write_text(approval_text, encoding="utf-8")

    payload_path = out_dir / "V16_STRATEGY_GRADE.json"
    payload = {
        "generated_at": generated_at,
        "pass_candidate": pass_count,
        "watch": watch_count,
        "rejected": rejected_count,
        "rows": rows,
    }
    payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("")
    print("V16 strategy grading completed.")
    print(f"- grade_md: {grade_md}")
    print(f"- grade_csv: {grade_csv}")
    print(f"- approval: {approval_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
