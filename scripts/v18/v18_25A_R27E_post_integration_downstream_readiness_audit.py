from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27E_POST_INTEGRATION_DOWNSTREAM_READINESS_READY"
STATUS_WARN = "WARN_V18_25A_R27E_DOWNSTREAM_READINESS_REVIEW_NEEDED"
STATUS_FAIL_INPUTS = "FAIL_V18_25A_R27E_REQUIRED_INPUTS_MISSING_OR_UNREADABLE"
STATUS_FAIL_FORBIDDEN = "FAIL_V18_25A_R27E_FORBIDDEN_MODIFIED"

MODE = "READ_ONLY_POST_INTEGRATION_DOWNSTREAM_READINESS_AUDIT"

TARGET_TICKERS = ["RDDT", "TLN"]
R27D_READ_FIRST = "outputs/v18/ops/V18_25A_R27D_READ_FIRST.txt"
R27D_EXPECTED_STATUS = "OK_V18_25A_R27D_PARTIAL_MATURE_PRICE_CACHE_LEDGER_INTEGRATION_READY"

PRICE_CACHE_DIR = "state/v18/price_cache"
LEDGER_PATH = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
FACTOR_PATH = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_PATH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CANDIDATES_PATH = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"

OUT_DIR = "outputs/v18/coverage_resolution"
OUT_AUDIT = f"{OUT_DIR}/V18_25A_R27E_CURRENT_DOWNSTREAM_READINESS_AUDIT.csv"
OUT_RECHECK = f"{OUT_DIR}/V18_25A_R27E_CURRENT_TARGET_COVERAGE_RECHECK.csv"
OUT_GAP = f"{OUT_DIR}/V18_25A_R27E_CURRENT_FACTOR_TECHNICAL_GAP_AUDIT.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27E_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27E_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27E_CURRENT_POST_INTEGRATION_DOWNSTREAM_READINESS_REPORT.md"

PRICE_CACHE_REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}

AUDIT_FIELDS = [
    "ticker",
    "price_cache_present",
    "price_cache_row_count",
    "price_cache_min_date",
    "price_cache_max_date",
    "price_cache_latest_close",
    "price_cache_latest_volume",
    "rolling_ledger_present",
    "rolling_last_scan_status",
    "rolling_last_success_scan_date",
    "factor_present",
    "technical_present",
    "ranked_candidate_present",
    "readiness_status",
    "recommended_next_action",
]

RECHECK_FIELDS = [
    "ticker",
    "price_cache_present",
    "price_cache_row_count",
    "rolling_ledger_success",
    "rolling_last_success_scan_date",
    "coverage_recheck_status",
    "notes",
]

GAP_FIELDS = [
    "ticker",
    "factor_present",
    "technical_present",
    "ranked_candidate_present",
    "gap_classification",
    "gap_reason",
    "recommended_next_action",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27D_STATUS",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "PRICE_CACHE_PRESENT_COUNT",
    "ROLLING_LEDGER_SUCCESS_COUNT",
    "FACTOR_PRESENT_COUNT",
    "TECHNICAL_PRESENT_COUNT",
    "RANKED_CANDIDATE_PRESENT_COUNT",
    "READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD_COUNT",
    "BLOCKED_COUNT",
    "TOTAL_LEDGER_ROWS",
    "COVERED_WITHIN_5D",
    "NEVER_SUCCESS_COUNT",
    "STALE_COUNT",
    "REMAINING_COUNT",
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


def changed_keys(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    return [key for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)]


def norm_key(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def find_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    by_norm = {norm_key(field): field for field in fields}
    for alias in aliases:
        hit = by_norm.get(norm_key(alias))
        if hit:
            return hit
    return None


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value != "":
            return value
    return ""


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def load_price_cache(path: Path) -> Tuple[bool, bool, int, str, str, str, str, List[str]]:
    rows, fields = read_csv(path)
    readable = bool(fields)
    field_set = {str(field).strip().lower() for field in fields}
    required_ok = PRICE_CACHE_REQUIRED_COLUMNS.issubset(field_set)
    dates: List[dt.date] = []
    latest_close = ""
    latest_volume = ""
    errors: List[str] = []
    if not path.exists():
        errors.append("missing")
    if not readable:
        errors.append("unreadable")
    if not required_ok:
        errors.append("required_columns_missing")
    for row in rows:
        parsed = parse_date(row.get("date", ""))
        if parsed:
            dates.append(parsed)
    if rows:
        latest = max(rows, key=lambda item: str(item.get("date", "") or ""))
        latest_close = str(latest.get("close", "") or "").strip()
        latest_volume = str(latest.get("volume", "") or "").strip()
    return (
        path.exists(),
        readable and required_ok,
        len(rows),
        min(dates).isoformat() if dates else "",
        max(dates).isoformat() if dates else "",
        latest_close,
        latest_volume,
        errors,
    )


def locate_row(rows: List[Dict[str, str]], fields: Sequence[str], ticker: str) -> Tuple[bool, Dict[str, str]]:
    ticker_col = find_col(fields, ["ticker", "symbol", "yf_ticker"])
    if not ticker_col:
        return False, {}
    for row in rows:
        if norm_ticker(row.get(ticker_col)) == ticker:
            return True, row
    return False, {}


def scan_presence(path: Path, ticker: str, alias_fields: Sequence[str]) -> Tuple[bool, int]:
    rows, fields = read_csv(path)
    if not rows or not fields:
        return False, 0
    ticker_col = find_col(fields, alias_fields)
    if not ticker_col:
        return False, 0
    count = sum(1 for row in rows if norm_ticker(row.get(ticker_col)) == ticker)
    return count > 0, count


def ledger_status(root: Path, ticker: str, run_date: dt.date) -> Tuple[bool, Dict[str, str], bool, bool]:
    rows, fields = read_csv(root / LEDGER_PATH)
    ticker_col = find_col(fields, ["ticker", "symbol"])
    status_col = find_col(fields, ["last_scan_status", "scan_status", "status"])
    success_date_col = find_col(fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    if not ticker_col:
        return False, {}, False, False
    for row in rows:
        if norm_ticker(row.get(ticker_col)) != ticker:
            continue
        status = get_field(row, status_col or "", "last_scan_status", "scan_status", "status")
        success_date = get_field(row, success_date_col or "", "last_success_scan_date", "last_success_date", "latest_success_date")
        success_ok = status == "SUCCESS_LOCAL_PRICE_FULL_HISTORY" and success_date == run_date.isoformat()
        present = True
        return present, row, success_ok, success_date == run_date.isoformat()
    return False, {}, False, False


def build_price_audit_row(root: Path, ticker: str, price_info: Tuple[bool, bool, int, str, str, str, str, List[str]], ledger_row: Dict[str, str], factor_present: bool, technical_present: bool, candidate_present: bool) -> Dict[str, object]:
    present, readable, row_count, min_date, max_date, latest_close, latest_volume, errors = price_info
    ledger_present = bool(ledger_row)
    ledger_status = get_field(ledger_row, "last_scan_status", "scan_status", "status")
    ledger_success_date = get_field(ledger_row, "last_success_scan_date", "last_success_date", "latest_success_date")
    if not present or not readable or not ledger_present or ledger_status != "SUCCESS_LOCAL_PRICE_FULL_HISTORY" or not non_null(ledger_success_date):
        readiness = "BLOCKED"
        next_action = "REVIEW_R27D_POST_APPLY_VALIDATION"
    elif factor_present and technical_present:
        readiness = "ALREADY_DOWNSTREAM_READY"
        next_action = "R27F_STAGED_FACTOR_TECHNICAL_BUILD_FOR_TLN_RDDT"
    else:
        readiness = "READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD"
        next_action = "R27F_STAGED_FACTOR_TECHNICAL_BUILD_FOR_TLN_RDDT"
    return {
        "ticker": ticker,
        "price_cache_present": str(present and readable).upper(),
        "price_cache_row_count": row_count,
        "price_cache_min_date": min_date,
        "price_cache_max_date": max_date,
        "price_cache_latest_close": latest_close,
        "price_cache_latest_volume": latest_volume,
        "rolling_ledger_present": str(ledger_present).upper(),
        "rolling_last_scan_status": ledger_status,
        "rolling_last_success_scan_date": ledger_success_date,
        "factor_present": str(factor_present).upper(),
        "technical_present": str(technical_present).upper(),
        "ranked_candidate_present": str(candidate_present).upper(),
        "readiness_status": readiness,
        "recommended_next_action": next_action,
    }


def metric_row(metric: str, value: object, expected: object, notes: str = "") -> Dict[str, object]:
    return {"metric": metric, "value": value, "expected": expected, "status": "OK" if str(value) == str(expected) else "WARN", "notes": notes}


def render_report(values: Dict[str, object], warnings: List[str], audit_rows: List[Dict[str, object]]) -> str:
    warning_text = "\n".join(f"- {item}" for item in warnings) if warnings else "- None."
    audit_text = "\n".join(f"- {row['ticker']}: {row['readiness_status']} -> {row['recommended_next_action']}" for row in audit_rows)
    return "\n".join(
        [
            "# V18.25A-R27E Post-Integration Downstream Readiness Audit",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27D_STATUS: {values['R27D_STATUS']}",
            "",
            "## Readiness",
            "",
            audit_text if audit_text else "- None.",
            "",
            "## Coverage",
            "",
            f"- TOTAL_LEDGER_ROWS: {values['TOTAL_LEDGER_ROWS']}",
            f"- COVERED_WITHIN_5D: {values['COVERED_WITHIN_5D']}",
            f"- NEVER_SUCCESS_COUNT: {values['NEVER_SUCCESS_COUNT']}",
            f"- STALE_COUNT: {values['STALE_COUNT']}",
            f"- REMAINING_COUNT: {values['REMAINING_COUNT']}",
            "",
            "## Warnings",
            "",
            warning_text,
            "",
            "## Guardrails",
            "",
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


def ledger_coverage(root: Path, run_date: dt.date) -> Dict[str, int]:
    rows, fields = read_csv(root / LEDGER_PATH)
    ticker_col = find_col(fields, ["ticker", "symbol"])
    success_count_col = find_col(fields, ["success_scan_count"])
    success_date_col = find_col(fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    artifact = 0
    covered = never = stale = 0
    seen: set[str] = set()
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col or ""))
        if ticker == "TICKERS":
            artifact += 1
        if ticker in seen:
            continue
        seen.add(ticker)
        success_count = to_int(row.get(success_count_col or ""))
        success_date = parse_date(row.get(success_date_col or ""))
        if success_count <= 0 or success_date is None:
            never += 1
        elif 0 <= (run_date - success_date).days <= 5:
            covered += 1
        else:
            stale += 1
    return {
        "total": len(rows),
        "covered": covered,
        "never": never,
        "stale": stale,
        "remaining": never + stale,
        "artifact": artifact,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27E_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_date = dt.date.today()

    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / LEDGER_PATH)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")
    official_before = tree_sig(root / "outputs" / "v18" / "official_decisions")

    required_paths = [root / R27D_READ_FIRST, root / PRICE_CACHE_DIR / "RDDT.csv", root / PRICE_CACHE_DIR / "TLN.csv", root / LEDGER_PATH]
    required_errors = [f"missing required input: {path}" for path in required_paths if not path.exists()]

    r27d_status = read_first_value(root / R27D_READ_FIRST, "STATUS")
    price_write_success = to_int(read_first_value(root / R27D_READ_FIRST, "PRICE_CACHE_WRITE_SUCCESS_COUNT"))
    ledger_write_success = to_int(read_first_value(root / R27D_READ_FIRST, "ROLLING_LEDGER_UPDATE_SUCCESS_COUNT"))
    post_validate_success = to_int(read_first_value(root / R27D_READ_FIRST, "POST_VALIDATE_SUCCESS_COUNT"))
    forbidden_flag = read_first_value(root / R27D_READ_FIRST, "FORBIDDEN_MODIFIED")

    warnings: List[str] = []
    if r27d_status != R27D_EXPECTED_STATUS:
        warnings.append(f"R27D status is {r27d_status or 'MISSING'}, expected {R27D_EXPECTED_STATUS}.")
    if price_write_success != 2:
        warnings.append(f"R27D price cache write success count is {price_write_success}, expected 2.")
    if ledger_write_success != 2:
        warnings.append(f"R27D rolling ledger update success count is {ledger_write_success}, expected 2.")
    if post_validate_success != 2:
        warnings.append(f"R27D post-apply validation success count is {post_validate_success}, expected 2.")
    if forbidden_flag != "FALSE":
        warnings.append(f"R27D forbidden flag is {forbidden_flag or 'MISSING'}, expected FALSE.")

    price_meta: Dict[str, Tuple[bool, bool, int, str, str, str, str, List[str]]] = {}
    audit_rows: List[Dict[str, object]] = []
    recheck_rows: List[Dict[str, object]] = []
    gap_rows: List[Dict[str, object]] = []
    ready_count = 0
    blocked_count = 0
    price_present_count = 0
    ledger_success_count = 0
    factor_present_count = 0
    technical_present_count = 0
    candidate_present_count = 0

    factor_rows, factor_fields = read_csv(root / FACTOR_PATH)
    tech_rows, tech_fields = read_csv(root / TECH_PATH)
    candidate_rows, candidate_fields = read_csv(root / CANDIDATES_PATH)
    for ticker in TARGET_TICKERS:
        price_info = load_price_cache(root / PRICE_CACHE_DIR / f"{ticker}.csv")
        price_meta[ticker] = price_info
        ledger_present, ledger_row, ledger_success, ledger_date_match = ledger_status(root, ticker, run_date)
        factor_present, factor_count = scan_presence(root / FACTOR_PATH, ticker, ["ticker"])
        technical_present, technical_count = scan_presence(root / TECH_PATH, ticker, ["ticker", "yf_ticker"])
        candidate_present, candidate_count = scan_presence(root / CANDIDATES_PATH, ticker, ["ticker"])
        if price_info[0] and price_info[1]:
            price_present_count += 1
        if ledger_success:
            ledger_success_count += 1
        if factor_present:
            factor_present_count += 1
        if technical_present:
            technical_present_count += 1
        if candidate_present:
            candidate_present_count += 1
        row = build_price_audit_row(root, ticker, price_info, ledger_row, factor_present, technical_present, candidate_present)
        audit_rows.append(row)
        if row["readiness_status"] == "READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD":
            ready_count += 1
        elif row["readiness_status"] == "BLOCKED":
            blocked_count += 1
        gap_reason = []
        if not row["price_cache_present"]:
            gap_reason.append("price_cache_missing_or_unreadable")
        if row["rolling_ledger_present"] != "TRUE":
            gap_reason.append("rolling_ledger_missing")
        if row["rolling_last_scan_status"] != "SUCCESS_LOCAL_PRICE_FULL_HISTORY":
            gap_reason.append("rolling_last_scan_status_not_success")
        if row["rolling_last_success_scan_date"] != run_date.isoformat():
            gap_reason.append("rolling_last_success_scan_date_not_current")
        if row["factor_present"] != "TRUE":
            gap_reason.append("factor_missing")
        if row["technical_present"] != "TRUE":
            gap_reason.append("technical_missing")
        if row["ranked_candidate_present"] != "TRUE":
            gap_reason.append("ranked_candidate_missing")
        gap_rows.append(
            {
                "ticker": ticker,
                "factor_present": row["factor_present"],
                "technical_present": row["technical_present"],
                "ranked_candidate_present": row["ranked_candidate_present"],
                "gap_classification": row["readiness_status"],
                "gap_reason": ";".join(gap_reason),
                "recommended_next_action": row["recommended_next_action"],
            }
        )
        recheck_rows.append(
            {
                "ticker": ticker,
                "price_cache_present": row["price_cache_present"],
                "price_cache_row_count": row["price_cache_row_count"],
                "rolling_ledger_success": str(ledger_success).upper(),
                "rolling_last_success_scan_date": row["rolling_last_success_scan_date"],
                "coverage_recheck_status": "PASS" if price_info[0] and price_info[1] and ledger_success else "FAIL",
                "notes": "" if price_info[0] and price_info[1] and ledger_success else "Recheck failed base readiness checks.",
            }
        )

    coverage = ledger_coverage(root, run_date)
    warn_counts: List[str] = []
    if coverage["total"] != 323:
        warn_counts.append(f"total ledger rows are {coverage['total']} not 323.")
    if coverage["covered"] != 303:
        warn_counts.append(f"covered within 5D is {coverage['covered']} not 303.")
    if coverage["never"] != 20:
        warn_counts.append(f"never-success count is {coverage['never']} not 20.")
    if coverage["stale"] != 0:
        warn_counts.append(f"stale count is {coverage['stale']} not 0.")
    if coverage["remaining"] != 20:
        warn_counts.append(f"remaining count is {coverage['remaining']} not 20.")
    warnings.extend(warn_counts)

    if required_errors:
        status = STATUS_FAIL_INPUTS
        validation_fail_count = 1
    else:
        validation_fail_count = 0
        if price_before != tree_sig(root / PRICE_CACHE_DIR) or ledger_before != file_sig(root / LEDGER_PATH) or factor_before != tree_sig(root / "outputs" / "v18" / "factor_pack") or tech_before != tree_sig(root / "outputs" / "v18" / "technical_timing") or candidates_before != tree_sig(root / "outputs" / "v18" / "candidates") or official_before != tree_sig(root / "outputs" / "v18" / "official_decisions"):
            status = STATUS_FAIL_FORBIDDEN
            validation_fail_count = 1
        elif blocked_count > 0:
            status = STATUS_WARN
        elif warnings:
            status = STATUS_WARN
        else:
            status = STATUS_OK

    target_tickers_text = ",".join(TARGET_TICKERS)
    target_ready_count = ready_count
    if ready_count == 2 and blocked_count == 0:
        next_step = "R27F_STAGED_FACTOR_TECHNICAL_BUILD_FOR_TLN_RDDT"
    elif blocked_count > 0:
        next_step = "REVIEW_R27D_POST_APPLY_VALIDATION"
    else:
        next_step = "R27F_STAGED_FACTOR_TECHNICAL_BUILD_FOR_TLN_RDDT"

    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(root / OUT_RECHECK, recheck_rows, RECHECK_FIELDS)
    write_csv(root / OUT_GAP, gap_rows, GAP_FIELDS)

    summary_rows = [
        metric_row("R27D_STATUS", r27d_status or "MISSING", R27D_EXPECTED_STATUS),
        metric_row("TARGET_TICKER_COUNT", len(TARGET_TICKERS), 2),
        metric_row("PRICE_CACHE_PRESENT_COUNT", price_present_count, 2),
        metric_row("ROLLING_LEDGER_SUCCESS_COUNT", ledger_success_count, 2),
        metric_row("FACTOR_PRESENT_COUNT", factor_present_count, 0),
        metric_row("TECHNICAL_PRESENT_COUNT", technical_present_count, 0),
        metric_row("RANKED_CANDIDATE_PRESENT_COUNT", candidate_present_count, 0),
        metric_row("READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD_COUNT", target_ready_count, 2),
        metric_row("BLOCKED_COUNT", blocked_count, 0),
        metric_row("TOTAL_LEDGER_ROWS", coverage["total"], 323),
        metric_row("COVERED_WITHIN_5D", coverage["covered"], 303),
        metric_row("NEVER_SUCCESS_COUNT", coverage["never"], 20),
        metric_row("STALE_COUNT", coverage["stale"], 0),
        metric_row("REMAINING_COUNT", coverage["remaining"], 20),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    price_after = tree_sig(root / PRICE_CACHE_DIR)
    ledger_after = file_sig(root / LEDGER_PATH)
    factor_after = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_after = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_after = tree_sig(root / "outputs" / "v18" / "candidates")
    official_after = tree_sig(root / "outputs" / "v18" / "official_decisions")
    price_modified = price_after != price_before
    ledger_modified = ledger_after != ledger_before
    factor_modified = factor_after != factor_before
    tech_modified = tech_after != tech_before
    candidates_modified = candidates_after != candidates_before
    official_modified = official_after != official_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or candidates_modified or official_modified
    if forbidden_modified:
        status = STATUS_FAIL_FORBIDDEN
        validation_fail_count = 1

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27D_STATUS": r27d_status or "MISSING",
        "TARGET_TICKER_COUNT": len(TARGET_TICKERS),
        "TARGET_TICKERS": target_tickers_text,
        "PRICE_CACHE_PRESENT_COUNT": price_present_count,
        "ROLLING_LEDGER_SUCCESS_COUNT": ledger_success_count,
        "FACTOR_PRESENT_COUNT": factor_present_count,
        "TECHNICAL_PRESENT_COUNT": technical_present_count,
        "RANKED_CANDIDATE_PRESENT_COUNT": candidate_present_count,
        "READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD_COUNT": target_ready_count,
        "BLOCKED_COUNT": blocked_count,
        "TOTAL_LEDGER_ROWS": coverage["total"],
        "COVERED_WITHIN_5D": coverage["covered"],
        "NEVER_SUCCESS_COUNT": coverage["never"],
        "STALE_COUNT": coverage["stale"],
        "REMAINING_COUNT": coverage["remaining"],
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
        "NEXT_RECOMMENDED_STEP": next_step,
    }

    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, warnings, audit_rows))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FAIL_INPUTS or status == STATUS_FAIL_FORBIDDEN else 0


if __name__ == "__main__":
    raise SystemExit(main())
