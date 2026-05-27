import argparse
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path


HORIZONS = [1, 5, 10, 20]


def read_csv_rows(path: Path):
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def write_csv_rows(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("$", "").replace("¥", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def parse_date(s):
    if not s:
        return None
    s = str(s).strip()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except Exception:
        return None


def extract_price_date_from_source_text(text):
    if not text:
        return None

    patterns = [
        r"(?:latest_price_date|price_date|latest_date|asof_date|snapshot_price_date)\s*=\s*(\d{4}-\d{2}-\d{2})",
        r"(?:latest_price_date|price_date|latest_date|asof_date|snapshot_price_date)\s*:\s*(\d{4}-\d{2}-\d{2})",
    ]

    for p in patterns:
        m = re.search(p, str(text), flags=re.IGNORECASE)
        if m:
            return parse_date(m.group(1))

    return None


def pick_col(rows, candidates):
    if not rows:
        return None
    cols = list(rows[0].keys())
    lower = {c.lower(): c for c in cols}

    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]

    for c in cols:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c

    return None


def build_local_price_map(tech_rows):
    price_map = {}

    if not tech_rows:
        return price_map

    ticker_col = pick_col(tech_rows, ["ticker", "symbol"])
    price_col = pick_col(tech_rows, ["latest_close", "last_close", "close", "price", "adj_close"])
    date_col = pick_col(tech_rows, ["latest_price_date", "price_date", "latest_date", "asof_date", "date"])

    if not ticker_col or not price_col:
        return price_map

    for r in tech_rows:
        t = str(r.get(ticker_col, "")).strip().upper()
        p = normalize_num(r.get(price_col))
        d = parse_date(r.get(date_col)) if date_col else None

        if t and p and p > 0:
            price_map[t] = {
                "price": p,
                "price_date": d,
            }

    return price_map


def load_yfinance_history(tickers, min_date, max_date):
    out = {}

    try:
        import yfinance as yf
    except Exception as e:
        return out, f"YFINANCE_IMPORT_FAIL: {e}"

    if not tickers:
        return out, "NO_TICKERS"

    start = (min_date - timedelta(days=10)).strftime("%Y-%m-%d")
    end = (max_date + timedelta(days=5)).strftime("%Y-%m-%d")

    for t in sorted(tickers):
        try:
            df = yf.download(
                t,
                start=start,
                end=end,
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            if df is None or df.empty:
                out[t] = []
                continue

            if "Adj Close" in df.columns:
                s = df["Adj Close"]
            elif "Close" in df.columns:
                s = df["Close"]
            else:
                out[t] = []
                continue

            rows = []
            for idx, val in s.dropna().items():
                try:
                    d = idx.date()
                except Exception:
                    d = parse_date(str(idx))
                price = normalize_num(val)
                if d and price and price > 0:
                    rows.append((d, float(price)))

            rows = sorted(rows, key=lambda x: x[0])
            out[t] = rows
        except Exception:
            out[t] = []

    return out, "YFINANCE_OK"


def find_base_index(series, base_date):
    if not series or not base_date:
        return None

    # Prefer exact base date. If not available, use nearest trading date at or before base_date.
    exact = [i for i, (d, _) in enumerate(series) if d == base_date]
    if exact:
        return exact[-1]

    before = [i for i, (d, _) in enumerate(series) if d <= base_date]
    if before:
        return before[-1]

    return None


def compute_yf_forward(row, history_by_ticker, horizon):
    ticker = str(row.get("ticker", "")).strip().upper()
    series = history_by_ticker.get(ticker) or []

    base_price = normalize_num(row.get("latest_price_usd"))
    if base_price is None or base_price <= 0:
        return None, "", "", "NO_BASE_PRICE"

    base_date = extract_price_date_from_source_text(row.get("source_row_text", ""))
    if base_date is None:
        base_date = parse_date(row.get("snapshot_date"))

    if base_date is None:
        return None, "", "", "NO_BASE_DATE"

    base_idx = find_base_index(series, base_date)
    if base_idx is None:
        return None, "", "", "NO_YF_BASE_INDEX"

    target_idx = base_idx + horizon
    if target_idx >= len(series):
        return None, "", "", "PENDING_NOT_ENOUGH_TRADING_DAYS"

    target_date, target_price = series[target_idx]
    ret = (target_price / base_price) - 1.0

    return ret, target_date.strftime("%Y-%m-%d"), f"{target_price:.4f}", "FILLED_YFINANCE"


def compute_local_approx(row, local_price_map, horizon):
    ticker = str(row.get("ticker", "")).strip().upper()
    current = local_price_map.get(ticker)

    if not current:
        return None, "", "", "NO_LOCAL_CURRENT_PRICE"

    base_price = normalize_num(row.get("latest_price_usd"))
    if base_price is None or base_price <= 0:
        return None, "", "", "NO_BASE_PRICE"

    base_date = extract_price_date_from_source_text(row.get("source_row_text", ""))
    if base_date is None:
        base_date = parse_date(row.get("snapshot_date"))

    current_date = current.get("price_date")
    if current_date is None:
        current_date = datetime.now().date()

    if base_date is None:
        return None, "", "", "NO_BASE_DATE"

    age_days = (current_date - base_date).days
    if age_days < horizon:
        return None, "", "", "PENDING_LOCAL_AGE_LT_HORIZON"

    current_price = current.get("price")
    ret = (current_price / base_price) - 1.0

    return ret, current_date.strftime("%Y-%m-%d"), f"{current_price:.4f}", "FILLED_LOCAL_APPROX"


def ensure_fieldnames(rows):
    base = []
    for r in rows:
        for k in r.keys():
            if k not in base:
                base.append(k)

    additions = []
    for h in HORIZONS:
        additions += [
            f"fwd_{h}d_return",
            f"fwd_{h}d_price_date",
            f"fwd_{h}d_price_usd",
            f"fwd_{h}d_fill_method",
        ]

    additions += [
        "forward_status",
        "last_forward_fill_at",
    ]

    for k in additions:
        if k not in base:
            base.append(k)

    return base


def update_forward_status(row):
    filled = 0
    pending = 0

    for h in HORIZONS:
        v = str(row.get(f"fwd_{h}d_return", "")).strip()
        if v:
            filled += 1
        else:
            pending += 1

    if filled == len(HORIZONS):
        row["forward_status"] = "FORWARD_COMPLETE"
    elif filled > 0:
        row["forward_status"] = "FORWARD_PARTIAL"
    else:
        row["forward_status"] = "PENDING_FORWARD_RETURNS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--use-yfinance", action="store_true")
    ap.add_argument("--allow-local-approx", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--max-report-rows", type=int, default=40)
    args = ap.parse_args()

    root = Path(args.root)

    state_tracker = root / "state" / "v18" / "simulation" / "V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"
    output_tracker = root / "outputs" / "v18" / "simulation" / "V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"
    audit_path = root / "outputs" / "v18" / "simulation" / "V18_9B_CURRENT_FORWARD_RETURN_FILLER_AUDIT.csv"
    report_path = root / "outputs" / "v18" / "simulation" / "V18_9B_CURRENT_FORWARD_RETURN_FILLER.md"
    read_first = root / "outputs" / "v18" / "simulation" / "V18_9B_READ_FIRST.txt"

    tech_dash = root / "outputs" / "v18" / "technical_timing_read_center" / "V18_6D_CURRENT_TECHNICAL_TIMING_DASHBOARD.csv"

    rows = read_csv_rows(state_tracker)
    tech_rows = read_csv_rows(tech_dash)
    local_price_map = build_local_price_map(tech_rows)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    status = "OK_FORWARD_RETURN_FILLER_READY"
    yf_status = "YFINANCE_NOT_USED"
    history_by_ticker = {}

    tickers = set()
    min_base_date = None
    max_today = datetime.now().date()

    for r in rows:
        t = str(r.get("ticker", "")).strip().upper()
        if t:
            tickers.add(t)

        bd = extract_price_date_from_source_text(r.get("source_row_text", ""))
        if bd is None:
            bd = parse_date(r.get("snapshot_date"))

        if bd is not None:
            min_base_date = bd if min_base_date is None else min(min_base_date, bd)

    if args.use_yfinance and rows and min_base_date:
        history_by_ticker, yf_status = load_yfinance_history(tickers, min_base_date, max_today)

    if not rows:
        status = "WARN_NO_TRACKER_ROWS"
    elif args.use_yfinance and yf_status.startswith("YFINANCE_IMPORT_FAIL"):
        status = "WARN_YFINANCE_IMPORT_FAIL_LOCAL_PENDING_ONLY"

    audit_rows = []
    filled_cells = 0
    pending_cells = 0
    skipped_existing = 0

    for r in rows:
        ticker = str(r.get("ticker", "")).strip().upper()

        for h in HORIZONS:
            ret_col = f"fwd_{h}d_return"
            date_col = f"fwd_{h}d_price_date"
            price_col = f"fwd_{h}d_price_usd"
            method_col = f"fwd_{h}d_fill_method"

            existing = str(r.get(ret_col, "")).strip()
            if existing and not args.overwrite:
                skipped_existing += 1
                continue

            ret = None
            d = ""
            p = ""
            method = "PENDING"

            if args.use_yfinance:
                ret, d, p, method = compute_yf_forward(r, history_by_ticker, h)

            if ret is None and args.allow_local_approx:
                ret, d, p, method = compute_local_approx(r, local_price_map, h)

            if ret is not None:
                r[ret_col] = f"{ret:.6f}"
                r[date_col] = d
                r[price_col] = p
                r[method_col] = method
                r["last_forward_fill_at"] = now
                filled_cells += 1
            else:
                if not str(r.get(method_col, "")).strip():
                    r[method_col] = method
                pending_cells += 1

        update_forward_status(r)

        filled_for_row = []
        pending_for_row = []
        for h in HORIZONS:
            if str(r.get(f"fwd_{h}d_return", "")).strip():
                filled_for_row.append(f"{h}D")
            else:
                pending_for_row.append(f"{h}D")

        audit_rows.append({
            "ticker": ticker,
            "snapshot_date": r.get("snapshot_date", ""),
            "base_price": r.get("latest_price_usd", ""),
            "technical_tags": r.get("technical_tags", ""),
            "candidate_bucket": r.get("candidate_bucket", ""),
            "filled_horizons": ";".join(filled_for_row),
            "pending_horizons": ";".join(pending_for_row),
            "forward_status": r.get("forward_status", ""),
        })

    fieldnames = ensure_fieldnames(rows)
    write_csv_rows(state_tracker, rows, fieldnames)
    write_csv_rows(output_tracker, rows, fieldnames)

    audit_fields = [
        "ticker",
        "snapshot_date",
        "base_price",
        "technical_tags",
        "candidate_bucket",
        "filled_horizons",
        "pending_horizons",
        "forward_status",
    ]
    write_csv_rows(audit_path, audit_rows, audit_fields)

    complete_rows = sum(1 for r in rows if r.get("forward_status") == "FORWARD_COMPLETE")
    partial_rows = sum(1 for r in rows if r.get("forward_status") == "FORWARD_PARTIAL")
    pending_rows = sum(1 for r in rows if r.get("forward_status") == "PENDING_FORWARD_RETURNS")

    report = []
    report.append("# V18.9B Forward Return Filler")
    report.append("")
    report.append(f"- STATUS: `{status}`")
    report.append(f"- GENERATED_AT: `{now}`")
    report.append("- MODE: `SHADOW_ONLY`")
    report.append(f"- USE_YFINANCE: `{args.use_yfinance}`")
    report.append(f"- ALLOW_LOCAL_APPROX: `{args.allow_local_approx}`")
    report.append(f"- OVERWRITE: `{args.overwrite}`")
    report.append(f"- YFINANCE_STATUS: `{yf_status}`")
    report.append("")
    report.append("## Summary")
    report.append("")
    report.append(f"- TRACKER_ROWS: `{len(rows)}`")
    report.append(f"- FILLED_CELLS_THIS_RUN: `{filled_cells}`")
    report.append(f"- PENDING_CELLS_THIS_RUN: `{pending_cells}`")
    report.append(f"- SKIPPED_EXISTING_CELLS: `{skipped_existing}`")
    report.append(f"- FORWARD_COMPLETE_ROWS: `{complete_rows}`")
    report.append(f"- FORWARD_PARTIAL_ROWS: `{partial_rows}`")
    report.append(f"- PENDING_FORWARD_ROWS: `{pending_rows}`")
    report.append("")
    report.append("## Audit Preview")
    report.append("")
    report.append("| ticker | snapshot_date | tags | bucket | filled | pending | status |")
    report.append("|---|---|---|---|---|---|---|")
    for r in audit_rows[: args.max_report_rows]:
        report.append(
            f"| {r.get('ticker','')} | {r.get('snapshot_date','')} | {r.get('technical_tags','')} | "
            f"{r.get('candidate_bucket','')} | {r.get('filled_horizons','')} | "
            f"{r.get('pending_horizons','')} | {r.get('forward_status','')} |"
        )
    if not audit_rows:
        report.append("| NONE |  |  |  |  |  |  |")

    report.append("")
    report.append("## Files")
    report.append("")
    report.append(f"- STATE_TRACKER: `{state_tracker}`")
    report.append(f"- OUTPUT_TRACKER: `{output_tracker}`")
    report.append(f"- AUDIT: `{audit_path}`")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first}`")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("- This module fills future-return fields for V18.9A candidate tracker rows.")
    report.append("- It is shadow-only and does not modify official buy permission.")
    report.append("- Same-day or not-yet-mature horizons remain pending.")
    report.append("- YFinance mode is more exact for trading-day horizons; local approximation is optional and disabled unless explicitly requested.")

    write_text(report_path, "\n".join(report))

    rf = []
    rf.append("V18.9B FORWARD RETURN FILLER")
    rf.append("")
    rf.append(f"STATUS: {status}")
    rf.append("MODE: SHADOW_ONLY")
    rf.append(f"USE_YFINANCE: {args.use_yfinance}")
    rf.append(f"ALLOW_LOCAL_APPROX: {args.allow_local_approx}")
    rf.append(f"YFINANCE_STATUS: {yf_status}")
    rf.append("")
    rf.append(f"TRACKER_ROWS: {len(rows)}")
    rf.append(f"FILLED_CELLS_THIS_RUN: {filled_cells}")
    rf.append(f"PENDING_CELLS_THIS_RUN: {pending_cells}")
    rf.append(f"SKIPPED_EXISTING_CELLS: {skipped_existing}")
    rf.append(f"FORWARD_COMPLETE_ROWS: {complete_rows}")
    rf.append(f"FORWARD_PARTIAL_ROWS: {partial_rows}")
    rf.append(f"PENDING_FORWARD_ROWS: {pending_rows}")
    rf.append("")
    rf.append("REPORT:")
    rf.append(str(report_path))
    rf.append("")
    rf.append("AUDIT:")
    rf.append(str(audit_path))
    rf.append("")
    rf.append("STATE_TRACKER:")
    rf.append(str(state_tracker))
    rf.append("")
    rf.append("OUTPUT_TRACKER:")
    rf.append(str(output_tracker))

    write_text(read_first, "\n".join(rf))

    print("")
    print("=== V18.9B FORWARD RETURN FILLER READY ===")
    print(f"STATUS: {status}")
    print(f"USE_YFINANCE: {args.use_yfinance}")
    print(f"ALLOW_LOCAL_APPROX: {args.allow_local_approx}")
    print(f"YFINANCE_STATUS: {yf_status}")
    print(f"TRACKER_ROWS: {len(rows)}")
    print(f"FILLED_CELLS_THIS_RUN: {filled_cells}")
    print(f"PENDING_CELLS_THIS_RUN: {pending_cells}")
    print(f"FORWARD_COMPLETE_ROWS: {complete_rows}")
    print(f"FORWARD_PARTIAL_ROWS: {partial_rows}")
    print(f"PENDING_FORWARD_ROWS: {pending_rows}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first}")
    print("")


if __name__ == "__main__":
    main()
