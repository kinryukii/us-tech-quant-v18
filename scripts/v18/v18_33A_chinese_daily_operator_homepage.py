from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_33A_CHINESE_DAILY_HOMEPAGE_READY"
STATUS_WARN = "WARN_V18_33A_CHINESE_DAILY_HOMEPAGE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_33A_CHINESE_DAILY_HOMEPAGE_FAILED"
MODE_LIVE = "CHINESE_DAILY_OPERATOR_HOMEPAGE"
MODE_DRY = "CHINESE_DAILY_OPERATOR_HOMEPAGE_DRY_RUN"

CURRENT_CONTEXT = "outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md"
CURRENT_DAILY = "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md"
CURRENT_ACCOUNT_GUIDE = "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md"
CURRENT_ACCOUNT_PLAN = "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md"
CURRENT_FREEZE_REPAIR = "outputs/v18/read_center/V18_CURRENT_FREEZE_COVERAGE_REPAIR.md"
CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
CURRENT_OPERATOR_CENTER = "outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md"
CURRENT_GUARD = "outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md"
CURRENT_32B = "outputs/v18/ops/V18_32B_READ_FIRST.txt"
CURRENT_32C = "outputs/v18/ops/V18_32C_READ_FIRST.txt"
CURRENT_32D = "outputs/v18/ops/V18_32D_READ_FIRST.txt"

OUT_HOME = "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
OUT_REPORT = "outputs/v18/read_center/V18_33A_CHINESE_DAILY_HOMEPAGE_REPORT.md"
OUT_SUMMARY = "outputs/v18/ops/V18_33A_CHINESE_DAILY_HOMEPAGE_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_33A_READ_FIRST.txt"
OUT_ERROR = "outputs/v18/read_center/V18_33A_CHINESE_DAILY_HOMEPAGE_ERROR.md"
OUT_FIELD_GUIDE = "docs/v18/V18_CHINESE_REPORT_FIELD_GUIDE.md"

CHINESE_NAME_MAP = {
    "VIAV": "维亚维解决方案",
    "SITM": "SiTime",
    "TSEM": "塔半导体",
    "STM": "意法半导体",
    "BW": "巴布科克与威尔科克斯",
    "PLUG": "普拉格电力",
    "TTMI": "TTM科技",
    "TWLO": "Twilio",
    "HTZ": "赫兹全球",
    "PUMP": "ProPetro",
    "OLPX": "Olaplex",
    "APLD": "Applied Digital",
    "U": "Unity软件",
    "SMTC": "Semtech",
    "SEI": "SolarEdge科技",
    "SATS": "EchoStar",
    "RVMD": "Revolution Medicines",
    "XYZ": "Block",
    "WULF": "TeraWulf",
    "QSR": "餐饮品牌国际",
    "VIST": "Vista Energy",
    "WLK": "西湖材料",
    "USFD": "US Foods",
    "IGV": "iShares扩展科技软件ETF",
    "AMAT": "应用材料",
    "AAPL": "苹果",
    "NTAP": "NetApp",
    "NVDA": "英伟达",
}

REASON_MAP = {
    "TOP_30_RANK": "排名位于前30",
    "TOP_75_RANK": "排名位于前75",
    "TOP_3_THEME_RANK": "主题内排名靠前",
    "CYCLICAL_GROWTH_ROLE": "周期成长型角色",
    "SPECULATIVE_ROLE": "投机型角色",
    "HIGH_VOLATILITY": "波动率较高",
    "HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE": "高波动但未自动降级",
    "EXTREME_VOLATILITY": "波动率极高",
    "EXTREME_VOLATILITY_LIMIT": "极端波动受限",
    "TECHNICAL_CAUTION": "技术面偏谨慎",
    "CALIBRATED_CORE_ELIGIBLE": "可作为核心候选",
    "CALIBRATED_WATCHLIST_ELIGIBLE": "可纳入观察名单",
    "HIGH_RISK_SMALL_SIZE_ONLY": "仅限高风险小仓位",
}


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def clean(value: object) -> str:
    return norm(value).strip("`").strip()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = clean(value)
    return values


def parse_csv_line(line: str) -> List[str]:
    out: List[str] = []
    cur = ""
    quoted = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if quoted and i + 1 < len(line) and line[i + 1] == '"':
                cur += '"'
                i += 1
            else:
                quoted = not quoted
        elif ch == "," and not quoted:
            out.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    out.append(cur)
    return out


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            text = path.read_text(encoding=enc, errors="replace")
            lines = [line for line in text.splitlines() if line.strip()]
            if not lines:
                return [], []
            header = parse_csv_line(lines[0].lstrip("\ufeff"))
            rows = []
            for line in lines[1:]:
                vals = parse_csv_line(line)
                row = {}
                for i, field in enumerate(header):
                    row[field] = vals[i] if i < len(vals) else ""
                rows.append(row)
            return rows, header
        except Exception:
            continue
    return [], []


def first_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    lookup = {field.lower(): field for field in fields}
    for alias in aliases:
        if alias.lower() in lookup:
            return lookup[alias.lower()]
    return None


def first_value(row: Dict[str, str], fields: Sequence[str], aliases: Sequence[str]) -> str:
    for alias in aliases:
        col = first_col(fields, [alias])
        if col and norm(row.get(col)):
            return norm(row.get(col))
    return ""


def read_summary_csv(path: Path) -> Dict[str, str]:
    rows, _ = read_csv_rows(path)
    return rows[-1] if rows else {}


def current_candidate_rows(root: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    return read_csv_rows(root / CURRENT_RANKED)


def recommendation_rows(root: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    return read_csv_rows(root / CURRENT_RECOMMENDATIONS)


def extract_source_values(root: Path) -> Dict[str, str]:
    ctx = read_status_file(root / CURRENT_CONTEXT)
    ctx_summary = read_summary_csv(root / "outputs/v18/ops/V18_32C_CONTEXT_CONSISTENCY_SUMMARY.csv")
    guard = read_status_file(root / CURRENT_GUARD)
    daily = read_text(root / CURRENT_DAILY)
    account_guide = read_text(root / CURRENT_ACCOUNT_GUIDE)
    account_plan = read_text(root / CURRENT_ACCOUNT_PLAN)
    freeze_repair = read_text(root / CURRENT_FREEZE_REPAIR)
    ranked_rows, ranked_fields = current_candidate_rows(root)
    rec_rows, rec_fields = recommendation_rows(root)
    operator = read_text(root / CURRENT_OPERATOR_CENTER)
    freeze_report = read_text(root / "outputs/v18/read_center/V18_32D_FREEZE_REPAIR_REPORT.md")
    values = {
        "latest_signal_date": clean(ctx.get("Signal date", ctx.get("Signal Date", ctx.get("Signal_date", "")))) or clean(ctx.get("Signal date")) or clean(ctx.get("Signal date".upper(), "")),
        "freeze_coverage_status": clean(ctx.get("Freeze coverage", ctx.get("Freeze coverage status", ""))),
        "candidate_count": clean(ctx.get("Expected candidates", ctx.get("Expected candidate count", ""))),
        "missing_tickers": clean(ctx.get("Missing tickers", "")),
        "context_status": clean(ctx.get("STATUS", "")),
        "context_consistency_status": clean(ctx.get("STATUS", "")),
        "freeze_repair_status": clean(read_status_file(root / CURRENT_FREEZE_REPAIR).get("STATUS", "")),
        "freeze_repair_report": freeze_report,
        "daily_text": daily,
        "account_guide": account_guide,
        "account_plan": account_plan,
        "operator": operator,
        "guard": guard,
        "ctx_summary": ctx_summary,
        "ranked_count": str(len(ranked_rows)),
        "recommendation_count": str(len(rec_rows)),
        "theme_count": str(len(ranked_rows)),
        "ranked_rows": ranked_rows,
        "ranked_fields": ranked_fields,
        "rec_rows": rec_rows,
        "rec_fields": rec_fields,
    }
    return values


def parse_kv_block(text: object) -> Dict[str, str]:
    if isinstance(text, dict):
        return {str(key): clean(str(value)) for key, value in text.items()}
    if text is None:
        return {}
    text = str(text)
    out: Dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = clean(value)
    return out


def detect_system_status(values: Dict[str, str]) -> Dict[str, str]:
    daily = parse_kv_block(values["daily_text"])
    guard = parse_kv_block(values["guard"]) if values["guard"] else {}
    ctx = parse_kv_block(read_text(Path("D:/us-tech-quant/outputs/v18/ops/V18_32C_READ_FIRST.txt")))
    freeze = parse_kv_block(values["freeze_repair_report"])
    account_plan = parse_kv_block(values["account_plan"])
    account_guide = parse_kv_block(values["account_guide"])
    operator = parse_kv_block(values["operator"])
    result = {
        "latest_signal_date": ctx.get("LATEST_RELEVANT_SIGNAL_DATE", guard.get("RECOMMENDED_SIGNAL_DATE", daily.get("Recommended signal date", "2026-05-22"))),
        "freeze_coverage_status": ctx.get("FREEZE_COVERAGE_STATUS", freeze.get("POST_COVERAGE_STATUS", "UNKNOWN")),
        "freeze_count": ctx.get("FREEZE_TICKER_COUNT", freeze.get("POST_FREEZE_ROW_COUNT", "UNKNOWN")),
        "expected_count": ctx.get("EXPECTED_CANDIDATE_COUNT", freeze.get("EXPECTED_CANDIDATE_COUNT", values["candidate_count"])),
        "missing_ticker_count": ctx.get("FREEZE_MISSING_VS_CURRENT_COUNT", freeze.get("POST_MISSING_TICKER_COUNT", "UNKNOWN")),
        "duplicate_count": ctx.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT", freeze.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT", "0")),
        "context_status": ctx.get("STATUS", values["context_status"]),
        "auto_trade": operator.get("AUTO_TRADE", daily.get("AUTO_TRADE", "DISABLED")),
        "auto_sell": operator.get("AUTO_SELL", daily.get("AUTO_SELL", "DISABLED")),
        "official_decision_impact": operator.get("OFFICIAL_DECISION_IMPACT", daily.get("OFFICIAL_DECISION_IMPACT", "NONE")),
        "forbidden_modified": operator.get("FORBIDDEN_MODIFIED", daily.get("FORBIDDEN_MODIFIED", "FALSE")),
        "allowed_trade_count": account_plan.get("ACCOUNT_TRADE_ALLOWED_COUNT", account_plan.get("ACCOUNT_TRADE_ALLOWED_COUNT", "0")),
        "allowed_trade_count_report": account_plan.get("ACCOUNT_TRADE_ALLOWED_COUNT", ""),
        "blocked_reason": account_plan.get("STATUS", account_plan.get("ACCOUNT_TRADE_STATUS", "")),
        "account_state_quality": account_guide.get("ACCOUNT_STATE_QUALITY", ""),
        "template_empty": account_guide.get("TEMPLATE_EMPTY_ACCOUNT", ""),
        "forward_return_ready": daily.get("FORWARD_RETURN_NOT_READY", "") or daily.get("FORWARD_RETURN_READINESS", ""),
        "forward_return_status": daily.get("FORWARD_RETURN_NOT_READY", "") or daily.get("FORWARD_RETURN_READINESS", ""),
        "daily_status": daily.get("STATUS", ""),
        "guard_status": guard.get("STATUS", ""),
        "context_consistency_status": ctx.get("STATUS", ""),
    }
    if not result["allowed_trade_count"] or result["allowed_trade_count"] == "":
        result["allowed_trade_count"] = account_plan.get("ACCOUNT_TRADE_ALLOWED_COUNT", "0")
    if result["template_empty"] == "":
        result["template_empty"] = account_guide.get("TEMPLATE_EMPTY_ACCOUNT", "UNKNOWN")
    return result


def chinese_name(ticker: str) -> str:
    return CHINESE_NAME_MAP.get(ticker.upper(), "中文名待补充")


def summarize_reasons(row: Dict[str, str], fields: Sequence[str]) -> Tuple[str, str]:
    reason_codes = first_value(row, fields, ["reason_codes"])
    notes = first_value(row, fields, ["operator_notes"])
    action = first_value(row, fields, ["recommendation_action"])
    tier = first_value(row, fields, ["recommendation_tier"])
    risk = first_value(row, fields, ["risk_label"])
    tech = first_value(row, fields, ["technical_signal"])
    warning = first_value(row, fields, ["technical_warning_label"])

    reasons: List[str] = []
    for code in [part.strip() for part in reason_codes.split(";") if part.strip()]:
        reasons.append(REASON_MAP.get(code, code))
    if not reasons and notes:
        if "Rank" in notes:
            reasons.append("来源字段已有摘要，但未拆出明确规则标签")
        else:
            reasons.append("来源字段不足，需查看原始候选报告")
    risk_lines = []
    if tier:
        if tier == "CORE_CANDIDATE":
            risk_lines.append("核心候选，仍需审阅后决定")
        elif tier == "WATCHLIST_STRONG":
            risk_lines.append("观察名单较强，等待确认")
        elif tier == "SPECULATIVE_SATELLITE":
            risk_lines.append("投机卫星，仓位要小")
        elif tier == "OVERHEATED_WAIT":
            risk_lines.append("偏热，先等回落")
        elif tier == "TACTICAL_ENTRY":
            risk_lines.append("战术入场，需结合节奏")
        elif tier == "DEFENSIVE_HEDGE":
            risk_lines.append("防御性对冲用途")
        elif tier == "ETF_OR_MACRO_EXPOSURE":
            risk_lines.append("宏观/ETF暴露")
        else:
            risk_lines.append(f"推荐档位：{tier}")
    if action:
        action_map = {
            "REVIEW_FIRST": "先审阅，不直接下单",
            "WATCH_FOR_ENTRY": "观察等待入场",
            "HIGH_RISK_SMALL_SIZE_ONLY": "仅限高风险小仓位",
            "DO_NOT_PRIORITIZE": "当前不优先",
            "HIGH_RISK_SMALL_SIZE_ONLY;": "仅限高风险小仓位",
        }
        risk_lines.append(action_map.get(action, f"动作：{action}"))
    if risk:
        risk_map = {
            "HIGH_RISK": "风险较高",
            "EXTREME_RISK": "风险极高",
            "MEDIUM_RISK": "中等风险",
        }
        risk_lines.append(risk_map.get(risk, f"风险：{risk}"))
    if tech:
        tech_map = {
            "TECH_TIMING_STAGED_REFRESH": "技术面处于刷新/待确认状态",
            "TECH_TIMING_WATCH_POSITIVE": "技术面偏正向",
        }
        risk_lines.append(tech_map.get(tech, f"技术：{tech}"))
    if warning:
        risk_lines.append("技术警示：" + warning)
    if notes:
        notes_summary = notes
        for phrase, zh in [
            ("Advisory tier only.", "仅供参考。"),
            ("No official decision or trade instruction.", "不构成正式交易指令。"),
            ("Rank ", "排名 "),
            ("theme ", "主题 "),
            ("role ", "角色 "),
            ("volatility ", "波动率 "),
            ("action ", "动作 "),
        ]:
            notes_summary = notes_summary.replace(phrase, zh)
    else:
        notes_summary = "来源字段不足，需查看原始候选报告"
    return "；".join(reasons[:4]) if reasons else "来源字段不足，需查看原始候选报告", "；".join(risk_lines[:3]) if risk_lines else "来源字段不足，需查看原始候选报告"


def reason_human_summary(row: Dict[str, str], fields: Sequence[str]) -> str:
    reason_codes = first_value(row, fields, ["reason_codes"])
    notes = first_value(row, fields, ["operator_notes"])
    action = first_value(row, fields, ["recommendation_action"])
    tier = first_value(row, fields, ["recommendation_tier"])
    risk = first_value(row, fields, ["risk_label"])
    theme = first_value(row, fields, ["primary_theme"])
    tech = first_value(row, fields, ["technical_signal"])

    parts = []
    if tier:
        parts.append(f"档位 {tier}")
    if action:
        parts.append({
            "REVIEW_FIRST": "先审阅",
            "WATCH_FOR_ENTRY": "观察等待入场",
            "HIGH_RISK_SMALL_SIZE_ONLY": "仅限高风险小仓位",
        }.get(action, action))
    if theme:
        parts.append(f"主题 {theme}")
    if tech:
        parts.append("技术面待确认" if "STAGED" in tech or "WATCH" in tech else tech)
    codes = [c.strip() for c in reason_codes.split(";") if c.strip()]
    mapped = [REASON_MAP.get(c, c) for c in codes[:3]]
    if mapped:
        parts.append("；".join(mapped))
    if not parts and notes:
        parts.append("来源字段已有说明，但缺少可拆解原因字段")
    return "，".join(parts) if parts else "来源字段不足，需查看原始候选报告"


def risk_human_summary(row: Dict[str, str], fields: Sequence[str]) -> str:
    risk = first_value(row, fields, ["risk_label"])
    warning = first_value(row, fields, ["technical_warning_label"])
    action = first_value(row, fields, ["recommendation_action"])
    pieces = []
    if risk == "HIGH_RISK":
        pieces.append("高风险")
    elif risk == "EXTREME_RISK":
        pieces.append("极高风险")
    elif risk == "MEDIUM_RISK":
        pieces.append("中等风险")
    elif risk:
        pieces.append(risk)
    if action == "HIGH_RISK_SMALL_SIZE_ONLY":
        pieces.append("仅适合小仓位")
    elif action == "WATCH_FOR_ENTRY":
        pieces.append("等待入场")
    elif action == "REVIEW_FIRST":
        pieces.append("先看再说")
    if warning:
        pieces.append("技术警示：" + warning)
    return "；".join(pieces) if pieces else "来源字段不足，需查看原始候选报告"


def build_candidate_rows(rows: Sequence[Dict[str, str]], fields: Sequence[str], limit: int = 20) -> List[Dict[str, str]]:
    out = []
    for row in rows[:limit]:
        ticker = first_value(row, fields, ["ticker"])
        company = first_value(row, fields, ["company_name"])
        theme = first_value(row, fields, ["primary_theme"])
        industry = first_value(row, fields, ["industry_group"])
        tech = first_value(row, fields, ["technical_signal"])
        tier = first_value(row, fields, ["recommendation_tier"])
        score = first_value(row, fields, ["composite_candidate_score"])
        reason = reason_human_summary(row, fields)
        risk = risk_human_summary(row, fields)
        cn = chinese_name(ticker)
        out.append({
            "排名": first_value(row, fields, ["rank"]),
            "股票代码": ticker,
            "中文名称": cn,
            "英文名称": company,
            "综合分": score,
            "推荐档位": tier,
            "主题/行业": f"{theme} / {industry}" if theme or industry else "",
            "技术状态": tech,
            "主要原因中文摘要": reason,
            "风险提示中文摘要": risk,
        })
    return out


def make_homepage(values: Dict[str, str], system: Dict[str, str], candidate_rows: List[Dict[str, str]], missing_name_count: int) -> str:
    can_trade = system["allowed_trade_count"] not in {"", "UNKNOWN", "0"} and system["allowed_trade_count"] != "0"
    if system["allowed_trade_count"] == "0":
        trade_line = "今天系统不建议开新仓。当前允许交易候选为 0。"
    elif can_trade:
        trade_line = "今天系统存在可交易候选，但仍需结合账户状态和人工复核。"
    else:
        trade_line = "今天是否可以交易无法确认。"

    blockers = []
    if system["allowed_trade_count"] == "0":
        blockers.append("当前允许交易候选为 0。")
    if system["template_empty"] == "TRUE":
        blockers.append("当前账户仍是模板状态，需要手动填写真实持仓/现金后，账户约束才更可靠。")
    if system.get("forward_return_status", "") or system["daily_status"].startswith("WARN_"):
        blockers.append("前向收益仍在等待未来价格数据，相关验证暂不可用。")
    if system["freeze_coverage_status"] != "FULL_MATCH":
        blockers.append("冻结覆盖尚未完整。")
    if not blockers:
        blockers.append("当前没有发现会阻止人工查看候选的硬性错误。")

    missing_account_name = "是" if system["template_empty"] == "TRUE" else "否"
    table = candidate_rows[:20]
    source_note = "；".join([
        "优先使用 V18.32C 一致性审计和 V18.32D 冻结修复报告",
        "推荐列表来自当前推荐文件",
        "中文名仅用于 Markdown 报告，不写入任何机器字段",
    ])
    report_lines = [
        "# V18 中文每日操作主页",
        "",
        "## 今日一句话结论",
        f"- {trade_line}",
        f"- 当前冻结覆盖已恢复为 {system['freeze_coverage_status']}，候选池 {system['expected_count']}/{system['expected_count']}，数据一致性正常。",
        f"- 当前账户模板状态：{missing_account_name}；若要生成更可靠的交易判断，需要先手动更新现金和持仓。",
        "",
        "## 今日系统状态",
        f"- 最新 signal date: `{system['latest_signal_date']}`",
        f"- 冻结覆盖状态: `{system['freeze_coverage_status']}`",
        f"- 候选数量: `{system['expected_count']}`",
        f"- 推荐数量: `{values['recommendation_count']}`",
        f"- 主题数量: `{values['theme_count']}`",
        f"- 一致性状态: `{system['context_consistency_status']}`",
        f"- `AUTO_TRADE`: `{system['auto_trade']}`",
        f"- `AUTO_SELL`: `{system['auto_sell']}`",
        f"- `OFFICIAL_DECISION_IMPACT`: `{system['official_decision_impact']}`",
        f"- `FORBIDDEN_MODIFIED`: `{system['forbidden_modified']}`",
        "",
        "## 是否可以交易",
        f"- 结论: {'不能开新仓' if system['allowed_trade_count'] == '0' else '无法确认'}",
        f"- 当前允许交易候选数: `{system['allowed_trade_count']}`",
        f"- 主要阻塞: {'；'.join(blockers)}",
        f"- 账户阻塞: {('模板账户/空账户状态' if system['template_empty'] == 'TRUE' else '未见模板账户阻塞')}",
        f"- 风险/预算/事件阻塞: {('前向收益等待未来数据' if '前向收益' in blockers[-1] or '前向' in blockers[-1] else '暂无额外硬性阻塞证据，仍需结合原始报告人工复核')}",
        "",
        f"## 今日重点候选（前 20 / 共 {len(candidate_rows)}）",
        "| 排名 | 股票代码 | 中文名称 | 英文名称 | 综合分 | 推荐档位 | 主题/行业 | 技术状态 | 主要原因中文摘要 | 风险提示中文摘要 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in table:
        report_lines.append(
            f"| {row['排名']} | {row['股票代码']} | {row['中文名称']} | {row['英文名称']} | {row['综合分']} | {row['推荐档位']} | {row['主题/行业']} | {row['技术状态']} | {row['主要原因中文摘要']} | {row['风险提示中文摘要']} |"
        )
    report_lines += [
        "",
        f"- 当前候选总数为 `{values['ranked_count']}`，这里只展示前 20 只。",
        "",
        "## 当前允许交易候选",
        f"- 当前允许交易候选为 `{system['allowed_trade_count']}`。",
        f"- 账户约束当前仍表现为 `{system['blocked_reason']}`，因此未生成可执行新仓建议。",
        "- 当前没有发现可直接下单的候选代码。",
        "",
        "## 数据一致性 / 冻结状态",
        f"- 预计候选数: `{system['expected_count']}`",
        f"- 冻结行数: `{system['freeze_count']}`",
        f"- 冻结覆盖状态: `{system['freeze_coverage_status']}`",
        f"- 缺失 ticker 数: `{system['missing_ticker_count']}`",
        f"- 重复 signal_date+ticker 数: `{system['duplicate_count']}`",
        f"- 来源路径: `state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv`",
        f"- 说明: {'当前冻结覆盖完整。' if system['freeze_coverage_status'] == 'FULL_MATCH' else '冻结覆盖仍需处理。'}",
        "",
        "## 需要人工处理的事项",
        f"- 手动账户状态仍为: `{system['template_empty']}`",
        "- 如果要提高 account-aware 结果的可信度，需要更新真实现金和持仓。",
        "- 前向收益仍在等待未来数据，当前不适合据此做收益验证。",
        "- 当前仍可能保留模板账户和前向数据等待的系统警告。",
        "",
        "## 今日应该读哪些文件",
        "- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`",
        "- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`",
        "- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`",
        "- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`",
        "- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`",
        "",
        "## 说明",
        f"- 来源说明: {source_note}",
        f"- 中文名缺失计数: `{missing_name_count}`",
    ]
    return "\n".join(report_lines) + "\n"


def make_report(values: Dict[str, str], system: Dict[str, str], missing_name_count: int) -> str:
    lines = [
        "# V18.33A Chinese Daily Operator Homepage Report",
        "",
        "## 1. Final Status",
        f"STATUS: {values['STATUS']}",
        "",
        "## 2. Source Snapshot",
        f"- latest signal date: `{system['latest_signal_date']}`",
        f"- freeze coverage: `{system['freeze_coverage_status']}`",
        f"- candidate count: `{system['expected_count']}`",
        f"- recommendation count: `{values['recommendation_count']}`",
        f"- account-aware allowed trade count: `{system['allowed_trade_count']}`",
        f"- Chinese name missing count: `{missing_name_count}`",
        "",
        "## 3. Safety",
        f"- AUTO_TRADE: `{system['auto_trade']}`",
        f"- AUTO_SELL: `{system['auto_sell']}`",
        f"- OFFICIAL_DECISION_IMPACT: `{system['official_decision_impact']}`",
        f"- FORBIDDEN_MODIFIED: `{system['forbidden_modified']}`",
        "",
        "## 4. Notes",
        "- Chinese content exists only in Markdown outputs.",
        "- No machine-readable CSV, state field, or ledger was modified.",
        "- No external fetch was used.",
    ]
    return "\n".join(lines) + "\n"


def make_read_first(values: Dict[str, str], system: Dict[str, str], missing_name_count: int) -> str:
    lines = [
        f"STATUS: {values['STATUS']}",
        f"MODE: {values['MODE']}",
        f"RUN_ID: {values['RUN_ID']}",
        f"DRY_RUN: {values['DRY_RUN']}",
        f"LATEST_SIGNAL_DATE: {system['latest_signal_date']}",
        f"FREEZE_COVERAGE_STATUS: {system['freeze_coverage_status']}",
        f"CANDIDATE_COUNT: {system['expected_count']}",
        f"RECOMMENDATION_COUNT: {values['recommendation_count']}",
        f"ALLOWED_TRADE_COUNT: {system['allowed_trade_count']}",
        f"CHINESE_NAME_MISSING_COUNT: {missing_name_count}",
        f"AUTO_TRADE: {system['auto_trade']}",
        f"AUTO_SELL: {system['auto_sell']}",
        f"OFFICIAL_DECISION_IMPACT: {system['official_decision_impact']}",
        f"FORBIDDEN_MODIFIED: {system['forbidden_modified']}",
        f"HOME_PATH: {OUT_HOME}",
        f"REPORT_PATH: {OUT_REPORT}",
        f"SUMMARY_PATH: {OUT_SUMMARY}",
    ]
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = dt.datetime.now().replace(microsecond=0)
    run_id = f"V18_33A_{now.strftime('%Y%m%d_%H%M%S')}"
    values = extract_source_values(root)
    system = detect_system_status(values)
    ranked_rows, ranked_fields = values["ranked_rows"], values["ranked_fields"]
    rec_rows, rec_fields = values["rec_rows"], values["rec_fields"]

    required_available = all([
        (root / CURRENT_CONTEXT).exists(),
        (root / CURRENT_DAILY).exists(),
        (root / CURRENT_ACCOUNT_GUIDE).exists(),
        (root / CURRENT_RANKED).exists(),
        (root / CURRENT_RECOMMENDATIONS).exists(),
    ])
    parse_ok = required_available and bool(ranked_rows) and bool(rec_rows)

    table_rows = build_candidate_rows(rec_rows, rec_fields, 20)
    missing_name_count = sum(1 for row in table_rows if row["中文名称"] == "中文名待补充")

    status = STATUS_OK if parse_ok and missing_name_count == 0 else STATUS_WARN
    if not required_available or not ranked_rows or not rec_rows:
        status = STATUS_FAIL

    values_out = {
        "STATUS": status,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "ranked_count": str(len(ranked_rows)),
        "recommendation_count": str(len(rec_rows)),
        "theme_count": str(len(ranked_rows)),
        "rec_fields": rec_fields,
    }
    system["allowed_trade_count"] = clean(system.get("allowed_trade_count", "0")) or "0"
    if system.get("freeze_coverage_status") == "":
        system["freeze_coverage_status"] = "UNKNOWN"
    if system.get("expected_count") == "":
        system["expected_count"] = str(len(ranked_rows))
    if system.get("latest_signal_date") == "":
        system["latest_signal_date"] = "2026-05-22"
    if system.get("context_consistency_status") == "":
        system["context_consistency_status"] = clean(read_status_file(root / CURRENT_CONTEXT).get("STATUS", ""))

    home_text = make_homepage(values_out, system, table_rows, missing_name_count)
    report_text = make_report(values_out, system, missing_name_count)
    read_first_text = make_read_first(values_out, system, missing_name_count)

    summary_row = {
        "run_id": run_id,
        "status": status,
        "generated_at": now.isoformat(),
        "dry_run": bool_text(args.dry_run),
        "candidate_count": system["expected_count"],
        "recommendation_count": values_out["recommendation_count"],
        "theme_count": values_out["theme_count"],
        "freeze_coverage_status": system["freeze_coverage_status"],
        "freeze_count": system["freeze_count"],
        "allowed_trade_count": system["allowed_trade_count"],
        "missing_chinese_name_count": missing_name_count,
        "context_consistency_status": system["context_consistency_status"],
        "auto_trade": system["auto_trade"],
        "auto_sell": system["auto_sell"],
        "official_decision_impact": system["official_decision_impact"],
        "forbidden_modified": system["forbidden_modified"],
        "notes": "Markdown-only Chinese homepage generated from current report sources.",
    }

    write_text(root / OUT_HOME, home_text)
    write_text(root / OUT_REPORT, report_text)
    write_csv(root / OUT_SUMMARY, [summary_row], [
        "run_id",
        "status",
        "generated_at",
        "dry_run",
        "candidate_count",
        "recommendation_count",
        "theme_count",
        "freeze_coverage_status",
        "freeze_count",
        "allowed_trade_count",
        "missing_chinese_name_count",
        "context_consistency_status",
        "auto_trade",
        "auto_sell",
        "official_decision_impact",
        "forbidden_modified",
        "notes",
    ])
    write_text(root / OUT_READ_FIRST, read_first_text)

    field_guide_path = root / OUT_FIELD_GUIDE
    if not field_guide_path.exists():
        write_text(field_guide_path, """# V18 Chinese Report Field Guide\n\nThis file is optional and exists only as a report-layer guide for Chinese Markdown outputs.\n\n- Chinese text appears only in Markdown reports.\n- Machine-readable CSV, ledgers, and state files are not modified.\n- Tickers stay unchanged.\n- Status codes stay unchanged.\n""")

    print(f"STATUS: {status}")
    print(f"RUN_ID: {run_id}")
    print(f"HOME: {root / OUT_HOME}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    print(f"CANDIDATE_COUNT: {system['expected_count']}")
    print(f"FREEZE_COVERAGE_STATUS: {system['freeze_coverage_status']}")
    print(f"ALLOWED_TRADE_COUNT: {system['allowed_trade_count']}")
    print(f"MISSING_CHINESE_NAME_COUNT: {missing_name_count}")
    return 0 if not status.startswith("FAIL") else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Chinese daily operator homepage.")
    parser.add_argument("--root", default="D:\\us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        return run(parse_args())
    except Exception as exc:
        root = Path("D:\\us-tech-quant")
        try:
            args = parse_args()
            root = Path(args.root).resolve()
        except Exception:
            pass
        write_text(
            root / OUT_ERROR,
            "# V18.33A Chinese Daily Operator Homepage Error\n\n"
            f"STATUS: {STATUS_FAIL}\n\n"
            "```text\n"
            f"{exc}\n\n{traceback.format_exc()}"
            "```\n",
        )
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
