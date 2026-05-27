from pathlib import Path
from datetime import datetime
import csv
import json
import re

root = Path(".").resolve()
stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

workflow_md = root / "outputs/v16/risk/V16_EVENT_CONFIRMATION_WORKFLOW.md"
workflow_json = root / "outputs/v16/risk/V16_EVENT_CONFIRMATION_WORKFLOW.json"
to_fill_path = root / "state/v16/event_confirmation_to_fill.csv"

to_fill_count = 0
if to_fill_path.exists():
    with to_fill_path.open("r", encoding="utf-8-sig", newline="") as f:
        to_fill_count = sum(1 for _ in csv.DictReader(f))

workflow_payload = {
    "summary": {
        "generated_at": stamp,
        "status": "EVENT_CONFIRMATION_WORKFLOW_READY",
        "to_fill_count": to_fill_count,
        "to_fill_file": "state\\v16\\event_confirmation_to_fill.csv",
        "workflow_file": "outputs\\v16\\risk\\V16_EVENT_CONFIRMATION_WORKFLOW.md",
    }
}
workflow_json.write_text(json.dumps(workflow_payload, indent=2, ensure_ascii=False), encoding="utf-8")


# Patch Health Check generator
health_py = root / "src/qutumn/cli/run_healthcheck.py"
txt = health_py.read_text(encoding="utf-8")

if "V16_EVENT_CONFIRMATION_WORKFLOW.md" not in txt:
    txt = txt.replace(
        'OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.md",',
        'OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.md",\n    OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.md",'
    )

if 'STATE_V16 / "event_confirmation_to_fill.csv",' not in txt:
    txt = txt.replace(
        'STATE_V16 / "event_confirmation_pending.csv",',
        'STATE_V16 / "event_confirmation_pending.csv",\n    STATE_V16 / "event_confirmation_to_fill.csv",'
    )

if 'event_workflow = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json")' not in txt:
    txt = txt.replace(
        'event_helper = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.json")',
        'event_helper = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.json")\n    event_workflow = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json")'
    )

if '"event_confirmation_workflow_status":' not in txt:
    txt = txt.replace(
        '"event_confirmation_helper_status": event_helper.get("status", "UNKNOWN"),',
        '"event_confirmation_helper_status": event_helper.get("status", "UNKNOWN"),\n        "event_confirmation_workflow_status": event_workflow.get("status", "UNKNOWN"),\n        "event_confirmation_to_fill_count": event_workflow.get("to_fill_count", 0),'
    )

txt = txt.replace(
    "V16.10D 的价格刷新、候选复核、事件实用化、事件确认模板、执行计划、事件闸门、行为纪律和核心阅读文件完整。",
    "V16.10F 的价格刷新、候选复核、事件实用化、事件确认模板、事件确认工作流、执行计划、事件闸门、行为纪律和核心阅读文件完整。"
)

health_py.write_text(txt, encoding="utf-8")


# Patch Daily generator
daily_py = root / "src/qutumn/cli/run_daily.py"
txt = daily_py.read_text(encoding="utf-8")

if 'event_workflow_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json")' not in txt:
    txt = txt.replace(
        'event_helper_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.json")',
        'event_helper_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_HELPER.json")\n    event_workflow_summary = _summary(OUTPUTS_V16 / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json")'
    )

if 'event_workflow_status = str(event_workflow_summary.get("status", "NOT_RUN"))' not in txt:
    txt = txt.replace(
        'existing_confirmed_count = int(event_helper_summary.get("existing_confirmed_count", 0) or 0)',
        'existing_confirmed_count = int(event_helper_summary.get("existing_confirmed_count", 0) or 0)\n\n    event_workflow_status = str(event_workflow_summary.get("status", "NOT_RUN"))\n    event_confirmation_to_fill_count = int(event_workflow_summary.get("to_fill_count", 0) or 0)'
    )

txt = txt.replace(
    "V16.10D Event Confirmation Helper Integration 已完成。",
    "V16.10F Event Confirmation Workflow Integration 已完成。"
)

if "- V16.10E Event Confirmation Workflow" not in txt:
    txt = txt.replace(
        "- V16.10D Event Confirmation Helper 接入 Daily / Health Check",
        "- V16.10D Event Confirmation Helper 接入 Daily / Health Check\n- V16.10E Event Confirmation Workflow\n- V16.10F Event Confirmation Workflow 接入 Daily / Health Check"
    )

if "事件确认工作流状态：**{event_workflow_status}**" not in txt:
    txt = txt.replace(
        "事件确认模板状态：**{event_helper_status}**",
        "事件确认模板状态：**{event_helper_status}**\n\n事件确认工作流状态：**{event_workflow_status}**"
    )

if "event_confirmation_to_fill_count" not in txt.split("## Event Confirmation Helper 状态", 1)[-1]:
    txt = txt.replace(
        "- existing_confirmed_count：`{existing_confirmed_count}`\n- pending file：`state\\\\v16\\\\event_confirmation_pending.csv`",
        "- existing_confirmed_count：`{existing_confirmed_count}`\n- workflow_status：`{event_workflow_status}`\n- to_fill_count：`{event_confirmation_to_fill_count}`\n- pending file：`state\\\\v16\\\\event_confirmation_pending.csv`"
    )

if "V16_EVENT_CONFIRMATION_WORKFLOW.md" not in txt:
    txt = txt.replace(
        "6. `outputs\\\\v16\\\\risk\\\\V16_EVENT_CONFIRMATION_HELPER.md`",
        "6. `outputs\\\\v16\\\\risk\\\\V16_EVENT_CONFIRMATION_HELPER.md`\n7. `outputs\\\\v16\\\\risk\\\\V16_EVENT_CONFIRMATION_WORKFLOW.md`"
    )

txt = re.sub(
    r"## 下一步[\s\S]*?5\. 检查 BE / CRWV 是否仍只能 REVIEW_ONLY，或被事件风险 BLOCK",
    """## 下一步

进入人工事件确认：

1. 打开 `state\\v16\\event_confirmation_to_fill.csv`
2. 人工检查 CPI / NFP / FOMC / 财报 / 公司新闻 / 地缘风险
3. 把确认后的行复制到 `state\\v16\\event_confirmation_log.csv`
4. 修改 conclusion / restriction
5. 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\run_v16_after_event_confirmation.ps1`
6. 检查 BE / CRWV 是否仍只能 REVIEW_ONLY，或被事件风险 BLOCK""",
    txt
)

daily_py.write_text(txt, encoding="utf-8")


# Patch helper markdown old next-step text
helper_md = root / "outputs/v16/risk/V16_EVENT_CONFIRMATION_HELPER.md"
if helper_md.exists():
    h = helper_md.read_text(encoding="utf-8")
    h = h.replace(
        "下一步进入 V16.10E：按 Event Confirmation Workflow 人工确认事件后，重新运行 daily flow。",
        "下一步：按 V16.10E Event Confirmation Workflow 人工确认事件后，重新运行 after-confirmation flow。"
    )
    helper_md.write_text(h, encoding="utf-8")

print("V16.10F2 patch completed.")
print(f"- workflow_json: {workflow_json}")
print(f"- to_fill_count: {to_fill_count}")
