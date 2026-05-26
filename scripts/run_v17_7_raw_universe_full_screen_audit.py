import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
OUT_DIR = ROOT / "outputs" / "v17" / "raw_universe_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_FULL_UNIVERSE_RAW.csv"
SCREENED_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_FULL_UNIVERSE_SCREENED.csv"
SELECTED_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_FULL_UNIVERSE_SELECTED_FOR_EXECUTION.csv"
SECOND_STAGE_PATH = ROOT / "outputs" / "v17" / "price" / "v17_6E_second_stage_tickers.csv"
LATEST_PRICE_PATH = ROOT / "outputs" / "v17" / "price" / "v17_6E_screened_universe_latest_prices.csv"
MANUAL_DECISION_PATH = ROOT / "state" / "v16_manual_review_decisions.csv"

AUDIT_CSV = OUT_DIR / "v17_7_raw_universe_full_screen_audit.csv"
SUMMARY_MD = OUT_DIR / "V17_7_RAW_UNIVERSE_FULL_SCREEN_AUDIT.md"
READ_FIRST = OUT_DIR / "V17_7_READ_FIRST.txt"

BENCHMARK_TICKERS = {"QQQ", "SPY", "XLK", "SMH", "SOXX"}
LEVERAGED_TICKERS = {"TQQQ", "SOXL", "SQQQ", "TECL", "TECS", "SPXL", "SPXS"}

def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()

def find_ticker_col(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    candidates = [
        "ticker", "Ticker", "symbol", "Symbol", "code", "Code",
        "asset", "Asset", "name", "Name"
    ]
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        lc = str(c).lower()
        if "ticker" in lc or "symbol" in lc:
            return c
    return df.columns[0] if len(df.columns) else None

def ticker_set(df: pd.DataFrame):
    col = find_ticker_col(df)
    if col is None:
        return set()
    return set(
        df[col]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"": pd.NA, "NAN": pd.NA})
        .dropna()
        .tolist()
    )

def normalize_ticker_series(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    col = find_ticker_col(df)
    if col is None:
        return df
    out = df.copy()
    if col != "ticker":
        out = out.rename(columns={col: "ticker"})
    out["ticker"] = out["ticker"].astype(str).str.strip().str.upper()
    out = out[out["ticker"].notna()]
    out = out[out["ticker"] != ""]
    out = out[out["ticker"] != "NAN"]
    return out

def pick_col(df: pd.DataFrame, names):
    for n in names:
        if n in df.columns:
            return n
    lower_map = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower_map:
            return lower_map[n.lower()]
    return None

def get_latest_price_from_existing_csv(ticker: str):
    candidates = [
        ROOT / "data" / "v16" / "prices_full" / f"{ticker}.csv",
        ROOT / "data" / "v16" / "prices" / f"{ticker}.csv",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p)
            if df.empty:
                continue
            date_col = pick_col(df, ["Date", "date", "Datetime", "timestamp"])
            close_col = pick_col(df, ["Close", "close", "Adj Close", "adj_close"])
            volume_col = pick_col(df, ["Volume", "volume"])
            if close_col is None:
                continue
            df = df.copy()
            if date_col is not None:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                df = df[df[date_col].notna()].sort_values(date_col)
            else:
                df = df.reset_index()
            df[close_col] = pd.to_numeric(df[close_col], errors="coerce")
            df = df[df[close_col].notna()]
            if df.empty:
                continue
            last = df.iloc[-1]
            latest_date = ""
            if date_col is not None:
                latest_date = str(pd.to_datetime(last[date_col]).date())
            close = float(last[close_col])
            volume = None
            if volume_col is not None:
                try:
                    volume = float(last[volume_col])
                except Exception:
                    volume = None
            return {
                "price_status": "OK_EXISTING_LOCAL_PRICE",
                "price_source": str(p),
                "latest_price_date": latest_date,
                "latest_close": close,
                "latest_volume": volume,
            }
        except Exception:
            continue
    return None

def fetch_latest_price_yfinance(ticker: str):
    try:
        import yfinance as yf
    except Exception as e:
        return {
            "price_status": "NO_YFINANCE_PACKAGE",
            "price_source": "",
            "latest_price_date": "",
            "latest_close": None,
            "latest_volume": None,
        }

    try:
        hist = yf.download(
            ticker,
            period="1y",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        if hist is None or hist.empty:
            return {
                "price_status": "YFINANCE_EMPTY",
                "price_source": "yfinance",
                "latest_price_date": "",
                "latest_close": None,
                "latest_volume": None,
            }

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] if isinstance(c, tuple) else c for c in hist.columns]

        close_col = "Close" if "Close" in hist.columns else None
        if close_col is None and "Adj Close" in hist.columns:
            close_col = "Adj Close"
        if close_col is None:
            return {
                "price_status": "YFINANCE_NO_CLOSE_COLUMN",
                "price_source": "yfinance",
                "latest_price_date": "",
                "latest_close": None,
                "latest_volume": None,
            }

        hist = hist.reset_index()
        date_col = pick_col(hist, ["Date", "Datetime"])
        hist[close_col] = pd.to_numeric(hist[close_col], errors="coerce")
        hist = hist[hist[close_col].notna()]
        if hist.empty:
            return {
                "price_status": "YFINANCE_NO_VALID_CLOSE",
                "price_source": "yfinance",
                "latest_price_date": "",
                "latest_close": None,
                "latest_volume": None,
            }

        last = hist.iloc[-1]
        latest_date = ""
        if date_col is not None:
            latest_date = str(pd.to_datetime(last[date_col]).date())

        volume = None
        if "Volume" in hist.columns:
            try:
                volume = float(last["Volume"])
            except Exception:
                volume = None

        return {
            "price_status": "OK_YFINANCE",
            "price_source": "yfinance",
            "latest_price_date": latest_date,
            "latest_close": float(last[close_col]),
            "latest_volume": volume,
        }
    except Exception as e:
        return {
            "price_status": "YFINANCE_ERROR",
            "price_source": "yfinance",
            "latest_price_date": "",
            "latest_close": None,
            "latest_volume": None,
        }

def get_latest_price(ticker: str):
    local = get_latest_price_from_existing_csv(ticker)
    if local is not None:
        return local
    return fetch_latest_price_yfinance(ticker)

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    raw = normalize_ticker_series(read_csv_safe(RAW_PATH))
    screened = normalize_ticker_series(read_csv_safe(SCREENED_PATH))
    selected = normalize_ticker_series(read_csv_safe(SELECTED_PATH))
    second_stage = normalize_ticker_series(read_csv_safe(SECOND_STAGE_PATH))
    latest_price_snapshot = normalize_ticker_series(read_csv_safe(LATEST_PRICE_PATH))
    manual = normalize_ticker_series(read_csv_safe(MANUAL_DECISION_PATH))

    if raw is None or raw.empty:
        print("ERROR: RAW universe file missing or empty:")
        print(str(RAW_PATH))
        sys.exit(2)

    raw_tickers = sorted(ticker_set(raw))
    screened_set = ticker_set(screened)
    selected_set = ticker_set(selected)
    second_stage_set = ticker_set(second_stage)
    latest_price_set = ticker_set(latest_price_snapshot)
    manual_set = ticker_set(manual)

    manual_decision_map = {}
    if manual is not None and not manual.empty and "ticker" in manual.columns:
        decision_col = pick_col(manual, [
            "user_review_decision",
            "candidate_review_decision",
            "review_decision",
            "decision",
            "manual_decision",
        ])
        if decision_col:
            for _, r in manual.iterrows():
                t = str(r.get("ticker", "")).strip().upper()
                if t:
                    manual_decision_map[t] = str(r.get(decision_col, "")).strip()

    raw_columns_to_keep = []
    for c in raw.columns:
        lc = str(c).lower()
        if c == "ticker":
            continue
        if any(k in lc for k in ["bucket", "reason", "status", "category", "sector", "theme", "type"]):
            raw_columns_to_keep.append(c)

    rows = []
    for t in raw_tickers:
        price = get_latest_price(t)

        in_screened = t in screened_set
        in_selected = t in selected_set
        in_second = t in second_stage_set
        in_latest_price_snapshot = t in latest_price_set
        in_manual = t in manual_set

        if in_second:
            full_status = "SECOND_STAGE_CANDIDATE"
        elif in_selected:
            full_status = "SELECTED_FOR_EXECUTION_REVIEW"
        elif in_screened:
            full_status = "SCREENED_PASS_NOT_SECOND_STAGE"
        else:
            full_status = "RAW_ONLY_EXCLUDED_BEFORE_SCREENED"

        if t in BENCHMARK_TICKERS:
            special_tag = "BENCHMARK_OR_CORE_ETF"
        elif t in LEVERAGED_TICKERS:
            special_tag = "LEVERAGED_ETF_WATCH_ONLY"
        else:
            special_tag = ""

        inferred_exclusion_reason = ""
        if not in_screened:
            if t in BENCHMARK_TICKERS:
                inferred_exclusion_reason = "INFERRED_BENCHMARK_ONLY_OR_CORE_REFERENCE"
            elif t in LEVERAGED_TICKERS:
                inferred_exclusion_reason = "INFERRED_LEVERAGED_WATCH_ONLY"
            else:
                inferred_exclusion_reason = "NOT_IN_SCREENED_UNIVERSE_CHECK_RULE_COLUMNS"

        raw_match = raw[raw["ticker"] == t].head(1)
        raw_extra = {}
        if not raw_match.empty:
            for c in raw_columns_to_keep:
                raw_extra[f"raw_{c}"] = raw_match.iloc[0].get(c, "")

        row = {
            "run_time": now,
            "ticker": t,
            "in_raw_universe": True,
            "in_screened_universe": in_screened,
            "in_selected_for_execution": in_selected,
            "in_second_stage": in_second,
            "in_latest_price_snapshot": in_latest_price_snapshot,
            "in_manual_review_file": in_manual,
            "manual_review_decision": manual_decision_map.get(t, ""),
            "full_pipeline_status": full_status,
            "special_tag": special_tag,
            "inferred_exclusion_reason": inferred_exclusion_reason,
            "price_status": price.get("price_status", ""),
            "price_source": price.get("price_source", ""),
            "latest_price_date": price.get("latest_price_date", ""),
            "latest_close": price.get("latest_close", None),
            "latest_volume": price.get("latest_volume", None),
        }
        row.update(raw_extra)
        rows.append(row)

    audit = pd.DataFrame(rows)

    raw_count = len(audit)
    screened_count = int(audit["in_screened_universe"].sum())
    selected_count = int(audit["in_selected_for_execution"].sum())
    second_count = int(audit["in_second_stage"].sum())
    latest_price_ok_count = int(audit["price_status"].astype(str).str.startswith("OK").sum())
    price_fail_count = raw_count - latest_price_ok_count
    excluded_before_screened_count = raw_count - screened_count

    status_counts = audit["full_pipeline_status"].value_counts(dropna=False).reset_index()
    status_counts.columns = ["full_pipeline_status", "count"]

    price_status_counts = audit["price_status"].value_counts(dropna=False).reset_index()
    price_status_counts.columns = ["price_status", "count"]

    audit.to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")

    md = []
    md.append("# V17.7 RAW Universe Full Screen Audit")
    md.append("")
    md.append(f"Generated: `{now}`")
    md.append("")
    md.append("## 1. Main Conclusion")
    md.append("")
    if raw_count > 0 and latest_price_ok_count == raw_count:
        audit_status = "OK"
    elif raw_count > 0 and latest_price_ok_count > 0:
        audit_status = "WARN_PRICE_PARTIAL"
    else:
        audit_status = "FAIL_NO_RAW_PRICE_OK"
    md.append(f"**RAW_FULL_AUDIT_STATUS: `{audit_status}`**")
    md.append("")
    md.append("This audit checks every ticker in the raw universe before the system narrows the list to screened universe and second-stage candidates.")
    md.append("")
    md.append("## 2. Count Summary")
    md.append("")
    md.append("| item | count |")
    md.append("|---|---:|")
    md.append(f"| RAW_UNIVERSE_COUNT | {raw_count} |")
    md.append(f"| SCREENED_UNIVERSE_COUNT | {screened_count} |")
    md.append(f"| EXCLUDED_BEFORE_SCREENED_COUNT | {excluded_before_screened_count} |")
    md.append(f"| SELECTED_FOR_EXECUTION_COUNT | {selected_count} |")
    md.append(f"| SECOND_STAGE_COUNT | {second_count} |")
    md.append(f"| RAW_PRICE_OK_COUNT | {latest_price_ok_count} |")
    md.append(f"| RAW_PRICE_FAIL_COUNT | {price_fail_count} |")
    md.append("")
    md.append("## 3. Pipeline Status Counts")
    md.append("")
    md.append("| status | count |")
    md.append("|---|---:|")
    for _, r in status_counts.iterrows():
        md.append(f"| {r['full_pipeline_status']} | {int(r['count'])} |")
    md.append("")
    md.append("## 4. Price Status Counts")
    md.append("")
    md.append("| price_status | count |")
    md.append("|---|---:|")
    for _, r in price_status_counts.iterrows():
        md.append(f"| {r['price_status']} | {int(r['count'])} |")
    md.append("")
    md.append("## 5. Important Output Files")
    md.append("")
    md.append(f"- Full audit CSV: `{AUDIT_CSV}`")
    md.append(f"- Summary: `{SUMMARY_MD}`")
    md.append(f"- Read first: `{READ_FIRST}`")
    md.append("")
    md.append("## 6. Interpretation")
    md.append("")
    md.append("- `RAW_UNIVERSE_COUNT` is the original pool size.")
    md.append("- `SCREENED_UNIVERSE_COUNT` is the number that survives the basic screen.")
    md.append("- `SECOND_STAGE_COUNT` is the number promoted to the focused candidate layer.")
    md.append("- `RAW_ONLY_EXCLUDED_BEFORE_SCREENED` means the ticker existed in the raw list but did not survive to the screened universe.")
    md.append("- `price_status` confirms whether the ticker had usable local or yfinance price data.")
    md.append("")
    SUMMARY_MD.write_text("\n".join(md), encoding="utf-8")

    rf = []
    rf.append("=== V17.7 RAW UNIVERSE FULL SCREEN AUDIT READY ===")
    rf.append(f"RAW_FULL_AUDIT_STATUS: {audit_status}")
    rf.append(f"RAW_UNIVERSE_COUNT: {raw_count}")
    rf.append(f"SCREENED_UNIVERSE_COUNT: {screened_count}")
    rf.append(f"EXCLUDED_BEFORE_SCREENED_COUNT: {excluded_before_screened_count}")
    rf.append(f"SELECTED_FOR_EXECUTION_COUNT: {selected_count}")
    rf.append(f"SECOND_STAGE_COUNT: {second_count}")
    rf.append(f"RAW_PRICE_OK_COUNT: {latest_price_ok_count}")
    rf.append(f"RAW_PRICE_FAIL_COUNT: {price_fail_count}")
    rf.append("")
    rf.append("START HERE:")
    rf.append(str(SUMMARY_MD))
    rf.append("")
    rf.append("FULL CSV:")
    rf.append(str(AUDIT_CSV))
    READ_FIRST.write_text("\n".join(rf), encoding="utf-8")

    print("")
    print("=== V17.7 RAW UNIVERSE FULL SCREEN AUDIT READY ===")
    print(f"RAW_FULL_AUDIT_STATUS: {audit_status}")
    print(f"RAW_UNIVERSE_COUNT: {raw_count}")
    print(f"SCREENED_UNIVERSE_COUNT: {screened_count}")
    print(f"EXCLUDED_BEFORE_SCREENED_COUNT: {excluded_before_screened_count}")
    print(f"SELECTED_FOR_EXECUTION_COUNT: {selected_count}")
    print(f"SECOND_STAGE_COUNT: {second_count}")
    print(f"RAW_PRICE_OK_COUNT: {latest_price_ok_count}")
    print(f"RAW_PRICE_FAIL_COUNT: {price_fail_count}")
    print("")
    print("START HERE:")
    print(str(SUMMARY_MD))
    print("")
    print("FULL CSV:")
    print(str(AUDIT_CSV))
    print("")
    print("READ FIRST:")
    print(str(READ_FIRST))

if __name__ == "__main__":
    main()
