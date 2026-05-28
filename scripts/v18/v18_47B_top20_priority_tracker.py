from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import mean


PATCH_VERSION = "V18.47B"
PATCH_NAME = "Top20 Priority Tracker"

SNAPSHOT_COLUMNS = [
    "snapshot_date",
    "snapshot_timestamp",
    "source_path",
    "ticker",
    "rank",
    "base_score",
    "composite_candidate_score",
    "latest_price_date",
    "technical_status",
    "pullback_status",
    "final_action",
    "freshness_status",
    "actionable_allowed_by_freshness",
    "source_row_hash",
]

TRACKER_COLUMNS = [
    "ticker",
    "latest_rank",
    "latest_snapshot_date",
    "latest_base_score",
    "latest_composite_candidate_score",
    "top20_entry_count_20d",
    "top20_entry_count_60d",
    "top20_entry_count_120d",
    "consecutive_top20_days",
    "avg_rank_20d",
    "avg_rank_60d",
    "best_rank_60d",
    "worst_rank_60d",
    "first_seen_top20_date",
    "last_seen_top20_date",
    "days_since_last_top20",
    "tracking_tier",
    "tracking_tier_reason",
    "event_tracking_priority",
    "options_tracking_priority",
    "manual_review_priority",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def clean(value: object, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def parse_int(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def parse_float(value: object) -> float | None:
    try:
        text = str(value).strip()
        if not text or text == "UNKNOWN":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_date(value: object) -> date | None:
    text = str(value).strip()
    if not text or text == "UNKNOWN":
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def find_current_source(root: Path) -> tuple[Path | None, str]:
    candidates = [
        root / "outputs" / "v18" / "ranked_candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "read_center" / "V18_CURRENT_TOP_RANKED_CANDIDATES.md",
        root / "outputs" / "v18" / "read_center" / "daily_packet" / "V18_CURRENT_TOP_RANKED_CANDIDATES.md",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate, "FOUND_CURRENT_TOP20_SOURCE"
    return None, "WARN_V18_47B_NO_CURRENT_TOP20_SOURCE"


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def read_markdown_table(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    table_lines = [line for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(table_lines) < 2:
        return rows
    header = [normalize_key(cell) for cell in table_lines[0].strip("|").split("|")]
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        if row.get("ticker") or row.get("symbol"):
            rows.append(row)
    return rows


def source_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".csv":
        rows = read_csv_rows(path)
    elif path.suffix.lower() == ".md":
        rows = read_markdown_table(path)
    else:
        rows = []
    rows = [row for row in rows if clean(row.get("ticker") or row.get("symbol"), "") != ""]
    rows.sort(key=lambda row: parse_int(row.get("rank") or row.get("freshness_eligible_rank") or row.get("original_full_rank"), 999999))
    return rows[:20]


def row_hash(row: dict[str, str]) -> str:
    payload = "|".join(f"{key}={clean(row.get(key), '')}" for key in sorted(row))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_snapshot(rows: list[dict[str, str]], source_path: Path, snapshot_date: str, timestamp: str) -> list[dict[str, str]]:
    snapshot: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        rank = clean(row.get("rank") or row.get("freshness_eligible_rank") or row.get("original_full_rank") or index)
        snapshot.append(
            {
                "snapshot_date": snapshot_date,
                "snapshot_timestamp": timestamp,
                "source_path": str(source_path),
                "ticker": clean(row.get("ticker") or row.get("symbol")),
                "rank": rank,
                "base_score": clean(row.get("base_score")),
                "composite_candidate_score": clean(row.get("composite_candidate_score") or row.get("score")),
                "latest_price_date": clean(row.get("latest_price_date")),
                "technical_status": clean(row.get("technical_status")),
                "pullback_status": clean(row.get("pullback_status")),
                "final_action": clean(row.get("final_action")),
                "freshness_status": clean(row.get("freshness_status")),
                "actionable_allowed_by_freshness": clean(row.get("actionable_allowed_by_freshness")),
                "source_row_hash": row_hash(row),
            }
        )
    return snapshot


def merge_history(history_path: Path, snapshot_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    if history_path.exists():
        history = read_csv_rows(history_path)
    snapshot_dates = {clean(row.get("snapshot_date"), "") for row in snapshot_rows}
    if snapshot_dates:
        history = [row for row in history if clean(row.get("snapshot_date"), "") not in snapshot_dates]
    merged: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in history + snapshot_rows:
        key = (clean(row.get("snapshot_date"), ""), clean(row.get("ticker"), ""), clean(row.get("rank"), ""))
        if all(key):
            merged[key] = {column: clean(row.get(column)) for column in SNAPSHOT_COLUMNS}
    rows = list(merged.values())
    rows.sort(key=lambda row: (row["snapshot_date"], parse_int(row["rank"], 999999), row["ticker"]))
    return rows


def count_in_window(rows: list[dict[str, str]], asof: date, days: int) -> int:
    start_ord = asof.toordinal() - days + 1
    seen_dates = {
        parsed
        for parsed in (parse_date(row.get("snapshot_date")) for row in rows)
        if parsed and start_ord <= parsed.toordinal() <= asof.toordinal()
    }
    return len(seen_dates)


def rank_values_in_window(rows: list[dict[str, str]], asof: date, days: int) -> list[int]:
    start_ord = asof.toordinal() - days + 1
    values: list[int] = []
    for row in rows:
        parsed = parse_date(row.get("snapshot_date"))
        if parsed and start_ord <= parsed.toordinal() <= asof.toordinal():
            values.append(parse_int(row.get("rank"), 0))
    return [value for value in values if value > 0]


def consecutive_days(rows: list[dict[str, str]], asof: date) -> int:
    seen = {
        parsed
        for parsed in (parse_date(row.get("snapshot_date")) for row in rows)
        if parsed
    }
    count = 0
    cursor = asof
    while cursor in seen:
        count += 1
        cursor = date.fromordinal(cursor.toordinal() - 1)
    return count


def format_float(value: float | None) -> str:
    if value is None:
        return "UNKNOWN"
    return f"{value:.2f}"


def tier_for(latest_rank: int | None, is_current: bool, count20: int, count60: int, consecutive: int) -> tuple[str, str]:
    if consecutive >= 3:
        return "TIER_1_CORE", "CONSECUTIVE_TOP20_DAYS_GE_3"
    if count60 >= 8:
        return "TIER_1_CORE", "TOP20_ENTRY_COUNT_60D_GE_8"
    if latest_rank is not None and latest_rank <= 5 and count20 >= 2:
        return "TIER_1_CORE", "LATEST_RANK_LE_5_AND_20D_COUNT_GE_2"
    if 3 <= count60 <= 7:
        return "TIER_2_IMPORTANT", "TOP20_ENTRY_COUNT_60D_BETWEEN_3_AND_7"
    if latest_rank is not None and latest_rank <= 10 and is_current:
        return "TIER_2_IMPORTANT", "CURRENT_LATEST_RANK_LE_10"
    if 1 <= count60 <= 2:
        return "TIER_3_OCCASIONAL", "TOP20_ENTRY_COUNT_60D_BETWEEN_1_AND_2"
    if is_current:
        return "TIER_3_OCCASIONAL", "CURRENT_TOP20_MINIMUM_TIER"
    return "TIER_4_CACHE_ONLY", "NO_CURRENT_TOP20_ENTRY_AND_LOW_HISTORICAL_FREQUENCY"


def priority_fields(tier: str, latest_rank: int | None) -> tuple[str, str, str]:
    event_map = {
        "TIER_1_CORE": "HIGH",
        "TIER_2_IMPORTANT": "MEDIUM",
        "TIER_3_OCCASIONAL": "LOW",
        "TIER_4_CACHE_ONLY": "CACHE_ONLY",
    }
    options_map = {
        "TIER_1_CORE": "HIGH",
        "TIER_2_IMPORTANT": "MEDIUM",
        "TIER_3_OCCASIONAL": "LOW",
        "TIER_4_CACHE_ONLY": "NONE",
    }
    if tier == "TIER_1_CORE" or (latest_rank is not None and latest_rank <= 5):
        manual = "HIGH"
    elif tier == "TIER_2_IMPORTANT" or (latest_rank is not None and latest_rank <= 10):
        manual = "MEDIUM"
    else:
        manual = "LOW"
    return event_map[tier], options_map[tier], manual


def build_tracker(history_rows: list[dict[str, str]], snapshot_date_text: str) -> list[dict[str, str]]:
    asof = parse_date(snapshot_date_text) or date.today()
    by_ticker: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in history_rows:
        ticker = clean(row.get("ticker"), "")
        if ticker:
            by_ticker[ticker].append(row)

    tracker: list[dict[str, str]] = []
    for ticker, rows in by_ticker.items():
        rows.sort(key=lambda row: (clean(row.get("snapshot_date"), ""), parse_int(row.get("rank"), 999999)))
        dated_rows = [(parse_date(row.get("snapshot_date")), row) for row in rows]
        dated_rows = [(dt, row) for dt, row in dated_rows if dt]
        if not dated_rows:
            continue
        latest_date = max(dt for dt, _ in dated_rows)
        latest_rows = [row for dt, row in dated_rows if dt == latest_date]
        latest_row = sorted(latest_rows, key=lambda row: parse_int(row.get("rank"), 999999))[0]
        latest_rank_value = parse_int(latest_row.get("rank"), 0)
        latest_rank = latest_rank_value if latest_rank_value > 0 else None
        is_current = latest_date == asof
        count20 = count_in_window(rows, asof, 20)
        count60 = count_in_window(rows, asof, 60)
        count120 = count_in_window(rows, asof, 120)
        consecutive = consecutive_days(rows, asof)
        ranks20 = rank_values_in_window(rows, asof, 20)
        ranks60 = rank_values_in_window(rows, asof, 60)
        tier, reason = tier_for(latest_rank, is_current, count20, count60, consecutive)
        event_priority, options_priority, manual_priority = priority_fields(tier, latest_rank)
        first_seen = min(dt for dt, _ in dated_rows)
        last_seen = max(dt for dt, _ in dated_rows)
        tracker.append(
            {
                "ticker": ticker,
                "latest_rank": str(latest_rank) if latest_rank is not None else "UNKNOWN",
                "latest_snapshot_date": latest_date.isoformat(),
                "latest_base_score": clean(latest_row.get("base_score")),
                "latest_composite_candidate_score": clean(latest_row.get("composite_candidate_score")),
                "top20_entry_count_20d": str(count20),
                "top20_entry_count_60d": str(count60),
                "top20_entry_count_120d": str(count120),
                "consecutive_top20_days": str(consecutive),
                "avg_rank_20d": format_float(mean(ranks20) if ranks20 else None),
                "avg_rank_60d": format_float(mean(ranks60) if ranks60 else None),
                "best_rank_60d": str(min(ranks60)) if ranks60 else "UNKNOWN",
                "worst_rank_60d": str(max(ranks60)) if ranks60 else "UNKNOWN",
                "first_seen_top20_date": first_seen.isoformat(),
                "last_seen_top20_date": last_seen.isoformat(),
                "days_since_last_top20": str(asof.toordinal() - last_seen.toordinal()),
                "tracking_tier": tier,
                "tracking_tier_reason": reason,
                "event_tracking_priority": event_priority,
                "options_tracking_priority": options_priority,
                "manual_review_priority": manual_priority,
            }
        )
    tracker.sort(key=lambda row: (row["tracking_tier"], parse_int(row["latest_rank"], 999999), row["ticker"]))
    return tracker


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
    return "\n".join(lines)


def build_report(source_path: str, snapshot_count: int, tracker_rows: list[dict[str, str]]) -> str:
    counts = Counter(row["tracking_tier"] for row in tracker_rows)
    tier1 = [row for row in tracker_rows if row["tracking_tier"] == "TIER_1_CORE"]
    tier2 = [row for row in tracker_rows if row["tracking_tier"] == "TIER_2_IMPORTANT"]
    event_high = [row for row in tracker_rows if row["event_tracking_priority"] == "HIGH"]
    options_high = [row for row in tracker_rows if row["options_tracking_priority"] == "HIGH"]
    summary_rows = [
        {"metric": "CURRENT_TOP20_SOURCE", "value": source_path},
        {"metric": "CURRENT_TOP20_SNAPSHOT_COUNT", "value": str(snapshot_count)},
        {"metric": "TIER_1_CORE_COUNT", "value": str(counts.get("TIER_1_CORE", 0))},
        {"metric": "TIER_2_IMPORTANT_COUNT", "value": str(counts.get("TIER_2_IMPORTANT", 0))},
        {"metric": "TIER_3_OCCASIONAL_COUNT", "value": str(counts.get("TIER_3_OCCASIONAL", 0))},
        {"metric": "TIER_4_CACHE_ONLY_COUNT", "value": str(counts.get("TIER_4_CACHE_ONLY", 0))},
    ]
    sections = [
        f"# {PATCH_VERSION} Top20 Priority Tracker Report",
        "",
        "V18.47B is a read-only Top20 tracking layer. It does not change official ranking logic, factor weights, candidate scoring, Top20 selection, freshness eligibility, trading execution, broker/order behavior, signal freeze ledgers, or V18.47A governance outputs.",
        "",
        "## Current source and counts",
        markdown_table(summary_rows, ["metric", "value"]),
        "",
        "## TIER_1_CORE tickers",
        markdown_table(tier1, ["ticker", "latest_rank", "top20_entry_count_60d", "consecutive_top20_days", "tracking_tier_reason"]),
        "",
        "## TIER_2_IMPORTANT tickers",
        markdown_table(tier2, ["ticker", "latest_rank", "top20_entry_count_60d", "tracking_tier_reason"]),
        "",
        "## High-priority event tracking tickers",
        markdown_table(event_high, ["ticker", "latest_rank", "tracking_tier", "event_tracking_priority"]),
        "",
        "## High-priority options tracking tickers",
        markdown_table(options_high, ["ticker", "latest_rank", "tracking_tier", "options_tracking_priority"]),
        "",
        "## Safety statement",
        "OFFICIAL_RANKING_CHANGED is FALSE and FACTOR_WEIGHTS_CHANGED is FALSE. V18.47B only records Top20 history and computes tracking tiers.",
        "",
        "## Suggested next step",
        "V18.47C Top20 Event / Earnings Risk Layer.",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(
    path: Path,
    status: str,
    source_found: bool,
    source_path: str,
    snapshot_count: int,
    history_count: int,
    tracker_rows: list[dict[str, str]],
    current_alias_written: bool,
    snapshot_path: Path,
    history_path: Path,
    tracker_path: Path,
    current_report_path: Path,
    validation_notes: str,
) -> None:
    counts = Counter(row["tracking_tier"] for row in tracker_rows)
    lines = [
        f"STATUS: {status}",
        f"PATCH_VERSION: {PATCH_VERSION}",
        f"PATCH_NAME: {PATCH_NAME}",
        f"CURRENT_TOP20_SOURCE_FOUND: {'TRUE' if source_found else 'FALSE'}",
        f"CURRENT_TOP20_SOURCE_PATH: {source_path}",
        f"SNAPSHOT_ROW_COUNT: {snapshot_count}",
        f"HISTORY_ROW_COUNT: {history_count}",
        f"TRACKER_ROW_COUNT: {len(tracker_rows)}",
        f"TIER_1_CORE_COUNT: {counts.get('TIER_1_CORE', 0)}",
        f"TIER_2_IMPORTANT_COUNT: {counts.get('TIER_2_IMPORTANT', 0)}",
        f"TIER_3_OCCASIONAL_COUNT: {counts.get('TIER_3_OCCASIONAL', 0)}",
        f"TIER_4_CACHE_ONLY_COUNT: {counts.get('TIER_4_CACHE_ONLY', 0)}",
        f"CURRENT_ALIAS_WRITTEN: {'TRUE' if current_alias_written else 'FALSE'}",
        "OFFICIAL_RANKING_CHANGED: FALSE",
        "FACTOR_WEIGHTS_CHANGED: FALSE",
        "TRADING_EXECUTION_ALLOWED: FALSE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
        f"SNAPSHOT_PATH: {snapshot_path}",
        f"HISTORY_PATH: {history_path}",
        f"TRACKER_PATH: {tracker_path}",
        f"CURRENT_REPORT_PATH: {current_report_path}",
        f"VALIDATION_NOTES: {validation_notes}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V18.47B Top20 priority tracker.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tracking_dir = root / "outputs" / "v18" / "tracking"
    read_center_dir = root / "outputs" / "v18" / "read_center"
    ops_dir = root / "outputs" / "v18" / "ops"
    snapshot_path = tracking_dir / "V18_47B_TOP20_PRIORITY_SNAPSHOT.csv"
    history_path = tracking_dir / "V18_47B_TOP20_PRIORITY_HISTORY.csv"
    tracker_path = tracking_dir / "V18_47B_TOP20_PRIORITY_TRACKER.csv"
    summary_path = tracking_dir / "V18_47B_TOP20_PRIORITY_SUMMARY.csv"
    report_path = read_center_dir / "V18_47B_TOP20_PRIORITY_TRACKER_REPORT.md"
    current_report_path = read_center_dir / "V18_CURRENT_TOP20_PRIORITY_TRACKER.md"
    read_first_path = ops_dir / "V18_47B_READ_FIRST.txt"

    source_path, status = find_current_source(root)
    now = datetime.now().astimezone()
    snapshot_date_text = now.date().isoformat()
    timestamp = now.isoformat(timespec="seconds")

    if source_path is None:
        existing_history = read_csv_rows(history_path) if history_path.exists() else []
        tracker_rows = build_tracker(existing_history, snapshot_date_text) if existing_history else []
        if tracker_rows:
            write_csv(tracker_path, tracker_rows, TRACKER_COLUMNS)
        write_read_first(
            read_first_path,
            status,
            False,
            "NONE",
            0,
            len(existing_history),
            tracker_rows,
            False,
            snapshot_path,
            history_path,
            tracker_path,
            current_report_path,
            "NO_CURRENT_TOP20_SOURCE_FOUND_NO_CURRENT_ALIAS_WRITTEN",
        )
        print(f"STATUS: {status}")
        print("CURRENT_TOP20_SOURCE_FOUND: FALSE")
        return 0

    rows = source_rows(source_path)
    if not rows:
        write_read_first(
            read_first_path,
            "WARN_V18_47B_NO_USABLE_TOP20_ROWS",
            True,
            str(source_path),
            0,
            0,
            [],
            False,
            snapshot_path,
            history_path,
            tracker_path,
            current_report_path,
            "CURRENT_TOP20_SOURCE_FOUND_BUT_NO_USABLE_ROWS_NO_CURRENT_ALIAS_WRITTEN",
        )
        print("STATUS: WARN_V18_47B_NO_USABLE_TOP20_ROWS")
        return 0

    snapshot_rows = build_snapshot(rows, source_path, snapshot_date_text, timestamp)
    history_rows = merge_history(history_path, snapshot_rows)
    tracker_rows = build_tracker(history_rows, snapshot_date_text)
    tier_counts = Counter(row["tracking_tier"] for row in tracker_rows)
    summary_rows = [
        {"summary_type": "SOURCE", "summary_key": "CURRENT_TOP20_SOURCE_PATH", "summary_value": str(source_path)},
        {"summary_type": "COUNT", "summary_key": "SNAPSHOT_ROW_COUNT", "summary_value": str(len(snapshot_rows))},
        {"summary_type": "COUNT", "summary_key": "HISTORY_ROW_COUNT", "summary_value": str(len(history_rows))},
        {"summary_type": "COUNT", "summary_key": "TRACKER_ROW_COUNT", "summary_value": str(len(tracker_rows))},
    ] + [
        {"summary_type": "TIER", "summary_key": key, "summary_value": str(value)}
        for key, value in sorted(tier_counts.items())
    ] + [
        {"summary_type": "SAFETY", "summary_key": "OFFICIAL_RANKING_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "FACTOR_WEIGHTS_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "TRADING_EXECUTION_ALLOWED", "summary_value": "FALSE"},
    ]

    write_csv(snapshot_path, snapshot_rows, SNAPSHOT_COLUMNS)
    write_csv(history_path, history_rows, SNAPSHOT_COLUMNS)
    write_csv(tracker_path, tracker_rows, TRACKER_COLUMNS)
    write_csv(summary_path, summary_rows, ["summary_type", "summary_key", "summary_value"])
    report = build_report(str(source_path), len(snapshot_rows), tracker_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_alias_written = False
    if args.write_current:
        current_report_path.write_text(report, encoding="utf-8")
        current_alias_written = True

    write_read_first(
        read_first_path,
        "PASS",
        True,
        str(source_path),
        len(snapshot_rows),
        len(history_rows),
        tracker_rows,
        current_alias_written,
        snapshot_path,
        history_path,
        tracker_path,
        current_report_path,
        "READ_ONLY_TOP20_PRIORITY_TRACKER_NO_RANKING_WEIGHT_TRADING_OR_BROKER_CHANGES",
    )
    print("STATUS: PASS")
    print(f"SNAPSHOT_ROW_COUNT: {len(snapshot_rows)}")
    print(f"HISTORY_ROW_COUNT: {len(history_rows)}")
    print(f"TRACKER_ROW_COUNT: {len(tracker_rows)}")
    print(f"CURRENT_ALIAS_WRITTEN: {'TRUE' if current_alias_written else 'FALSE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
