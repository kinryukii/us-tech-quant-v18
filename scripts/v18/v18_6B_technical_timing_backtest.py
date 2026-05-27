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

    raise RuntimeError("No universe file found.")


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
    period = f"{max(300, lookback_days + 160)}d"

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
    return df.sort_values("date").tail(lookback_days + 160)


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


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy().sort_values(["ticker", "date"]).reset_index(drop=True)

    out = []

    for ticker, g in x.groupby("ticker", sort=False):
        g = g.copy().sort_values("date").reset_index(drop=True)

        g["ret_fwd_1"] = g["close"].shift(-1) / g["close"] - 1
        g["ret_fwd_3"] = g["close"].shift(-3) / g["close"] - 1
        g["ret_fwd_5"] = g["close"].shift(-5) / g["close"] - 1
        g["ret_fwd_10"] = g["close"].shift(-10) / g["close"] - 1
        g["ret_fwd_20"] = g["close"].shift(-20) / g["close"] - 1

        g["bb_mid"] = g["close"].rolling(20, min_periods=20).mean()
        g["bb_std"] = g["close"].rolling(20, min_periods=20).std()
        g["bb_upper"] = g["bb_mid"] + 2 * g["bb_std"]
        g["bb_lower"] = g["bb_mid"] - 2 * g["bb_std"]
        g["bb_percent_b"] = (g["close"] - g["bb_lower"]) / (g["bb_upper"] - g["bb_lower"]).replace(0, np.nan)
        g["bb_bandwidth"] = (g["bb_upper"] - g["bb_lower"]) / g["bb_mid"].replace(0, np.nan)
        g["bb_bandwidth_q20"] = g["bb_bandwidth"].rolling(120, min_periods=60).quantile(0.2)
        g["bb_squeeze_flag"] = g["bb_bandwidth"] <= g["bb_bandwidth_q20"]

        g["rsi_14"] = rsi(g["close"], 14)

        k, d, j = kdj(g, 9)
        g["kdj_k"] = k
        g["kdj_d"] = d
        g["kdj_j"] = j

        g["kdj_prev_k"] = g["kdj_k"].shift(1)
        g["kdj_prev_d"] = g["kdj_d"].shift(1)

        g["vol_ma5"] = g["volume"].rolling(5, min_periods=5).mean()
        g["vol_ma20"] = g["volume"].rolling(20, min_periods=20).mean()
        g["volume_ratio_5_20"] = g["vol_ma5"] / g["vol_ma20"].replace(0, np.nan)

        out.append(g)

    return pd.concat(out, ignore_index=True)


def make_signals(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()

    x["bb_lower_zone"] = x["bb_percent_b"] <= 0.4
    x["bb_near_lower"] = x["bb_percent_b"] <= 0.1
    x["bb_upper_zone"] = x["bb_percent_b"] >= 0.6
    x["bb_near_upper"] = x["bb_percent_b"] >= 0.9
    x["bb_above_upper"] = x["close"] > x["bb_upper"]
    x["bb_below_lower"] = x["close"] < x["bb_lower"]

    x["rsi_weak"] = (x["rsi_14"] >= 30) & (x["rsi_14"] < 45)
    x["rsi_oversold"] = x["rsi_14"] < 30
    x["rsi_strong"] = (x["rsi_14"] >= 60) & (x["rsi_14"] < 70)
    x["rsi_overheat"] = x["rsi_14"] >= 70
    x["rsi_extreme_overheat"] = x["rsi_14"] >= 75

    x["kdj_oversold"] = (x["kdj_k"] < 20) & (x["kdj_d"] < 20)
    x["kdj_extreme_oversold"] = (x["kdj_k"] < 20) & (x["kdj_d"] < 20) & (x["kdj_j"] < 0)
    x["kdj_overheat"] = (x["kdj_k"] > 80) & (x["kdj_d"] > 80)
    x["kdj_extreme_overheat"] = (x["kdj_k"] > 80) & (x["kdj_d"] > 80) & (x["kdj_j"] > 100)

    x["kdj_golden_cross"] = (x["kdj_prev_k"] <= x["kdj_prev_d"]) & (x["kdj_k"] > x["kdj_d"])
    x["kdj_dead_cross"] = (x["kdj_prev_k"] >= x["kdj_prev_d"]) & (x["kdj_k"] < x["kdj_d"])
    x["kdj_low_golden_cross"] = x["kdj_golden_cross"] & (x[["kdj_k", "kdj_d"]].max(axis=1) <= 50)
    x["kdj_high_dead_cross"] = x["kdj_dead_cross"] & (x[["kdj_k", "kdj_d"]].min(axis=1) >= 50)

    x["overheat_penalty"] = 0
    x.loc[x["bb_near_upper"] | x["bb_above_upper"], "overheat_penalty"] += 10
    x.loc[x["rsi_overheat"], "overheat_penalty"] += 10
    x.loc[x["rsi_extreme_overheat"], "overheat_penalty"] += 5
    x.loc[x["kdj_overheat"] | x["kdj_high_dead_cross"], "overheat_penalty"] += 10
    x.loc[x["kdj_extreme_overheat"], "overheat_penalty"] += 5

    x["pullback_timing_bonus"] = 0
    x.loc[x["bb_lower_zone"] | x["bb_below_lower"], "pullback_timing_bonus"] += 8
    x.loc[x["rsi_weak"] | x["rsi_oversold"], "pullback_timing_bonus"] += 6
    x.loc[x["kdj_oversold"] | x["kdj_extreme_oversold"] | x["kdj_low_golden_cross"], "pullback_timing_bonus"] += 8

    x["breakout_confirmation_bonus"] = 0
    x.loc[x["bb_above_upper"] & (x["rsi_14"] >= 55) & (x["rsi_14"] <= 75), "breakout_confirmation_bonus"] += 5
    x.loc[x["volume_ratio_5_20"] >= 1.2, "breakout_confirmation_bonus"] += 4

    x["technical_timing_score"] = (
        50 + x["pullback_timing_bonus"] + x["breakout_confirmation_bonus"] - x["overheat_penalty"]
    ).clip(0, 100)

    x["signal_watch_positive"] = (x["technical_timing_score"] >= 65) & (x["overheat_penalty"] <= 10)
    x["signal_pullback_watch"] = (x["pullback_timing_bonus"] >= 14) & ~x["signal_watch_positive"]
    x["signal_overheat_avoid"] = x["overheat_penalty"] >= 25
    x["signal_bb_squeeze"] = x["bb_squeeze_flag"].fillna(False)

    return x


def summarize_signal(df: pd.DataFrame, signal_col: str, label: str):
    horizons = [1, 3, 5, 10, 20]
    rows = []

    sig = df[df[signal_col].fillna(False)].copy()

    for h in horizons:
        col = f"ret_fwd_{h}"
        s = pd.to_numeric(sig[col], errors="coerce").dropna()

        if len(s) == 0:
            rows.append({
                "signal": label,
                "horizon_days": h,
                "obs": 0,
                "avg_ret": np.nan,
                "median_ret": np.nan,
                "win_rate": np.nan,
                "avg_win": np.nan,
                "avg_loss": np.nan,
            })
            continue

        wins = s[s > 0]
        losses = s[s <= 0]

        rows.append({
            "signal": label,
            "horizon_days": h,
            "obs": int(len(s)),
            "avg_ret": round(float(s.mean()), 6),
            "median_ret": round(float(s.median()), 6),
            "win_rate": round(float((s > 0).mean()), 6),
            "avg_win": round(float(wins.mean()), 6) if len(wins) else np.nan,
            "avg_loss": round(float(losses.mean()), 6) if len(losses) else np.nan,
        })

    return rows


def topn_daily_backtest(df: pd.DataFrame, topn: int, hold_days: int, cost_bps: float):
    x = df.dropna(subset=["technical_timing_score", f"ret_fwd_{hold_days}"]).copy()

    rows = []
    for date, g in x.groupby("date"):
        g = g.sort_values(["technical_timing_score", "overheat_penalty"], ascending=[False, True]).head(topn)
        if len(g) == 0:
            continue
        gross = g[f"ret_fwd_{hold_days}"].mean()
        net = gross - (cost_bps / 10000.0)
        rows.append({
            "date": date,
            "strategy": f"TECH_SCORE_TOP{topn}_H{hold_days}",
            "topn": topn,
            "hold_days": hold_days,
            "gross_ret": gross,
            "net_ret": net,
            "name_count": len(g),
        })

    return pd.DataFrame(rows)


def perf_summary(bt: pd.DataFrame):
    if bt.empty:
        return pd.DataFrame()

    rows = []
    for strategy, g in bt.groupby("strategy"):
        r = pd.to_numeric(g["net_ret"], errors="coerce").dropna()
        if len(r) == 0:
            continue

        avg = r.mean()
        med = r.median()
        win = (r > 0).mean()
        vol = r.std()
        sharpe_like = avg / vol if vol and not np.isnan(vol) and vol != 0 else np.nan

        rows.append({
            "strategy": strategy,
            "obs": int(len(r)),
            "avg_net_ret_per_trade": round(float(avg), 6),
            "median_net_ret_per_trade": round(float(med), 6),
            "win_rate": round(float(win), 6),
            "ret_std": round(float(vol), 6) if not np.isnan(vol) else np.nan,
            "sharpe_like": round(float(sharpe_like), 6) if not np.isnan(sharpe_like) else np.nan,
        })

    return pd.DataFrame(rows).sort_values(["avg_net_ret_per_trade", "win_rate"], ascending=[False, False])


def make_report(signal_summary, strategy_summary, out_report, read_first, detail_path, matrix_path, stamp_text):
    def table(df):
        if df is None or df.empty:
            return "_EMPTY_"
        return df.to_markdown(index=False)

    watch = signal_summary[signal_summary["signal"] == "WATCH_POSITIVE"] if not signal_summary.empty else pd.DataFrame()
    pull = signal_summary[signal_summary["signal"] == "PULLBACK_WATCH"] if not signal_summary.empty else pd.DataFrame()
    over = signal_summary[signal_summary["signal"] == "OVERHEAT_AVOID"] if not signal_summary.empty else pd.DataFrame()
    squeeze = signal_summary[signal_summary["signal"] == "BB_SQUEEZE"] if not signal_summary.empty else pd.DataFrame()

    md = f"""# V18.6B Technical Timing Backtest Report

Generated: `{stamp_text}`

## 1. Status

- V18_6B_STATUS: `OK_TECHNICAL_TIMING_BACKTEST_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- DETAIL_CSV: `{detail_path}`
- MATRIX_CSV: `{matrix_path}`

## 2. Signal Forward Return Summary

### WATCH_POSITIVE

{table(watch)}

### PULLBACK_WATCH

{table(pull)}

### OVERHEAT_AVOID

{table(over)}

### BB_SQUEEZE

{table(squeeze)}

## 3. TopN Daily Strategy Summary

{table(strategy_summary)}

## 4. Interpretation Rule

- If `WATCH_POSITIVE` and `PULLBACK_WATCH` have better 5/10/20 day forward return than neutral/overheat groups, V18.6A has useful timing value.
- If `OVERHEAT_AVOID` has weaker 3/5/10/20 day forward return, it can become a chase-risk filter.
- This module is still shadow only and does not change official daily decisions.
"""
    out_report.write_text(md, encoding="utf-8")

    rf = f"""V18.6B TECHNICAL TIMING BACKTEST READ FIRST

STATUS:
OK_TECHNICAL_TIMING_BACKTEST_READY

OFFICIAL_DECISION_IMPACT:
NONE

READ:
{out_report}

DETAIL:
{detail_path}

MATRIX:
{matrix_path}
"""
    read_first.write_text(rf, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--lookback-days", type=int, default=756)
    parser.add_argument("--topn-list", default="5,10,15")
    parser.add_argument("--hold-days-list", default="3,5,10,20")
    parser.add_argument("--cost-bps", type=float, default=20.0)
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = root / "outputs" / "v18" / "technical_timing_backtest"
    out_dir.mkdir(parents=True, exist_ok=True)

    s = stamp()

    detail_csv = out_dir / "V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_DETAIL.csv"
    signal_csv = out_dir / "V18_6B_CURRENT_TECHNICAL_SIGNAL_FORWARD_SUMMARY.csv"
    matrix_csv = out_dir / "V18_6B_CURRENT_TECHNICAL_TOPN_BACKTEST_MATRIX.csv"
    strategy_csv = out_dir / "V18_6B_CURRENT_TECHNICAL_TOPN_STRATEGY_SUMMARY.csv"
    report_md = out_dir / "V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_REPORT.md"
    global_md = out_dir / "V18_CURRENT_TECHNICAL_TIMING_BACKTEST.md"
    read_first = out_dir / "V18_6B_READ_FIRST.txt"

    yf = get_yfinance()
    tickers = load_universe(root)

    all_hist = []
    fails = []

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] BACKTEST_DATA: {ticker}")
        try:
            h = download_ohlcv(yf, ticker, args.lookback_days)
            if h.empty or len(h) < 180:
                fails.append({"ticker": ticker, "reason": "NO_OR_INSUFFICIENT_HISTORY"})
                continue
            all_hist.append(h)
        except Exception as e:
            fails.append({"ticker": ticker, "reason": f"{type(e).__name__}: {e}"})

    if not all_hist:
        raise RuntimeError("No history downloaded.")

    raw = pd.concat(all_hist, ignore_index=True)
    features = make_signals(add_indicators(raw))
    features = features.dropna(subset=["technical_timing_score"])

    features.to_csv(detail_csv, index=False, encoding="utf-8-sig")

    signal_rows = []
    for col, label in [
        ("signal_watch_positive", "WATCH_POSITIVE"),
        ("signal_pullback_watch", "PULLBACK_WATCH"),
        ("signal_overheat_avoid", "OVERHEAT_AVOID"),
        ("signal_bb_squeeze", "BB_SQUEEZE"),
    ]:
        signal_rows.extend(summarize_signal(features, col, label))

    signal_summary = pd.DataFrame(signal_rows)
    signal_summary.to_csv(signal_csv, index=False, encoding="utf-8-sig")

    topn_list = [int(x.strip()) for x in args.topn_list.split(",") if x.strip()]
    hold_days_list = [int(x.strip()) for x in args.hold_days_list.split(",") if x.strip()]

    matrices = []
    for topn in topn_list:
        for hold_days in hold_days_list:
            matrices.append(topn_daily_backtest(features, topn, hold_days, args.cost_bps))

    matrix = pd.concat(matrices, ignore_index=True) if matrices else pd.DataFrame()
    matrix.to_csv(matrix_csv, index=False, encoding="utf-8-sig")

    strategy_summary = perf_summary(matrix)
    strategy_summary.to_csv(strategy_csv, index=False, encoding="utf-8-sig")

    make_report(signal_summary, strategy_summary, report_md, read_first, detail_csv, matrix_csv, s)
    global_md.write_text(report_md.read_text(encoding="utf-8"), encoding="utf-8")

    print("")
    print("=== V18.6B TECHNICAL TIMING BACKTEST READY ===")
    print(f"RAW_HISTORY_ROWS: {len(raw)}")
    print(f"FEATURE_ROWS: {len(features)}")
    print(f"FAIL_COUNT: {len(fails)}")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"SIGNAL_SUMMARY: {signal_csv}")
    print(f"STRATEGY_SUMMARY: {strategy_csv}")
    print(f"REPORT: {report_md}")
    print(f"READ_FIRST: {read_first}")


if __name__ == "__main__":
    main()
