import argparse
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except Exception as exc:
    print("YFINANCE_IMPORT_FAIL:", repr(exc))
    print("FIX: pip install yfinance")
    sys.exit(2)


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "v18" / "factor_backtest"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_safe(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def detect_ticker_col(df: pd.DataFrame) -> str:
    preferred = ["ticker", "symbol", "Ticker", "Symbol", "code", "Code"]
    for col in preferred:
        if col in df.columns:
            return col
    for col in df.columns:
        name = str(col).lower()
        if "ticker" in name or "symbol" in name:
            return col
    return df.columns[0]


def clean_ticker(x):
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    if s in ("", "NAN", "NONE", "NULL"):
        return None
    s = s.replace(".", "-")
    s = s.split()[0]
    return s


def load_universe():
    candidates = [
        ROOT / "outputs" / "v18" / "factor_pack" / "V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        ROOT / "state" / "v18" / "V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv",
    ]

    for path in candidates:
        if not path.exists():
            continue

        df = read_csv_safe(path)
        if df.empty:
            continue

        col = detect_ticker_col(df)
        tickers = [clean_ticker(x) for x in df[col].tolist()]
        tickers = sorted({t for t in tickers if t and 1 <= len(t) <= 8 and not t.isdigit()})

        if len(tickers) >= 5:
            return tickers, path

    raise FileNotFoundError("No usable universe file found for V18.4H backtest.")


def normalize_yf_panel(raw: pd.DataFrame, tickers):
    fields = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    data = {f: {} for f in fields}

    if raw is None or raw.empty:
        return {f: pd.DataFrame() for f in fields}

    for t in tickers:
        sub = None

        if isinstance(raw.columns, pd.MultiIndex):
            level0 = list(raw.columns.get_level_values(0).unique())
            level1 = list(raw.columns.get_level_values(1).unique())

            if t in level0:
                sub = raw[t].copy()
            elif t in level1:
                sub = raw.xs(t, axis=1, level=1).copy()
        else:
            if len(tickers) == 1:
                sub = raw.copy()

        if sub is None or sub.empty:
            continue

        for f in fields:
            if f in sub.columns:
                data[f][t] = pd.to_numeric(sub[f], errors="coerce")

    panel = {}
    for f in fields:
        panel[f] = pd.DataFrame(data[f]).sort_index()
        if not panel[f].empty:
            panel[f] = panel[f].loc[~panel[f].index.duplicated(keep="last")]

    return panel


def download_panel(tickers, start_date, end_date):
    raw = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    return normalize_yf_panel(raw, tickers)


def pct_rank(df: pd.DataFrame) -> pd.DataFrame:
    return df.rank(axis=1, pct=True, ascending=True)


def compute_factors(close: pd.DataFrame, volume: pd.DataFrame):
    ret_5 = close.pct_change(5)
    ret_20 = close.pct_change(20)
    ret_60 = close.pct_change(60)
    ret_120 = close.pct_change(120)

    ma_120 = close.rolling(120, min_periods=80).mean()
    vol_20 = volume.rolling(20, min_periods=10).mean()

    vol_abnormal = volume / vol_20 - 1.0
    dist_ma120 = close / ma_120 - 1.0

    factors = {}

    factors["F006_SHORT_REV_5D"] = -ret_5
    factors["F007_PULLBACK_IN_UPTREND"] = (-ret_5) + 0.35 * ret_60 + 0.15 * dist_ma120
    factors["F008_VOLUME_ABNORMAL_5_20"] = vol_abnormal
    factors["F009_VOLUME_PRICE_CONFIRM"] = ret_20 * (1.0 + vol_abnormal.clip(lower=-0.8, upper=3.0))
    factors["F011_TS_MOMENTUM_60_120"] = 0.50 * ret_60 + 0.50 * ret_120

    ranks = [
        pct_rank(factors["F006_SHORT_REV_5D"]),
        pct_rank(factors["F007_PULLBACK_IN_UPTREND"]),
        pct_rank(factors["F008_VOLUME_ABNORMAL_5_20"]),
        pct_rank(factors["F009_VOLUME_PRICE_CONFIRM"]),
        pct_rank(factors["F011_TS_MOMENTUM_60_120"]),
    ]
    factors["F010_XSEC_COMPOSITE_RANK"] = sum(ranks) / len(ranks)

    return factors


def max_drawdown(ret: pd.Series) -> float:
    ret = ret.dropna()
    if ret.empty:
        return np.nan
    equity = (1.0 + ret).cumprod()
    dd = equity / equity.cummax() - 1.0
    return float(dd.min())


def calc_metrics(ret: pd.Series, benchmark_ret=None):
    ret = ret.replace([np.inf, -np.inf], np.nan).dropna()

    if ret.empty:
        return {
            "daily_count": 0,
            "total_return": np.nan,
            "cagr": np.nan,
            "ann_vol": np.nan,
            "sharpe_0rf": np.nan,
            "max_drawdown": np.nan,
            "hit_rate": np.nan,
            "bench_cagr": np.nan,
            "excess_cagr_vs_bench": np.nan,
            "corr_vs_bench": np.nan,
        }

    equity = (1.0 + ret).cumprod()
    years = max(len(ret) / 252.0, 1e-9)

    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0)
    ann_vol = float(ret.std(ddof=0) * math.sqrt(252.0))
    sharpe = float(ret.mean() / ret.std(ddof=0) * math.sqrt(252.0)) if ret.std(ddof=0) > 0 else np.nan
    mdd = max_drawdown(ret)
    hit_rate = float((ret > 0).mean())

    bench_cagr = np.nan
    excess = np.nan
    corr = np.nan

    if benchmark_ret is not None:
        b = benchmark_ret.reindex(ret.index).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        if len(b) > 2:
            beq = (1.0 + b).cumprod()
            byears = max(len(b) / 252.0, 1e-9)
            bench_cagr = float(beq.iloc[-1] ** (1.0 / byears) - 1.0)
            excess = cagr - bench_cagr
            corr = float(ret.corr(b))

    return {
        "daily_count": int(len(ret)),
        "total_return": total_return,
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe_0rf": sharpe,
        "max_drawdown": mdd,
        "hit_rate": hit_rate,
        "bench_cagr": bench_cagr,
        "excess_cagr_vs_bench": excess,
        "corr_vs_bench": corr,
    }


def run_backtest(factor, daily_returns, strategy_type, top_n, bottom_n, hold_days, cost_bps, min_names):
    dates = daily_returns.index.intersection(factor.index)
    factor = factor.reindex(dates)
    daily_returns = daily_returns.reindex(dates)

    port_ret = pd.Series(0.0, index=dates, name=strategy_type)
    records = []

    valid_dates = factor.notna().sum(axis=1)
    valid_dates = valid_dates[valid_dates >= min_names].index

    if len(valid_dates) == 0:
        return port_ret, pd.DataFrame(), {
            "avg_turnover": np.nan,
            "rebalance_count": 0,
            "avg_holding_names": np.nan,
        }

    start_pos = dates.get_indexer([valid_dates[0]])[0]
    rebalance_positions = set(range(start_pos, len(dates) - 1, hold_days))

    current_weights = pd.Series(dtype=float)
    previous_weights = pd.Series(dtype=float)

    pending_cost = 0.0
    turnovers = []
    holding_counts = []
    rebalance_count = 0

    for i in range(0, len(dates) - 1):
        dt = dates[i]
        next_dt = dates[i + 1]

        if i in rebalance_positions:
            scores = factor.loc[dt].replace([np.inf, -np.inf], np.nan).dropna()

            if len(scores) >= min_names:
                if strategy_type == "LONG_ONLY_TOPN":
                    selected = scores.nlargest(min(top_n, len(scores)))
                    current_weights = pd.Series(1.0 / len(selected), index=selected.index)

                    for ticker, value in selected.items():
                        records.append({
                            "rebalance_date": dt.date().isoformat(),
                            "strategy_type": strategy_type,
                            "side": "LONG",
                            "ticker": ticker,
                            "weight": float(current_weights[ticker]),
                            "factor_value": float(value),
                        })

                elif strategy_type == "LONG_SHORT_SPREAD":
                    n_long = min(top_n, len(scores) // 2)
                    n_short = min(bottom_n, len(scores) - n_long)

                    long_sel = scores.nlargest(n_long)
                    short_sel = scores.nsmallest(n_short)

                    long_w = pd.Series(1.0 / len(long_sel), index=long_sel.index)
                    short_w = pd.Series(-1.0 / len(short_sel), index=short_sel.index)
                    current_weights = pd.concat([long_w, short_w]).groupby(level=0).sum()

                    for ticker, value in long_sel.items():
                        records.append({
                            "rebalance_date": dt.date().isoformat(),
                            "strategy_type": strategy_type,
                            "side": "LONG",
                            "ticker": ticker,
                            "weight": float(long_w[ticker]),
                            "factor_value": float(value),
                        })

                    for ticker, value in short_sel.items():
                        records.append({
                            "rebalance_date": dt.date().isoformat(),
                            "strategy_type": strategy_type,
                            "side": "SHORT",
                            "ticker": ticker,
                            "weight": float(short_w[ticker]),
                            "factor_value": float(value),
                        })

                all_names = sorted(set(previous_weights.index).union(set(current_weights.index)))
                prev = previous_weights.reindex(all_names).fillna(0.0)
                curr = current_weights.reindex(all_names).fillna(0.0)

                turnover = float((curr - prev).abs().sum() / 2.0)
                pending_cost = turnover * cost_bps / 10000.0

                turnovers.append(turnover)
                holding_counts.append(int((current_weights != 0).sum()))
                previous_weights = current_weights.copy()
                rebalance_count += 1

        if not current_weights.empty:
            r = daily_returns.loc[next_dt].reindex(current_weights.index)
            r = r.replace([np.inf, -np.inf], np.nan).dropna()

            if not r.empty:
                w = current_weights.reindex(r.index).dropna()

                if strategy_type == "LONG_ONLY_TOPN":
                    s = w.abs().sum()
                    if s > 0:
                        w = w / s

                daily = float((w * r).sum()) - pending_cost
                port_ret.loc[next_dt] = daily
                pending_cost = 0.0

    aux = {
        "avg_turnover": float(np.nanmean(turnovers)) if turnovers else np.nan,
        "rebalance_count": int(rebalance_count),
        "avg_holding_names": float(np.nanmean(holding_counts)) if holding_counts else np.nan,
    }

    return port_ret, pd.DataFrame(records), aux


def fmt_pct(x):
    if pd.isna(x):
        return "NA"
    return f"{x * 100:.2f}%"


def write_report(path, universe_source, raw_count, available_count, missing_count, start_date, end_date, args, summary):
    lines = []

    lines.append("# V18.4H 当前量化因子滚动回测报告")
    lines.append("")
    lines.append("## 1. 结论")
    lines.append("")
    lines.append("本模块用于评估当前 WorldQuant-style 因子 F006-F011 的历史表现。")
    lines.append("它只提供历史证据层，不直接改变 official daily decision。")
    lines.append("")
    lines.append("## 2. 回测配置")
    lines.append("")
    lines.append(f"- UNIVERSE_SOURCE: `{universe_source}`")
    lines.append(f"- RAW_UNIVERSE_COUNT: `{raw_count}`")
    lines.append(f"- AVAILABLE_TICKER_COUNT: `{available_count}`")
    lines.append(f"- MISSING_TICKER_COUNT: `{missing_count}`")
    lines.append(f"- START_DATE: `{start_date}`")
    lines.append(f"- END_DATE: `{end_date}`")
    lines.append(f"- HOLD_DAYS: `{args.hold_days}`")
    lines.append(f"- TOP_N: `{args.top_n}`")
    lines.append(f"- BOTTOM_N: `{args.bottom_n}`")
    lines.append(f"- COST_BPS_ONE_WAY: `{args.cost_bps}`")
    lines.append(f"- BENCHMARK: `QQQ`")
    lines.append("")
    lines.append("## 3. 因子说明")
    lines.append("")
    lines.append("| factor | meaning |")
    lines.append("|---|---|")
    lines.append("| F006_SHORT_REV_5D | 5日短期反转 |")
    lines.append("| F007_PULLBACK_IN_UPTREND | 中期上行趋势中的短线回撤 |")
    lines.append("| F008_VOLUME_ABNORMAL_5_20 | 成交量相对20日均量异常 |")
    lines.append("| F009_VOLUME_PRICE_CONFIRM | 20日价格强度 × 成交量确认 |")
    lines.append("| F010_XSEC_COMPOSITE_RANK | 综合横截面排名 |")
    lines.append("| F011_TS_MOMENTUM_60_120 | 60日和120日时间序列动量 |")
    lines.append("")

    long_only = summary[summary["strategy_type"] == "LONG_ONLY_TOPN"].copy()
    if not long_only.empty:
        long_only = long_only.sort_values(["sharpe_0rf", "excess_cagr_vs_bench"], ascending=False)

        lines.append("## 4. LONG_ONLY_TOPN 排名")
        lines.append("")
        lines.append("| rank | factor | CAGR | Sharpe | Max DD | Excess CAGR vs QQQ | Avg Turnover |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|")

        for idx, (_, row) in enumerate(long_only.iterrows(), start=1):
            lines.append(
                f"| {idx} | {row['factor']} | {fmt_pct(row['cagr'])} | "
                f"{row['sharpe_0rf']:.2f} | {fmt_pct(row['max_drawdown'])} | "
                f"{fmt_pct(row['excess_cagr_vs_bench'])} | {fmt_pct(row['avg_turnover'])} |"
            )

        lines.append("")

    spread = summary[summary["strategy_type"] == "LONG_SHORT_SPREAD"].copy()
    if not spread.empty:
        spread = spread.sort_values(["sharpe_0rf", "cagr"], ascending=False)

        lines.append("## 5. LONG_SHORT_SPREAD 因子区分度")
        lines.append("")
        lines.append("| rank | factor | Spread CAGR | Spread Sharpe | Spread Max DD |")
        lines.append("|---:|---|---:|---:|---:|")

        for idx, (_, row) in enumerate(spread.iterrows(), start=1):
            lines.append(
                f"| {idx} | {row['factor']} | {fmt_pct(row['cagr'])} | "
                f"{row['sharpe_0rf']:.2f} | {fmt_pct(row['max_drawdown'])} |"
            )

        lines.append("")

    lines.append("## 6. 输出文件")
    lines.append("")
    lines.append("- `V18_4H_CURRENT_FACTOR_BACKTEST_SUMMARY.csv`")
    lines.append("- `V18_4H_CURRENT_FACTOR_BACKTEST_DAILY_RETURNS.csv`")
    lines.append("- `V18_4H_CURRENT_FACTOR_BACKTEST_HOLDINGS.csv`")
    lines.append("- `V18_4H_CURRENT_FACTOR_LATEST_SCORES.csv`")
    lines.append("")
    lines.append("## 7. 解释边界")
    lines.append("")
    lines.append("LONG_ONLY_TOPN 更接近实际交易。")
    lines.append("LONG_SHORT_SPREAD 主要用于判断因子排序能力，不代表当前账户要做空。")
    lines.append("本模块暂时不纳入事件门、预算锁、Rakuten 一股最小单位、行为纪律。")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback-days", type=int, default=756)
    parser.add_argument("--start-date", type=str, default="")
    parser.add_argument("--end-date", type=str, default="")
    parser.add_argument("--hold-days", type=int, default=5)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--bottom-n", type=int, default=10)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--min-names", type=int, default=20)

    args = parser.parse_args()

    end_date = args.end_date.strip() or datetime.today().date().isoformat()

    if args.start_date.strip():
        start_date = args.start_date.strip()
    else:
        start_date = (datetime.today().date() - timedelta(days=args.lookback_days)).isoformat()

    universe, universe_source = load_universe()
    raw_count = len(universe)

    tickers_to_download = sorted(set(universe + ["QQQ"]))

    print("")
    print("=== V18.4H DOWNLOAD PRICE DATA ===")
    print(f"UNIVERSE_SOURCE: {universe_source}")
    print(f"RAW_UNIVERSE_COUNT: {raw_count}")
    print(f"START_DATE: {start_date}")
    print(f"END_DATE: {end_date}")

    panel = download_panel(tickers_to_download, start_date, end_date)

    adj_close = panel.get("Adj Close", pd.DataFrame())
    close_raw = panel.get("Close", pd.DataFrame())
    volume_raw = panel.get("Volume", pd.DataFrame())

    close_all = adj_close if not adj_close.empty else close_raw

    available = [
        t for t in universe
        if t in close_all.columns and close_all[t].notna().sum() >= 160
    ]

    missing = sorted(set(universe) - set(available))

    if len(available) < args.min_names:
        raise RuntimeError(
            f"Not enough tickers with usable historical data. "
            f"available={len(available)}, min_names={args.min_names}"
        )

    close = close_all[available].copy()
    volume = volume_raw.reindex(close.index)[available].copy()

    daily_returns = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    qqq_ret = None
    if "QQQ" in close_all.columns:
        qqq_ret = close_all["QQQ"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    factors = compute_factors(close, volume)

    summary_rows = []
    all_daily = pd.DataFrame(index=daily_returns.index)
    holding_frames = []

    for factor_name, factor_df in factors.items():
        for strategy_type in ("LONG_ONLY_TOPN", "LONG_SHORT_SPREAD"):
            ret, holdings, aux = run_backtest(
                factor=factor_df,
                daily_returns=daily_returns,
                strategy_type=strategy_type,
                top_n=args.top_n,
                bottom_n=args.bottom_n,
                hold_days=args.hold_days,
                cost_bps=args.cost_bps,
                min_names=args.min_names,
            )

            all_daily[f"{factor_name}__{strategy_type}"] = ret

            if not holdings.empty:
                holdings.insert(0, "factor", factor_name)
                holding_frames.append(holdings)

            metrics = calc_metrics(ret, qqq_ret)

            row = {
                "factor": factor_name,
                "strategy_type": strategy_type,
                "start_date": start_date,
                "end_date": end_date,
                "hold_days": args.hold_days,
                "top_n": args.top_n,
                "bottom_n": args.bottom_n,
                "cost_bps": args.cost_bps,
                "available_ticker_count": len(available),
                "missing_ticker_count": len(missing),
                **metrics,
                **aux,
            }
            summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)

    summary_path = OUT_DIR / "V18_4H_CURRENT_FACTOR_BACKTEST_SUMMARY.csv"
    daily_path = OUT_DIR / "V18_4H_CURRENT_FACTOR_BACKTEST_DAILY_RETURNS.csv"
    holdings_path = OUT_DIR / "V18_4H_CURRENT_FACTOR_BACKTEST_HOLDINGS.csv"
    latest_path = OUT_DIR / "V18_4H_CURRENT_FACTOR_LATEST_SCORES.csv"
    report_path = OUT_DIR / "V18_4H_CURRENT_FACTOR_BACKTEST_REPORT.md"

    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    all_daily.to_csv(daily_path, index=True, encoding="utf-8-sig")

    if holding_frames:
        pd.concat(holding_frames, ignore_index=True).to_csv(holdings_path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame().to_csv(holdings_path, index=False, encoding="utf-8-sig")

    latest_date = close.index.max()
    latest_scores = pd.DataFrame({"ticker": available})
    latest_scores.insert(0, "score_date", latest_date.date().isoformat())

    for factor_name, factor_df in factors.items():
        latest_scores[factor_name] = factor_df.loc[latest_date].reindex(available).values
        latest_scores[f"{factor_name}_rank_pct"] = pct_rank(factor_df).loc[latest_date].reindex(available).values

    latest_scores.to_csv(latest_path, index=False, encoding="utf-8-sig")

    write_report(
        path=report_path,
        universe_source=universe_source,
        raw_count=raw_count,
        available_count=len(available),
        missing_count=len(missing),
        start_date=start_date,
        end_date=end_date,
        args=args,
        summary=summary,
    )

    print("")
    print("=== V18.4H FACTOR ROLLING BACKTEST READY ===")
    print(f"AVAILABLE_TICKER_COUNT: {len(available)}")
    print(f"MISSING_TICKER_COUNT: {len(missing)}")
    print(f"SUMMARY: {summary_path}")
    print(f"DAILY_RETURNS: {daily_path}")
    print(f"HOLDINGS: {holdings_path}")
    print(f"LATEST_SCORES: {latest_path}")
    print(f"REPORT: {report_path}")

    print("")
    print("=== LONG_ONLY_TOPN RANKING ===")
    long_only = summary[summary["strategy_type"] == "LONG_ONLY_TOPN"].copy()
    long_only = long_only.sort_values(["sharpe_0rf", "excess_cagr_vs_bench"], ascending=False)

    for _, row in long_only.iterrows():
        print(
            f"{row['factor']}: "
            f"CAGR={row['cagr']:.4f}, "
            f"SHARPE={row['sharpe_0rf']:.3f}, "
            f"MAX_DD={row['max_drawdown']:.4f}, "
            f"EXCESS_CAGR_VS_QQQ={row['excess_cagr_vs_bench']:.4f}"
        )


if __name__ == "__main__":
    main()