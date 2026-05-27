#!/usr/bin/env python
"""V18.44A daily operator homepage consolidation.

Read-only homepage builder that consolidates current daily operator outputs.
It parses existing READ_FIRST/current aliases only and writes a Chinese-friendly
operator homepage without changing rankings, gates, ledgers, or trading state.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.44A"
PATCH_FIX_VERSION = "V18.44B_REVIEW_FIXES"
PATCH_NAME = "DAILY_OPERATOR_HOMEPAGE_CONSOLIDATION"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

OUT_READ_FIRST = "outputs/v18/ops/V18_44A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_44A_DAILY_OPERATOR_HOMEPAGE_SUMMARY.csv"
OUT_FILE_CHECKLIST = "outputs/v18/ops/V18_44A_DAILY_OPERATOR_FILE_CHECKLIST.csv"
OUT_WARNING_CLASSIFICATION = "outputs/v18/ops/V18_44A_DAILY_OPERATOR_WARNING_CLASSIFICATION.csv"
OUT_HOMEPAGE = "outputs/v18/read_center/V18_44A_DAILY_OPERATOR_HOMEPAGE.md"

CUR_HOMEPAGE = "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_V2.md"
CUR_SUMMARY = "outputs/v18/ops/V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_SUMMARY.csv"
CUR_FILE_CHECKLIST = "outputs/v18/ops/V18_CURRENT_DAILY_OPERATOR_FILE_CHECKLIST.csv"
CUR_WARNING_CLASSIFICATION = "outputs/v18/ops/V18_CURRENT_DAILY_OPERATOR_WARNING_CLASSIFICATION.csv"
CUR_READ_FIRST = "outputs/v18/ops/V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_READ_FIRST.txt"

INPUTS = [
    ("v18_41a_read_first", "outputs/v18/ops/V18_41A_READ_FIRST.txt", "V18.41A pipeline READ_FIRST", "CORE"),
    ("daily_clean_status", "outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md", "current daily clean operator status", "CORE"),
    ("topn_read_first", "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt", "TopN explainer READ_FIRST", "IMPORTANT"),
    ("topn_packet", "outputs/v18/read_center/V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md", "TopN explainer packet", "IMPORTANT"),
    ("topn_summary", "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_SUMMARY.csv", "TopN summary csv", "IMPORTANT"),
    ("topn_close_gaps", "outputs/v18/ops/V18_CURRENT_TOPN_CLOSE_RANK_GAPS.csv", "TopN close rank gaps", "IMPORTANT"),
    ("topn_driver_matrix", "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_DRIVER_MATRIX.csv", "TopN driver matrix", "IMPORTANT"),
    ("single_read_first", "outputs/v18/ops/V18_42A_READ_FIRST.txt", "single ticker READ_FIRST", "IMPORTANT"),
    ("single_report", "outputs/v18/read_center/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md", "single ticker report", "IMPORTANT"),
    ("single_summary", "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER_SUMMARY.csv", "single ticker summary csv", "IMPORTANT"),
    ("single_attribution", "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_RANKING_ATTRIBUTION.csv", "single ticker attribution", "IMPORTANT"),
    ("single_neighbors", "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv", "single ticker neighbor comparison", "IMPORTANT"),
    ("old_chinese_homepage", "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md", "older Chinese homepage V18.33A", "OPTIONAL"),
    ("daily_brief", "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md", "current daily brief", "OPTIONAL"),
    ("portfolio_target_preview", "outputs/v18/read_center/V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md", "portfolio target preview", "OPTIONAL"),
    ("shadow_risk_model_preview", "outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md", "shadow risk model preview", "OPTIONAL"),
    ("operator_clean_status", "outputs/v18/read_center/V18_CURRENT_OPERATOR_CLEAN_STATUS.md", "operator clean status", "OPTIONAL"),
    ("fixable_warning_reducer", "outputs/v18/read_center/V18_CURRENT_FIXABLE_WARNING_REDUCER.md", "fixable warning reducer", "OPTIONAL"),
    ("residual_action_warning_resolver", "outputs/v18/read_center/V18_CURRENT_RESIDUAL_ACTION_WARNING_RESOLVER.md", "residual action warning resolver", "OPTIONAL"),
    ("alpha_signal_objects", "outputs/v18/read_center/V18_CURRENT_ALPHA_SIGNAL_OBJECTS.md", "alpha signal objects", "OPTIONAL"),
    ("candidate_top_full_sync", "outputs/v18/read_center/V18_CURRENT_CANDIDATE_TOP_FULL_CANONICAL_SYNC.md", "candidate top/full canonical sync", "OPTIONAL"),
]

SUMMARY_FIELDS = [
    "status", "patch_version", "patch_fix_version", "patch_name", "run_id", "generated_at",
    "write_current_requested", "current_alias_written", "current_read_first_written",
    "require_topn_current", "topn_current_required", "topn_current_ready", "topn_current_blocking_reason",
    "homepage_path", "current_homepage_path", "current_read_first_path",
    "daily_run_usable", "buy_candidate_report_usable", "trading_execution_allowed",
    "auto_trade", "auto_sell", "broker_api_used", "order_execution_used",
    "latest_signal_date", "latest_signal_freeze_count", "current_full_candidate_count",
    "current_top_candidate_count", "long_candidate_count", "top_full_mismatch_count",
    "blocking_current_failure_count", "expected_remaining_action_required_count",
    "topn_effective", "topn_close_gap_count", "topn_score_spread",
    "single_ticker", "single_ticker_found", "single_ticker_rank", "single_ticker_score",
    "warning_classification_row_count", "file_checklist_row_count",
    "missing_optional_count", "nonblocking_warning_count", "old_homepage_candidate_count_mismatch",
    "old_homepage_candidate_count", "old_homepage_candidate_count_source", "official_decision_impact", "ranking_logic_changed",
    "factor_weights_changed", "signal_freeze_ledger_modified", "trading_execution_allowed_guard",
]

CHECKLIST_FIELDS = [
    "file_key", "path", "exists", "role", "required_level", "parse_status",
    "row_count", "modified_time", "notes",
]

WARNING_FIELDS = [
    "warning_key", "source", "severity", "status_text", "operator_meaning_cn",
    "recommended_action_cn", "blocking_flag",
]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def clean(value: object) -> str:
    return str(value or "").strip()


def bool_text(value: object) -> str:
    text = clean(value).upper()
    return "TRUE" if text in {"TRUE", "YES", "1"} else "FALSE"


def is_true(value: object) -> bool:
    return bool_text(value) == "TRUE"


def int_value(value: object, default: int = 0) -> int:
    try:
        text = clean(value).replace(",", "")
        if not text:
            return default
        return int(float(text))
    except Exception:
        return default


def rel(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def read_text(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "", "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace"), "OK"
        except Exception:
            continue
    return "", "READ_ERROR"


def parse_read_first(path: Path) -> tuple[dict[str, str], str]:
    text, status = read_text(path)
    if status != "OK":
        return {}, status
    data: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper()
        if key:
            data[key] = value.strip()
    return data, "OK" if data else "UNPARSABLE"


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "READ_ERROR"


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def file_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def file_checklist(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key, rel_path, role, level in INPUTS:
        path = root / rel_path
        exists = path.exists()
        parse_status = "MISSING_OPTIONAL" if not exists and level == "OPTIONAL" else ("MISSING" if not exists else "OK")
        row_count: str | int = ""
        notes = ""
        if exists and path.suffix.lower() == ".csv":
            csv_rows, _, csv_status = read_csv_rows(path)
            parse_status = csv_status
            row_count = len(csv_rows) if csv_status == "OK" else ""
        elif exists and path.name.endswith("READ_FIRST.txt"):
            _, rf_status = parse_read_first(path)
            parse_status = rf_status
        rows.append({
            "file_key": key,
            "path": rel_path,
            "exists": "TRUE" if exists else "FALSE",
            "role": role,
            "required_level": level,
            "parse_status": parse_status,
            "row_count": row_count,
            "modified_time": file_mtime(path),
            "notes": notes,
        })
    return rows


def extract_old_candidate_count(root: Path, current_full_count: int) -> tuple[str, str, str]:
    path = root / "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
    text, status = read_text(path)
    if status != "OK" or current_full_count <= 0:
        return "", "UNKNOWN", status
    patterns = [
        ("OLD_HOMEPAGE_CANDIDATE_COUNT_FIELD", r"(?i)\bCANDIDATE[_\s-]*COUNT\b\s*[:：]?\s*`?(\d{1,6})"),
        ("OLD_HOMEPAGE_ENGLISH_CANDIDATE_COUNT_TEXT", r"(?i)\bcandidate\s+count\b\s*[:：]?\s*`?(\d{1,6})"),
        ("OLD_HOMEPAGE_CHINESE_CANDIDATE_COUNT_TEXT", r"候选(?:数|数量)\D{0,30}?`?(\d{1,6})"),
        ("OLD_HOMEPAGE_CHINESE_CANDIDATE_POOL_TEXT", r"候选池\D{0,30}?`?(\d{1,6})"),
        ("mojibake_candidate_count", r"鍊欓€夋(?:暟|暟閲|暟量)\D{0,30}?`?(\d{1,6})"),
        ("mojibake_candidate_pool", r"鍊欓€夋睜\D{0,30}?`?(\d{1,6})"),
    ]
    for source, pattern in patterns:
        for match in re.finditer(pattern, text):
            count = int_value(match.group(1), -1)
            if count > 0:
                mismatch = "TRUE" if count != current_full_count else "FALSE"
                return str(count), mismatch, source
    return "", "UNKNOWN", "NOT_FOUND"


def topn_current_status(
    topn: dict[str, str],
    checklist: list[dict[str, object]],
    require_topn_current: bool,
) -> tuple[str, str]:
    if not require_topn_current:
        return "NOT_REQUIRED", "NOT_REQUIRED"
    by_key = {clean(row.get("file_key")): row for row in checklist}
    read_first = by_key.get("topn_read_first", {})
    packet = by_key.get("topn_packet", {})
    if read_first.get("exists") != "TRUE":
        return "FALSE", "TOPN_READ_FIRST_MISSING"
    if read_first.get("parse_status") != "OK":
        return "FALSE", "TOPN_READ_FIRST_UNPARSABLE"
    if packet.get("exists") != "TRUE":
        return "FALSE", "TOPN_PACKET_MISSING"
    if topn.get("CURRENT_ALIAS_WRITTEN", "").upper() != "TRUE":
        return "FALSE", "TOPN_CURRENT_ALIAS_NOT_WRITTEN"
    if topn.get("CURRENT_READ_FIRST_WRITTEN", "").upper() != "TRUE":
        return "FALSE", "TOPN_CURRENT_READ_FIRST_NOT_WRITTEN"
    if int_value(topn.get("TOP_N_EFFECTIVE", topn.get("TOPN_EFFECTIVE")), 0) <= 0:
        return "FALSE", "TOP_N_EFFECTIVE_MISSING_OR_ZERO"
    return "TRUE", "NONE"


def add_warning(rows: list[dict[str, object]], key: str, source: str, severity: str, status: str, meaning: str, action: str) -> None:
    rows.append({
        "warning_key": key,
        "source": source,
        "severity": severity,
        "status_text": status,
        "operator_meaning_cn": meaning,
        "recommended_action_cn": action,
        "blocking_flag": "TRUE" if severity == "BLOCKING" else "FALSE",
    })


def classify_warnings(
    daily: dict[str, str],
    topn: dict[str, str],
    single: dict[str, str],
    checklist: list[dict[str, object]],
    root: Path,
    require_topn_current: bool,
    topn_ready: str,
    topn_blocking_reason: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    blocking_count = int_value(daily.get("BLOCKING_CURRENT_FAILURE_COUNT"))
    if blocking_count > 0:
        add_warning(rows, "BLOCKING_CURRENT_FAILURE_COUNT_GT_0", "V18_41A_READ_FIRST", "BLOCKING", str(blocking_count), "当前 daily pipeline 有阻塞失败。", "先处理 blocking failure，再阅读候选池。")
    if not is_true(daily.get("DAILY_RUN_USABLE")):
        add_warning(rows, "DAILY_RUN_USABLE_NOT_TRUE", "V18_41A_READ_FIRST", "BLOCKING", daily.get("DAILY_RUN_USABLE", ""), "今日 daily run 不可确认可用。", "检查 V18_41A_READ_FIRST 和 daily clean status。")
    if not is_true(daily.get("BUY_CANDIDATE_REPORT_USABLE")):
        add_warning(rows, "BUY_CANDIDATE_REPORT_USABLE_NOT_TRUE", "V18_41A_READ_FIRST", "BLOCKING", daily.get("BUY_CANDIDATE_REPORT_USABLE", ""), "买入候选报告不可确认可读。", "先修复候选报告生成链路。")
    for row in checklist:
        if row["required_level"] in {"CORE", "IMPORTANT"} and row["exists"] != "TRUE":
            is_required_topn = require_topn_current and row["file_key"] in {"topn_read_first", "topn_packet"}
            severity = "BLOCKING" if row["required_level"] == "CORE" or is_required_topn else "REVIEW"
            add_warning(rows, f"{row['file_key']}_MISSING", clean(row["file_key"]), severity, "MISSING", "关键或重要 current 文件缺失。", "如刚跑完 pipeline，检查对应可选步骤是否启用。")
    if require_topn_current and topn_ready == "FALSE":
        add_warning(rows, "TOPN_CURRENT_REQUIRED_NOT_READY", "TopN current requirement", "BLOCKING", topn_blocking_reason, "本次运行明确要求 TopN current 文件可用，但检查未通过。", "先重跑 V18.43A TopN explainer，带 -WriteCurrent。")
    elif topn and topn.get("CURRENT_ALIAS_WRITTEN", "").upper() != "TRUE":
        add_warning(rows, "TOPN_CURRENT_ALIAS_NOT_WRITTEN", "TopN READ_FIRST", "REVIEW", topn.get("CURRENT_ALIAS_WRITTEN", ""), "TopN current alias 未确认写入。", "重跑 V18.43A TopN explainer，带 -WriteCurrent。")
    for label, data, source in (
        ("V18_41A_STATUS", daily, "V18_41A_READ_FIRST"),
        ("TOPN_STATUS", topn, "TopN READ_FIRST"),
        ("SINGLE_STATUS", single, "V18_42A_READ_FIRST"),
    ):
        status = data.get("STATUS", "")
        if status.startswith("WARN_"):
            add_warning(rows, label, source, "REVIEW", status, "状态为 WARN，通常表示非阻塞但建议阅读。", "阅读对应报告的 warning/provenance 段落。")
        elif status.startswith("FAIL_"):
            add_warning(rows, label, source, "BLOCKING", status, "状态为 FAIL。", "先处理失败原因。")
    missing_optional = [r for r in checklist if r["required_level"] == "OPTIONAL" and r["exists"] != "TRUE"]
    for row in missing_optional:
        add_warning(rows, f"{row['file_key']}_MISSING_OPTIONAL", clean(row["file_key"]), "REVIEW", "MISSING_OPTIONAL", "可选 supporting 报告缺失，不应阻塞首页生成。", "需要细节时再补跑对应报告。")
    for key, rel_path, label in (
        ("DAILY_TRUST_LOW", "outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md", "DAILY_TRUST_LEVEL LOW"),
        ("HISTORICAL_YFINANCE_PREFLIGHT_FAILED", "outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md", "Historical yfinance preflight failed"),
        ("RISK_PREVIEW_REVIEW_NEEDED", "outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md", "V18.39C risk preview review needed"),
        ("FIXABLE_WARNINGS_ZERO_ACTION_REQUIRED", "outputs/v18/read_center/V18_CURRENT_FIXABLE_WARNING_REDUCER.md", "action-required zero"),
    ):
        text, status = read_text(root / rel_path)
        up = text.upper()
        if status == "OK" and (label.upper() in up or ("LOW" in up and "TRUST" in up and key == "DAILY_TRUST_LOW") or ("REVIEW" in up and "RISK" in up and key == "RISK_PREVIEW_REVIEW_NEEDED")):
            add_warning(rows, key, rel_path, "REVIEW", label, "发现非阻塞 review 信号。", "阅读对应 supporting 报告确认上下文。")
    for key, value in (
        ("AUTO_TRADE_DISABLED_EXPECTED", AUTO_TRADE),
        ("AUTO_SELL_DISABLED_EXPECTED", AUTO_SELL),
        ("TRADING_EXECUTION_ALLOWED_FALSE_EXPECTED", "FALSE"),
        ("OFFICIAL_DECISION_IMPACT_NONE_EXPECTED", OFFICIAL_DECISION_IMPACT),
    ):
        add_warning(rows, key, "V18.44A safety guard", "EXPECTED", value, "这是预期安全边界，不是故障。", "无需修复。")
    add_warning(rows, "FORWARD_EVIDENCE_PENDING_EXPECTED", "research-only daily process", "EXPECTED", "EXPECTED", "前向证据等待未来价格是研究流程中的预期状态。", "继续按 research-only 阅读。")
    add_warning(rows, "SHADOW_RESEARCH_ONLY_EXPECTED", "shadow/read-only reports", "EXPECTED", "EXPECTED", "shadow/research-only warning 不代表可交易。", "保持人工审阅。")
    return rows


def cn_bool(value: object) -> str:
    return "是" if is_true(value) else "否"


def status_level(status: str) -> str:
    if status.startswith("OK_"):
        return "OK"
    if status.startswith("FAIL_"):
        return "FAIL"
    return "WARN"


def build_homepage(
    summary: dict[str, object],
    daily: dict[str, str],
    topn: dict[str, str],
    single: dict[str, str],
    warning_rows: list[dict[str, object]],
    include_checklist: bool,
    include_warning_details: bool,
    checklist: list[dict[str, object]],
) -> str:
    status = clean(summary["status"])
    blocking = [r for r in warning_rows if r["severity"] == "BLOCKING"]
    review = [r for r in warning_rows if r["severity"] == "REVIEW"]
    expected = [r for r in warning_rows if r["severity"] == "EXPECTED"]
    one_line = "今天 pipeline 可用，没有 blocking failure；WARN 主要来自非阻塞的覆盖率、risk preview 或 supporting inputs partial。"
    if blocking:
        one_line = "今天存在 blocking failure，先不要把候选池当作可用操作输入。"
    elif status.startswith("OK_"):
        one_line = "今天 pipeline 可用，没有 blocking failure；可以先读 TopN 与单票解释。"
    mismatch_note = ""
    if summary.get("old_homepage_candidate_count_mismatch") == "TRUE":
        mismatch_note = "\n\n> 旧中文首页候选数与当前 pipeline 口径不一致，V18.44A 以 V18.41A 当前口径为准。"
    lines = [
        "# V18.44A 每日操作首页 / Daily Operator Homepage V2",
        "",
        "## 1. 今天先看结论",
        "",
        "| 项目 | 结论 |",
        "| --- | --- |",
        f"| 今日系统是否可用 | {cn_bool(summary.get('daily_run_usable'))} |",
        f"| 候选池是否可读 | {cn_bool(summary.get('buy_candidate_report_usable'))} |",
        f"| 是否有阻塞失败 | {'是' if blocking else '否'} |",
        "| 是否允许交易 | 否 |",
        f"| 自动交易 | {AUTO_TRADE} |",
        f"| 自动卖出 | {AUTO_SELL} |",
        f"| 当前状态 | {status_level(status)} |",
        f"| 一句话解释 | {one_line} |",
        "",
        "## 2. 今日核心数字",
        "",
        "| Machine field | Value |",
        "| --- | --- |",
    ]
    for field in (
        "LATEST_SIGNAL_DATE", "LATEST_SIGNAL_FREEZE_COUNT", "CURRENT_FULL_CANDIDATE_COUNT",
        "CURRENT_TOP_CANDIDATE_COUNT", "LONG_CANDIDATE_COUNT", "TOP_FULL_MISMATCH_COUNT",
        "BLOCKING_CURRENT_FAILURE_COUNT", "EXPECTED_REMAINING_ACTION_REQUIRED_COUNT",
        "DAILY_RUN_USABLE", "BUY_CANDIDATE_REPORT_USABLE", "TRADING_EXECUTION_ALLOWED",
    ):
        lines.append(f"| {field} | `{daily.get(field, summary.get(field.lower(), ''))}` |")
    if mismatch_note:
        lines.append(mismatch_note)
    lines += [
        "",
        "## 3. TopN 排名解释摘要",
        "",
        "| Machine field | Value |",
        "| --- | --- |",
    ]
    for field in ("STATUS", "TOP_N_EFFECTIVE", "TOP_SCORE", "BOTTOM_SCORE_WITHIN_TOPN", "TOPN_SCORE_SPREAD", "CLOSE_GAP_COUNT", "CURRENT_ALIAS_WRITTEN", "CURRENT_READ_FIRST_WRITTEN"):
        lines.append(f"| {field} | `{topn.get(field, '')}` |")
    lines += [
        "",
        "- Packet: `outputs/v18/read_center/V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`",
        "- Driver matrix: `outputs/v18/ops/V18_CURRENT_TOPN_RANKING_DRIVER_MATRIX.csv`",
        "- Close rank gaps: `outputs/v18/ops/V18_CURRENT_TOPN_CLOSE_RANK_GAPS.csv`",
        "",
        "## 4. 当前单票解释摘要",
        "",
        "| Machine field | Value |",
        "| --- | --- |",
    ]
    for field in ("STATUS", "TICKER", "TICKER_FOUND", "TARGET_RANK", "TARGET_SCORE_COLUMN", "TARGET_SCORE_VALUE", "CURRENT_ALIAS_WRITTEN"):
        lines.append(f"| {field} | `{single.get(field, '')}` |")
    lines += [
        "",
        "- Report: `outputs/v18/read_center/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md`",
        "- Attribution: `outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_RANKING_ATTRIBUTION.csv`",
        "- Neighbor comparison: `outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv`",
        "",
        "## 5. WARN 分类",
        "",
        "### A. Blocking / 阻塞",
    ]
    if blocking:
        for row in blocking:
            lines.append(f"- `{row['warning_key']}`: {row['operator_meaning_cn']} 建议: {row['recommended_action_cn']}")
    else:
        lines.append("- 当前未发现 blocking warning。")
    lines.append("")
    lines.append("### B. Nonblocking but review / 非阻塞但建议看")
    if review:
        for row in review[:20]:
            lines.append(f"- `{row['warning_key']}`: {row['operator_meaning_cn']} 状态: `{row['status_text']}`")
    else:
        lines.append("- 当前未发现需要 review 的非阻塞 warning。")
    lines.append("")
    lines.append("### C. Expected / 预期存在")
    for row in expected[:20]:
        lines.append(f"- `{row['warning_key']}`: {row['operator_meaning_cn']}")
    lines += [
        "",
        "## 6. 今天建议阅读顺序",
        "",
        "1. `outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_V2.md`",
        "2. `outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt`",
        "3. `outputs/v18/read_center/V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md`",
        "4. `outputs/v18/read_center/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md`",
        "5. `outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md`",
        "6. `outputs/v18/read_center/V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md`",
        "7. `outputs/v18/read_center/V18_CURRENT_OPERATOR_CLEAN_STATUS.md`",
        "",
        "## 7. 下一步操作建议",
        "",
    ]
    if not blocking:
        lines.append("- 今天不需要修复阻塞问题，可以直接阅读 TopN 与单票解释。")
    if int_value(summary.get("topn_close_gap_count")) >= 10:
        lines.append("- 排名接近区较多，建议重点看 close rank gaps。")
    if is_true(summary.get("single_ticker_found")):
        lines.append(f"- 当前单票解释对象是 `{summary.get('single_ticker')}`，可继续换 ticker 做 drilldown。")
    if len(review) >= len(blocking):
        lines.append("- WARN 主要是非阻塞 review，不影响候选池阅读。")
    lines += [
        "",
        "## 8. Safety / 安全边界",
        "",
        "- 本首页不重新计算排名。",
        "- 本首页不修改候选池。",
        "- 本首页不修改 signal freeze ledger。",
        "- 本首页不改变交易决策。",
        "- 本首页不允许自动交易。",
        "- AUTO_TRADE remains DISABLED.",
        "- AUTO_SELL remains DISABLED.",
    ]
    if include_warning_details:
        lines += ["", "## 附录 A. Warning 明细", "", "| warning_key | severity | source | status_text |", "| --- | --- | --- | --- |"]
        for row in warning_rows:
            lines.append(f"| `{row['warning_key']}` | `{row['severity']}` | `{row['source']}` | `{row['status_text']}` |")
    if include_checklist:
        lines += ["", "## 附录 B. 文件检查清单", "", "| file_key | exists | required_level | parse_status |", "| --- | --- | --- | --- |"]
        for row in checklist:
            lines.append(f"| `{row['file_key']}` | `{row['exists']}` | `{row['required_level']}` | `{row['parse_status']}` |")
    return "\n".join(lines) + "\n"


def build_read_first(summary: dict[str, object]) -> str:
    order = [
        "status", "patch_version", "patch_fix_version", "patch_name", "write_current_requested", "current_alias_written",
        "current_read_first_written", "require_topn_current", "topn_current_required", "topn_current_ready",
        "topn_current_blocking_reason", "homepage_path", "current_homepage_path", "current_read_first_path",
        "daily_run_usable", "buy_candidate_report_usable", "trading_execution_allowed", "auto_trade",
        "auto_sell", "broker_api_used", "order_execution_used", "latest_signal_date",
        "latest_signal_freeze_count", "current_full_candidate_count", "current_top_candidate_count",
        "long_candidate_count", "top_full_mismatch_count", "blocking_current_failure_count",
        "expected_remaining_action_required_count", "topn_effective", "topn_close_gap_count",
        "topn_score_spread", "single_ticker", "single_ticker_found", "single_ticker_rank",
        "single_ticker_score", "warning_classification_row_count", "file_checklist_row_count",
        "old_homepage_candidate_count", "old_homepage_candidate_count_mismatch", "old_homepage_candidate_count_source",
        "official_decision_impact", "ranking_logic_changed", "factor_weights_changed",
        "signal_freeze_ledger_modified", "trading_execution_allowed_guard",
    ]
    aliases = {
        "status": "STATUS",
        "patch_version": "PATCH_VERSION",
        "patch_fix_version": "PATCH_FIX_VERSION",
        "patch_name": "PATCH_NAME",
        "trading_execution_allowed_guard": "TRADING_EXECUTION_ALLOWED",
    }
    lines = []
    for key in order:
        label = aliases.get(key, key.upper())
        lines.append(f"{label}: {summary.get(key, '')}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--include-file-checklist", action="store_true")
    parser.add_argument("--include-warning-details", action="store_true")
    parser.add_argument("--require-topn-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"{PATCH_NAME}_{now_ts()}"
    generated_at = now_iso()
    daily, daily_status = parse_read_first(root / "outputs/v18/ops/V18_41A_READ_FIRST.txt")
    if args.strict and daily_status != "OK":
        summary = {
            "status": "FAIL_V18_44A_CORE_STATUS_MISSING",
            "patch_version": PATCH_VERSION,
            "patch_fix_version": PATCH_FIX_VERSION,
            "patch_name": PATCH_NAME,
            "run_id": run_id,
            "generated_at": generated_at,
            "write_current_requested": "TRUE" if args.write_current else "FALSE",
            "current_alias_written": "FALSE",
            "current_read_first_written": "FALSE",
            "require_topn_current": "TRUE" if args.require_topn_current else "FALSE",
            "topn_current_required": "TRUE" if args.require_topn_current else "FALSE",
            "topn_current_ready": "FALSE" if args.require_topn_current else "NOT_REQUIRED",
            "topn_current_blocking_reason": "CORE_STATUS_MISSING",
            "homepage_path": OUT_HOMEPAGE,
            "current_homepage_path": "",
            "current_read_first_path": "",
            "daily_run_usable": "FALSE",
            "buy_candidate_report_usable": "FALSE",
            "trading_execution_allowed": "FALSE",
            "auto_trade": AUTO_TRADE,
            "auto_sell": AUTO_SELL,
            "broker_api_used": "FALSE",
            "order_execution_used": "FALSE",
            "latest_signal_date": "",
            "latest_signal_freeze_count": "",
            "current_full_candidate_count": "",
            "current_top_candidate_count": "",
            "long_candidate_count": "",
            "top_full_mismatch_count": "",
            "blocking_current_failure_count": "",
            "expected_remaining_action_required_count": "",
            "topn_effective": "",
            "topn_close_gap_count": "",
            "topn_score_spread": "",
            "single_ticker": "",
            "single_ticker_found": "FALSE",
            "single_ticker_rank": "",
            "single_ticker_score": "",
            "warning_classification_row_count": "0",
            "file_checklist_row_count": "0",
            "old_homepage_candidate_count": "",
            "old_homepage_candidate_count_mismatch": "UNKNOWN",
            "old_homepage_candidate_count_source": "",
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "ranking_logic_changed": "FALSE",
            "factor_weights_changed": "FALSE",
            "signal_freeze_ledger_modified": "FALSE",
            "trading_execution_allowed_guard": "FALSE",
        }
        try:
            write_text(root / OUT_READ_FIRST, build_read_first(summary))
            write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
        except Exception:
            pass
        return 2

    topn, _ = parse_read_first(root / "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt")
    single, _ = parse_read_first(root / "outputs/v18/ops/V18_42A_READ_FIRST.txt")
    checklist = file_checklist(root)
    topn_ready, topn_blocking_reason = topn_current_status(topn, checklist, args.require_topn_current)
    warning_rows = classify_warnings(daily, topn, single, checklist, root, args.require_topn_current, topn_ready, topn_blocking_reason)
    missing_optional_count = sum(1 for r in checklist if r["required_level"] == "OPTIONAL" and r["exists"] != "TRUE")
    blocking_warning_count = sum(1 for r in warning_rows if r["severity"] == "BLOCKING")
    review_warning_count = sum(1 for r in warning_rows if r["severity"] == "REVIEW")
    current_full_count = int_value(daily.get("CURRENT_FULL_CANDIDATE_COUNT"))
    old_count, old_mismatch, old_count_source = extract_old_candidate_count(root, current_full_count)
    has_low_trust = any("TRUST" in clean(r["warning_key"]) and r["severity"] == "REVIEW" for r in warning_rows)
    if daily_status != "OK" and args.strict:
        status = "FAIL_V18_44A_CORE_STATUS_MISSING"
    elif blocking_warning_count == 0 and daily_status == "OK" and not review_warning_count and not missing_optional_count and not has_low_trust:
        status = "OK_V18_44A_DAILY_OPERATOR_HOMEPAGE_READY"
    elif daily_status == "MISSING" and args.strict:
        status = "FAIL_V18_44A_CORE_STATUS_MISSING"
    else:
        status = "WARN_V18_44A_DAILY_OPERATOR_HOMEPAGE_REVIEW_NEEDED"

    summary: dict[str, object] = {
        "status": status,
        "patch_version": PATCH_VERSION,
        "patch_fix_version": PATCH_FIX_VERSION,
        "patch_name": PATCH_NAME,
        "run_id": run_id,
        "generated_at": generated_at,
        "write_current_requested": "TRUE" if args.write_current else "FALSE",
        "current_alias_written": "FALSE",
        "current_read_first_written": "FALSE",
        "require_topn_current": "TRUE" if args.require_topn_current else "FALSE",
        "topn_current_required": "TRUE" if args.require_topn_current else "FALSE",
        "topn_current_ready": topn_ready,
        "topn_current_blocking_reason": topn_blocking_reason,
        "homepage_path": OUT_HOMEPAGE,
        "current_homepage_path": CUR_HOMEPAGE if args.write_current else "",
        "current_read_first_path": CUR_READ_FIRST if args.write_current else "",
        "daily_run_usable": bool_text(daily.get("DAILY_RUN_USABLE")),
        "buy_candidate_report_usable": bool_text(daily.get("BUY_CANDIDATE_REPORT_USABLE")),
        "trading_execution_allowed": "FALSE",
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "broker_api_used": bool_text(daily.get("BROKER_API_USED")),
        "order_execution_used": bool_text(daily.get("ORDER_EXECUTION_USED")),
        "latest_signal_date": daily.get("LATEST_SIGNAL_DATE", ""),
        "latest_signal_freeze_count": daily.get("LATEST_SIGNAL_FREEZE_COUNT", ""),
        "current_full_candidate_count": daily.get("CURRENT_FULL_CANDIDATE_COUNT", ""),
        "current_top_candidate_count": daily.get("CURRENT_TOP_CANDIDATE_COUNT", ""),
        "long_candidate_count": daily.get("LONG_CANDIDATE_COUNT", ""),
        "top_full_mismatch_count": daily.get("TOP_FULL_MISMATCH_COUNT", ""),
        "blocking_current_failure_count": daily.get("BLOCKING_CURRENT_FAILURE_COUNT", ""),
        "expected_remaining_action_required_count": daily.get("EXPECTED_REMAINING_ACTION_REQUIRED_COUNT", ""),
        "topn_effective": topn.get("TOP_N_EFFECTIVE", topn.get("TOPN_EFFECTIVE", "")),
        "topn_close_gap_count": topn.get("CLOSE_GAP_COUNT", ""),
        "topn_score_spread": topn.get("TOPN_SCORE_SPREAD", ""),
        "single_ticker": single.get("TICKER", ""),
        "single_ticker_found": bool_text(single.get("TICKER_FOUND")),
        "single_ticker_rank": single.get("TARGET_RANK", ""),
        "single_ticker_score": single.get("TARGET_SCORE_VALUE", ""),
        "warning_classification_row_count": str(len(warning_rows)),
        "file_checklist_row_count": str(len(checklist)),
        "missing_optional_count": str(missing_optional_count),
        "nonblocking_warning_count": str(review_warning_count),
        "old_homepage_candidate_count_mismatch": old_mismatch,
        "old_homepage_candidate_count": old_count,
        "old_homepage_candidate_count_source": old_count_source,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "ranking_logic_changed": "FALSE",
        "factor_weights_changed": "FALSE",
        "signal_freeze_ledger_modified": "FALSE",
        "trading_execution_allowed_guard": "FALSE",
    }

    homepage = build_homepage(summary, daily, topn, single, warning_rows, args.include_file_checklist, args.include_warning_details, checklist)
    read_first = build_read_first(summary)
    try:
        write_text(root / OUT_HOMEPAGE, homepage)
        write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
        write_csv(root / OUT_FILE_CHECKLIST, checklist, CHECKLIST_FIELDS)
        write_csv(root / OUT_WARNING_CLASSIFICATION, warning_rows, WARNING_FIELDS)
        write_text(root / OUT_READ_FIRST, read_first)
        if args.write_current:
            shutil.copyfile(root / OUT_HOMEPAGE, root / CUR_HOMEPAGE)
            shutil.copyfile(root / OUT_SUMMARY, root / CUR_SUMMARY)
            shutil.copyfile(root / OUT_FILE_CHECKLIST, root / CUR_FILE_CHECKLIST)
            shutil.copyfile(root / OUT_WARNING_CLASSIFICATION, root / CUR_WARNING_CLASSIFICATION)
            summary["current_alias_written"] = "TRUE"
            summary["current_read_first_written"] = "TRUE"
            read_first = build_read_first(summary)
            write_text(root / OUT_READ_FIRST, read_first)
            write_text(root / CUR_READ_FIRST, read_first)
            write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
            shutil.copyfile(root / OUT_SUMMARY, root / CUR_SUMMARY)
    except Exception as exc:
        fail_summary = dict(summary)
        fail_summary["status"] = "FAIL_V18_44A_HOMEPAGE_WRITE_FAILED"
        fail_summary["current_alias_written"] = "FALSE"
        fail_summary["current_read_first_written"] = "FALSE"
        try:
            write_text(root / OUT_READ_FIRST, build_read_first(fail_summary))
        except Exception:
            pass
        print(f"WRITE_FAILED: {exc}", file=sys.stderr)
        return 3
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
