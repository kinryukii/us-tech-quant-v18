import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
OUT_DIR = ROOT / "outputs" / "v17" / "raw_universe_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_FULL_UNIVERSE_RAW.csv"

OUT_CSV = OUT_DIR / "v17_7F_raw105_latest_price_refresh.csv"
SUMMARY_MD = OUT_DIR / "V17_7F_RAW105_LATEST_PRICE_REFRESH.md"
READ_FIRST = OUT_DIR / "V17_7F_READ_FIRST.txt"

def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path)

def find_ticker_col(df: pd.DataFrame):
    if df.empty:
        return None
    candidates = ["ticker", "Ticker", "symbol", "Symbol", "code", "Code"]
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        lc = str(c).lower()
        if "ticker" in lc or "symbol" in lc:
            return c
    return df.columns[0]

def get_raw_tickers():
    raw = read_csv_safe(RAW_PATH)
    if raw.empty:
        raise RuntimeError(f"RAW universe missing or empty: {RAW_PATH}")
    col = find_ticker_col(raw)
    if col is None:
        raise RuntimeError(f"No ticker column found in: {RAW_PATH}")
    tickers = (
        raw[col]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"": pd.NA, "NAN": pd.NA})
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    return tickers

def normalize_download(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [c[0] if isinstance(c, tuple) else c for c in out.columns]
    out = out.reset_index()
    return out

def fetch_one(ticker: str):
    try:
        import yfinance as yf
    except Exception as e:
        return {
            "ticker": ticker,
            "refresh_status": "FAIL_NO_YFINANCE",
            "latest_price_date": "",
            "latest_close": "",
            "latest_volume": "",
            "source": "yfinance",
            "error": str(e),
        }

    try:
        df = yf.download(
            ticker,
            period="15d",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        df = normalize_download(df)

        if df.empty:
            return {
                "ticker": ticker,
                "refresh_status": "FAIL_EMPTY_DOWNLOAD",
                "latest_price_date": "",
                "latest_close": "",
                "latest_volume": "",
                "source": "yfinance",
                "error": "",
            }

        date_col = None
        for c in ["Date", "Datetime", "date", "datetime"]:
            if c in df.columns:
                date_col = c
                break

        close_col = None
        for c in ["Close", "Adj Close", "close", "adj_close"]:
            if c in df.columns:
                close_col = c
                break

        volume_col = None
        for c in ["Volume", "volume"]:
            if c in df.columns:
                volume_col = c
                break

        if date_col is None or close_col is None:
            return {
                "ticker": ticker,
                "refresh_status": "FAIL_MISSING_DATE_OR_CLOSE",
                "latest_price_date": "",
                "latest_close": "",
                "latest_volume": "",
                "source": "yfinance",
                "error": f"columns={list(df.columns)}",
            }

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df[close_col] = pd.to_numeric(df[close_col], errors="coerce")
        df = df[df[date_col].notna()]
        df = df[df[close_col].notna()]
        df = df.sort_values(date_col)

        if df.empty:
            return {
                "ticker": ticker,
                "refresh_status": "FAIL_NO_VALID_CLOSE",
                "latest_price_date": "",
                "latest_close": "",
                "latest_volume": "",
                "source": "yfinance",
                "error": "",
            }

        last = df.iloc[-1]
        vol = ""
        if volume_col is not None:
            try:
                vol = float(last[volume_col])
            except Exception:
                vol = ""

        return {
            "ticker": ticker,
            "refresh_status": "OK_YFINANCE_LATEST_AVAILABLE",
            "latest_price_date": str(pd.to_datetime(last[date_col]).date()),
            "latest_close": float(last[close_col]),
            "latest_volume": vol,
            "source": "yfinance",
            "error": "",
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "refresh_status": "FAIL_YFINANCE_ERROR",
            "latest_price_date": "",
            "latest_close": "",
            "latest_volume": "",
            "source": "yfinance",
            "error": str(e),
        }

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tickers = get_raw_tickers()

    rows = []
    total = len(tickers)

    print("")
    print("=== V17.7F RAW105 LATEST PRICE REFRESH RUNNING ===")
    print(f"RAW_TICKER_COUNT: {total}")

    for i, t in enumerate(tickers, start=1):
        result = fetch_one(t)
        result["run_time"] = now
        result["raw_index"] = i
        rows.append(result)

        if i % 10 == 0 or i == total:
            print(f"progress: {i}/{total}")

    df = pd.DataFrame(rows)
    ok_mask = df["refresh_status"].astype(str).str.startswith("OK")
    ok_count = int(ok_mask.sum())
    fail_count = int((~ok_mask).sum())

    if ok_count > 0:
        min_date = str(df.loc[ok_mask, "latest_price_date"].min())
        max_date = str(df.loc[ok_mask, "latest_price_date"].max())
        date_counts = (
            df.loc[ok_mask]
            .groupby("latest_price_date")
            .size()
            .reset_index(name="count")
            .sort_values("latest_price_date")
        )
    else:
        min_date = ""
        max_date = ""
        date_counts = pd.DataFrame(columns=["latest_price_date", "count"])

    latest_date_count = 0
    stale_count = 0
    if max_date:
        latest_date_count = int((df["latest_price_date"].astype(str) == max_date).sum())
        stale_count = ok_count - latest_date_count

    df["freshness_status"] = df.apply(
        lambda r: (
            "OK_LATEST_AVAILABLE"
            if str(r.get("refresh_status", "")).startswith("OK") and str(r.get("latest_price_date", "")) == max_date
            else (
                "OK_BUT_NOT_MAX_DATE"
                if str(r.get("refresh_status", "")).startswith("OK")
                else "PRICE_REFRESH_FAILED"
            )
        ),
        axis=1,
    )

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    status = "OK"
    if fail_count > 0:
        status = "WARN_PRICE_REFRESH_PARTIAL"
    if ok_count == 0:
        status = "FAIL_NO_PRICE_REFRESH_OK"

    md = []
    md.append("# V17.7F RAW105 Latest Price Refresh")
    md.append("")
    md.append(f"Generated: {now}")
    md.append("")
    md.append("## 1. Main Conclusion")
    md.append("")
    md.append(f"RAW105_PRICE_REFRESH_STATUS: {status}")
    md.append("")
    md.append("本报告对 RAW 原始池 105 个标的逐个尝试 yfinance 最新可用价格刷新。")
    md.append("")
    md.append("## 2. Count Summary")
    md.append("")
    md.append("| item | value |")
    md.append("|---|---:|")
    md.append(f"| RAW_TICKER_COUNT | {total} |")
    md.append(f"| PRICE_REFRESH_OK_COUNT | {ok_count} |")
    md.append(f"| PRICE_REFRESH_FAIL_COUNT | {fail_count} |")
    md.append(f"| MIN_LATEST_PRICE_DATE | {min_date} |")
    md.append(f"| MAX_LATEST_PRICE_DATE | {max_date} |")
    md.append(f"| LATEST_DATE_COUNT | {latest_date_count} |")
    md.append(f"| OK_BUT_NOT_MAX_DATE_COUNT | {stale_count} |")
    md.append("")
    md.append("## 3. latest_price_date Distribution")
    md.append("")
    md.append("| latest_price_date | count |")
    md.append("|---|---:|")
    for _, r in date_counts.iterrows():
        md.append(f"| {r['latest_price_date']} | {int(r['count'])} |")
    md.append("")
    md.append("## 4. Non Latest / Failed Rows")
    md.append("")
    md.append("| ticker | refresh_status | latest_price_date | latest_close | freshness_status |")
    md.append("|---|---|---:|---:|---|")
    non_latest = df[df["freshness_status"] != "OK_LATEST_AVAILABLE"].sort_values(["freshness_status", "ticker"])
    for _, r in non_latest.iterrows():
        md.append(f"| {r['ticker']} | {r['refresh_status']} | {r['latest_price_date']} | {r['latest_close']} | {r['freshness_status']} |")
    md.append("")
    md.append("## 5. Output Files")
    md.append("")
    md.append(f"- Full CSV: {OUT_CSV}")
    md.append(f"- Summary: {SUMMARY_MD}")
    md.append(f"- Read first: {READ_FIRST}")
    md.append("")

    SUMMARY_MD.write_text("\n".join(md), encoding="utf-8")

    rf = []
    rf.append("=== V17.7F RAW105 LATEST PRICE REFRESH READY ===")
    rf.append(f"RAW105_PRICE_REFRESH_STATUS: {status}")
    rf.append(f"RAW_TICKER_COUNT: {total}")
    rf.append(f"PRICE_REFRESH_OK_COUNT: {ok_count}")
    rf.append(f"PRICE_REFRESH_FAIL_COUNT: {fail_count}")
    rf.append(f"MIN_LATEST_PRICE_DATE: {min_date}")
    rf.append(f"MAX_LATEST_PRICE_DATE: {max_date}")
    rf.append(f"LATEST_DATE_COUNT: {latest_date_count}")
    rf.append(f"OK_BUT_NOT_MAX_DATE_COUNT: {stale_count}")
    rf.append("")
    rf.append("START HERE:")
    rf.append(str(SUMMARY_MD))
    rf.append("")
    rf.append("FULL CSV:")
    rf.append(str(OUT_CSV))
    READ_FIRST.write_text("\n".join(rf), encoding="utf-8")

    print("")
    print("=== V17.7F RAW105 LATEST PRICE REFRESH READY ===")
    print(f"RAW105_PRICE_REFRESH_STATUS: {status}")
    print(f"RAW_TICKER_COUNT: {total}")
    print(f"PRICE_REFRESH_OK_COUNT: {ok_count}")
    print(f"PRICE_REFRESH_FAIL_COUNT: {fail_count}")
    print(f"MIN_LATEST_PRICE_DATE: {min_date}")
    print(f"MAX_LATEST_PRICE_DATE: {max_date}")
    print(f"LATEST_DATE_COUNT: {latest_date_count}")
    print(f"OK_BUT_NOT_MAX_DATE_COUNT: {stale_count}")
    print("")
    print("START HERE:")
    print(str(SUMMARY_MD))
    print("")
    print("FULL CSV:")
    print(str(OUT_CSV))
    print("")
    print("READ FIRST:")
    print(str(READ_FIRST))

    if ok_count == 0:
        sys.exit(2)
    if fail_count > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
