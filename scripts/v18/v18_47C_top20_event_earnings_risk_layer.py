from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


PATCH_VERSION = "V18.47C"
PATCH_NAME = "Top20 Event / Earnings Risk Layer"

RISK_LEVELS = [
    "LOW_PASS",
    "MEDIUM_REDUCE_SIZE",
    "HIGH_HOLD_REVIEW",
    "EXTREME_NO_NEW_BUYS",
    "UNKNOWN_REVIEW",
]

KNOWN_SEVERITY = {
    "LOW_PASS": 0,
    "MEDIUM_REDUCE_SIZE": 1,
    "HIGH_HOLD_REVIEW": 2,
    "EXTREME_NO_NEW_BUYS": 3,
}

BUY_PERMISSION = {
    "LOW_PASS": "EVENT_GATE_PASS",
    "MEDIUM_REDUCE_SIZE": "SMALL_SIZE_ONLY",
    "HIGH_HOLD_REVIEW": "NO_CHASE_HOLD_REVIEW",
    "EXTREME_NO_NEW_BUYS": "NO_NEW_BUYS_EVENT_LOCKED",
    "UNKNOWN_REVIEW": "EVENT_DATA_UNKNOWN_REVIEW_REQUIRED",
}

SELL_REVIEW = {
    "LOW_PASS": "NO_EVENT_SELL_REVIEW_REQUIRED",
    "MEDIUM_REDUCE_SIZE": "REVIEW_POSITION_SIZE",
    "HIGH_HOLD_REVIEW": "REVIEW_HOLDING_RISK",
    "EXTREME_NO_NEW_BUYS": "REDUCE_RISK_REVIEW",
    "UNKNOWN_REVIEW": "EVENT_DATA_UNKNOWN_REVIEW_REQUIRED",
}

OUTPUT_COLUMNS = [
    "snapshot_date",
    "snapshot_timestamp",
    "ticker",
    "rank",
    "base_score",
    "composite_candidate_score",
    "tracking_tier",
    "event_tracking_priority",
    "options_tracking_priority",
    "latest_price_date",
    "freshness_status",
    "actionable_allowed_by_freshness",
    "next_earnings_date",
    "days_to_earnings",
    "earnings_source",
    "earnings_window_flag",
    "post_earnings_window_flag",
    "earnings_risk_level",
    "earnings_risk_reason",
    "macro_event_date",
    "macro_event_type",
    "days_to_macro_event",
    "macro_risk_level",
    "macro_risk_reason",
    "manual_event_flag",
    "manual_event_date",
    "manual_event_type",
    "manual_event_risk_level",
    "manual_event_reason",
    "sector_event_exposure",
    "sector_event_risk_level",
    "final_event_risk_level",
    "final_event_risk_reason",
    "buy_permission_after_event_gate",
    "sell_review_after_event_gate",
    "event_data_quality",
    "event_source_coverage",
    "notes",
]

EVENT_SOURCE_PATHS = [
    "state/v18/manual_event_overrides.csv",
    "state/v18/V18_47C_MANUAL_EVENT_OVERRIDES.csv",
    "state/v18/V18_47C_TOP20_EVENT_EARNINGS_SEED.csv",
    "state/v18/V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv",
    "state/v18/cloud_earnings_event_calendar.csv",
    "state/v16/event_calendar.csv",
    "data/events/v16_macro_events.csv",
    "data/events/v16_earnings_overrides.csv",
]

MANUAL_TEMPLATE_COLUMNS = [
    "event_date",
    "ticker",
    "event_type",
    "event_risk_level",
    "event_reason",
    "applies_to_buy_gate",
    "applies_to_sell_review",
]


def clean(value: object, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, csv.Error, UnicodeDecodeError):
        return []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_int(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    text = str(value).strip()
    if not text or text == "UNKNOWN":
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def business_day_delta(start: date, end: date) -> int:
    step = 1 if end >= start else -1
    days = 0
    cursor = start
    while cursor != end:
        cursor += timedelta(days=step)
        if cursor.weekday() < 5:
            days += step
    return days


def find_top20_source(root: Path) -> Path | None:
    candidates = [
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "ranked_candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_RANKED_CANDIDATES.csv",
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def find_tracker_source(root: Path) -> Path | None:
    path = root / "outputs" / "v18" / "tracking" / "V18_47B_TOP20_PRIORITY_TRACKER.csv"
    return path if path.exists() and path.is_file() else None


def top20_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    rows = [row for row in read_csv(path) if clean(row.get("ticker"), "") != ""]
    rows.sort(key=lambda row: parse_int(row.get("rank") or row.get("freshness_eligible_rank") or row.get("original_full_rank"), 999999))
    return rows[:20]


def tracker_map(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    return {clean(row.get("ticker"), ""): row for row in read_csv(path) if clean(row.get("ticker"), "")}


def existing_event_sources(root: Path) -> tuple[list[Path], list[Path]]:
    found: list[Path] = []
    missing: list[Path] = []
    for rel in EVENT_SOURCE_PATHS:
        path = root / rel
        if path.exists() and path.is_file():
            found.append(path)
        else:
            missing.append(path)
    return found, missing


def ensure_manual_template(root: Path, found_sources: Iterable[Path]) -> Path | None:
    manual_names = {"manual_event_overrides.csv", "V18_47C_MANUAL_EVENT_OVERRIDES.csv"}
    if any(path.name in manual_names for path in found_sources):
        return None
    template = root / "state" / "v18" / "V18_47C_MANUAL_EVENT_OVERRIDES_TEMPLATE.csv"
    if not template.exists():
        write_csv(template, [], MANUAL_TEMPLATE_COLUMNS)
    return template


def event_date_from_row(row: dict[str, str]) -> date | None:
    for key in ["event_date", "manual_event_date", "earnings_date", "manual_next_earnings_date", "date", "calendar_date"]:
        parsed = parse_date(row.get(key))
        if parsed:
            return parsed
    return None


def ticker_from_row(row: dict[str, str]) -> str:
    return clean(row.get("ticker") or row.get("symbol"), "").upper()


def row_source(path: Path, row: dict[str, str]) -> str:
    quality = clean(row.get("source_quality") or row.get("source") or row.get("status"), "")
    return f"{path}:{quality}" if quality else str(path)


def collect_earnings(root: Path, found_sources: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    earnings_names = {
        "cloud_earnings_event_calendar.csv",
        "event_calendar.csv",
        "v16_earnings_overrides.csv",
        "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv",
        "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv",
    }
    for path in found_sources:
        if path.name not in earnings_names:
            continue
        for row in read_csv(path):
            if path.name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv" and clean(row.get("active"), "FALSE").upper() != "TRUE":
                continue
            ticker = ticker_from_row(row)
            event_date = parse_date(row.get("manual_next_earnings_date")) or event_date_from_row(row)
            event_type = clean(row.get("event_type") or row.get("event_name") or row.get("type"), "")
            if path.name == "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv":
                event_type = clean(row.get("event_type"))
                if clean(row.get("event_scope")).upper() != "COMPANY" or event_type.upper() != "EARNINGS":
                    continue
            if ticker and event_date and (path.name in {"v16_earnings_overrides.csv", "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv", "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv"} or "EARN" in event_type.upper() or "earn" in path.name.lower()):
                source = row_source(path, row)
                if path.name == "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv":
                    source = f"AUTO_90D_CACHE:{clean(row.get('source_name'))}"
                rows.append(
                    {
                        "ticker": ticker,
                        "event_date": event_date,
                        "event_type": event_type or "EARNINGS",
                        "source": source,
                        "reason": clean(row.get("notes") or row.get("source_note") or row.get("event_name") or row.get("company") or row.get("company_name"), ""),
                    }
                )
    return rows


def collect_macro(found_sources: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in found_sources:
        if path.name not in {"v16_macro_events.csv", "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv"}:
            continue
        for row in read_csv(path):
            if path.name == "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv" and clean(row.get("event_scope")).upper() != "MACRO":
                continue
            event_date = event_date_from_row(row)
            if not event_date:
                continue
            event_name = clean(row.get("event_name") or row.get("event_type") or row.get("type"), "")
            source = row_source(path, row)
            if path.name == "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv":
                source = f"AUTO_90D_CACHE:{clean(row.get('source_name'))}"
            rows.append(
                {
                    "event_date": event_date,
                    "event_type": event_name or "MACRO",
                    "source": source,
                    "reason": clean(row.get("notes") or row.get("importance"), ""),
                }
            )
    return rows


def collect_manual(found_sources: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    manual_names = {"manual_event_overrides.csv", "V18_47C_MANUAL_EVENT_OVERRIDES.csv", "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv"}
    for path in found_sources:
        if path.name not in manual_names:
            continue
        for row in read_csv(path):
            if path.name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv" and clean(row.get("active"), "FALSE").upper() != "TRUE":
                continue
            risk = clean(row.get("event_risk_level") or row.get("manual_event_risk_level"), "").upper()
            event_date = event_date_from_row(row)
            ticker = ticker_from_row(row)
            if risk not in RISK_LEVELS or not event_date or not ticker:
                continue
            rows.append(
                {
                    "ticker": ticker,
                    "event_date": event_date,
                    "event_type": clean(row.get("event_type"), "MANUAL_EVENT"),
                    "risk_level": risk,
                    "reason": clean(row.get("event_reason"), "Manual event override."),
                    "applies_to_buy_gate": clean(row.get("applies_to_buy_gate"), "TRUE"),
                    "applies_to_sell_review": clean(row.get("applies_to_sell_review"), "TRUE"),
                    "source": str(path),
                }
            )
    return rows


def earnings_risk(ticker: str, earnings_rows: list[dict[str, object]], asof: date) -> dict[str, str]:
    ticker_events = [row for row in earnings_rows if row["ticker"] == ticker]
    future = sorted([row for row in ticker_events if row["event_date"] >= asof], key=lambda row: row["event_date"])
    past = sorted([row for row in ticker_events if row["event_date"] < asof], key=lambda row: row["event_date"], reverse=True)
    if not future and not past:
        return {
            "next_earnings_date": "UNKNOWN",
            "days_to_earnings": "UNKNOWN",
            "earnings_source": "UNKNOWN",
            "earnings_window_flag": "UNKNOWN",
            "post_earnings_window_flag": "LOW_PASS",
            "earnings_risk_level": "UNKNOWN_REVIEW",
            "earnings_risk_reason": "No local earnings date found for ticker.",
        }

    if future:
        row = future[0]
        days = business_day_delta(asof, row["event_date"])
        if days in (0, 1):
            level = "EXTREME_NO_NEW_BUYS"
        elif 2 <= days <= 7:
            level = "HIGH_HOLD_REVIEW"
        elif 8 <= days <= 14:
            level = "MEDIUM_REDUCE_SIZE"
        else:
            level = "LOW_PASS"
        window_flag = "TRUE" if days <= 14 else "FALSE"
        reason = f"Next earnings event is {days} business day(s) away."
        source = clean(row.get("source"))
        next_date = row["event_date"].isoformat()
    else:
        level = "LOW_PASS"
        window_flag = "FALSE"
        reason = "No future local earnings event found; checking post-earnings window."
        source = clean(past[0].get("source")) if past else "UNKNOWN"
        next_date = "UNKNOWN"
        days = "UNKNOWN"

    post_flag = "LOW_PASS"
    if past:
        past_days = business_day_delta(past[0]["event_date"], asof)
        if 0 <= past_days <= 1:
            post_flag = "HIGH_HOLD_REVIEW"
            if KNOWN_SEVERITY[post_flag] > KNOWN_SEVERITY.get(level, -1):
                level = post_flag
                reason = f"Latest known earnings event was {past_days} business day(s) ago."
        elif 2 <= past_days <= 3:
            post_flag = "MEDIUM_REDUCE_SIZE"
            if KNOWN_SEVERITY[post_flag] > KNOWN_SEVERITY.get(level, -1):
                level = post_flag
                reason = f"Latest known earnings event was {past_days} business day(s) ago."

    return {
        "next_earnings_date": next_date,
        "days_to_earnings": str(days),
        "earnings_source": source,
        "earnings_window_flag": window_flag,
        "post_earnings_window_flag": post_flag,
        "earnings_risk_level": level,
        "earnings_risk_reason": reason,
    }


def macro_risk(macro_rows: list[dict[str, object]], asof: date, macro_source_found: bool) -> dict[str, str]:
    if not macro_source_found or not macro_rows:
        return {
            "macro_event_date": "UNKNOWN",
            "macro_event_type": "UNKNOWN",
            "days_to_macro_event": "UNKNOWN",
            "macro_risk_level": "UNKNOWN_REVIEW",
            "macro_risk_reason": "No usable local macro event source found.",
        }
    future = sorted([row for row in macro_rows if row["event_date"] >= asof], key=lambda row: row["event_date"])
    if not future:
        return {
            "macro_event_date": "UNKNOWN",
            "macro_event_type": "NONE_NEAR",
            "days_to_macro_event": "UNKNOWN",
            "macro_risk_level": "LOW_PASS",
            "macro_risk_reason": "No future local macro event window found.",
        }
    watched = {"FOMC", "CPI", "PCE", "NFP"}
    for row in future:
        days = business_day_delta(asof, row["event_date"])
        event_type = clean(row.get("event_type"))
        upper = event_type.upper()
        if days == 0 and any(token in upper for token in watched):
            level = "EXTREME_NO_NEW_BUYS"
        elif days <= 1:
            level = "HIGH_HOLD_REVIEW"
        elif 2 <= days <= 3:
            level = "MEDIUM_REDUCE_SIZE"
        else:
            continue
        return {
            "macro_event_date": row["event_date"].isoformat(),
            "macro_event_type": event_type,
            "days_to_macro_event": str(days),
            "macro_risk_level": level,
            "macro_risk_reason": f"Near macro event detected: {event_type}.",
        }
    return {
        "macro_event_date": future[0]["event_date"].isoformat(),
        "macro_event_type": clean(future[0].get("event_type")),
        "days_to_macro_event": str(business_day_delta(asof, future[0]["event_date"])),
        "macro_risk_level": "LOW_PASS",
        "macro_risk_reason": "No macro event within 3 business days.",
    }


def manual_risk(ticker: str, manual_rows: list[dict[str, object]], asof: date) -> dict[str, str]:
    applicable = [
        row
        for row in manual_rows
        if row["ticker"] in {ticker, "ALL"} and -1 <= business_day_delta(asof, row["event_date"]) <= 14
    ]
    if not applicable:
        return {
            "manual_event_flag": "FALSE",
            "manual_event_date": "UNKNOWN",
            "manual_event_type": "UNKNOWN",
            "manual_event_risk_level": "LOW_PASS",
            "manual_event_reason": "No applicable manual event override.",
        }
    applicable.sort(key=lambda row: KNOWN_SEVERITY.get(row["risk_level"], -1), reverse=True)
    row = applicable[0]
    return {
        "manual_event_flag": "TRUE",
        "manual_event_date": row["event_date"].isoformat(),
        "manual_event_type": clean(row.get("event_type")),
        "manual_event_risk_level": clean(row.get("risk_level")),
        "manual_event_reason": clean(row.get("reason")),
    }


def combine_risks(parts: list[tuple[str, str]]) -> tuple[str, str]:
    unknown_reasons = [reason for level, reason in parts if level == "UNKNOWN_REVIEW"]
    known = [(level, reason) for level, reason in parts if level in KNOWN_SEVERITY]
    if not known:
        return "UNKNOWN_REVIEW", "; ".join(unknown_reasons) or "No usable event risk inputs."
    level, reason = max(known, key=lambda item: KNOWN_SEVERITY[item[0]])
    if level == "LOW_PASS" and unknown_reasons:
        return "UNKNOWN_REVIEW", "Known event risks are low, but missing source data prevents confident pass: " + "; ".join(unknown_reasons)
    return level, reason


def data_quality(earnings_found: bool, macro_found: bool, manual_found: bool, final_level: str) -> str:
    if final_level == "UNKNOWN_REVIEW":
        if not earnings_found and not macro_found and not manual_found:
            return "MISSING_ALL_EVENT_SOURCES"
        if not earnings_found:
            return "MISSING_EARNINGS"
        if not macro_found:
            return "MISSING_MACRO"
        return "UNKNOWN_REVIEW_REQUIRED"
    if earnings_found and macro_found:
        return "COMPLETE" if manual_found else "PARTIAL"
    if not earnings_found and not macro_found:
        return "MISSING_ALL_EVENT_SOURCES"
    if not earnings_found:
        return "MISSING_EARNINGS"
    if not macro_found:
        return "MISSING_MACRO"
    return "PARTIAL"


def build_rows(
    top20: list[dict[str, str]],
    tracker: dict[str, dict[str, str]],
    earnings_rows: list[dict[str, object]],
    macro_rows: list[dict[str, object]],
    manual_rows: list[dict[str, object]],
    source_coverage: str,
    asof: date,
    timestamp: str,
    earnings_found: bool,
    macro_found: bool,
    manual_found: bool,
) -> list[dict[str, str]]:
    macro_result = macro_risk(macro_rows, asof, macro_found)
    rows: list[dict[str, str]] = []
    for index, candidate in enumerate(top20, start=1):
        ticker = clean(candidate.get("ticker")).upper()
        track = tracker.get(ticker, {})
        er = earnings_risk(ticker, earnings_rows, asof)
        mr = macro_result
        manual = manual_risk(ticker, manual_rows, asof)
        sector_exposure = clean(candidate.get("sector_event_exposure") or candidate.get("event_risk_status"), "UNKNOWN")
        sector_level = "LOW_PASS" if sector_exposure in {"UNKNOWN", "NOT_AVAILABLE_RESERVED"} else "MEDIUM_REDUCE_SIZE"
        final_level, final_reason = combine_risks(
            [
                (er["earnings_risk_level"], er["earnings_risk_reason"]),
                (er["post_earnings_window_flag"], "Post-earnings window risk."),
                (mr["macro_risk_level"], mr["macro_risk_reason"]),
                (manual["manual_event_risk_level"], manual["manual_event_reason"]),
                (sector_level, f"Sector event exposure: {sector_exposure}."),
            ]
        )
        row = {
            "snapshot_date": asof.isoformat(),
            "snapshot_timestamp": timestamp,
            "ticker": ticker,
            "rank": clean(candidate.get("rank") or candidate.get("freshness_eligible_rank") or candidate.get("original_full_rank") or index),
            "base_score": clean(candidate.get("base_score")),
            "composite_candidate_score": clean(candidate.get("composite_candidate_score")),
            "tracking_tier": clean(track.get("tracking_tier")),
            "event_tracking_priority": clean(track.get("event_tracking_priority")),
            "options_tracking_priority": clean(track.get("options_tracking_priority")),
            "latest_price_date": clean(candidate.get("latest_price_date")),
            "freshness_status": clean(candidate.get("freshness_status")),
            "actionable_allowed_by_freshness": clean(candidate.get("actionable_allowed_by_freshness")),
            **er,
            **mr,
            **manual,
            "sector_event_exposure": sector_exposure,
            "sector_event_risk_level": sector_level,
            "final_event_risk_level": final_level,
            "final_event_risk_reason": final_reason,
            "buy_permission_after_event_gate": BUY_PERMISSION[final_level],
            "sell_review_after_event_gate": SELL_REVIEW[final_level],
            "event_data_quality": data_quality(earnings_found, macro_found, manual_found, final_level),
            "event_source_coverage": source_coverage,
            "notes": "Read-only event risk layer; no prediction, ranking, weight, trading, broker, or order changes.",
        }
        rows.append(row)
    return rows


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
    return "\n".join(lines)


def build_report(
    top20_source: str,
    tracker_source: str,
    found_sources: list[Path],
    missing_sources: list[Path],
    rows: list[dict[str, str]],
) -> str:
    counts = Counter(row["final_event_risk_level"] for row in rows)
    summary = [
        {"metric": "CURRENT_TOP20_SOURCE", "value": top20_source},
        {"metric": "V18_47B_TRACKER_SOURCE", "value": tracker_source},
        {"metric": "EVENT_SOURCE_COUNT_FOUND", "value": str(len(found_sources))},
        {"metric": "EVENT_SOURCES_FOUND", "value": ";".join(str(path) for path in found_sources) or "NONE"},
        {"metric": "EVENT_SOURCES_MISSING", "value": ";".join(str(path) for path in missing_sources) or "NONE"},
    ] + [{"metric": level, "value": str(counts.get(level, 0))} for level in RISK_LEVELS]
    sections = [
        f"# {PATCH_VERSION} Top20 Event / Earnings Risk Report",
        "",
        "V18.47C is a read-only event risk layer. It does not predict event outcomes and does not change official ranking logic, factor weights, candidate scoring, Top20 selection, freshness eligibility, trading execution, broker/order behavior, signal freeze ledgers, or V18.47A/V18.47B outputs.",
        "",
        "## Source coverage and distribution",
        markdown_table(summary, ["metric", "value"]),
        "",
        "## EXTREME_NO_NEW_BUYS",
        markdown_table([row for row in rows if row["final_event_risk_level"] == "EXTREME_NO_NEW_BUYS"], ["ticker", "rank", "final_event_risk_reason", "buy_permission_after_event_gate"]),
        "",
        "## HIGH_HOLD_REVIEW",
        markdown_table([row for row in rows if row["final_event_risk_level"] == "HIGH_HOLD_REVIEW"], ["ticker", "rank", "final_event_risk_reason", "sell_review_after_event_gate"]),
        "",
        "## MEDIUM_REDUCE_SIZE",
        markdown_table([row for row in rows if row["final_event_risk_level"] == "MEDIUM_REDUCE_SIZE"], ["ticker", "rank", "final_event_risk_reason", "buy_permission_after_event_gate"]),
        "",
        "## UNKNOWN_REVIEW",
        markdown_table([row for row in rows if row["final_event_risk_level"] == "UNKNOWN_REVIEW"], ["ticker", "rank", "event_data_quality", "final_event_risk_reason"]),
        "",
        "## Upcoming earnings windows",
        markdown_table([row for row in rows if row["earnings_window_flag"] == "TRUE" or row["post_earnings_window_flag"] != "LOW_PASS"], ["ticker", "next_earnings_date", "days_to_earnings", "earnings_risk_level", "earnings_risk_reason"]),
        "",
        "## Upcoming macro event windows",
        markdown_table([row for row in rows if row["macro_risk_level"] != "LOW_PASS"], ["ticker", "macro_event_date", "macro_event_type", "days_to_macro_event", "macro_risk_level"]),
        "",
        "## Manual override events",
        markdown_table([row for row in rows if row["manual_event_flag"] == "TRUE"], ["ticker", "manual_event_date", "manual_event_type", "manual_event_risk_level", "manual_event_reason"]),
        "",
        "## Suggested next step",
        "V18.48A Top20 Options Data Collector if options data readiness is the priority, or V18.49B Entry/Exit Plan Generator if action planning is the priority.",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(
    path: Path,
    status: str,
    top20_source: Path | None,
    tracker_source: Path | None,
    found_sources: list[Path],
    missing_sources: list[Path],
    rows: list[dict[str, str]],
    current_alias_written: bool,
    event_risk_path: Path,
    summary_path: Path,
    current_report_path: Path,
    validation_notes: str,
) -> None:
    counts = Counter(row["final_event_risk_level"] for row in rows)
    lines = [
        f"STATUS: {status}",
        f"PATCH_VERSION: {PATCH_VERSION}",
        f"PATCH_NAME: {PATCH_NAME}",
        f"CURRENT_TOP20_SOURCE_FOUND: {'TRUE' if top20_source else 'FALSE'}",
        f"CURRENT_TOP20_SOURCE_PATH: {top20_source if top20_source else 'NONE'}",
        f"TOP20_PRIORITY_TRACKER_FOUND: {'TRUE' if tracker_source else 'FALSE'}",
        f"TOP20_PRIORITY_TRACKER_PATH: {tracker_source if tracker_source else 'NONE'}",
        f"EVENT_SOURCE_COUNT_FOUND: {len(found_sources)}",
        f"EVENT_SOURCES_FOUND: {';'.join(str(path) for path in found_sources) if found_sources else 'NONE'}",
        f"EVENT_SOURCES_MISSING: {';'.join(str(path) for path in missing_sources) if missing_sources else 'NONE'}",
        f"OUTPUT_ROW_COUNT: {len(rows)}",
        f"LOW_PASS_COUNT: {counts.get('LOW_PASS', 0)}",
        f"MEDIUM_REDUCE_SIZE_COUNT: {counts.get('MEDIUM_REDUCE_SIZE', 0)}",
        f"HIGH_HOLD_REVIEW_COUNT: {counts.get('HIGH_HOLD_REVIEW', 0)}",
        f"EXTREME_NO_NEW_BUYS_COUNT: {counts.get('EXTREME_NO_NEW_BUYS', 0)}",
        f"UNKNOWN_REVIEW_COUNT: {counts.get('UNKNOWN_REVIEW', 0)}",
        f"CURRENT_ALIAS_WRITTEN: {'TRUE' if current_alias_written else 'FALSE'}",
        "OFFICIAL_RANKING_CHANGED: FALSE",
        "FACTOR_WEIGHTS_CHANGED: FALSE",
        "TRADING_EXECUTION_ALLOWED: FALSE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
        f"EVENT_RISK_PATH: {event_risk_path}",
        f"SUMMARY_PATH: {summary_path}",
        f"CURRENT_REPORT_PATH: {current_report_path}",
        f"VALIDATION_NOTES: {validation_notes}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V18.47C Top20 event/earnings risk layer.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    now = datetime.now().astimezone()
    asof = now.date()
    timestamp = now.isoformat(timespec="seconds")
    event_dir = root / "outputs" / "v18" / "event_risk"
    read_center = root / "outputs" / "v18" / "read_center"
    ops = root / "outputs" / "v18" / "ops"
    event_risk_path = event_dir / "V18_47C_TOP20_EVENT_EARNINGS_RISK.csv"
    summary_path = event_dir / "V18_47C_TOP20_EVENT_EARNINGS_RISK_SUMMARY.csv"
    report_path = read_center / "V18_47C_TOP20_EVENT_EARNINGS_RISK_REPORT.md"
    current_report_path = read_center / "V18_CURRENT_TOP20_EVENT_EARNINGS_RISK.md"
    read_first_path = ops / "V18_47C_READ_FIRST.txt"

    top20_source = find_top20_source(root)
    tracker_source = find_tracker_source(root)
    found_sources, missing_sources = existing_event_sources(root)
    ensure_manual_template(root, found_sources)

    top20 = top20_rows(top20_source)
    tracker = tracker_map(tracker_source)
    earnings = collect_earnings(root, found_sources)
    macro = collect_macro(found_sources)
    manual = collect_manual(found_sources)
    earnings_found = bool(earnings)
    macro_found = any(path.name == "v16_macro_events.csv" for path in found_sources) and bool(macro)
    manual_found = bool(manual)
    coverage = f"EARNINGS={'TRUE' if earnings_found else 'FALSE'};MACRO={'TRUE' if macro_found else 'FALSE'};MANUAL={'TRUE' if manual_found else 'FALSE'}"

    rows = build_rows(
        top20,
        tracker,
        earnings,
        macro,
        manual,
        coverage,
        asof,
        timestamp,
        earnings_found,
        macro_found,
        manual_found,
    )

    if not found_sources:
        status = "WARN_V18_47C_EVENT_SOURCES_MISSING"
    elif not top20_source or not rows:
        status = "WARN_V18_47C_NO_CURRENT_TOP20_SOURCE"
    else:
        status = "PASS"

    summary_rows = [
        {"summary_type": "SOURCE", "summary_key": "CURRENT_TOP20_SOURCE_PATH", "summary_value": str(top20_source) if top20_source else "NONE"},
        {"summary_type": "SOURCE", "summary_key": "TOP20_PRIORITY_TRACKER_PATH", "summary_value": str(tracker_source) if tracker_source else "NONE"},
        {"summary_type": "SOURCE", "summary_key": "EVENT_SOURCES_FOUND", "summary_value": ";".join(str(path) for path in found_sources) or "NONE"},
        {"summary_type": "SOURCE", "summary_key": "EVENT_SOURCES_MISSING", "summary_value": ";".join(str(path) for path in missing_sources) or "NONE"},
        {"summary_type": "COUNT", "summary_key": "OUTPUT_ROW_COUNT", "summary_value": str(len(rows))},
    ] + [
        {"summary_type": "RISK", "summary_key": level, "summary_value": str(Counter(row["final_event_risk_level"] for row in rows).get(level, 0))}
        for level in RISK_LEVELS
    ] + [
        {"summary_type": "SAFETY", "summary_key": "OFFICIAL_RANKING_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "FACTOR_WEIGHTS_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "TRADING_EXECUTION_ALLOWED", "summary_value": "FALSE"},
    ]

    write_csv(event_risk_path, rows, OUTPUT_COLUMNS)
    write_csv(summary_path, summary_rows, ["summary_type", "summary_key", "summary_value"])
    report = build_report(str(top20_source) if top20_source else "NONE", str(tracker_source) if tracker_source else "NONE", found_sources, missing_sources, rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_alias_written = False
    if args.write_current and rows:
        current_report_path.write_text(report, encoding="utf-8")
        current_alias_written = True

    write_read_first(
        read_first_path,
        status,
        top20_source,
        tracker_source,
        found_sources,
        missing_sources,
        rows,
        current_alias_written,
        event_risk_path,
        summary_path,
        current_report_path,
        "READ_ONLY_TOP20_EVENT_EARNINGS_RISK_NO_RANKING_WEIGHT_TRADING_OR_BROKER_CHANGES",
    )
    print(f"STATUS: {status}")
    print(f"OUTPUT_ROW_COUNT: {len(rows)}")
    print(f"EVENT_SOURCE_COUNT_FOUND: {len(found_sources)}")
    print(f"CURRENT_ALIAS_WRITTEN: {'TRUE' if current_alias_written else 'FALSE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
