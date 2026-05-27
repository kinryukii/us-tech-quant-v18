from pathlib import Path
from datetime import datetime
import sys
import traceback
import pandas as pd

try:
    import yfinance as yf
except Exception as e:
    print("IMPORT_ERROR:", repr(e))
    sys.exit(1)

ROOT = Path(r"D:\us-tech-quant")
SCREENED_YAML = ROOT / "configs" / "v16" / "universe" / "us_full_screened_generated.yaml"
SECOND_STAGE_YAML = ROOT / "configs" / "v16" / "universe" / "us_full_second_stage_generated.yaml"

OUT_DIR = ROOT / "outputs" / "v17" / "price"
STATE_DIR = ROOT / "state"
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIME_JST = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

OUT_SCREENED_TICKERS = OUT_DIR / "v17_6E_screened_universe_tickers.csv"
OUT_SECOND_STAGE_TICKERS = OUT_DIR / "v17_6E_second_stage_tickers.csv"
OUT_PRICES = OUT_DIR / "v17_6E_screened_universe_latest_prices.csv"
OUT_STATE_PRICES = STATE_DIR / "v17_6E_screened_universe_latest_price_snapshot.csv"
OUT_REPORT = OUT_DIR / "V17_6E_SCREENED_UNIVERSE_LATEST_PRICE_AUDIT.md"
OUT_READ_FIRST = OUT_DIR / "V17_6E_READ_FIRST.txt"


def read_yaml_tickers(path: Path):
    tickers = []
    if not path.exists():
        return tickers

    in_tickers = False
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith("tickers:"):
            in_tickers = True
            continue
        if in_tickers and line.startswith("-"):
            t = line.replace("-", "", 1).strip().upper()
            if t:
                tickers.append(t)
    return sorted(set(tickers))


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

    return pd.to_numeric(s, errors="coerce").dropna()


def fetch_latest_price(ticker: str):
    yf_candidates = [ticker]
    if "." in ticker:
        yf_candidates.append(ticker.replace(".", "-"))

    last_error = ""

    for yf_ticker in yf_candidates:
        try:
            df = yf.download(
                yf_ticker,
                period="10d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            s = extract_close_series(df)

            if s is None or s.empty:
                last_error = "NO_CLOSE_SERIES"
                continue

            return {
                "ticker": ticker,
                "yf_ticker": yf_ticker,
                "price_source": "yfinance",
                "fetch_status": "OK",
                "latest_price_date": s.index[-1].strftime("%Y-%m-%d"),
                "latest_close": round(float(s.iloc[-1]), 4),
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


def main():
    print("=== V17.6E SCREENED UNIVERSE LATEST PRICE AUDIT START ===")
    print(f"SCREENED_YAML: {SCREENED_YAML}")
    print(f"SECOND_STAGE_YAML: {SECOND_STAGE_YAML}")

    screened = read_yaml_tickers(SCREENED_YAML)
    second_stage = read_yaml_tickers(SECOND_STAGE_YAML)

    pd.DataFrame([{"ticker": t, "run_time_jst": RUN_TIME_JST, "source_file": str(SCREENED_YAML)} for t in screened]).to_csv(
        OUT_SCREENED_TICKERS, index=False, encoding="utf-8-sig"
    )
    pd.DataFrame([{"ticker": t, "run_time_jst": RUN_TIME_JST, "source_file": str(SECOND_STAGE_YAML)} for t in second_stage]).to_csv(
        OUT_SECOND_STAGE_TICKERS, index=False, encoding="utf-8-sig"
    )

    if not screened:
        audit_status = "FAIL_NO_SCREENED_TICKERS"
        prices_df = pd.DataFrame()
    else:
        rows = []
        print(f"SCREENED_UNIVERSE_COUNT: {len(screened)}")
        print(f"SECOND_STAGE_COUNT: {len(second_stage)}")
        print("FETCHING_SCREENED_UNIVERSE_PRICES_FROM_YFINANCE...")

        second_set = set(second_stage)

        for i, ticker in enumerate(screened, start=1):
            print(f"[{i}/{len(screened)}] {ticker}")
            r = fetch_latest_price(ticker)
            r["run_time_jst"] = RUN_TIME_JST
            r["in_second_stage"] = "YES" if ticker in second_set else "NO"
            r["universe_source"] = "us_full_screened_generated.yaml"
            rows.append(r)

        prices_df = pd.DataFrame(rows)

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

        fail_count = int((prices_df["fetch_status"] != "OK").sum())
        stale_count = int((prices_df["freshness_status"] == "STALE_VS_MAX_DATE").sum())

        if fail_count > 0:
            audit_status = "WARN_PRICE_FETCH_PARTIAL_FAIL"
        elif stale_count > 0:
            audit_status = "WARN_MIXED_PRICE_DATES"
        else:
            audit_status = "OK"

    if prices_df.empty:
        prices_df = pd.DataFrame(columns=[
            "run_time_jst", "ticker", "yf_ticker", "price_source", "fetch_status",
            "latest_price_date", "latest_close", "freshness_status",
            "in_second_stage", "universe_source", "error"
        ])

    ordered = [
        "run_time_jst", "ticker", "yf_ticker", "price_source", "fetch_status",
        "latest_price_date", "latest_close", "freshness_status",
        "in_second_stage", "universe_source", "error"
    ]
    for c in ordered:
        if c not in prices_df.columns:
            prices_df[c] = ""

    prices_df = prices_df[ordered].sort_values("ticker")
    prices_df.to_csv(OUT_PRICES, index=False, encoding="utf-8-sig")
    prices_df.to_csv(OUT_STATE_PRICES, index=False, encoding="utf-8-sig")

    price_ok = int((prices_df["fetch_status"] == "OK").sum())
    price_fail = int((prices_df["fetch_status"] != "OK").sum())

    ok_dates = prices_df.loc[prices_df["fetch_status"] == "OK", "latest_price_date"]
    ok_dates = ok_dates[ok_dates.astype(str).str.len() > 0]
    max_date = "" if ok_dates.empty else str(ok_dates.max())
    min_date = "" if ok_dates.empty else str(ok_dates.min())

    date_counts = prices_df.groupby("latest_price_date").size().reset_index(name="count") if not prices_df.empty else pd.DataFrame()

    lines = []
    lines.append("# V17.6E Screened Universe Latest Price Audit")
    lines.append("")
    lines.append(f"生成时间：{RUN_TIME_JST}")
    lines.append("")
    lines.append("## 1. 结论")
    lines.append("")
    lines.append(f"- AUDIT_STATUS: `{audit_status}`")
    lines.append(f"- SCREENED_UNIVERSE_COUNT: `{len(screened)}`")
    lines.append(f"- SECOND_STAGE_COUNT: `{len(second_stage)}`")
    lines.append(f"- PRICE_OK_COUNT: `{price_ok}`")
    lines.append(f"- PRICE_FAIL_COUNT: `{price_fail}`")
    lines.append(f"- MIN_LATEST_PRICE_DATE: `{min_date}`")
    lines.append(f"- MAX_LATEST_PRICE_DATE: `{max_date}`")
    lines.append("")
    lines.append("## 2. latest_price_date 分布")
    lines.append("")
    lines.append("| latest_price_date | count |")
    lines.append("|---|---:|")
    if date_counts.empty:
        lines.append("| NONE | 0 |")
    else:
        for _, r in date_counts.sort_values("latest_price_date").iterrows():
            lines.append(f"| {r['latest_price_date']} | {int(r['count'])} |")
    lines.append("")
    lines.append("## 3. 第二阶段候选")
    lines.append("")
    lines.append("| ticker | latest_price_date | latest_close | freshness_status |")
    lines.append("|---|---:|---:|---|")
    for _, r in prices_df[prices_df["in_second_stage"] == "YES"].sort_values("ticker").iterrows():
        lines.append(f"| {r['ticker']} | {r['latest_price_date']} | {r['latest_close']} | {r['freshness_status']} |")
    lines.append("")
    lines.append("## 4. 输出文件")
    lines.append("")
    lines.append(f"- SCREENED TICKERS: `{OUT_SCREENED_TICKERS}`")
    lines.append(f"- SECOND STAGE TICKERS: `{OUT_SECOND_STAGE_TICKERS}`")
    lines.append(f"- LATEST PRICES: `{OUT_PRICES}`")
    lines.append(f"- STATE PRICE SNAPSHOT: `{OUT_STATE_PRICES}`")
    lines.append(f"- REPORT: `{OUT_REPORT}`")
    lines.append("")
    lines.append("## 5. 下一步")
    lines.append("")
    lines.append("如果 AUDIT_STATUS 为 OK，则下一步 V17.6F 可以把手动 daily 入口改成：")
    lines.append("")
    lines.append("全量链路 → screened universe 66 只 → 最新价格 → second stage candidate → 操作建议。")
    lines.append("")
    lines.append("如果不是 OK，则不允许生成买入建议。")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    OUT_READ_FIRST.write_text(str(OUT_REPORT), encoding="utf-8")

    print("")
    print("=== V17.6E SCREENED UNIVERSE LATEST PRICE AUDIT READY ===")
    print(f"AUDIT_STATUS: {audit_status}")
    print(f"SCREENED_UNIVERSE_COUNT: {len(screened)}")
    print(f"SECOND_STAGE_COUNT: {len(second_stage)}")
    print(f"PRICE_OK_COUNT: {price_ok}")
    print(f"PRICE_FAIL_COUNT: {price_fail}")
    print(f"MAX_LATEST_PRICE_DATE: {max_date}")
    print("")
    print(f"REPORT: {OUT_REPORT}")
    print(f"LATEST PRICES: {OUT_PRICES}")
    print(f"STATE PRICE SNAPSHOT: {OUT_STATE_PRICES}")
    print(f"READ FIRST: {OUT_READ_FIRST}")

    return 0 if audit_status == "OK" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
