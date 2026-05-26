import argparse
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ["utf-8", "utf-8-sig", "cp936", "gbk"]:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
    return ""


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


def table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_EMPTY_"
    return df.to_markdown(index=False)


def to_bool_series(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def scan_key_lines(text: str) -> pd.DataFrame:
    keys = [
        "V18_4J",
        "FINAL_ACTION",
        "BUY_PERMISSION",
        "TODAY_SAFE",
        "DIRECT_PROMOTION",
        "PROMOTION_ACTION",
        "PROMOTION_RECOMMENDATION",
        "OFFICIAL_DECISION_IMPACT",
        "FORWARD_KEEP",
        "NO_BUY",
        "NO_NEW_BUYS",
    ]

    rows = []
    seen = set()

    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue

        hit = False
        for k in keys:
            if k in raw:
                hit = True
                break

        if hit:
            clean = re.sub(r"\s+", " ", raw)
            if clean not in seen:
                seen.add(clean)
                rows.append({"main_read_center_key_line": clean})

    return pd.DataFrame(rows[:40])


def normalize_numeric(df: pd.DataFrame, cols):
    x = df.copy()
    for c in cols:
        if c in x.columns:
            x[c] = pd.to_numeric(x[c], errors="coerce")
        else:
            x[c] = np.nan
    return x


def load_dashboard(path: Path):
    df = read_csv_safe(path)
    if df.empty:
        return df, pd.DataFrame(), "", {}

    if "price_date" not in df.columns:
        df["price_date"] = ""

    df["price_date"] = df["price_date"].astype(str)
    latest_date = df["price_date"].max()
    fresh = df[df["price_date"] == latest_date].copy()

    num_cols = [
        "close",
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
    ]

    df = normalize_numeric(df, num_cols)
    fresh = normalize_numeric(fresh, num_cols)

    bool_cols = [
        "signal_watch_positive",
        "signal_pullback_watch",
        "signal_bb_squeeze",
        "signal_breakout_continuation",
        "signal_exhaustion_risk",
        "signal_overheat_unclassified",
        "signal_old_overheat",
    ]

    for c in bool_cols:
        if c in fresh.columns:
            fresh[c] = to_bool_series(fresh[c])
        else:
            fresh[c] = False

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

    meta = {
        "latest_date": latest_date,
        "total_rows": len(df),
        "fresh_rows": len(fresh),
        "stale_rows": len(df) - len(fresh),
        "vix_close": vix_close,
        "vix_regime": vix_regime,
        **counts,
    }

    return df, fresh, latest_date, meta


def top_bucket(fresh: pd.DataFrame, bool_col: str, n: int = 10, sort_cols=None):
    if fresh.empty or bool_col not in fresh.columns:
        return pd.DataFrame()

    sub = fresh[fresh[bool_col].fillna(False)].copy()
    if sub.empty:
        return pd.DataFrame()

    if sort_cols is None:
        sort_cols = ["technical_timing_score", "volume_ratio_5_20"]

    sub = sub.sort_values(sort_cols, ascending=[False] * len(sort_cols)).head(n)

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


def signal_20d_summary(path: Path):
    df = read_csv_safe(path)
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

    df["priority"] = df["signal"].astype(str).apply(lambda x: priority.index(x) if x in priority else 999)
    df = df.sort_values(["priority", "signal"])
    return df[wanted]


def strategy_h20_summary(path: Path):
    df = read_csv_safe(path)
    if df.empty:
        return pd.DataFrame()

    if "strategy" in df.columns:
        df = df[df["strategy"].astype(str).str.contains("_H20", na=False)].copy()

    for c in ["avg_net_ret", "avg_excess_vs_QQQ", "avg_excess_vs_SPY", "avg_excess_vs_SMH", "win_rate"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = np.nan

    df = df.sort_values(["avg_excess_vs_QQQ", "avg_net_ret"], ascending=[False, False]).head(10)

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


def forward_maturity(path: Path):
    df = read_csv_safe(path)
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

    main_read_first = root / "outputs" / "v18" / "read_center" / "V18_CURRENT_READ_FIRST.md"
    main_read_center = root / "outputs" / "v18" / "read_center" / "V18_4J_CURRENT_READ_CENTER.md"

    tech_dashboard = root / "outputs" / "v18" / "technical_timing_read_center" / "V18_6D_CURRENT_TECHNICAL_TIMING_DASHBOARD.csv"
    tech_read_center = root / "outputs" / "v18" / "technical_timing_read_center" / "V18_CURRENT_TECHNICAL_TIMING_READ_CENTER.md"
    tech_read_first = root / "outputs" / "v18" / "technical_timing_read_center" / "V18_CURRENT_TECHNICAL_TIMING_READ_FIRST.md"

    signal_summary = root / "outputs" / "v18" / "technical_timing_backtest" / "V18_6B_R1_CURRENT_SIGNAL_EXCESS_SUMMARY.csv"
    strategy_summary = root / "outputs" / "v18" / "technical_timing_backtest" / "V18_6B_R1_CURRENT_TOPN_EXCESS_STRATEGY_SUMMARY.csv"
    forward_summary = root / "outputs" / "v18" / "technical_timing_forward" / "V18_6C_R1_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv"
    stale_audit_path = root / "outputs" / "v18" / "technical_timing_forward" / "V18_6C_R1_CURRENT_STALE_PRICE_AUDIT.csv"

    out_dir = root / "outputs" / "v18" / "read_center"
    report_path = out_dir / "V18_6E_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md"
    global_report_path = out_dir / "V18_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md"
    read_first_path = out_dir / "V18_6E_READ_FIRST.txt"
    global_read_first_path = out_dir / "V18_CURRENT_READ_FIRST_WITH_TECHNICAL.md"

    main_text = read_text_safe(main_read_first) + "\n" + read_text_safe(main_read_center)
    main_key_lines = scan_key_lines(main_text)

    dashboard_all, fresh, latest_date, meta = load_dashboard(tech_dashboard)

    watch = top_bucket(fresh, "signal_watch_positive", 12)
    pullback = top_bucket(fresh, "signal_pullback_watch", 12)
    breakout = top_bucket(fresh, "signal_breakout_continuation", 12)
    exhaustion = top_bucket(fresh, "signal_exhaustion_risk", 12, sort_cols=["overheat_penalty", "technical_timing_score"])
    squeeze = top_bucket(fresh, "signal_bb_squeeze", 12)
    overheat_unclassified = top_bucket(fresh, "signal_overheat_unclassified", 12)

    stale_audit = read_csv_safe(stale_audit_path)
    signal20 = signal_20d_summary(signal_summary)
    strategy20 = strategy_h20_summary(strategy_summary)
    forward = forward_maturity(forward_summary)

    counts_df = pd.DataFrame([
        {"bucket": "WATCH_POSITIVE", "current_count": meta.get("WATCH_POSITIVE", 0)},
        {"bucket": "PULLBACK_WATCH", "current_count": meta.get("PULLBACK_WATCH", 0)},
        {"bucket": "BB_SQUEEZE", "current_count": meta.get("BB_SQUEEZE", 0)},
        {"bucket": "BREAKOUT_CONTINUATION", "current_count": meta.get("BREAKOUT_CONTINUATION", 0)},
        {"bucket": "EXHAUSTION_RISK", "current_count": meta.get("EXHAUSTION_RISK", 0)},
        {"bucket": "OVERHEAT_UNCLASSIFIED", "current_count": meta.get("OVERHEAT_UNCLASSIFIED", 0)},
        {"bucket": "OLD_OVERHEAT", "current_count": meta.get("OLD_OVERHEAT", 0)},
    ])

    report = f"""# V18.6E Final Read Center With Technical Timing

Generated: `{stamp()}`

## 1. Status

- V18_6E_STATUS: `OK_FINAL_READ_CENTER_WITH_TECHNICAL_READY`
- MAIN_READ_FIRST_FOUND: `{main_read_first.exists()}`
- MAIN_READ_CENTER_FOUND: `{main_read_center.exists()}`
- TECHNICAL_READ_CENTER_FOUND: `{tech_read_center.exists()}`
- TECHNICAL_DASHBOARD_FOUND: `{tech_dashboard.exists()}`
- TECH_LATEST_PRICE_DATE: `{meta.get("latest_date", "")}`
- TECH_CURRENT_TOTAL_ROWS: `{meta.get("total_rows", 0)}`
- TECH_FRESH_ROWS: `{meta.get("fresh_rows", 0)}`
- TECH_STALE_ROWS: `{meta.get("stale_rows", 0)}`
- VIX_CLOSE: `{meta.get("vix_close", np.nan)}`
- VIX_REGIME: `{meta.get("vix_regime", "VIX_UNKNOWN")}`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. Main Daily Decision Key Lines

{table(main_key_lines)}

## 3. Technical Timing Current Bucket Counts

{table(counts_df)}

## 4. Current WATCH_POSITIVE

{table(watch)}

## 5. Current PULLBACK_WATCH

{table(pullback)}

## 6. Current BREAKOUT_CONTINUATION

{table(breakout)}

## 7. Current EXHAUSTION_RISK

{table(exhaustion)}

## 8. Current BB_SQUEEZE

{table(squeeze)}

## 9. Current OVERHEAT_UNCLASSIFIED

{table(overheat_unclassified)}

## 10. Stale Ticker Audit

{table(stale_audit)}

## 11. Historical 20D Technical Signal Evidence

{table(signal20)}

## 12. Historical H20 TopN Technical Strategy Evidence

{table(strategy20)}

## 13. Technical Forward Tracker Maturity

{table(forward)}

## 14. Interpretation

- The technical timing layer is now visible in the final read center.
- `WATCH_POSITIVE` and `PULLBACK_WATCH` are observation buckets, not official buy instructions.
- `BREAKOUT_CONTINUATION` should not be treated as bearish overheat.
- `EXHAUSTION_RISK` is a review bucket, not a forced sell rule.
- `BB_SQUEEZE` needs direction confirmation.
- `OFFICIAL_DECISION_IMPACT` remains `NONE`.

## 15. Source Files

- MAIN_READ_FIRST: `{main_read_first}`
- MAIN_READ_CENTER: `{main_read_center}`
- TECH_READ_FIRST: `{tech_read_first}`
- TECH_READ_CENTER: `{tech_read_center}`
- TECH_DASHBOARD: `{tech_dashboard}`
- SIGNAL_SUMMARY: `{signal_summary}`
- STRATEGY_SUMMARY: `{strategy_summary}`
- FORWARD_SUMMARY: `{forward_summary}`
- STALE_AUDIT: `{stale_audit_path}`
"""

    write_text(report_path, report)
    write_text(global_report_path, report)

    read_first = f"""V18.6E FINAL READ CENTER WITH TECHNICAL READ FIRST

STATUS:
OK_FINAL_READ_CENTER_WITH_TECHNICAL_READY

TECH_LATEST_PRICE_DATE:
{meta.get("latest_date", "")}

TECH_FRESH_ROWS:
{meta.get("fresh_rows", 0)}

TECH_STALE_ROWS:
{meta.get("stale_rows", 0)}

VIX:
{meta.get("vix_close", np.nan)} / {meta.get("vix_regime", "VIX_UNKNOWN")}

CURRENT_TECHNICAL_COUNTS:
WATCH_POSITIVE={meta.get("WATCH_POSITIVE", 0)}
PULLBACK_WATCH={meta.get("PULLBACK_WATCH", 0)}
BB_SQUEEZE={meta.get("BB_SQUEEZE", 0)}
BREAKOUT_CONTINUATION={meta.get("BREAKOUT_CONTINUATION", 0)}
EXHAUSTION_RISK={meta.get("EXHAUSTION_RISK", 0)}
OVERHEAT_UNCLASSIFIED={meta.get("OVERHEAT_UNCLASSIFIED", 0)}
OLD_OVERHEAT={meta.get("OLD_OVERHEAT", 0)}

OFFICIAL_DECISION_IMPACT:
NONE

READ:
{report_path}

GLOBAL_READ:
{global_report_path}
"""

    write_text(read_first_path, read_first)
    write_text(global_read_first_path, read_first)

    print("")
    print("=== V18.6E FINAL READ CENTER WITH TECHNICAL READY ===")
    print(f"MAIN_READ_FIRST_FOUND: {main_read_first.exists()}")
    print(f"MAIN_READ_CENTER_FOUND: {main_read_center.exists()}")
    print(f"TECHNICAL_DASHBOARD_FOUND: {tech_dashboard.exists()}")
    print(f"TECH_LATEST_PRICE_DATE: {meta.get('latest_date', '')}")
    print(f"TECH_FRESH_ROWS: {meta.get('fresh_rows', 0)}")
    print(f"TECH_STALE_ROWS: {meta.get('stale_rows', 0)}")
    print(f"VIX_CLOSE: {meta.get('vix_close', np.nan)}")
    print(f"VIX_REGIME: {meta.get('vix_regime', 'VIX_UNKNOWN')}")
    print(f"WATCH_POSITIVE_COUNT: {meta.get('WATCH_POSITIVE', 0)}")
    print(f"PULLBACK_WATCH_COUNT: {meta.get('PULLBACK_WATCH', 0)}")
    print(f"BB_SQUEEZE_COUNT: {meta.get('BB_SQUEEZE', 0)}")
    print(f"BREAKOUT_CONTINUATION_COUNT: {meta.get('BREAKOUT_CONTINUATION', 0)}")
    print(f"EXHAUSTION_RISK_COUNT: {meta.get('EXHAUSTION_RISK', 0)}")
    print(f"OVERHEAT_UNCLASSIFIED_COUNT: {meta.get('OVERHEAT_UNCLASSIFIED', 0)}")
    print(f"OLD_OVERHEAT_COUNT: {meta.get('OLD_OVERHEAT', 0)}")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"READ_CENTER: {report_path}")
    print(f"READ_FIRST: {read_first_path}")


if __name__ == "__main__":
    main()
