#!/usr/bin/env python
"""V18.39C shadow risk model preview / LEAN-inspired risk preview.

Read-only report layer. It consumes V18.39A alpha signal objects and V18.39B
portfolio target previews, then evaluates concentration, feasibility, signal
quality, and data/risk tag diagnostics. It never uses real accounts, creates
orders, or mutates ledgers/state.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


MODE = "READ_ONLY_SHADOW_RISK_MODEL_PREVIEW"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

DETAIL_COLUMNS = [
    "run_id",
    "generated_at",
    "scenario_name",
    "simulated_capital_usd",
    "scenario_type",
    "included_ticker_count",
    "target_weight_sum",
    "max_single_name_weight",
    "top5_weight_sum",
    "top10_weight_sum",
    "concentration_status",
    "price_available_count",
    "price_missing_count",
    "whole_share_feasible_count",
    "too_small_for_one_share_count",
    "too_small_pct",
    "feasibility_status",
    "long_candidate_count",
    "watch_count",
    "avoid_count",
    "high_confidence_count",
    "medium_confidence_count",
    "low_confidence_count",
    "pending_forward_outcome_count",
    "signal_quality_status",
    "severe_overheat_count",
    "data_quality_warning_count",
    "freeze_missing_count",
    "risk_tag_count",
    "data_quality_status",
    "scenario_risk_level",
    "scenario_risk_reason",
    "recommended_operator_interpretation",
    "official_decision_impact",
    "auto_trade",
    "order_execution_used",
    "notes",
]

SUMMARY_COLUMNS = [
    "total_scenario_capital_rows",
    "low_risk_count",
    "medium_risk_count",
    "high_risk_count",
    "research_only_count",
    "unknown_risk_count",
    "concentration_watch_count",
    "high_concentration_count",
    "small_capital_constraint_count",
    "price_missing_risk_count",
    "forward_evidence_pending_count",
    "data_quality_review_count",
    "command_status_current_blocking_count",
    "daily_run_usable",
    "overall_risk_preview_status",
    "next_recommended_step",
]

RULE_COLUMNS = ["rule_id", "rule_name", "threshold", "triggered_level", "description"]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel in ["outputs/v18/risk_preview", "outputs/v18/read_center", "outputs/v18/ops"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        out = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        out = df[columns]
    out.to_csv(path, index=False, encoding="utf-8")


def safe_read_csv(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding=enc), "OK"
        except Exception:
            continue
    return pd.DataFrame(), "READ_ERROR"


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if text == "":
            return default
        return float(text)
    except Exception:
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip()
        if text == "":
            return default
        return int(float(text))
    except Exception:
        return default


def split_tags(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [tag.strip() for tag in text.replace("|", ";").split(";") if tag.strip()]


def rules_df() -> pd.DataFrame:
    rows = [
        {
            "rule_id": "CONC_MAX_GT_10",
            "rule_name": "Max single-name weight watch",
            "threshold": "max_single_name_weight > 0.10",
            "triggered_level": "WATCH_CONCENTRATED",
            "description": "Single-name target weight above 10% should be reviewed for concentration.",
        },
        {
            "rule_id": "CONC_MAX_GT_20",
            "rule_name": "Max single-name weight high",
            "threshold": "max_single_name_weight > 0.20",
            "triggered_level": "HIGH_CONCENTRATION",
            "description": "Single-name target weight above 20% is high concentration in this preview.",
        },
        {
            "rule_id": "CONC_TOP5_GT_50",
            "rule_name": "Top5 concentration watch",
            "threshold": "top5_weight_sum > 0.50",
            "triggered_level": "WATCH_CONCENTRATED",
            "description": "Top five names above 50% should be reviewed.",
        },
        {
            "rule_id": "CONC_TOP5_GT_70",
            "rule_name": "Top5 concentration high",
            "threshold": "top5_weight_sum > 0.70",
            "triggered_level": "HIGH_CONCENTRATION",
            "description": "Top five names above 70% is high concentration in this preview.",
        },
        {
            "rule_id": "FEAS_TOO_SMALL_GT_30",
            "rule_name": "Small capital whole-share constraint",
            "threshold": "too_small_pct > 0.30",
            "triggered_level": "SMALL_CAPITAL_CONSTRAINT",
            "description": "More than 30% too-small whole-share rows indicates small simulated capital constraints.",
        },
        {
            "rule_id": "FEAS_PRICE_MISSING",
            "rule_name": "Missing price risk",
            "threshold": "price_missing_count > 0",
            "triggered_level": "PRICE_MISSING_RISK",
            "description": "Missing prices make share feasibility unknown but do not create a trading failure.",
        },
        {
            "rule_id": "SIG_FORWARD_PENDING",
            "rule_name": "Forward evidence pending",
            "threshold": "pending_forward_outcome_count > 0",
            "triggered_level": "FORWARD_EVIDENCE_PENDING",
            "description": "Pending forward evidence is expected research state and does not block output generation.",
        },
        {
            "rule_id": "DATA_TAG_REVIEW",
            "rule_name": "Risk or data tag review",
            "threshold": "risk_tag_count > 0 or data_quality_warning_count > 0 or freeze_missing_count > 0",
            "triggered_level": "REVIEW_NEEDED",
            "description": "Risk, data-quality, or freeze gaps should be reviewed before interpreting the preview.",
        },
        {
            "rule_id": "SAFETY_NO_EXECUTION",
            "rule_name": "No execution safety",
            "threshold": "AUTO_TRADE DISABLED; ORDER_EXECUTION_USED FALSE; BROKER_API_USED FALSE",
            "triggered_level": "PASS_REQUIRED",
            "description": "This module is report-only and must not create orders, broker instructions, or account-aware plans.",
        },
    ]
    return pd.DataFrame(rows, columns=RULE_COLUMNS)


def concentration_status(max_weight: float, top5_weight: float) -> str:
    if max_weight > 0.20 or top5_weight > 0.70:
        return "HIGH_CONCENTRATION"
    if max_weight > 0.10 or top5_weight > 0.50:
        return "WATCH_CONCENTRATED"
    return "OK"


def feasibility_status(scenario_type: str, price_missing: int, too_small_pct: float) -> str:
    if scenario_type == "RESEARCH_ONLY":
        return "RESEARCH_ONLY"
    if price_missing > 0:
        return "PRICE_MISSING_RISK"
    if too_small_pct > 0.30:
        return "SMALL_CAPITAL_CONSTRAINT"
    return "OK"


def signal_quality_status(scenario_type: str, pending: int, low: int, included: int) -> str:
    if scenario_type == "RESEARCH_ONLY":
        return "RESEARCH_ONLY"
    if included <= 0:
        return "UNKNOWN"
    if low > included * 0.50:
        return "TOO_MANY_LOW_CONFIDENCE"
    if pending > 0:
        return "FORWARD_EVIDENCE_PENDING"
    return "OK"


def data_quality_status(data_quality_warning_count: int, freeze_missing_count: int, risk_tag_count: int) -> str:
    if data_quality_warning_count > 0 or freeze_missing_count > 0 or risk_tag_count > 0:
        return "REVIEW_NEEDED"
    return "OK"


def scenario_risk(
    scenario_type: str,
    conc: str,
    feas: str,
    sig: str,
    data_status: str,
) -> tuple[str, str, str]:
    reasons: list[str] = []
    if scenario_type == "RESEARCH_ONLY":
        return "RESEARCH_ONLY", "Research-only watchlist scenario; not investable target risk.", "RESEARCH_ONLY_NOT_INVESTABLE"
    if conc == "HIGH_CONCENTRATION":
        reasons.append("high concentration")
    elif conc == "WATCH_CONCENTRATED":
        reasons.append("concentration watch")
    if feas == "PRICE_MISSING_RISK":
        reasons.append("missing price evidence")
    elif feas == "SMALL_CAPITAL_CONSTRAINT":
        reasons.append("small capital whole-share constraints")
    if sig == "FORWARD_EVIDENCE_PENDING":
        reasons.append("forward evidence pending")
    elif sig == "TOO_MANY_LOW_CONFIDENCE":
        reasons.append("too many low-confidence signals")
    if data_status == "REVIEW_NEEDED":
        reasons.append("risk/data tags need review")

    if conc == "HIGH_CONCENTRATION" or feas == "PRICE_MISSING_RISK":
        level = "HIGH"
    elif reasons:
        level = "MEDIUM"
    else:
        level = "LOW"

    if conc in {"HIGH_CONCENTRATION", "WATCH_CONCENTRATED"}:
        interp = "REVIEW_CONCENTRATION"
    elif feas in {"PRICE_MISSING_RISK", "SMALL_CAPITAL_CONSTRAINT"}:
        interp = "REVIEW_FEASIBILITY"
    elif sig == "FORWARD_EVIDENCE_PENDING":
        interp = "PREVIEW_USABLE_BUT_WAIT_FORWARD_EVIDENCE"
    elif level == "LOW":
        interp = "PREVIEW_USABLE"
    else:
        interp = "PREVIEW_USABLE_BUT_WAIT_FORWARD_EVIDENCE"
    return level, "; ".join(reasons) if reasons else "No material preview risk flags.", interp


def row_tag_count(rows: pd.DataFrame, column: str) -> int:
    if column not in rows.columns:
        return 0
    return sum(1 for value in rows[column].tolist() if split_tags(value))


def warning_tag_count(rows: pd.DataFrame) -> int:
    if "data_quality_tags" not in rows.columns:
        return 0
    warning_words = ("MISSING", "WARN", "UNKNOWN", "READ_ERROR", "NOT_AVAILABLE")
    count = 0
    for value in rows["data_quality_tags"].tolist():
        tags = split_tags(value)
        if any(any(word in tag.upper() for word in warning_words) for tag in tags):
            count += 1
    return count


def build_detail(root: Path, run_id: str, generated_at: str) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    preview_path = root / "outputs/v18/portfolio_preview/V18_39B_PORTFOLIO_TARGET_PREVIEW.csv"
    summary_path = root / "outputs/v18/portfolio_preview/V18_39B_PORTFOLIO_TARGET_SUMMARY.csv"
    alpha_path = root / "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_OBJECTS.csv"
    alpha_summary_path = root / "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_SUMMARY.csv"
    portfolio_diag_path = root / "outputs/v18/portfolio_preview/V18_39B_PORTFOLIO_TARGET_DIAGNOSTICS.csv"

    preview, preview_status = safe_read_csv(preview_path)
    target_summary, target_summary_status = safe_read_csv(summary_path)
    alpha, alpha_status = safe_read_csv(alpha_path)
    alpha_summary, alpha_summary_status = safe_read_csv(alpha_summary_path)
    portfolio_diag, portfolio_diag_status = safe_read_csv(portfolio_diag_path)
    read39a = parse_kv(root / "outputs/v18/ops/V18_39A_READ_FIRST.txt")
    read39b = parse_kv(root / "outputs/v18/ops/V18_39B_READ_FIRST.txt")
    read38c = parse_kv(root / "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt")

    if preview_status != "OK" or preview.empty:
        raise RuntimeError(f"Required V18.39B portfolio preview is not readable: {preview_status}")

    required = {"scenario_name", "simulated_capital_usd", "scenario_type", "ticker", "target_weight"}
    missing = sorted(required - set(preview.columns))
    if missing:
        raise RuntimeError(f"Required V18.39B preview columns are missing: {missing}")

    details: list[dict[str, Any]] = []
    group_cols = ["scenario_name", "simulated_capital_usd"]
    for (scenario_name, capital), rows in preview.groupby(group_cols, dropna=False, sort=True):
        rows = rows.copy()
        weights = [to_float(v) for v in rows.get("target_weight", pd.Series(dtype=str)).tolist()]
        weights_sorted = sorted(weights, reverse=True)
        included = int(len(rows))
        scenario_type = str(rows["scenario_type"].iloc[0]) if "scenario_type" in rows.columns and not rows.empty else "UNKNOWN"
        target_weight_sum = sum(weights)
        max_weight = max(weights) if weights else 0.0
        top5 = sum(weights_sorted[:5])
        top10 = sum(weights_sorted[:10])
        conc = concentration_status(max_weight, top5)

        latest_prices = rows.get("latest_price", pd.Series([""] * len(rows))).tolist()
        price_available = sum(1 for value in latest_prices if to_float(value, -1.0) > 0)
        price_missing = included - price_available
        feas_col = rows.get("whole_share_feasibility", pd.Series([""] * len(rows))).astype(str)
        whole_feasible = int((feas_col == "FEASIBLE").sum())
        too_small = int((feas_col == "TOO_SMALL_FOR_ONE_SHARE").sum())
        too_small_pct = too_small / included if included else 0.0
        feas = feasibility_status(scenario_type, price_missing, too_small_pct)

        directions = rows.get("alpha_direction", pd.Series([""] * len(rows))).astype(str)
        confidence = rows.get("alpha_confidence", pd.Series([""] * len(rows))).astype(str)
        forward = rows.get("forward_evidence_status", pd.Series([""] * len(rows))).astype(str)
        long_count = int((directions == "LONG_CANDIDATE").sum())
        watch_count = int((directions == "WATCH").sum())
        avoid_count = int((directions == "AVOID").sum())
        high_count = int((confidence == "HIGH").sum())
        medium_count = int((confidence == "MEDIUM").sum())
        low_count = int((confidence == "LOW").sum())
        pending_count = int(forward.str.contains("PENDING_FORWARD_OUTCOME", case=False, na=False).sum())
        sig = signal_quality_status(scenario_type, pending_count, low_count, included)

        overheat = rows.get("risk_tags", pd.Series([""] * len(rows))).astype(str)
        severe_overheat = int(overheat.str.contains("EXTREME|SEVERE_OVERHEAT|HIGH_OVERHEAT", case=False, na=False).sum())
        data_warning = warning_tag_count(rows)
        freeze = rows.get("freeze_status", pd.Series([""] * len(rows))).astype(str)
        freeze_missing = int((freeze.isin(["", "UNKNOWN", "NOT_IN_LATEST_FREEZE"])).sum())
        risk_count = row_tag_count(rows, "risk_tags")
        data_status = data_quality_status(data_warning, freeze_missing, risk_count)
        risk_level, risk_reason, interpretation = scenario_risk(scenario_type, conc, feas, sig, data_status)

        details.append(
            {
                "run_id": run_id,
                "generated_at": generated_at,
                "scenario_name": scenario_name,
                "simulated_capital_usd": capital,
                "scenario_type": scenario_type,
                "included_ticker_count": included,
                "target_weight_sum": f"{target_weight_sum:.10f}",
                "max_single_name_weight": f"{max_weight:.10f}",
                "top5_weight_sum": f"{top5:.10f}",
                "top10_weight_sum": f"{top10:.10f}",
                "concentration_status": conc,
                "price_available_count": price_available,
                "price_missing_count": price_missing,
                "whole_share_feasible_count": whole_feasible,
                "too_small_for_one_share_count": too_small,
                "too_small_pct": f"{too_small_pct:.6f}",
                "feasibility_status": feas,
                "long_candidate_count": long_count,
                "watch_count": watch_count,
                "avoid_count": avoid_count,
                "high_confidence_count": high_count,
                "medium_confidence_count": medium_count,
                "low_confidence_count": low_count,
                "pending_forward_outcome_count": pending_count,
                "signal_quality_status": sig,
                "severe_overheat_count": severe_overheat,
                "data_quality_warning_count": data_warning,
                "freeze_missing_count": freeze_missing,
                "risk_tag_count": risk_count,
                "data_quality_status": data_status,
                "scenario_risk_level": risk_level,
                "scenario_risk_reason": risk_reason,
                "recommended_operator_interpretation": interpretation,
                "official_decision_impact": "NONE",
                "auto_trade": "DISABLED",
                "order_execution_used": "FALSE",
                "notes": "Read-only risk preview only; not a trade risk engine and not an order plan.",
            }
        )

    detail = pd.DataFrame(details, columns=DETAIL_COLUMNS)
    context = {
        "preview_status": preview_status,
        "target_summary_status": target_summary_status,
        "alpha_status": alpha_status,
        "alpha_summary_status": alpha_summary_status,
        "portfolio_diag_status": portfolio_diag_status,
        "alpha_signal_count": len(alpha) if alpha_status == "OK" else read39a.get("TOTAL_SIGNAL_COUNT", ""),
        "portfolio_preview_rows": len(preview),
        "portfolio_summary_rows": len(target_summary) if target_summary_status == "OK" else "",
        "portfolio_diagnostic_fail_count": int((portfolio_diag["status"] == "FAIL").sum()) if portfolio_diag_status == "OK" and "status" in portfolio_diag.columns else 0,
        "command_status_current_blocking_count": read38c.get("CURRENT_FAIL_BLOCKING_COUNT", ""),
        "daily_run_usable": read38c.get("DAILY_RUN_USABLE", ""),
        "v18_39a_status": read39a.get("STATUS", ""),
        "v18_39b_status": read39b.get("STATUS", ""),
        "alpha_summary_rows": len(alpha_summary) if alpha_summary_status == "OK" else "",
    }
    return detail, rules_df(), context


def compact_summary(detail: pd.DataFrame, context: dict[str, Any]) -> pd.DataFrame:
    if detail.empty:
        row = {col: 0 for col in SUMMARY_COLUMNS}
        row.update(
            {
                "command_status_current_blocking_count": context.get("command_status_current_blocking_count", ""),
                "daily_run_usable": context.get("daily_run_usable", ""),
                "overall_risk_preview_status": "FAIL_V18_39C_SHADOW_RISK_MODEL_PREVIEW_BLOCKED",
                "next_recommended_step": "Fix required V18.39B portfolio preview input, then rerun V18.39C.",
            }
        )
        return pd.DataFrame([row], columns=SUMMARY_COLUMNS)

    high_risk = int((detail["scenario_risk_level"] == "HIGH").sum())
    medium_risk = int((detail["scenario_risk_level"] == "MEDIUM").sum())
    research_only = int((detail["scenario_risk_level"] == "RESEARCH_ONLY").sum())
    forward_pending = int((detail["signal_quality_status"] == "FORWARD_EVIDENCE_PENDING").sum())
    data_review = int((detail["data_quality_status"] == "REVIEW_NEEDED").sum())
    small_cap = int((detail["feasibility_status"] == "SMALL_CAPITAL_CONSTRAINT").sum())
    price_missing = int((detail["feasibility_status"] == "PRICE_MISSING_RISK").sum())
    concentration_watch = int((detail["concentration_status"] == "WATCH_CONCENTRATED").sum())
    high_conc = int((detail["concentration_status"] == "HIGH_CONCENTRATION").sum())

    if high_risk > 0:
        status = "WARN_V18_39C_SHADOW_RISK_MODEL_PREVIEW_REVIEW_NEEDED"
        next_step = "Review high-risk scenario diagnostics before using the preview for research interpretation."
    elif any(v > 0 for v in [medium_risk, small_cap, price_missing, forward_pending, data_review, concentration_watch, high_conc]):
        status = "WARN_V18_39C_SHADOW_RISK_MODEL_PREVIEW_REVIEW_NEEDED"
        next_step = "Preview is usable for research, but wait for forward evidence and review feasibility/data tags."
    else:
        status = "OK_V18_39C_SHADOW_RISK_MODEL_PREVIEW_READY"
        next_step = "Risk preview is ready for downstream read-only reporting."

    row = {
        "total_scenario_capital_rows": len(detail),
        "low_risk_count": int((detail["scenario_risk_level"] == "LOW").sum()),
        "medium_risk_count": medium_risk,
        "high_risk_count": high_risk,
        "research_only_count": research_only,
        "unknown_risk_count": int((detail["scenario_risk_level"] == "UNKNOWN").sum()),
        "concentration_watch_count": concentration_watch,
        "high_concentration_count": high_conc,
        "small_capital_constraint_count": small_cap,
        "price_missing_risk_count": price_missing,
        "forward_evidence_pending_count": forward_pending,
        "data_quality_review_count": data_review,
        "command_status_current_blocking_count": context.get("command_status_current_blocking_count", ""),
        "daily_run_usable": context.get("daily_run_usable", ""),
        "overall_risk_preview_status": status,
        "next_recommended_step": next_step,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def build_report(status: str, summary: pd.DataFrame, detail: pd.DataFrame, context: dict[str, Any]) -> str:
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    detail_lines = []
    if not detail.empty:
        for _, item in detail.sort_values(["scenario_name", "simulated_capital_usd"]).iterrows():
            detail_lines.append(
                f"- {item['scenario_name']} / {item['simulated_capital_usd']} USD: "
                f"{item['scenario_risk_level']}；{item['scenario_risk_reason']}；"
                f"建议={item['recommended_operator_interpretation']}"
            )
    scenario_text = "\n".join(detail_lines[:40]) if detail_lines else "- 暂无 scenario detail。"
    return f"""# V18.39C Shadow Risk Model Preview 报告

## 1. 今日结论
- 状态: {status}
- Scenario + capital rows: {row.get('total_scenario_capital_rows', '')}
- Low / Medium / High / Research-only: {row.get('low_risk_count', '')} / {row.get('medium_risk_count', '')} / {row.get('high_risk_count', '')} / {row.get('research_only_count', '')}
- Daily run usable: {row.get('daily_run_usable', '')}

## 2. Shadow Risk Model Preview 是什么
这是对 V18.39B 组合目标预览的只读风险检查，参考 LEAN Risk Management 的分层思想，但只做研究诊断。它检查集中度、整股可买性、信号质量、forward outcome pending、过热与数据质量标签。

## 3. 总体风险分布
- LOW: {row.get('low_risk_count', '')}
- MEDIUM: {row.get('medium_risk_count', '')}
- HIGH: {row.get('high_risk_count', '')}
- RESEARCH_ONLY: {row.get('research_only_count', '')}
- UNKNOWN: {row.get('unknown_risk_count', '')}

## 4. 权重集中度风险
- Concentration watch rows: {row.get('concentration_watch_count', '')}
- High concentration rows: {row.get('high_concentration_count', '')}
- 规则: 单票 >10% 或 Top5 >50% 进入 watch；单票 >20% 或 Top5 >70% 进入 high。

## 5. 小资金整股可买性风险
- Small capital constraint rows: {row.get('small_capital_constraint_count', '')}
- Price missing risk rows: {row.get('price_missing_risk_count', '')}
- 小资金整股约束不代表系统阻断，只说明模拟资金较小时，部分目标无法买入一整股。

## 6. 信号质量与 forward evidence pending
- Forward evidence pending rows: {row.get('forward_evidence_pending_count', '')}
- Pending forward outcome 是当前研究层的可等待状态，不等同于交易阻断。

## 7. 数据质量 / freeze / overheat 风险
- Data quality review rows: {row.get('data_quality_review_count', '')}
- Alpha input status: {context.get('v18_39a_status', '')}
- Portfolio input status: {context.get('v18_39b_status', '')}

## 8. 每个 scenario 的风险解释
{scenario_text}

## 9. 为什么这不是交易风控/不是下单
- 不使用真实账户现金或持仓。
- 不调用 broker/API。
- 不生成 order ticket、broker instruction、executable trade file 或 account-aware trade plan。
- 输出只用于模拟组合目标的研究风险预览。

## 10. Safety / no-impact confirmation
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- ORDER_EXECUTION_USED: FALSE
- BROKER_API_USED: FALSE
- REAL_ACCOUNT_USED: FALSE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE

## 11. 下一步建议
{row.get('next_recommended_step', '')}
"""


def build_read_first(status: str, run_id: str, generated_at: str, summary: pd.DataFrame) -> str:
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    fields = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "GENERATED_AT": generated_at,
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "ORDER_EXECUTION_USED": "FALSE",
        "BROKER_API_USED": "FALSE",
        "REAL_ACCOUNT_USED": "FALSE",
        "RANKING_MODIFIED": "FALSE",
        "FACTOR_WEIGHTS_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
        "ACCOUNT_STATE_MODIFIED": "FALSE",
        "TOTAL_SCENARIO_CAPITAL_ROWS": row.get("total_scenario_capital_rows", ""),
        "LOW_RISK_COUNT": row.get("low_risk_count", ""),
        "MEDIUM_RISK_COUNT": row.get("medium_risk_count", ""),
        "HIGH_RISK_COUNT": row.get("high_risk_count", ""),
        "RESEARCH_ONLY_COUNT": row.get("research_only_count", ""),
        "UNKNOWN_RISK_COUNT": row.get("unknown_risk_count", ""),
        "CONCENTRATION_WATCH_COUNT": row.get("concentration_watch_count", ""),
        "HIGH_CONCENTRATION_COUNT": row.get("high_concentration_count", ""),
        "SMALL_CAPITAL_CONSTRAINT_COUNT": row.get("small_capital_constraint_count", ""),
        "PRICE_MISSING_RISK_COUNT": row.get("price_missing_risk_count", ""),
        "FORWARD_EVIDENCE_PENDING_COUNT": row.get("forward_evidence_pending_count", ""),
        "DATA_QUALITY_REVIEW_COUNT": row.get("data_quality_review_count", ""),
        "COMMAND_STATUS_CURRENT_BLOCKING_COUNT": row.get("command_status_current_blocking_count", ""),
        "DAILY_RUN_USABLE": row.get("daily_run_usable", ""),
        "OVERALL_RISK_PREVIEW_STATUS": row.get("overall_risk_preview_status", status),
        "NEXT_RECOMMENDED_STEP": row.get("next_recommended_step", ""),
    }
    return "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n"


def run(root: Path) -> int:
    ensure_dirs(root)
    run_id = f"V18_39C_SHADOW_RISK_MODEL_PREVIEW_{now_ts()}"
    generated_at = now_iso()
    out_dir = root / "outputs/v18/risk_preview"
    read_center = root / "outputs/v18/read_center"
    ops = root / "outputs/v18/ops"
    try:
        detail, rules, context = build_detail(root, run_id, generated_at)
        summary = compact_summary(detail, context)
        status = str(summary.iloc[0]["overall_risk_preview_status"])
    except Exception as exc:
        detail = pd.DataFrame(columns=DETAIL_COLUMNS)
        rules = rules_df()
        context = {"command_status_current_blocking_count": "", "daily_run_usable": ""}
        summary = compact_summary(detail, context)
        status = "FAIL_V18_39C_SHADOW_RISK_MODEL_PREVIEW_BLOCKED"
        summary.loc[0, "overall_risk_preview_status"] = status
        summary.loc[0, "next_recommended_step"] = f"Fix required V18.39B portfolio preview input, then rerun V18.39C. Error: {type(exc).__name__}: {exc}"

    write_csv(out_dir / "V18_39C_SHADOW_RISK_PREVIEW_SUMMARY.csv", summary, SUMMARY_COLUMNS)
    write_csv(out_dir / "V18_39C_SHADOW_RISK_PREVIEW_DETAIL.csv", detail, DETAIL_COLUMNS)
    write_csv(out_dir / "V18_39C_SHADOW_RISK_RULES.csv", rules, RULE_COLUMNS)
    report = build_report(status, summary, detail, context)
    write_text(read_center / "V18_39C_SHADOW_RISK_MODEL_PREVIEW_REPORT.md", report)
    write_text(read_center / "V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md", report)
    write_text(ops / "V18_39C_READ_FIRST.txt", build_read_first(status, run_id, generated_at, summary))
    return 1 if status.startswith("FAIL_") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
