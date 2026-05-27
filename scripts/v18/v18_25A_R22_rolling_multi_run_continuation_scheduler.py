from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_PLAN_READY = "OK_V18_25A_R22_ROLLING_MULTI_RUN_CONTINUATION_PLAN_READY"
STATUS_NO_REFRESH = "OK_V18_25A_R22_NO_REFRESH_NEEDED_TRUE_COVERAGE_MET"
STATUS_LEDGER_MISSING = "WARN_V18_25A_R22_LEDGER_MISSING"
STATUS_LEDGER_UNUSABLE = "WARN_V18_25A_R22_LEDGER_UNUSABLE"
STATUS_NO_ELIGIBLE = "WARN_V18_25A_R22_NO_ELIGIBLE_PENDING_BUT_COVERAGE_INCOMPLETE"
STATUS_PARTIAL_FIELDS = "WARN_V18_25A_R22_PARTIAL_LEDGER_FIELDS"

MODE_DRYRUN = "DRYRUN_PLAN_ONLY"
MODE_APPLY = "APPLY_PLAN_METADATA_ONLY"

LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OPTIONAL_INPUTS = [
    "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_REMAINING_STALE_TICKERS.csv",
    "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_COVERAGE_AUDIT.csv",
    "outputs/v18/degraded_daily_review/V18_25A_R16_CURRENT_BATCH3_CANDIDATES.csv",
    "outputs/v18/degraded_daily_review/V18_25A_R15_CURRENT_REMAINING_WORK.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
]

OUT_PLAN = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_MULTI_RUN_REFRESH_PLAN.csv"
OUT_AUDIT = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_MULTI_RUN_REFRESH_AUDIT.csv"
OUT_COVERAGE = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_5DAY_COVERAGE_AUDIT.csv"
OUT_STATE = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_CONTINUATION_STATE.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R22_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R22_CURRENT_ROLLING_MULTI_RUN_CONTINUATION_REPORT.md"

STATE_FIELDS = [
    "ticker",
    "last_success_date",
    "last_success_timestamp",
    "days_since_success",
    "success_within_lookback",
    "success_today",
    "never_success",
    "stale_overdue",
    "continuation_eligible",
    "priority_bucket",
    "priority_rank",
    "selected_for_next_refresh",
    "reason",
]

PLAN_FIELDS = [
    "priority_rank",
    "ticker",
    "priority_bucket",
    "reason",
    "last_success_date",
    "days_since_success",
    "success_today",
    "success_within_lookback",
    "selected_for_next_refresh",
]

AUDIT_FIELDS = ["metric", "value", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "LOOKBACK_DAYS",
    "BATCH_SIZE",
    "ALLOW_SAME_DAY_CONTINUATION",
    "EXCLUDE_TODAY_SUCCESS",
    "LEDGER_PATH",
    "TOTAL_UNIVERSE_COUNT",
    "UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW",
    "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT",
    "NEVER_SUCCESS_COUNT",
    "STALE_OVERDUE_COUNT",
    "TODAY_SUCCESS_COUNT",
    "ELIGIBLE_PENDING_AFTER_TODAY_EXCLUSION",
    "PLANNED_REFRESH_COUNT",
    "TRUE_LOOKBACK_COVERAGE_MET",
    "PLAN_PATH",
    "CONTINUATION_STATE_PATH",
    "COVERAGE_AUDIT_PATH",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "ROLLING_LEDGER_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_key(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def find_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    by_norm = {norm_key(field): field for field in fields}
    for alias in aliases:
        hit = by_norm.get(norm_key(alias))
        if hit:
            return hit
    return None


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except Exception:
            continue
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def collect_optional_tickers(root: Path) -> Tuple[set[str], List[str]]:
    tickers: set[str] = set()
    loaded: List[str] = []
    for rel in OPTIONAL_INPUTS:
        path = root / rel
        rows, fields = read_csv(path)
        if not rows:
            continue
        ticker_col = find_col(fields, ["ticker", "symbol", "Ticker", "candidate_ticker"])
        if not ticker_col:
            continue
        loaded.append(rel)
        for row in rows:
            ticker = norm_ticker(row.get(ticker_col))
            if ticker:
                tickers.add(ticker)
    return tickers, loaded


def classify_rows(
    rows: List[Dict[str, str]],
    fields: Sequence[str],
    today: dt.date,
    lookback_days: int,
    batch_size: int,
    exclude_today_success: bool,
    optional_tickers: set[str],
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], Dict[str, object], List[str]]:
    ticker_col = find_col(fields, ["ticker", "symbol", "Ticker"])
    success_date_col = find_col(fields, ["last_success_scan_date", "last_success_date", "success_date"])
    success_ts_col = find_col(fields, ["last_success_scan_timestamp", "last_success_timestamp", "success_timestamp"])
    status_col = find_col(fields, ["last_scan_status", "scan_status", "status"])
    missing = [
        name
        for name, col in [
            ("ticker", ticker_col),
            ("last_success_scan_date", success_date_col),
            ("last_success_scan_timestamp", success_ts_col),
            ("last_scan_status", status_col),
        ]
        if not col
    ]
    if not ticker_col:
        return [], [], {}, missing

    start_date = today - dt.timedelta(days=max(lookback_days, 1) - 1)
    by_ticker: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col))
        if ticker and ticker not in by_ticker:
            by_ticker[ticker] = row

    state_rows: List[Dict[str, object]] = []
    for ticker, row in sorted(by_ticker.items()):
        last_success_date = parse_date(row.get(success_date_col)) if success_date_col else None
        last_success_ts = str(row.get(success_ts_col, "") or "").strip() if success_ts_col else ""
        status = str(row.get(status_col, "") or "").strip() if status_col else ""
        never_success = last_success_date is None
        days_since = "" if never_success else (today - last_success_date).days
        success_today = bool(last_success_date == today)
        within = bool(last_success_date and start_date <= last_success_date <= today)
        stale = bool(last_success_date and last_success_date < start_date)
        optional = ticker in optional_tickers

        eligible = not success_today or not exclude_today_success
        if never_success:
            bucket = "01_NEVER_SUCCESS"
            base_reason = "NEVER_SUCCESS"
        elif stale:
            bucket = "02_STALE_OVERDUE"
            base_reason = "STALE_OVERDUE"
        elif optional and eligible:
            bucket = "04_OPTIONAL_DEGRADED_VISIBLE"
            base_reason = "OPTIONAL_DEGRADED_OR_CANDIDATE_VISIBLE"
        elif eligible:
            bucket = "03_OLDEST_SUCCESS_REFRESH"
            base_reason = "OLDEST_SUCCESS_REFRESH"
        else:
            bucket = "99_EXCLUDED_TODAY_SUCCESS"
            base_reason = "EXCLUDED_TODAY_SUCCESS"

        continuation_eligible = eligible and bucket != "99_EXCLUDED_TODAY_SUCCESS"
        reason = base_reason
        if optional and base_reason not in {"OPTIONAL_DEGRADED_OR_CANDIDATE_VISIBLE"}:
            reason = f"{base_reason};OPTIONAL_INPUT_VISIBLE"
        if status and base_reason in {"NEVER_SUCCESS", "STALE_OVERDUE"}:
            reason = f"{reason};last_status={status}"

        state_rows.append(
            {
                "ticker": ticker,
                "last_success_date": last_success_date.isoformat() if last_success_date else "",
                "last_success_timestamp": last_success_ts,
                "days_since_success": days_since,
                "success_within_lookback": within,
                "success_today": success_today,
                "never_success": never_success,
                "stale_overdue": stale,
                "continuation_eligible": continuation_eligible,
                "priority_bucket": bucket,
                "priority_rank": "",
                "selected_for_next_refresh": False,
                "reason": reason,
                "_sort_date": last_success_date or dt.date.min,
            }
        )

    true_coverage = sum(1 for row in state_rows if row["success_within_lookback"]) == len(state_rows) and bool(state_rows)
    pending_count = sum(1 for row in state_rows if row["never_success"] or row["stale_overdue"])
    eligible_rows = [row for row in state_rows if row["continuation_eligible"]]
    eligible_rows.sort(key=lambda row: (str(row["priority_bucket"]), row["_sort_date"], str(row["ticker"])))
    plan_rows: List[Dict[str, object]] = [] if true_coverage else eligible_rows[: max(batch_size, 0)]

    selected = {row["ticker"]: idx + 1 for idx, row in enumerate(plan_rows)}
    for row in state_rows:
        if row["ticker"] in selected:
            row["priority_rank"] = selected[row["ticker"]]
            row["selected_for_next_refresh"] = True
    state_rows.sort(key=lambda row: (0 if row["selected_for_next_refresh"] else 1, row["priority_rank"] or 999999, str(row["ticker"])))

    metrics = {
        "total_universe_count": len(state_rows),
        "unique_success_within_lookback_window": sum(1 for row in state_rows if row["success_within_lookback"]),
        "remaining_stale_or_never_success_count": pending_count,
        "never_success_count": sum(1 for row in state_rows if row["never_success"]),
        "stale_overdue_count": sum(1 for row in state_rows if row["stale_overdue"]),
        "today_success_count": sum(1 for row in state_rows if row["success_today"]),
        "eligible_pending_after_today_exclusion": len(eligible_rows) if exclude_today_success else len([row for row in state_rows if row["continuation_eligible"]]),
        "planned_refresh_count": len(plan_rows),
        "true_lookback_coverage_met": true_coverage,
        "lookback_days": lookback_days,
        "batch_size": batch_size,
        "same_day_continuation_enabled": True,
        "exclude_today_success": exclude_today_success,
    }
    return state_rows, plan_rows, metrics, missing


def bool_text(value: object) -> str:
    return "TRUE" if bool(value) else "FALSE"


def audit_rows(metrics: Dict[str, object], optional_loaded: List[str], status: str, validation_fails: int) -> List[Dict[str, object]]:
    rows = [{"metric": key, "value": bool_text(value) if isinstance(value, bool) else value, "notes": ""} for key, value in metrics.items()]
    rows.extend(
        [
            {"metric": "status", "value": status, "notes": ""},
            {"metric": "optional_inputs_loaded_count", "value": len(optional_loaded), "notes": ";".join(optional_loaded)},
            {"metric": "external_fetch_executed", "value": "FALSE", "notes": "Scheduler is local planning only."},
            {"metric": "backtest_executed", "value": "FALSE", "notes": "No backtest execution in R22."},
            {"metric": "validation_fail_count", "value": validation_fails, "notes": ""},
            {"metric": "forbidden_modified", "value": "FALSE", "notes": "R22 writes only its declared outputs."},
        ]
    )
    return rows


def render_read_first(values: Dict[str, object]) -> str:
    lines = []
    for field in READ_FIRST_FIELDS:
        value = values.get(field, "")
        if isinstance(value, bool):
            value = bool_text(value)
        lines.append(f"{field}: {value}")
    return "\n".join(lines) + "\n"


def render_report(values: Dict[str, object], plan_rows: List[Dict[str, object]]) -> str:
    top = ", ".join(str(row["ticker"]) for row in plan_rows[:20]) if plan_rows else "(none)"
    return "\n".join(
        [
            "# V18.25A R22 Rolling Multi-Run Continuation Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Coverage",
            f"- total_universe_count: {values['TOTAL_UNIVERSE_COUNT']}",
            f"- unique_success_within_lookback_window: {values['UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW']}",
            f"- remaining_stale_or_never_success_count: {values['REMAINING_STALE_OR_NEVER_SUCCESS_COUNT']}",
            f"- true_lookback_coverage_met: {values['TRUE_LOOKBACK_COVERAGE_MET']}",
            "",
            "## Next Plan",
            f"- planned_refresh_count: {values['PLANNED_REFRESH_COUNT']}",
            f"- top_20_planned_tickers: {top}",
            "",
            "## Safety",
            "- external_fetch_executed: FALSE",
            "- backtest_executed: FALSE",
            "- rolling_ledger_modified: FALSE",
            "- forbidden_modified: FALSE",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--batch-size", type=int, default=65)
    parser.add_argument("--lookback-days", type=int, default=5)
    parser.add_argument("--allow-same-day-continuation", action="store_true")
    parser.add_argument("--apply-plan", action="store_true")
    parser.add_argument("--exclude-today-success", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    today = dt.date.today()
    run_id = f"V18_25A_R22_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ledger_path = root / LEDGER
    ledger_before = file_sig(ledger_path)
    optional_tickers, optional_loaded = collect_optional_tickers(root)

    status = STATUS_PLAN_READY
    validation_fails = 0
    state_rows: List[Dict[str, object]] = []
    plan_rows: List[Dict[str, object]] = []
    missing_fields: List[str] = []
    metrics: Dict[str, object] = {
        "total_universe_count": 0,
        "unique_success_within_lookback_window": 0,
        "remaining_stale_or_never_success_count": 0,
        "never_success_count": 0,
        "stale_overdue_count": 0,
        "today_success_count": 0,
        "eligible_pending_after_today_exclusion": 0,
        "planned_refresh_count": 0,
        "true_lookback_coverage_met": False,
        "lookback_days": args.lookback_days,
        "batch_size": args.batch_size,
        "same_day_continuation_enabled": args.allow_same_day_continuation,
        "exclude_today_success": args.exclude_today_success,
    }

    if not ledger_path.exists():
        status = STATUS_LEDGER_MISSING
        validation_fails = 1
    else:
        ledger_rows, ledger_fields = read_csv(ledger_path)
        if not ledger_rows or not ledger_fields:
            status = STATUS_LEDGER_UNUSABLE
            validation_fails = 1
        else:
            state_rows, plan_rows, metrics, missing_fields = classify_rows(
                ledger_rows,
                ledger_fields,
                today,
                max(args.lookback_days, 1),
                max(args.batch_size, 0),
                args.exclude_today_success,
                optional_tickers,
            )
            metrics["same_day_continuation_enabled"] = args.allow_same_day_continuation
            if missing_fields:
                status = STATUS_PARTIAL_FIELDS
                validation_fails = 1
            elif metrics["true_lookback_coverage_met"]:
                status = STATUS_NO_REFRESH
            elif metrics["planned_refresh_count"] == 0:
                status = STATUS_NO_ELIGIBLE
                validation_fails = 1

    ledger_after = file_sig(ledger_path)
    ledger_modified = ledger_before != ledger_after
    if ledger_modified and not args.apply_plan:
        validation_fails += 1

    plan_export = [{field: row.get(field, "") for field in PLAN_FIELDS} for row in plan_rows]
    for idx, row in enumerate(plan_export, 1):
        row["priority_rank"] = idx
        row["selected_for_next_refresh"] = True

    write_csv(root / OUT_PLAN, plan_export, PLAN_FIELDS)
    write_csv(root / OUT_STATE, state_rows, STATE_FIELDS)
    write_csv(root / OUT_AUDIT, audit_rows(metrics, optional_loaded, status, validation_fails), AUDIT_FIELDS)
    write_csv(root / OUT_COVERAGE, audit_rows(metrics, optional_loaded, status, validation_fails), AUDIT_FIELDS)

    next_step = "Run the next local refresh batch using the R22 plan, then update the rolling ledger with the validated refresh result."
    if status == STATUS_NO_REFRESH:
        next_step = "No refresh needed; true lookback coverage is already met."
    elif status.startswith("WARN"):
        next_step = "Review ledger fields and continuation eligibility before scheduling another refresh."

    read_values = {
        "STATUS": status,
        "MODE": MODE_APPLY if args.apply_plan else MODE_DRYRUN,
        "RUN_ID": run_id,
        "LOOKBACK_DAYS": args.lookback_days,
        "BATCH_SIZE": args.batch_size,
        "ALLOW_SAME_DAY_CONTINUATION": args.allow_same_day_continuation,
        "EXCLUDE_TODAY_SUCCESS": args.exclude_today_success,
        "LEDGER_PATH": LEDGER,
        "TOTAL_UNIVERSE_COUNT": metrics["total_universe_count"],
        "UNIQUE_SUCCESS_WITHIN_LOOKBACK_WINDOW": metrics["unique_success_within_lookback_window"],
        "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT": metrics["remaining_stale_or_never_success_count"],
        "NEVER_SUCCESS_COUNT": metrics["never_success_count"],
        "STALE_OVERDUE_COUNT": metrics["stale_overdue_count"],
        "TODAY_SUCCESS_COUNT": metrics["today_success_count"],
        "ELIGIBLE_PENDING_AFTER_TODAY_EXCLUSION": metrics["eligible_pending_after_today_exclusion"],
        "PLANNED_REFRESH_COUNT": metrics["planned_refresh_count"],
        "TRUE_LOOKBACK_COVERAGE_MET": metrics["true_lookback_coverage_met"],
        "PLAN_PATH": OUT_PLAN,
        "CONTINUATION_STATE_PATH": OUT_STATE,
        "COVERAGE_AUDIT_PATH": OUT_COVERAGE,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "ROLLING_LEDGER_MODIFIED": bool_text(ledger_modified),
        "PRICE_CACHE_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_FILES_MODIFIED": "FALSE",
        "VALIDATION_FAIL_COUNT": validation_fails,
        "FORBIDDEN_MODIFIED": bool_text(ledger_modified and not args.apply_plan),
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, render_read_first(read_values))
    write_text(root / OUT_REPORT, render_report(read_values, plan_rows))

    print(f"STATUS: {status}")
    print(f"MODE: {read_values['MODE']}")
    print(f"READ_FIRST: {(root / OUT_READ_FIRST)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
