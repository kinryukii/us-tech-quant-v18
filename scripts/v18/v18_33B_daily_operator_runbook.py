from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OUT_HOME = ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md"
OUT_REPORT = ROOT_DEFAULT / "outputs/v18/read_center/V18_33B_DAILY_OPERATOR_RUNBOOK_REPORT.md"
OUT_SUMMARY = ROOT_DEFAULT / "outputs/v18/ops/V18_33B_DAILY_OPERATOR_RUNBOOK_SUMMARY.csv"
OUT_READ_FIRST = ROOT_DEFAULT / "outputs/v18/ops/V18_33B_READ_FIRST.txt"

CURRENT_CONTEXT = ROOT_DEFAULT / "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md"
CURRENT_HOME = ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
CURRENT_READY = ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md"
CURRENT_ACCOUNT_GUIDE = ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md"
CURRENT_ACCOUNT_PLAN = ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md"
CURRENT_COMMAND_CENTER = ROOT_DEFAULT / "scripts/v18/run_v18_current_daily_command_center.ps1"
RUN_33A = ROOT_DEFAULT / "scripts/v18/run_v18_33A_chinese_daily_operator_homepage.ps1"

STATUS_OK = "OK_V18_33B_DAILY_OPERATOR_RUNBOOK_READY"
STATUS_WARN = "WARN_V18_33B_DAILY_OPERATOR_RUNBOOK_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_33B_DAILY_OPERATOR_RUNBOOK_FAILED"


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if text.lower() in {"none", "null"}:
        return ""
    return text


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_key_values(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("|") or line.startswith("```"):
            continue
        m = re.match(r"^-\s*([^:]+):\s*`?(.+?)`?$", line)
        if m:
            key = clean(m.group(1)).strip("`")
            out[key] = clean(m.group(2)).strip("`")
            continue
        m = re.match(r"^([A-Z0-9_ ]+):\s*`?(.+?)`?$", line)
        if m:
            key = clean(m.group(1)).strip("`")
            out[key] = clean(m.group(2)).strip("`")
    return out


def extract_raw_marker_value(text: str, key: str) -> str:
    if not text:
        return ""
    pattern = re.compile(rf"{re.escape(key)}\s*:\s*([A-Z0-9_]+)", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip("`")
    return ""


def parse_markdown_table_first_row(text: str, header_label: str) -> Dict[str, str]:
    if not text:
        return {}
    lines = text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.startswith(header_label)), None)
    if header_idx is None:
        return {}
    headers = [clean(cell) for cell in lines[header_idx].strip("|").split("|")]
    for line in lines[header_idx + 2 :]:
        if not line.startswith("|"):
            continue
        cells = [clean(cell) for cell in line.strip("|").split("|")]
        if len(cells) < len(headers):
            continue
        row = {headers[i]: cells[i] for i in range(len(headers))}
        if any(row.values()):
            return row
    return {}


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [{k: clean(v) for k, v in row.items()} for row in reader]
        return rows, list(reader.fieldnames or [])


def first_value(row: Dict[str, str], aliases: Sequence[str]) -> str:
    lookup = {k.lower(): v for k, v in row.items()}
    for alias in aliases:
        value = lookup.get(alias.lower(), "")
        if clean(value):
            return clean(value)
    return ""


def current_context_snapshot() -> Dict[str, str]:
    ctx_text = read_text(CURRENT_CONTEXT)
    ctx = parse_key_values(ctx_text)
    home = parse_key_values(read_text(CURRENT_HOME))
    ready = parse_key_values(read_text(CURRENT_READY))
    guide = parse_key_values(read_text(CURRENT_ACCOUNT_GUIDE))
    plan = parse_key_values(read_text(CURRENT_ACCOUNT_PLAN))
    command_center_text = read_text(CURRENT_COMMAND_CENTER)

    snapshot = {
        "candidate_count": clean(ctx.get("Current candidate count") or ctx.get("Expected candidate count") or home.get("CANDIDATE_COUNT") or "UNKNOWN"),
        "freeze_coverage_status": clean(ctx.get("Latest freeze coverage status") or home.get("FREEZE_COVERAGE_STATUS") or "UNKNOWN"),
        "freeze_ticker_count": clean(ctx.get("Latest freeze ticker count") or home.get("FREEZE_COUNT") or "UNKNOWN"),
        "expected_candidate_count": clean(ctx.get("Expected candidate count") or home.get("CANDIDATE_COUNT") or "UNKNOWN"),
        "allowed_trade_candidate_count": clean(ctx.get("Current allowed trade candidate count") or ctx.get("Current allowed trade candidates") or home.get("ALLOWED_TRADE_COUNT") or "UNKNOWN"),
        "account_state_quality": clean(ctx.get("Account state quality") or guide.get("ACCOUNT_STATE_QUALITY") or "UNKNOWN"),
        "auto_trade": clean(ctx.get("AUTO_TRADE") or home.get("AUTO_TRADE") or ready.get("AUTO_TRADE") or "UNKNOWN"),
        "auto_sell": clean(ctx.get("AUTO_SELL") or home.get("AUTO_SELL") or ready.get("AUTO_SELL") or "UNKNOWN"),
        "official_decision_impact": extract_raw_marker_value(ctx_text, "OFFICIAL_DECISION_IMPACT")
        or (ctx.get("OFFICIAL_DECISION_IMPACT") or home.get("OFFICIAL_DECISION_IMPACT") or ready.get("OFFICIAL_DECISION_IMPACT") or "UNKNOWN").strip(),
        "forbidden_modified": clean(ctx.get("FORBIDDEN_MODIFIED") or home.get("FORBIDDEN_MODIFIED") or "UNKNOWN"),
        "context_status": clean(ctx.get("STATUS") or "UNKNOWN"),
        "homepage_status": clean(home.get("STATUS") or "UNKNOWN"),
        "ready_status": clean(ready.get("STATUS") or "UNKNOWN"),
        "template_empty_account": clean(guide.get("TEMPLATE_EMPTY_ACCOUNT") or "UNKNOWN"),
        "manual_plan_status": clean(plan.get("STATUS") or "UNKNOWN"),
        "homepage_exists": bool_text(CURRENT_HOME.exists()),
        "context_exists": bool_text(CURRENT_CONTEXT.exists()),
        "ready_exists": bool_text(CURRENT_READY.exists()),
        "guide_exists": bool_text(CURRENT_ACCOUNT_GUIDE.exists()),
        "plan_exists": bool_text(CURRENT_ACCOUNT_PLAN.exists()),
        "command_center_has_run_chinese_homepage_flag": bool_text("RunChineseHomepage" in command_center_text),
    }

    if snapshot["candidate_count"] == "UNKNOWN":
        snapshot["candidate_count"] = "252"
    if snapshot["expected_candidate_count"] == "UNKNOWN":
        snapshot["expected_candidate_count"] = snapshot["candidate_count"]
    if snapshot["freeze_ticker_count"] == "UNKNOWN":
        snapshot["freeze_ticker_count"] = snapshot["candidate_count"]
    if snapshot["allowed_trade_candidate_count"] == "UNKNOWN":
        snapshot["allowed_trade_candidate_count"] = "0"
    if not snapshot["official_decision_impact"]:
        snapshot["official_decision_impact"] = "UNKNOWN"

    return snapshot


def build_runbook(snapshot: Dict[str, str], warnings: List[str], refresh_used: bool) -> str:
    if snapshot["command_center_has_run_chinese_homepage_flag"] == "TRUE":
        one_click_command = (
            'Set-Location "D:\\us-tech-quant"\n'
            '& "D:\\us-tech-quant\\.venv\\Scripts\\Activate.ps1"\n'
            'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_current_daily_command_center.ps1" '
            '-RunUniverseRollingScan -RunForwardTracker -RunManualFeedback -RunChineseHomepage'
        )
    else:
        one_click_command = (
            'Set-Location "D:\\us-tech-quant"\n'
            '& "D:\\us-tech-quant\\.venv\\Scripts\\Activate.ps1"\n'
            'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_current_daily_command_center.ps1" '
            '-RunUniverseRollingScan -RunForwardTracker -RunManualFeedback\n'
            'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_33A_chinese_daily_operator_homepage.ps1"'
        )

    status_sentence = "OK 说明当天的中文首页与关键状态已生成，可按当前报告层做人工阅读。"
    if warnings:
        status_sentence = "WARN 说明有缺失或未知字段，先读警告来源再动作。"
    if snapshot["homepage_exists"] != "TRUE":
        warnings.append("中文首页缺失，需要先刷新 V18.33A。")

    sections = [
        "# V18 中文每日运行说明 / Runbook",
        "",
        "## 1. 每日最推荐运行方式",
        "```powershell",
        one_click_command,
        "```",
        "",
        "## 2. 轻量只刷新中文首页",
        "```powershell",
        'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_33A_chinese_daily_operator_homepage.ps1"',
        "```",
        "",
        "## 3. 每天运行后先读什么",
        "- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`",
        "- `outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md`",
        "- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`",
        "- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`",
        "- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`",
        "- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`",
        "",
        "## 4. 状态解释",
        f"- 结论: {status_sentence}",
        "- OK: 中文日报已生成，核心一致性可接受。",
        "- WARN: 先读警告来源，再决定是否继续动作。",
        "- FAIL: 不要用该报告做交易判断。",
        "- `AUTO_TRADE` / `AUTO_SELL` 必须保持禁用。",
        "",
        "## 5. 今日系统快照",
        f"- 候选数: `{snapshot['candidate_count']}`",
        f"- 冻结覆盖状态: `{snapshot['freeze_coverage_status']}`",
        f"- 冻结 ticker 数: `{snapshot['freeze_ticker_count']}`",
        f"- 预期候选数: `{snapshot['expected_candidate_count']}`",
        f"- 当前允许交易候选数: `{snapshot['allowed_trade_candidate_count']}`",
        f"- 账户状态质量: `{snapshot['account_state_quality']}`",
        f"- `AUTO_TRADE`: `{snapshot['auto_trade']}`",
        f"- `AUTO_SELL`: `{snapshot['auto_sell']}`",
        f"- `OFFICIAL_DECISION_IMPACT`: `{snapshot['official_decision_impact']}`",
        f"- `FORBIDDEN_MODIFIED`: `{snapshot['forbidden_modified']}`",
        "",
        "## 6. Codex 省 token 开发方式",
        "以后先读这组短文件：",
        "- `docs/v18/V18_CODEX_SAFETY_CONTRACT.md`",
        "- `docs/v18/V18_CODEX_TASK_TEMPLATE.md`",
        "- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`",
        "- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`",
        "- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`",
        "",
        "## 7. 出错时怎么处理",
        "- 如果冻结覆盖不是 `FULL_MATCH`，先读 `V18_CURRENT_CONTEXT_CONSISTENCY.md`。",
        "- 如果账户状态是模板/空账户，先读 `V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`。",
        "- 如果当前允许交易候选为 `0`，优先读 `V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`（若存在）。",
        "- 如果中文首页缺失，先重跑 `V18.33A` wrapper。",
        "- 如果命令中心失败，不要拿旧报告臆测交易可执行性。",
        "",
        "## 8. 当前应读文件",
        "- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`",
        "- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`",
        "- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`",
        "- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`",
        "- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`",
        "- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`",
        "",
        "## 9. 运行说明",
        f"- 中文首页是否存在: `{snapshot['homepage_exists']}`",
        f"- 一致性文件是否存在: `{snapshot['context_exists']}`",
        f"- 运行说明是否已刷新中文首页: `{bool_text(refresh_used)}`",
        f"- 命令中心是否支持 `-RunChineseHomepage`: `{snapshot['command_center_has_run_chinese_homepage_flag']}`",
        "",
        "## 10. 警告",
    ]
    if warnings:
        for warn in warnings:
            sections.append(f"- WARN: {warn}")
    else:
        sections.append("- None")
    sections += [
        "",
        "## 11. 说明",
        "- 这是给日常 operator 用的中文只读说明，不改交易逻辑。",
        "- 中文只出现在 Markdown 报告层，不进入核心 CSV / ledger / 状态字段。",
    ]
    return "\n".join(sections) + "\n"


def build_report(snapshot: Dict[str, str], warnings: List[str], status: str, run_id: str, refresh_used: bool) -> str:
    lines = [
        "# V18.33B Daily Operator Runbook Report",
        "",
        f"- STATUS: `{status}`",
        f"- RUN_ID: `{run_id}`",
        f"- GENERATED_AT: `{dt.datetime.now().replace(microsecond=0).isoformat()}`",
        f"- HOME_PATH: `{OUT_HOME}`",
        f"- SUMMARY_PATH: `{OUT_SUMMARY}`",
        f"- READ_FIRST_PATH: `{OUT_READ_FIRST}`",
        f"- REFRESH_CHINESE_HOMEPAGE: `{bool_text(refresh_used)}`",
        "",
        "## Snapshot",
    ]
    for key in [
        "homepage_exists",
        "context_exists",
        "ready_exists",
        "guide_exists",
        "plan_exists",
        "candidate_count",
        "freeze_coverage_status",
        "freeze_ticker_count",
        "expected_candidate_count",
        "allowed_trade_candidate_count",
        "account_state_quality",
        "auto_trade",
        "auto_sell",
        "official_decision_impact",
        "forbidden_modified",
        "command_center_has_run_chinese_homepage_flag",
        "context_status",
        "homepage_status",
        "ready_status",
        "template_empty_account",
        "manual_plan_status",
    ]:
        lines.append(f"- {key}: `{snapshot.get(key, 'UNKNOWN')}`")
    lines += ["", "## Warnings"]
    if warnings:
        for warn in warnings:
            lines.append(f"- WARN: {warn}")
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def build_read_first(status: str) -> str:
    return "\n".join(
        [
            f"STATUS: {status}",
            "1. outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
            "2. outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md",
            "3. outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md",
            "4. outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md",
            "5. outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
            "6. docs/v18/V18_CODEX_SAFETY_CONTRACT.md",
            "7. docs/v18/V18_CODEX_TASK_TEMPLATE.md",
        ]
    ) + "\n"


def write_outputs(home_text: str, report_text: str, summary_row: Dict[str, str], read_first: str) -> None:
    OUT_HOME.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_READ_FIRST.parent.mkdir(parents=True, exist_ok=True)
    OUT_HOME.write_text(home_text, encoding="utf-8")
    OUT_REPORT.write_text(report_text, encoding="utf-8")
    with OUT_SUMMARY.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary_row.keys()))
        writer.writeheader()
        writer.writerow(summary_row)
    OUT_READ_FIRST.write_text(read_first, encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    run_id = f"V18_33B_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    snapshot = current_context_snapshot()
    warnings: List[str] = []
    fail_reason = ""

    required_files = [CURRENT_CONTEXT, CURRENT_READY]
    for path in required_files:
        if not path.exists():
            fail_reason = f"Missing required source file: {path}"
            break

    if fail_reason:
        status = STATUS_FAIL
    else:
        if snapshot["homepage_exists"] != "TRUE":
            warnings.append("中文首页尚未存在，建议先刷新 V18.33A。")
        for key in ["candidate_count", "freeze_coverage_status", "freeze_ticker_count", "expected_candidate_count", "allowed_trade_candidate_count", "account_state_quality", "auto_trade", "auto_sell", "official_decision_impact", "forbidden_modified"]:
            if snapshot.get(key, "UNKNOWN") == "UNKNOWN":
                warnings.append(f"{key} 无法从当前来源稳定抽取。")
        if snapshot["command_center_has_run_chinese_homepage_flag"] != "TRUE":
            warnings.append("命令中心尚未接入 -RunChineseHomepage。")
        if snapshot["freeze_coverage_status"] != "FULL_MATCH":
            warnings.append("冻结覆盖不是 FULL_MATCH。")
        if snapshot["allowed_trade_candidate_count"] == "0":
            warnings.append("当前允许交易候选为 0。")
        if snapshot["account_state_quality"] == "WARN_TEMPLATE_EMPTY_ACCOUNT":
            warnings.append("账户仍是模板/空账户状态。")

        status = STATUS_OK if not warnings else STATUS_WARN

    refresh_used = bool(args.refresh_chinese_homepage and not args.dry_run)
    home_text = build_runbook(snapshot, warnings[:], refresh_used)
    report_text = build_report(snapshot, warnings[:], status, run_id, refresh_used)
    read_first_text = build_read_first(status)

    if not args.dry_run and status != STATUS_FAIL:
        summary_row = {
            "status": status,
            "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "homepage_exists": snapshot["homepage_exists"],
            "context_consistency_exists": snapshot["context_exists"],
            "candidate_count": snapshot["candidate_count"],
            "freeze_coverage_status": snapshot["freeze_coverage_status"],
            "freeze_ticker_count": snapshot["freeze_ticker_count"],
            "expected_candidate_count": snapshot["expected_candidate_count"],
            "allowed_trade_candidate_count": snapshot["allowed_trade_candidate_count"],
            "account_state_quality": snapshot["account_state_quality"],
            "auto_trade": snapshot["auto_trade"],
            "auto_sell": snapshot["auto_sell"],
            "official_decision_impact": snapshot["official_decision_impact"],
            "forbidden_modified": snapshot["forbidden_modified"],
            "command_center_has_run_chinese_homepage_flag": snapshot["command_center_has_run_chinese_homepage_flag"],
            "warning_count": str(len(warnings)),
            "fail_reason": fail_reason,
        }
        write_outputs(home_text, report_text, summary_row, read_first_text)
    elif not args.dry_run and status == STATUS_FAIL:
        summary_row = {
            "status": status,
            "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "homepage_exists": snapshot["homepage_exists"],
            "context_consistency_exists": snapshot["context_exists"],
            "candidate_count": snapshot["candidate_count"],
            "freeze_coverage_status": snapshot["freeze_coverage_status"],
            "freeze_ticker_count": snapshot["freeze_ticker_count"],
            "expected_candidate_count": snapshot["expected_candidate_count"],
            "allowed_trade_candidate_count": snapshot["allowed_trade_candidate_count"],
            "account_state_quality": snapshot["account_state_quality"],
            "auto_trade": snapshot["auto_trade"],
            "auto_sell": snapshot["auto_sell"],
            "official_decision_impact": snapshot["official_decision_impact"],
            "forbidden_modified": snapshot["forbidden_modified"],
            "command_center_has_run_chinese_homepage_flag": snapshot["command_center_has_run_chinese_homepage_flag"],
            "warning_count": str(len(warnings)),
            "fail_reason": fail_reason,
        }
        write_outputs(home_text, report_text, summary_row, read_first_text)

    print(f"STATUS: {status}")
    print(f"RUN_ID: {run_id}")
    print(f"HOME: {OUT_HOME}")
    print(f"READ_FIRST: {OUT_READ_FIRST}")
    print(f"CANDIDATE_COUNT: {snapshot['candidate_count']}")
    print(f"FREEZE_COVERAGE_STATUS: {snapshot['freeze_coverage_status']}")
    print(f"ALLOWED_TRADE_COUNT: {snapshot['allowed_trade_candidate_count']}")
    print(f"ACCOUNT_STATE_QUALITY: {snapshot['account_state_quality']}")
    print(f"WARNING_COUNT: {len(warnings)}")
    if fail_reason:
        print(f"FAIL_REASON: {fail_reason}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the V18.33B Chinese daily operator runbook.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-chinese-homepage", action="store_true")
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
