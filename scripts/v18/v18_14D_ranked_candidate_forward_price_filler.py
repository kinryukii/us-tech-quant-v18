from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

STATUS_OK = "OK_V18_14D_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_READY"
STATUS_FAIL = "FAIL_V18_14D_RANKED_CANDIDATE_FORWARD_PRICE_FILLER"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
FORWARD_PRICE_FILLER_ONLY = "TRUE"

DANGEROUS_TOKENS = (
    "SELL_NOW",
    "BUY_NOW_FORCE",
    "AUTO_EXECUTE",
    "LIVE_ORDER",
    "LIVE_SELL",
    "BROKER_ORDER",
)

FORWARD_HORIZONS = (1, 3, 5, 10, 20)

SUMMARY_FIELDS = [
    "status",
    "tracker_rows",
    "updated_forward_rows",
    "forward_complete_rows",
    "partial_forward_filled_rows",
    "pending_forward_rows",
    "pending_signal_price_rows",
    "price_source_count",
    "price_source_status",
    "min_signal_date",
    "max_signal_date",
    "top_5_tickers",
    "validation_fail_count",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "read_only",
    "forward_price_filler_only",
    "read_first",
]

AUDIT_FIELDS = ["input_name", "path", "exists", "rows", "columns", "last_write_time", "status", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def audit_row(name: str, path: Path, rows: int, columns: Sequence[str], status: str, notes: str) -> Dict[str, str]:
    last_write = ""
    if path.exists():
        last_write = dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "input_name": name,
        "path": str(path),
        "exists": "YES" if path.exists() else "NO",
        "rows": str(rows),
        "columns": ";".join(columns),
        "last_write_time": last_write,
        "status": status,
        "notes": notes,
    }


def parse_date(value: str) -> Optional[dt.date]:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text[: len(fmt)], fmt).date()
        except Exception:
            continue
    try:
        return dt.date.fromisoformat(text[:10])
    except Exception:
        return None


def parse_float(value: str) -> Optional[float]:
    if value is None:
        return None
    try:
        text = str(value).strip().replace(",", "")
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def fmt_float(value: Optional[float]) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def pick(row: Dict[str, str], names: Sequence[str]) -> str:
    lower_map = {key.lower(): key for key in row}
    for name in names:
        key = lower_map.get(name.lower())
        if key and str(row.get(key, "")).strip():
            return str(row.get(key, "")).strip()
    return ""


def local_price_files(root: Path) -> List[Path]:
    bases = [
        root / "outputs/v18/data",
        root / "outputs/v18/prices",
        root / "outputs/v18/daily_integrated",
        root / "outputs/v18/read_center",
        root / "outputs/v16/data",
        root / "outputs/v15/data",
        root / "state/v18",
        root / "state/v16",
        root / "state/v15",
        root / "outputs/v18/factor_pack",
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/technical_timing_backtest",
        root / "outputs/v18/simulation",
    ]
    files: List[Path] = []
    for base in bases:
        if base.exists():
            files.extend(base.rglob("*.csv"))
    return files


def load_local_prices(root: Path, input_audit: List[Dict[str, str]]) -> Dict[str, Dict[dt.date, float]]:
    date_cols = ("date", "price_date", "latest_price_date", "snapshot_date", "snapshot_price_date", "score_date", "updated_at")
    close_cols = ("close", "adj_close", "latest_close", "price", "last_price_usd", "current_price", "baseline_close")
    ticker_cols = ("ticker", "symbol", "yf_ticker")
    price_by_ticker: Dict[str, Dict[dt.date, float]] = {}
    source_count = 0
    for path in local_price_files(root):
        rows, fields, status = read_csv(path)
        if status != "OK" or not rows:
            continue
        lower_fields = {field.lower() for field in fields}
        if not any(col in lower_fields for col in ticker_cols):
            continue
        if not any(col in lower_fields for col in date_cols):
            continue
        if not any(col in lower_fields for col in close_cols):
            continue
        points = 0
        for row in rows:
            ticker = pick(row, ticker_cols).upper()
            day = parse_date(pick(row, date_cols))
            close = parse_float(pick(row, close_cols))
            if ticker and day and close is not None:
                price_by_ticker.setdefault(ticker, {})[day] = close
                points += 1
        if points:
            source_count += 1
            input_audit.append(audit_row(f"LOCAL_PRICE_SOURCE_{source_count}", path, len(rows), fields, "USED", f"price_points={points}"))
    return price_by_ticker


def try_yfinance(root: Path, rows: Sequence[Dict[str, str]], use_yfinance: bool, input_audit: List[Dict[str, str]]) -> Dict[str, Dict[dt.date, float]]:
    if not use_yfinance:
        input_audit.append(audit_row("YFINANCE", root, 0, [], "SKIPPED", "use_yfinance_false"))
        return {}
    if importlib.util.find_spec("yfinance") is None:
        input_audit.append(audit_row("YFINANCE", root, 0, [], "UNAVAILABLE", "yfinance_not_installed"))
        return {}
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        input_audit.append(audit_row("YFINANCE", root, 0, [], "IMPORT_FAILED", f"{type(exc).__name__}: {exc}"))
        return {}
    tickers = sorted({row.get("ticker", "").upper() for row in rows if row.get("ticker")})
    price_by_ticker: Dict[str, Dict[dt.date, float]] = {}
    for ticker in tickers:
        signal_date = parse_date(next((row.get("signal_date", "") for row in rows if row.get("ticker", "").upper() == ticker), ""))
        if not signal_date:
            continue
        start = signal_date.isoformat()
        end = (signal_date + dt.timedelta(days=45)).isoformat()
        try:
            hist = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
            if hist is None or hist.empty:
                continue
            for idx, item in hist.iterrows():
                day = idx.date() if hasattr(idx, "date") else parse_date(str(idx))
                close = item.get("Close") if "Close" in item else item.get("Adj Close")
                value = parse_float(str(close))
                if day and value is not None:
                    price_by_ticker.setdefault(ticker, {})[day] = value
        except Exception as exc:
            input_audit.append(audit_row(f"YFINANCE_{ticker}", root, 0, [], "FETCH_FAILED", f"{type(exc).__name__}: {exc}"))
    input_audit.append(audit_row("YFINANCE", root, sum(len(v) for v in price_by_ticker.values()), ["ticker", "date", "close"], "USED" if price_by_ticker else "NO_DATA", "optional_fetch"))
    return price_by_ticker


def merge_prices(primary: Dict[str, Dict[dt.date, float]], extra: Dict[str, Dict[dt.date, float]]) -> Dict[str, Dict[dt.date, float]]:
    merged = {ticker: dict(points) for ticker, points in primary.items()}
    for ticker, points in extra.items():
        merged.setdefault(ticker, {}).update(points)
    return merged


def future_price(points: Dict[dt.date, float], signal_date: dt.date, horizon: int) -> Tuple[Optional[dt.date], Optional[float], str]:
    ordered = sorted(points)
    if signal_date in points:
        future = [day for day in ordered if day > signal_date]
        note = ""
    else:
        future = [day for day in ordered if day > signal_date]
        note = "SIGNAL_DATE_PRICE_ROW_MISSING_USED_NEXT_AVAILABLE" if future else ""
    if len(future) >= horizon:
        day = future[horizon - 1]
        return day, points[day], note
    return None, None, note


def update_row_forward(row: Dict[str, str], price_by_ticker: Dict[str, Dict[dt.date, float]], now: str) -> bool:
    ticker = row.get("ticker", "").upper()
    signal_date = parse_date(row.get("signal_date", ""))
    price_at_signal = parse_float(row.get("price_at_signal", ""))
    old = dict(row)
    notes = row.get("notes", "")
    if price_at_signal is None:
        row["validation_status"] = "PENDING_SIGNAL_PRICE"
        row["last_updated"] = now
        return row != old
    if not ticker or not signal_date:
        row["validation_status"] = "PENDING_FORWARD_DATA"
        row["last_updated"] = now
        return row != old
    points = price_by_ticker.get(ticker, {})
    filled_count = 0
    available_forward_prices: List[float] = []
    for horizon in FORWARD_HORIZONS:
        price_key = f"forward_{horizon}d_price"
        ret_key = f"forward_{horizon}d_return"
        day, price, note = future_price(points, signal_date, horizon)
        if note and note not in notes:
            notes = f"{notes};{note}".strip(";")
        if price is None:
            if row.get(price_key) and row.get(ret_key):
                filled_count += 1
                existing = parse_float(row.get(price_key, ""))
                if existing is not None:
                    available_forward_prices.append(existing)
            continue
        available_forward_prices.append(price)
        if not row.get(price_key):
            row[price_key] = fmt_float(price)
        if not row.get(ret_key):
            row[ret_key] = fmt_float(price / price_at_signal - 1)
        if row.get(price_key) and row.get(ret_key):
            filled_count += 1
    if available_forward_prices:
        runup = max(price / price_at_signal - 1 for price in available_forward_prices)
        drawdown = min(price / price_at_signal - 1 for price in available_forward_prices)
        if not row.get("max_runup_20d"):
            row["max_runup_20d"] = fmt_float(runup)
        if not row.get("max_drawdown_20d"):
            row["max_drawdown_20d"] = fmt_float(drawdown)
    if filled_count == len(FORWARD_HORIZONS):
        row["validation_status"] = "FORWARD_COMPLETE"
    elif filled_count > 0:
        row["validation_status"] = "PARTIAL_FORWARD_FILLED"
    else:
        row["validation_status"] = "PENDING_FORWARD_DATA"
    row["notes"] = notes
    if row != old:
        row["last_updated"] = now
    return row != old


def duplicate_count(rows: Sequence[Dict[str, str]]) -> int:
    keys = [(row.get("signal_date", ""), row.get("ticker", ""), row.get("rank_source", "")) for row in rows]
    return len(keys) - len(set(keys))


def top_5(rows: Sequence[Dict[str, str]]) -> str:
    ordered = sorted(rows, key=lambda row: int(parse_float(row.get("rank", "999999")) or 999999))
    return ",".join(row.get("ticker", "") for row in ordered[:5])


def scan_tokens(root: Path, paths: Iterable[Path]) -> List[str]:
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{rel(root, path)}::{token}")
    return hits


def markdown_table(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[str]:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return out


def build(root: Path, max_rows: int, use_yfinance: bool, allow_local_price_only: bool) -> Tuple[Dict[str, str], int]:
    tracker_path = root / "state/v18/candidate_forward_tracker/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"
    output_csv = root / "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv"
    output_audit = root / "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_AUDIT.csv"
    read_first = root / "outputs/v18/ops/V18_14D_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_REPORT.md"
    summary_path = root / "outputs/v18/ops/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_SUMMARY.csv"
    input_audit_path = root / "outputs/v18/ops/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_INPUT_AUDIT.csv"

    tracker_rows, tracker_fields, tracker_status = read_csv(tracker_path)
    fields = list(tracker_fields)
    for required in (
        "forward_1d_price", "forward_1d_return", "forward_3d_price", "forward_3d_return",
        "forward_5d_price", "forward_5d_return", "forward_10d_price", "forward_10d_return",
        "forward_20d_price", "forward_20d_return", "max_runup_20d", "max_drawdown_20d",
        "validation_status", "last_updated", "notes",
    ):
        if required not in fields:
            fields.append(required)
    tracker_rows = [{field: row.get(field, "") for field in fields} for row in tracker_rows]
    target_rows = tracker_rows if max_rows <= 0 else tracker_rows[:max_rows]

    input_audit: List[Dict[str, str]] = [
        audit_row("TRACKER", tracker_path, len(tracker_rows), tracker_fields, tracker_status, "PERSISTENT_FORWARD_TRACKER"),
    ]
    local_prices = load_local_prices(root, input_audit) if allow_local_price_only else {}
    yf_prices = try_yfinance(root, target_rows, use_yfinance, input_audit)
    price_by_ticker = merge_prices(local_prices, yf_prices)
    price_source_count = sum(1 for row in input_audit if row["status"] == "USED" and ("PRICE_SOURCE" in row["input_name"] or row["input_name"] == "YFINANCE"))
    price_source_status = "LOCAL_PRICE_AVAILABLE" if price_source_count else "NO_FORWARD_PRICE_DATA_AVAILABLE"

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated = 0
    for row in target_rows:
        if update_row_forward(row, price_by_ticker, now):
            updated += 1

    dup_count = duplicate_count(tracker_rows)
    complete = sum(1 for row in tracker_rows if row.get("validation_status") == "FORWARD_COMPLETE")
    partial = sum(1 for row in tracker_rows if row.get("validation_status") == "PARTIAL_FORWARD_FILLED")
    pending_signal = sum(1 for row in tracker_rows if row.get("validation_status") == "PENDING_SIGNAL_PRICE")
    pending_forward = sum(1 for row in tracker_rows if row.get("validation_status") == "PENDING_FORWARD_DATA")
    signal_dates = [parse_date(row.get("signal_date", "")) for row in tracker_rows]
    signal_dates = [day for day in signal_dates if day]

    failures: List[str] = []
    if tracker_status != "OK" or not tracker_rows:
        failures.append("TRACKER_MISSING_OR_UNREADABLE")
    if dup_count:
        failures.append("DUPLICATE_TRACKER_KEYS_DETECTED")
    if OFFICIAL_DECISION_IMPACT != "NONE":
        failures.append("OFFICIAL_DECISION_IMPACT_NOT_NONE")
    if AUTO_TRADE != "DISABLED":
        failures.append("AUTO_TRADE_NOT_DISABLED")
    if AUTO_SELL != "DISABLED":
        failures.append("AUTO_SELL_NOT_DISABLED")

    write_csv(tracker_path, tracker_rows, fields)
    ensure_dir(output_csv.parent)
    shutil.copy2(tracker_path, output_csv)
    filler_audit_rows = [
        {"metric": "tracker_path", "value": str(tracker_path)},
        {"metric": "max_rows", "value": str(max_rows)},
        {"metric": "use_yfinance", "value": "TRUE" if use_yfinance else "FALSE"},
        {"metric": "allow_local_price_only", "value": "TRUE" if allow_local_price_only else "FALSE"},
        {"metric": "duplicate_count", "value": str(dup_count)},
        {"metric": "price_source_count", "value": str(price_source_count)},
    ]
    write_csv(output_audit, filler_audit_rows, ["metric", "value"])

    scan_paths = [tracker_path, output_csv, output_audit, read_first, report_path, summary_path, input_audit_path]
    pre_hits = scan_tokens(root, [tracker_path, output_csv, output_audit])
    if pre_hits:
        failures.append("DANGEROUS_TOKEN_DETECTED")

    status = STATUS_OK if not failures else STATUS_FAIL
    values = {
        "STATUS": status,
        "TRACKER_ROWS": str(len(tracker_rows)),
        "UPDATED_FORWARD_ROWS": str(updated),
        "FORWARD_COMPLETE_ROWS": str(complete),
        "PARTIAL_FORWARD_FILLED_ROWS": str(partial),
        "PENDING_FORWARD_ROWS": str(pending_forward),
        "PENDING_SIGNAL_PRICE_ROWS": str(pending_signal),
        "PRICE_SOURCE_COUNT": str(price_source_count),
        "PRICE_SOURCE_STATUS": price_source_status,
        "MIN_SIGNAL_DATE": min(signal_dates).isoformat() if signal_dates else "",
        "MAX_SIGNAL_DATE": max(signal_dates).isoformat() if signal_dates else "",
        "TOP_5_TICKERS": top_5(tracker_rows),
        "VALIDATION_FAIL_COUNT": str(len(failures)),
        "FAIL_REASONS": ";".join(failures) if failures else "NONE",
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "FORWARD_PRICE_FILLER_ONLY": FORWARD_PRICE_FILLER_ONLY,
        "DANGEROUS_TOKEN_DETECTED": "YES" if pre_hits else "NO",
        "DUPLICATE_PREVENTION_VALIDATED": "YES" if dup_count == 0 else "NO",
        "TRACKER_CSV": rel(root, tracker_path),
        "READ_FIRST": rel(root, read_first),
    }

    read_first_keys = [
        "STATUS", "TRACKER_ROWS", "UPDATED_FORWARD_ROWS", "FORWARD_COMPLETE_ROWS",
        "PARTIAL_FORWARD_FILLED_ROWS", "PENDING_FORWARD_ROWS", "PENDING_SIGNAL_PRICE_ROWS",
        "PRICE_SOURCE_COUNT", "PRICE_SOURCE_STATUS", "MIN_SIGNAL_DATE", "MAX_SIGNAL_DATE",
        "TOP_5_TICKERS", "VALIDATION_FAIL_COUNT", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE",
        "AUTO_SELL", "READ_ONLY", "FORWARD_PRICE_FILLER_ONLY",
    ]
    write_text(read_first, "\n".join(f"{key}: {values[key]}" for key in read_first_keys) + f"\nFAIL_REASONS: {values['FAIL_REASONS']}\nDANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}\nDUPLICATE_PREVENTION_VALIDATED: {values['DUPLICATE_PREVENTION_VALIDATED']}\nTRACKER_CSV: {values['TRACKER_CSV']}\n")

    summary_row = {field: values[field.upper()] for field in SUMMARY_FIELDS if field.upper() in values}
    summary_row["status"] = values["STATUS"]
    summary_row["tracker_rows"] = values["TRACKER_ROWS"]
    summary_row["updated_forward_rows"] = values["UPDATED_FORWARD_ROWS"]
    summary_row["forward_complete_rows"] = values["FORWARD_COMPLETE_ROWS"]
    summary_row["partial_forward_filled_rows"] = values["PARTIAL_FORWARD_FILLED_ROWS"]
    summary_row["pending_forward_rows"] = values["PENDING_FORWARD_ROWS"]
    summary_row["pending_signal_price_rows"] = values["PENDING_SIGNAL_PRICE_ROWS"]
    summary_row["price_source_count"] = values["PRICE_SOURCE_COUNT"]
    summary_row["price_source_status"] = values["PRICE_SOURCE_STATUS"]
    summary_row["min_signal_date"] = values["MIN_SIGNAL_DATE"]
    summary_row["max_signal_date"] = values["MAX_SIGNAL_DATE"]
    summary_row["top_5_tickers"] = values["TOP_5_TICKERS"]
    summary_row["validation_fail_count"] = values["VALIDATION_FAIL_COUNT"]
    summary_row["official_decision_impact"] = OFFICIAL_DECISION_IMPACT
    summary_row["auto_trade"] = AUTO_TRADE
    summary_row["auto_sell"] = AUTO_SELL
    summary_row["read_only"] = READ_ONLY
    summary_row["forward_price_filler_only"] = FORWARD_PRICE_FILLER_ONLY
    summary_row["read_first"] = rel(root, read_first)
    write_csv(summary_path, [summary_row], SUMMARY_FIELDS)
    write_csv(input_audit_path, input_audit, AUDIT_FIELDS)

    report = [
        "# V18.14D Ranked Candidate Forward Price Filler",
        "",
        "Research-only forward price filler. No trading, selling, broker, or official decision impact.",
        "",
        "## Status",
        "",
    ]
    report.extend(f"- {key}: {values[key]}" for key in read_first_keys)
    report.extend([
        f"- FAIL_REASONS: {values['FAIL_REASONS']}",
        f"- DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}",
        f"- DUPLICATE_PREVENTION_VALIDATED: {values['DUPLICATE_PREVENTION_VALIDATED']}",
        f"- TRACKER_CSV: {values['TRACKER_CSV']}",
        "",
        "## Tracker Sample",
        "",
    ])
    report.extend(markdown_table(tracker_rows[:20], ["signal_date", "ticker", "rank", "validation_status", "forward_1d_price", "forward_20d_price"]))
    write_text(report_path, "\n".join(report) + "\n")

    post_hits = scan_tokens(root, scan_paths)
    if post_hits and not pre_hits:
        values["STATUS"] = STATUS_FAIL
        values["VALIDATION_FAIL_COUNT"] = "1"
        values["DANGEROUS_TOKEN_DETECTED"] = "YES"
        write_text(read_first, "\n".join(f"{key}: {values[key]}" for key in read_first_keys) + "\nFAIL_REASONS: DANGEROUS_TOKEN_DETECTED\nDANGEROUS_TOKEN_DETECTED: YES\n")

    for key in read_first_keys:
        print(f"{key}: {values[key]}")
    print(f"FAIL_REASONS: {values['FAIL_REASONS']}")
    print(f"DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}")
    print(f"DUPLICATE_PREVENTION_VALIDATED: {values['DUPLICATE_PREVENTION_VALIDATED']}")
    print(f"TRACKER_CSV: {values['TRACKER_CSV']}")
    return values, 0 if values["STATUS"] == STATUS_OK else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.14D ranked candidate forward price filler.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--use-yfinance", action="store_true")
    parser.add_argument("--allow-local-price-only", action="store_true")
    args = parser.parse_args()
    _, code = build(Path(args.root), args.max_rows, args.use_yfinance, args.allow_local_price_only)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
