from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

STATUS_OK = "OK_V18_14C_RANKED_CANDIDATE_FORWARD_TRACKER_READY"
STATUS_FAIL = "FAIL_V18_14C_RANKED_CANDIDATE_FORWARD_TRACKER"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
FORWARD_VALIDATION_ONLY = "TRUE"

DANGEROUS_TOKENS = (
    "SELL_NOW",
    "BUY_NOW_FORCE",
    "AUTO_EXECUTE",
    "LIVE_ORDER",
    "LIVE_SELL",
    "BROKER_ORDER",
)

TRACKER_COLUMNS = [
    "signal_date",
    "ticker",
    "rank",
    "rank_source",
    "score",
    "price_at_signal",
    "price_date",
    "sector",
    "industry",
    "factor_score",
    "technical_score",
    "risk_label",
    "run_mode",
    "full_daily_mode_status",
    "official_daily_status",
    "v18_14b_status",
    "v18_14a_status",
    "top_5_snapshot",
    "forward_1d_price",
    "forward_1d_return",
    "forward_3d_price",
    "forward_3d_return",
    "forward_5d_price",
    "forward_5d_return",
    "forward_10d_price",
    "forward_10d_return",
    "forward_20d_price",
    "forward_20d_return",
    "max_runup_20d",
    "max_drawdown_20d",
    "validation_status",
    "last_updated",
    "notes",
]

SUMMARY_FIELDS = [
    "status",
    "signal_date",
    "rank_source",
    "tracker_rows",
    "new_signal_rows_added",
    "updated_forward_rows",
    "forward_complete_rows",
    "pending_forward_rows",
    "top_5_tickers",
    "validation_fail_count",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "read_only",
    "forward_validation_only",
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


def first_value(path: Path, key: str) -> str:
    target = f"{key}:"
    bullet_target = f"- {target}"
    lines = [line.strip() for line in read_text(path).splitlines()]
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt.strip("` ")
        if line.startswith(target):
            value = line[len(target) :].strip()
            if value:
                return value.strip("` ")
        if line.startswith(bullet_target):
            value = line[len(bullet_target) :].strip()
            if value:
                return value.strip("` ")
    return ""


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
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(value[: len(fmt)], fmt).date()
        except Exception:
            continue
    try:
        return dt.date.fromisoformat(value[:10])
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
    for name in names:
        if name in row and str(row.get(name, "")).strip():
            return str(row.get(name, "")).strip()
    return ""


def find_ranked_candidates(root: Path) -> Tuple[Path, List[Dict[str, str]], List[str], str]:
    primary = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
    fallback = root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv"
    rows, fields, status = read_csv(primary)
    if status == "OK" and rows:
        return primary, rows, fields, status
    rows, fields, status = read_csv(fallback)
    return fallback, rows, fields, status


def detect_signal_date(rows: Sequence[Dict[str, str]], current_read_first: Path, v14b_read_first: Path) -> str:
    for row in rows:
        value = pick(row, ["signal_date", "snapshot_date", "latest_price_date", "price_date", "date"])
        parsed = parse_date(value)
        if parsed:
            return parsed.isoformat()
    for path in (v14b_read_first, current_read_first):
        for key in ("SIGNAL_DATE", "PRICE_DATE", "RUN_DATE", "DATE"):
            parsed = parse_date(first_value(path, key))
            if parsed:
                return parsed.isoformat()
    return dt.date.today().isoformat()


def tracker_key(row: Dict[str, str]) -> Tuple[str, str, str]:
    return (row.get("signal_date", ""), row.get("ticker", ""), row.get("rank_source", ""))


def local_price_files(root: Path) -> List[Path]:
    bases = [
        root / "outputs/v18/data",
        root / "outputs/v18/prices",
        root / "outputs/v18/daily_integrated",
        root / "outputs/v18/read_center",
        root / "outputs/v16/data",
        root / "outputs/v15/data",
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


def load_price_points(root: Path, audit_rows: List[Dict[str, str]]) -> Dict[str, Dict[dt.date, float]]:
    price_by_ticker: Dict[str, Dict[dt.date, float]] = {}
    date_cols = ("date", "Date", "price_date", "latest_price_date", "snapshot_date", "snapshot_price_date", "score_date")
    close_cols = ("close", "Close", "latest_close", "last_price_usd", "current_price", "baseline_close", "target_close_1obs")
    ticker_cols = ("ticker", "symbol", "yf_ticker")
    used = 0
    for path in local_price_files(root):
        rows, fields, status = read_csv(path)
        if status != "OK" or not rows:
            continue
        has_ticker = any(col in fields for col in ticker_cols)
        has_date = any(col in fields for col in date_cols)
        has_close = any(col in fields for col in close_cols)
        if not (has_ticker and has_date and has_close):
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
            used += 1
            audit_rows.append(audit_row(f"PRICE_SOURCE_{used}", path, rows=len(rows), columns=fields, status="USED_FOR_PRICE_CONTEXT", notes=f"price_points={points}"))
    return price_by_ticker


def future_price(points: Dict[dt.date, float], signal_date: dt.date, min_days: int) -> Tuple[Optional[dt.date], Optional[float]]:
    future_dates = sorted(day for day in points if day > signal_date)
    if len(future_dates) >= min_days:
        day = future_dates[min_days - 1]
        return day, points[day]
    return None, None


def update_forward(row: Dict[str, str], price_by_ticker: Dict[str, Dict[dt.date, float]]) -> bool:
    ticker = row.get("ticker", "").upper()
    signal_day = parse_date(row.get("signal_date", ""))
    price_at_signal = parse_float(row.get("price_at_signal", ""))
    if not ticker or not signal_day:
        row["validation_status"] = "PENDING_SIGNAL_DATE"
        return False
    if price_at_signal is None:
        row["validation_status"] = "PENDING_SIGNAL_PRICE"
        return False
    points = price_by_ticker.get(ticker, {})
    changed = False
    completed = True
    forward_prices: List[float] = []
    for horizon in (1, 3, 5, 10, 20):
        price_key = f"forward_{horizon}d_price"
        ret_key = f"forward_{horizon}d_return"
        _, price = future_price(points, signal_day, horizon)
        if price is None:
            completed = False
            continue
        forward_prices.append(price)
        old_price = row.get(price_key, "")
        old_ret = row.get(ret_key, "")
        ret = price / price_at_signal - 1
        row[price_key] = fmt_float(price)
        row[ret_key] = fmt_float(ret)
        if row[price_key] != old_price or row[ret_key] != old_ret:
            changed = True
    if forward_prices:
        max_runup = max(price / price_at_signal - 1 for price in forward_prices)
        max_drawdown = min(price / price_at_signal - 1 for price in forward_prices)
        old_runup = row.get("max_runup_20d", "")
        old_drawdown = row.get("max_drawdown_20d", "")
        row["max_runup_20d"] = fmt_float(max_runup)
        row["max_drawdown_20d"] = fmt_float(max_drawdown)
        changed = changed or row["max_runup_20d"] != old_runup or row["max_drawdown_20d"] != old_drawdown
    old_status = row.get("validation_status", "")
    row["validation_status"] = "FORWARD_COMPLETE" if completed else "PENDING_FORWARD_DATA"
    return changed or row["validation_status"] != old_status


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


def build(root: Path, max_rank: int, use_yfinance: bool) -> Tuple[Dict[str, str], int]:
    state_path = root / "state/v18/candidate_forward_tracker/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"
    out_tracker = root / "outputs/v18/candidates/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"
    out_tracker_audit = root / "outputs/v18/candidates/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER_AUDIT.csv"
    read_first = root / "outputs/v18/ops/V18_14C_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER_REPORT.md"
    summary_path = root / "outputs/v18/ops/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER_SUMMARY.csv"
    input_audit_path = root / "outputs/v18/ops/V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER_INPUT_AUDIT.csv"

    current_read_first = root / "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt"
    v14b_read_first = root / "outputs/v18/ops/V18_14B_READ_FIRST.txt"
    ranked_path, ranked_rows_all, ranked_fields, ranked_status = find_ranked_candidates(root)
    ranked_rows = sorted(ranked_rows_all, key=lambda row: int(parse_float(row.get("rank", "999999")) or 999999))[:max_rank]
    signal_date = detect_signal_date(ranked_rows, current_read_first, v14b_read_first)
    rank_source = "V18_CURRENT_RANKED_CANDIDATES" if ranked_path.name == "V18_CURRENT_RANKED_CANDIDATES.csv" else "V18_13B_CURRENT_RANKED_CANDIDATES"

    input_audit: List[Dict[str, str]] = [
        audit_row("PRIMARY_RANKED_CANDIDATES", root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv", len(read_csv(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv")[0]), read_csv(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv")[1], "OK" if (root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv").exists() else "MISSING", "PRIMARY_INPUT"),
        audit_row("FALLBACK_RANKED_CANDIDATES", root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv", len(read_csv(root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv")[0]), read_csv(root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv")[1], "OK" if (root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv").exists() else "MISSING", "FALLBACK_INPUT"),
        audit_row("CURRENT_READ_FIRST", current_read_first, 0, [], "OK_TEXT" if current_read_first.exists() else "MISSING", "RUN_CONTEXT"),
        audit_row("V18_14B_READ_FIRST", v14b_read_first, 0, [], "OK_TEXT" if v14b_read_first.exists() else "MISSING", "RUN_CONTEXT"),
    ]

    tracker_rows, _, _ = read_csv(state_path)
    normalized_rows: List[Dict[str, str]] = []
    for row in tracker_rows:
        normalized_rows.append({col: row.get(col, "") for col in TRACKER_COLUMNS})
    tracker_rows = normalized_rows
    existing_keys = {tracker_key(row) for row in tracker_rows}

    run_mode = first_value(v14b_read_first, "RUN_MODE") or first_value(current_read_first, "RUN_MODE")
    full_daily_mode_status = first_value(v14b_read_first, "FULL_DAILY_MODE_STATUS")
    official_daily_status = first_value(v14b_read_first, "OFFICIAL_DAILY_STATUS") or first_value(current_read_first, "OFFICIAL_DAILY_STATUS")
    v14b_status = first_value(v14b_read_first, "STATUS")
    v14a_status = first_value(v14b_read_first, "V18_14A_STATUS")
    top_5 = first_value(v14b_read_first, "TOP_5_TICKERS") or ",".join(row.get("ticker", "") for row in ranked_rows[:5])
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_count = 0
    for row in ranked_rows:
        ticker = row.get("ticker", "").strip().upper()
        if not ticker:
            continue
        new_row = {col: "" for col in TRACKER_COLUMNS}
        new_row.update(
            {
                "signal_date": signal_date,
                "ticker": ticker,
                "rank": row.get("rank", ""),
                "rank_source": rank_source,
                "score": pick(row, ["composite_candidate_score", "score", "candidate_score"]),
                "price_at_signal": pick(row, ["latest_close", "close", "price_at_signal"]),
                "price_date": pick(row, ["latest_price_date", "price_date"]),
                "sector": pick(row, ["sector"]),
                "industry": pick(row, ["industry"]),
                "factor_score": pick(row, ["factor_pack_score", "factor_score"]),
                "technical_score": pick(row, ["technical_timing_score", "technical_score"]),
                "risk_label": pick(row, ["event_risk_status", "risk_label", "technical_status"]),
                "run_mode": run_mode,
                "full_daily_mode_status": full_daily_mode_status,
                "official_daily_status": official_daily_status,
                "v18_14b_status": v14b_status,
                "v18_14a_status": v14a_status,
                "top_5_snapshot": top_5,
                "validation_status": "PENDING_SIGNAL_PRICE" if not pick(row, ["latest_close", "close", "price_at_signal"]) else "PENDING_FORWARD_DATA",
                "last_updated": now,
                "notes": "FORWARD_VALIDATION_RESEARCH_ONLY",
            }
        )
        key = tracker_key(new_row)
        if key not in existing_keys:
            tracker_rows.append(new_row)
            existing_keys.add(key)
            new_count += 1

    price_by_ticker = load_price_points(root, input_audit)
    updated_forward = 0
    for row in tracker_rows:
        changed = update_forward(row, price_by_ticker)
        if changed:
            row["last_updated"] = now
            updated_forward += 1

    duplicate_count = len(tracker_rows) - len({tracker_key(row) for row in tracker_rows})
    forward_complete = sum(1 for row in tracker_rows if row.get("validation_status") == "FORWARD_COMPLETE")
    pending_forward = sum(1 for row in tracker_rows if row.get("validation_status", "").startswith("PENDING"))

    failures: List[str] = []
    if ranked_status != "OK" or not ranked_rows_all:
        failures.append("RANKED_CANDIDATES_INPUT_MISSING_OR_UNREADABLE")
    if duplicate_count:
        failures.append("DUPLICATE_TRACKER_KEYS_DETECTED")
    if OFFICIAL_DECISION_IMPACT != "NONE":
        failures.append("OFFICIAL_DECISION_IMPACT_NOT_NONE")
    if AUTO_TRADE != "DISABLED":
        failures.append("AUTO_TRADE_NOT_DISABLED")
    if AUTO_SELL != "DISABLED":
        failures.append("AUTO_SELL_NOT_DISABLED")

    write_csv(state_path, tracker_rows, TRACKER_COLUMNS)
    ensure_dir(out_tracker.parent)
    shutil.copy2(state_path, out_tracker)
    tracker_audit_rows = [
        {"metric": "state_path", "value": str(state_path)},
        {"metric": "output_path", "value": str(out_tracker)},
        {"metric": "dedup_key", "value": "signal_date+ticker+rank_source"},
        {"metric": "duplicate_count", "value": str(duplicate_count)},
        {"metric": "price_source_file_count", "value": str(sum(1 for row in input_audit if row["input_name"].startswith("PRICE_SOURCE_")))},
        {"metric": "use_yfinance", "value": "TRUE" if use_yfinance else "FALSE"},
    ]
    write_csv(out_tracker_audit, tracker_audit_rows, ["metric", "value"])

    scan_paths = [state_path, out_tracker, out_tracker_audit, read_first, report_path, summary_path, input_audit_path]
    pre_hits = scan_tokens(root, [state_path, out_tracker, out_tracker_audit])
    if pre_hits:
        failures.append("DANGEROUS_TOKEN_DETECTED")

    status = STATUS_OK if not failures else STATUS_FAIL
    values = {
        "STATUS": status,
        "SIGNAL_DATE": signal_date,
        "RANK_SOURCE": rank_source,
        "TRACKER_ROWS": str(len(tracker_rows)),
        "NEW_SIGNAL_ROWS_ADDED": str(new_count),
        "UPDATED_FORWARD_ROWS": str(updated_forward),
        "FORWARD_COMPLETE_ROWS": str(forward_complete),
        "PENDING_FORWARD_ROWS": str(pending_forward),
        "TOP_5_TICKERS": top_5,
        "VALIDATION_FAIL_COUNT": str(len(failures)),
        "FAIL_REASONS": ";".join(failures) if failures else "NONE",
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "FORWARD_VALIDATION_ONLY": FORWARD_VALIDATION_ONLY,
        "DANGEROUS_TOKEN_DETECTED": "YES" if pre_hits else "NO",
        "TRACKER_CSV": rel(root, state_path),
        "READ_FIRST": rel(root, read_first),
    }

    read_first_keys = [
        "STATUS",
        "SIGNAL_DATE",
        "RANK_SOURCE",
        "TRACKER_ROWS",
        "NEW_SIGNAL_ROWS_ADDED",
        "UPDATED_FORWARD_ROWS",
        "FORWARD_COMPLETE_ROWS",
        "PENDING_FORWARD_ROWS",
        "TOP_5_TICKERS",
        "VALIDATION_FAIL_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "FORWARD_VALIDATION_ONLY",
    ]
    write_text(read_first, "\n".join(f"{key}: {values[key]}" for key in read_first_keys) + f"\nFAIL_REASONS: {values['FAIL_REASONS']}\nDANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}\nTRACKER_CSV: {values['TRACKER_CSV']}\n")

    summary_row = {
        "status": values["STATUS"],
        "signal_date": signal_date,
        "rank_source": rank_source,
        "tracker_rows": values["TRACKER_ROWS"],
        "new_signal_rows_added": values["NEW_SIGNAL_ROWS_ADDED"],
        "updated_forward_rows": values["UPDATED_FORWARD_ROWS"],
        "forward_complete_rows": values["FORWARD_COMPLETE_ROWS"],
        "pending_forward_rows": values["PENDING_FORWARD_ROWS"],
        "top_5_tickers": top_5,
        "validation_fail_count": values["VALIDATION_FAIL_COUNT"],
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "read_only": READ_ONLY,
        "forward_validation_only": FORWARD_VALIDATION_ONLY,
        "read_first": rel(root, read_first),
    }
    write_csv(summary_path, [summary_row], SUMMARY_FIELDS)
    write_csv(input_audit_path, input_audit, AUDIT_FIELDS)

    report_lines = [
        "# V18.14C Ranked Candidate Forward Tracker",
        "",
        "Research-only forward validation tracker. No trading, selling, or official decision impact.",
        "",
        "## Status",
        "",
    ]
    report_lines.extend(f"- {key}: {values[key]}" for key in read_first_keys)
    report_lines.extend(
        [
            f"- FAIL_REASONS: {values['FAIL_REASONS']}",
            f"- DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}",
            f"- TRACKER_CSV: {values['TRACKER_CSV']}",
            "",
            "## Pending Price Data",
            "",
            f"- Price source files used: {sum(1 for row in input_audit if row['input_name'].startswith('PRICE_SOURCE_'))}",
            f"- Pending forward rows: {pending_forward}",
            "",
            "## Current Signals",
            "",
        ]
    )
    report_lines.extend(markdown_table(tracker_rows[-max_rank:], ["signal_date", "ticker", "rank", "rank_source", "price_at_signal", "validation_status"]))
    write_text(report_path, "\n".join(report_lines) + "\n")

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
    print(f"TRACKER_CSV: {values['TRACKER_CSV']}")
    return values, 0 if values["STATUS"] == STATUS_OK else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.14C ranked candidate forward validation tracker.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--max-rank", type=int, default=20)
    parser.add_argument("--use-yfinance", action="store_true")
    args = parser.parse_args()
    _, code = build(Path(args.root), args.max_rank, args.use_yfinance)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
