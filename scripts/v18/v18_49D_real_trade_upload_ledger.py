from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path


PATCH_VERSION = "V18.49D"
PATCH_NAME = "REAL_TRADE_UPLOAD_LEDGER_AND_POSITION_BOOK_UPDATE"

TEMPLATE_COLUMNS = [
    "trade_date", "ticker", "side", "shares", "price", "fees", "account",
    "currency", "reason", "user_note", "source_advice_file", "uploaded_at",
]

AUDIT_COLUMNS = [
    "run_date", "source_file", "source_row_number", "trade_date", "ticker",
    "side", "shares", "price", "fees", "account", "currency", "validation_status",
    "validation_reason", "ledger_eligible", "position_rebuild_eligible",
]

LEDGER_COLUMNS = [
    "run_date", "source_file", "source_row_number", "trade_date", "ticker",
    "side", "shares", "price", "fees", "account", "currency", "reason",
    "user_note", "source_advice_file", "uploaded_at", "gross_amount",
    "net_cash_effect", "broker_api_used", "order_execution_used",
]

POSITION_COLUMNS = [
    "ticker", "account", "shares", "avg_cost", "current_position_usd",
    "max_position_usd", "target_weight_pct", "do_not_buy", "do_not_sell",
    "notes", "last_review_date",
]

SUMMARY_COLUMNS = [
    "run_date", "upload_directory_ready", "upload_template_ready",
    "upload_file_count", "uploaded_row_count", "valid_trade_row_count",
    "invalid_trade_row_count", "review_required_row_count", "ledger_written",
    "real_position_book_rebuilt", "real_position_book_state_written",
    "write_real_position_book_requested", "real_position_row_count",
    "position_rebuild_review_required_count", "official_ranking_changed",
    "factor_weights_changed", "real_trade_execution_allowed", "broker_api_used",
    "order_execution_used",
]

SHARE_SIDES = {"BUY", "ADD", "SELL", "TRIM"}
ALLOWED_SIDES = SHARE_SIDES | {"DIVIDEND", "CASH_DEPOSIT", "CASH_WITHDRAWAL", "MANUAL_ADJUSTMENT"}


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
        for row in rows:
            writer.writerow({column: clean(row.get(column)) for column in fieldnames})


def parse_positive_float(value: object) -> tuple[float | None, str | None]:
    text = clean(value)
    if not text:
        return None, "MISSING"
    try:
        out = float(text)
    except ValueError:
        return None, "NOT_NUMERIC"
    if out <= 0:
        return None, "NOT_POSITIVE"
    return out, None


def parse_nonnegative_float(value: object, default: float = 0.0) -> tuple[float, str | None]:
    text = clean(value)
    if not text:
        return default, None
    try:
        out = float(text)
    except ValueError:
        return default, "NOT_NUMERIC"
    if out < 0:
        return default, "NEGATIVE"
    return out, None


def create_template(path: Path) -> None:
    if path.exists():
        return
    write_csv(path, [], TEMPLATE_COLUMNS)


def is_blank_upload_row(row: dict[str, str]) -> bool:
    return not any(clean(row.get(column)) for column in TEMPLATE_COLUMNS)


def is_sample_row(row: dict[str, str], source_file: Path) -> bool:
    if source_file.name == "V18_REAL_TRADE_UPLOAD_TEMPLATE.csv":
        return True
    if clean(row.get("is_sample")).upper() == "TRUE":
        return True
    return clean(row.get("reason")).upper() == "SAMPLE"


def validate_row(row: dict[str, str]) -> tuple[str, str, dict[str, str]]:
    side = clean(row.get("side")).upper()
    ticker = clean(row.get("ticker")).upper()
    account = clean(row.get("account"), "UNKNOWN_ACCOUNT")
    currency = clean(row.get("currency"), "USD").upper()
    normalized = {
        "trade_date": clean(row.get("trade_date")),
        "ticker": ticker,
        "side": side,
        "shares": clean(row.get("shares")),
        "price": clean(row.get("price")),
        "fees": clean(row.get("fees"), "0"),
        "account": account,
        "currency": currency,
        "reason": clean(row.get("reason")),
        "user_note": clean(row.get("user_note")),
        "source_advice_file": clean(row.get("source_advice_file")),
        "uploaded_at": clean(row.get("uploaded_at")),
    }
    reasons: list[str] = []
    status = "VALID"

    if not normalized["trade_date"]:
        reasons.append("TRADE_DATE_REQUIRED")
    if side not in ALLOWED_SIDES:
        reasons.append("SIDE_NOT_ALLOWED")
    fees, fee_error = parse_nonnegative_float(normalized["fees"])
    if fee_error:
        reasons.append(f"FEES_{fee_error}")
    normalized["fees"] = f"{fees:.6f}"
    if not normalized["account"]:
        normalized["account"] = "UNKNOWN_ACCOUNT"
    if not normalized["currency"]:
        normalized["currency"] = "USD"

    if side in SHARE_SIDES:
        if not ticker:
            reasons.append("TICKER_REQUIRED")
        shares, share_error = parse_positive_float(normalized["shares"])
        price, price_error = parse_positive_float(normalized["price"])
        if share_error:
            reasons.append(f"SHARES_{share_error}")
        if price_error:
            reasons.append(f"PRICE_{price_error}")
        if shares is not None:
            normalized["shares"] = f"{shares:.6f}"
        if price is not None:
            normalized["price"] = f"{price:.6f}"
    elif side == "DIVIDEND":
        if not ticker:
            reasons.append("TICKER_REQUIRED")
        price, price_error = parse_positive_float(normalized["price"])
        if price_error:
            reasons.append("DIVIDEND_AMOUNT_REVIEW_REQUIRED")
            status = "REVIEW_REQUIRED"
        else:
            normalized["price"] = f"{price:.6f}"
        normalized["shares"] = "0"
    elif side in {"CASH_DEPOSIT", "CASH_WITHDRAWAL"}:
        normalized["ticker"] = ticker if ticker else "CASH"
        price, price_error = parse_positive_float(normalized["price"])
        if price_error:
            reasons.append("CASH_AMOUNT_REQUIRED_IN_PRICE")
        else:
            normalized["price"] = f"{price:.6f}"
        normalized["shares"] = "0"
    elif side == "MANUAL_ADJUSTMENT":
        if not normalized["user_note"]:
            reasons.append("USER_NOTE_REQUIRED")
        status = "REVIEW_REQUIRED"

    advice_file = normalized["source_advice_file"]
    if advice_file and not Path(advice_file).name.startswith("V18_49C_") and "V18_CURRENT_DUAL_BOOK_ACTION_PLAN" not in advice_file:
        reasons.append("SOURCE_ADVICE_FILE_NOT_V18_49C_REFERENCE")
        status = "REVIEW_REQUIRED"

    if reasons and status != "REVIEW_REQUIRED":
        status = "INVALID"
    reason_text = ";".join(reasons) if reasons else "OK"
    return status, reason_text, normalized


def collect_upload_rows(upload_dir: Path, template_path: Path) -> tuple[list[dict[str, str]], list[Path]]:
    generated_files = {template_path.name, "V18_REAL_TRADE_UPLOAD_LEDGER.csv"}
    files = sorted(path for path in upload_dir.glob("*.csv") if path.name not in generated_files)
    rows: list[dict[str, str]] = []
    for path in files:
        for idx, row in enumerate(read_csv(path), start=2):
            if is_blank_upload_row(row) or is_sample_row(row, path):
                continue
            row = dict(row)
            row["_source_file"] = str(path)
            row["_source_row_number"] = str(idx)
            rows.append(row)
    return rows, files


def ledger_row(run_ts: str, row: dict[str, str], normalized: dict[str, str]) -> dict[str, str]:
    side = normalized["side"]
    shares = float(normalized["shares"] or 0)
    price = float(normalized["price"] or 0)
    fees = float(normalized["fees"] or 0)
    gross = shares * price if side in SHARE_SIDES else price
    if side in {"BUY", "ADD", "CASH_WITHDRAWAL"}:
        cash_effect = -(gross + fees)
    elif side in {"SELL", "TRIM", "DIVIDEND", "CASH_DEPOSIT"}:
        cash_effect = gross - fees
    else:
        cash_effect = 0.0
    return {
        "run_date": run_ts,
        "source_file": clean(row.get("_source_file")),
        "source_row_number": clean(row.get("_source_row_number")),
        **normalized,
        "gross_amount": f"{gross:.6f}",
        "net_cash_effect": f"{cash_effect:.6f}",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }


def audit_row(run_ts: str, row: dict[str, str], normalized: dict[str, str], status: str, reason: str) -> dict[str, str]:
    ledger_eligible = status == "VALID"
    position_eligible = ledger_eligible and normalized["side"] in SHARE_SIDES
    return {
        "run_date": run_ts,
        "source_file": clean(row.get("_source_file")),
        "source_row_number": clean(row.get("_source_row_number")),
        **normalized,
        "validation_status": status,
        "validation_reason": reason,
        "ledger_eligible": "TRUE" if ledger_eligible else "FALSE",
        "position_rebuild_eligible": "TRUE" if position_eligible else "FALSE",
    }


def rebuild_positions(ledger_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    positions: dict[tuple[str, str], dict[str, float | str | list[str]]] = defaultdict(
        lambda: {"shares": 0.0, "cost": 0.0, "last_date": "", "notes": []}
    )
    review_required = 0
    for row in sorted(ledger_rows, key=lambda item: (item["trade_date"], item["source_file"], item["source_row_number"])):
        side = row["side"]
        if side not in SHARE_SIDES:
            continue
        key = (row["ticker"], row["account"])
        pos = positions[key]
        shares = float(row["shares"])
        price = float(row["price"])
        fees = float(row["fees"])
        current_shares = float(pos["shares"])
        current_cost = float(pos["cost"])
        pos["last_date"] = row["trade_date"]
        if side in {"BUY", "ADD"}:
            pos["shares"] = current_shares + shares
            pos["cost"] = current_cost + shares * price + fees
        else:
            if shares > current_shares:
                review_required += 1
                notes = pos["notes"]
                assert isinstance(notes, list)
                notes.append("POSITION_REBUILD_REVIEW_REQUIRED_SELL_EXCEEDS_SHARES")
                continue
            avg_cost = current_cost / current_shares if current_shares > 0 else 0.0
            pos["shares"] = current_shares - shares
            pos["cost"] = max(0.0, current_cost - avg_cost * shares)
    rows: list[dict[str, str]] = []
    for (ticker, account), pos in sorted(positions.items()):
        shares = float(pos["shares"])
        if shares <= 0:
            continue
        cost = float(pos["cost"])
        avg_cost = cost / shares if shares > 0 else 0.0
        notes = pos["notes"]
        assert isinstance(notes, list)
        rows.append({
            "ticker": ticker,
            "account": account,
            "shares": f"{shares:.6f}",
            "avg_cost": f"{avg_cost:.6f}",
            "current_position_usd": "",
            "max_position_usd": "",
            "target_weight_pct": "",
            "do_not_buy": "FALSE",
            "do_not_sell": "FALSE",
            "notes": ";".join(notes + ["GENERATED_FROM_VALID_USER_UPLOADS_ONLY", "FEES_INCLUDED_IN_BUY_COST_BASIS"]),
            "last_review_date": clean(pos["last_date"]),
        })
    return rows, review_required


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_report(values: dict[str, str], upload_dir: Path, template_path: Path, audit_rows: list[dict[str, str]], ledger_rows: list[dict[str, str]], position_rows: list[dict[str, str]]) -> str:
    review_rows = [row for row in audit_rows if row["validation_status"] == "REVIEW_REQUIRED"]
    return "\n".join([
        "# V18.49D Real Trade Upload Ledger",
        "",
        "V18.49D is a manual-upload workflow. Only user-provided upload CSV rows can become real trade ledger rows.",
        "",
        "## Manual Workflow",
        f"- Upload directory: {upload_dir}",
        f"- Template: {template_path}",
        "- Fill a separate CSV using the template columns, then rerun V18.49D.",
        "- The template itself is ignored as a trade source.",
        "",
        "## Upload Validation Summary",
        markdown_table([values], ["UPLOAD_FILE_COUNT", "UPLOADED_ROW_COUNT", "VALID_TRADE_ROW_COUNT", "INVALID_TRADE_ROW_COUNT", "REVIEW_REQUIRED_ROW_COUNT"]),
        "",
        "## Valid Trade Ledger Summary",
        markdown_table(ledger_rows[:10], ["trade_date", "ticker", "side", "shares", "price", "account", "currency"]) if ledger_rows else "No valid user-uploaded trade rows found.",
        "",
        "## Review-Required Rows",
        markdown_table(review_rows[:10], ["source_file", "source_row_number", "ticker", "side", "validation_reason"]) if review_rows else "No review-required rows.",
        "",
        "## Rebuilt Position Book",
        markdown_table(position_rows[:10], ["ticker", "account", "shares", "avg_cost", "notes"]) if position_rows else "No generated open positions.",
        "",
        "## State Write",
        f"- State real position book written: {values['REAL_POSITION_BOOK_STATE_WRITTEN']}",
        f"- Write requested: {values['WRITE_REAL_POSITION_BOOK_REQUESTED']}",
        "",
        "## Safety",
        "No broker API was used. No order was generated. No execution occurred. Official ranking, factor weights, Top20 selection, candidate scoring, and official buy/sell permissions are unchanged.",
        "",
        "## Handoff",
        "After user uploads are validated and the state real position book is intentionally written, rerun V18.49C to refresh real-position advice.",
        "",
    ]) + "\n"


def status_for(uploaded_count: int, review_count: int, position_rows: list[dict[str, str]], state_written: bool) -> str:
    if uploaded_count == 0:
        return "WARN_V18_49D_NO_USER_UPLOADS_FOUND"
    if review_count > 0:
        return "WARN_V18_49D_UPLOAD_ROWS_REVIEW_REQUIRED"
    if position_rows and not state_written:
        return "WARN_V18_49D_POSITION_BOOK_NOT_WRITTEN"
    return "PASS"


def summary_row(values: dict[str, str]) -> dict[str, str]:
    return {
        "run_date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "upload_directory_ready": values["UPLOAD_DIRECTORY_READY"],
        "upload_template_ready": values["UPLOAD_TEMPLATE_READY"],
        "upload_file_count": values["UPLOAD_FILE_COUNT"],
        "uploaded_row_count": values["UPLOADED_ROW_COUNT"],
        "valid_trade_row_count": values["VALID_TRADE_ROW_COUNT"],
        "invalid_trade_row_count": values["INVALID_TRADE_ROW_COUNT"],
        "review_required_row_count": values["REVIEW_REQUIRED_ROW_COUNT"],
        "ledger_written": values["LEDGER_WRITTEN"],
        "real_position_book_rebuilt": values["REAL_POSITION_BOOK_REBUILT"],
        "real_position_book_state_written": values["REAL_POSITION_BOOK_STATE_WRITTEN"],
        "write_real_position_book_requested": values["WRITE_REAL_POSITION_BOOK_REQUESTED"],
        "real_position_row_count": values["REAL_POSITION_ROW_COUNT"],
        "position_rebuild_review_required_count": values["POSITION_REBUILD_REVIEW_REQUIRED_COUNT"],
        "official_ranking_changed": values["OFFICIAL_RANKING_CHANGED"],
        "factor_weights_changed": values["FACTOR_WEIGHTS_CHANGED"],
        "real_trade_execution_allowed": values["REAL_TRADE_EXECUTION_ALLOWED"],
        "broker_api_used": values["BROKER_API_USED"],
        "order_execution_used": values["ORDER_EXECUTION_USED"],
    }


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "UPLOAD_DIRECTORY_READY",
        "UPLOAD_TEMPLATE_READY", "UPLOAD_FILE_COUNT", "UPLOADED_ROW_COUNT",
        "VALID_TRADE_ROW_COUNT", "INVALID_TRADE_ROW_COUNT", "REVIEW_REQUIRED_ROW_COUNT",
        "LEDGER_WRITTEN", "REAL_POSITION_BOOK_REBUILT", "REAL_POSITION_BOOK_STATE_WRITTEN",
        "WRITE_REAL_POSITION_BOOK_REQUESTED", "REAL_POSITION_ROW_COUNT",
        "POSITION_REBUILD_REVIEW_REQUIRED_COUNT", "CURRENT_ALIAS_WRITTEN",
        "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED",
        "OFFICIAL_SELL_PERMISSION_CHANGED", "REAL_TRADE_EXECUTION_ALLOWED",
        "OPTIONS_TRADE_EXECUTION_ALLOWED", "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE",
        "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only/manual V18.49D real trade upload ledger.")
    parser.add_argument("--root", "--project-root", dest="root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--create-template", action="store_true")
    parser.add_argument("--write-real-position-book", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_ts = datetime.now().astimezone().isoformat(timespec="seconds")
    upload_dir = root / "state/v18/manual/real_trade_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    template_path = upload_dir / "V18_REAL_TRADE_UPLOAD_TEMPLATE.csv"
    create_template(template_path)

    upload_rows, upload_files = collect_upload_rows(upload_dir, template_path)
    audit_rows: list[dict[str, str]] = []
    ledger_rows: list[dict[str, str]] = []
    for row in upload_rows:
        status, reason, normalized = validate_row(row)
        audit_rows.append(audit_row(run_ts, row, normalized, status, reason))
        if status == "VALID":
            ledger_rows.append(ledger_row(run_ts, row, normalized))

    position_rows, rebuild_review_count = rebuild_positions(ledger_rows)

    out_dir = root / "outputs/v18/action_plan"
    ledger_path = upload_dir / "V18_REAL_TRADE_UPLOAD_LEDGER.csv"
    rebuilt_path = out_dir / "V18_49D_REAL_POSITION_BOOK_REBUILT.csv"
    write_csv(ledger_path, ledger_rows, LEDGER_COLUMNS)
    write_csv(out_dir / "V18_49D_REAL_TRADE_UPLOAD_AUDIT.csv", audit_rows, AUDIT_COLUMNS)
    write_csv(rebuilt_path, position_rows, POSITION_COLUMNS)

    state_written = False
    if args.write_real_position_book:
        write_csv(root / "state/v18/manual/V18_REAL_POSITION_BOOK.csv", position_rows, POSITION_COLUMNS)
        state_written = True

    invalid_count = sum(1 for row in audit_rows if row["validation_status"] == "INVALID")
    review_count = sum(1 for row in audit_rows if row["validation_status"] == "REVIEW_REQUIRED") + rebuild_review_count
    status = status_for(len(upload_rows), review_count, position_rows, state_written)
    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "UPLOAD_DIRECTORY_READY": "TRUE",
        "UPLOAD_TEMPLATE_READY": "TRUE" if template_path.exists() else "FALSE",
        "UPLOAD_FILE_COUNT": str(len(upload_files)),
        "UPLOADED_ROW_COUNT": str(len(upload_rows)),
        "VALID_TRADE_ROW_COUNT": str(len(ledger_rows)),
        "INVALID_TRADE_ROW_COUNT": str(invalid_count),
        "REVIEW_REQUIRED_ROW_COUNT": str(review_count),
        "LEDGER_WRITTEN": "TRUE",
        "REAL_POSITION_BOOK_REBUILT": "TRUE",
        "REAL_POSITION_BOOK_STATE_WRITTEN": "TRUE" if state_written else "FALSE",
        "WRITE_REAL_POSITION_BOOK_REQUESTED": "TRUE" if args.write_real_position_book else "FALSE",
        "REAL_POSITION_ROW_COUNT": str(len(position_rows)),
        "POSITION_REBUILD_REVIEW_REQUIRED_COUNT": str(rebuild_review_count),
        "CURRENT_ALIAS_WRITTEN": "FALSE",
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
        "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
        "REAL_TRADE_EXECUTION_ALLOWED": "FALSE",
        "OPTIONS_TRADE_EXECUTION_ALLOWED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "VALIDATION_NOTES": "MANUAL_UPLOAD_ONLY_NO_BROKER_NO_ORDERS_NO_EXECUTION_NO_SIMULATION_OR_ADVICE_TO_TRADE_CONVERSION",
    }
    summary_path = out_dir / "V18_49D_REAL_TRADE_UPLOAD_SUMMARY.csv"
    write_csv(summary_path, [summary_row(values)], SUMMARY_COLUMNS)

    report = build_report(values, upload_dir, template_path, audit_rows, ledger_rows, position_rows)
    report_path = root / "outputs/v18/read_center/V18_49D_REAL_TRADE_UPLOAD_LEDGER_REPORT.md"
    current_path = root / "outputs/v18/read_center/V18_CURRENT_REAL_TRADE_UPLOAD_STATUS.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    if args.write_current:
        current_path.write_text(report, encoding="utf-8")
        values["CURRENT_ALIAS_WRITTEN"] = "TRUE"
        write_csv(summary_path, [summary_row(values)], SUMMARY_COLUMNS)

    write_read_first(root / "outputs/v18/ops/V18_49D_READ_FIRST.txt", values)
    print(f"STATUS: {status}")
    print(f"UPLOAD_FILE_COUNT: {values['UPLOAD_FILE_COUNT']}")
    print(f"UPLOADED_ROW_COUNT: {values['UPLOADED_ROW_COUNT']}")
    print(f"VALID_TRADE_ROW_COUNT: {values['VALID_TRADE_ROW_COUNT']}")
    print(f"REVIEW_REQUIRED_ROW_COUNT: {values['REVIEW_REQUIRED_ROW_COUNT']}")
    print(f"REAL_POSITION_BOOK_STATE_WRITTEN: {values['REAL_POSITION_BOOK_STATE_WRITTEN']}")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
