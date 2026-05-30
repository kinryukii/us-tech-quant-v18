from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.50C-R1"
PATCH_NAME = "COMMAND_CENTER_ACTION_PACKET_SEQUENCE_FIX"
SOURCE_GATE_REQUIRED_PATCH_VERSION = "V18.50B-R2"

READ50B = "outputs/v18/ops/V18_50B_R2_READ_FIRST.txt"
CURRENT_TOP20 = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
STATUS35D = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_COMPUTATION_STATUS.csv"
FAILURES35D = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_RECOMPUTE_FAILURES.csv"
UNIVERSE_META = "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv"
RECOMMENDATION_META = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
ACTION_PACKET = "outputs/v18/action_plan/V18_50A_DAILY_OPERATOR_ACTION_PACKET.csv"
ACTION_SUMMARY = "outputs/v18/action_plan/V18_50A_DAILY_OPERATOR_ACTION_SUMMARY.csv"
ACTION_READ_FIRST = "outputs/v18/ops/V18_50A_READ_FIRST.txt"

OUT_READ_FIRST = "outputs/v18/ops/V18_50C_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_50C_DAILY_OPERATOR_READABILITY_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_50C_DAILY_OPERATOR_HOMEPAGE_CN.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_HOMEPAGE_CN.md"
OUT_BRIEF = "outputs/v18/read_center/V18_50C_DAILY_OPERATOR_HOMEPAGE_BRIEF_CN.md"

OPTIONAL_REPORTS = [
    ("event_risk_summary", "outputs/v18/event_risk/V18_47C_R2_TOP20_90D_RISK_EVENT_SUMMARY.csv"),
    ("event_risk_diagnostics", "outputs/v18/event_risk/V18_47C_R2_TOP20_90D_RISK_EVENT_DIAGNOSTICS.csv"),
    ("options_risk_summary", "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_SUMMARY.csv"),
    ("options_risk_detail", "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_RADAR_DETAIL.csv"),
    ("priority_summary", "outputs/v18/tracking/V18_47B_TOP20_PRIORITY_SUMMARY.csv"),
    ("priority_snapshot", "outputs/v18/tracking/V18_47B_TOP20_PRIORITY_SNAPSHOT.csv"),
    ("v18_49a_read_first", "outputs/v18/ops/V18_49A_READ_FIRST.txt"),
    ("v18_49b_read_first", "outputs/v18/ops/V18_49B_READ_FIRST.txt"),
    ("v18_49c_read_first", "outputs/v18/ops/V18_49C_READ_FIRST.txt"),
    ("v18_49d_read_first", "outputs/v18/ops/V18_49D_READ_FIRST.txt"),
    ("v18_50a_read_first", "outputs/v18/ops/V18_50A_READ_FIRST.txt"),
    ("v18_50a_action_summary", ACTION_SUMMARY),
]

SAFETY_FIELDS = {
    "OFFICIAL_RANKING_CHANGED": "FALSE",
    "FACTOR_WEIGHTS_CHANGED": "FALSE",
    "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
    "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
    "TRADING_EXECUTION_ALLOWED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BROKER_API_USED": "FALSE",
    "ORDER_EXECUTION_USED": "FALSE",
}

READ_FIRST_ORDER = [
    "STATUS",
    "PATCH_VERSION",
    "PATCH_NAME",
    "SOURCE_GATE_REQUIRED_PATCH_VERSION",
    "SOURCE_GATE_STATUS",
    "SOURCE_GATE_OK",
    "SOLE_WRITER_AUDIT_OK",
    "CURRENT_TOP20_SOURCE_OK",
    "CURRENT_TOP20_ROW_COUNT",
    "CURRENT_TOP20_LATEST_PRICE_DATE_MIN",
    "CURRENT_TOP20_LATEST_PRICE_DATE_MAX",
    "TOP20_REPORT_WRITTEN",
    "CURRENT_HOMEPAGE_CN_WRITTEN",
    "ACTION_PACKET_FOUND",
    "ACTION_PACKET_ROW_COUNT",
    "ACTION_PACKET_REVALIDATED_BEFORE_REPORT",
    "COMMAND_CENTER_SEQUENCE_OK",
    "ACTION_PACKET_REVALIDATION_SOURCE",
    "REQUIRED_SEQUENCE",
    "PAPER_BUY_COUNT",
    "PAPER_WATCH_COUNT",
    "PAPER_SKIP_POLICY_LIMIT_COUNT",
    "REAL_POSITION_DATA_MISSING_COUNT",
    "OPTIONAL_RISK_REPORTS_FOUND_COUNT",
    "OPTIONAL_RISK_REPORTS_MISSING_COUNT",
    "DAILY_OPERATOR_REPORT_USABLE",
    "OFFICIAL_RANKING_CHANGED",
    "FACTOR_WEIGHTS_CHANGED",
    "OFFICIAL_BUY_PERMISSION_CHANGED",
    "OFFICIAL_SELL_PERMISSION_CHANGED",
    "TRADING_EXECUTION_ALLOWED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "BROKER_API_USED",
    "ORDER_EXECUTION_USED",
]


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def clean(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip().upper()] = value.strip()
    return out


def to_int(value: object) -> int:
    try:
        text = clean(value).replace(",", "")
        return int(float(text)) if text else 0
    except Exception:
        return 0


def to_float_text(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        return f"{float(text):.4f}"
    except Exception:
        return text


def sort_by_rank(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(row: dict[str, str]) -> tuple[int, str]:
        rank = to_int(row.get("rank")) or 10**9
        return rank, clean(row.get("ticker")).upper()

    return sorted(rows, key=key)


def index_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = clean(row.get("ticker")).upper()
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def company_names(root: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    for rel in (UNIVERSE_META, RECOMMENDATION_META):
        rows, _ = read_csv(root / rel)
        for row in rows:
            ticker = clean(row.get("ticker")).upper()
            name = clean(row.get("company_name") or row.get("company") or row.get("security_name"))
            if ticker and name and ticker not in names:
                names[ticker] = name
    return names


def source_gate_ok(read50b: dict[str, str]) -> bool:
    required = {
        "PATCH_VERSION": SOURCE_GATE_REQUIRED_PATCH_VERSION,
        "STATUS": "PASS",
        "SOLE_WRITER_AUDIT_OK": "TRUE",
        "CURRENT_TOP20_WRITE_ALLOWED": "TRUE",
        "V18_35D_TOP20_MATCH_CURRENT_TOP20": "TRUE",
        "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK": "TRUE",
        "HOMEPAGE_SOURCE_OK": "TRUE",
    }
    return all(read50b.get(key) == value for key, value in required.items())


def action_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    sim = [clean(row.get("simulation_action")).upper() for row in rows]
    real = [clean(row.get("real_position_action")).upper() for row in rows]
    return {
        "PAPER_BUY_COUNT": sum(1 for x in sim if x.startswith("PAPER_BUY")),
        "PAPER_WATCH_COUNT": sum(1 for x in sim if x.startswith("PAPER_WATCH")),
        "PAPER_SKIP_POLICY_LIMIT_COUNT": sum(1 for x in sim if x == "PAPER_SKIP_POLICY_LIMIT"),
        "REAL_POSITION_DATA_MISSING_COUNT": sum(1 for x in real if x == "REAL_POSITION_DATA_MISSING"),
    }


def optional_status(root: Path) -> tuple[list[dict[str, str]], int, int]:
    rows: list[dict[str, str]] = []
    found = 0
    missing = 0
    for name, rel in OPTIONAL_REPORTS:
        path = root / rel
        exists = path.exists()
        found += 1 if exists else 0
        missing += 0 if exists else 1
        row_count = 0
        if exists and path.suffix.lower() == ".csv":
            parsed, _ = read_csv(path)
            row_count = len(parsed)
        rows.append({
            "name": name,
            "path": rel,
            "exists": bool_text(exists),
            "row_count": str(row_count),
            "status": "FOUND" if exists else "WARN_OPTIONAL_REPORT_MISSING",
        })
    return rows, found, missing


def summary_map(rows: list[dict[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        key = clean(row.get("summary_key") or row.get("metric") or row.get("name"))
        value = clean(row.get("summary_value") or row.get("value"))
        if key:
            out[key] = value
    return out


def markdown_table(rows: list[dict[str, object]], fields: Sequence[str]) -> list[str]:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        vals = [clean(row.get(field)).replace("|", "/") for field in fields]
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def build_top20_rows(
    top20: list[dict[str, str]],
    status_by_ticker: dict[str, dict[str, str]],
    action_by_ticker: dict[str, dict[str, str]],
    names: dict[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in sort_by_rank(top20)[:20]:
        ticker = clean(row.get("ticker")).upper()
        status = status_by_ticker.get(ticker, {})
        action = action_by_ticker.get(ticker, {})
        rows.append({
            "rank": clean(row.get("rank")),
            "ticker": ticker,
            "company_name": names.get(ticker, ""),
            "composite_candidate_score": to_float_text(row.get("composite_candidate_score")),
            "factor_score": to_float_text(status.get("factor_score")),
            "technical_score": to_float_text(status.get("technical_timing_score")),
            "latest_price_date": clean(row.get("latest_price_date")),
            "authoritative_row_ok": clean(row.get("authoritative_row_ok")),
            "simulation_action": clean(action.get("simulation_action")),
            "real_position_action": clean(action.get("real_position_action")),
            "explanation_cn": "权威重算Top20；仅供复核，不代表自动买入。" if clean(row.get("authoritative_row_ok")) == "TRUE" else "来源未通过权威行检查。",
        })
    return rows


def render_report(
    values: dict[str, str],
    read50b: dict[str, str],
    top20_rows: list[dict[str, object]],
    action_rows: list[dict[str, str]],
    action_summary: dict[str, str],
    optional_rows: list[dict[str, str]],
    failures: list[dict[str, str]],
    warnings: list[str],
    root: Path,
) -> str:
    event_summary, _ = read_csv(root / "outputs/v18/event_risk/V18_47C_R2_TOP20_90D_RISK_EVENT_SUMMARY.csv")
    options_summary, _ = read_csv(root / "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_SUMMARY.csv")
    priority_summary, _ = read_csv(root / "outputs/v18/tracking/V18_47B_TOP20_PRIORITY_SUMMARY.csv")
    event_map = summary_map(event_summary)
    priority_map = summary_map(priority_summary)
    options_row = options_summary[0] if options_summary else {}

    lines: list[str] = [
        "# V18.50C 每日操作员中文首页",
        "",
        f"- 生成时间: `{now_iso()}`",
        f"- 报告状态: `{values['STATUS']}`",
        f"- Source gate: `{values['SOURCE_GATE_STATUS']}` / OK=`{values['SOURCE_GATE_OK']}`",
        f"- Required sequence: `{values['REQUIRED_SEQUENCE']}`",
        f"- Action packet revalidated before report: `{values['ACTION_PACKET_REVALIDATED_BEFORE_REPORT']}`",
        "",
        "## 1. 每日 source-chain 状态",
        "",
        "| 项目 | 值 |",
        "| --- | --- |",
        f"| V18.50B-R2 PATCH_VERSION | `{read50b.get('PATCH_VERSION', '')}` |",
        f"| source-chain status | `{read50b.get('STATUS', '')}` |",
        f"| sole-writer audit | `{read50b.get('SOLE_WRITER_AUDIT_OK', '')}` |",
        f"| active legacy writer count | `{read50b.get('ACTIVE_LEGACY_WRITER_COUNT', '')}` |",
        f"| current Top20 write allowed | `{read50b.get('CURRENT_TOP20_WRITE_ALLOWED', '')}` |",
        f"| current Top20 blocked reason | `{read50b.get('CURRENT_TOP20_WRITE_BLOCKED_REASON', '')}` |",
        f"| reconciliation | `{read50b.get('RECONCILIATION_FORMULA', '')}` / `{read50b.get('RECONCILIATION_OK', '')}` |",
        f"| freshness | full=`{read50b.get('FULL_UNIVERSE_PRICE_REFRESH_COMPLETE', '')}`, top20=`{read50b.get('TOP20_PRICE_REFRESH_COMPLETE', '')}` |",
        f"| safety | ranking=`{values['OFFICIAL_RANKING_CHANGED']}`, weights=`{values['FACTOR_WEIGHTS_CHANGED']}`, trading=`{values['TRADING_EXECUTION_ALLOWED']}` |",
        "",
        "## 2. 今日可用性结论",
        "",
        "| 判断 | 值 |",
        "| --- | --- |",
        f"| 今日系统可读 | `{values['DAILY_OPERATOR_REPORT_USABLE']}` |",
        f"| 今日数据可信 | `{values['SOURCE_GATE_OK']}` |",
        f"| 今日 Top20 可用 | `{values['CURRENT_TOP20_SOURCE_OK']}` |",
        f"| 今日模拟动作可参考 | `{bool_text(values['ACTION_PACKET_FOUND'] == 'TRUE' and values['SOURCE_GATE_OK'] == 'TRUE')}` |",
        f"| 今日真实持仓动作可参考 | `{bool_text(action_summary.get('real_position_book_found') == 'TRUE')}` |",
        f"| 今日是否允许交易执行 | `{values['TRADING_EXECUTION_ALLOWED']}` |",
        "",
        "## 3. 当前 Top20",
        "",
    ]
    lines.extend(markdown_table(top20_rows, [
        "rank", "ticker", "company_name", "composite_candidate_score", "factor_score",
        "technical_score", "latest_price_date", "authoritative_row_ok", "explanation_cn",
    ]))
    lines.extend([
        "",
        "## 4. V18.50A action packet 摘要",
        "",
        f"- action packet found: `{values['ACTION_PACKET_FOUND']}`",
        f"- action packet revalidated before report: `{values['ACTION_PACKET_REVALIDATED_BEFORE_REPORT']}`",
        f"- revalidation source: `{values['ACTION_PACKET_REVALIDATION_SOURCE']}`",
        f"- action packet rows: `{values['ACTION_PACKET_ROW_COUNT']}`",
        f"- PAPER_BUY: `{values['PAPER_BUY_COUNT']}`",
        f"- PAPER_WATCH: `{values['PAPER_WATCH_COUNT']}`",
        f"- PAPER_SKIP_POLICY_LIMIT: `{values['PAPER_SKIP_POLICY_LIMIT_COUNT']}`",
        f"- REAL_POSITION_DATA_MISSING: `{values['REAL_POSITION_DATA_MISSING_COUNT']}`",
    ])
    top20_action_count = sum(1 for row in top20_rows if clean(row.get("simulation_action")))
    top20_skip_count = sum(1 for row in top20_rows if clean(row.get("simulation_action")).upper() == "PAPER_SKIP_POLICY_LIMIT")
    if top20_action_count and top20_action_count == top20_skip_count:
        lines += [
            "",
            "> 当前模拟买入策略尚未放开，本报告只显示 source-safe Top20，不代表今日有买入信号。",
        ]
    lines += ["", "### Top20 动作明细", ""]
    lines.extend(markdown_table(top20_rows, ["rank", "ticker", "simulation_action", "real_position_action"]))
    lines += [
        "",
        "## 5. 风险与阻塞摘要",
        "",
        "| 来源 | 摘要 |",
        "| --- | --- |",
        f"| Event risk | TOP20_TOTAL=`{event_map.get('TOP20_TOTAL_COUNT', '')}`, EARNINGS_FOUND=`{event_map.get('EARNINGS_DATE_FOUND_COUNT', '')}`, UNKNOWN=`{event_map.get('UNKNOWN_EVENT_DATA_COUNT', '')}` |",
        f"| Options risk | ticker_count=`{options_row.get('ticker_count', '')}`, medium=`{options_row.get('medium_risk_count', '')}`, high=`{options_row.get('high_risk_count', '')}`, avg_score=`{options_row.get('average_options_risk_score', '')}` |",
        f"| Priority tracker | SNAPSHOT_ROWS=`{priority_map.get('SNAPSHOT_ROW_COUNT', '')}`, TRACKER_ROWS=`{priority_map.get('TRACKER_ROW_COUNT', '')}` |",
        f"| V18.49A/B/C/D | 49A=`{action_summary.get('v18_49a_status', '')}`, 49B=`{action_summary.get('v18_49b_status', '')}`, 49C=`{action_summary.get('v18_49c_status', '')}`, 49D=`{action_summary.get('v18_49d_status', '')}` |",
        f"| V18.50A | status=`{action_summary.get('status', '')}`, simulation_decision=`{action_summary.get('simulation_decision', '')}`, source_policy_confidence=`{action_summary.get('source_policy_confidence', '')}` |",
        "",
        "### 可选风险报告文件",
        "",
    ]
    lines.extend(markdown_table(optional_rows, ["name", "exists", "row_count", "status"]))
    lines += [
        "",
        "## 6. 今日需要注意的问题",
        "",
    ]
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- 暂无额外警告。")
    if failures:
        unavailable = [clean(row.get("ticker")).upper() for row in failures if clean(row.get("failure_bucket")).upper() == "UNAVAILABLE_PRICE_DATA_EXCLUDED"]
        insufficient = [clean(row.get("ticker")).upper() for row in failures if clean(row.get("failure_bucket")).upper() == "PRICE_HISTORY_INSUFFICIENT"]
        if unavailable:
            lines.append(f"- 不可用/疑似退市 ticker: `{', '.join(unavailable)}`")
        if insufficient:
            lines.append(f"- 价格历史不足 ticker: `{', '.join(insufficient)}`")
    lines += [
        "",
        "## 7. 操作员下一步",
        "",
        "- 先确认 V18.50B-R2 source gate PASS。",
        "- 看 Top20 表，确认价格日期和权威来源。",
        "- 看 action packet，确认 simulation_action 与 real_position_action。",
        "- 看 event/options risk 和 priority tracker。",
        "- 若 simulation_action 全部为 PAPER_SKIP_POLICY_LIMIT，说明买入策略尚未恢复，不要当作买入建议。",
        "- 不做真实交易。",
        "- 下一阶段才做模拟买入策略矩阵。",
        "",
        "## 安全声明",
        "",
        "V18.50C 只做可读性和 source audit 汇总；不改排名、不改权重、不改买卖策略、不写 Top20 current alias、不启用交易。",
    ]
    return "\n".join(lines) + "\n"


def run(root: Path) -> int:
    read50b = read_kv(root / READ50B)
    read50a = read_kv(root / ACTION_READ_FIRST)
    source_ok = source_gate_ok(read50b)
    top20, _ = read_csv(root / CURRENT_TOP20)
    action_packet, _ = read_csv(root / ACTION_PACKET)
    action_summary_rows, _ = read_csv(root / ACTION_SUMMARY)
    action_summary = action_summary_rows[0] if action_summary_rows else {}
    status_rows, _ = read_csv(root / STATUS35D)
    failures, _ = read_csv(root / FAILURES35D)
    optional_rows, optional_found, optional_missing = optional_status(root)
    names = company_names(root)

    top20_sorted = sort_by_rank(top20)[:20]
    top20_dates = [clean(row.get("latest_price_date")) for row in top20_sorted if clean(row.get("latest_price_date"))]
    action_by_ticker = index_by_ticker(action_packet)
    status_by_ticker = index_by_ticker(status_rows)
    top20_report_rows = build_top20_rows(top20_sorted, status_by_ticker, action_by_ticker, names)
    counts = action_counts(action_packet)
    action_packet_revalidated = (
        bool(action_packet)
        and read50a.get("STATUS") == "PASS"
        and read50a.get("PATCH_VERSION") == "V18.50A"
        and read50a.get("DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK") == "TRUE"
        and read50a.get("DAILY_OPERATOR_ACTION_ENTRY_SOURCE_BLOCKED_REASON") == "NONE"
    )

    current_top20_source_ok = (
        source_ok
        and len(top20_sorted) == 20
        and all(clean(row.get("authoritative_row_ok")).upper() == "TRUE" for row in top20_sorted)
        and all(clean(row.get("current_top20_written_by_module")) == SOURCE_GATE_REQUIRED_PATCH_VERSION for row in top20_sorted)
    )

    warnings: list[str] = []
    if not source_ok:
        warnings.append("source-chain 未通过 V18.50B-R2 锁定 gate，本报告不可作为 source-safe 日报。")
    if not action_packet_revalidated:
        warnings.append("V18.50A action packet 未确认在报告前完成 source-safe revalidation。")
    if optional_missing:
        warnings.append(f"可选风险报告缺失 {optional_missing} 个，标记为 WARN_OPTIONAL_REPORT_MISSING。")
    if counts["PAPER_BUY_COUNT"] == 0:
        warnings.append("今日没有 PAPER_BUY 候选。")
    if counts["REAL_POSITION_DATA_MISSING_COUNT"]:
        warnings.append("真实持仓数据缺失，真实持仓动作不可参考。")
    if to_int(read50b.get("FULL_UNIVERSE_STALE_ROW_COUNT")) or to_int(read50b.get("TOP20_STALE_ROW_COUNT")):
        warnings.append("存在 stale price row，请先复核 freshness audit。")

    report_written = "FALSE"
    current_written = "FALSE"
    values = {
        "STATUS": "PASS" if source_ok and current_top20_source_ok and action_packet_revalidated else "WARN_V18_50C_SOURCE_GATE_NOT_READY",
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "SOURCE_GATE_REQUIRED_PATCH_VERSION": SOURCE_GATE_REQUIRED_PATCH_VERSION,
        "SOURCE_GATE_STATUS": read50b.get("STATUS", "MISSING"),
        "SOURCE_GATE_OK": bool_text(source_ok),
        "SOLE_WRITER_AUDIT_OK": read50b.get("SOLE_WRITER_AUDIT_OK", "FALSE"),
        "CURRENT_TOP20_SOURCE_OK": bool_text(current_top20_source_ok),
        "CURRENT_TOP20_ROW_COUNT": str(len(top20_sorted)),
        "CURRENT_TOP20_LATEST_PRICE_DATE_MIN": min(top20_dates) if top20_dates else "",
        "CURRENT_TOP20_LATEST_PRICE_DATE_MAX": max(top20_dates) if top20_dates else "",
        "TOP20_REPORT_WRITTEN": report_written,
        "CURRENT_HOMEPAGE_CN_WRITTEN": current_written,
        "ACTION_PACKET_FOUND": bool_text(bool(action_packet)),
        "ACTION_PACKET_ROW_COUNT": str(len(action_packet)),
        "ACTION_PACKET_REVALIDATED_BEFORE_REPORT": bool_text(action_packet_revalidated),
        "COMMAND_CENTER_SEQUENCE_OK": bool_text(source_ok and action_packet_revalidated),
        "ACTION_PACKET_REVALIDATION_SOURCE": ACTION_READ_FIRST,
        "REQUIRED_SEQUENCE": "V18.50B-R2 -> V18.50A -> V18.50C",
        "PAPER_BUY_COUNT": str(counts["PAPER_BUY_COUNT"]),
        "PAPER_WATCH_COUNT": str(counts["PAPER_WATCH_COUNT"]),
        "PAPER_SKIP_POLICY_LIMIT_COUNT": str(counts["PAPER_SKIP_POLICY_LIMIT_COUNT"]),
        "REAL_POSITION_DATA_MISSING_COUNT": str(counts["REAL_POSITION_DATA_MISSING_COUNT"]),
        "OPTIONAL_RISK_REPORTS_FOUND_COUNT": str(optional_found),
        "OPTIONAL_RISK_REPORTS_MISSING_COUNT": str(optional_missing),
        "DAILY_OPERATOR_REPORT_USABLE": bool_text(source_ok and current_top20_source_ok and action_packet_revalidated),
        **SAFETY_FIELDS,
    }

    report = render_report(values, read50b, top20_report_rows, action_packet, action_summary, optional_rows, failures, warnings, root)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)
    brief = "\n".join([
        "# V18.50C 今日简报",
        "",
        f"- STATUS: `{values['STATUS']}`",
        f"- SOURCE_GATE_OK: `{values['SOURCE_GATE_OK']}`",
        f"- CURRENT_TOP20_ROW_COUNT: `{values['CURRENT_TOP20_ROW_COUNT']}`",
        f"- PAPER_BUY_COUNT: `{values['PAPER_BUY_COUNT']}`",
        f"- TRADING_EXECUTION_ALLOWED: `{values['TRADING_EXECUTION_ALLOWED']}`",
        "",
    ])
    write_text(root / OUT_BRIEF, brief)
    values["TOP20_REPORT_WRITTEN"] = "TRUE"
    values["CURRENT_HOMEPAGE_CN_WRITTEN"] = "TRUE"
    values["DAILY_OPERATOR_REPORT_USABLE"] = bool_text(source_ok and current_top20_source_ok and action_packet_revalidated)

    write_csv(root / OUT_SUMMARY, [values], READ_FIRST_ORDER)
    write_text(root / OUT_READ_FIRST, "\n".join(f"{key}: {values.get(key, '')}" for key in READ_FIRST_ORDER) + "\n")

    print(f"STATUS: {values['STATUS']}")
    print(f"SOURCE_GATE_OK: {values['SOURCE_GATE_OK']}")
    print(f"CURRENT_TOP20_SOURCE_OK: {values['CURRENT_TOP20_SOURCE_OK']}")
    print(f"TOP20_REPORT_WRITTEN: {values['TOP20_REPORT_WRITTEN']}")
    print(f"CURRENT_HOMEPAGE_CN_WRITTEN: {values['CURRENT_HOMEPAGE_CN_WRITTEN']}")
    print(f"DAILY_OPERATOR_REPORT_USABLE: {values['DAILY_OPERATOR_REPORT_USABLE']}")
    return 0 if values["STATUS"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.50C daily operator readability and source audit lock.")
    parser.add_argument("--root", "--project-root", dest="root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
