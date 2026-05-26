from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json

from qutumn.common.paths import ROOT, STATE_V16, OUTPUTS_V16, ensure_dir


@dataclass
class EventPracticalityRow:
    ticker: str
    candidate_status: str
    trigger_level: str
    price: str
    price_date: str
    event_gate_status: str
    event_calendar_status: str
    confirmation_status: str
    confirmation_id: str
    confirmation_conclusion: str
    restriction: str
    upgrade_status: str
    final_status: str
    reason: str


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows: list[dict] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ensure_confirmation_log() -> Path:
    path = STATE_V16 / "event_confirmation_log.csv"

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "confirmation_id,confirmation_datetime_jst,ticker,scope,checked_cpi,checked_nfp,checked_fomc,checked_earnings,checked_company_news,checked_geopolitical,conclusion,restriction,notes\n",
            encoding="utf-8-sig",
        )

    return path


def _nonempty_rows(rows: list[dict], required_key: str) -> list[dict]:
    result = []
    for row in rows:
        if str(row.get(required_key, "")).strip():
            result.append(row)
    return result


def _event_gate_status() -> str:
    payload = _read_json(OUTPUTS_V16 / "risk" / "V16_EVENT_GATE.json")
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        return "UNKNOWN"
    return str(summary.get("status", "UNKNOWN"))


def _find_confirmation(ticker: str, confirmations: list[dict]) -> dict | None:
    ticker = ticker.upper().strip()

    matched = []

    for row in confirmations:
        row_ticker = str(row.get("ticker", "")).upper().strip()
        scope = str(row.get("scope", "")).upper().strip()

        if row_ticker == ticker or scope in {"ALL", "US_ALL", "SINGLE_STOCK", "TICKER"}:
            matched.append(row)

    if not matched:
        return None

    matched = sorted(
        matched,
        key=lambda r: str(r.get("confirmation_datetime_jst", "")),
        reverse=True,
    )

    return matched[0]


def _decide_row(candidate: dict, event_rows: list[dict], confirmations: list[dict], gate_status: str) -> EventPracticalityRow:
    ticker = str(candidate.get("ticker", "")).upper().strip()
    candidate_status = str(candidate.get("review_status", "")).strip()

    event_calendar_status = "HAS_EVENTS" if event_rows else "EMPTY_EVENT_CALENDAR"

    confirmation = _find_confirmation(ticker, confirmations)
    confirmation_id = ""
    confirmation_conclusion = ""
    restriction = ""
    confirmation_status = "MISSING_CONFIRMATION"

    if confirmation is not None:
        confirmation_id = str(confirmation.get("confirmation_id", ""))
        confirmation_conclusion = str(confirmation.get("conclusion", "")).upper().strip()
        restriction = str(confirmation.get("restriction", "")).upper().strip()
        confirmation_status = "CONFIRMED"

    blocking_conclusions = {
        "BLOCK",
        "OBSERVE_ONLY",
        "FREEZE_NEW_BUYS",
        "EARNINGS_RISK",
        "MACRO_RISK",
        "COMPANY_NEWS_RISK",
    }

    clear_conclusions = {
        "CLEAR",
        "NO_KNOWN_EVENT",
        "REVIEW_ONLY_OK",
    }

    if candidate_status != "REVIEW_ONLY_CANDIDATE":
        upgrade_status = "NOT_A_REVIEW_ONLY_CANDIDATE"
        final_status = "NO_UPGRADE"
        reason = "Candidate is not REVIEW_ONLY_CANDIDATE."
    elif gate_status == "EVENT_LOCK_ACTIVE":
        upgrade_status = "UPGRADE_BLOCKED_EVENT_GATE_ACTIVE"
        final_status = "REVIEW_ONLY_EVENT_BLOCKED"
        reason = "Event Gate has active lock."
    elif event_calendar_status == "EMPTY_EVENT_CALENDAR" and confirmation is None:
        upgrade_status = "UPGRADE_BLOCKED_EVENT_CALENDAR_EMPTY"
        final_status = "REVIEW_ONLY_EVENT_UNCONFIRMED"
        reason = "Event calendar is empty and no manual confirmation exists."
    elif confirmation is None:
        upgrade_status = "UPGRADE_BLOCKED_CONFIRMATION_MISSING"
        final_status = "REVIEW_ONLY_EVENT_UNCONFIRMED"
        reason = "Manual event confirmation is missing for candidate."
    elif confirmation_conclusion in blocking_conclusions or restriction in blocking_conclusions:
        upgrade_status = "UPGRADE_BLOCKED_EVENT_RISK"
        final_status = "REVIEW_ONLY_EVENT_BLOCKED"
        reason = "Manual event confirmation indicates blocking event risk."
    elif confirmation_conclusion in clear_conclusions or restriction in {"NONE", "REVIEW_ONLY"}:
        upgrade_status = "EVENT_CONFIRMED_REVIEW_ONLY"
        final_status = "REVIEW_ONLY_EVENT_CONFIRMED"
        reason = "Manual event confirmation exists. Candidate remains review-only, not a trade instruction."
    else:
        upgrade_status = "UPGRADE_BLOCKED_CONFIRMATION_AMBIGUOUS"
        final_status = "REVIEW_ONLY_EVENT_UNCONFIRMED"
        reason = "Manual event confirmation exists but conclusion is ambiguous."

    return EventPracticalityRow(
        ticker=ticker,
        candidate_status=candidate_status,
        trigger_level=str(candidate.get("trigger_level", "")),
        price=str(candidate.get("current_price_usd", "")),
        price_date=str(candidate.get("last_price_date", "")),
        event_gate_status=gate_status,
        event_calendar_status=event_calendar_status,
        confirmation_status=confirmation_status,
        confirmation_id=confirmation_id,
        confirmation_conclusion=confirmation_conclusion,
        restriction=restriction,
        upgrade_status=upgrade_status,
        final_status=final_status,
        reason=reason,
    )


def build_event_practicality() -> tuple[list[EventPracticalityRow], dict]:
    confirmation_path = _ensure_confirmation_log()

    candidate_rows = _read_csv(OUTPUTS_V16 / "review" / "V16_CANDIDATE_REVIEW.csv")
    candidate_rows = [
        row for row in candidate_rows
        if str(row.get("review_status", "")).strip() == "REVIEW_ONLY_CANDIDATE"
    ]

    event_rows = _nonempty_rows(_read_csv(STATE_V16 / "event_calendar.csv"), "event_id")
    confirmation_rows = _nonempty_rows(_read_csv(confirmation_path), "confirmation_id")

    gate_status = _event_gate_status()

    rows = [
        _decide_row(candidate, event_rows, confirmation_rows, gate_status)
        for candidate in candidate_rows
    ]

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "candidate_count": len(candidate_rows),
        "event_calendar_count": len(event_rows),
        "confirmation_count": len(confirmation_rows),
        "event_gate_status": gate_status,
        "event_unconfirmed_count": sum(1 for r in rows if r.final_status == "REVIEW_ONLY_EVENT_UNCONFIRMED"),
        "event_blocked_count": sum(1 for r in rows if r.final_status == "REVIEW_ONLY_EVENT_BLOCKED"),
        "event_confirmed_review_only_count": sum(1 for r in rows if r.final_status == "REVIEW_ONLY_EVENT_CONFIRMED"),
        "small_real_trial_candidate_count": 0,
    }

    if summary["candidate_count"] == 0:
        status = "NO_CANDIDATES"
        reason = "No REVIEW_ONLY candidate exists."
    elif summary["event_unconfirmed_count"] > 0:
        status = "EVENT_CONFIRMATION_REQUIRED"
        reason = "At least one candidate lacks event confirmation. No upgrade allowed."
    elif summary["event_blocked_count"] > 0:
        status = "EVENT_BLOCKED"
        reason = "At least one candidate is blocked by event risk."
    else:
        status = "EVENT_REVIEW_ONLY_CONFIRMED"
        reason = "Event confirmation exists. Candidates remain review-only."

    summary["status"] = status
    summary["reason"] = reason

    return rows, summary


def write_event_practicality(rows: list[EventPracticalityRow], summary: dict) -> tuple[Path, Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "risk")
    md_path = out_dir / "V16_EVENT_PRACTICALITY.md"
    csv_path = out_dir / "V16_EVENT_PRACTICALITY.csv"
    json_path = out_dir / "V16_EVENT_PRACTICALITY.json"

    fieldnames = list(EventPracticalityRow.__dataclass_fields__.keys())

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row.__dict__)

    lines: list[str] = []
    lines.append("# V16 Event Practicality")
    lines.append("")
    lines.append(f"生成时间：`{summary.get('generated_at')}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append(f"状态：**{summary.get('status')}**")
    lines.append("")
    lines.append(str(summary.get("reason")))
    lines.append("")
    lines.append("重要限制：事件实用化层不是行情判断，也不是下单指令。它只决定候选能否从 REVIEW_ONLY 继续升级。")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---:|")
    for key in [
        "candidate_count",
        "event_calendar_count",
        "confirmation_count",
        "event_unconfirmed_count",
        "event_blocked_count",
        "event_confirmed_review_only_count",
        "small_real_trial_candidate_count",
    ]:
        lines.append(f"| {key} | `{summary.get(key, 0)}` |")

    lines.append("")
    lines.append("## 3. Candidate Event Status")
    lines.append("")
    if rows:
        lines.append("| ticker | final_status | upgrade_status | calendar | confirmation | conclusion | reason |")
        lines.append("|---|---|---|---|---|---|---|")
        for row in rows:
            lines.append(
                f"| `{row.ticker}` | `{row.final_status}` | `{row.upgrade_status}` | "
                f"`{row.event_calendar_status}` | `{row.confirmation_status}` | `{row.confirmation_conclusion}` | {row.reason} |"
            )
    else:
        lines.append("无候选。")

    lines.append("")
    lines.append("## 4. 如何填写事件确认")
    lines.append("")
    lines.append("文件：`state\\v16\\event_confirmation_log.csv`")
    lines.append("")
    lines.append("字段：")
    lines.append("")
    lines.append("confirmation_id,confirmation_datetime_jst,ticker,scope,checked_cpi,checked_nfp,checked_fomc,checked_earnings,checked_company_news,checked_geopolitical,conclusion,restriction,notes")
    lines.append("")
    lines.append("示例：")
    lines.append("")
    lines.append("EC20260509_BE,2026-05-09 22:00:00,BE,TICKER,true,true,true,true,true,true,NO_KNOWN_EVENT,REVIEW_ONLY,manual checked")
    lines.append("EC20260509_CRWV,2026-05-09 22:00:00,CRWV,TICKER,true,true,true,true,true,true,NO_KNOWN_EVENT,REVIEW_ONLY,manual checked")
    lines.append("")
    lines.append("## 5. 当前纪律")
    lines.append("")
    if summary.get("status") == "EVENT_CONFIRMATION_REQUIRED":
        lines.append("事件日历为空或确认缺失时，BE / CRWV 只能停留在 REVIEW_ONLY_EVENT_UNCONFIRMED。")
        lines.append("不能升级到 SMALL_REAL_TRIAL_CANDIDATE。")
    elif summary.get("status") == "EVENT_BLOCKED":
        lines.append("存在事件风险阻断，不能升级。")
    elif summary.get("status") == "EVENT_REVIEW_ONLY_CONFIRMED":
        lines.append("事件已人工确认，但仍然只是 REVIEW_ONLY，不是买入指令。")
    else:
        lines.append("当前无候选。")

    lines.append("")
    lines.append("## 6. 下一步")
    lines.append("")
    lines.append("下一步可手动填写 event_confirmation_log.csv，再重新运行 daily flow。")
    lines.append("只有事件确认完成后，系统才允许进入更高一级的小实盘候选研究。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "summary": summary,
        "rows": [row.__dict__ for row in rows],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, json_path


def run_event_practicality() -> int:
    rows, summary = build_event_practicality()
    md_path, csv_path, json_path = write_event_practicality(rows, summary)

    print("")
    print("V16 event practicality completed.")
    print(f"- status: {summary.get('status')}")
    print(f"- candidates: {summary.get('candidate_count')}")
    print(f"- event_unconfirmed: {summary.get('event_unconfirmed_count')}")
    print(f"- event_confirmed_review_only: {summary.get('event_confirmed_review_only_count')}")
    print(f"- report: {md_path}")
    print(f"- csv: {csv_path}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_event_practicality())
