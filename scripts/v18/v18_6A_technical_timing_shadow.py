import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, encoding="utf-8-sig")


def find_ticker_col(df: pd.DataFrame):
    for c in ["ticker", "Ticker", "symbol", "Symbol", "name", "Name", "TICKER", "SYMBOL"]:
        if c in df.columns:
            return c
    return None


def load_universe(root: Path):
    candidates = [
        root / "outputs" / "v18" / "factor_pack" / "V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        root / "outputs" / "v18" / "factor_pack" / "V18_CURRENT_FACTOR_PACK_RANKING.csv",
        root / "outputs" / "v18" / "daily_integrated" / "V18_CURRENT_FINAL_DAILY.csv",
    ]

    for p in candidates:
        df = read_csv(p)
        if df.empty:
            continue
        col = find_ticker_col(df)
        if not col:
            continue
        vals = df[col].dropna().astype(str).str.strip().tolist()
        vals = [v for v in vals if v and v.upper() not in {"NAN", "NONE"}]
        if vals:
            seen = set()
            out = []
            for v in vals:
                if v not in seen:
                    seen.add(v)
                    out.append(v)
            print(f"UNIVERSE_SOURCE: {p}")
            print(f"UNIVERSE_COUNT: {len(out)}")
            return out

    raise RuntimeError("No universe file found. Expected V18 factor pack ranking CSV with ticker column.")


def yf_symbol(ticker: str) -> str:
    return str(ticker).strip().replace(".", "-")


def get_yfinance():
    try:
        import yfinance as yf
        return yf
    except Exception as e:
        raise RuntimeError("Missing yfinance. Run: python -m pip install yfinance") from e


def download_ohlcv(yf, ticker: str, lookback_days: int) -> pd.DataFrame:
    symbol = yf_symbol(ticker)
    period = f"{max(260, lookback_days + 100)}d"

    df = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [x[0] for x in df.columns]

    df = df.reset_index()

    rename = {}
    for c in df.columns:
        lc = str(c).lower()
        if lc == "date":
            rename[c] = "date"
        elif lc == "open":
            rename[c] = "open"
        elif lc == "high":
            rename[c] = "high"
        elif lc == "low":
            rename[c] = "low"
        elif lc == "close":
            rename[c] = "close"
        elif lc == "volume":
            rename[c] = "volume"

    df = df.rename(columns=rename)

    need = ["date", "open", "high", "low", "close", "volume"]
    if any(c not in df.columns for c in need):
        return pd.DataFrame()

    df = df[need].copy()
    df["ticker"] = ticker
    df["yf_ticker"] = symbol
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["high", "low", "close"])
    return df.sort_values("date").tail(lookback_days + 100)


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    out = out.where(~((avg_loss == 0) & (avg_gain > 0)), 100)
    out = out.where(~((avg_gain == 0) & (avg_loss > 0)), 0)
    return out


def kdj(df: pd.DataFrame, n: int = 9):
    low_n = df["low"].rolling(n, min_periods=n).min()
    high_n = df["high"].rolling(n, min_periods=n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    rsv = rsv.clip(0, 100)

    k = rsv.ewm(alpha=1 / 3, min_periods=n, adjust=False).mean()
    d = k.ewm(alpha=1 / 3, min_periods=n, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def bb_status(row):
    if pd.isna(row["bb_percent_b"]):
        return "BB_UNKNOWN"
    if row["close"] > row["bb_upper"]:
        return "BB_ABOVE_UPPER"
    if row["close"] < row["bb_lower"]:
        return "BB_BELOW_LOWER"
    if row["bb_percent_b"] >= 0.9:
        return "BB_NEAR_UPPER"
    if row["bb_percent_b"] <= 0.1:
        return "BB_NEAR_LOWER"
    if row["bb_percent_b"] >= 0.6:
        return "BB_UPPER_HALF"
    if row["bb_percent_b"] <= 0.4:
        return "BB_LOWER_HALF"
    return "BB_MID"


def rsi_status(x):
    if pd.isna(x):
        return "RSI_UNKNOWN"
    if x >= 75:
        return "RSI_EXTREME_OVERHEAT"
    if x >= 70:
        return "RSI_OVERHEAT"
    if x >= 60:
        return "RSI_STRONG"
    if x >= 45:
        return "RSI_NEUTRAL"
    if x >= 30:
        return "RSI_WEAK"
    return "RSI_OVERSOLD"


def kdj_status(k, d, j, pk, pd_):
    if pd.isna(k) or pd.isna(d) or pd.isna(j):
        return "KDJ_UNKNOWN"

    golden = (not pd.isna(pk)) and (not pd.isna(pd_)) and pk <= pd_ and k > d
    dead = (not pd.isna(pk)) and (not pd.isna(pd_)) and pk >= pd_ and k < d

    if k > 80 and d > 80 and j > 100:
        return "KDJ_EXTREME_OVERHEAT"
    if k < 20 and d < 20 and j < 0:
        return "KDJ_EXTREME_OVERSOLD"
    if golden and max(k, d) <= 50:
        return "KDJ_LOW_GOLDEN_CROSS"
    if dead and min(k, d) >= 50:
        return "KDJ_HIGH_DEAD_CROSS"
    if k > 80 and d > 80:
        return "KDJ_OVERHEAT"
    if k < 20 and d < 20:
        return "KDJ_OVERSOLD"
    if golden:
        return "KDJ_GOLDEN_CROSS"
    if dead:
        return "KDJ_DEAD_CROSS"
    return "KDJ_NEUTRAL"


def vix_regime(v):
    if pd.isna(v):
        return "VIX_UNKNOWN"
    if v >= 30:
        return "VIX_PANIC_BLOCK_LEVERAGE"
    if v >= 25:
        return "VIX_RISK_OFF_DELEVERAGE"
    if v >= 18:
        return "VIX_CAUTION"
    return "VIX_NORMAL"


def compute_ticker(df: pd.DataFrame):
    x = df.copy().sort_values("date").reset_index(drop=True)

    x["bb_mid"] = x["close"].rolling(20, min_periods=20).mean()
    x["bb_std"] = x["close"].rolling(20, min_periods=20).std()
    x["bb_upper"] = x["bb_mid"] + 2 * x["bb_std"]
    x["bb_lower"] = x["bb_mid"] - 2 * x["bb_std"]
    x["bb_percent_b"] = (x["close"] - x["bb_lower"]) / (x["bb_upper"] - x["bb_lower"]).replace(0, np.nan)
    x["bb_bandwidth"] = (x["bb_upper"] - x["bb_lower"]) / x["bb_mid"].replace(0, np.nan)
    x["bb_bandwidth_q20"] = x["bb_bandwidth"].rolling(120, min_periods=60).quantile(0.2)
    x["bb_squeeze_flag"] = x["bb_bandwidth"] <= x["bb_bandwidth_q20"]

    x["rsi_14"] = rsi(x["close"], 14)

    k, d, j = kdj(x, 9)
    x["kdj_k"] = k
    x["kdj_d"] = d
    x["kdj_j"] = j

    x["vol_ma5"] = x["volume"].rolling(5, min_periods=5).mean()
    x["vol_ma20"] = x["volume"].rolling(20, min_periods=20).mean()
    x["volume_ratio_5_20"] = x["vol_ma5"] / x["vol_ma20"].replace(0, np.nan)

    last = x.iloc[-1]
    prev = x.iloc[-2] if len(x) >= 2 else last

    bbs = bb_status(last)
    rsis = rsi_status(last["rsi_14"])
    kdjs = kdj_status(last["kdj_k"], last["kdj_d"], last["kdj_j"], prev["kdj_k"], prev["kdj_d"])

    overheat = 0
    pullback = 0
    breakout = 0
    labels = []

    if bbs in {"BB_ABOVE_UPPER", "BB_NEAR_UPPER"}:
        overheat += 10
        labels.append("BB_UPPER_CHASE_RISK")

    if rsis in {"RSI_OVERHEAT", "RSI_EXTREME_OVERHEAT"}:
        overheat += 10 if rsis == "RSI_OVERHEAT" else 15
        labels.append(rsis)

    if kdjs in {"KDJ_OVERHEAT", "KDJ_EXTREME_OVERHEAT", "KDJ_HIGH_DEAD_CROSS"}:
        overheat += 10 if kdjs != "KDJ_EXTREME_OVERHEAT" else 15
        labels.append(kdjs)

    if bbs in {"BB_LOWER_HALF", "BB_NEAR_LOWER", "BB_BELOW_LOWER"}:
        pullback += 8

    if rsis in {"RSI_WEAK", "RSI_OVERSOLD"}:
        pullback += 6

    if kdjs in {"KDJ_LOW_GOLDEN_CROSS", "KDJ_OVERSOLD", "KDJ_EXTREME_OVERSOLD"}:
        pullback += 8

    if bbs == "BB_ABOVE_UPPER" and not pd.isna(last["rsi_14"]) and 55 <= last["rsi_14"] <= 75:
        breakout += 5

    if not pd.isna(last["volume_ratio_5_20"]) and last["volume_ratio_5_20"] >= 1.2:
        breakout += 4

    score = max(0, min(100, 50 + pullback + breakout - overheat))

    if score >= 65 and overheat <= 10:
        signal = "TECH_TIMING_WATCH_POSITIVE"
    elif overheat >= 25:
        signal = "TECH_TIMING_OVERHEAT_AVOID_CHASE"
    elif pullback >= 14:
        signal = "TECH_TIMING_PULLBACK_WATCH"
    else:
        signal = "TECH_TIMING_NEUTRAL"

    return {
        "ticker": last["ticker"],
        "yf_ticker": last["yf_ticker"],
        "price_date": last["date"],
        "close": round(float(last["close"]), 4),
        "bb_mid_20": round(float(last["bb_mid"]), 4) if not pd.isna(last["bb_mid"]) else np.nan,
        "bb_upper_20_2": round(float(last["bb_upper"]), 4) if not pd.isna(last["bb_upper"]) else np.nan,
        "bb_lower_20_2": round(float(last["bb_lower"]), 4) if not pd.isna(last["bb_lower"]) else np.nan,
        "bb_percent_b": round(float(last["bb_percent_b"]), 4) if not pd.isna(last["bb_percent_b"]) else np.nan,
        "bb_bandwidth": round(float(last["bb_bandwidth"]), 4) if not pd.isna(last["bb_bandwidth"]) else np.nan,
        "bb_squeeze_flag": bool(last["bb_squeeze_flag"]) if not pd.isna(last["bb_squeeze_flag"]) else False,
        "bb_status": bbs,
        "rsi_14": round(float(last["rsi_14"]), 4) if not pd.isna(last["rsi_14"]) else np.nan,
        "rsi_status": rsis,
        "kdj_k": round(float(last["kdj_k"]), 4) if not pd.isna(last["kdj_k"]) else np.nan,
        "kdj_d": round(float(last["kdj_d"]), 4) if not pd.isna(last["kdj_d"]) else np.nan,
        "kdj_j": round(float(last["kdj_j"]), 4) if not pd.isna(last["kdj_j"]) else np.nan,
        "kdj_status": kdjs,
        "volume_ratio_5_20": round(float(last["volume_ratio_5_20"]), 4) if not pd.isna(last["volume_ratio_5_20"]) else np.nan,
        "overheat_penalty": overheat,
        "pullback_timing_bonus": pullback,
        "breakout_confirmation_bonus": breakout,
        "technical_timing_score": round(float(score), 4),
        "technical_signal": signal,
        "technical_warning_label": ";".join(labels) if labels else "NONE",
        "option_data_status": "NOT_AVAILABLE_RESERVED",
        "put_call_ratio": np.nan,
        "iv_rank_proxy": np.nan,
        "gamma_squeeze_status": "NOT_AVAILABLE_RESERVED",
        "gamma_squeeze_risk_label": "NOT_AVAILABLE_RESERVED",
        "official_decision_impact": "NONE",
    }


def get_vix(yf):
    try:
        df = download_ohlcv(yf, "^VIX", 120)
        if df.empty:
            return {"vix_date": "", "vix_close": np.nan, "vix_regime": "VIX_UNKNOWN"}
        last = df.sort_values("date").iloc[-1]
        v = float(last["close"])
        return {"vix_date": last["date"], "vix_close": round(v, 4), "vix_regime": vix_regime(v)}
    except Exception:
        return {"vix_date": "", "vix_close": np.nan, "vix_regime": "VIX_UNKNOWN"}


def write_report(df, report_path: Path, read_first_path: Path, vix_info: dict, current_csv: Path):
    total = len(df)
    positive = int((df["technical_signal"] == "TECH_TIMING_WATCH_POSITIVE").sum())
    pullback = int((df["technical_signal"] == "TECH_TIMING_PULLBACK_WATCH").sum())
    overheat = int((df["technical_signal"] == "TECH_TIMING_OVERHEAT_AVOID_CHASE").sum())
    squeeze = int(df["bb_squeeze_flag"].sum())

    cols = [
        "ticker", "price_date", "close", "technical_timing_score", "technical_signal",
        "bb_status", "rsi_status", "kdj_status", "volume_ratio_5_20", "technical_warning_label"
    ]

    top_positive = df.sort_values(
        ["technical_timing_score", "pullback_timing_bonus", "breakout_confirmation_bonus"],
        ascending=[False, False, False]
    ).head(15)[cols]

    top_overheat = df.sort_values(
        ["overheat_penalty", "technical_timing_score"],
        ascending=[False, False]
    ).head(15)[cols]

    md = []
    md.append("# V18.6A Technical Timing Shadow Report\n")
    md.append("## 1. Status\n")
    md.append("- V18_6A_STATUS: `OK_TECHNICAL_TIMING_SHADOW_READY`")
    md.append(f"- TOTAL_TICKER_COUNT: `{total}`")
    md.append(f"- TECH_TIMING_WATCH_POSITIVE_COUNT: `{positive}`")
    md.append(f"- TECH_TIMING_PULLBACK_WATCH_COUNT: `{pullback}`")
    md.append(f"- TECH_TIMING_OVERHEAT_AVOID_CHASE_COUNT: `{overheat}`")
    md.append(f"- BB_SQUEEZE_COUNT: `{squeeze}`")
    md.append(f"- VIX_DATE: `{vix_info.get('vix_date', '')}`")
    md.append(f"- VIX_CLOSE: `{vix_info.get('vix_close', np.nan)}`")
    md.append(f"- VIX_REGIME: `{vix_info.get('vix_regime', 'VIX_UNKNOWN')}`")
    md.append("- OFFICIAL_DECISION_IMPACT: `NONE`\n")
    md.append("## 2. 技术择时分数靠前\n")
    md.append(top_positive.to_markdown(index=False))
    md.append("\n## 3. 过热/追高风险靠前\n")
    md.append(top_overheat.to_markdown(index=False))
    md.append("\n## 4. 说明\n")
    md.append("本模块加入 Bollinger Bands、RSI、KDJ、VIX；期权和 Gamma Squeeze 字段先预留。当前是 shadow 层，不改变官方交易动作。\n")

    report_path.write_text("\n".join(md), encoding="utf-8")

    read_first = f"""V18.6A TECHNICAL TIMING SHADOW READ FIRST

STATUS:
OK_TECHNICAL_TIMING_SHADOW_READY

TOTAL_TICKER_COUNT:
{total}

VIX:
{vix_info.get('vix_close', np.nan)} / {vix_info.get('vix_regime', 'VIX_UNKNOWN')}

OFFICIAL_DECISION_IMPACT:
NONE

CSV:
{current_csv}

REPORT:
{report_path}
"""
    read_first_path.write_text(read_first, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--lookback-days", type=int, default=420)
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = root / "outputs" / "v18" / "technical_timing"
    out_dir.mkdir(parents=True, exist_ok=True)

    s = stamp()
    current_csv = out_dir / "V18_6A_CURRENT_TECHNICAL_TIMING.csv"
    stamped_csv = out_dir / f"V18_6A_TECHNICAL_TIMING_{s}.csv"
    current_report = out_dir / "V18_6A_CURRENT_TECHNICAL_TIMING_REPORT.md"
    global_report = out_dir / "V18_CURRENT_TECHNICAL_TIMING.md"
    read_first = out_dir / "V18_6A_READ_FIRST.txt"
    fail_csv = out_dir / "V18_6A_CURRENT_TECHNICAL_TIMING_FAILURES.csv"

    yf = get_yfinance()
    tickers = load_universe(root)

    rows = []
    fails = []

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}")
        try:
            hist = download_ohlcv(yf, ticker, args.lookback_days)
            if hist.empty or len(hist) < 80:
                fails.append({"ticker": ticker, "reason": "NO_OR_INSUFFICIENT_HISTORY"})
                continue
            rows.append(compute_ticker(hist))
        except Exception as e:
            fails.append({"ticker": ticker, "reason": f"{type(e).__name__}: {e}"})

    if not rows:
        raise RuntimeError("No rows produced.")

    df = pd.DataFrame(rows)

    vix_info = get_vix(yf)
    df["vix_date"] = vix_info.get("vix_date", "")
    df["vix_close"] = vix_info.get("vix_close", np.nan)
    df["vix_regime"] = vix_info.get("vix_regime", "VIX_UNKNOWN")

    df = df.sort_values(
        ["technical_timing_score", "overheat_penalty", "ticker"],
        ascending=[False, True, True]
    )

    df.to_csv(current_csv, index=False, encoding="utf-8-sig")
    df.to_csv(stamped_csv, index=False, encoding="utf-8-sig")

    if fails:
        pd.DataFrame(fails).to_csv(fail_csv, index=False, encoding="utf-8-sig")

    write_report(df, current_report, read_first, vix_info, current_csv)
    global_report.write_text(current_report.read_text(encoding="utf-8"), encoding="utf-8")

    print("")
    print("=== V18.6A TECHNICAL TIMING SHADOW READY ===")
    print(f"TOTAL_TICKER_COUNT: {len(df)}")
    print(f"FAIL_COUNT: {len(fails)}")
    print(f"VIX_CLOSE: {vix_info.get('vix_close', np.nan)}")
    print(f"VIX_REGIME: {vix_info.get('vix_regime', 'VIX_UNKNOWN')}")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"CSV: {current_csv}")
    print(f"REPORT: {current_report}")
    print(f"READ_FIRST: {read_first}")


if __name__ == "__main__":
    main()
