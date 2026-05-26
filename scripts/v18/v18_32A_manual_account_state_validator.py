from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_32A_MANUAL_ACCOUNT_STATE_VALIDATOR_DRY_RUN_READY"
STATUS_OK = "OK_V18_32A_MANUAL_ACCOUNT_STATE_VALIDATED"
STATUS_WARN_TEMPLATE = "WARN_V18_32A_MANUAL_ACCOUNT_STATE_TEMPLATE_REVIEW_NEEDED"
STATUS_WARN = "WARN_V18_32A_MANUAL_ACCOUNT_STATE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_32A_MANUAL_ACCOUNT_STATE_VALIDATION_FAILED"
MODE_LIVE = "MANUAL_ACCOUNT_STATE_VALIDATOR"
MODE_DRY = "MANUAL_ACCOUNT_STATE_VALIDATOR_DRY_RUN"

ACCOUNT_STATE = "state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE.csv"
ACCOUNT_TEMPLATE = "state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE_TEMPLATE.csv"
ACCOUNT_AWARE = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"
COST_ADJUSTED = "outputs/v18/execution/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
R31F_READ_FIRST = "outputs/v18/ops/V18_31F_READ_FIRST.txt"
R31D_READ_FIRST = "outputs/v18/ops/V18_31D_READ_FIRST.txt"

OUT_VALIDATION = "outputs/v18/account/V18_32A_MANUAL_ACCOUNT_STATE_VALIDATION.csv"
OUT_NORMALIZED = "outputs/v18/account/V18_32A_MANUAL_ACCOUNT_HOLDINGS_NORMALIZED.csv"
OUT_CURRENT_GUIDE = "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md"
OUT_REPORT = "outputs/v18/read_center/V18_32A_MANUAL_ACCOUNT_STATE_VALIDATION_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_32A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_32A_MANUAL_ACCOUNT_STATE_VALIDATION_SUMMARY.csv"
OUT_ERROR = "outputs/v18/read_center/V18_32A_MANUAL_ACCOUNT_STATE_VALIDATION_ERROR.md"

REQUIRED_COLUMNS = [
    "account_id",
    "as_of_date",
    "account_total_value_usd",
    "cash_usd",
    "ticker",
    "shares",
    "avg_cost_usd",
    "current_price_usd",
    "market_value_usd",
    "position_pct",
    "primary_theme",
    "position_type",
    "notes",
]

VALIDATION_FIELDS = [
    "run_id",
    "check_name",
    "severity",
    "status",
    "affected_ticker",
    "message",
    "suggested_fix",
]

NORMALIZED_FIELDS = [
    "account_id",
    "as_of_date",
    "ticker",
    "shares",
    "avg_cost_usd",
    "current_price_usd",
    "normalized_market_value_usd",
    "normalized_position_pct",
    "primary_theme",
    "position_type",
    "row_quality",
    "row_warnings",
    "computed_unrealized_pnl_pct",
    "generated_at",
    "run_id",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "ACCOUNT_STATE_FILE",
    "ACCOUNT_STATE_EXISTS",
    "ACCOUNT_STATE_MODE",
    "ACCOUNT_STATE_QUALITY",
    "ACCOUNT_ID",
    "AS_OF_DATE",
    "ACCOUNT_TOTAL_VALUE_USD",
    "CASH_USD",
    "CASH_RESERVE_PCT",
    "CASH_RESERVE_REQUIRED_USD",
    "AVAILABLE_CASH_AFTER_RESERVE_USD",
    "HOLDING_ROW_COUNT",
    "NON_CASH_POSITION_COUNT",
    "CASH_ROW_COUNT",
    "DUPLICATE_TICKER_COUNT",
    "MISSING_REQUIRED_COLUMN_COUNT",
    "FAIL_CHECK_COUNT",
    "WARN_CHECK_COUNT",
    "INFO_CHECK_COUNT",
    "TEMPLATE_EMPTY_ACCOUNT",
    "NORMALIZED_HOLDINGS_ROWS",
    "R31D_ACCOUNT_TOTAL_VALUE_USD",
    "R31D_CASH_USD",
    "R31D_ACCOUNT_STATE_MODE",
    "R31D_ACCOUNT_STATE_QUALITY",
    "ACCOUNT_STATE_CHANGED_RERUN_R31D_REQUIRED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "account_state_file",
    "account_state_mode",
    "account_state_quality",
    "account_total_value_usd",
    "cash_usd",
    "available_cash_after_reserve_usd",
    "holding_row_count",
    "non_cash_position_count",
    "duplicate_ticker_count",
    "missing_required_column_count",
    "fail_check_count",
    "warn_check_count",
    "template_empty_account",
    "account_state_changed_rerun_r31d_required",
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


def money(value: float) -> str:
    return f"{value:.2f}"


def pct(value: float) -> str:
    return f"{value:.4f}"


def to_float(value: object, default: float = 0.0) -> float:
    text = norm(value).replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


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
    raise RuntimeError(f"Unable to read CSV: {path}")


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


def row_count(path: Path) -> int:
    rows, _fields = read_csv(path)
    return len(rows)


def add_check(checks: List[Dict[str, object]], run_id: str, name: str, severity: str, status: str, ticker: str, message: str, fix: str) -> None:
    checks.append({
        "run_id": run_id,
        "check_name": name,
        "severity": severity,
        "status": status,
        "affected_ticker": ticker,
        "message": message,
        "suggested_fix": fix,
    })


def is_cash_row(row: Dict[str, str]) -> bool:
    return upper(row.get("ticker")) == "CASH_USD" or upper(row.get("position_type")) == "CASH"


def ensure_account_files(root: Path, account_state_path: Path, args: argparse.Namespace, today: str) -> bool:
    template_path = root / ACCOUNT_TEMPLATE
    if not template_path.exists():
        write_csv(template_path, [], REQUIRED_COLUMNS)
    if account_state_path.exists():
        return False
    cash = args.cash_usd if args.cash_usd is not None else args.account_size_usd
    starter = {
        "account_id": "MANUAL_DEFAULT",
        "as_of_date": today,
        "account_total_value_usd": money(args.account_size_usd),
        "cash_usd": money(cash),
        "ticker": "CASH_USD",
        "shares": "0",
        "avg_cost_usd": "0",
        "current_price_usd": "1",
        "market_value_usd": "0",
        "position_pct": "0",
        "primary_theme": "CASH",
        "position_type": "CASH",
        "notes": "TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA",
    }
    write_csv(account_state_path, [starter], REQUIRED_COLUMNS)
    return True


def md_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 25) -> str:
    if not rows:
        return "_None._\n"
    selected = list(rows)[:limit]
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    body = ["| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |" for row in selected]
    suffix = [f"\n_Showing {len(selected)} of {len(rows)} rows._"] if len(rows) > len(selected) else []
    return "\n".join([header, sep] + body + suffix) + "\n"


def first_valid_account_row(rows: Sequence[Dict[str, str]]) -> Dict[str, str]:
    for row in rows:
        if to_float(row.get("account_total_value_usd"), -1) > 0 and to_float(row.get("cash_usd"), -1) >= 0:
            return row
    return rows[0] if rows else {}


def validate_account(root: Path, args: argparse.Namespace, run_id: str, generated_at: str) -> Dict[str, object]:
    account_state_path = Path(args.account_state_file).resolve() if args.account_state_file else root / ACCOUNT_STATE
    account_state_path.parent.mkdir(parents=True, exist_ok=True)
    account_existed_before = account_state_path.exists()
    created_starter = ensure_account_files(root, account_state_path, args, generated_at[:10])
    rows, fields = read_csv(account_state_path)
    checks: List[Dict[str, object]] = []
    normalized: List[Dict[str, object]] = []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in fields]
    if missing_columns:
        add_check(checks, run_id, "REQUIRED_COLUMNS", "FAIL", "FAIL", "", f"Missing required columns: {', '.join(missing_columns)}", "Restore the V18 manual account schema before relying on account-aware constraints.")
    else:
        add_check(checks, run_id, "REQUIRED_COLUMNS", "INFO", "PASS", "", "Manual account file contains all required columns.", "No action required.")

    account_row = first_valid_account_row(rows)
    account_id = norm(account_row.get("account_id")) or "MANUAL_DEFAULT"
    as_of_date = norm(account_row.get("as_of_date")) or generated_at[:10]
    account_total = to_float(account_row.get("account_total_value_usd"), args.account_size_usd if created_starter else -1.0)
    cash_default = args.cash_usd if args.cash_usd is not None else account_total
    cash = to_float(account_row.get("cash_usd"), cash_default if created_starter else -1.0)
    reserve = account_total * args.cash_reserve_pct / 100.0 if account_total > 0 else 0.0
    available_cash = cash - reserve if account_total > 0 and cash >= 0 else 0.0

    if account_total <= 0:
        add_check(checks, run_id, "ACCOUNT_TOTAL_VALUE_USD", "FAIL", "FAIL", "", "account_total_value_usd must be numeric and greater than zero.", "Enter the manually verified total account value in USD.")
    else:
        add_check(checks, run_id, "ACCOUNT_TOTAL_VALUE_USD", "INFO", "PASS", "", f"account_total_value_usd = {money(account_total)}.", "No action required.")
    if cash < 0:
        add_check(checks, run_id, "CASH_USD", "FAIL", "FAIL", "", "cash_usd must be numeric and greater than or equal to zero.", "Enter the manually verified cash balance in USD.")
    elif account_total > 0 and cash > account_total * 1.5:
        add_check(checks, run_id, "CASH_USD", "WARN", "WARN", "", "cash_usd is more than 150% of account_total_value_usd.", "Verify cash and total account value; update one or both values if stale.")
    else:
        add_check(checks, run_id, "CASH_USD", "INFO", "PASS", "", f"cash_usd = {money(cash)}.", "No action required.")

    cash_rows = [row for row in rows if is_cash_row(row)]
    non_cash_rows = [row for row in rows if not is_cash_row(row)]
    template_empty = bool(rows) and len(non_cash_rows) == 0 and any("TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA" in upper(row.get("notes")) for row in rows)
    if created_starter or template_empty:
        add_check(checks, run_id, "TEMPLATE_EMPTY_ACCOUNT", "WARN", "WARN", "CASH_USD", "Manual account file is still the template/empty cash-only assumption.", "Before relying on account-aware constraints, replace the template row values and add real manually verified holdings.")

    tickers = [upper(row.get("ticker")) for row in non_cash_rows if upper(row.get("ticker"))]
    duplicate_tickers = sorted([ticker for ticker, count in Counter(tickers).items() if count > 1])
    if duplicate_tickers:
        add_check(checks, run_id, "DUPLICATE_TICKERS", "WARN", "WARN", ", ".join(duplicate_tickers), f"Duplicate non-cash ticker rows: {', '.join(duplicate_tickers)}.", "Merge duplicate ticker rows into one manually verified holding row.")
    else:
        add_check(checks, run_id, "DUPLICATE_TICKERS", "INFO", "PASS", "", "No duplicate non-cash ticker rows detected.", "No action required.")

    non_cash_market_value = 0.0
    position_pct_sum = 0.0
    for row in rows:
        ticker = upper(row.get("ticker"))
        row_warnings: List[str] = []
        row_fail = False
        shares = to_float(row.get("shares"), -1.0)
        avg_cost = to_float(row.get("avg_cost_usd"), -1.0)
        price = to_float(row.get("current_price_usd"), -1.0)
        market_value_raw = to_float(row.get("market_value_usd"), -1.0)
        position_pct_raw = to_float(row.get("position_pct"), -1.0)
        theme = upper(row.get("primary_theme"))
        position_type = upper(row.get("position_type")) or ("CASH" if is_cash_row(row) else "MANUAL_HOLDING")

        if is_cash_row(row):
            normalized_market_value = cash if cash >= 0 else 0.0
            normalized_position_pct = (cash / account_total * 100.0) if account_total > 0 and cash >= 0 else 0.0
            normalized.append({
                "account_id": account_id,
                "as_of_date": as_of_date,
                "ticker": "CASH_USD",
                "shares": "0",
                "avg_cost_usd": "0.00",
                "current_price_usd": "1.00",
                "normalized_market_value_usd": money(normalized_market_value),
                "normalized_position_pct": pct(normalized_position_pct),
                "primary_theme": "CASH",
                "position_type": "CASH",
                "row_quality": "WARN_TEMPLATE_EMPTY_ACCOUNT" if template_empty else "OK",
                "row_warnings": "TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA" if template_empty else "",
                "computed_unrealized_pnl_pct": "0.0000",
                "generated_at": generated_at,
                "run_id": run_id,
            })
            continue

        if not ticker:
            row_fail = True
            row_warnings.append("MISSING_TICKER")
            add_check(checks, run_id, "HOLDING_TICKER", "FAIL", "FAIL", "", "Non-cash holding row has an empty ticker.", "Enter the ticker symbol or remove the row.")
        if shares < 0:
            row_fail = True
            row_warnings.append("INVALID_SHARES")
            add_check(checks, run_id, "HOLDING_SHARES", "FAIL", "FAIL", ticker, "shares must be numeric and non-negative.", "Enter manually verified share quantity.")
        if avg_cost < 0:
            row_fail = True
            row_warnings.append("INVALID_AVG_COST")
            add_check(checks, run_id, "HOLDING_AVG_COST", "FAIL", "FAIL", ticker, "avg_cost_usd must be numeric and non-negative.", "Enter manually verified average cost.")
        if price < 0:
            row_fail = True
            row_warnings.append("INVALID_CURRENT_PRICE")
            add_check(checks, run_id, "HOLDING_CURRENT_PRICE", "FAIL", "FAIL", ticker, "current_price_usd must be numeric and non-negative.", "Enter manually verified current price.")
        if market_value_raw < 0:
            row_fail = True
            row_warnings.append("INVALID_MARKET_VALUE")
            add_check(checks, run_id, "HOLDING_MARKET_VALUE", "FAIL", "FAIL", ticker, "market_value_usd must be numeric and non-negative.", "Enter manually verified market value or set shares/current_price_usd so it can be checked.")
        if position_pct_raw < 0:
            row_fail = True
            row_warnings.append("INVALID_POSITION_PCT")
            add_check(checks, run_id, "HOLDING_POSITION_PCT", "FAIL", "FAIL", ticker, "position_pct must be numeric and non-negative.", "Enter manually verified position percent or leave zero for recomputation.")
        if not theme:
            row_warnings.append("MISSING_PRIMARY_THEME")
            add_check(checks, run_id, "HOLDING_PRIMARY_THEME", "WARN", "WARN", ticker, "primary_theme is empty.", "Enter the manually assigned primary theme used for concentration checks.")

        computed_market_value = shares * price if shares >= 0 and price >= 0 else 0.0
        normalized_market_value = market_value_raw if market_value_raw > 0 else computed_market_value
        if market_value_raw == 0 and computed_market_value > 0:
            row_warnings.append("MARKET_VALUE_COMPUTED_FROM_SHARES_PRICE")
            add_check(checks, run_id, "HOLDING_MARKET_VALUE_COMPUTED", "WARN", "WARN", ticker, "market_value_usd was zero but shares * current_price_usd was positive; normalized output computed market value.", "Update market_value_usd manually to match the latest verified value.")
        if market_value_raw > 0 and computed_market_value > 0:
            diff_pct = abs(market_value_raw - computed_market_value) / computed_market_value * 100.0
            if diff_pct > 2.0:
                row_warnings.append("MARKET_VALUE_DIFFERS_FROM_SHARES_PRICE")
                add_check(checks, run_id, "HOLDING_MARKET_VALUE_RECONCILIATION", "WARN", "WARN", ticker, f"market_value_usd differs from shares * current_price_usd by {pct(diff_pct)}%.", "Verify shares, current price, and market value.")
        normalized_position_pct = position_pct_raw if position_pct_raw > 0 else ((normalized_market_value / account_total * 100.0) if account_total > 0 else 0.0)
        unrealized = ((price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 and price >= 0 else 0.0
        non_cash_market_value += max(0.0, normalized_market_value)
        position_pct_sum += max(0.0, normalized_position_pct)
        normalized.append({
            "account_id": account_id,
            "as_of_date": as_of_date,
            "ticker": ticker,
            "shares": f"{max(0.0, shares):.6f}" if shares >= 0 else "",
            "avg_cost_usd": money(max(0.0, avg_cost)) if avg_cost >= 0 else "",
            "current_price_usd": money(max(0.0, price)) if price >= 0 else "",
            "normalized_market_value_usd": money(max(0.0, normalized_market_value)),
            "normalized_position_pct": pct(max(0.0, normalized_position_pct)),
            "primary_theme": theme,
            "position_type": position_type,
            "row_quality": "FAIL" if row_fail else ("WARN" if row_warnings else "OK"),
            "row_warnings": ";".join(row_warnings),
            "computed_unrealized_pnl_pct": pct(unrealized),
            "generated_at": generated_at,
            "run_id": run_id,
        })

    cash_pct = (cash / account_total * 100.0) if account_total > 0 and cash >= 0 else 0.0
    total_pct = cash_pct + position_pct_sum
    if account_total > 0 and rows and not template_empty and abs(total_pct - 100.0) > 5.0:
        add_check(checks, run_id, "ACCOUNT_PERCENT_RECONCILIATION", "WARN", "WARN", "", f"Cash percent plus holding position_pct totals {pct(total_pct)}%, not near 100%.", "Verify cash_usd, account_total_value_usd, and each position_pct.")
    elif account_total > 0:
        add_check(checks, run_id, "ACCOUNT_PERCENT_RECONCILIATION", "INFO", "PASS", "", f"Cash percent plus holding position_pct totals {pct(total_pct)}%.", "No action required unless values are stale.")

    r31d = read_status_file(root / R31D_READ_FIRST)
    r31d_total = to_float(r31d.get("ACCOUNT_TOTAL_VALUE_USD"), 0.0)
    r31d_cash = to_float(r31d.get("CASH_USD"), 0.0)
    account_state_changed = False
    if r31d_total > 0 and account_total > 0 and abs(r31d_total - account_total) / account_total > 0.01:
        account_state_changed = True
    if r31d_cash > 0 and cash >= 0 and abs(r31d_cash - cash) / max(cash, 1.0) > 0.01:
        account_state_changed = True
    r31d_quality = r31d.get("ACCOUNT_STATE_QUALITY_FLAG", "")
    if non_cash_rows and r31d_quality == "WARN_TEMPLATE_EMPTY_ACCOUNT":
        account_state_changed = True
        add_check(checks, run_id, "R31D_REFRESH_REQUIRED", "WARN", "WARN", "", "Manual holdings exist but latest R31D still reports WARN_TEMPLATE_EMPTY_ACCOUNT.", "Rerun R31F after validating the account file.")
    elif account_state_changed:
        add_check(checks, run_id, "R31D_REFRESH_REQUIRED", "WARN", "WARN", "", "Manual account file differs from latest R31D account assumptions.", "Rerun R31F so account-aware constraints use the updated file.")
    else:
        add_check(checks, run_id, "R31D_REFRESH_REQUIRED", "INFO", "PASS", "", "No material R31D account assumption mismatch detected.", "No action required.")

    fail_count = sum(1 for check in checks if check.get("severity") == "FAIL")
    warn_count = sum(1 for check in checks if check.get("severity") == "WARN")
    info_count = sum(1 for check in checks if check.get("severity") == "INFO")
    if fail_count:
        account_quality = "FAIL_INVALID_ACCOUNT_STATE"
        status = STATUS_FAIL
    elif template_empty or created_starter or (rows and len(non_cash_rows) == 0):
        account_quality = "WARN_TEMPLATE_EMPTY_ACCOUNT"
        status = STATUS_WARN_TEMPLATE
    elif warn_count:
        account_quality = "WARN_PARTIAL_ACCOUNT_DATA"
        status = STATUS_WARN
    else:
        account_quality = "OK"
        status = STATUS_OK
    account_mode = "TEMPLATE_OR_EMPTY_ACCOUNT_ASSUMPTION" if account_quality == "WARN_TEMPLATE_EMPTY_ACCOUNT" else "MANUAL_HOLDINGS_FILE"

    return {
        "status": status,
        "account_state_path": account_state_path,
        "account_state_exists": account_existed_before or account_state_path.exists(),
        "rows": rows,
        "fields": fields,
        "checks": checks,
        "normalized": normalized,
        "account_id": account_id,
        "as_of_date": as_of_date,
        "account_total": account_total,
        "cash": cash,
        "reserve": reserve,
        "available_cash": available_cash,
        "cash_rows": cash_rows,
        "non_cash_rows": non_cash_rows,
        "duplicate_tickers": duplicate_tickers,
        "missing_columns": missing_columns,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "info_count": info_count,
        "template_empty": template_empty or created_starter,
        "account_mode": account_mode,
        "account_quality": account_quality,
        "r31d": r31d,
        "r31d_total": r31d_total,
        "r31d_cash": r31d_cash,
        "account_state_changed": account_state_changed,
    }


def build_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def build_summary(values: Dict[str, object]) -> Dict[str, object]:
    return {
        "run_id": values.get("RUN_ID", ""),
        "status": values.get("STATUS", ""),
        "generated_at": values.get("_GENERATED_AT", ""),
        "account_state_file": values.get("ACCOUNT_STATE_FILE", ""),
        "account_state_mode": values.get("ACCOUNT_STATE_MODE", ""),
        "account_state_quality": values.get("ACCOUNT_STATE_QUALITY", ""),
        "account_total_value_usd": values.get("ACCOUNT_TOTAL_VALUE_USD", ""),
        "cash_usd": values.get("CASH_USD", ""),
        "available_cash_after_reserve_usd": values.get("AVAILABLE_CASH_AFTER_RESERVE_USD", ""),
        "holding_row_count": values.get("HOLDING_ROW_COUNT", ""),
        "non_cash_position_count": values.get("NON_CASH_POSITION_COUNT", ""),
        "duplicate_ticker_count": values.get("DUPLICATE_TICKER_COUNT", ""),
        "missing_required_column_count": values.get("MISSING_REQUIRED_COLUMN_COUNT", ""),
        "fail_check_count": values.get("FAIL_CHECK_COUNT", ""),
        "warn_check_count": values.get("WARN_CHECK_COUNT", ""),
        "template_empty_account": values.get("TEMPLATE_EMPTY_ACCOUNT", ""),
        "account_state_changed_rerun_r31d_required": values.get("ACCOUNT_STATE_CHANGED_RERUN_R31D_REQUIRED", ""),
        "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
        "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
        "notes": values.get("_NOTES", ""),
    }


def build_guide(values: Dict[str, object], checks: Sequence[Dict[str, object]], normalized: Sequence[Dict[str, object]]) -> str:
    failing = [row for row in checks if row.get("severity") == "FAIL"]
    warnings = [row for row in checks if row.get("severity") == "WARN"]
    return "\n".join([
        "# V18 Current Manual Account State Guide",
        "",
        "## 1. Final Validation Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Current Account State Mode And Quality",
        f"- ACCOUNT_STATE_MODE: `{values.get('ACCOUNT_STATE_MODE', '')}`",
        f"- ACCOUNT_STATE_QUALITY: `{values.get('ACCOUNT_STATE_QUALITY', '')}`",
        f"- ACCOUNT_STATE_FILE: `{values.get('ACCOUNT_STATE_FILE', '')}`",
        "",
        "## 3. Template / Empty Account Check",
        f"- TEMPLATE_EMPTY_ACCOUNT: `{values.get('TEMPLATE_EMPTY_ACCOUNT', '')}`",
        "- If this is TRUE, V18.31D/R31F account-aware outputs are based on a cash-only manual assumption, not real holdings.",
        "",
        "## 4. How To Update The Manual Account File",
        "Edit `state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE.csv` manually.",
        "- Keep one `CASH_USD` row with total account value and cash.",
        "- Add one row per holding with ticker, shares, average cost, current price, market value, position percent, theme, and position type.",
        "- Use manually verified values only. This validator does not connect to a broker and does not fetch prices.",
        "",
        "## 5. Example Rows",
        "```csv",
        "account_id,as_of_date,account_total_value_usd,cash_usd,ticker,shares,avg_cost_usd,current_price_usd,market_value_usd,position_pct,primary_theme,position_type,notes",
        "MANUAL_DEFAULT,2026-05-22,2000.00,650.00,CASH_USD,0,0,1,0,0,CASH,CASH,MANUAL_CASH_BALANCE",
        "MANUAL_DEFAULT,2026-05-22,2000.00,650.00,NVDA,1,100.00,120.00,120.00,6.00,AI_INFRA,CORE_HOLDING,MANUALLY_VERIFIED_HOLDING",
        "```",
        "",
        "## 6. Required Columns",
        md_table([{"column": col, "purpose": column_purpose(col)} for col in REQUIRED_COLUMNS], ["column", "purpose"], 20),
        "## 7. How R31D/R31F Use This File",
        "- R31D reads this file to calculate existing position exposure, cash availability, theme exposure, high-risk exposure, active positions, and whether a current COST_OK name can be considered manually.",
        "- R31F uses R31D as part of the full daily trade-readiness homepage.",
        "- If this file is updated, rerun V18.32A first, then rerun R31F.",
        "",
        "## 8. Current Normalized Holdings Preview",
        md_table(normalized, ["ticker", "normalized_market_value_usd", "normalized_position_pct", "primary_theme", "position_type", "row_quality", "row_warnings"], 30),
        "## 9. Validation Warnings And Failures",
        "### Failures",
        md_table(failing, ["check_name", "affected_ticker", "message", "suggested_fix"], 30),
        "### Warnings",
        md_table(warnings, ["check_name", "affected_ticker", "message", "suggested_fix"], 30),
        "## 10. Safety",
        "- Manual file only.",
        "- No broker connection.",
        "- No order placement.",
        "- No external data fetch.",
        "- User must verify all values manually before relying on account-aware constraints.",
        "- `AUTO_TRADE: DISABLED`",
        "- `AUTO_SELL: DISABLED`",
        "- `OFFICIAL_DECISION_IMPACT: NONE`",
        "",
        "## 11. Next Step",
        "- If template/empty: edit the manual account file with real cash and holdings, then rerun V18.32A and R31F.",
        "- If valid: rerun R31F so account-aware trade-readiness uses the updated manual account state.",
        "",
    ])


def column_purpose(column: str) -> str:
    purposes = {
        "account_id": "Manual account identifier.",
        "as_of_date": "Date the manual values were verified.",
        "account_total_value_usd": "Total account value in USD.",
        "cash_usd": "Available cash balance in USD.",
        "ticker": "CASH_USD or holding ticker.",
        "shares": "Manual share quantity.",
        "avg_cost_usd": "Manual average cost per share.",
        "current_price_usd": "Manual current price per share.",
        "market_value_usd": "Manual holding market value.",
        "position_pct": "Holding market value divided by account total value.",
        "primary_theme": "Theme used for exposure checks.",
        "position_type": "CASH, CORE_HOLDING, SPECULATIVE, ETF, or another operator label.",
        "notes": "Manual source notes and warnings.",
    }
    return purposes.get(column, "")


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    run_id = f"V18_32A_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    for rel in [OUT_VALIDATION, OUT_NORMALIZED, OUT_CURRENT_GUIDE, OUT_REPORT, OUT_READ_FIRST, OUT_SUMMARY]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        account_state_path = Path(args.account_state_file).resolve() if args.account_state_file else root / ACCOUNT_STATE
        account_state_path.parent.mkdir(parents=True, exist_ok=True)
        if not (root / ACCOUNT_TEMPLATE).exists():
            write_csv(root / ACCOUNT_TEMPLATE, [], REQUIRED_COLUMNS)
        values: Dict[str, object] = {
            "STATUS": STATUS_DRY,
            "MODE": MODE_DRY,
            "RUN_ID": run_id,
            "DRY_RUN": "TRUE",
            "ACCOUNT_STATE_FILE": str(account_state_path),
            "ACCOUNT_STATE_EXISTS": bool_text(account_state_path.exists()),
            "ACCOUNT_STATE_MODE": "DRY_RUN_VALIDATION_ONLY",
            "ACCOUNT_STATE_QUALITY": "NOT_EVALUATED",
            "ACCOUNT_ID": "",
            "AS_OF_DATE": "",
            "ACCOUNT_TOTAL_VALUE_USD": money(args.account_size_usd),
            "CASH_USD": "" if args.cash_usd is None else money(args.cash_usd),
            "CASH_RESERVE_PCT": pct(args.cash_reserve_pct),
            "CASH_RESERVE_REQUIRED_USD": money(args.account_size_usd * args.cash_reserve_pct / 100.0),
            "AVAILABLE_CASH_AFTER_RESERVE_USD": "",
            "HOLDING_ROW_COUNT": "",
            "NON_CASH_POSITION_COUNT": "",
            "CASH_ROW_COUNT": "",
            "DUPLICATE_TICKER_COUNT": "",
            "MISSING_REQUIRED_COLUMN_COUNT": "",
            "FAIL_CHECK_COUNT": "0",
            "WARN_CHECK_COUNT": "0",
            "INFO_CHECK_COUNT": "0",
            "TEMPLATE_EMPTY_ACCOUNT": "",
            "NORMALIZED_HOLDINGS_ROWS": "",
            "R31D_ACCOUNT_TOTAL_VALUE_USD": "",
            "R31D_CASH_USD": "",
            "R31D_ACCOUNT_STATE_MODE": "",
            "R31D_ACCOUNT_STATE_QUALITY": "",
            "ACCOUNT_STATE_CHANGED_RERUN_R31D_REQUIRED": "FALSE",
            "AUTO_TRADE": "DISABLED",
            "AUTO_SELL": "DISABLED",
            "OFFICIAL_DECISION_IMPACT": "NONE",
            "VALIDATION_FAIL_COUNT": "0",
            "FORBIDDEN_MODIFIED": "FALSE",
            "NEXT_RECOMMENDED_STEP": "Run V18.32A live to validate the manual account file, then rerun R31F after edits.",
            "_GENERATED_AT": generated_at,
            "_NOTES": "DRY_RUN_ONLY_NO_ACCOUNT_VALIDATION_WRITES",
        }
        write_text(root / OUT_READ_FIRST, build_read_first(values))
        write_csv(root / OUT_SUMMARY, [build_summary(values)], SUMMARY_FIELDS)
        dry_report = "\n".join([
            "# V18.32A Manual Account State Validator",
            "",
            f"STATUS: {STATUS_DRY}",
            "",
            "Dry run validated paths and wrapper wiring. No account-state validation outputs were refreshed.",
            "",
            "Safety: no broker connection, no order placement, no external data fetch.",
            "",
        ])
        write_text(root / OUT_CURRENT_GUIDE, dry_report)
        write_text(root / OUT_REPORT, dry_report)
        return 0, values

    result = validate_account(root, args, run_id, generated_at)
    checks = result["checks"]
    normalized = result["normalized"]
    r31d = result["r31d"]
    fail_count = int(result["fail_count"])
    warn_count = int(result["warn_count"])
    values = {
        "STATUS": result["status"],
        "MODE": MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": "FALSE",
        "ACCOUNT_STATE_FILE": str(result["account_state_path"]),
        "ACCOUNT_STATE_EXISTS": bool_text(bool(result["account_state_exists"])),
        "ACCOUNT_STATE_MODE": result["account_mode"],
        "ACCOUNT_STATE_QUALITY": result["account_quality"],
        "ACCOUNT_ID": result["account_id"],
        "AS_OF_DATE": result["as_of_date"],
        "ACCOUNT_TOTAL_VALUE_USD": money(float(result["account_total"])) if float(result["account_total"]) >= 0 else "",
        "CASH_USD": money(float(result["cash"])) if float(result["cash"]) >= 0 else "",
        "CASH_RESERVE_PCT": pct(args.cash_reserve_pct),
        "CASH_RESERVE_REQUIRED_USD": money(float(result["reserve"])),
        "AVAILABLE_CASH_AFTER_RESERVE_USD": money(float(result["available_cash"])),
        "HOLDING_ROW_COUNT": str(len(result["rows"])),
        "NON_CASH_POSITION_COUNT": str(len(result["non_cash_rows"])),
        "CASH_ROW_COUNT": str(len(result["cash_rows"])),
        "DUPLICATE_TICKER_COUNT": str(len(result["duplicate_tickers"])),
        "MISSING_REQUIRED_COLUMN_COUNT": str(len(result["missing_columns"])),
        "FAIL_CHECK_COUNT": str(fail_count),
        "WARN_CHECK_COUNT": str(warn_count),
        "INFO_CHECK_COUNT": str(result["info_count"]),
        "TEMPLATE_EMPTY_ACCOUNT": bool_text(bool(result["template_empty"])),
        "NORMALIZED_HOLDINGS_ROWS": str(len(normalized)),
        "R31D_ACCOUNT_TOTAL_VALUE_USD": r31d.get("ACCOUNT_TOTAL_VALUE_USD", ""),
        "R31D_CASH_USD": r31d.get("CASH_USD", ""),
        "R31D_ACCOUNT_STATE_MODE": r31d.get("ACCOUNT_STATE_MODE", ""),
        "R31D_ACCOUNT_STATE_QUALITY": r31d.get("ACCOUNT_STATE_QUALITY_FLAG", ""),
        "ACCOUNT_STATE_CHANGED_RERUN_R31D_REQUIRED": bool_text(bool(result["account_state_changed"])),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": str(fail_count),
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "Edit manual account file if template/empty, rerun V18.32A, then rerun R31F.",
        "_GENERATED_AT": generated_at,
        "_NOTES": "TEMPLATE_EMPTY_ACCOUNT_ASSUMPTION_NOT_BROKER_DATA" if result["template_empty"] else ("WARNINGS_REQUIRE_OPERATOR_REVIEW" if warn_count else "MANUAL_ACCOUNT_STATE_VALIDATED"),
    }
    write_csv(root / OUT_VALIDATION, checks, VALIDATION_FIELDS)
    write_csv(root / OUT_NORMALIZED, normalized, NORMALIZED_FIELDS)
    write_text(root / OUT_READ_FIRST, build_read_first(values))
    write_csv(root / OUT_SUMMARY, [build_summary(values)], SUMMARY_FIELDS)
    guide = build_guide(values, checks, normalized)
    write_text(root / OUT_CURRENT_GUIDE, guide)
    write_text(root / OUT_REPORT, guide.replace("# V18 Current Manual Account State Guide", "# V18.32A Manual Account State Validation Report", 1))
    return (1 if fail_count and args.strict else 0), values


def write_failure(root: Path, exc: BaseException, args: argparse.Namespace) -> Dict[str, object]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    run_id = f"V18_32A_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    account_state_path = Path(args.account_state_file).resolve() if getattr(args, "account_state_file", "") else root / ACCOUNT_STATE
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(bool(getattr(args, "dry_run", False))),
        "ACCOUNT_STATE_FILE": str(account_state_path),
        "ACCOUNT_STATE_EXISTS": bool_text(account_state_path.exists()),
        "ACCOUNT_STATE_MODE": "ERROR",
        "ACCOUNT_STATE_QUALITY": "FAIL_INVALID_ACCOUNT_STATE",
        "ACCOUNT_ID": "",
        "AS_OF_DATE": "",
        "ACCOUNT_TOTAL_VALUE_USD": "",
        "CASH_USD": "",
        "CASH_RESERVE_PCT": pct(float(getattr(args, "cash_reserve_pct", 15.0))),
        "CASH_RESERVE_REQUIRED_USD": "",
        "AVAILABLE_CASH_AFTER_RESERVE_USD": "",
        "HOLDING_ROW_COUNT": "",
        "NON_CASH_POSITION_COUNT": "",
        "CASH_ROW_COUNT": "",
        "DUPLICATE_TICKER_COUNT": "",
        "MISSING_REQUIRED_COLUMN_COUNT": "",
        "FAIL_CHECK_COUNT": "1",
        "WARN_CHECK_COUNT": "0",
        "INFO_CHECK_COUNT": "0",
        "TEMPLATE_EMPTY_ACCOUNT": "",
        "NORMALIZED_HOLDINGS_ROWS": "",
        "R31D_ACCOUNT_TOTAL_VALUE_USD": "",
        "R31D_CASH_USD": "",
        "R31D_ACCOUNT_STATE_MODE": "",
        "R31D_ACCOUNT_STATE_QUALITY": "",
        "ACCOUNT_STATE_CHANGED_RERUN_R31D_REQUIRED": "",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": "1",
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "Inspect the V18.32A error report and repair the manual account file schema.",
        "_GENERATED_AT": generated_at,
        "_NOTES": f"ERROR: {exc}",
    }
    write_text(root / OUT_READ_FIRST, build_read_first(values))
    write_csv(root / OUT_SUMMARY, [build_summary(values)], SUMMARY_FIELDS)
    error = "\n".join([
        "# V18.32A Manual Account State Validation Error",
        "",
        f"STATUS: {STATUS_FAIL}",
        f"ERROR: {exc}",
        "",
        "```",
        traceback.format_exc(),
        "```",
        "",
    ])
    write_text(root / OUT_ERROR, error)
    write_text(root / OUT_CURRENT_GUIDE, error)
    write_text(root / OUT_REPORT, error)
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.32A manual account state validator.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--account-state-file", default="")
    parser.add_argument("--account-size-usd", type=float, default=2000.0)
    parser.add_argument("--cash-usd", type=float, default=None)
    parser.add_argument("--cash-reserve-pct", type=float, default=15.0)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Compatibility flag; no files are opened by this script.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        code, values = run(root, args)
        print(f"STATUS: {values.get('STATUS', '')}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return code
    except Exception as exc:
        values = write_failure(root, exc, args)
        print(f"STATUS: {values.get('STATUS', STATUS_FAIL)}")
        print(f"ERROR: {exc}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
