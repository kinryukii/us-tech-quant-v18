#!/usr/bin/env python
"""V18.38C-R1 command center status normalization / operator classifier.

Read-only reporting layer. R1 separates current critical/supporting evidence
from historical legacy READ_FIRST/report files so old failures do not decide
today's operator status.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


MODE = "READ_ONLY_COMMAND_STATUS_NORMALIZATION_R1"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

CURRENT_CRITICAL = {
    "outputs/v18/ops/V18_38A_READ_FIRST.txt",
    "outputs/v18/ops/V18_38B_READ_FIRST.txt",
    "outputs/v18/ops/V18_37C_READ_FIRST.txt",
    "outputs/v18/ops/V18_36A_READ_FIRST.txt",
    "outputs/v18/ops/V18_35A_READ_FIRST.txt",
    "outputs/v18/ops/V18_35B_READ_FIRST.txt",
    "outputs/v18/ops/V18_35C_READ_FIRST.txt",
    "outputs/v18/ops/V18_35F_READ_FIRST.txt",
    "outputs/v18/ops/V18_35G_READ_FIRST.txt",
    "outputs/v18/ops/V18_34B_READ_FIRST.txt",
    "outputs/v18/ops/V18_34C_READ_FIRST.txt",
    "outputs/v18/ops/V18_33A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
}

CURRENT_SUPPORTING = {
    "outputs/v18/read_center/V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md",
    "outputs/v18/read_center/V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md",
    "outputs/v18/read_center/V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md",
    "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md",
    "outputs/v18/read_center/V18_CURRENT_FULL_UNIVERSE_RECOMPUTE.md",
    "outputs/v18/read_center/V18_CURRENT_UNIVERSE_TO_CANDIDATE_AUDIT.md",
    "outputs/v18/read_center/V18_CURRENT_CANDIDATE_SOURCE_NORMALIZATION.md",
    "outputs/v18/read_center/V18_CURRENT_CANDIDATE_SOURCE_DEPENDENCY_REVIEW.md",
}

DETAIL_COLUMNS = [
    "source_name",
    "source_path",
    "exists",
    "source_scope",
    "affects_overall_status",
    "legacy_status",
    "is_current_alias",
    "status_raw",
    "mode",
    "run_id",
    "generated_at",
    "normalized_status",
    "severity",
    "is_blocking",
    "is_expected_pending",
    "safety_status",
    "current_blocking_reason",
    "stale_age_hours",
    "notes",
]

SUMMARY_COLUMNS = [
    "total_sources_scanned",
    "existing_sources",
    "missing_optional_sources",
    "missing_expected_sources",
    "ok_ready_count",
    "expected_pending_count",
    "account_template_warn_count",
    "research_not_ready_count",
    "review_needed_non_blocking_count",
    "unknown_review_count",
    "current_critical_count",
    "current_supporting_count",
    "historical_legacy_count",
    "unknown_legacy_count",
    "current_fail_blocking_count",
    "legacy_fail_count",
    "current_data_provider_warn_count",
    "legacy_data_provider_warn_count",
    "current_report_stale_warn_count",
    "legacy_report_stale_warn_count",
    "legacy_warn_count",
    "legacy_unknown_review_count",
    "historical_issues_present",
    "current_issues_present",
    "overall_operator_status",
    "daily_run_usable",
    "forward_research_usable",
    "trading_execution_allowed",
    "next_recommended_step",
]

RULE_ROWS = [
    {
        "rule_id": "R1_001",
        "rule_name": "Source scope controls overall impact",
        "match_pattern": "CURRENT_CRITICAL/CURRENT_SUPPORTING vs HISTORICAL_LEGACY/UNKNOWN_LEGACY",
        "normalized_status": "SCOPE_APPLIED",
        "severity": "INFO",
        "description": "Only current critical and selected current supporting evidence can affect today's overall operator status.",
    },
    {
        "rule_id": "R1_002",
        "rule_name": "Current safety invariant",
        "match_pattern": "AUTO_TRADE not DISABLED, AUTO_SELL not DISABLED, BROKER_API_USED TRUE, ORDER_EXECUTION_USED TRUE, OFFICIAL_DECISION_IMPACT not NONE",
        "normalized_status": "FAIL_BLOCKING",
        "severity": "BLOCKING",
        "description": "Current critical/supporting sources with active safety violations are true blocking failures.",
    },
    {
        "rule_id": "R1_003",
        "rule_name": "Historical fail isolation",
        "match_pattern": "STATUS begins with FAIL_ in HISTORICAL_LEGACY or UNKNOWN_LEGACY",
        "normalized_status": "LEGACY_FAIL",
        "severity": "WARN",
        "description": "Old historical failures are retained as evidence but do not make today's daily run unusable.",
    },
    {
        "rule_id": "R1_004",
        "rule_name": "Forward pending is expected",
        "match_pattern": "PENDING_FORWARD, ANY_FORWARD_OUTCOME_AVAILABLE FALSE, READY_FOR_FACTOR_FORWARD_ATTRIBUTION FALSE",
        "normalized_status": "EXPECTED_PENDING_FORWARD_OUTCOME",
        "severity": "INFO",
        "description": "Forward outcome waiting is expected until future price horizons mature.",
    },
    {
        "rule_id": "R1_005",
        "rule_name": "Provider warning scope split",
        "match_pattern": "yfinance, historical provider, price cache, preflight",
        "normalized_status": "DATA_PROVIDER_WARN or LEGACY_DATA_PROVIDER_WARN",
        "severity": "WARN",
        "description": "Provider warnings are split into current and legacy buckets by source scope.",
    },
    {
        "rule_id": "R1_006",
        "rule_name": "Stale warning scope split",
        "match_pattern": "stale current report or historical stale report",
        "normalized_status": "REPORT_STALE_WARN or LEGACY_REPORT_STALE_WARN",
        "severity": "WARN",
        "description": "Stale warnings in legacy files are not current blocking issues.",
    },
    {
        "rule_id": "R1_007",
        "rule_name": "Missing current critical review",
        "match_pattern": "CURRENT_CRITICAL source missing",
        "normalized_status": "MISSING_CURRENT_CRITICAL_REVIEW",
        "severity": "WARN",
        "description": "Missing current critical sources need review, but do not automatically block if the module was not run.",
    },
    {
        "rule_id": "R1_008",
        "rule_name": "Missing current supporting",
        "match_pattern": "CURRENT_SUPPORTING source missing",
        "normalized_status": "MISSING_SUPPORTING",
        "severity": "WARN",
        "description": "Missing supporting current reports are non-blocking warnings.",
    },
]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel_path in ["outputs/v18/ops", "outputs/v18/read_center"]:
        (root / rel_path).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    out = df[columns] if not df.empty else pd.DataFrame(columns=columns)
    out.to_csv(path, index=False, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def parse_kv(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper()
        if key:
            data[key] = value.strip()
    return data


def source_text(kv: dict[str, str]) -> str:
    return " ".join(f"{k}={v}" for k, v in kv.items()).upper()


def contains_any(text: str, needles: list[str]) -> bool:
    text = text.upper()
    return any(needle.upper() in text for needle in needles)


def age_hours(path: Path) -> str:
    if not path.exists():
        return ""
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return f"{age.total_seconds() / 3600:.2f}"


def generated_today(kv: dict[str, str], path: Path) -> bool:
    today = datetime.now().date()
    raw = kv.get("GENERATED_AT", "")
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date() == today
        except Exception:
            return raw.startswith(today.isoformat())
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime).date() == today
    return False


def source_scope(root: Path, path: Path) -> str:
    path_rel = rel(root, path)
    if path_rel in CURRENT_CRITICAL:
        return "CURRENT_CRITICAL"
    if path_rel in CURRENT_SUPPORTING:
        return "CURRENT_SUPPORTING"
    if path_rel.startswith("outputs/v18/ops/") and path.name.endswith("READ_FIRST.txt"):
        return "HISTORICAL_LEGACY"
    if path_rel.startswith("outputs/v18/read_center/"):
        return "UNKNOWN_LEGACY"
    return "UNKNOWN_LEGACY"


def current_alias(scope: str, path: Path) -> bool:
    return scope in {"CURRENT_CRITICAL", "CURRENT_SUPPORTING"} or path.name.startswith("V18_CURRENT")


def safety_status(kv: dict[str, str], current: bool) -> tuple[str, list[str]]:
    issues: list[str] = []
    if not current:
        return "SAFETY_LEGACY_NOT_OVERALL", issues
    if kv.get("AUTO_TRADE", AUTO_TRADE).upper() != AUTO_TRADE:
        issues.append("AUTO_TRADE is not DISABLED")
    if kv.get("AUTO_SELL", AUTO_SELL).upper() != AUTO_SELL:
        issues.append("AUTO_SELL is not DISABLED")
    if kv.get("OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT).upper() != OFFICIAL_DECISION_IMPACT:
        issues.append("OFFICIAL_DECISION_IMPACT is not NONE")
    if kv.get("BROKER_API_USED", "FALSE").upper() == "TRUE":
        issues.append("BROKER_API_USED is TRUE")
    if kv.get("ORDER_EXECUTION_USED", "FALSE").upper() == "TRUE":
        issues.append("ORDER_EXECUTION_USED is TRUE")
    return ("SAFETY_BLOCKING" if issues else "SAFETY_OK"), issues


def is_legacy_scope(scope: str) -> bool:
    return scope in {"HISTORICAL_LEGACY", "UNKNOWN_LEGACY"}


def classify_existing(path: Path, kv: dict[str, str], scope: str) -> tuple[str, str, bool, bool, str, str, str]:
    status = kv.get("STATUS", "").strip()
    status_upper = status.upper()
    text = source_text(kv)
    current = scope in {"CURRENT_CRITICAL", "CURRENT_SUPPORTING"}
    legacy = is_legacy_scope(scope)
    safe, safety_issues = safety_status(kv, current)
    blocking_reason = ""

    if safety_issues:
        blocking_reason = "; ".join(safety_issues)
        return "FAIL_BLOCKING", "BLOCKING", True, False, safe, blocking_reason, blocking_reason

    if contains_any(text, ["PENDING_NOT_ENOUGH_FUTURE_PRICES", "PENDING_FORWARD_OUTCOME"]):
        return "EXPECTED_PENDING_FORWARD_OUTCOME", "INFO", False, True, safe, "", "Forward price horizon has not matured"
    if kv.get("ANY_FORWARD_OUTCOME_AVAILABLE", "").upper() == "FALSE" or kv.get("READY_FOR_FACTOR_FORWARD_ATTRIBUTION", "").upper() == "FALSE":
        return "EXPECTED_PENDING_FORWARD_OUTCOME", "INFO", False, True, safe, "", "Forward outcome or attribution readiness is FALSE"

    if contains_any(text, ["YFINANCE", "HISTORICAL PROVIDER", "HISTORICAL_PROVIDER", "PRICE CACHE", "PRICE_CACHE", "PREFLIGHT"]):
        if legacy:
            return "LEGACY_DATA_PROVIDER_WARN", "WARN", False, False, safe, "", "Legacy data provider, yfinance, preflight, or price-cache warning"
        return "DATA_PROVIDER_WARN", "WARN", False, False, safe, "", "Current data provider, yfinance, preflight, or price-cache warning"

    if contains_any(text, ["WARN_TEMPLATE_EMPTY_ACCOUNT", "ACCOUNT_STATE", "EMPTY_ACCOUNT", "TEMPLATE_ACCOUNT"]):
        return "ACCOUNT_TEMPLATE_WARN", "WARN", False, False, safe, "", "Account template or account-state quality warning"

    if status_upper.startswith("FAIL_"):
        if legacy or scope == "CURRENT_SUPPORTING":
            return "LEGACY_FAIL" if legacy else "REVIEW_NEEDED_NON_BLOCKING", "WARN", False, False, safe, "", "Explicit FAIL_ status outside current critical blocking scope"
        blocking_reason = "Explicit FAIL_ status in current critical source"
        return "FAIL_BLOCKING", "BLOCKING", True, False, safe, blocking_reason, blocking_reason

    if not generated_today(kv, path):
        if legacy:
            return "LEGACY_REPORT_STALE_WARN", "WARN", False, False, safe, "", "Legacy source is stale or has no current generated date"
        if scope == "CURRENT_SUPPORTING":
            return "REPORT_STALE_WARN", "WARN", False, False, safe, "", "Current supporting report does not appear to be generated today"

    if contains_any(text, ["MISSING_FACTOR", "MISSING_INPUT_EXPERIMENT", "RESEARCH_NOT_READY", "REGISTERED_NOT_YET_MEASURABLE"]):
        return "RESEARCH_NOT_READY", "INFO", False, False, safe, "", "Research/experiment evidence is not ready"

    if status_upper.startswith("WARN_"):
        if legacy:
            return "LEGACY_WARN", "WARN", False, False, safe, "", "Legacy WARN_ status retained as historical evidence"
        return "REVIEW_NEEDED_NON_BLOCKING", "WARN", False, False, safe, "", "Current WARN_ status needs operator review"

    if status_upper.startswith("OK_") or status_upper == "OK":
        return "OK_READY", "OK", False, False, safe, "", "OK status with read-only safety contract intact"

    if status:
        note = f"Unrecognized STATUS={status}"
    else:
        note = "No STATUS key found"
    if legacy:
        return "LEGACY_UNKNOWN_REVIEW", "UNKNOWN", False, False, safe, "", note
    return "UNKNOWN_REVIEW", "UNKNOWN", False, False, safe, "", note


def detail_row(root: Path, path: Path) -> dict[str, Any]:
    scope = source_scope(root, path)
    legacy = is_legacy_scope(scope)
    alias = current_alias(scope, path)
    exists = path.exists()
    affects = scope == "CURRENT_CRITICAL"

    if not exists:
        if scope == "CURRENT_CRITICAL":
            normalized = "MISSING_CURRENT_CRITICAL_REVIEW"
            severity = "WARN"
            notes = "Current critical source missing; review whether this module was run today"
        elif scope == "CURRENT_SUPPORTING":
            normalized = "MISSING_SUPPORTING"
            severity = "WARN"
            notes = "Current supporting report missing"
        else:
            normalized = "MISSING_OPTIONAL"
            severity = "INFO"
            notes = "Legacy optional source missing"
        return {
            "source_name": path.name,
            "source_path": rel(root, path),
            "exists": "FALSE",
            "source_scope": scope,
            "affects_overall_status": "FALSE",
            "legacy_status": bool_text(legacy),
            "is_current_alias": bool_text(alias),
            "status_raw": "",
            "mode": "",
            "run_id": "",
            "generated_at": "",
            "normalized_status": normalized,
            "severity": severity,
            "is_blocking": "FALSE",
            "is_expected_pending": "FALSE",
            "safety_status": "NOT_EVALUATED_MISSING",
            "current_blocking_reason": "",
            "stale_age_hours": "",
            "notes": notes,
        }

    kv = parse_kv(path)
    normalized, severity, blocking, expected_pending, safe, reason, notes = classify_existing(path, kv, scope)
    affects = blocking and scope == "CURRENT_CRITICAL"
    return {
        "source_name": path.name,
        "source_path": rel(root, path),
        "exists": "TRUE",
        "source_scope": scope,
        "affects_overall_status": bool_text(affects),
        "legacy_status": bool_text(legacy),
        "is_current_alias": bool_text(alias),
        "status_raw": kv.get("STATUS", ""),
        "mode": kv.get("MODE", ""),
        "run_id": kv.get("RUN_ID", ""),
        "generated_at": kv.get("GENERATED_AT", ""),
        "normalized_status": normalized,
        "severity": severity,
        "is_blocking": bool_text(blocking and affects),
        "is_expected_pending": bool_text(expected_pending),
        "safety_status": safe,
        "current_blocking_reason": reason if affects else "",
        "stale_age_hours": age_hours(path) if normalized in {"REPORT_STALE_WARN", "LEGACY_REPORT_STALE_WARN"} else "",
        "notes": notes,
    }


def discover_sources(root: Path) -> list[Path]:
    ops = root / "outputs/v18/ops"
    read_center = root / "outputs/v18/read_center"
    seen: set[Path] = set()
    sources: list[Path] = []

    for rel_path in sorted(CURRENT_CRITICAL | CURRENT_SUPPORTING):
        p = root / rel_path
        sources.append(p)
        seen.add(p.resolve())

    if ops.exists():
        for p in sorted(ops.glob("*READ_FIRST.txt")):
            if p.resolve() not in seen:
                sources.append(p)
                seen.add(p.resolve())

    if read_center.exists():
        for p in sorted(read_center.glob("V18_CURRENT*.md")):
            if p.resolve() not in seen:
                sources.append(p)
                seen.add(p.resolve())
        current_txt = read_center / "V18_CURRENT_READ_FIRST.txt"
        if current_txt.exists() and current_txt.resolve() not in seen:
            sources.append(current_txt)
    return sources


def count_status(df: pd.DataFrame, status: str) -> int:
    return int((df["normalized_status"] == status).sum())


def build_summary(detail: pd.DataFrame) -> dict[str, Any]:
    current = detail[detail["source_scope"].isin(["CURRENT_CRITICAL", "CURRENT_SUPPORTING"])]
    current_blocking = detail[detail["affects_overall_status"] == "TRUE"]
    legacy = detail[detail["legacy_status"] == "TRUE"]
    current_non_blocking_warn = current[
        current["normalized_status"].isin(
            [
                "DATA_PROVIDER_WARN",
                "REPORT_STALE_WARN",
                "ACCOUNT_TEMPLATE_WARN",
                "REVIEW_NEEDED_NON_BLOCKING",
                "UNKNOWN_REVIEW",
                "MISSING_CURRENT_CRITICAL_REVIEW",
                "MISSING_SUPPORTING",
                "EXPECTED_PENDING_FORWARD_OUTCOME",
            ]
        )
    ]
    legacy_issue_count = int(
        legacy["normalized_status"].isin(
            ["LEGACY_FAIL", "LEGACY_WARN", "LEGACY_DATA_PROVIDER_WARN", "LEGACY_REPORT_STALE_WARN", "LEGACY_UNKNOWN_REVIEW"]
        ).sum()
    )
    current_fail_blocking = len(current_blocking)

    if current_fail_blocking > 0:
        overall = "FAIL_V18_38C_R1_COMMAND_STATUS_NORMALIZATION_BLOCKED"
        next_step = "Resolve current critical blocking safety/status issues, then rerun V18.38C-R1."
    elif len(current_non_blocking_warn) > 0 or legacy_issue_count > 0:
        overall = "WARN_V18_38C_R1_COMMAND_STATUS_NORMALIZATION_REVIEW_NEEDED"
        next_step = "Daily run is usable; review current warnings and keep legacy issues separated from today's blocking status."
    else:
        overall = "OK_V18_38C_R1_COMMAND_STATUS_NORMALIZATION_READY"
        next_step = "Command-center status is ready; wait for forward outcomes to mature where applicable."

    return {
        "total_sources_scanned": len(detail),
        "existing_sources": int((detail["exists"] == "TRUE").sum()),
        "missing_optional_sources": count_status(detail, "MISSING_OPTIONAL"),
        "missing_expected_sources": count_status(detail, "MISSING_CURRENT_CRITICAL_REVIEW"),
        "ok_ready_count": count_status(detail, "OK_READY"),
        "expected_pending_count": count_status(detail, "EXPECTED_PENDING_FORWARD_OUTCOME"),
        "account_template_warn_count": count_status(detail, "ACCOUNT_TEMPLATE_WARN"),
        "research_not_ready_count": count_status(detail, "RESEARCH_NOT_READY"),
        "review_needed_non_blocking_count": count_status(detail, "REVIEW_NEEDED_NON_BLOCKING"),
        "unknown_review_count": count_status(detail, "UNKNOWN_REVIEW") + count_status(detail, "LEGACY_UNKNOWN_REVIEW"),
        "current_critical_count": int((detail["source_scope"] == "CURRENT_CRITICAL").sum()),
        "current_supporting_count": int((detail["source_scope"] == "CURRENT_SUPPORTING").sum()),
        "historical_legacy_count": int((detail["source_scope"] == "HISTORICAL_LEGACY").sum()),
        "unknown_legacy_count": int((detail["source_scope"] == "UNKNOWN_LEGACY").sum()),
        "current_fail_blocking_count": current_fail_blocking,
        "legacy_fail_count": count_status(detail, "LEGACY_FAIL"),
        "current_data_provider_warn_count": count_status(detail, "DATA_PROVIDER_WARN"),
        "legacy_data_provider_warn_count": count_status(detail, "LEGACY_DATA_PROVIDER_WARN"),
        "current_report_stale_warn_count": count_status(detail, "REPORT_STALE_WARN"),
        "legacy_report_stale_warn_count": count_status(detail, "LEGACY_REPORT_STALE_WARN"),
        "legacy_warn_count": count_status(detail, "LEGACY_WARN"),
        "legacy_unknown_review_count": count_status(detail, "LEGACY_UNKNOWN_REVIEW"),
        "historical_issues_present": bool_text(legacy_issue_count > 0),
        "current_issues_present": bool_text(len(current_non_blocking_warn) > 0 or current_fail_blocking > 0),
        "overall_operator_status": overall,
        "daily_run_usable": bool_text(current_fail_blocking == 0),
        "forward_research_usable": bool_text(current_fail_blocking == 0),
        "trading_execution_allowed": "FALSE",
        "next_recommended_step": next_step,
    }


def bullets(df: pd.DataFrame, statuses: list[str], empty: str, limit: int = 20) -> str:
    rows = df[df["normalized_status"].isin(statuses)]
    if rows.empty:
        return f"- {empty}"
    lines = []
    for _, row in rows.head(limit).iterrows():
        reason = row["current_blocking_reason"] or row["notes"]
        lines.append(f"- {row['source_name']} [{row['source_scope']}]: {row['normalized_status']} - {reason}")
    if len(rows) > limit:
        lines.append(f"- 另有 {len(rows) - limit} 项未展开，详见 detail CSV。")
    return "\n".join(lines)


def build_report(summary: dict[str, Any], detail: pd.DataFrame, generated_at: str) -> str:
    current_detail = detail[detail["source_scope"].isin(["CURRENT_CRITICAL", "CURRENT_SUPPORTING"])]
    legacy_detail = detail[detail["legacy_status"] == "TRUE"]
    blocking = detail[detail["affects_overall_status"] == "TRUE"]
    return f"""# V18.38C-R1 命令中心状态归一化报告

生成时间: {generated_at}

## 1. 今日总判定
- 总状态: {summary['overall_operator_status']}
- 今日只读日报是否可用: {summary['daily_run_usable']}
- Forward research 是否可用: {summary['forward_research_usable']}
- 当前 blocking 数量: {summary['current_fail_blocking_count']}
- 历史 FAIL 数量: {summary['legacy_fail_count']}
- 历史问题是否存在: {summary['historical_issues_present']}

## 2. 当前关键源状态
- CURRENT_CRITICAL 数量: {summary['current_critical_count']}
- CURRENT_SUPPORTING 数量: {summary['current_supporting_count']}
{bullets(current_detail, ['FAIL_BLOCKING', 'MISSING_CURRENT_CRITICAL_REVIEW', 'MISSING_SUPPORTING', 'OK_READY'], '当前关键源没有可展示状态。')}

## 3. 历史旧问题与当前问题的区分
- HISTORICAL_LEGACY 数量: {summary['historical_legacy_count']}
- UNKNOWN_LEGACY 数量: {summary['unknown_legacy_count']}
- 这些旧问题会写入 detail 和 summary，但不会让 DAILY_RUN_USABLE 变成 FALSE。
{bullets(legacy_detail, ['LEGACY_FAIL', 'LEGACY_WARN', 'LEGACY_DATA_PROVIDER_WARN', 'LEGACY_REPORT_STALE_WARN', 'LEGACY_UNKNOWN_REVIEW'], '未发现历史旧问题。')}

## 4. 是否有真正阻断
{bullets(blocking, ['FAIL_BLOCKING'], '未发现当前真正阻断。')}

## 5. 可忽略/可等待的问题
{bullets(detail, ['EXPECTED_PENDING_FORWARD_OUTCOME', 'MISSING_OPTIONAL'], '当前没有 expected pending 或 legacy optional missing。')}

## 6. 需要之后处理的问题
{bullets(current_detail, ['DATA_PROVIDER_WARN', 'REPORT_STALE_WARN', 'ACCOUNT_TEMPLATE_WARN', 'REVIEW_NEEDED_NON_BLOCKING', 'UNKNOWN_REVIEW', 'MISSING_CURRENT_CRITICAL_REVIEW', 'MISSING_SUPPORTING'], '当前没有需要后续处理的 current warning。')}

## 7. Forward outcome 状态
{bullets(detail, ['EXPECTED_PENDING_FORWARD_OUTCOME'], '未发现 forward outcome 等待状态。')}

## 8. 数据源 warning 状态
- 当前数据源 warning: {summary['current_data_provider_warn_count']}
- 历史数据源 warning: {summary['legacy_data_provider_warn_count']}
{bullets(detail, ['DATA_PROVIDER_WARN', 'LEGACY_DATA_PROVIDER_WARN'], '未发现数据源 warning。')}

## 9. 账户 template warning 状态
{bullets(detail, ['ACCOUNT_TEMPLATE_WARN'], '未发现账户 template warning。')}

## 10. 安全确认
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE
- TRADING_EXECUTION_ALLOWED: FALSE

## 11. 下一步建议
{summary['next_recommended_step']}
"""


def build_read_first(summary: dict[str, Any], run_id: str, generated_at: str) -> str:
    fields = {
        "STATUS": summary["overall_operator_status"],
        "MODE": MODE,
        "RUN_ID": run_id,
        "GENERATED_AT": generated_at,
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "RANKING_MODIFIED": "FALSE",
        "FACTOR_WEIGHTS_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
        "ACCOUNT_STATE_MODIFIED": "FALSE",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "TOTAL_SOURCES_SCANNED": summary["total_sources_scanned"],
        "CURRENT_CRITICAL_COUNT": summary["current_critical_count"],
        "CURRENT_SUPPORTING_COUNT": summary["current_supporting_count"],
        "HISTORICAL_LEGACY_COUNT": summary["historical_legacy_count"],
        "UNKNOWN_LEGACY_COUNT": summary["unknown_legacy_count"],
        "CURRENT_FAIL_BLOCKING_COUNT": summary["current_fail_blocking_count"],
        "LEGACY_FAIL_COUNT": summary["legacy_fail_count"],
        "CURRENT_DATA_PROVIDER_WARN_COUNT": summary["current_data_provider_warn_count"],
        "LEGACY_DATA_PROVIDER_WARN_COUNT": summary["legacy_data_provider_warn_count"],
        "CURRENT_REPORT_STALE_WARN_COUNT": summary["current_report_stale_warn_count"],
        "LEGACY_REPORT_STALE_WARN_COUNT": summary["legacy_report_stale_warn_count"],
        "EXPECTED_PENDING_COUNT": summary["expected_pending_count"],
        "ACCOUNT_TEMPLATE_WARN_COUNT": summary["account_template_warn_count"],
        "RESEARCH_NOT_READY_COUNT": summary["research_not_ready_count"],
        "UNKNOWN_REVIEW_COUNT": summary["unknown_review_count"],
        "HISTORICAL_ISSUES_PRESENT": summary["historical_issues_present"],
        "CURRENT_ISSUES_PRESENT": summary["current_issues_present"],
        "OVERALL_OPERATOR_STATUS": summary["overall_operator_status"],
        "DAILY_RUN_USABLE": summary["daily_run_usable"],
        "FORWARD_RESEARCH_USABLE": summary["forward_research_usable"],
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "NEXT_RECOMMENDED_STEP": summary["next_recommended_step"],
    }
    return "\n".join(f"{key}: {value}" for key, value in fields.items()) + "\n"


def run(root: Path) -> int:
    ensure_dirs(root)
    run_id = f"V18_38C_R1_COMMAND_STATUS_NORMALIZATION_{now_ts()}"
    generated_at = now_iso()
    ops = root / "outputs/v18/ops"
    read_center = root / "outputs/v18/read_center"

    detail_path = ops / "V18_38C_R1_COMMAND_STATUS_DETAIL.csv"
    summary_path = ops / "V18_38C_R1_COMMAND_STATUS_SUMMARY.csv"
    rules_path = ops / "V18_38C_R1_COMMAND_STATUS_RULES.csv"
    report_path = read_center / "V18_38C_R1_COMMAND_STATUS_NORMALIZATION_REPORT.md"
    current_report_path = read_center / "V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md"
    read_first_path = ops / "V18_38C_R1_READ_FIRST.txt"
    legacy_read_first_path = ops / "V18_38C_READ_FIRST.txt"

    detail = pd.DataFrame([detail_row(root, path) for path in discover_sources(root)], columns=DETAIL_COLUMNS)
    rules = pd.DataFrame(RULE_ROWS)
    summary = build_summary(detail)
    summary_df = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    report = build_report(summary, detail, generated_at)
    read_first = build_read_first(summary, run_id, generated_at)

    write_csv(detail_path, detail, DETAIL_COLUMNS)
    write_csv(summary_path, summary_df, SUMMARY_COLUMNS)
    write_csv(rules_path, rules, ["rule_id", "rule_name", "match_pattern", "normalized_status", "severity", "description"])
    write_text(report_path, report)
    shutil.copyfile(report_path, current_report_path)
    write_text(read_first_path, read_first)
    write_text(legacy_read_first_path, read_first)

    return 1 if int(summary["current_fail_blocking_count"]) > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
