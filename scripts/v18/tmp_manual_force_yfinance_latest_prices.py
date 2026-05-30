from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

try:
    import yfinance as yf
except Exception as e:
    print(f"IMPORT_YFINANCE_FAILED: {e}")
    sys.exit(1)

ROOT = Path(r"D:\us-tech-quant")
SRC = ROOT / "outputs" / "v18" / "candidates" / "V18_CURRENT_RANKED_CANDIDATES.csv"
OUT_DIR = ROOT / "outputs" / "v18" / "price"
OUT_DIR.mkdir(parents=True, exist_ok=True)

run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = OUT_DIR / f"V18_MANUAL_FORCE_YFINANCE_LATEST_PRICES_{run_id}.csv"
SUMMARY = OUT_DIR / f"V18_MANUAL_FORCE_YFINANCE_LATEST_PRICES_SUMMARY_{run_id}.csv"

if not SRC.exists():
    print(f"MISSING_SOURCE: {SRC}")
    sys.exit(1)

df = pd.read_csv(SRC)
if "ticker" not in df.columns:
    print(f"MISSING_TICKER_COLUMN_IN: {SRC}")
    sys.exit(1)

tickers = (
    df["ticker"]
    .dropna()
    .astype(str)
    .str.strip()
    .replace("", pd.NA)
    .dropna()
    .drop_duplicates()
    .tolist()
)

rows = []
print(f"TICKER_COUNT: {len(tickers)}")

for i, ticker in enumerate(tickers, 1):
    try:
        hist = yf.download(
            ticker,
            period="30d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if hist is None or hist.empty:
            rows.append({
                "ticker": ticker,
                "manual_fetch_status": "NO_DATA",
                "manual_latest_price_date": "",
                "manual_latest_close": "",
                "row_count": 0,
                "error": "",
            })
            print(f"[{i}/{len(tickers)}] {ticker}: NO_DATA")
            continue

        hist = hist.dropna(how="all")
        if hist.empty:
            rows.append({
                "ticker": ticker,
                "manual_fetch_status": "EMPTY_AFTER_DROPNA",
                "manual_latest_price_date": "",
                "manual_latest_close": "",
                "row_count": 0,
                "error": "",
            })
            print(f"[{i}/{len(tickers)}] {ticker}: EMPTY_AFTER_DROPNA")
            continue

        last_idx = hist.index[-1]
        latest_date = pd.Timestamp(last_idx).date().isoformat()

        close_col = "Close"
        if isinstance(hist.columns, pd.MultiIndex):
            # yfinance can return multi-index columns in some versions
            close_candidates = [c for c in hist.columns if str(c[0]).lower() == "close"]
            if close_candidates:
                latest_close = hist[close_candidates[0]].iloc[-1]
            else:
                latest_close = ""
        else:
            latest_close = hist[close_col].iloc[-1] if close_col in hist.columns else ""

        rows.append({
            "ticker": ticker,
            "manual_fetch_status": "OK",
            "manual_latest_price_date": latest_date,
            "manual_latest_close": latest_close,
            "row_count": len(hist),
            "error": "",
        })
        print(f"[{i}/{len(tickers)}] {ticker}: OK {latest_date} {latest_close}")

    except Exception as e:
        rows.append({
            "ticker": ticker,
            "manual_fetch_status": "ERROR",
            "manual_latest_price_date": "",
            "manual_latest_close": "",
            "row_count": 0,
            "error": str(e),
        })
        print(f"[{i}/{len(tickers)}] {ticker}: ERROR {e}")

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False, encoding="utf-8-sig")

summary = (
    out.groupby(["manual_fetch_status", "manual_latest_price_date"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values(["manual_fetch_status", "manual_latest_price_date"])
)
summary.to_csv(SUMMARY, index=False, encoding="utf-8-sig")

print("")
print(f"OUTPUT: {OUT}")
print(f"SUMMARY: {SUMMARY}")
print("")
print("DATE_DISTRIBUTION:")
print(out.groupby("manual_latest_price_date", dropna=False).size().sort_index())
print("")
print("STATUS_DISTRIBUTION:")
print(out.groupby("manual_fetch_status", dropna=False).size().sort_index())
