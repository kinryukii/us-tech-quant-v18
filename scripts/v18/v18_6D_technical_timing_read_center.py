import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return pd.DataFrame()


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def to_bool_series(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_EMPTY_"
    return df.to_markdown(index=False)


def add_current_signal_flags(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()

    for c in [
        "technical_timing_score",
        "overheat_penalty",
        "pullback_timing_bonus",
        "breakout_confirmation_bonus",
        "volume_ratio_5_20",
        "rsi_14",
        "kdj_k",
        "kdj_d",
        "kdj_j",
        "bb_percent_b",
        "bb_bandwidth",
        "vix_close",
    ]:
        if c in x.columns:
            x[c] = pd.to_numeric(x[c], errors="coerce")
        else:
            x[c] = np.nan

    if "technical_signal" not in x.columns:
        x["technical_signal"] = ""
    if "bb_status" not in x.columns:
        x["bb_status"] = ""
    if "rsi_status" not in x.columns:
        x["rsi_status"] = ""
    if "kdj_status" not in x.columns:
        x["kdj_status"] = ""
    if "technical_warning_label" not in x.columns:
        x["technical_warning_label"] = "NONE"
    if "price_date" not in x.columns:
        x["price_date"] = ""
    if "ticker" not in x.columns:
        x["ticker"] = ""

    x["ticker"] = x["ticker"].astype(str).str.strip()
    x["price_date"] = x["price_date"].astype(str).str.strip()

    if "bb_squeeze_flag" in x.columns:
        x["signal_bb_squeeze"] = to_bool_series(x["bb_squeeze_flag"])
    else:
        x["signal_bb_squeeze"] = False

    x["signal_watch_positive"] = x["technical_signal"].astype(str).eq("TECH_TIMING_WATCH_POSITIVE")
    x["signal_pullback_watch"] = x["technical_signal"].astype(str).eq("TECH_TIMING_PULLBACK_WATCH")
    x["signal_old_overheat"] = x["technical_signal"].astype(str).eq("TECH_TIMING_OVERHEAT_AVOID_CHASE")

    x["signal_breakout_continuation"] = (
        x["bb_status"].astype(str).isin(["BB_ABOVE_UPPER", "BB_NEAR_UPPER"])
        & (x["rsi_14"] >= 60)
        & (x["rsi_14"] <= 78)
        & (x["volume_ratio_5_20"] >= 1.15)
        & (~x["kdj_status"].astype(str).isin(["KDJ_HIGH_DEAD_CROSS"]))
    )

    x["signal_exhaustion_risk"] = (
        (x["rsi_14"] >= 75)
        & x["kdj_status"].astype(str).isin(["KDJ_EXTREME_OVERHEAT", "KDJ_HIGH_DEAD_CROSS"])
        & ((x["volume_ratio_5_20"] < 1.0) | x["volume_ratio_5_20"].isna())
    )

    x["signal_overheat_unclassified"] = (
        x["signal_old_overheat"]
        & (~x["signal_breakout_continuation"])
        & (~x["signal_exhaustion_risk"])
    )

    def label(row):
        if row["signal_watch_positive"]:
            return "WATCH_POSITIVE"
        if row["signal_pullback_watch"]:
            return "PULLBACK_WATCH"
        if row["signal_breakout_continuation"]:
            return "BREAKOUT_CONTINUATION"
        if row["signal_exhaustion_risk"]:
            return "EXHAUSTION_RISK"
        if row["signal_overheat_unclassified"]:
            return "OVERHEAT_UNCLASSIFIED"
        if row["signal_bb_squeeze"]:
            return "BB_SQUEEZE_ONLY"
        if row["signal_old_overheat"]:
            return "OLD_OVERHEAT_REVIEW"
        return "NEUTRAL"

    x["technical_read_center_label"] = x.apply(label, axis=1)
    return x


def top_rows(df: pd.DataFrame, mask_col: str, n: int = 15, sort_cols=None) -> pd.DataFrame:
    if df.empty or mask_col not in df.columns:
        return pd.DataFrame()

    sub = df[df[mask_col].fillna(False)].copy()
    if sub.empty:
        return pd.DataFrame()

    if sort_cols is None:
        sort_cols = ["technical_timing_score", "volume_ratio_5_20"]

    ascending = [False for _ in sort_cols]
    sub = sub.sort_values(sort_cols, ascending=ascending).head(n)

    cols = [
        "ticker",
        "price_date",
        "close",
        "technical_timing_score",
        "technical_read_center_label",
        "technical_signal",
        "bb_status",
        "rsi_status",
        "kdj_status",
        "volume_ratio_5_20",
        "technical_warning_label",
    ]

    for c in cols:
        if c not in sub.columns:
            sub[c] = np.nan

    return sub[cols]


def load_signal_20d(signal_path: Path) -> pd.DataFrame:
    df = read_csv_safe(signal_path)
    if df.empty:
        return pd.DataFrame()

    if "horizon_days" in df.columns:
        df["horizon_days"] = pd.to_numeric(df["horizon_days"], errors="coerce")
        df = df[df["horizon_days"] == 20].copy()

    wanted = [
        "signal",
        "horizon_days",
        "obs",
        "avg_ret",
        "win_rate",
        "avg_excess_vs_QQQ",
        "avg_excess_vs_SPY",
        "avg_excess_vs_SMH",
        "excess_win_rate_vs_QQQ",
        "excess_win_rate_vs_SPY",
        "excess_win_rate_vs_SMH",
    ]

    for c in wanted:
        if c not in df.columns:
            df[c] = np.nan

    priority = [
        "WATCH_POSITIVE",
        "PULLBACK_WATCH",
        "BB_SQUEEZE",
        "OVERHEAT_BREAKOUT_CONTINUATION",
        "OVERHEAT_EXHAUSTION_RISK",
        "OVERHEAT_UNCLASSIFIED",
    ]

    df["signal_priority"] = df["signal"].astype(str).apply(lambda x: priority.index(x) if x in priority else 999)
    df = df.sort_values(["signal_priority", "signal"])
    return df[wanted]


def load_strategy_summary(strategy_path: Path) -> pd.DataFrame:
    df = read_csv_safe(strategy_path)
    if df.empty:
        return pd.DataFrame()

    for c in ["avg_net_ret", "avg_excess_vs_QQQ", "avg_excess_vs_SPY", "avg_excess_vs_SMH", "win_rate"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = np.nan

    df = df.sort_values(["avg_excess_vs_QQQ", "avg_net_ret", "win_rate"], ascending=[False, False, False]).head(10)

    wanted = [
        "strategy",
        "obs",
        "avg_net_ret",
        "win_rate",
        "avg_excess_vs_QQQ",
        "avg_excess_vs_SPY",
        "avg_excess_vs_SMH",
        "excess_win_rate_vs_QQQ",
        "excess_win_rate_vs_SPY",
        "excess_win_rate_vs_SMH",
    ]

    for c in wanted:
        if c not in df.columns:
            df[c] = np.nan

    return df[wanted]


def summarize_forward_tracker(summary_path: Path) -> pd.DataFrame:
    df = read_csv_safe(summary_path)
    if df.empty:
        return pd.DataFrame()

    wanted = [
        "signal",
        "horizon_days",
        "completed_obs",
        "avg_ret",
        "median_ret",
        "win_rate",
        "avg_win",
        "avg_loss",
    ]

    for c in wanted:
        if c not in df.columns:
            df[c] = np.nan

    return df[wanted]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    root = Path(args.root)

    current_path = root / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING.csv"
    signal_summary_path = root / "outputs" / "v18" / "technical_timing_backtest" / "V18_6B_R1_CURRENT_SIGNAL_EXCESS_SUMMARY.csv"
    strategy_summary_path = root / "outputs" / "v18" / "technical_timing_backtest" / "V18_6B_R1_CURRENT_TOPN_EXCESS_STRATEGY_SUMMARY.csv"
    forward_summary_path = root / "outputs" / "v18" / "technical_timing_forward" / "V18_6C_R1_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv"
    stale_audit_path = root / "outputs" / "v18" / "technical_timing_forward" / "V18_6C_R1_CURRENT_STALE_PRICE_AUDIT.csv"
    freshness_report_path = root / "outputs" / "v18" / "technical_timing_forward" / "V18_6C_R1_CURRENT_FRESHNESS_GUARD_REPORT.md"

    out_dir = root / "outputs" / "v18" / "technical_timing_read_center"
    out_dir.mkdir(parents=True, exist_ok=True)

    dashboard_csv = out_dir / "V18_6D_CURRENT_TECHNICAL_TIMING_DASHBOARD.csv"
    report_path = out_dir / "V18_6D_CURRENT_TECHNICAL_TIMING_READ_CENTER.md"
    global_report_path = out_dir / "V18_CURRENT_TECHNICAL_TIMING_READ_CENTER.md"
    read_first_path = out_dir / "V18_6D_READ_FIRST.txt"
    global_read_first_path = out_dir / "V18_CURRENT_TECHNICAL_TIMING_READ_FIRST.md"

    current_raw = read_csv_safe(current_path)
    if current_raw.empty:
        raise RuntimeError(f"Missing current technical timing CSV: {current_path}")

    current = add_current_signal_flags(current_raw)

    latest_date = current["price_date"].max()
    fresh = current[current["price_date"] == latest_date].copy()
    stale = current[current["price_date"] != latest_date].copy()

    write_csv(current, dashboard_csv)

    stale_audit = read_csv_safe(stale_audit_path)
    signal_20d = load_signal_20d(signal_summary_path)
    top_strategy = load_strategy_summary(strategy_summary_path)
    forward_summary = summarize_forward_tracker(forward_summary_path)

    vix_close = np.nan
    vix_regime = "VIX_UNKNOWN"
    if "vix_close" in fresh.columns and fresh["vix_close"].notna().any():
        vix_close = fresh["vix_close"].dropna().iloc[0]
    if "vix_regime" in fresh.columns and fresh["vix_regime"].notna().any():
        vix_regime = str(fresh["vix_regime"].dropna().iloc[0])

    counts = {
        "WATCH_POSITIVE": int(fresh["signal_watch_positive"].sum()),
        "PULLBACK_WATCH": int(fresh["signal_pullback_watch"].sum()),
        "BB_SQUEEZE": int(fresh["signal_bb_squeeze"].sum()),
        "BREAKOUT_CONTINUATION": int(fresh["signal_breakout_continuation"].sum()),
        "EXHAUSTION_RISK": int(fresh["signal_exhaustion_risk"].sum()),
        "OVERHEAT_UNCLASSIFIED": int(fresh["signal_overheat_unclassified"].sum()),
        "OLD_OVERHEAT": int(fresh["signal_old_overheat"].sum()),
    }

    count_df = pd.DataFrame([
        {"bucket": k, "current_count": v}
        for k, v in counts.items()
    ])

    key_cols = [
        "ticker",
        "price_date",
        "close",
        "technical_timing_score",
        "technical_read_center_label",
        "technical_signal",
        "bb_status",
        "rsi_status",
        "kdj_status",
        "volume_ratio_5_20",
        "technical_warning_label",
    ]

    watch = top_rows(fresh, "signal_watch_positive", 15)
    pullback = top_rows(fresh, "signal_pullback_watch", 15)
    breakout = top_rows(fresh, "signal_breakout_continuation", 15)
    exhaustion = top_rows(fresh, "signal_exhaustion_risk", 15, sort_cols=["overheat_penalty", "technical_timing_score"])
    squeeze = top_rows(fresh, "signal_bb_squeeze", 15, sort_cols=["technical_timing_score", "volume_ratio_5_20"])
    overheat_unclassified = top_rows(fresh, "signal_overheat_unclassified", 15, sort_cols=["technical_timing_score", "volume_ratio_5_20"])

    report = f"""# V18.6D Technical Timing Read Center

Generated: `{stamp()}`

## 1. Status

- V18_6D_STATUS: `OK_TECHNICAL_TIMING_READ_CENTER_READY`
- CURRENT_TOTAL_ROWS: `{len(current)}`
- FRESH_ROWS_LATEST_DATE: `{len(fresh)}`
- STALE_ROWS: `{len(stale)}`
- LATEST_PRICE_DATE: `{latest_date}`
- VIX_CLOSE: `{vix_close}`
- VIX_REGIME: `{vix_regime}`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. Current Signal Bucket Counts

{table(count_df)}

## 3. Current Watch Positive

{table(watch)}

## 4. Current Pullback Watch

{table(pullback)}

## 5. Current Breakout Continuation Review

{table(breakout)}

## 6. Current Exhaustion Risk Review

{table(exhaustion)}

## 7. Current BB Squeeze

{table(squeeze)}

## 8. Current Overheat Unclassified

{table(overheat_unclassified)}

## 9. Stale Price Audit

{table(stale_audit if not stale_audit.empty else stale)}

## 10. Historical 20D Signal Evidence From V18.6B-R1

{table(signal_20d)}

## 11. Top Technical Strategy Evidence From V18.6B-R1

{table(top_strategy)}

## 12. Forward Tracker Maturity From V18.6C-R1

{table(forward_summary)}

## 13. Interpretation

- `WATCH_POSITIVE` is the highest-quality technical timing observation bucket.
- `PULLBACK_WATCH` is a secondary observation bucket.
- `BREAKOUT_CONTINUATION` should not be treated as bearish overheat; it may represent momentum continuation.
- `EXHAUSTION_RISK` is a review bucket, not a forced sell rule.
- `BB_SQUEEZE` is a volatility-compression tag and needs direction confirmation.
- `OFFICIAL_DECISION_IMPACT` remains `NONE`.

## 14. Source Files

- CURRENT_TECHNICAL_TIMING: `{current_path}`
- SIGNAL_EXCESS_SUMMARY: `{signal_summary_path}`
- TOPN_EXCESS_STRATEGY_SUMMARY: `{strategy_summary_path}`
- FORWARD_SUMMARY: `{forward_summary_path}`
- STALE_AUDIT: `{stale_audit_path}`
- FRESHNESS_REPORT: `{freshness_report_path}`
- DASHBOARD_CSV: `{dashboard_csv}`
"""

    write_text(report_path, report)
    write_text(global_report_path, report)

    read_first = f"""# V18.6D Technical Timing Read First

STATUS: `OK_TECHNICAL_TIMING_READ_CENTER_READY`

LATEST_PRICE_DATE: `{latest_date}`

CURRENT_TOTAL_ROWS: `{len(current)}`
FRESH_ROWS_LATEST_DATE: `{len(fresh)}`
STALE_ROWS: `{len(stale)}`

VIX: `{vix_close}` / `{vix_regime}`

CURRENT_COUNTS:
- WATCH_POSITIVE: `{counts["WATCH_POSITIVE"]}`
- PULLBACK_WATCH: `{counts["PULLBACK_WATCH"]}`
- BB_SQUEEZE: `{counts["BB_SQUEEZE"]}`
- BREAKOUT_CONTINUATION: `{counts["BREAKOUT_CONTINUATION"]}`
- EXHAUSTION_RISK: `{counts["EXHAUSTION_RISK"]}`
- OVERHEAT_UNCLASSIFIED: `{counts["OVERHEAT_UNCLASSIFIED"]}`
- OLD_OVERHEAT: `{counts["OLD_OVERHEAT"]}`

OFFICIAL_DECISION_IMPACT: `NONE`

READ:
`{report_path}`

DASHBOARD:
`{dashboard_csv}`
"""

    write_text(read_first_path, read_first)
    write_text(global_read_first_path, read_first)

    print("")
    print("=== V18.6D TECHNICAL TIMING READ CENTER READY ===")
    print(f"CURRENT_TOTAL_ROWS: {len(current)}")
    print(f"FRESH_ROWS_LATEST_DATE: {len(fresh)}")
    print(f"STALE_ROWS: {len(stale)}")
    print(f"LATEST_PRICE_DATE: {latest_date}")
    print(f"VIX_CLOSE: {vix_close}")
    print(f"VIX_REGIME: {vix_regime}")
    for k, v in counts.items():
        print(f"{k}_COUNT: {v}")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"READ_CENTER: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    print(f"DASHBOARD: {dashboard_csv}")


if __name__ == "__main__":
    main()
