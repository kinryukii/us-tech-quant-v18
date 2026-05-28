from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


PATCH_VERSION = "V18.47C-R1"
PATCH_NAME = "Event Source Coverage Repair"

RISK_LEVELS = {
    "LOW_PASS",
    "MEDIUM_REDUCE_SIZE",
    "HIGH_HOLD_REVIEW",
    "EXTREME_NO_NEW_BUYS",
    "UNKNOWN_REVIEW",
}

EVENT_SOURCES = [
    "state/v18/cloud_earnings_event_calendar.csv",
    "state/v16/event_calendar.csv",
    "data/events/v16_macro_events.csv",
    "data/events/v16_earnings_overrides.csv",
    "state/v18/manual_event_overrides.csv",
    "state/v18/V18_47C_MANUAL_EVENT_OVERRIDES.csv",
    "state/v18/V18_47C_TOP20_EVENT_EARNINGS_SEED.csv",
]

SEED_COLUMNS = [
    "ticker",
    "company_name",
    "rank",
    "tracking_tier",
    "manual_next_earnings_date",
    "manual_event_date",
    "manual_event_type",
    "manual_event_risk_level",
    "manual_event_reason",
    "source_note",
    "last_reviewed_date",
    "active",
]

AUDIT_COLUMNS = [
    "source_path",
    "source_exists",
    "row_count",
    "detected_ticker_columns",
    "detected_date_columns",
    "detected_event_type_columns",
    "parseable_date_count",
    "min_event_date",
    "max_event_date",
    "current_top20_ticker_match_count",
    "current_top20_ticker_match_rate",
    "missing_required_columns",
    "source_usable",
    "source_issue_reason",
]

NORMALIZED_COLUMNS = [
    "source_path",
    "source_row_number",
    "normalized_ticker",
    "normalized_event_date",
    "normalized_event_type",
    "original_event_type",
    "parse_status",
    "parse_issue_reason",
    "is_current_top20_match",
    "raw_ticker",
    "raw_date",
    "raw_reason",
]

DIAG_COLUMNS = [
    "snapshot_date",
    "ticker",
    "rank",
    "tracking_tier",
    "matched_any_event_source",
    "matched_earnings_source",
    "matched_macro_source",
    "matched_manual_source",
    "matched_seed_source",
    "best_next_earnings_date",
    "best_next_earnings_source",
    "days_to_best_next_earnings",
    "latest_past_earnings_date",
    "latest_past_earnings_source",
    "days_since_latest_past_earnings",
    "nearest_macro_event_date",
    "nearest_macro_event_type",
    "days_to_nearest_macro_event",
    "manual_override_found",
    "seed_row_found",
    "match_status",
    "unknown_reason",
    "recommended_fix",
]


def clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, UnicodeDecodeError, csv.Error):
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


def normalize_ticker(value: object) -> str:
    text = clean(value).upper().strip("'\"")
    if text.startswith("$"):
        text = text[1:]
    text = re.sub(r"\s+", "", text)
    text = text.replace("/", "-")
    if not text or text.isdigit():
        return ""
    if not re.match(r"^[A-Z][A-Z0-9.\-]{0,14}$", text):
        return ""
    return text


def parse_date(value: object) -> tuple[date | None, str]:
    text = clean(value)
    if not text:
        return None, "BLANK_DATE"
    text = text.strip("'\"")
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%-m/%-d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text[:10] if fmt != "%Y%m%d" else text[:8], fmt).date(), ""
        except ValueError:
            continue
    # Windows strptime does not support %-m; handle M/D/YYYY manually.
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if match:
        month, day, year = map(int, match.groups())
        try:
            return date(year, month, day), ""
        except ValueError:
            pass
    return None, f"UNPARSEABLE_DATE:{text}"


def business_days(start: date, end: date) -> int:
    step = 1 if end >= start else -1
    count = 0
    cursor = start
    while cursor != end:
        cursor = date.fromordinal(cursor.toordinal() + step)
        if cursor.weekday() < 5:
            count += step
    return count


def find_top20_source(root: Path) -> Path | None:
    candidates = [
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "ranked_candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_RANKED_CANDIDATES.csv",
    ]
    return next((path for path in candidates if path.exists()), None)


def top20_rows(path: Path | None) -> list[dict[str, str]]:
    if not path:
        return []
    rows = [row for row in read_csv(path) if normalize_ticker(row.get("ticker"))]
    rows.sort(key=lambda row: parse_int(row.get("rank") or row.get("freshness_eligible_rank") or row.get("original_full_rank"), 999999))
    return rows[:20]


def tracker_rows(root: Path) -> tuple[Path | None, dict[str, dict[str, str]]]:
    path = root / "outputs" / "v18" / "tracking" / "V18_47B_TOP20_PRIORITY_TRACKER.csv"
    if not path.exists():
        return None, {}
    return path, {normalize_ticker(row.get("ticker")): row for row in read_csv(path) if normalize_ticker(row.get("ticker"))}


def detect_columns(headers: list[str], names: set[str]) -> list[str]:
    return [header for header in headers if header.strip().lower() in names]


def event_type(raw: str, path: Path) -> str:
    upper = raw.upper()
    name = path.name.upper()
    if "EARN" in upper or "EARN" in name:
        return "EARNINGS"
    if any(token in upper for token in ["FOMC", "CPI", "PCE", "NFP", "MACRO"]) or "MACRO" in name:
        return "MACRO"
    if "MANUAL" in name or "OVERRIDE" in name or "SEED" in name:
        return "MANUAL"
    if "SECTOR" in upper:
        return "SECTOR"
    return "OTHER"


def normalize_source(path: Path, top20: set[str]) -> tuple[list[dict[str, str]], dict[str, str]]:
    exists = path.exists()
    rows = read_csv(path) if exists else []
    headers = list(rows[0].keys()) if rows else []
    ticker_cols = detect_columns(headers, {"ticker", "symbol"})
    date_cols = detect_columns(headers, {"event_date", "date", "earnings_date", "report_date", "next_earnings_date", "manual_next_earnings_date", "manual_event_date", "calendar_date", "announcement_date"})
    type_cols = detect_columns(headers, {"event_type", "type", "event_name", "manual_event_type"})
    normalized: list[dict[str, str]] = []
    parsed_dates: list[date] = []
    matched_tickers: set[str] = set()
    parse_failed = False
    for idx, row in enumerate(rows, start=1):
        raw_ticker = clean(next((row.get(col) for col in ticker_cols if clean(row.get(col))), "ALL" if path.name == "v16_macro_events.csv" else ""))
        ticker = "ALL" if raw_ticker.upper() == "ALL" or path.name == "v16_macro_events.csv" else normalize_ticker(raw_ticker)
        raw_date = clean(next((row.get(col) for col in date_cols if clean(row.get(col))), ""))
        parsed, issue = parse_date(raw_date)
        raw_type = clean(next((row.get(col) for col in type_cols if clean(row.get(col))), ""))
        normalized_type = event_type(raw_type, path)
        if parsed:
            parsed_dates.append(parsed)
        else:
            parse_failed = True
        is_match = ticker in top20
        if is_match:
            matched_tickers.add(ticker)
        normalized.append(
            {
                "source_path": str(path),
                "source_row_number": str(idx),
                "normalized_ticker": ticker,
                "normalized_event_date": parsed.isoformat() if parsed else "",
                "normalized_event_type": normalized_type,
                "original_event_type": raw_type,
                "parse_status": "OK" if parsed else "DATE_PARSE_FAILED",
                "parse_issue_reason": issue,
                "is_current_top20_match": "TRUE" if is_match else "FALSE",
                "raw_ticker": raw_ticker,
                "raw_date": raw_date,
                "raw_reason": clean(row.get("notes") or row.get("event_reason") or row.get("manual_event_reason") or row.get("source_note") or row.get("event_name")),
            }
        )
    missing = []
    if not ticker_cols and path.name != "v16_macro_events.csv":
        missing.append("ticker")
    if not date_cols:
        missing.append("date")
    if not type_cols:
        missing.append("event_type")
    usable = exists and bool(rows) and bool(parsed_dates) and (bool(ticker_cols) or path.name == "v16_macro_events.csv")
    if not exists:
        reason = "SOURCE_MISSING"
    elif not rows:
        reason = "NO_ROWS"
    elif missing:
        reason = "MISSING_REQUIRED_COLUMNS:" + ";".join(missing)
    elif parse_failed and not parsed_dates:
        reason = "EVENT_SOURCE_DATE_PARSE_FAILED"
    elif path.name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv" and not parsed_dates:
        reason = "MANUAL_SEED_BLANK"
    elif not matched_tickers and path.name != "v16_macro_events.csv":
        reason = "NO_CURRENT_TOP20_TICKER_MATCH"
    else:
        reason = "OK"
    audit = {
        "source_path": str(path),
        "source_exists": "TRUE" if exists else "FALSE",
        "row_count": str(len(rows)),
        "detected_ticker_columns": ";".join(ticker_cols) or "NONE",
        "detected_date_columns": ";".join(date_cols) or "NONE",
        "detected_event_type_columns": ";".join(type_cols) or "NONE",
        "parseable_date_count": str(len(parsed_dates)),
        "min_event_date": min(parsed_dates).isoformat() if parsed_dates else "UNKNOWN",
        "max_event_date": max(parsed_dates).isoformat() if parsed_dates else "UNKNOWN",
        "current_top20_ticker_match_count": str(len(matched_tickers)),
        "current_top20_ticker_match_rate": f"{(len(matched_tickers) / len(top20)):.2f}" if top20 else "0.00",
        "missing_required_columns": ";".join(missing) or "NONE",
        "source_usable": "TRUE" if usable else "FALSE",
        "source_issue_reason": reason,
    }
    return normalized, audit


def ensure_seed_files(root: Path, top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], asof: str) -> tuple[bool, bool]:
    state = root / "state" / "v18"
    template = state / "V18_47C_TOP20_EVENT_EARNINGS_SEED_TEMPLATE.csv"
    seed = state / "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv"
    template_written = False
    seed_written = False
    if not template.exists():
        write_csv(template, [], SEED_COLUMNS)
        template_written = True
    if not seed.exists():
        rows = []
        for candidate in top20:
            ticker = normalize_ticker(candidate.get("ticker"))
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": clean(candidate.get("company_name") or candidate.get("company")),
                    "rank": clean(candidate.get("rank")),
                    "tracking_tier": clean(tracker.get(ticker, {}).get("tracking_tier")),
                    "manual_next_earnings_date": "",
                    "manual_event_date": "",
                    "manual_event_type": "",
                    "manual_event_risk_level": "UNKNOWN_REVIEW",
                    "manual_event_reason": "",
                    "source_note": "Fill local earnings/event date manually; set active TRUE after review.",
                    "last_reviewed_date": asof,
                    "active": "FALSE",
                }
            )
        write_csv(seed, rows, SEED_COLUMNS)
        seed_written = True
    return template_written, seed_written


def diagnostics(top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], normalized: list[dict[str, str]], asof: date) -> list[dict[str, str]]:
    by_ticker = defaultdict(list)
    seed_blank_by_ticker = defaultdict(list)
    macro_rows = []
    for row in normalized:
        if Path(row["source_path"]).name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv" and row["normalized_ticker"] and row["normalized_ticker"] != "ALL":
            seed_blank_by_ticker[row["normalized_ticker"]].append(row)
        if row["parse_status"] != "OK":
            continue
        if row["normalized_event_type"] == "MACRO":
            macro_rows.append(row)
        ticker = row["normalized_ticker"]
        if ticker and ticker != "ALL":
            by_ticker[ticker].append(row)
    macro_future = sorted([row for row in macro_rows if parse_date(row["normalized_event_date"])[0] and parse_date(row["normalized_event_date"])[0] >= asof], key=lambda row: row["normalized_event_date"])
    diag_rows = []
    for candidate in top20:
        ticker = normalize_ticker(candidate.get("ticker"))
        events = by_ticker.get(ticker, [])
        earnings = [row for row in events if row["normalized_event_type"] == "EARNINGS"]
        manual = [row for row in events if row["normalized_event_type"] == "MANUAL"]
        seed = [row for row in events if Path(row["source_path"]).name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv"]
        seed_row_present = bool(seed or seed_blank_by_ticker.get(ticker))
        future_e = sorted([row for row in earnings if parse_date(row["normalized_event_date"])[0] and parse_date(row["normalized_event_date"])[0] >= asof], key=lambda row: row["normalized_event_date"])
        past_e = sorted([row for row in earnings if parse_date(row["normalized_event_date"])[0] and parse_date(row["normalized_event_date"])[0] < asof], key=lambda row: row["normalized_event_date"], reverse=True)
        nearest_macro = macro_future[0] if macro_future else None
        if future_e:
            match_status = "MATCHED_SEED" if Path(future_e[0]["source_path"]).name.endswith("SEED.csv") else "MATCHED_EARNINGS"
            unknown_reason = "NONE"
            fix = "NONE"
        elif manual:
            match_status = "MATCHED_MANUAL"
            unknown_reason = "NONE"
            fix = "NONE"
        elif seed:
            match_status = "MATCHED_SEED"
            unknown_reason = "NONE"
            fix = "NONE"
        elif seed_row_present:
            match_status = "UNKNOWN_REVIEW_REQUIRED"
            unknown_reason = "MANUAL_SEED_BLANK"
            fix = "ADD_MANUAL_EARNINGS_DATE_TO_SEED"
        elif nearest_macro:
            match_status = "MATCHED_MACRO_ONLY"
            unknown_reason = "ONLY_MACRO_AVAILABLE_NO_TICKER_EARNINGS"
            fix = "ADD_MANUAL_EARNINGS_DATE_TO_SEED"
        else:
            match_status = "NO_TICKER_MATCH"
            unknown_reason = "NO_EARNINGS_ROW_FOR_TICKER"
            fix = "ADD_MANUAL_EARNINGS_DATE_TO_SEED"
        if not events and not nearest_macro:
            fix = "CHECK_TICKER_ALIAS"
        best = future_e[0] if future_e else None
        past = past_e[0] if past_e else None
        best_dt = parse_date(best["normalized_event_date"])[0] if best else None
        past_dt = parse_date(past["normalized_event_date"])[0] if past else None
        macro_dt = parse_date(nearest_macro["normalized_event_date"])[0] if nearest_macro else None
        diag_rows.append(
            {
                "snapshot_date": asof.isoformat(),
                "ticker": ticker,
                "rank": clean(candidate.get("rank")),
                "tracking_tier": clean(tracker.get(ticker, {}).get("tracking_tier")),
                "matched_any_event_source": "TRUE" if events or nearest_macro else "FALSE",
                "matched_earnings_source": "TRUE" if earnings else "FALSE",
                "matched_macro_source": "TRUE" if nearest_macro else "FALSE",
                "matched_manual_source": "TRUE" if manual else "FALSE",
                "matched_seed_source": "TRUE" if seed else "FALSE",
                "best_next_earnings_date": best_dt.isoformat() if best_dt else "UNKNOWN",
                "best_next_earnings_source": best["source_path"] if best else "UNKNOWN",
                "days_to_best_next_earnings": str(business_days(asof, best_dt)) if best_dt else "UNKNOWN",
                "latest_past_earnings_date": past_dt.isoformat() if past_dt else "UNKNOWN",
                "latest_past_earnings_source": past["source_path"] if past else "UNKNOWN",
                "days_since_latest_past_earnings": str(business_days(past_dt, asof)) if past_dt else "UNKNOWN",
                "nearest_macro_event_date": macro_dt.isoformat() if macro_dt else "UNKNOWN",
                "nearest_macro_event_type": nearest_macro["original_event_type"] if nearest_macro else "UNKNOWN",
                "days_to_nearest_macro_event": str(business_days(asof, macro_dt)) if macro_dt else "UNKNOWN",
                "manual_override_found": "TRUE" if manual else "FALSE",
                "seed_row_found": "TRUE" if seed_row_present else "FALSE",
                "match_status": match_status,
                "unknown_reason": unknown_reason,
                "recommended_fix": fix,
            }
        )
    return diag_rows


def read_unknown_before(root: Path) -> int:
    read_first = root / "outputs" / "v18" / "ops" / "V18_47C_READ_FIRST.txt"
    if read_first.exists():
        for line in read_first.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("UNKNOWN_REVIEW_COUNT:"):
                return parse_int(line.split(":", 1)[1])
    rows = read_csv(root / "outputs" / "v18" / "event_risk" / "V18_47C_TOP20_EVENT_EARNINGS_RISK.csv")
    return sum(1 for row in rows if clean(row.get("final_event_risk_level")) == "UNKNOWN_REVIEW")


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_report(top20_source: str, tracker_source: str, audit: list[dict[str, str]], diag: list[dict[str, str]], before: int, after: int, seed_path: Path) -> str:
    usable = [row for row in audit if row["source_usable"] == "TRUE"]
    matched = [row for row in audit if parse_int(row["current_top20_ticker_match_count"]) > 0]
    unknown = [row for row in diag if row["match_status"] not in {"MATCHED_EARNINGS", "MATCHED_MANUAL", "MATCHED_SEED"}]
    next_step = "V18.48A Top20 Options Data Collector" if after <= 5 else "fill manual seed file, rerun V18.47C-R1, then rerun V18.47C"
    sections = [
        f"# {PATCH_VERSION} Event Source Coverage Repair Report",
        "",
        "V18.47C-R1 is a local-only coverage audit and seed repair layer. It does not predict event outcomes and does not change official ranking, factor weights, candidate scoring, Top20 selection, freshness eligibility, trading execution, broker/order behavior, or signal freeze ledgers.",
        "",
        "## Sources",
        markdown_table([
            {"metric": "CURRENT_TOP20_SOURCE", "value": top20_source},
            {"metric": "V18_47B_TRACKER_SOURCE", "value": tracker_source},
            {"metric": "USABLE_EVENT_SOURCE_COUNT", "value": str(len(usable))},
            {"metric": "EVENT_SOURCES_WITH_TOP20_MATCHES", "value": str(len(matched))},
            {"metric": "UNKNOWN_BEFORE", "value": str(before)},
            {"metric": "UNKNOWN_AFTER", "value": str(after)},
        ], ["metric", "value"]),
        "",
        "## Event Source Audit",
        markdown_table(audit, ["source_path", "source_exists", "row_count", "parseable_date_count", "current_top20_ticker_match_count", "source_usable", "source_issue_reason"]),
        "",
        "## Why UNKNOWN_REVIEW Was High",
        "The available local earnings calendars cover only a small subset of current Top20 tickers. Macro data is market-wide and cannot replace ticker-level earnings coverage. Blank or missing manual seed rows keep tickers in UNKNOWN_REVIEW by design.",
        "",
        "## Remaining UNKNOWN_REVIEW Fixes",
        markdown_table(unknown, ["ticker", "rank", "match_status", "unknown_reason", "recommended_fix"]),
        "",
        "## Manual Seed File",
        f"Fill `{seed_path}` with reviewed local earnings/event dates, set `active` to TRUE for reviewed rows, rerun V18.47C-R1, then rerun V18.47C.",
        "",
        "## Suggested Next Step",
        next_step + ".",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(path: Path, status: str, values: dict[str, str]) -> None:
    ordered = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "CURRENT_TOP20_SOURCE_FOUND", "CURRENT_TOP20_SOURCE_PATH",
        "TOP20_PRIORITY_TRACKER_FOUND", "TOP20_PRIORITY_TRACKER_PATH", "EVENT_SOURCE_COUNT_FOUND",
        "EVENT_SOURCE_COUNT_USABLE", "EVENT_SOURCE_COUNT_WITH_TOP20_MATCHES", "TOP20_TOTAL_COUNT",
        "TOP20_MATCHED_EARNINGS_COUNT", "TOP20_MATCHED_MANUAL_OR_SEED_COUNT", "TOP20_UNKNOWN_BEFORE_COUNT",
        "TOP20_UNKNOWN_AFTER_COUNT", "UNKNOWN_REDUCTION_COUNT", "MANUAL_SEED_TEMPLATE_WRITTEN",
        "MANUAL_SEED_FILE_WRITTEN", "CURRENT_ALIAS_UPDATED", "OFFICIAL_RANKING_CHANGED",
        "FACTOR_WEIGHTS_CHANGED", "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL",
        "BROKER_API_USED", "ORDER_EXECUTION_USED", "COVERAGE_AUDIT_PATH", "MATCH_DIAGNOSTICS_PATH",
        "NORMALIZED_EVENT_ROWS_PATH", "SUMMARY_PATH", "REPORT_PATH", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in ordered) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and repair V18.47C event source coverage.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    asof = datetime.now().astimezone().date()
    top20_source = find_top20_source(root)
    top20 = top20_rows(top20_source)
    tracker_source, tracker = tracker_rows(root)
    template_written, seed_written = ensure_seed_files(root, top20, tracker, asof.isoformat())

    top20_set = {normalize_ticker(row.get("ticker")) for row in top20}
    all_normalized: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []
    for rel in EVENT_SOURCES:
        normalized, audit = normalize_source(root / rel, top20_set)
        all_normalized.extend(normalized)
        audit_rows.append(audit)

    diag_rows = diagnostics(top20, tracker, all_normalized, asof)
    unknown_before = read_unknown_before(root)
    matched_earnings = sum(1 for row in diag_rows if row["matched_earnings_source"] == "TRUE")
    matched_manual_seed = sum(1 for row in diag_rows if row["matched_manual_source"] == "TRUE" or row["matched_seed_source"] == "TRUE")
    unknown_after = sum(1 for row in diag_rows if row["match_status"] not in {"MATCHED_EARNINGS", "MATCHED_MANUAL", "MATCHED_SEED"})
    reduction = max(0, unknown_before - unknown_after)

    out_dir = root / "outputs" / "v18" / "event_risk"
    audit_path = out_dir / "V18_47C_R1_EVENT_SOURCE_COVERAGE_AUDIT.csv"
    diag_path = out_dir / "V18_47C_R1_TOP20_EVENT_MATCH_DIAGNOSTICS.csv"
    normalized_path = out_dir / "V18_47C_R1_NORMALIZED_EVENT_SOURCE_ROWS.csv"
    summary_path = out_dir / "V18_47C_R1_EVENT_SOURCE_COVERAGE_SUMMARY.csv"
    report_path = root / "outputs" / "v18" / "read_center" / "V18_47C_R1_EVENT_SOURCE_COVERAGE_REPAIR_REPORT.md"
    read_first_path = root / "outputs" / "v18" / "ops" / "V18_47C_R1_READ_FIRST.txt"
    seed_path = root / "state" / "v18" / "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv"

    write_csv(audit_path, audit_rows, AUDIT_COLUMNS)
    write_csv(diag_path, diag_rows, DIAG_COLUMNS)
    write_csv(normalized_path, all_normalized, NORMALIZED_COLUMNS)
    usable_count = sum(1 for row in audit_rows if row["source_usable"] == "TRUE")
    match_source_count = sum(1 for row in audit_rows if parse_int(row["current_top20_ticker_match_count"]) > 0)
    summary_rows = [
        {"summary_type": "COUNT", "summary_key": "TOP20_TOTAL_COUNT", "summary_value": str(len(top20))},
        {"summary_type": "COUNT", "summary_key": "TOP20_MATCHED_EARNINGS_COUNT", "summary_value": str(matched_earnings)},
        {"summary_type": "COUNT", "summary_key": "TOP20_MATCHED_MANUAL_OR_SEED_COUNT", "summary_value": str(matched_manual_seed)},
        {"summary_type": "COUNT", "summary_key": "TOP20_UNKNOWN_BEFORE_COUNT", "summary_value": str(unknown_before)},
        {"summary_type": "COUNT", "summary_key": "TOP20_UNKNOWN_AFTER_COUNT", "summary_value": str(unknown_after)},
        {"summary_type": "COUNT", "summary_key": "UNKNOWN_REDUCTION_COUNT", "summary_value": str(reduction)},
        {"summary_type": "SAFETY", "summary_key": "OFFICIAL_RANKING_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "FACTOR_WEIGHTS_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "TRADING_EXECUTION_ALLOWED", "summary_value": "FALSE"},
    ]
    write_csv(summary_path, summary_rows, ["summary_type", "summary_key", "summary_value"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(str(top20_source) if top20_source else "NONE", str(tracker_source) if tracker_source else "NONE", audit_rows, diag_rows, unknown_before, unknown_after, seed_path), encoding="utf-8")

    current_alias_updated = "FALSE"
    if args.write_current and reduction > 0:
        current_alias_updated = "FALSE"

    if usable_count == 0:
        status = "WARN_V18_47C_R1_NO_USABLE_EVENT_SOURCES"
    elif unknown_after > 10:
        status = "WARN_V18_47C_R1_EVENT_COVERAGE_STILL_WEAK"
    else:
        status = "PASS"

    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "CURRENT_TOP20_SOURCE_FOUND": "TRUE" if top20_source else "FALSE",
        "CURRENT_TOP20_SOURCE_PATH": str(top20_source) if top20_source else "NONE",
        "TOP20_PRIORITY_TRACKER_FOUND": "TRUE" if tracker_source else "FALSE",
        "TOP20_PRIORITY_TRACKER_PATH": str(tracker_source) if tracker_source else "NONE",
        "EVENT_SOURCE_COUNT_FOUND": str(sum(1 for row in audit_rows if row["source_exists"] == "TRUE")),
        "EVENT_SOURCE_COUNT_USABLE": str(usable_count),
        "EVENT_SOURCE_COUNT_WITH_TOP20_MATCHES": str(match_source_count),
        "TOP20_TOTAL_COUNT": str(len(top20)),
        "TOP20_MATCHED_EARNINGS_COUNT": str(matched_earnings),
        "TOP20_MATCHED_MANUAL_OR_SEED_COUNT": str(matched_manual_seed),
        "TOP20_UNKNOWN_BEFORE_COUNT": str(unknown_before),
        "TOP20_UNKNOWN_AFTER_COUNT": str(unknown_after),
        "UNKNOWN_REDUCTION_COUNT": str(reduction),
        "MANUAL_SEED_TEMPLATE_WRITTEN": "TRUE" if template_written else "FALSE",
        "MANUAL_SEED_FILE_WRITTEN": "TRUE" if seed_written else "FALSE",
        "CURRENT_ALIAS_UPDATED": current_alias_updated,
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "COVERAGE_AUDIT_PATH": str(audit_path),
        "MATCH_DIAGNOSTICS_PATH": str(diag_path),
        "NORMALIZED_EVENT_ROWS_PATH": str(normalized_path),
        "SUMMARY_PATH": str(summary_path),
        "REPORT_PATH": str(report_path),
        "VALIDATION_NOTES": "READ_ONLY_EVENT_SOURCE_COVERAGE_REPAIR_NO_RANKING_WEIGHT_TRADING_OR_BROKER_CHANGES",
    }
    write_read_first(read_first_path, status, values)
    print(f"STATUS: {status}")
    print(f"TOP20_UNKNOWN_BEFORE_COUNT: {unknown_before}")
    print(f"TOP20_UNKNOWN_AFTER_COUNT: {unknown_after}")
    print(f"UNKNOWN_REDUCTION_COUNT: {reduction}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
