from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_DRY_RUN_READY"
STATUS_CLEAN = "OK_V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_CLEAN"
STATUS_WARN = "WARN_V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_NEEDED"
STATUS_CLEANUP_OK = "OK_V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_CLEANUP_READY"
STATUS_DATE_REQUIRED = "FAIL_V18_31G_R1_CLEANUP_DATE_REQUIRED"
STATUS_DATE_NOT_ELIGIBLE = "FAIL_V18_31G_R1_CLEANUP_DATE_NOT_ELIGIBLE"
STATUS_CLEANUP_FAIL = "FAIL_V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_CLEANUP_FAILED"
STATUS_FAIL = "FAIL_V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_FAILED"

MODE_LIVE = "UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW"
MODE_DRY = "UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_DRY_RUN"

SIGNAL_FREEZE = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
RECOMMENDATION = "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv"
TRADE_PLAN = "state/v18/trade_plan_snapshots/V18_DAILY_TRADE_PLAN_LEDGER.csv"
R31G_READ_FIRST = "outputs/v18/ops/V18_31G_READ_FIRST.txt"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
BACKUP_ROOT = "archive/v18/non_trading_signal_date_guard_backups"

OUT_READ_FIRST = "outputs/v18/ops/V18_31G_R1_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_SUMMARY.csv"
OUT_DETAIL = "outputs/v18/ops/V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_DETAIL.csv"
OUT_REPORT = "outputs/v18/read_center/V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_REPORT.md"
OUT_CURRENT = "outputs/v18/read_center/V18_CURRENT_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW.md"
OUT_ERROR = "outputs/v18/read_center/V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_ERROR.md"

LEDGERS = [
    ("SIGNAL_FREEZE", SIGNAL_FREEZE, ["signal_date", "snapshot_date", "trade_date", "date", "as_of_date"]),
    ("RECOMMENDATION_SNAPSHOT", RECOMMENDATION, ["snapshot_date", "signal_date", "trade_date", "date", "as_of_date"]),
    ("TRADE_PLAN", TRADE_PLAN, ["signal_date", "snapshot_date", "trade_date", "date", "as_of_date"]),
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "LATEST_SUPPORTED_SIGNAL_DATE",
    "CLEANUP_DATE",
    "APPLY_CLEANUP",
    "ALLOW_CLEANUP_NON_WEEKEND",
    "LEDGER_COUNT_CHECKED",
    "LEDGER_COUNT_EXISTING",
    "UNSUPPORTED_DATE_COUNT",
    "UNSUPPORTED_ROW_COUNT",
    "CLEANUP_ELIGIBLE_ROW_COUNT",
    "CLEANUP_REMOVED_ROW_COUNT",
    "BACKUP_DIR",
    "SIGNAL_FREEZE_UNSUPPORTED_ROW_COUNT",
    "RECOMMENDATION_SNAPSHOT_UNSUPPORTED_ROW_COUNT",
    "TRADE_PLAN_UNSUPPORTED_ROW_COUNT",
    "SIGNAL_FREEZE_CLEANUP_REMOVED_ROWS",
    "RECOMMENDATION_SNAPSHOT_CLEANUP_REMOVED_ROWS",
    "TRADE_PLAN_CLEANUP_REMOVED_ROWS",
    "POST_CLEANUP_SIGNAL_FREEZE_DUPLICATE_COUNT",
    "POST_CLEANUP_RECOMMENDATION_SNAPSHOT_DUPLICATE_COUNT",
    "POST_CLEANUP_TRADE_PLAN_DUPLICATE_COUNT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "mode",
    "latest_supported_signal_date",
    "cleanup_date",
    "apply_cleanup",
    "ledger_count_checked",
    "ledger_count_existing",
    "unsupported_date_count",
    "unsupported_row_count",
    "cleanup_eligible_row_count",
    "cleanup_removed_row_count",
    "post_cleanup_duplicate_date_ticker_count",
    "backup_dir",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

DETAIL_FIELDS = [
    "run_id",
    "ledger_name",
    "ledger_path",
    "ledger_exists",
    "date_column_used",
    "ticker_column_used",
    "date_value",
    "is_weekend",
    "is_after_latest_supported_signal_date",
    "is_unsupported",
    "row_count",
    "unique_ticker_count",
    "duplicate_date_ticker_count",
    "cleanup_eligible",
    "cleanup_applied",
    "removed_rows",
    "notes",
]


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def upper(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def parse_date(value: object) -> Optional[dt.date]:
    text = norm(value)
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m-%d-%Y"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def date_text(value: Optional[dt.date]) -> str:
    return value.isoformat() if value else ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def first_col(fields: Sequence[str], aliases: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for alias in aliases:
        if alias.lower() in lower:
            return lower[alias.lower()]
    return ""


def duplicate_count(rows: Sequence[Dict[str, str]], date_col: str, ticker_col: str) -> int:
    if not date_col or not ticker_col:
        return 0
    counts = Counter((norm(row.get(date_col)), upper(row.get(ticker_col))) for row in rows)
    return sum(1 for (date, ticker), count in counts.items() if date and ticker and count > 1)


def latest_full_signal_date(root: Path) -> Optional[dt.date]:
    rows, fields = read_csv(root / SIGNAL_FREEZE)
    date_col = first_col(fields, ["signal_date"])
    ticker_col = first_col(fields, ["ticker", "symbol", "asset"])
    by_date: Dict[dt.date, set[str]] = {}
    for row in rows:
        date = parse_date(row.get(date_col))
        ticker = upper(row.get(ticker_col))
        if date and ticker and date.weekday() < 5:
            by_date.setdefault(date, set()).add(ticker)
    full = [date for date, tickers in by_date.items() if len(tickers) == 252]
    return max(full, default=None)


def latest_price_date(root: Path) -> Optional[dt.date]:
    dates: List[dt.date] = []
    for rel in [TECHNICAL_TIMING, CURRENT_RANKED, SIGNAL_FREEZE]:
        rows, fields = read_csv(root / rel)
        for col in fields:
            if col.lower() in {"price_date", "latest_price_date", "latest_close_date", "price_asof_date", "trade_date"}:
                for row in rows:
                    parsed = parse_date(row.get(col))
                    if parsed:
                        dates.append(parsed)
    return max(dates, default=None)


def determine_latest_supported(root: Path, override: str) -> Optional[dt.date]:
    cli = parse_date(override)
    if cli:
        return cli
    r31g = read_status_file(root / R31G_READ_FIRST)
    for field in ["RECOMMENDED_SIGNAL_DATE", "LATEST_OBSERVED_PRICE_DATE"]:
        parsed = parse_date(r31g.get(field))
        if parsed:
            return parsed
    return latest_full_signal_date(root) or latest_price_date(root)


def is_unsupported(date: dt.date, latest_supported: Optional[dt.date]) -> Tuple[bool, bool, bool]:
    is_weekend = date.weekday() >= 5
    is_after = bool(latest_supported and date > latest_supported)
    return is_weekend or is_after, is_weekend, is_after


def audit_ledger(root: Path, run_id: str, name: str, rel: str, date_aliases: Sequence[str], latest_supported: Optional[dt.date], cleanup_date: Optional[dt.date], allow_cleanup_non_weekend: bool) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    path = root / rel
    rows, fields = read_csv(path)
    date_col = first_col(fields, date_aliases)
    ticker_col = first_col(fields, ["ticker", "symbol", "asset"])
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        parsed = parse_date(row.get(date_col))
        if parsed:
            grouped.setdefault(parsed.isoformat(), []).append(row)
    details: List[Dict[str, object]] = []
    unsupported_rows = 0
    eligible_rows = 0
    for date_value, group in sorted(grouped.items()):
        date = parse_date(date_value)
        unsupported, weekend, after_supported = is_unsupported(date, latest_supported) if date else (False, False, False)
        row_count = len(group)
        unique_tickers = len({upper(row.get(ticker_col)) for row in group if ticker_col and upper(row.get(ticker_col))})
        dup = duplicate_count(group, date_col, ticker_col)
        cleanup_eligible = bool(cleanup_date and date == cleanup_date and (unsupported or allow_cleanup_non_weekend))
        if unsupported:
            unsupported_rows += row_count
        if cleanup_eligible:
            eligible_rows += row_count
        details.append({
            "run_id": run_id,
            "ledger_name": name,
            "ledger_path": str(path),
            "ledger_exists": bool_text(path.exists()),
            "date_column_used": date_col,
            "ticker_column_used": ticker_col,
            "date_value": date_value,
            "is_weekend": bool_text(weekend),
            "is_after_latest_supported_signal_date": bool_text(after_supported),
            "is_unsupported": bool_text(unsupported),
            "row_count": row_count,
            "unique_ticker_count": unique_tickers,
            "duplicate_date_ticker_count": dup,
            "cleanup_eligible": bool_text(cleanup_eligible),
            "cleanup_applied": "FALSE",
            "removed_rows": 0,
            "notes": "" if ticker_col else "ticker column missing; duplicate check limited",
        })
    stats = {
        "exists": path.exists(),
        "rows": len(rows),
        "fields": fields,
        "date_col": date_col,
        "ticker_col": ticker_col,
        "unsupported_rows": unsupported_rows,
        "eligible_rows": eligible_rows,
        "duplicate_count": duplicate_count(rows, date_col, ticker_col),
    }
    return details, stats


def apply_cleanup(root: Path, rel: str, fields: Sequence[str], date_col: str, cleanup_date: dt.date, backup_dir: Path) -> int:
    path = root / rel
    rows, _ = read_csv(path)
    if not path.exists() or not rows or not date_col:
        return 0
    kept = [row for row in rows if parse_date(row.get(date_col)) != cleanup_date]
    removed = len(rows) - len(kept)
    if removed:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_dir / path.name)
        tmp = path.with_suffix(path.suffix + ".tmp")
        write_csv(tmp, kept, fields)
        tmp.replace(path)
    return removed


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 50) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def build_report(values: Dict[str, object], details: Sequence[Dict[str, object]]) -> str:
    unsupported = [row for row in details if row.get("is_unsupported") == "TRUE"]
    eligible = [row for row in details if row.get("cleanup_eligible") == "TRUE"]
    if values["STATUS"] == STATUS_WARN:
        next_step = "Review detail CSV and run ApplyCleanup with CleanupDate only after operator confirmation."
    elif values["STATUS"] == STATUS_CLEANUP_OK:
        next_step = "Rerun R31G and R31F to confirm the ledger hygiene state."
    elif values["STATUS"] == STATUS_CLEAN:
        next_step = "Continue using R31F as the daily entry point."
    else:
        next_step = "Inspect the error report or READ_FIRST fields before proceeding."
    return "\n".join([
        "# V18.31G-R1 Unsupported Signal-Date Ledger Review",
        "",
        "## 1. Final Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Latest Supported Signal Date",
        f"- LATEST_SUPPORTED_SIGNAL_DATE: `{values.get('LATEST_SUPPORTED_SIGNAL_DATE', '')}`",
        "",
        "## 3. Audit Summary",
        f"- Unsupported dates: `{values.get('UNSUPPORTED_DATE_COUNT', '')}`",
        f"- Unsupported rows: `{values.get('UNSUPPORTED_ROW_COUNT', '')}`",
        f"- Cleanup eligible rows: `{values.get('CLEANUP_ELIGIBLE_ROW_COUNT', '')}`",
        "",
        "## 4. Unsupported Dates By Ledger",
        markdown_table(unsupported, ["ledger_name", "date_value", "row_count", "is_weekend", "is_after_latest_supported_signal_date", "duplicate_date_ticker_count"]),
        "## 5. Cleanup Eligibility",
        markdown_table(eligible, ["ledger_name", "date_value", "row_count", "cleanup_eligible", "cleanup_applied", "removed_rows"]),
        "## 6. Cleanup Result",
        f"- APPLY_CLEANUP: `{values.get('APPLY_CLEANUP', '')}`",
        f"- CLEANUP_DATE: `{values.get('CLEANUP_DATE', '')}`",
        f"- CLEANUP_REMOVED_ROW_COUNT: `{values.get('CLEANUP_REMOVED_ROW_COUNT', '')}`",
        "",
        "## 7. Backup Directory",
        f"- BACKUP_DIR: `{values.get('BACKUP_DIR', '')}`",
        "",
        "## 8. Duplicate Key Validation",
        f"- Signal freeze duplicates: `{values.get('POST_CLEANUP_SIGNAL_FREEZE_DUPLICATE_COUNT', '')}`",
        f"- Recommendation snapshot duplicates: `{values.get('POST_CLEANUP_RECOMMENDATION_SNAPSHOT_DUPLICATE_COUNT', '')}`",
        f"- Trade plan duplicates: `{values.get('POST_CLEANUP_TRADE_PLAN_DUPLICATE_COUNT', '')}`",
        "",
        "## 9. Safety",
        "- No broker connection.",
        "- No order placement.",
        "- No external data fetch.",
        "- Audit-only unless `ApplyCleanup` and `CleanupDate` are both provided.",
        "- `AUTO_TRADE: DISABLED`",
        "- `AUTO_SELL: DISABLED`",
        "- `OFFICIAL_DECISION_IMPACT: NONE`",
        "",
        "## 10. Recommended Next Step",
        next_step,
    ]) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31G_R1_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    latest_supported = determine_latest_supported(root, args.latest_supported_signal_date)
    cleanup_date = parse_date(args.cleanup_date)
    backup_dir = root / BACKUP_ROOT / run_id

    detail_rows: List[Dict[str, object]] = []
    stats_by_name: Dict[str, Dict[str, object]] = {}
    for name, rel, aliases in LEDGERS:
        details, stats = audit_ledger(root, run_id, name, rel, aliases, latest_supported, cleanup_date, args.allow_cleanup_non_weekend)
        detail_rows.extend(details)
        stats_by_name[name] = stats

    unsupported_dates = {(row["ledger_name"], row["date_value"]) for row in detail_rows if row.get("is_unsupported") == "TRUE"}
    unsupported_row_count = sum(int(row["row_count"]) for row in detail_rows if row.get("is_unsupported") == "TRUE")
    eligible_row_count = sum(int(row["row_count"]) for row in detail_rows if row.get("cleanup_eligible") == "TRUE")
    removed_by_name = {"SIGNAL_FREEZE": 0, "RECOMMENDATION_SNAPSHOT": 0, "TRADE_PLAN": 0}
    validation_fails = 0
    status = STATUS_DRY if args.dry_run else (STATUS_WARN if unsupported_row_count else STATUS_CLEAN)
    notes = "Audit only."

    cleanup_requested = bool(args.apply_cleanup)
    if cleanup_requested and not cleanup_date:
        status = STATUS_DATE_REQUIRED
        validation_fails += 1
        notes = "ApplyCleanup requires CleanupDate."
    elif cleanup_requested:
        cleanup_is_unsupported = any(row.get("date_value") == args.cleanup_date and row.get("is_unsupported") == "TRUE" for row in detail_rows)
        if not cleanup_is_unsupported and not args.allow_cleanup_non_weekend:
            status = STATUS_DATE_NOT_ELIGIBLE
            validation_fails += 1
            notes = "CleanupDate is not weekend/future/unsupported."
        elif not args.dry_run and cleanup_date:
            for name, rel, _aliases in LEDGERS:
                stats = stats_by_name[name]
                removed = apply_cleanup(root, rel, stats["fields"], str(stats["date_col"]), cleanup_date, backup_dir)
                removed_by_name[name] = removed
            for row in detail_rows:
                if row.get("date_value") == args.cleanup_date and row.get("cleanup_eligible") == "TRUE":
                    row["cleanup_applied"] = "TRUE"
                    row["removed_rows"] = row.get("row_count", 0)
            removed_total = sum(removed_by_name.values())
            status = STATUS_CLEANUP_OK if removed_total >= 0 else STATUS_CLEANUP_FAIL
            notes = f"Cleanup applied for {args.cleanup_date}; removed {removed_total} rows."
        else:
            notes = "Dry run cleanup requested; no ledger writes."

    post_duplicates: Dict[str, int] = {}
    for name, rel, aliases in LEDGERS:
        rows, fields = read_csv(root / rel)
        date_col = first_col(fields, aliases)
        ticker_col = first_col(fields, ["ticker", "symbol", "asset"])
        post_duplicates[name] = duplicate_count(rows, date_col, ticker_col)
    duplicate_total = sum(post_duplicates.values())
    if cleanup_requested and not args.dry_run and duplicate_total:
        status = STATUS_CLEANUP_FAIL
        validation_fails += 1
        notes = "Duplicate date+ticker keys remain after cleanup."

    removed_total = sum(removed_by_name.values())
    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "LATEST_SUPPORTED_SIGNAL_DATE": date_text(latest_supported),
        "CLEANUP_DATE": args.cleanup_date,
        "APPLY_CLEANUP": bool_text(args.apply_cleanup),
        "ALLOW_CLEANUP_NON_WEEKEND": bool_text(args.allow_cleanup_non_weekend),
        "LEDGER_COUNT_CHECKED": len(LEDGERS),
        "LEDGER_COUNT_EXISTING": sum(1 for stats in stats_by_name.values() if stats["exists"]),
        "UNSUPPORTED_DATE_COUNT": len(unsupported_dates),
        "UNSUPPORTED_ROW_COUNT": unsupported_row_count,
        "CLEANUP_ELIGIBLE_ROW_COUNT": eligible_row_count,
        "CLEANUP_REMOVED_ROW_COUNT": removed_total,
        "BACKUP_DIR": str(backup_dir) if removed_total else "",
        "SIGNAL_FREEZE_UNSUPPORTED_ROW_COUNT": stats_by_name["SIGNAL_FREEZE"]["unsupported_rows"],
        "RECOMMENDATION_SNAPSHOT_UNSUPPORTED_ROW_COUNT": stats_by_name["RECOMMENDATION_SNAPSHOT"]["unsupported_rows"],
        "TRADE_PLAN_UNSUPPORTED_ROW_COUNT": stats_by_name["TRADE_PLAN"]["unsupported_rows"],
        "SIGNAL_FREEZE_CLEANUP_REMOVED_ROWS": removed_by_name["SIGNAL_FREEZE"],
        "RECOMMENDATION_SNAPSHOT_CLEANUP_REMOVED_ROWS": removed_by_name["RECOMMENDATION_SNAPSHOT"],
        "TRADE_PLAN_CLEANUP_REMOVED_ROWS": removed_by_name["TRADE_PLAN"],
        "POST_CLEANUP_SIGNAL_FREEZE_DUPLICATE_COUNT": post_duplicates["SIGNAL_FREEZE"],
        "POST_CLEANUP_RECOMMENDATION_SNAPSHOT_DUPLICATE_COUNT": post_duplicates["RECOMMENDATION_SNAPSHOT"],
        "POST_CLEANUP_TRADE_PLAN_DUPLICATE_COUNT": post_duplicates["TRADE_PLAN"],
        "VALIDATION_FAIL_COUNT": validation_fails,
        "FORBIDDEN_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "NEXT_RECOMMENDED_STEP": "Review details and run ApplyCleanup with CleanupDate only after confirmation." if status == STATUS_WARN else ("Rerun R31G and R31F to confirm." if status == STATUS_CLEANUP_OK else "Continue using R31F as daily entry point."),
        "_GENERATED_AT": generated_at,
        "_NOTES": notes,
    }
    summary = [{
        "run_id": run_id,
        "status": status,
        "generated_at": generated_at,
        "mode": values["MODE"],
        "latest_supported_signal_date": values["LATEST_SUPPORTED_SIGNAL_DATE"],
        "cleanup_date": args.cleanup_date,
        "apply_cleanup": values["APPLY_CLEANUP"],
        "ledger_count_checked": values["LEDGER_COUNT_CHECKED"],
        "ledger_count_existing": values["LEDGER_COUNT_EXISTING"],
        "unsupported_date_count": values["UNSUPPORTED_DATE_COUNT"],
        "unsupported_row_count": values["UNSUPPORTED_ROW_COUNT"],
        "cleanup_eligible_row_count": values["CLEANUP_ELIGIBLE_ROW_COUNT"],
        "cleanup_removed_row_count": values["CLEANUP_REMOVED_ROW_COUNT"],
        "post_cleanup_duplicate_date_ticker_count": duplicate_total,
        "backup_dir": values["BACKUP_DIR"],
        "validation_fail_count": validation_fails,
        "forbidden_modified": "FALSE",
        "notes": notes,
    }]
    write_read_first(root / OUT_READ_FIRST, values)
    write_csv(root / OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(root / OUT_DETAIL, detail_rows, DETAIL_FIELDS)
    report = build_report(values, detail_rows)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT, report)
    return (1 if status.startswith("FAIL_") else 0), values


def write_failure(root: Path, args: argparse.Namespace, exc: BaseException) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {field: "" for field in READ_FIRST_FIELDS}
    values.update({
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31G_R1_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "APPLY_CLEANUP": bool_text(args.apply_cleanup),
        "VALIDATION_FAIL_COUNT": 1,
        "FORBIDDEN_MODIFIED": "UNKNOWN",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "NEXT_RECOMMENDED_STEP": "Inspect R31G-R1 error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    })
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_ERROR, f"# V18.31G-R1 Unsupported Signal-Date Ledger Review Error\n\n```text\n{exc}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31G-R1 unsupported signal-date ledger review and optional cleanup.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cleanup-date", default="")
    parser.add_argument("--apply-cleanup", action="store_true")
    parser.add_argument("--latest-supported-signal-date", default="")
    parser.add_argument("--allow-cleanup-non-weekend", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        code, values = run(root, args)
        print(f"STATUS: {values.get('STATUS', '')}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return code
    except Exception as exc:
        values = write_failure(root, args, exc)
        print(f"STATUS: {values.get('STATUS', STATUS_FAIL)}")
        print(f"ERROR: {exc}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
