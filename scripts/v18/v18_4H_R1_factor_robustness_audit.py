import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import v18_4H_factor_rolling_backtest as base


ROOT = base.ROOT
OUT_DIR = ROOT / "outputs" / "v18" / "factor_backtest"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_int_list(text, default):
    if text is None or str(text).strip() == "":
        return default
    return [int(x.strip()) for x in str(text).split(",") if x.strip()]


def parse_float_list(text, default):
    if text is None or str(text).strip() == "":
        return default
    return [float(x.strip()) for x in str(text).split(",") if x.strip()]


def fmt_pct(x):
    if pd.isna(x):
        return "NA"
    return f"{x * 100:.2f}%"


def prepare_data(lookback_days, end_date, min_names):
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_dt = datetime.today().date()

    start_dt = end_dt - timedelta(days=int(lookback_days))

    start_date = start_dt.isoformat()
    end_date_str = end_dt.isoformat()

    universe, universe_source = base.load_universe()
    raw_count = len(universe)

    tickers_to_download = sorted(set(universe + ["QQQ"]))

    print("")
    print("=== V18.4H-R1 DOWNLOAD PRICE DATA ===")
    print(f"LOOKBACK_DAYS: {lookback_days}")
    print(f"UNIVERSE_SOURCE: {universe_source}")
    print(f"RAW_UNIVERSE_COUNT: {raw_count}")
    print(f"START_DATE: {start_date}")
    print(f"END_DATE: {end_date_str}")

    panel = base.download_panel(tickers_to_download, start_date, end_date_str)

    adj_close = panel.get("Adj Close", pd.DataFrame())
    close_raw = panel.get("Close", pd.DataFrame())
    volume_raw = panel.get("Volume", pd.DataFrame())

    close_all = adj_close if not adj_close.empty else close_raw

    available = [
        t for t in universe
        if t in close_all.columns and close_all[t].notna().sum() >= 160
    ]

    missing = sorted(set(universe) - set(available))

    if len(available) < min_names:
        raise RuntimeError(
            f"Not enough usable tickers for lookback {lookback_days}. "
            f"available={len(available)}, min_names={min_names}"
        )

    close = close_all[available].copy()
    volume = volume_raw.reindex(close.index)[available].copy()

    daily_returns = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    qqq_ret = None
    if "QQQ" in close_all.columns:
        qqq_ret = close_all["QQQ"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    factors = base.compute_factors(close, volume)

    meta = {
        "lookback_days": lookback_days,
        "start_date": start_date,
        "end_date": end_date_str,
        "universe_source": str(universe_source),
        "raw_universe_count": raw_count,
        "available_ticker_count": len(available),
        "missing_ticker_count": len(missing),
    }

    return factors, daily_returns, qqq_ret, meta


def assign_config_ranks(matrix):
    ranked_frames = []

    group_cols = ["lookback_days", "top_n", "hold_days", "cost_bps"]

    for _, g in matrix.groupby(group_cols, dropna=False):
        h = g.sort_values(
            ["sharpe_0rf", "excess_cagr_vs_bench", "cagr"],
            ascending=[False, False, False],
            na_position="last",
        ).copy()

        h["config_rank"] = range(1, len(h) + 1)
        ranked_frames.append(h)

    if not ranked_frames:
        return matrix

    return pd.concat(ranked_frames, ignore_index=True)


def make_summary(matrix):
    rows = []

    total_config_count = matrix[["lookback_days", "top_n", "hold_days", "cost_bps"]].drop_duplicates().shape[0]

    for factor, g in matrix.groupby("factor"):
        config_count = len(g)

        top1_count = int((g["config_rank"] == 1).sum())
        top3_count = int((g["config_rank"] <= 3).sum())

        avg_rank = float(g["config_rank"].mean())
        median_rank = float(g["config_rank"].median())
        best_rank = int(g["config_rank"].min())
        worst_rank = int(g["config_rank"].max())
        rank_std = float(g["config_rank"].std(ddof=0))

        avg_sharpe = float(g["sharpe_0rf"].mean())
        median_sharpe = float(g["sharpe_0rf"].median())
        min_sharpe = float(g["sharpe_0rf"].min())

        avg_cagr = float(g["cagr"].mean())
        median_cagr = float(g["cagr"].median())
        avg_excess = float(g["excess_cagr_vs_bench"].mean())

        avg_max_dd = float(g["max_drawdown"].mean())
        worst_max_dd = float(g["max_drawdown"].min())

        avg_turnover = float(g["avg_turnover"].mean())
        negative_excess_count = int((g["excess_cagr_vs_bench"] < 0).sum())
        maxdd_over_50_count = int((g["max_drawdown"] <= -0.50).sum())

        top1_rate = top1_count / max(config_count, 1)
        top3_rate = top3_count / max(config_count, 1)

        if top3_rate >= 0.60 and avg_rank <= 3.0 and avg_sharpe >= 1.60 and worst_max_dd > -0.55:
            recommendation = "STRONG_WATCH"
        elif top3_rate >= 0.45 and avg_rank <= 3.5 and avg_sharpe >= 1.45:
            recommendation = "WATCH"
        elif top3_count > 0 and avg_sharpe >= 1.30:
            recommendation = "SECONDARY_EVIDENCE"
        else:
            recommendation = "WEAK_OR_SENSITIVE"

        if factor == "F007_PULLBACK_IN_UPTREND":
            role = "CORE_PULLBACK_UPTREND_CANDIDATE"
        elif factor == "F010_XSEC_COMPOSITE_RANK":
            role = "COMPOSITE_RANK_STABILIZER"
        elif factor == "F006_SHORT_REV_5D":
            role = "SHORT_REVERSAL_CONFIRMATION"
        elif factor == "F009_VOLUME_PRICE_CONFIRM":
            role = "VOLUME_PRICE_CONFIRMATION"
        elif factor == "F008_VOLUME_ABNORMAL_5_20":
            role = "VOLUME_ABNORMALITY_SECONDARY"
        elif factor == "F011_TS_MOMENTUM_60_120":
            role = "TREND_CONFIRMATION_ONLY"
        else:
            role = "UNKNOWN"

        rows.append({
            "factor": factor,
            "role": role,
            "recommendation": recommendation,
            "config_count": config_count,
            "total_config_count": total_config_count,
            "avg_rank": avg_rank,
            "median_rank": median_rank,
            "best_rank": best_rank,
            "worst_rank": worst_rank,
            "rank_std": rank_std,
            "top1_count": top1_count,
            "top1_rate": top1_rate,
            "top3_count": top3_count,
            "top3_rate": top3_rate,
            "avg_sharpe": avg_sharpe,
            "median_sharpe": median_sharpe,
            "min_sharpe": min_sharpe,
            "avg_cagr": avg_cagr,
            "median_cagr": median_cagr,
            "avg_excess_cagr_vs_qqq": avg_excess,
            "avg_max_drawdown": avg_max_dd,
            "worst_max_drawdown": worst_max_dd,
            "avg_turnover": avg_turnover,
            "negative_excess_count": negative_excess_count,
            "maxdd_over_50_count": maxdd_over_50_count,
        })

    summary = pd.DataFrame(rows)

    if not summary.empty:
        summary = summary.sort_values(
            ["avg_rank", "top3_rate", "avg_sharpe"],
            ascending=[True, False, False],
        )

    return summary


def write_report(report_path, current_path, args, matrix, summary):
    lines = []

    lines.append("# V18.4H-R1 因子稳健性审计报告")
    lines.append("")
    lines.append("## 1. 结论")
    lines.append("")
    lines.append("本报告自动测试当前 F006-F011 因子在不同参数组合下的稳健性。")
    lines.append("它是历史回测证据层，不直接改变 official daily decision。")
    lines.append("")
    lines.append("## 2. 参数矩阵")
    lines.append("")
    lines.append(f"- LOOKBACK_DAYS_LIST: `{args.lookback_days_list}`")
    lines.append(f"- TOP_N_LIST: `{args.top_n_list}`")
    lines.append(f"- HOLD_DAYS_LIST: `{args.hold_days_list}`")
    lines.append(f"- COST_BPS_LIST: `{args.cost_bps_list}`")
    lines.append(f"- MATRIX_ROWS: `{len(matrix)}`")
    lines.append(f"- CONFIG_COUNT: `{matrix[['lookback_days', 'top_n', 'hold_days', 'cost_bps']].drop_duplicates().shape[0]}`")
    lines.append("")

    lines.append("## 3. 因子稳健性排名")
    lines.append("")
    lines.append("| rank | factor | recommendation | role | avg rank | top1 | top3 rate | avg Sharpe | avg CAGR | worst MaxDD |")
    lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---:|")

    for idx, (_, row) in enumerate(summary.iterrows(), start=1):
        lines.append(
            f"| {idx} | {row['factor']} | {row['recommendation']} | {row['role']} | "
            f"{row['avg_rank']:.2f} | {int(row['top1_count'])} | "
            f"{fmt_pct(row['top3_rate'])} | {row['avg_sharpe']:.3f} | "
            f"{fmt_pct(row['avg_cagr'])} | {fmt_pct(row['worst_max_drawdown'])} |"
        )

    lines.append("")
    lines.append("## 4. 解释规则")
    lines.append("")
    lines.append("- STRONG_WATCH：多数参数下进入前三，平均排名靠前，Sharpe 较高，且最差回撤没有严重失控。")
    lines.append("- WATCH：整体表现良好，但仍存在参数敏感性。")
    lines.append("- SECONDARY_EVIDENCE：可作为确认层，不适合作为单独主信号。")
    lines.append("- WEAK_OR_SENSITIVE：参数敏感或排序不稳定。")
    lines.append("")
    lines.append("## 5. 当前系统建议")
    lines.append("")
    lines.append("当前不做直接 promotion。")
    lines.append("下一步应把本历史稳健性审计结果与 V18.4A forward tracker 合并，形成 V18.4I backtest-forward promotion evidence。")
    lines.append("")
    lines.append("建议的候选结构不是单因子，而是：")
    lines.append("")
    lines.append("```text")
    lines.append("F007_PULLBACK_IN_UPTREND")
    lines.append("+ F010_XSEC_COMPOSITE_RANK")
    lines.append("+ F006_SHORT_REV_5D or F009_VOLUME_PRICE_CONFIRM")
    lines.append("```")
    lines.append("")
    lines.append("F011_TS_MOMENTUM_60_120 只作为趋势确认层，不作为单独 promotion 主因子。")
    lines.append("")
    lines.append("## 6. 输出文件")
    lines.append("")
    lines.append("- `V18_4H_R1_CURRENT_ROBUSTNESS_MATRIX.csv`")
    lines.append("- `V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_SUMMARY.csv`")
    lines.append("- `V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_REPORT.md`")
    lines.append("- `V18_CURRENT_FACTOR_ROBUSTNESS.md`")

    text = "\n".join(lines)
    report_path.write_text(text, encoding="utf-8")
    current_path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--lookback-days-list", type=str, default="756,1260")
    parser.add_argument("--top-n-list", type=str, default="5,10,15,20")
    parser.add_argument("--hold-days-list", type=str, default="3,5,10,20")
    parser.add_argument("--cost-bps-list", type=str, default="10,25,50")
    parser.add_argument("--min-names", type=int, default=20)
    parser.add_argument("--end-date", type=str, default="")

    args = parser.parse_args()

    lookback_days_list = parse_int_list(args.lookback_days_list, [756, 1260])
    top_n_list = parse_int_list(args.top_n_list, [5, 10, 15, 20])
    hold_days_list = parse_int_list(args.hold_days_list, [3, 5, 10, 20])
    cost_bps_list = parse_float_list(args.cost_bps_list, [10.0, 25.0, 50.0])

    all_rows = []

    for lookback_days in lookback_days_list:
        factors, daily_returns, qqq_ret, meta = prepare_data(
            lookback_days=lookback_days,
            end_date=args.end_date,
            min_names=args.min_names,
        )

        for top_n in top_n_list:
            for hold_days in hold_days_list:
                for cost_bps in cost_bps_list:
                    print("")
                    print(
                        "RUN_CONFIG:",
                        f"LOOKBACK={lookback_days}",
                        f"TOP_N={top_n}",
                        f"HOLD_DAYS={hold_days}",
                        f"COST_BPS={cost_bps}",
                    )

                    for factor_name, factor_df in factors.items():
                        ret, holdings, aux = base.run_backtest(
                            factor=factor_df,
                            daily_returns=daily_returns,
                            strategy_type="LONG_ONLY_TOPN",
                            top_n=top_n,
                            bottom_n=top_n,
                            hold_days=hold_days,
                            cost_bps=cost_bps,
                            min_names=args.min_names,
                        )

                        metrics = base.calc_metrics(ret, qqq_ret)

                        row = {
                            "factor": factor_name,
                            "strategy_type": "LONG_ONLY_TOPN",
                            "lookback_days": lookback_days,
                            "start_date": meta["start_date"],
                            "end_date": meta["end_date"],
                            "top_n": top_n,
                            "hold_days": hold_days,
                            "cost_bps": cost_bps,
                            "universe_source": meta["universe_source"],
                            "raw_universe_count": meta["raw_universe_count"],
                            "available_ticker_count": meta["available_ticker_count"],
                            "missing_ticker_count": meta["missing_ticker_count"],
                            **metrics,
                            **aux,
                        }

                        all_rows.append(row)

    matrix = pd.DataFrame(all_rows)

    if matrix.empty:
        raise RuntimeError("No robustness matrix rows generated.")

    matrix = assign_config_ranks(matrix)
    summary = make_summary(matrix)

    matrix_path = OUT_DIR / "V18_4H_R1_CURRENT_ROBUSTNESS_MATRIX.csv"
    summary_path = OUT_DIR / "V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_SUMMARY.csv"
    report_path = OUT_DIR / "V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_REPORT.md"
    current_path = OUT_DIR / "V18_CURRENT_FACTOR_ROBUSTNESS.md"

    matrix.to_csv(matrix_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    write_report(
        report_path=report_path,
        current_path=current_path,
        args=args,
        matrix=matrix,
        summary=summary,
    )

    print("")
    print("=== V18.4H-R1 FACTOR ROBUSTNESS AUDIT READY ===")
    print(f"MATRIX_ROWS: {len(matrix)}")
    print(f"CONFIG_COUNT: {matrix[['lookback_days', 'top_n', 'hold_days', 'cost_bps']].drop_duplicates().shape[0]}")
    print(f"MATRIX: {matrix_path}")
    print(f"SUMMARY: {summary_path}")
    print(f"REPORT: {report_path}")
    print(f"CURRENT: {current_path}")

    print("")
    print("=== ROBUSTNESS SUMMARY RANKING ===")

    for _, row in summary.iterrows():
        print(
            f"{row['factor']}: "
            f"REC={row['recommendation']}, "
            f"AVG_RANK={row['avg_rank']:.2f}, "
            f"TOP1={int(row['top1_count'])}, "
            f"TOP3_RATE={row['top3_rate']:.2%}, "
            f"AVG_SHARPE={row['avg_sharpe']:.3f}, "
            f"AVG_CAGR={row['avg_cagr']:.4f}, "
            f"WORST_DD={row['worst_max_drawdown']:.4f}"
        )


if __name__ == "__main__":
    main()