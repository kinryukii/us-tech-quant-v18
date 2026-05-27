from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
import csv
import json

from qutumn.common.paths import ROOT, CONFIGS_V16, STATE_V16, OUTPUTS_V16, ensure_dir
from qutumn.common.config_io import load_yaml_like


CORE_ETF = {"QQQ", "XLK", "SMH", "SOXX"}
LEVERAGED_ETF = {"TQQQ", "SOXL"}


@dataclass
class EventRecord:
    event_id: str
    event_date: date
    event_time_jst: str
    event_type: str
    ticker: str
    market: str
    importance: str
    lock_scope: str
    days_before: int
    days_after: int
    restriction: str
    notes: str
    active_start: date
    active_end: date
    is_active: bool
    days_until_event: int


@dataclass
class EventAdjustedRow:
    ticker: str
    role: str
    base_action: str
    base_level: str
    price_freshness_status: str
    current_price_usd: str
    last_price_date: str
    event_gate_status: str
    event_adjusted_action: str
    active_event_count: int
    active_event_ids: str
    strongest_restriction: str
    reason: str


def _safe_int(value: object, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_event_config() -> dict:
    path = CONFIGS_V16 / "event" / "event_gate_config.yaml"
    if not path.exists():
        return {}
    return load_yaml_like(path)


def _ensure_event_calendar() -> Path:
    path = STATE_V16 / "event_calendar.csv"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "event_id,event_date,event_time_jst,event_type,ticker,market,importance,lock_scope,days_before,days_after,restriction,notes\n",
            encoding="utf-8-sig",
        )
    return path


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _read_events() -> tuple[list[EventRecord], list[str]]:
    path = _ensure_event_calendar()
    today = datetime.now().date()

    events: list[EventRecord] = []
    warnings: list[str] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=2):
            event_id = _safe_str(row.get("event_id"))
            event_date_raw = _safe_str(row.get("event_date"))

            if not event_id and not event_date_raw:
                continue

            if not event_id:
                warnings.append(f"row {idx}: missing event_id")
                continue

            parsed_date = _parse_date(event_date_raw)
            if parsed_date is None:
                warnings.append(f"row {idx}: invalid event_date {event_date_raw}")
                continue

            event_type = _safe_str(row.get("event_type")).upper() or "OTHER"
            ticker = _safe_str(row.get("ticker")).upper()
            market = _safe_str(row.get("market")).upper() or "US"
            importance = _safe_str(row.get("importance")).upper() or "MEDIUM"
            lock_scope = _safe_str(row.get("lock_scope")).upper() or "US_ALL"
            restriction = _safe_str(row.get("restriction")).upper() or "OBSERVE_ONLY"

            days_before = _safe_int(row.get("days_before"), 1)
            days_after = _safe_int(row.get("days_after"), 1)

            active_start = parsed_date - timedelta(days=days_before)
            active_end = parsed_date + timedelta(days=days_after)
            is_active = active_start <= today <= active_end
            days_until = (parsed_date - today).days

            events.append(
                EventRecord(
                    event_id=event_id,
                    event_date=parsed_date,
                    event_time_jst=_safe_str(row.get("event_time_jst")),
                    event_type=event_type,
                    ticker=ticker,
                    market=market,
                    importance=importance,
                    lock_scope=lock_scope,
                    days_before=days_before,
                    days_after=days_after,
                    restriction=restriction,
                    notes=_safe_str(row.get("notes")),
                    active_start=active_start,
                    active_end=active_end,
                    is_active=is_active,
                    days_until_event=days_until,
                )
            )

    return events, warnings


def _read_execution_summary() -> list[dict]:
    path = OUTPUTS_V16 / "execution" / "V16_EXECUTION_TICKER_SUMMARY.csv"
    if not path.exists():
        return []

    rows: list[dict] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def _is_single_stock(ticker: str, role: str) -> bool:
    if ticker in CORE_ETF or ticker in LEVERAGED_ETF:
        return False
    if "SINGLE" in role.upper():
        return True
    return True


def _event_impacts_row(event: EventRecord, row: dict) -> bool:
    ticker = _safe_str(row.get("ticker")).upper()
    role = _safe_str(row.get("role")).upper()
    scope = event.lock_scope.upper()

    if scope in {"ALL", "US_ALL"}:
        return True

    if scope == "TICKER":
        return event.ticker == ticker

    if scope == "CORE_ETF":
        return ticker in CORE_ETF

    if scope == "LEVERAGED_ETF":
        return ticker in LEVERAGED_ETF or "LEVERAGED" in role

    if scope == "SINGLE_STOCK":
        if event.ticker:
            return event.ticker == ticker
        return _is_single_stock(ticker, role)

    if event.ticker:
        return event.ticker == ticker

    return False


def _restriction_rank(restriction: str) -> int:
    rank = {
        "FREEZE_NEW_BUYS": 100,
        "OBSERVE_ONLY": 90,
        "DISABLE_LEVERAGED": 80,
        "DISABLE_SINGLE_STOCK": 75,
        "DISABLE_CORE": 70,
        "TRIAL_ONLY": 60,
        "NONE": 0,
    }
    return rank.get(restriction.upper(), 10)


def _strongest_restriction(events: list[EventRecord]) -> str:
    if not events:
        return "NONE"
    return sorted([e.restriction for e in events], key=_restriction_rank, reverse=True)[0]


def _adjust_action(row: dict, impacting_events: list[EventRecord]) -> tuple[str, str, str]:
    base_action = _safe_str(row.get("best_action_status"))
    level = _safe_str(row.get("best_triggered_level")).upper()
    ticker = _safe_str(row.get("ticker")).upper()
    role = _safe_str(row.get("role")).upper()

    if not impacting_events:
        return "NO_EVENT_LOCK", base_action, "No active event lock impacts this ticker."

    restrictions = {event.restriction.upper() for event in impacting_events}
    strongest = _strongest_restriction(impacting_events)

    if "FREEZE_NEW_BUYS" in restrictions:
        return "EVENT_LOCKED", "EVENT_BLOCKED_NEW_BUY", "Active event freezes new buys."

    if "OBSERVE_ONLY" in restrictions:
        return "EVENT_LOCKED", "EVENT_OBSERVE_ONLY", "Active event sets affected ticker to observe-only."

    if "DISABLE_LEVERAGED" in restrictions and (ticker in LEVERAGED_ETF or "LEVERAGED" in role):
        return "EVENT_LOCKED", "EVENT_BLOCKED_LEVERAGED", "Active event disables leveraged ETF actions."

    if "DISABLE_SINGLE_STOCK" in restrictions and _is_single_stock(ticker, role):
        return "EVENT_LOCKED", "EVENT_BLOCKED_SINGLE_STOCK", "Active event disables single-stock actions."

    if "DISABLE_CORE" in restrictions and ticker in CORE_ETF:
        return "EVENT_LOCKED", "EVENT_BLOCKED_CORE", "Active event disables core ETF actions."

    if "TRIAL_ONLY" in restrictions:
        if base_action == "PLAN_ONLY_TRIGGERED" and level == "TRIAL":
            return "EVENT_RESTRICTED", "EVENT_TRIAL_ONLY_ALLOWED", "Active event permits trial-only review."
        return "EVENT_RESTRICTED", "EVENT_TRIAL_ONLY_REVIEW", "Active event caps action to trial-only review."

    return "EVENT_REVIEW", base_action, f"Active event requires review. Strongest restriction: {strongest}."


def build_event_gate() -> tuple[list[EventRecord], list[EventAdjustedRow], dict, list[str]]:
    events, warnings = _read_events()
    execution_rows = _read_execution_summary()

    active_events = [event for event in events if event.is_active]
    adjusted_rows: list[EventAdjustedRow] = []

    for row in execution_rows:
        ticker = _safe_str(row.get("ticker")).upper()
        role = _safe_str(row.get("role"))
        impacting = [event for event in active_events if _event_impacts_row(event, row)]

        gate_status, adjusted_action, reason = _adjust_action(row, impacting)
        strongest = _strongest_restriction(impacting)

        adjusted_rows.append(
            EventAdjustedRow(
                ticker=ticker,
                role=role,
                base_action=_safe_str(row.get("best_action_status")),
                base_level=_safe_str(row.get("best_triggered_level")),
                price_freshness_status=_safe_str(row.get("price_freshness_status")),
                current_price_usd=_safe_str(row.get("current_price_usd")),
                last_price_date=_safe_str(row.get("last_price_date")),
                event_gate_status=gate_status,
                event_adjusted_action=adjusted_action,
                active_event_count=len(impacting),
                active_event_ids=";".join(event.event_id for event in impacting),
                strongest_restriction=strongest,
                reason=reason,
            )
        )

    event_lock_count = sum(1 for row in adjusted_rows if row.event_gate_status != "NO_EVENT_LOCK")

    if warnings:
        status = "REVIEW_REQUIRED"
        reason = "Event calendar contains invalid rows or warnings."
    elif not events:
        status = "READY_NO_EVENTS"
        reason = "Event calendar exists but contains no events."
    elif not active_events:
        status = "READY_NO_ACTIVE_LOCK"
        reason = "Events exist, but no event lock is active today."
    elif event_lock_count > 0:
        status = "EVENT_LOCK_ACTIVE"
        reason = "At least one active event lock affects the current execution universe."
    else:
        status = "READY_NO_IMPACT"
        reason = "Active events exist, but none affect current execution universe."

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "reason": reason,
        "event_count": len(events),
        "active_event_count": len(active_events),
        "adjusted_row_count": len(adjusted_rows),
        "event_lock_count": event_lock_count,
        "warning_count": len(warnings),
    }

    return events, adjusted_rows, summary, warnings


def write_event_gate_outputs(
    events: list[EventRecord],
    adjusted_rows: list[EventAdjustedRow],
    summary: dict,
    warnings: list[str],
) -> tuple[Path, Path, Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "risk")

    event_csv = out_dir / "V16_EVENT_GATE_EVENTS.csv"
    adjusted_csv = out_dir / "V16_EVENT_ADJUSTED_EXECUTION.csv"
    md_path = out_dir / "V16_EVENT_GATE.md"
    json_path = out_dir / "V16_EVENT_GATE.json"

    event_fields = list(EventRecord.__dataclass_fields__.keys())
    with event_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=event_fields)
        writer.writeheader()
        for event in events:
            data = event.__dict__.copy()
            for key in ["event_date", "active_start", "active_end"]:
                data[key] = str(data[key])
            writer.writerow(data)

    adjusted_fields = list(EventAdjustedRow.__dataclass_fields__.keys())
    with adjusted_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=adjusted_fields)
        writer.writeheader()
        for row in adjusted_rows:
            writer.writerow(row.__dict__)

    active_events = [event for event in events if event.is_active]
    impacted_rows = [row for row in adjusted_rows if row.event_gate_status != "NO_EVENT_LOCK"]

    lines: list[str] = []
    lines.append("# V16 Event Gate")
    lines.append("")
    lines.append(f"生成时间：`{summary.get('generated_at')}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append(f"状态：**{summary.get('status')}**")
    lines.append("")
    lines.append(str(summary.get("reason")))
    lines.append("")
    lines.append("重要限制：Event Gate 是风险覆盖层，不产生实盘下单指令。")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---:|")
    for key in ["event_count", "active_event_count", "adjusted_row_count", "event_lock_count", "warning_count"]:
        lines.append(f"| {key} | `{summary.get(key, 0)}` |")

    lines.append("")
    lines.append("## 3. 今日活跃事件")
    lines.append("")
    if active_events:
        lines.append("| event_id | date | type | ticker | importance | scope | restriction | active_window | notes |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for event in active_events:
            lines.append(
                f"| `{event.event_id}` | `{event.event_date}` | `{event.event_type}` | `{event.ticker}` | "
                f"`{event.importance}` | `{event.lock_scope}` | `{event.restriction}` | "
                f"`{event.active_start} to {event.active_end}` | {event.notes} |"
            )
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 4. 受事件影响的执行覆盖")
    lines.append("")
    if impacted_rows:
        lines.append("| ticker | base_action | event_adjusted_action | events | restriction | reason |")
        lines.append("|---|---|---|---|---|---|")
        for row in impacted_rows:
            lines.append(
                f"| `{row.ticker}` | `{row.base_action}` | `{row.event_adjusted_action}` | "
                f"`{row.active_event_ids}` | `{row.strongest_restriction}` | {row.reason} |"
            )
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 5. Event-adjusted ticker table")
    lines.append("")
    if adjusted_rows:
        lines.append("| ticker | base_action | event_action | gate | freshness | level | events |")
        lines.append("|---|---|---|---|---|---|---|")
        for row in adjusted_rows:
            lines.append(
                f"| `{row.ticker}` | `{row.base_action}` | `{row.event_adjusted_action}` | "
                f"`{row.event_gate_status}` | `{row.price_freshness_status}` | `{row.base_level}` | `{row.active_event_ids}` |"
            )
    else:
        lines.append("无 execution summary。")

    lines.append("")
    lines.append("## 6. Calendar warnings")
    lines.append("")
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 7. 如何添加事件")
    lines.append("")
    lines.append("编辑文件：state/v16/event_calendar.csv")
    lines.append("")
    lines.append("字段：event_id,event_date,event_time_jst,event_type,ticker,market,importance,lock_scope,days_before,days_after,restriction,notes")
    lines.append("")
    lines.append("下一步进入 V16.7 Behavior Guard：把 FOMO、防乱补仓、防乱追高、防杠杆冲动写入每日纪律层。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "summary": summary,
        "events": [
            {
                **event.__dict__,
                "event_date": str(event.event_date),
                "active_start": str(event.active_start),
                "active_end": str(event.active_end),
            }
            for event in events
        ],
        "adjusted_rows": [row.__dict__ for row in adjusted_rows],
        "warnings": warnings,
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, event_csv, adjusted_csv, json_path


def run_event_gate() -> int:
    events, adjusted_rows, summary, warnings = build_event_gate()
    md_path, event_csv, adjusted_csv, json_path = write_event_gate_outputs(events, adjusted_rows, summary, warnings)

    print("")
    print("V16 event gate completed.")
    print(f"- status: {summary.get('status')}")
    print(f"- events: {len(events)}")
    print(f"- active_events: {summary.get('active_event_count')}")
    print(f"- event_locks: {summary.get('event_lock_count')}")
    print(f"- report: {md_path}")
    print(f"- event_csv: {event_csv}")
    print(f"- adjusted_csv: {adjusted_csv}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_event_gate())
