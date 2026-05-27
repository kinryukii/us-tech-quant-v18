from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27C_CONTROLLED_PARTIAL_MATURE_INTEGRATION_DRYRUN_READY"
STATUS_WARN = "WARN_V18_25A_R27C_DRYRUN_WARNINGS"
STATUS_FAIL_INPUTS = "FAIL_V18_25A_R27C_REQUIRED_INPUTS_MISSING_OR_UNREADABLE"
STATUS_FAIL_FORBIDDEN = "FAIL_V18_25A_R27C_FORBIDDEN_PATH_MODIFIED"

MODE = "DRYRUN_CONTROLLED_PARTIAL_MATURE_INTEGRATION_ONLY"

EXPECTED_TICKERS = {"TLN", "RDDT"}
R27B_READ_FIRST = "outputs/v18/ops/V18_25A_R27B_READ_FIRST.txt"
R27B_EXPECTED_STATUS = "OK_V18_25A_R27B_MATURE_PARTIAL_POLICY_REVIEW_READY"
R27B_CANDIDATES = "outputs/v18/coverage_resolution/V18_25A_R27B_CURRENT_R27C_DRYRUN_CANDIDATES.csv"
R27B_POLICY = "outputs/v18/coverage_resolution/V18_25A_R27B_CURRENT_MATURE_PARTIAL_POLICY_REVIEW.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
PRICE_CACHE = "state/v18/price_cache"

OUT_DIR = "outputs/v18/coverage_resolution"
OUT_PRICE_PLAN = f"{OUT_DIR}/V18_25A_R27C_CURRENT_PARTIAL_MATURE_PRICE_CACHE_INTEGRATION_DRYRUN_PLAN.csv"
OUT_LEDGER_PLAN = f"{OUT_DIR}/V18_25A_R27C_CURRENT_PARTIAL_MATURE_ROLLING_LEDGER_DRYRUN_PLAN.csv"
OUT_VALIDATION = f"{OUT_DIR}/V18_25A_R27C_CURRENT_DRYRUN_VALIDATION.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27C_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27C_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27C_CURRENT_CONTROLLED_PARTIAL_MATURE_INTEGRATION_DRYRUN_REPORT.md"

REQUIRED_COLUMNS = {"ticker", "date", "open", "high", "low", "close", "volume"}

PRICE_PLAN_FIELDS = [
    "ticker",
    "source_normalized_file",
    "target_price_cache_file",
    "action",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "dryrun_status",
    "blocker",
]

LEDGER_PLAN_FIELDS = [
    "ticker",
    "current_last_scan_status",
    "current_last_success_scan_date",
    "would_set_last_scan_status",
    "would_set_last_success_scan_date",
    "would_set_last_attempt_scan_timestamp",
    "dryrun_status",
]

VALIDATION_FIELDS = [
    "ticker",
    "source_normalized_file",
    "target_price_cache_file",
    "file_exists",
    "readable",
    "required_columns_present",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "date_parse_ok",
    "duplicate_date_count",
    "null_close_count",
    "rolling_ledger_present",
    "rolling_ledger_current_never_success",
    "price_cache_present",
    "dryrun_status",
    "blocker",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27B_STATUS",
    "DRYRUN_CANDIDATE_COUNT",
    "EXPECTED_TICKER_MATCH",
    "DRYRUN_PASS_COUNT",
    "DRYRUN_BLOCKED_COUNT",
    "PRICE_CACHE_DRYRUN_CREATE_COUNT",
    "PRICE_CACHE_DRYRUN_UPDATE_COUNT",
    "ROLLING_LEDGER_DRYRUN_UPDATE_COUNT",
    "R27D_APPLY_RECOMMENDED",
    "OFFICIAL_INTEGRATION_ALLOWED_NEXT",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "CANDIDATES_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def norm_bool(value: object) -> bool:
    return str(value or "").strip().upper() == "TRUE"


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except Exception:
            continue
    return None


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value != "":
            return value
    return ""


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def read_optional_status(path: Path) -> str:
    text = read_text(path)
    for line in text.splitlines():
        if line.startswith("STATUS:"):
            return line.split(":", 1)[1].strip()
    return ""


def load_required_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], Optional[str]]:
    rows, fields = read_csv(path)
    if not path.exists():
        return rows, fields, "missing"
    if path.exists() and path.stat().st_size > 0 and not fields:
        return rows, fields, "unreadable"
    return rows, fields, None


def load_source_metrics(path: Path) -> Tuple[bool, bool, bool, int, str, str, float, float, int, int]:
    rows, fields = read_csv(path)
    file_exists = path.exists()
    readable = bool(fields)
    required_present = REQUIRED_COLUMNS.issubset({str(f).strip().lower() for f in fields})
    dates: List[dt.date] = []
    duplicate_count = 0
    null_close_count = 0
    seen_dates: set[str] = set()
    latest_close = ""
    latest_volume = ""
    for row in rows:
        date_text = str(row.get("date", "") or "").strip()[:10]
        parsed = parse_date(date_text)
        if parsed is not None:
            dates.append(parsed)
        if date_text in seen_dates:
            duplicate_count += 1
        else:
            seen_dates.add(date_text)
        if not str(row.get("close", "") or "").strip():
            null_close_count += 1
    if rows:
        latest_row = max(rows, key=lambda r: str(r.get("date", "") or ""))
        latest_close = str(latest_row.get("close", "") or "").strip()
        latest_volume = str(latest_row.get("volume", "") or "").strip()
    date_parse_ok = len(dates) == len(rows) and all(dates)
    min_date = min(dates).isoformat() if dates else ""
    max_date = max(dates).isoformat() if dates else ""
    row_count = len(rows)
    return file_exists, readable, required_present, row_count, min_date, max_date, latest_close, latest_volume, date_parse_ok, duplicate_count, null_close_count


def row_passes_dryrun(row: Dict[str, str], ticker: str, source_path: Path, ledger_row: Dict[str, str], root: Path) -> Tuple[bool, str, Dict[str, object]]:
    file_exists, readable, required_ok, row_count, min_date, max_date, latest_close, latest_volume, date_parse_ok, duplicate_count, null_close_count = load_source_metrics(source_path)
    blockers: List[str] = []
    if not file_exists:
        blockers.append("source_normalized_file_missing")
    if file_exists and not readable:
        blockers.append("source_normalized_file_unreadable")
    if not required_ok:
        blockers.append("required_columns_missing")
    if row_count < 500:
        blockers.append("row_count_below_500")
    if not date_parse_ok:
        blockers.append("date_parse_failed")
    if duplicate_count != 0:
        blockers.append("duplicate_date_count_nonzero")
    if null_close_count != 0:
        blockers.append("null_close_count_nonzero")
    if not non_null(latest_close):
        blockers.append("latest_close_missing")
    if not non_null(latest_volume):
        blockers.append("latest_volume_missing")
    ledger_present = bool(ledger_row)
    if not ledger_present:
        blockers.append("missing_from_rolling_ledger")
    else:
        success_date = get_field(ledger_row, "last_success_scan_date")
        success_count = to_int(get_field(ledger_row, "success_scan_count"))
        if success_count > 0 or non_null(success_date):
            blockers.append("not_current_never_success")
    current_scan_status = get_field(ledger_row, "last_scan_status", "scan_status", "status")
    price_cache_path = root / "state" / "v18" / "price_cache" / f"{ticker}.csv"
    price_cache_present = price_cache_path.exists()
    action = "WOULD_UPDATE" if price_cache_present else "WOULD_CREATE"
    dryrun_ok = not blockers
    return dryrun_ok, ";".join(blockers), {
        "ticker": ticker,
        "source_normalized_file": source_path.as_posix(),
        "target_price_cache_file": price_cache_path.as_posix(),
        "action": action,
        "row_count": row_count,
        "min_date": min_date,
        "max_date": max_date,
        "latest_close": latest_close,
        "latest_volume": latest_volume,
        "dryrun_status": "DRYRUN_PASS" if dryrun_ok else "DRYRUN_BLOCKED",
        "blocker": ";".join(blockers),
        "current_last_scan_status": current_scan_status,
        "current_last_success_scan_date": get_field(ledger_row, "last_success_scan_date"),
        "would_set_last_scan_status": "SUCCESS_LOCAL_PRICE_FULL_HISTORY",
        "would_set_last_success_scan_date": dt.date.today().isoformat(),
        "would_set_last_attempt_scan_timestamp": dt.datetime.now().replace(microsecond=0).isoformat(),
        "file_exists": str(file_exists).upper(),
        "readable": str(readable).upper(),
        "required_columns_present": str(required_ok).upper(),
        "date_parse_ok": str(date_parse_ok).upper(),
        "duplicate_date_count": duplicate_count,
        "null_close_count": null_close_count,
        "rolling_ledger_present": str(ledger_present).upper(),
        "rolling_ledger_current_never_success": str(bool(ledger_present and to_int(get_field(ledger_row, "success_scan_count")) <= 0 and not non_null(get_field(ledger_row, "last_success_scan_date")))).upper(),
        "price_cache_present": str(price_cache_present).upper(),
    }


def metric_row(metric: str, value: object, expected: object, notes: str = "") -> Dict[str, object]:
    return {
        "metric": metric,
        "value": value,
        "expected": expected,
        "status": "OK" if str(value) == str(expected) else "WARN",
        "notes": notes,
    }


def render_report(values: Dict[str, object], warnings: List[str], validation_rows: List[Dict[str, object]], price_plan_rows: List[Dict[str, object]]) -> str:
    warning_lines = "\n".join(f"- {line}" for line in warnings) if warnings else "- None."
    pass_lines = "\n".join(f"- {row['ticker']}: {row['dryrun_status']} -> {row['action']}" for row in price_plan_rows)
    return "\n".join(
        [
            "# V18.25A-R27C Controlled Partial-Mature Integration Dry Run",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27B_STATUS: {values['R27B_STATUS']}",
            "",
            "## Dry Run",
            "",
            f"- DRYRUN_CANDIDATE_COUNT: {values['DRYRUN_CANDIDATE_COUNT']}",
            f"- EXPECTED_TICKER_MATCH: {values['EXPECTED_TICKER_MATCH']}",
            f"- DRYRUN_PASS_COUNT: {values['DRYRUN_PASS_COUNT']}",
            f"- DRYRUN_BLOCKED_COUNT: {values['DRYRUN_BLOCKED_COUNT']}",
            f"- PRICE_CACHE_DRYRUN_CREATE_COUNT: {values['PRICE_CACHE_DRYRUN_CREATE_COUNT']}",
            f"- PRICE_CACHE_DRYRUN_UPDATE_COUNT: {values['PRICE_CACHE_DRYRUN_UPDATE_COUNT']}",
            f"- ROLLING_LEDGER_DRYRUN_UPDATE_COUNT: {values['ROLLING_LEDGER_DRYRUN_UPDATE_COUNT']}",
            f"- R27D_APPLY_RECOMMENDED: {values['R27D_APPLY_RECOMMENDED']}",
            "",
            "## Candidate Plan",
            "",
            pass_lines if pass_lines else "- None.",
            "",
            "## Warnings",
            "",
            warning_lines,
            "",
            "## Guardrails",
            "",
            f"- OFFICIAL_INTEGRATION_ALLOWED_NEXT: {values['OFFICIAL_INTEGRATION_ALLOWED_NEXT']}",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- EXTERNAL_FETCH_EXECUTED: {values['EXTERNAL_FETCH_EXECUTED']}",
            f"- BACKTEST_EXECUTED: {values['BACKTEST_EXECUTED']}",
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27C_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    price_before = tree_sig(root / "state" / "v18" / "price_cache")
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")

    required_paths = [root / R27B_CANDIDATES, root / LEDGER]
    required_errors: List[str] = []
    for path in required_paths:
        if not path.exists():
            required_errors.append(f"missing required input: {path}")

    r27b_status = read_optional_status(root / R27B_READ_FIRST)
    candidate_rows, candidate_fields, candidate_err = load_required_csv(root / R27B_CANDIDATES)
    policy_rows, policy_fields, policy_err = load_required_csv(root / R27B_POLICY)
    ledger_rows, ledger_fields, ledger_err = load_required_csv(root / LEDGER)
    if candidate_err:
        required_errors.append(f"R27B candidates {candidate_err}")
    if ledger_err:
        required_errors.append(f"rolling ledger {ledger_err}")
    if policy_err:
        warnings_policy = f"R27B policy file {policy_err}"
    else:
        warnings_policy = ""

    warnings: List[str] = []
    if r27b_status and r27b_status != R27B_EXPECTED_STATUS:
        warnings.append(f"R27B status is {r27b_status}, expected {R27B_EXPECTED_STATUS}.")
    if not r27b_status:
        warnings.append("R27B status line was not available.")
    if len(candidate_rows) != 2:
        warnings.append(f"candidate count is {len(candidate_rows)} not 2.")
    candidate_tickers = [norm_ticker(get_field(row, "ticker")) for row in candidate_rows]
    if set(candidate_tickers) != EXPECTED_TICKERS:
        warnings.append(f"candidate tickers are {','.join(sorted(set(candidate_tickers)))} not TLN,RDDT.")
    if warnings_policy:
        warnings.append(warnings_policy)

    ledger_by_ticker = {norm_ticker(get_field(row, "ticker")): row for row in ledger_rows}
    plan_rows: List[Dict[str, object]] = []
    validation_rows: List[Dict[str, object]] = []
    mature_pass_count = 0
    blocked_count = 0
    create_count = 0
    update_count = 0
    ledger_update_count = 0

    for row in candidate_rows:
        ticker = norm_ticker(get_field(row, "ticker"))
        source_path = root / "data" / "v18" / "staged_backfill" / "V18_25A_R23B_MISSING_CACHE" / "normalized" / f"{ticker}.csv"
        ledger_row = ledger_by_ticker.get(ticker, {})
        ok, blocker, payload = row_passes_dryrun(row, ticker, source_path, ledger_row, root)
        plan_rows.append(payload)
        validation_rows.append(
            {
                "ticker": ticker,
                "source_normalized_file": payload["source_normalized_file"],
                "target_price_cache_file": payload["target_price_cache_file"],
                "file_exists": payload["file_exists"],
                "readable": payload["readable"],
                "required_columns_present": payload["required_columns_present"],
                "row_count": payload["row_count"],
                "min_date": payload["min_date"],
                "max_date": payload["max_date"],
                "latest_close": payload["latest_close"],
                "latest_volume": payload["latest_volume"],
                "date_parse_ok": payload["date_parse_ok"],
                "duplicate_date_count": payload["duplicate_date_count"],
                "null_close_count": payload["null_close_count"],
                "rolling_ledger_present": payload["rolling_ledger_present"],
                "rolling_ledger_current_never_success": payload["rolling_ledger_current_never_success"],
                "price_cache_present": payload["price_cache_present"],
                "dryrun_status": payload["dryrun_status"],
                "blocker": blocker,
            }
        )
        if ok:
            mature_pass_count += 1
            ledger_update_count += 1
            if payload["action"] == "WOULD_CREATE":
                create_count += 1
            else:
                update_count += 1
        else:
            blocked_count += 1
            if payload["action"] == "WOULD_CREATE":
                create_count += 1
            else:
                update_count += 1

    ledger_plan_rows = [
        {
            "ticker": row["ticker"],
            "current_last_scan_status": row["current_last_scan_status"],
            "current_last_success_scan_date": row["current_last_success_scan_date"],
            "would_set_last_scan_status": row["would_set_last_scan_status"],
            "would_set_last_success_scan_date": row["would_set_last_success_scan_date"],
            "would_set_last_attempt_scan_timestamp": row["would_set_last_attempt_scan_timestamp"],
            "dryrun_status": row["dryrun_status"],
        }
        for row in plan_rows
    ]

    expected_match = set(candidate_tickers) == EXPECTED_TICKERS and len(candidate_rows) == 2
    apply_recommended = mature_pass_count == 2 and blocked_count == 0 and expected_match and not required_errors

    status = STATUS_OK if apply_recommended else STATUS_WARN
    validation_fail_count = 0
    if required_errors:
        status = STATUS_FAIL_INPUTS
        validation_fail_count = 1

    write_csv(root / OUT_PRICE_PLAN, plan_rows, PRICE_PLAN_FIELDS)
    write_csv(root / OUT_LEDGER_PLAN, ledger_plan_rows, LEDGER_PLAN_FIELDS)
    write_csv(root / OUT_VALIDATION, validation_rows, VALIDATION_FIELDS)

    summary_rows = [
        metric_row("R27B_STATUS", r27b_status or "MISSING", R27B_EXPECTED_STATUS),
        metric_row("DRYRUN_CANDIDATE_COUNT", len(candidate_rows), 2),
        metric_row("EXPECTED_TICKER_MATCH", str(expected_match).upper(), "TRUE"),
        metric_row("DRYRUN_PASS_COUNT", mature_pass_count, 2),
        metric_row("DRYRUN_BLOCKED_COUNT", blocked_count, 0),
        metric_row("PRICE_CACHE_DRYRUN_CREATE_COUNT", create_count, 2),
        metric_row("PRICE_CACHE_DRYRUN_UPDATE_COUNT", update_count, 0),
        metric_row("ROLLING_LEDGER_DRYRUN_UPDATE_COUNT", ledger_update_count, 2),
        metric_row("R27D_APPLY_RECOMMENDED", str(apply_recommended).upper(), "TRUE"),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    price_modified = tree_sig(root / "state" / "v18" / "price_cache") != price_before
    ledger_modified = file_sig(root / LEDGER) != ledger_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    candidates_modified = tree_sig(root / "outputs" / "v18" / "candidates") != candidates_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or candidates_modified
    if forbidden_modified:
        status = STATUS_FAIL_FORBIDDEN
        validation_fail_count = max(validation_fail_count, 1)

    if status == STATUS_OK and warnings:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27B_STATUS": r27b_status or "MISSING",
        "DRYRUN_CANDIDATE_COUNT": len(candidate_rows),
        "EXPECTED_TICKER_MATCH": str(expected_match).upper(),
        "DRYRUN_PASS_COUNT": mature_pass_count,
        "DRYRUN_BLOCKED_COUNT": blocked_count,
        "PRICE_CACHE_DRYRUN_CREATE_COUNT": create_count,
        "PRICE_CACHE_DRYRUN_UPDATE_COUNT": update_count,
        "ROLLING_LEDGER_DRYRUN_UPDATE_COUNT": ledger_update_count,
        "R27D_APPLY_RECOMMENDED": str(apply_recommended).upper(),
        "OFFICIAL_INTEGRATION_ALLOWED_NEXT": "FALSE",
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "CANDIDATES_MODIFIED": str(candidates_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R27D: review the dry-run plan for TLN and RDDT, then apply only if no new blockers are introduced; keep official integration disabled.",
    }

    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, warnings, validation_rows, plan_rows))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if validation_fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
