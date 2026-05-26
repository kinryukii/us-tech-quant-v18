from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


RETURN_LABEL_COLUMNS = {
    1: "fwd_1d_return",
    5: "fwd_5d_return",
    10: "fwd_10d_return",
    20: "fwd_20d_return",
}


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def norm(s: str) -> str:
    return str(s or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return rows, fields


def write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def find_col(fields: List[str], names: List[str]) -> Optional[str]:
    nmap = {norm(f): f for f in fields}

    for name in names:
        nn = norm(name)
        if nn in nmap:
            return nmap[nn]

    for name in names:
        nn = norm(name)
        if len(nn) < 4:
            continue
        for f in fields:
            if nn in norm(f):
                return f

    return None


def detect_source_paths(root: Path) -> List[Path]:
    paths = [
        root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
    ]
    return [p for p in paths if p.exists()]


def choose_source(root: Path) -> Tuple[Optional[Path], List[Dict[str, str]], List[str], List[Dict[str, str]]]:
    source_rows = []

    best_path = None
    best_rows: List[Dict[str, str]] = []
    best_fields: List[str] = []
    best_score = (-1, -1)

    for p in detect_source_paths(root):
        rows, fields = read_csv(p)

        forward_cells = 0
        label_fields = {f for f in fields if norm(f) in {norm(x) for x in RETURN_LABEL_COLUMNS.values()}}
        for f in label_fields:
                forward_cells += sum(1 for r in rows if str(r.get(f, "")).strip() != "")

        score = (len(rows), forward_cells)

        source_rows.append({
            "path": str(p),
            "rows": str(len(rows)),
            "columns": str(len(fields)),
            "forward_nonblank_cells": str(forward_cells),
        })

        if score > best_score:
            best_score = score
            best_path = p
            best_rows = rows
            best_fields = fields

    return best_path, best_rows, best_fields, source_rows


def detect_label_cols(fields: List[str]) -> Dict[int, Optional[str]]:
    aliases = {
        1: ["fwd_1d_return", "forward_return_1d", "fwd_1d", "fwd_return_1d", "return_1d", "return_1d_pct", "forward_1d_return"],
        5: ["fwd_5d_return", "forward_return_5d", "fwd_5d", "fwd_return_5d", "return_5d", "return_5d_pct", "forward_5d_return"],
        10: ["fwd_10d_return", "forward_return_10d", "fwd_10d", "fwd_return_10d", "return_10d", "return_10d_pct", "forward_10d_return"],
        20: ["fwd_20d_return", "forward_return_20d", "fwd_20d", "fwd_return_20d", "return_20d", "return_20d_pct", "forward_20d_return"],
    }
    out: Dict[int, Optional[str]] = {}
    for h, names in aliases.items():
        out[h] = find_col(fields, names)
    return out


def parse_date(x: str) -> Optional[dt.date]:
    s = str(x or "").strip()
    if not s:
        return None

    # Keep date part if datetime-like.
    s = s.replace("/", "-")
    if "T" in s:
        s = s.split("T")[0]
    if " " in s:
        s = s.split(" ")[0]

    formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return dt.datetime.strptime(s, fmt).date()
        except Exception:
            pass

    return None


def extract_price_date_from_source_text(text: str) -> Optional[dt.date]:
    if not text:
        return None

    patterns = [
        r"(?:latest_price_date|price_date|latest_date|asof_date|snapshot_price_date)\s*=\s*(\d{4}-\d{2}-\d{2})",
        r"(?:latest_price_date|price_date|latest_date|asof_date|snapshot_price_date)\s*:\s*(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in patterns:
        m = re.search(pattern, str(text), flags=re.IGNORECASE)
        if m:
            return parse_date(m.group(1))

    return None


def row_base_date(row: Dict[str, str], date_col: Optional[str]) -> Tuple[Optional[dt.date], str, str]:
    price_date = extract_price_date_from_source_text(row.get("source_row_text", ""))
    if price_date is not None:
        return price_date, "source_row_text.price_date", str(price_date)

    raw = row.get(date_col, "") if date_col else ""
    snapshot_date = parse_date(raw)
    if snapshot_date is not None:
        return snapshot_date, date_col or "snapshot_date", str(snapshot_date)

    return None, "missing", ""


def load_yfinance_history(
    tickers: List[str],
    min_base_date: Optional[dt.date],
    as_of: dt.date,
) -> Tuple[Dict[str, List[dt.date]], str]:
    if min_base_date is None or not tickers:
        return {}, "YFINANCE_UNAVAILABLE_CONSERVATIVE"

    try:
        import yfinance as yf
    except Exception:
        return {}, "YFINANCE_UNAVAILABLE_CONSERVATIVE"

    start = (min_base_date - dt.timedelta(days=10)).strftime("%Y-%m-%d")
    end = (as_of + dt.timedelta(days=5)).strftime("%Y-%m-%d")
    history: Dict[str, List[dt.date]] = {}
    any_history = False

    for ticker in sorted(set(tickers)):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                progress=False,
                auto_adjust=False,
                threads=False,
            )
        except Exception:
            history[ticker] = []
            continue

        if df is None or df.empty:
            history[ticker] = []
            continue

        dates: List[dt.date] = []
        for idx in df.index:
            try:
                d = idx.date()
            except Exception:
                d = parse_date(str(idx))
            if d is not None and d <= as_of:
                dates.append(d)

        dates = sorted(set(dates))
        history[ticker] = dates
        if dates:
            any_history = True

    if not any_history:
        return history, "YFINANCE_UNAVAILABLE_CONSERVATIVE"

    return history, "YFINANCE_OK"


def yfinance_maturity_status(
    history_by_ticker: Dict[str, List[dt.date]],
    ticker: str,
    base_date: Optional[dt.date],
    horizon: int,
    yf_status: str,
) -> Tuple[str, str, str, str]:
    method = "YFINANCE_TRADING_DAY"

    if yf_status != "YFINANCE_OK":
        return "NOT_YET_MATURE", method, yf_status, ""

    if base_date is None:
        return "UNKNOWN_MISSING_DATE", method, "NO_BASE_DATE", ""

    series = history_by_ticker.get(str(ticker or "").strip().upper(), [])
    if not series:
        return "NOT_YET_MATURE", method, "NO_YFINANCE_HISTORY_CONSERVATIVE", ""

    exact = [i for i, d in enumerate(series) if d == base_date]
    if exact:
        base_idx = exact[-1]
    else:
        before = [i for i, d in enumerate(series) if d <= base_date]
        if not before:
            return "NOT_YET_MATURE", method, "NO_YFINANCE_BASE_INDEX_CONSERVATIVE", ""
        base_idx = before[-1]

    target_idx = base_idx + horizon
    if target_idx >= len(series):
        return "NOT_YET_MATURE", method, "PENDING_NOT_ENOUGH_TRADING_DAYS", ""

    return "TRADING_DAY_MATURE", method, "YFINANCE_HORIZON_MATURE", str(series[target_idx])


def is_nonblank(x: str) -> bool:
    s = str(x or "").strip()
    return s != "" and s.lower() not in ("nan", "none", "null", "na", "n/a")


def detect_date_col(fields: List[str]) -> Optional[str]:
    return find_col(fields, [
        "snapshot_date",
        "candidate_date",
        "signal_date",
        "as_of_date",
        "trade_date",
        "date",
        "price_date",
        "latest_price_date",
    ])


def detect_ticker_col(fields: List[str]) -> Optional[str]:
    return find_col(fields, ["ticker", "symbol", "asset", "name"])


def maturity_status(
    ready: bool,
    mature_blank: int,
    not_mature_blank: int,
    date_col: Optional[str],
    yf_status: str,
) -> str:
    if ready:
        return "READY_FOR_FACTOR_BACKTEST"

    if yf_status != "YFINANCE_OK":
        return "WAIT_YFINANCE_UNAVAILABLE_CONSERVATIVE"

    if date_col is None:
        return "WAIT_NO_DATE_COLUMN_FOR_BASE_DATE"

    if mature_blank > 0:
        return "MATURE_BUT_FORWARD_RETURN_NOT_FILLED"

    if not_mature_blank > 0:
        return "WAIT_FOR_FORWARD_HORIZON_TO_MATURE"

    return "WAIT_FOR_MORE_SAMPLES"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--min-count", type=int, default=20)
    ap.add_argument("--as-of-date", default="")
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = root / "outputs/v18/factor_research"
    ensure_dir(out_dir)

    as_of = parse_date(args.as_of_date) if args.as_of_date else dt.date.today()

    maturity_path = out_dir / "V18_10B_R1_CURRENT_FORWARD_RETURN_MATURITY.csv"
    pending_path = out_dir / "V18_10B_R1_CURRENT_FORWARD_RETURN_PENDING_ROWS.csv"
    source_audit_path = out_dir / "V18_10B_R1_CURRENT_FORWARD_RETURN_SOURCE_AUDIT.csv"
    report_path = out_dir / "V18_10B_R1_CURRENT_FORWARD_RETURN_MATURITY_REPORT.md"
    read_first_path = out_dir / "V18_10B_R1_READ_FIRST.txt"

    source_path, rows, fields, source_audit = choose_source(root)

    date_col = detect_date_col(fields)
    ticker_col = detect_ticker_col(fields)
    label_cols = detect_label_cols(fields)
    tickers = sorted({str(r.get(ticker_col, "")).strip().upper() for r in rows if ticker_col and str(r.get(ticker_col, "")).strip()})
    base_dates = [row_base_date(r, date_col)[0] for r in rows]
    min_base_date = min([d for d in base_dates if d is not None], default=None)
    history_by_ticker, yf_status = load_yfinance_history(tickers, min_base_date, as_of)

    maturity_rows: List[Dict[str, str]] = []
    pending_rows: List[Dict[str, str]] = []

    for horizon in [1, 5, 10, 20]:
        label_col = label_cols.get(horizon)

        total_rows = len(rows)
        nonblank = 0
        blank = 0
        trading_day_mature = 0
        trading_day_not_mature = 0
        mature_blank = 0
        not_mature_blank = 0
        missing_date = 0

        for idx, r in enumerate(rows):
            label_value = r.get(label_col, "") if label_col else ""
            has_label = is_nonblank(label_value)

            if has_label:
                nonblank += 1
            else:
                blank += 1

            ticker = r.get(ticker_col, "") if ticker_col else ""
            base_date, base_date_source, base_date_raw = row_base_date(r, date_col)
            row_maturity, maturity_method, maturity_reason, target_date = yfinance_maturity_status(
                history_by_ticker=history_by_ticker,
                ticker=ticker,
                base_date=base_date,
                horizon=horizon,
                yf_status=yf_status,
            )

            if row_maturity == "UNKNOWN_MISSING_DATE":
                missing_date += 1
            elif row_maturity == "TRADING_DAY_MATURE":
                trading_day_mature += 1
            else:
                trading_day_not_mature += 1

            if not has_label:
                if row_maturity == "TRADING_DAY_MATURE":
                    mature_blank += 1
                elif row_maturity == "NOT_YET_MATURE":
                    not_mature_blank += 1

                pending_rows.append({
                    "row_index": str(idx),
                    "ticker": ticker,
                    "horizon": f"{horizon}D",
                    "label_column": label_col or "",
                    "label_status": "BLANK",
                    "date_column": date_col or "",
                    "base_date": base_date_raw,
                    "base_date_source": base_date_source,
                    "as_of_date": str(as_of),
                    "maturity_method": maturity_method,
                    "maturity_reason": maturity_reason,
                    "target_price_date": target_date,
                    "trading_day_maturity_status": row_maturity,
                    "recommended_action": "RUN_FORWARD_FILLER" if row_maturity == "TRADING_DAY_MATURE" else "WAIT_MATURITY",
                })

        ready = nonblank >= args.min_count and trading_day_mature >= args.min_count and yf_status == "YFINANCE_OK"
        status = maturity_status(
            ready=ready,
            mature_blank=mature_blank,
            not_mature_blank=not_mature_blank,
            date_col=date_col,
            yf_status=yf_status,
        )

        maturity_rows.append({
            "horizon": f"{horizon}D",
            "label_column": label_col or "",
            "source_rows": str(total_rows),
            "label_nonblank_count": str(nonblank),
            "label_blank_count": str(blank),
            "trading_day_mature_count": str(trading_day_mature),
            "trading_day_not_mature_count": str(trading_day_not_mature),
            "mature_but_label_blank_count": str(mature_blank),
            "not_yet_mature_blank_count": str(not_mature_blank),
            "missing_date_count": str(missing_date),
            "base_date_source": "source_row_text.price_date_preferred_snapshot_date_fallback",
            "maturity_method": "YFINANCE_TRADING_DAY_CONSERVATIVE",
            "yfinance_status": yf_status,
            "min_count_required": str(args.min_count),
            "ready_for_factor_backtest": "YES" if ready else "NO",
            "maturity_status": status,
        })

    write_csv(maturity_path, maturity_rows, [
        "horizon",
        "label_column",
        "source_rows",
        "label_nonblank_count",
        "label_blank_count",
        "trading_day_mature_count",
        "trading_day_not_mature_count",
        "mature_but_label_blank_count",
        "not_yet_mature_blank_count",
        "missing_date_count",
        "base_date_source",
        "maturity_method",
        "yfinance_status",
        "min_count_required",
        "ready_for_factor_backtest",
        "maturity_status",
    ])

    write_csv(pending_path, pending_rows, [
        "row_index",
        "ticker",
        "horizon",
        "label_column",
        "label_status",
        "date_column",
        "base_date",
        "base_date_source",
        "as_of_date",
        "maturity_method",
        "maturity_reason",
        "target_price_date",
        "trading_day_maturity_status",
        "recommended_action",
    ])

    write_csv(source_audit_path, source_audit, [
        "path",
        "rows",
        "columns",
        "forward_nonblank_cells",
    ])

    ready_count = sum(1 for r in maturity_rows if r["ready_for_factor_backtest"] == "YES")
    all_label_nonblank = sum(int(r["label_nonblank_count"]) for r in maturity_rows)
    all_mature_blank = sum(int(r["mature_but_label_blank_count"]) for r in maturity_rows)

    report = []
    report.append("# V18.10B-R1 Forward Return Maturity Monitor")
    report.append("")
    report.append(f"Generated: `{now_text()}`")
    report.append("")
    report.append("## 1. Status")
    report.append("")
    report.append("- STATUS: `OK_FORWARD_RETURN_MATURITY_MONITOR_READY`")
    report.append("- MODE: `SHADOW_ONLY_MATURITY_GUARD`")
    report.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    report.append("- AUTO_WEIGHT_CHANGE: `DISABLED`")
    report.append("- AUTO_PROMOTION: `DISABLED`")
    report.append("- AUTO_TRADE: `DISABLED`")
    report.append("")
    report.append("## 2. Source")
    report.append("")
    report.append(f"- SELECTED_SOURCE: `{source_path}`")
    report.append(f"- SOURCE_ROWS: `{len(rows)}`")
    report.append(f"- DATE_COLUMN: `{date_col or ''}`")
    report.append(f"- TICKER_COLUMN: `{ticker_col or ''}`")
    report.append(f"- AS_OF_DATE: `{as_of}`")
    report.append(f"- MIN_COUNT_REQUIRED: `{args.min_count}`")
    report.append("- BASE_DATE_SOURCE: `source_row_text.price_date preferred; snapshot_date fallback`")
    report.append("- MATURITY_METHOD: `YFINANCE_TRADING_DAY_CONSERVATIVE`")
    report.append(f"- YFINANCE_STATUS: `{yf_status}`")
    report.append("")
    report.append("## 3. Maturity summary")
    report.append("")
    report.append("| horizon | label_column | nonblank | trading_mature | mature_blank | not_yet_mature_blank | ready | status |")
    report.append("|---|---|---:|---:|---:|---:|---|---|")
    for r in maturity_rows:
        report.append(
            f"| {r['horizon']} | {r['label_column']} | {r['label_nonblank_count']} | "
            f"{r['trading_day_mature_count']} | {r['mature_but_label_blank_count']} | {r['not_yet_mature_blank_count']} | "
            f"{r['ready_for_factor_backtest']} | {r['maturity_status']} |"
        )
    report.append("")
    report.append("## 4. Interpretation")
    report.append("")
    report.append("- `READY_FOR_FACTOR_BACKTEST`: enough nonblank labels exist for that horizon.")
    report.append("- `WAIT_FOR_FORWARD_HORIZON_TO_MATURE`: YFinance trading history does not prove the horizon is mature yet.")
    report.append("- `MATURE_BUT_FORWARD_RETURN_NOT_FILLED`: YFinance proves the horizon is mature, but labels are still blank; rerun forward filler.")
    report.append("- `WAIT_NO_DATE_COLUMN_FOR_BASE_DATE`: no embedded market price date or fallback snapshot date was found.")
    report.append("- If YFinance is unavailable, this monitor stays conservative and does not mark horizons ready.")
    report.append("")
    report.append("## 5. Outputs")
    report.append("")
    report.append(f"- MATURITY: `{maturity_path}`")
    report.append(f"- PENDING_ROWS: `{pending_path}`")
    report.append(f"- SOURCE_AUDIT: `{source_audit_path}`")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first_path}`")
    report.append("")
    report.append("## 6. Next step")
    report.append("")
    if ready_count == 0:
        if all_mature_blank > 0:
            report.append("Some horizons appear mature but labels are blank. Run V18.9B forward return filler with `-UseYFinance`, then rerun V18.10B.")
        else:
            report.append("No horizon has enough mature labels yet. Continue daily candidate tracking and forward return filling.")
    else:
        report.append("At least one horizon is ready. Rerun V18.10B factor effectiveness backtest and review summary.")
    report.append("")

    report_path.write_text("\n".join(report), encoding="utf-8")

    read_first = f"""V18.10B-R1 FORWARD RETURN MATURITY MONITOR READ FIRST

STATUS:
OK_FORWARD_RETURN_MATURITY_MONITOR_READY

MODE:
SHADOW_ONLY_MATURITY_GUARD

OFFICIAL_DECISION_IMPACT:
NONE

AUTO_WEIGHT_CHANGE:
DISABLED

AUTO_PROMOTION:
DISABLED

AUTO_TRADE:
DISABLED

SELECTED_SOURCE:
{source_path}

SOURCE_ROWS:
{len(rows)}

DATE_COLUMN:
{date_col or ""}

TICKER_COLUMN:
{ticker_col or ""}

AS_OF_DATE:
{as_of}

MIN_COUNT_REQUIRED:
{args.min_count}

BASE_DATE_SOURCE:
source_row_text.price_date preferred; snapshot_date fallback

MATURITY_METHOD:
YFINANCE_TRADING_DAY_CONSERVATIVE

YFINANCE_STATUS:
{yf_status}

READY_HORIZON_COUNT:
{ready_count}

TOTAL_LABEL_NONBLANK_COUNT:
{all_label_nonblank}

TOTAL_MATURE_BUT_LABEL_BLANK_COUNT:
{all_mature_blank}

MATURITY:
{maturity_path}

PENDING_ROWS:
{pending_path}

SOURCE_AUDIT:
{source_audit_path}

REPORT:
{report_path}

READ_FIRST:
{read_first_path}

NEXT_STEP:
If READY_HORIZON_COUNT is 0, do not adjust weights.
If TOTAL_MATURE_BUT_LABEL_BLANK_COUNT is greater than 0, run:
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_9B_forward_return_filler.ps1" -UseYFinance

Then rerun:
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_10B_factor_effectiveness_backtest.ps1"
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.10B-R1 FORWARD RETURN MATURITY MONITOR READY ===")
    print("STATUS: OK_FORWARD_RETURN_MATURITY_MONITOR_READY")
    print("MODE: SHADOW_ONLY_MATURITY_GUARD")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("AUTO_WEIGHT_CHANGE: DISABLED")
    print("AUTO_PROMOTION: DISABLED")
    print("AUTO_TRADE: DISABLED")
    print(f"SELECTED_SOURCE: {source_path}")
    print(f"SOURCE_ROWS: {len(rows)}")
    print(f"DATE_COLUMN: {date_col or ''}")
    print(f"TICKER_COLUMN: {ticker_col or ''}")
    print(f"AS_OF_DATE: {as_of}")
    print(f"MIN_COUNT_REQUIRED: {args.min_count}")
    print("BASE_DATE_SOURCE: source_row_text.price_date preferred; snapshot_date fallback")
    print("MATURITY_METHOD: YFINANCE_TRADING_DAY_CONSERVATIVE")
    print(f"YFINANCE_STATUS: {yf_status}")
    print(f"READY_HORIZON_COUNT: {ready_count}")
    print(f"TOTAL_LABEL_NONBLANK_COUNT: {all_label_nonblank}")
    print(f"TOTAL_MATURE_BUT_LABEL_BLANK_COUNT: {all_mature_blank}")
    print(f"MATURITY: {maturity_path}")
    print(f"PENDING_ROWS: {pending_path}")
    print(f"SOURCE_AUDIT: {source_audit_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
