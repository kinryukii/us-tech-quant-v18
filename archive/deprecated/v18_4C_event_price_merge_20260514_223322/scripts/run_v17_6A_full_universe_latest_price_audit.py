from pathlib import Path
from datetime import datetime
import re
import sys
import traceback

import pandas as pd

try:
    import yfinance as yf
except Exception as e:
    print("IMPORT_ERROR: yfinance is not available:", repr(e))
    sys.exit(1)


ROOT = Path(r"D:\us-tech-quant")
OUT_DIR = ROOT / "outputs" / "v17" / "price"
STATE_DIR = ROOT / "state"
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIME_JST = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

OUT_TICKERS = OUT_DIR / "v17_6A_full_universe_tickers.csv"
OUT_SOURCES = OUT_DIR / "v17_6A_universe_source_files.csv"
OUT_PRICES = OUT_DIR / "v17_6A_latest_prices.csv"
OUT_STATE_PRICES = STATE_DIR / "v17_6A_latest_price_snapshot.csv"
OUT_REPORT = OUT_DIR / "V17_6A_FULL_UNIVERSE_LATEST_PRICE_AUDIT.md"
OUT_READ_FIRST = OUT_DIR / "V17_6A_READ_FIRST.txt"

SEARCH_DIRS = [
    ROOT / "data",
    ROOT / "configs",
    ROOT / "state",
    ROOT / "outputs" / "v16",
    ROOT / "outputs" / "v17" / "factor_effectiveness",
]

TICKER_COLS = {
    "ticker",
    "symbol",
    "ticker_symbol",
    "stock",
    "stock_symbol",
    "code",
}

EXCLUDE_VALUES = {
    "", "NA", "N/A", "NULL", "NONE", "TRUE", "FALSE",
    "OK", "WARN", "FAIL", "ERROR",
    "WATCH", "BLOCK", "PENDING",
    "ACTIVE", "INACTIVE",
    "HIGH", "MEDIUM", "LOW",
    "MACRO", "EVENT",
}

TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


def read_csv_robust(path: Path):
    encodings = ["utf-8-sig", "utf-8", "cp932", "gb18030", "latin1"]
    last_error = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception as e:
            last_error = e
    raise last_error


def normalize_ticker(x):
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    s = s.replace(" ", "")
    if s in EXCLUDE_VALUES:
        return None
    if not TICKER_RE.match(s):
        return None
    return s


def file_relevance(path: Path):
    s = str(path).lower()
    name = path.name.lower()

    if any(part in s for part in [r"\.venv", r"\archive", r"\logs", r"\__pycache__"]):
        return False

    if path.suffix.lower() != ".csv":
        return False

    # Avoid giant accidental files.
    try:
        if path.stat().st_size > 20 * 1024 * 1024:
            return False
    except Exception:
        return False

    keywords = [
        "universe", "ticker", "symbol", "candidate", "screen", "watch",
        "manual", "tracking", "route", "budget", "execution", "factor",
        "score", "snapshot", "review", "decision"
    ]
    return any(k in name for k in keywords)


def source_priority(path: Path):
    s = str(path).lower()
    name = path.name.lower()

    if ("data" in s or "configs" in s) and any(k in name for k in ["universe", "ticker", "symbol", "stock"]):
        return "HIGH_UNIVERSE_SOURCE"
    if "outputs\\v16" in s and any(k in name for k in ["universe", "screen", "candidate"]):
        return "MID_SCREEN_SOURCE"
    if "state" in s and any(k in name for k in ["manual", "tracking", "decision"]):
        return "STATE_SOURCE"
    if "factor" in s or "manual_review" in s:
        return "FALLBACK_SOURCE"
    return "OTHER_SOURCE"


def discover_tickers():
    ticker_rows = []
    source_rows = []

    candidate_files = []
    for d in SEARCH_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*.csv"):
            if file_relevance(p):
                candidate_files.append(p)

    for path in sorted(set(candidate_files)):
        row = {
            "run_time_jst": RUN_TIME_JST,
            "file": str(path),
            "priority": source_priority(path),
            "read_status": "",
            "ticker_columns": "",
            "ticker_count": 0,
            "sample_tickers": "",
            "error": "",
        }

        try:
            df = read_csv_robust(path)
            lower_map = {str(c).strip().lower(): c for c in df.columns}
            hit_cols = [lower_map[c] for c in TICKER_COLS if c in lower_map]

            tickers = set()
            for col in hit_cols:
                for v in df[col].dropna().tolist():
                    t = normalize_ticker(v)
                    if t:
                        tickers.add(t)

            row["read_status"] = "OK"
            row["ticker_columns"] = ",".join([str(c) for c in hit_cols])
            row["ticker_count"] = len(tickers)
            row["sample_tickers"] = ",".join(sorted(tickers)[:20])

            for t in sorted(tickers):
                ticker_rows.append({
                    "run_time_jst": RUN_TIME_JST,
                    "ticker": t,
                    "source_file": str(path),
                    "source_priority": source_priority(path),
                })

        except Exception as e:
            row["read_status"] = "ERROR"
            row["error"] = repr(e)

        source_rows.append(row)

    tickers_df = pd.DataFrame(ticker_rows)
    sources_df = pd.DataFrame(source_rows)

    if tickers_df.empty:
        return tickers_df, sources_df

    # One row per ticker, preserving all source files.
    grouped = (
        tickers_df
        .groupby("ticker", as_index=False)
        .agg({
            "run_time_jst": "first",
            "source_file": lambda x: " | ".join(sorted(set(map(str, x)))),
            "source_priority": lambda x: " | ".join(sorted(set(map(str, x)))),
        })
    )
    return grouped.sort_values("ticker"), sources_df.sort_values(["priority", "file"])


def extract_close_series(df):
    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if any(str(part).lower() == "close" for part in c)]
        if not close_cols:
            return None
        s = df[close_cols[0]]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
    else:
        close_name = None
        for c in df.columns:
            if str(c).lower() == "close":
                close_name = c
                break
        if close_name is None:
            return None
        s = df[close_name]

    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]

    s = pd.to_numeric(s, errors="coerce").dropna()
    return s


def fetch_latest_price(ticker):
    yf_tickers_to_try = [ticker]
    if "." in ticker:
        yf_tickers_to_try.append(ticker.replace(".", "-"))

    last_error = ""

    for yf_ticker in yf_tickers_to_try:
        try:
            df = yf.download(
                yf_ticker,
                period="10d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            close_series = extract_close_series(df)

            if close_series is None or close_series.empty:
                last_error = "NO_CLOSE_SERIES"
                continue

            latest_date = close_series.index[-1].strftime("%Y-%m-%d")
            latest_close = float(close_series.iloc[-1])

            return {
                "ticker": ticker,
                "yf_ticker": yf_ticker,
                "price_source": "yfinance",
                "fetch_status": "OK",
                "latest_price_date": latest_date,
                "latest_close": round(latest_close, 4),
                "error": "",
            }

        except Exception as e:
            last_error = repr(e)

    return {
        "ticker": ticker,
        "yf_ticker": ticker,
        "price_source": "yfinance",
        "fetch_status": "ERROR",
        "latest_price_date": "",
        "latest_close": "",
        "error": last_error,
    }


def build_report(tickers_df, sources_df, prices_df, audit_status):
    total_tickers = 0 if tickers_df.empty else len(tickers_df)
    source_file_count = 0 if sources_df.empty else len(sources_df)
    price_ok_count = int((prices_df["fetch_status"] == "OK").sum()) if not prices_df.empty else 0
    price_fail_count = int((prices_df["fetch_status"] != "OK").sum()) if not prices_df.empty else 0

    if not prices_df.empty and "latest_price_date" in prices_df.columns:
        ok_dates = prices_df.loc[prices_df["fetch_status"] == "OK", "latest_price_date"]
        ok_dates = ok_dates[ok_dates.astype(str).str.len() > 0]
        max_date = "" if ok_dates.empty else str(ok_dates.max())
        min_date = "" if ok_dates.empty else str(ok_dates.min())
    else:
        max_date = ""
        min_date = ""

    date_counts_md = "暂无"
    if not prices_df.empty and "latest_price_date" in prices_df.columns:
        tmp = prices_df.copy()
        tmp["latest_price_date"] = tmp["latest_price_date"].fillna("").astype(str)
        counts = tmp.groupby("latest_price_date").size().reset_index(name="count")
        lines = ["| latest_price_date | count |", "|---|---:|"]
        for _, r in counts.sort_values("latest_price_date").iterrows():
            lines.append(f"| {r['latest_price_date']} | {int(r['count'])} |")
        date_counts_md = "\n".join(lines)

    bad_prices_md = "无"
    if not prices_df.empty:
        bad = prices_df[prices_df["fetch_status"] != "OK"].copy()
        if not bad.empty:
            lines = ["| ticker | fetch_status | error |", "|---|---|---|"]
            for _, r in bad.head(50).iterrows():
                err = str(r.get("error", "")).replace("|", "/")
                lines.append(f"| {r['ticker']} | {r['fetch_status']} | {err} |")
            bad_prices_md = "\n".join(lines)

    sample_prices_md = "无"
    if not prices_df.empty:
        lines = ["| ticker | latest_price_date | latest_close | freshness_status |", "|---|---:|---:|---|"]
        for _, r in prices_df.sort_values("ticker").head(50).iterrows():
            lines.append(
                f"| {r['ticker']} | {r.get('latest_price_date','')} | {r.get('latest_close','')} | {r.get('freshness_status','')} |"
            )
        sample_prices_md = "\n".join(lines)

    md = f"""# V17.6A Full Universe Latest Price Audit

生成时间：{RUN_TIME_JST}

## 1. 结论

- AUDIT_STATUS: `{audit_status}`
- UNIVERSE_TICKER_COUNT: `{total_tickers}`
- SOURCE_FILE_COUNT: `{source_file_count}`
- PRICE_OK_COUNT: `{price_ok_count}`
- PRICE_FAIL_COUNT: `{price_fail_count}`
- MIN_LATEST_PRICE_DATE: `{min_date}`
- MAX_LATEST_PRICE_DATE: `{max_date}`

## 2. 这一步的意义

V17.6A 不生成买卖建议，只检查新的价格地基是否成立。

目标：

1. 每次手动运行时重新发现股票池 ticker；
2. 每只 ticker 强制拉取 yfinance 最新可用日线 close；
3. 保存 latest_price_date / latest_close / source / freshness_status；
4. 后续 daily 建议必须基于这份 price snapshot，而不是旧 helper 价格。

## 3. latest_price_date 分布

{date_counts_md}

## 4. 价格样例

{sample_prices_md}

## 5. 失败价格

{bad_prices_md}

## 6. 输出文件

- FULL UNIVERSE TICKERS: `{OUT_TICKERS}`
- UNIVERSE SOURCE FILES: `{OUT_SOURCES}`
- LATEST PRICES: `{OUT_PRICES}`
- STATE PRICE SNAPSHOT: `{OUT_STATE_PRICES}`
- REPORT: `{OUT_REPORT}`
- READ FIRST: `{OUT_READ_FIRST}`

## 7. 下一步

如果 AUDIT_STATUS 是 OK，则进入 V17.6B，把 official daily 改成：

手动运行 → 全股票池 → 最新价格 → price freshness gate → 操作建议。

如果 AUDIT_STATUS 是 WARN 或 FAIL，先修 ticker source / price fetch，不允许恢复买入建议。
"""
    OUT_REPORT.write_text(md, encoding="utf-8")


def main():
    print("=== V17.6A FULL UNIVERSE LATEST PRICE AUDIT START ===")
    print(f"ROOT: {ROOT}")

    tickers_df, sources_df = discover_tickers()

    if sources_df.empty:
        sources_df = pd.DataFrame(columns=[
            "run_time_jst", "file", "priority", "read_status", "ticker_columns",
            "ticker_count", "sample_tickers", "error"
        ])
    sources_df.to_csv(OUT_SOURCES, index=False, encoding="utf-8-sig")

    if tickers_df.empty:
        pd.DataFrame(columns=["run_time_jst", "ticker", "source_file", "source_priority"]).to_csv(
            OUT_TICKERS, index=False, encoding="utf-8-sig"
        )
        empty_prices = pd.DataFrame(columns=[
            "run_time_jst", "ticker", "yf_ticker", "price_source", "fetch_status",
            "latest_price_date", "latest_close", "freshness_status", "error"
        ])
        empty_prices.to_csv(OUT_PRICES, index=False, encoding="utf-8-sig")
        empty_prices.to_csv(OUT_STATE_PRICES, index=False, encoding="utf-8-sig")
        build_report(tickers_df, sources_df, empty_prices, "FAIL_NO_TICKERS")
        OUT_READ_FIRST.write_text(str(OUT_REPORT), encoding="utf-8")
        print("AUDIT_STATUS: FAIL_NO_TICKERS")
        print(f"REPORT: {OUT_REPORT}")
        return 1

    tickers_df.to_csv(OUT_TICKERS, index=False, encoding="utf-8-sig")

    prices = []
    ticker_list = tickers_df["ticker"].dropna().astype(str).sort_values().tolist()

    print(f"DISCOVERED_TICKERS: {len(ticker_list)}")
    print("FETCHING_PRICES_FROM_YFINANCE...")

    for i, ticker in enumerate(ticker_list, start=1):
        print(f"[{i}/{len(ticker_list)}] {ticker}")
        row = fetch_latest_price(ticker)
        row["run_time_jst"] = RUN_TIME_JST
        prices.append(row)

    prices_df = pd.DataFrame(prices)

    if prices_df.empty:
        prices_df = pd.DataFrame(columns=[
            "run_time_jst", "ticker", "yf_ticker", "price_source", "fetch_status",
            "latest_price_date", "latest_close", "error"
        ])

    ok_dates = prices_df.loc[prices_df["fetch_status"] == "OK", "latest_price_date"]
    ok_dates = ok_dates[ok_dates.astype(str).str.len() > 0]
    max_date = "" if ok_dates.empty else str(ok_dates.max())

    freshness = []
    for _, r in prices_df.iterrows():
        if r["fetch_status"] != "OK":
            freshness.append("PRICE_FETCH_FAIL")
        elif str(r["latest_price_date"]) == max_date:
            freshness.append("OK_LATEST_AVAILABLE")
        else:
            freshness.append("STALE_VS_MAX_DATE")
    prices_df["freshness_status"] = freshness

    merged = prices_df.merge(
        tickers_df[["ticker", "source_priority", "source_file"]],
        on="ticker",
        how="left",
    )

    ordered_cols = [
        "run_time_jst", "ticker", "yf_ticker", "price_source", "fetch_status",
        "latest_price_date", "latest_close", "freshness_status",
        "source_priority", "source_file", "error"
    ]
    for c in ordered_cols:
        if c not in merged.columns:
            merged[c] = ""

    merged = merged[ordered_cols].sort_values("ticker")
    merged.to_csv(OUT_PRICES, index=False, encoding="utf-8-sig")
    merged.to_csv(OUT_STATE_PRICES, index=False, encoding="utf-8-sig")

    fail_count = int((merged["fetch_status"] != "OK").sum())
    stale_count = int((merged["freshness_status"] == "STALE_VS_MAX_DATE").sum())

    if fail_count > 0:
        audit_status = "WARN_PRICE_FETCH_PARTIAL_FAIL"
    elif stale_count > 0:
        audit_status = "WARN_MIXED_PRICE_DATES"
    else:
        audit_status = "OK"

    build_report(tickers_df, sources_df, merged, audit_status)
    OUT_READ_FIRST.write_text(str(OUT_REPORT), encoding="utf-8")

    print("")
    print("=== V17.6A FULL UNIVERSE LATEST PRICE AUDIT READY ===")
    print(f"AUDIT_STATUS: {audit_status}")
    print(f"UNIVERSE_TICKER_COUNT: {len(ticker_list)}")
    print(f"PRICE_OK_COUNT: {int((merged['fetch_status'] == 'OK').sum())}")
    print(f"PRICE_FAIL_COUNT: {fail_count}")
    print(f"MAX_LATEST_PRICE_DATE: {max_date}")
    print("")
    print(f"REPORT: {OUT_REPORT}")
    print(f"LATEST PRICES: {OUT_PRICES}")
    print(f"STATE PRICE SNAPSHOT: {OUT_STATE_PRICES}")
    print(f"READ FIRST: {OUT_READ_FIRST}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
