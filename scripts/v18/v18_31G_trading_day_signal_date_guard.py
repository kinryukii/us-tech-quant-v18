from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_31G_TRADING_DAY_SIGNAL_DATE_GUARD_DRY_RUN_READY"
STATUS_ALLOWED = "OK_V18_31G_TRADING_DAY_SIGNAL_DATE_ALLOWED"
STATUS_BLOCK_REUSE = "WARN_V18_31G_TRADING_DAY_SIGNAL_DATE_BLOCKED_REUSE_LATEST"
STATUS_UNKNOWN_PRICE = "WARN_V18_31G_PRICE_DATE_UNKNOWN_BLOCK_NEW_SIGNAL_DATE"
STATUS_OVERRIDE = "WARN_V18_31G_SIGNAL_DATE_OVERRIDE_USED_REVIEW_NEEDED"
STATUS_REVIEW = "WARN_V18_31G_NON_TRADING_SIGNAL_DATE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31G_TRADING_DAY_SIGNAL_DATE_GUARD_FAILED"

MODE_LIVE = "TRADING_DAY_SIGNAL_DATE_GUARD"
MODE_DRY = "TRADING_DAY_SIGNAL_DATE_GUARD_DRY_RUN"
EXPECTED_ROWS = 252

DATE_COLUMNS = {
    "signal_date",
    "snapshot_date",
    "price_date",
    "latest_price_date",
    "latest_close_date",
    "as_of_date",
    "data_date",
    "generated_date",
    "trade_date",
    "price_asof_date",
    "latest_full_freeze_signal_date",
    "latest_signal_freeze_date",
}
PRICE_DATE_COLUMNS = {"price_date", "latest_price_date", "latest_close_date", "price_asof_date", "trade_date"}

CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
CURRENT_RECS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
POSITION_POLICY = "outputs/v18/execution/V18_CURRENT_POSITION_SIZING_POLICY.csv"
COST_ADJUSTED = "outputs/v18/execution/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.csv"
ACCOUNT_AWARE = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
RECOMMENDATION_LEDGER = "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv"
TRADE_PLAN_LEDGER = "state/v18/trade_plan_snapshots/V18_DAILY_TRADE_PLAN_LEDGER.csv"
BACKUP_ROOT = "archive/v18/non_trading_signal_date_guard_backups"

OUT_READ_FIRST = "outputs/v18/ops/V18_31G_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31G_TRADING_DAY_SIGNAL_DATE_GUARD_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_31G_TRADING_DAY_SIGNAL_DATE_GUARD_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md"
OUT_ERROR = "outputs/v18/read_center/V18_31G_TRADING_DAY_SIGNAL_DATE_GUARD_ERROR.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "CANDIDATE_SIGNAL_DATE",
    "CURRENT_LOCAL_DATE",
    "CANDIDATE_DATE_WEEKDAY",
    "CANDIDATE_IS_WEEKEND",
    "LATEST_OBSERVED_PRICE_DATE",
    "LATEST_FULL_FREEZE_SIGNAL_DATE",
    "LATEST_RECOMMENDATION_SNAPSHOT_DATE",
    "LATEST_TRADE_PLAN_LEDGER_SIGNAL_DATE",
    "NEW_SIGNAL_DATE_ALLOWED",
    "REUSE_LATEST_SIGNAL_DATE_RECOMMENDED",
    "RECOMMENDED_SIGNAL_DATE",
    "R31F_SHOULD_SKIP_R21",
    "R31F_SHOULD_SKIP_R29C",
    "R31F_SHOULD_PREVENT_NEW_R31E_DATE",
    "ALLOW_NON_TRADING_DATE_OVERRIDE",
    "ALLOW_UNKNOWN_PRICE_DATE_OVERRIDE",
    "APPLY_CLEANUP",
    "CLEANUP_DATE",
    "CLEANUP_ACTION",
    "SIGNAL_FREEZE_LEDGER_ROWS",
    "RECOMMENDATION_SNAPSHOT_LEDGER_ROWS",
    "TRADE_PLAN_LEDGER_ROWS",
    "NON_TRADING_SIGNAL_DATE_COUNT",
    "FUTURE_OR_UNSUPPORTED_SIGNAL_DATE_COUNT",
    "DUPLICATE_TRADE_PLAN_SIGNAL_DATE_TICKER_COUNT",
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
    "candidate_signal_date",
    "latest_observed_price_date",
    "latest_full_freeze_signal_date",
    "latest_recommendation_snapshot_date",
    "latest_trade_plan_ledger_signal_date",
    "new_signal_date_allowed",
    "reuse_latest_signal_date_recommended",
    "recommended_signal_date",
    "r31f_should_skip_r21",
    "r31f_should_skip_r29c",
    "r31f_should_prevent_new_r31e_date",
    "non_trading_signal_date_count",
    "future_or_unsupported_signal_date_count",
    "duplicate_trade_plan_signal_date_ticker_count",
    "apply_cleanup",
    "cleanup_date",
    "cleanup_action",
    "validation_fail_count",
    "forbidden_modified",
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


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def observed_dates_from_rows(rows: Sequence[Dict[str, str]], fields: Sequence[str], price_only: bool) -> List[dt.date]:
    out: List[dt.date] = []
    allowed = PRICE_DATE_COLUMNS if price_only else DATE_COLUMNS
    for field in fields:
        if field.lower() not in allowed:
            continue
        for row in rows:
            parsed = parse_date(row.get(field))
            if parsed:
                out.append(parsed)
    return out


def latest_full_date(rows: Sequence[Dict[str, str]], date_field: str, ticker_field: str = "ticker") -> Optional[dt.date]:
    by_date: Dict[dt.date, set[str]] = {}
    for row in rows:
        date = parse_date(row.get(date_field))
        ticker = upper(row.get(ticker_field))
        if date and ticker:
            by_date.setdefault(date, set()).add(ticker)
    full_dates = [date for date, tickers in by_date.items() if len(tickers) == EXPECTED_ROWS]
    if full_dates:
        return max(full_dates)
    return max(by_date.keys(), default=None)


def duplicate_signal_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter((norm(row.get("signal_date")), upper(row.get("ticker"))) for row in rows)
    return sum(1 for (signal_date, ticker), count in counts.items() if signal_date and ticker and count > 1)


def all_signal_dates(rows: Sequence[Dict[str, str]], date_fields: Sequence[str]) -> List[dt.date]:
    dates: List[dt.date] = []
    for row in rows:
        for field in date_fields:
            parsed = parse_date(row.get(field))
            if parsed:
                dates.append(parsed)
                break
    return dates


def supported_signal_dates(rows: Sequence[Dict[str, str]], latest_price_date: Optional[dt.date]) -> List[dt.date]:
    if not latest_price_date:
        return []
    dates = set()
    for row in rows:
        signal_date = parse_date(row.get("signal_date")) or parse_date(row.get("snapshot_date")) or parse_date(row.get("latest_signal_freeze_date"))
        if signal_date and signal_date.weekday() < 5 and signal_date <= latest_price_date:
            dates.add(signal_date)
    return sorted(dates)


def collect_context(root: Path) -> Dict[str, object]:
    source_rels = [CURRENT_RANKED, CURRENT_THEMES, CURRENT_RECS, TECHNICAL_TIMING, BUYABILITY, POSITION_POLICY, COST_ADJUSTED, ACCOUNT_AWARE, SIGNAL_FREEZE_LEDGER]
    price_dates: List[dt.date] = []
    all_source_dates: List[dt.date] = []
    for rel in source_rels:
        rows, fields = read_csv(root / rel)
        price_dates.extend(observed_dates_from_rows(rows, fields, price_only=True))
        all_source_dates.extend(observed_dates_from_rows(rows, fields, price_only=False))

    freeze_rows, _ = read_csv(root / SIGNAL_FREEZE_LEDGER)
    rec_rows, _ = read_csv(root / RECOMMENDATION_LEDGER)
    trade_rows, _ = read_csv(root / TRADE_PLAN_LEDGER)
    latest_price = max(price_dates, default=None)
    latest_full_freeze = latest_full_date(freeze_rows, "signal_date")
    latest_rec_snapshot = latest_full_date(rec_rows, "snapshot_date")
    latest_trade_signal = latest_full_date(trade_rows, "signal_date")
    ledger_dates = all_signal_dates(freeze_rows, ["signal_date"]) + all_signal_dates(rec_rows, ["snapshot_date", "latest_signal_freeze_date"]) + all_signal_dates(trade_rows, ["signal_date"])
    non_trading = {date for date in ledger_dates if date.weekday() >= 5}
    future_or_unsupported = {date for date in ledger_dates if latest_price and date > latest_price}
    supported_dates = supported_signal_dates(freeze_rows + rec_rows + trade_rows, latest_price)
    recommended = max(supported_dates, default=None) or latest_price or latest_full_freeze or latest_rec_snapshot or latest_trade_signal
    return {
        "price_dates": price_dates,
        "latest_observed_price_date": latest_price,
        "latest_full_freeze_signal_date": latest_full_freeze,
        "latest_recommendation_snapshot_date": latest_rec_snapshot,
        "latest_trade_plan_ledger_signal_date": latest_trade_signal,
        "recommended_signal_date": recommended,
        "signal_freeze_rows": len(freeze_rows),
        "recommendation_rows": len(rec_rows),
        "trade_plan_rows": len(trade_rows),
        "non_trading_signal_date_count": len(non_trading),
        "future_or_unsupported_signal_date_count": len(future_or_unsupported),
        "duplicate_trade_plan_signal_date_ticker_count": duplicate_signal_ticker_count(trade_rows),
    }


def cleanup_ledger(path: Path, date_field: str, cleanup_date: dt.date, backup_dir: Path) -> Tuple[int, str]:
    rows, fields = read_csv(path)
    if not path.exists() or not rows:
        return 0, ""
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / path.name
    shutil.copy2(path, backup_path)
    kept = [row for row in rows if parse_date(row.get(date_field)) != cleanup_date]
    removed = len(rows) - len(kept)
    if removed:
        write_csv(path, kept, fields)
    return removed, str(backup_path)


def build_values(root: Path, args: argparse.Namespace, run_id: str, generated_at: str) -> Tuple[Dict[str, object], str]:
    today = dt.date.today()
    candidate = parse_date(args.candidate_signal_date) if args.candidate_signal_date else today
    if candidate is None:
        candidate = today
    context = collect_context(root)
    latest_price: Optional[dt.date] = context["latest_observed_price_date"]  # type: ignore[assignment]
    is_weekend = candidate.weekday() >= 5
    weekday_name = candidate.strftime("%A")
    structural_ok = (
        (root / CURRENT_RANKED).exists()
        and (root / CURRENT_RECS).exists()
        and (root / CURRENT_THEMES).exists()
    )
    override_used = (is_weekend and args.allow_non_trading_date) or (latest_price is None and args.allow_unknown_price_date)
    date_supported = bool(latest_price and latest_price >= candidate)
    if latest_price is None:
        allowed = bool(args.allow_unknown_price_date and not is_weekend and structural_ok)
    else:
        allowed = bool(candidate.weekday() < 5 and date_supported and structural_ok)
    if args.allow_non_trading_date and latest_price and latest_price >= candidate and structural_ok:
        allowed = True
    if args.allow_unknown_price_date and candidate.weekday() < 5 and structural_ok:
        allowed = True

    recommended: Optional[dt.date] = context["recommended_signal_date"]  # type: ignore[assignment]
    reuse = not allowed and recommended is not None
    if args.dry_run:
        status = STATUS_DRY
        next_step = "Run live R31G audit before full R31F orchestration."
    elif override_used:
        status = STATUS_OVERRIDE
        next_step = "Override used; review local price-date evidence before creating ledgers."
    elif not structural_ok:
        status = STATUS_FAIL
        next_step = "Restore current ranked/recommendation/theme files before running R31F."
    elif allowed:
        status = STATUS_ALLOWED
        next_step = "Run normal R31F sequence."
    elif latest_price is None and not args.allow_unknown_price_date:
        status = STATUS_UNKNOWN_PRICE
        next_step = "Do not create a new signal date until local price-date evidence is available."
    elif context["non_trading_signal_date_count"] or context["future_or_unsupported_signal_date_count"]:
        status = STATUS_REVIEW if not reuse else STATUS_BLOCK_REUSE
        next_step = "Reuse the latest supported signal date; optional cleanup can be reviewed separately."
    else:
        status = STATUS_BLOCK_REUSE
        next_step = "Reuse the latest supported signal date and skip new R21/R29C/R31E calendar-date creation."

    cleanup_action = "AUDIT_ONLY_NO_CLEANUP"
    if args.apply_cleanup:
        cleanup_date = parse_date(args.cleanup_date)
        if not cleanup_date:
            status = STATUS_FAIL
            cleanup_action = "FAILED_CLEANUP_DATE_REQUIRED"
        elif not args.allow_non_trading_date and latest_price and cleanup_date <= latest_price and cleanup_date.weekday() < 5:
            status = STATUS_FAIL
            cleanup_action = "FAILED_CLEANUP_DATE_NOT_UNSUPPORTED"
        elif not args.dry_run:
            backup_dir = root / BACKUP_ROOT / run_id
            removed_trade, _ = cleanup_ledger(root / TRADE_PLAN_LEDGER, "signal_date", cleanup_date, backup_dir)
            removed_rec, _ = cleanup_ledger(root / RECOMMENDATION_LEDGER, "snapshot_date", cleanup_date, backup_dir)
            removed_freeze, _ = cleanup_ledger(root / SIGNAL_FREEZE_LEDGER, "signal_date", cleanup_date, backup_dir)
            cleanup_action = f"REMOVED trade_plan={removed_trade};recommendation={removed_rec};signal_freeze={removed_freeze};backup={backup_dir}"
            context = collect_context(root)
        else:
            cleanup_action = "DRY_RUN_CLEANUP_NOT_APPLIED"

    validation_fails = 0
    if status == STATUS_FAIL:
        validation_fails += 1
    if context["duplicate_trade_plan_signal_date_ticker_count"]:
        validation_fails += 1

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "CANDIDATE_SIGNAL_DATE": date_text(candidate),
        "CURRENT_LOCAL_DATE": date_text(today),
        "CANDIDATE_DATE_WEEKDAY": weekday_name,
        "CANDIDATE_IS_WEEKEND": bool_text(is_weekend),
        "LATEST_OBSERVED_PRICE_DATE": date_text(latest_price),
        "LATEST_FULL_FREEZE_SIGNAL_DATE": date_text(context["latest_full_freeze_signal_date"]),  # type: ignore[arg-type]
        "LATEST_RECOMMENDATION_SNAPSHOT_DATE": date_text(context["latest_recommendation_snapshot_date"]),  # type: ignore[arg-type]
        "LATEST_TRADE_PLAN_LEDGER_SIGNAL_DATE": date_text(context["latest_trade_plan_ledger_signal_date"]),  # type: ignore[arg-type]
        "NEW_SIGNAL_DATE_ALLOWED": bool_text(allowed),
        "REUSE_LATEST_SIGNAL_DATE_RECOMMENDED": bool_text(reuse),
        "RECOMMENDED_SIGNAL_DATE": date_text(recommended),
        "R31F_SHOULD_SKIP_R21": bool_text(not allowed and reuse),
        "R31F_SHOULD_SKIP_R29C": bool_text(not allowed and reuse),
        "R31F_SHOULD_PREVENT_NEW_R31E_DATE": bool_text(not allowed),
        "ALLOW_NON_TRADING_DATE_OVERRIDE": bool_text(args.allow_non_trading_date),
        "ALLOW_UNKNOWN_PRICE_DATE_OVERRIDE": bool_text(args.allow_unknown_price_date),
        "APPLY_CLEANUP": bool_text(args.apply_cleanup),
        "CLEANUP_DATE": args.cleanup_date,
        "CLEANUP_ACTION": cleanup_action,
        "SIGNAL_FREEZE_LEDGER_ROWS": context["signal_freeze_rows"],
        "RECOMMENDATION_SNAPSHOT_LEDGER_ROWS": context["recommendation_rows"],
        "TRADE_PLAN_LEDGER_ROWS": context["trade_plan_rows"],
        "NON_TRADING_SIGNAL_DATE_COUNT": context["non_trading_signal_date_count"],
        "FUTURE_OR_UNSUPPORTED_SIGNAL_DATE_COUNT": context["future_or_unsupported_signal_date_count"],
        "DUPLICATE_TRADE_PLAN_SIGNAL_DATE_TICKER_COUNT": context["duplicate_trade_plan_signal_date_ticker_count"],
        "VALIDATION_FAIL_COUNT": validation_fails,
        "FORBIDDEN_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "NEXT_RECOMMENDED_STEP": next_step,
        "_GENERATED_AT": generated_at,
    }
    if args.apply_cleanup:
        values["FORBIDDEN_MODIFIED"] = "FALSE"
    notes = "NORMAL_DAILY_RUN" if allowed else ("REUSE_LATEST_SIGNAL_DATE_SKIP_NEW_LEDGER_DATE" if reuse else "BLOCK_NEW_SIGNAL_DATE_REQUIRES_OVERRIDE")
    if context["non_trading_signal_date_count"] or context["future_or_unsupported_signal_date_count"]:
        notes += ";OPTIONAL_CLEANUP_RECOMMENDED"
    if override_used:
        notes += ";OVERRIDE_USED"
    return values, notes


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [{
        "run_id": values.get("RUN_ID", ""),
        "status": values.get("STATUS", ""),
        "generated_at": values.get("_GENERATED_AT", ""),
        "candidate_signal_date": values.get("CANDIDATE_SIGNAL_DATE", ""),
        "latest_observed_price_date": values.get("LATEST_OBSERVED_PRICE_DATE", ""),
        "latest_full_freeze_signal_date": values.get("LATEST_FULL_FREEZE_SIGNAL_DATE", ""),
        "latest_recommendation_snapshot_date": values.get("LATEST_RECOMMENDATION_SNAPSHOT_DATE", ""),
        "latest_trade_plan_ledger_signal_date": values.get("LATEST_TRADE_PLAN_LEDGER_SIGNAL_DATE", ""),
        "new_signal_date_allowed": values.get("NEW_SIGNAL_DATE_ALLOWED", ""),
        "reuse_latest_signal_date_recommended": values.get("REUSE_LATEST_SIGNAL_DATE_RECOMMENDED", ""),
        "recommended_signal_date": values.get("RECOMMENDED_SIGNAL_DATE", ""),
        "r31f_should_skip_r21": values.get("R31F_SHOULD_SKIP_R21", ""),
        "r31f_should_skip_r29c": values.get("R31F_SHOULD_SKIP_R29C", ""),
        "r31f_should_prevent_new_r31e_date": values.get("R31F_SHOULD_PREVENT_NEW_R31E_DATE", ""),
        "non_trading_signal_date_count": values.get("NON_TRADING_SIGNAL_DATE_COUNT", ""),
        "future_or_unsupported_signal_date_count": values.get("FUTURE_OR_UNSUPPORTED_SIGNAL_DATE_COUNT", ""),
        "duplicate_trade_plan_signal_date_ticker_count": values.get("DUPLICATE_TRADE_PLAN_SIGNAL_DATE_TICKER_COUNT", ""),
        "apply_cleanup": values.get("APPLY_CLEANUP", ""),
        "cleanup_date": values.get("CLEANUP_DATE", ""),
        "cleanup_action": values.get("CLEANUP_ACTION", ""),
        "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
        "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
        "notes": notes,
    }]


def build_report(values: Dict[str, object], notes: str) -> str:
    return "\n".join([
        "# V18.31G Trading-Day / Latest-Price-Date Signal-Date Guard",
        "",
        "## 1. Final Guard Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Candidate Signal Date",
        f"- Candidate signal date: `{values.get('CANDIDATE_SIGNAL_DATE', '')}`",
        f"- Weekday: `{values.get('CANDIDATE_DATE_WEEKDAY', '')}`",
        f"- Weekend: `{values.get('CANDIDATE_IS_WEEKEND', '')}`",
        "",
        "## 3. Latest Observed Price Date",
        f"- Latest observed local price date: `{values.get('LATEST_OBSERVED_PRICE_DATE', '')}`",
        "",
        "## 4. Latest Full Freeze Signal Date",
        f"- Latest full freeze signal date: `{values.get('LATEST_FULL_FREEZE_SIGNAL_DATE', '')}`",
        "",
        "## 5. Latest Recommendation Snapshot Date",
        f"- Latest recommendation snapshot date: `{values.get('LATEST_RECOMMENDATION_SNAPSHOT_DATE', '')}`",
        "",
        "## 6. Latest Trade Plan Ledger Signal Date",
        f"- Latest trade plan ledger signal date: `{values.get('LATEST_TRADE_PLAN_LEDGER_SIGNAL_DATE', '')}`",
        "",
        "## 7. New Signal Date Allowed",
        f"- NEW_SIGNAL_DATE_ALLOWED: `{values.get('NEW_SIGNAL_DATE_ALLOWED', '')}`",
        f"- RECOMMENDED_SIGNAL_DATE: `{values.get('RECOMMENDED_SIGNAL_DATE', '')}`",
        "",
        "## 8. Recommended Action",
        f"- `{notes}`",
        f"- R31F skip R21: `{values.get('R31F_SHOULD_SKIP_R21', '')}`",
        f"- R31F skip R29C: `{values.get('R31F_SHOULD_SKIP_R29C', '')}`",
        f"- R31F prevent new R31E date: `{values.get('R31F_SHOULD_PREVENT_NEW_R31E_DATE', '')}`",
        "",
        "## 9. Unsupported / Non-Trading Signal Dates",
        f"- NON_TRADING_SIGNAL_DATE_COUNT: `{values.get('NON_TRADING_SIGNAL_DATE_COUNT', '')}`",
        f"- FUTURE_OR_UNSUPPORTED_SIGNAL_DATE_COUNT: `{values.get('FUTURE_OR_UNSUPPORTED_SIGNAL_DATE_COUNT', '')}`",
        f"- DUPLICATE_TRADE_PLAN_SIGNAL_DATE_TICKER_COUNT: `{values.get('DUPLICATE_TRADE_PLAN_SIGNAL_DATE_TICKER_COUNT', '')}`",
        f"- CLEANUP_ACTION: `{values.get('CLEANUP_ACTION', '')}`",
        "",
        "## 10. Safety Notes",
        "- No broker connection.",
        "- No order placement.",
        "- No external data fetch.",
        "- Guard is based on local files only.",
        "- `AUTO_TRADE: DISABLED`",
        "- `AUTO_SELL: DISABLED`",
        "- `OFFICIAL_DECISION_IMPACT: NONE`",
    ]) + "\n"


def write_outputs(root: Path, values: Dict[str, object], notes: str) -> None:
    write_read_first(root / OUT_READ_FIRST, values)
    write_csv(root / OUT_SUMMARY, build_summary(values, notes), SUMMARY_FIELDS)
    report = build_report(values, notes)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31G_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    values, notes = build_values(root, args, run_id, generated_at)
    write_outputs(root, values, notes)
    return (1 if values["STATUS"] == STATUS_FAIL else 0), values


def write_failure(root: Path, args: argparse.Namespace, exc: BaseException) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {field: "" for field in READ_FIRST_FIELDS}
    values.update({
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31G_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 1,
        "FORBIDDEN_MODIFIED": "UNKNOWN",
        "NEXT_RECOMMENDED_STEP": "Inspect R31G error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    })
    write_read_first(root / OUT_READ_FIRST, values)
    write_csv(root / OUT_SUMMARY, build_summary(values, str(exc)), SUMMARY_FIELDS)
    write_text(root / OUT_ERROR, f"# V18.31G Trading-Day Signal-Date Guard Error\n\n```text\n{exc}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31G trading-day/latest-price-date signal-date guard.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--candidate-signal-date", default="")
    parser.add_argument("--allow-non-trading-date", action="store_true")
    parser.add_argument("--allow-unknown-price-date", action="store_true")
    parser.add_argument("--apply-cleanup", action="store_true")
    parser.add_argument("--cleanup-date", default="")
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
