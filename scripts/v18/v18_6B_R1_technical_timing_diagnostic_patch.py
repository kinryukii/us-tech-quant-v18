import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, encoding="utf-8-sig")


def to_bool(s):
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def ensure_bool_cols(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = to_bool(df[c])
        else:
            df[c] = False
    return df


def add_overheat_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()

    bool_cols = [
        "bb_near_upper",
        "bb_above_upper",
        "bb_upper_zone",
        "rsi_overheat",
        "rsi_extreme_overheat",
        "kdj_overheat",
        "kdj_extreme_overheat",
        "kdj_high_dead_cross",
        "signal_watch_positive",
        "signal_pullback_watch",
        "signal_overheat_avoid",
        "signal_bb_squeeze",
    ]
    x = ensure_bool_cols(x, bool_cols)

    x["rsi_14"] = pd.to_numeric(x.get("rsi_14", np.nan), errors="coerce")
    x["volume_ratio_5_20"] = pd.to_numeric(x.get("volume_ratio_5_20", np.nan), errors="coerce")
    x["bb_percent_b"] = pd.to_numeric(x.get("bb_percent_b", np.nan), errors="coerce")
    x["technical_timing_score"] = pd.to_numeric(x.get("technical_timing_score", np.nan), errors="coerce")
    x["overheat_penalty"] = pd.to_numeric(x.get("overheat_penalty", np.nan), errors="coerce")

    # 强势突破型过热：价格靠近/突破上轨，RSI 强但未极端失控，放量，且没有高位死叉。
    x["signal_overheat_breakout_continuation"] = (
        (x["bb_near_upper"] | x["bb_above_upper"] | (x["bb_percent_b"] >= 0.90))
        & (x["rsi_14"] >= 60)
        & (x["rsi_14"] <= 78)
        & (x["volume_ratio_5_20"] >= 1.15)
        & (~x["kdj_high_dead_cross"])
    )

    # 衰竭追高型过热：RSI 极端热，KDJ 极端热或高位死叉，且量能没有有效确认。
    x["signal_overheat_exhaustion_risk"] = (
        (x["rsi_14"] >= 75)
        & (x["kdj_extreme_overheat"] | x["kdj_high_dead_cross"])
        & ((x["volume_ratio_5_20"] < 1.0) | x["volume_ratio_5_20"].isna())
    )

    # 未拆清的旧过热：旧 overheat 中既不是突破延续也不是衰竭风险。
    x["signal_overheat_unclassified"] = (
        x["signal_overheat_avoid"]
        & (~x["signal_overheat_breakout_continuation"])
        & (~x["signal_overheat_exhaustion_risk"])
    )

    return x


def add_benchmark_excess(df: pd.DataFrame, benchmarks=("QQQ", "SPY", "SMH"), horizons=(1, 3, 5, 10, 20)):
    x = df.copy()

    for h in horizons:
        ret_col = f"ret_fwd_{h}"
        x[ret_col] = pd.to_numeric(x[ret_col], errors="coerce")

    for bench in benchmarks:
        b = x[x["ticker"].astype(str).str.upper() == bench].copy()
        if b.empty:
            for h in horizons:
                x[f"bench_{bench}_ret_fwd_{h}"] = np.nan
                x[f"excess_vs_{bench}_{h}"] = np.nan
            continue

        b = b[["date"] + [f"ret_fwd_{h}" for h in horizons]].drop_duplicates("date")
        rename = {f"ret_fwd_{h}": f"bench_{bench}_ret_fwd_{h}" for h in horizons}
        b = b.rename(columns=rename)

        x = x.merge(b, on="date", how="left")

        for h in horizons:
            x[f"excess_vs_{bench}_{h}"] = x[f"ret_fwd_{h}"] - x[f"bench_{bench}_ret_fwd_{h}"]

    return x


def summarize_signal(df, signal_col, label, horizons=(1, 3, 5, 10, 20), benchmarks=("QQQ", "SPY", "SMH")):
    rows = []
    sig = df[df[signal_col].fillna(False)].copy()

    for h in horizons:
        ret_col = f"ret_fwd_{h}"
        r = pd.to_numeric(sig[ret_col], errors="coerce").dropna()

        base = {
            "signal": label,
            "horizon_days": h,
            "obs": int(len(r)),
            "avg_ret": round(float(r.mean()), 6) if len(r) else np.nan,
            "median_ret": round(float(r.median()), 6) if len(r) else np.nan,
            "win_rate": round(float((r > 0).mean()), 6) if len(r) else np.nan,
        }

        for bench in benchmarks:
            ex_col = f"excess_vs_{bench}_{h}"
            ex = pd.to_numeric(sig[ex_col], errors="coerce").dropna()
            base[f"avg_excess_vs_{bench}"] = round(float(ex.mean()), 6) if len(ex) else np.nan
            base[f"excess_win_rate_vs_{bench}"] = round(float((ex > 0).mean()), 6) if len(ex) else np.nan

        rows.append(base)

    return rows


def topn_excess_strategy(df, topn_list=(5, 10, 15), hold_days_list=(3, 5, 10, 20), cost_bps=20.0, benchmarks=("QQQ", "SPY", "SMH")):
    rows = []

    for topn in topn_list:
        for h in hold_days_list:
            ret_col = f"ret_fwd_{h}"
            needed = ["date", "ticker", "technical_timing_score", "overheat_penalty", ret_col]
            g0 = df.dropna(subset=[ret_col, "technical_timing_score"]).copy()

            daily_rows = []
            for date, g in g0.groupby("date"):
                pick = g.sort_values(
                    ["technical_timing_score", "overheat_penalty"],
                    ascending=[False, True]
                ).head(topn)

                if pick.empty:
                    continue

                net = pick[ret_col].mean() - cost_bps / 10000.0
                one = {
                    "date": date,
                    "strategy": f"TECH_SCORE_TOP{topn}_H{h}",
                    "topn": topn,
                    "hold_days": h,
                    "net_ret": net,
                    "name_count": len(pick),
                }

                for bench in benchmarks:
                    bench_col = f"bench_{bench}_ret_fwd_{h}"
                    if bench_col in pick.columns:
                        bench_val = pd.to_numeric(pick[bench_col], errors="coerce").dropna()
                        one[f"bench_{bench}_ret"] = bench_val.iloc[0] if len(bench_val) else np.nan
                        one[f"excess_vs_{bench}"] = net - one[f"bench_{bench}_ret"]
                    else:
                        one[f"bench_{bench}_ret"] = np.nan
                        one[f"excess_vs_{bench}"] = np.nan

                daily_rows.append(one)

            daily = pd.DataFrame(daily_rows)
            if daily.empty:
                continue

            r = pd.to_numeric(daily["net_ret"], errors="coerce").dropna()

            out = {
                "strategy": f"TECH_SCORE_TOP{topn}_H{h}",
                "obs": int(len(r)),
                "avg_net_ret": round(float(r.mean()), 6),
                "median_net_ret": round(float(r.median()), 6),
                "win_rate": round(float((r > 0).mean()), 6),
                "ret_std": round(float(r.std()), 6) if len(r) > 1 else np.nan,
            }

            for bench in benchmarks:
                ex = pd.to_numeric(daily[f"excess_vs_{bench}"], errors="coerce").dropna()
                out[f"avg_excess_vs_{bench}"] = round(float(ex.mean()), 6) if len(ex) else np.nan
                out[f"excess_win_rate_vs_{bench}"] = round(float((ex > 0).mean()), 6) if len(ex) else np.nan

            rows.append(out)

    return pd.DataFrame(rows)


def make_report(signal_summary, strategy_summary, out_report, read_first, detail_out, signal_out, strategy_out):
    def table(df):
        if df is None or df.empty:
            return "_EMPTY_"
        return df.to_markdown(index=False)

    key_signals = [
        "WATCH_POSITIVE",
        "PULLBACK_WATCH",
        "BB_SQUEEZE",
        "OVERHEAT_BREAKOUT_CONTINUATION",
        "OVERHEAT_EXHAUSTION_RISK",
        "OVERHEAT_UNCLASSIFIED",
    ]

    parts = []
    for sig in key_signals:
        part = signal_summary[signal_summary["signal"] == sig]
        parts.append(f"### {sig}\n\n{table(part)}\n")

    md = f"""# V18.6B-R1 Technical Timing Diagnostic Patch

## 1. Status

- V18_6B_R1_STATUS: `OK_TECHNICAL_TIMING_DIAGNOSTIC_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- MAIN_PURPOSE: `OVERHEAT_DECOMPOSITION_AND_BENCHMARK_EXCESS`

## 2. Signal Forward Return + Benchmark Excess

{chr(10).join(parts)}

## 3. TopN Strategy Benchmark Excess

{table(strategy_summary)}

## 4. Interpretation

- `OVERHEAT_BREAKOUT_CONTINUATION` means overheat with volume/price confirmation. It may be momentum continuation rather than a sell/avoid signal.
- `OVERHEAT_EXHAUSTION_RISK` means extreme RSI/KDJ heat with weak volume confirmation. This is the real chase-risk candidate.
- `WATCH_POSITIVE` and `PULLBACK_WATCH` remain timing-watch signals, not official buy signals.
- This patch is diagnostic only and does not change official daily decisions.

## 5. Outputs

- DETAIL: `{detail_out}`
- SIGNAL_SUMMARY: `{signal_out}`
- STRATEGY_SUMMARY: `{strategy_out}`
"""
    out_report.write_text(md, encoding="utf-8")

    rf = f"""V18.6B-R1 TECHNICAL TIMING DIAGNOSTIC READ FIRST

STATUS:
OK_TECHNICAL_TIMING_DIAGNOSTIC_READY

OFFICIAL_DECISION_IMPACT:
NONE

PURPOSE:
Split old OVERHEAT_AVOID into BREAKOUT_CONTINUATION vs EXHAUSTION_RISK and add benchmark excess vs QQQ/SPY/SMH.

READ:
{out_report}

SIGNAL_SUMMARY:
{signal_out}

STRATEGY_SUMMARY:
{strategy_out}
"""
    read_first.write_text(rf, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--topn-list", default="5,10,15")
    parser.add_argument("--hold-days-list", default="3,5,10,20")
    parser.add_argument("--cost-bps", type=float, default=20.0)
    args = parser.parse_args()

    root = Path(args.root)
    src = root / "outputs" / "v18" / "technical_timing_backtest" / "V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_DETAIL.csv"
    out_dir = root / "outputs" / "v18" / "technical_timing_backtest"
    out_dir.mkdir(parents=True, exist_ok=True)

    detail_out = out_dir / "V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv"
    signal_out = out_dir / "V18_6B_R1_CURRENT_SIGNAL_EXCESS_SUMMARY.csv"
    strategy_out = out_dir / "V18_6B_R1_CURRENT_TOPN_EXCESS_STRATEGY_SUMMARY.csv"
    report = out_dir / "V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_REPORT.md"
    global_report = out_dir / "V18_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC.md"
    read_first = out_dir / "V18_6B_R1_READ_FIRST.txt"

    df = read_csv(src)
    df = add_overheat_decomposition(df)
    df = add_benchmark_excess(df)

    df.to_csv(detail_out, index=False, encoding="utf-8-sig")

    signal_defs = [
        ("signal_watch_positive", "WATCH_POSITIVE"),
        ("signal_pullback_watch", "PULLBACK_WATCH"),
        ("signal_bb_squeeze", "BB_SQUEEZE"),
        ("signal_overheat_breakout_continuation", "OVERHEAT_BREAKOUT_CONTINUATION"),
        ("signal_overheat_exhaustion_risk", "OVERHEAT_EXHAUSTION_RISK"),
        ("signal_overheat_unclassified", "OVERHEAT_UNCLASSIFIED"),
    ]

    rows = []
    for col, label in signal_defs:
        rows.extend(summarize_signal(df, col, label))

    signal_summary = pd.DataFrame(rows)
    signal_summary.to_csv(signal_out, index=False, encoding="utf-8-sig")

    topn_list = [int(x.strip()) for x in args.topn_list.split(",") if x.strip()]
    hold_days_list = [int(x.strip()) for x in args.hold_days_list.split(",") if x.strip()]

    strategy_summary = topn_excess_strategy(
        df,
        topn_list=topn_list,
        hold_days_list=hold_days_list,
        cost_bps=args.cost_bps,
    )
    strategy_summary.to_csv(strategy_out, index=False, encoding="utf-8-sig")

    make_report(signal_summary, strategy_summary, report, read_first, detail_out, signal_out, strategy_out)
    global_report.write_text(report.read_text(encoding="utf-8"), encoding="utf-8")

    print("")
    print("=== V18.6B-R1 TECHNICAL TIMING DIAGNOSTIC READY ===")
    print(f"INPUT_DETAIL: {src}")
    print(f"ROWS: {len(df)}")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"SIGNAL_SUMMARY: {signal_out}")
    print(f"STRATEGY_SUMMARY: {strategy_out}")
    print(f"REPORT: {report}")
    print(f"READ_FIRST: {read_first}")


if __name__ == "__main__":
    main()
