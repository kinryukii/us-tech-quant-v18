from __future__ import annotations
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
VERSION = "V18.2A"
STATE_DIR = ROOT / "state" / "v18"
OUT_DIR = ROOT / "outputs" / "v18" / "factor_validation"
MANIFEST_DIR = ROOT / "outputs" / "v18" / "manifests"
UNIVERSE_SNAPSHOT = STATE_DIR / "raw105_universe_for_factor_lab.csv"
FACTOR_REGISTRY = STATE_DIR / "factor_registry.csv"
OUT_SUMMARY = OUT_DIR / "V18_2A_FACTOR_VALIDATION_SUMMARY.csv"
OUT_DETAIL = OUT_DIR / "V18_2A_FACTOR_VALIDATION_DETAIL.csv"
OUT_MD = OUT_DIR / "V18_2A_FACTOR_VALIDATION_REPORT.md"
READ_FIRST = OUT_DIR / "V18_2A_READ_FIRST.txt"
AUDIT_CSV = OUT_DIR / "V18_2A_FACTOR_VALIDATION_AUDIT.csv"
MANIFEST = MANIFEST_DIR / "V18_2A_FACTOR_VALIDATION_MANIFEST.csv"
BENCHMARK = "QQQ"
HORIZONS = [1, 3, 5, 10, 20]
STEP_DAYS = 5

def fail(msg: str, code: int = 1) -> None:
    print("")
    print("V18_2A_STATUS: FAIL")
    print(f"REASON: {msg}")
    print("")
    sys.exit(code)

def ensure_dirs() -> None:
    for p in [STATE_DIR, OUT_DIR, MANIFEST_DIR]:
        p.mkdir(parents=True, exist_ok=True)

def clean_ticker(x) -> str | None:
    if x is None:
        return None
    try:
        if isinstance(x, float) and math.isnan(x):
            return None
    except Exception:
        pass
    s = str(x).strip().upper().replace(".", "-")
    if not s or s in {"NAN", "NONE", "NULL", "TICKER", "SYMBOL"}:
        return None
    if len(s) > 12:
        return None
    return s

def load_universe() -> Tuple[List[str], str]:
    if UNIVERSE_SNAPSHOT.exists():
        df = pd.read_csv(UNIVERSE_SNAPSHOT)
        col = "ticker" if "ticker" in df.columns else df.columns[0]
        tickers = sorted(set(filter(None, [clean_ticker(x) for x in df[col].tolist()])))
        if len(tickers) >= 50:
            return tickers, str(UNIVERSE_SNAPSHOT)
    fallback = ROOT / "outputs" / "v17" / "raw105_decision" / "v17_8A_raw105_full_decision_daily.csv"
    if fallback.exists():
        df = pd.read_csv(fallback)
        col = "ticker" if "ticker" in df.columns else None
        if col is not None:
            tickers = sorted(set(filter(None, [clean_ticker(x) for x in df[col].tolist()])))
            if len(tickers) >= 50:
                return tickers, str(fallback)
    fail("UNIVERSE_NOT_FOUND. Run V18.1B first.")

def download_close(tickers: List[str]) -> pd.DataFrame:
    try:
        import yfinance as yf
    except Exception as e:
        fail(f"YFINANCE_IMPORT_FAILED: {e}")
    all_tickers = sorted(set(tickers + [BENCHMARK]))
    print(f"PRICE_DOWNLOAD_TICKER_COUNT: {len(all_tickers)}")
    data = yf.download(tickers=all_tickers, period="3y", interval="1d", auto_adjust=True, progress=False, threads=True, group_by="column")
    if data is None or data.empty:
        fail("YFINANCE_DOWNLOAD_EMPTY")
    if isinstance(data.columns, pd.MultiIndex):
        lvl0 = list(data.columns.get_level_values(0))
        if "Close" in lvl0:
            close = data["Close"].copy()
        elif "Adj Close" in lvl0:
            close = data["Adj Close"].copy()
        else:
            fail("CLOSE_LEVEL_MISSING")
    else:
        if "Close" not in data.columns:
            fail("CLOSE_COLUMN_MISSING")
        close = data[["Close"]].copy()
        close.columns = all_tickers[:1]
    close = close.sort_index().dropna(how="all")
    if close.empty:
        fail("CLOSE_EMPTY_AFTER_CLEAN")
    return close

def calc_metrics(s: pd.Series, qqq20: float, qqq60: float) -> Dict[str, float]:
    s = s.dropna()
    if len(s) < 65:
        return {}
    last = float(s.iloc[-1])
    ret20 = float(s.iloc[-1] / s.iloc[-21] - 1.0)
    ret60 = float(s.iloc[-1] / s.iloc[-61] - 1.0)
    daily = s.pct_change().dropna()
    vol20 = float(daily.tail(20).std())
    ma5 = float(s.tail(5).mean())
    ma10 = float(s.tail(10).mean())
    ma20 = float(s.tail(20).mean())
    high20 = float(s.tail(20).max())
    dd20 = last / high20 - 1.0 if high20 > 0 else 0.0
    dist_ma20 = last / ma20 - 1.0 if ma20 > 0 else 0.0
    reclaim_ma10 = 1.0 if last > ma10 else 0.0
    reclaim_ma5 = 1.0 if last > ma5 else 0.0
    pullback_depth_ok = 1.0 if -0.15 <= dd20 <= -0.02 else 0.0
    pullback_repair = reclaim_ma10 + 0.5 * reclaim_ma5 + pullback_depth_ok + dd20
    vol_adj = ret20 / vol20 if vol20 > 0 else float("nan")
    dist_rank = -abs(dist_ma20 - 0.03)
    return {
        "F001": ret20 - qqq20,
        "F002": ret60 - qqq60,
        "F003": vol_adj,
        "F004": pullback_repair,
        "F005": dist_rank,
    }

def spearman_ic(x: pd.Series, y: pd.Series) -> float:
    xr = x.rank(method="average")
    yr = y.rank(method="average")
    v = xr.corr(yr)
    return float(v) if pd.notna(v) else float("nan")

def validate(close: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    if BENCHMARK not in close.columns:
        fail("QQQ_BENCHMARK_MISSING")
    n = len(close)
    if n < 180:
        fail(f"INSUFFICIENT_PRICE_HISTORY: {n}")
    rows = []
    max_h = max(HORIZONS)
    start_i = 65
    end_i = n - max_h - 1
    print(f"VALIDATION_DATE_COUNT_APPROX: {max(0, (end_i - start_i) // STEP_DAYS)}")
    for i in range(start_i, end_i, STEP_DAYS):
        anchor_date = close.index[i]
        q = close[BENCHMARK]
        if pd.isna(q.iloc[i]) or pd.isna(q.iloc[i-20]) or pd.isna(q.iloc[i-60]):
            continue
        qqq20 = float(q.iloc[i] / q.iloc[i-20] - 1.0)
        qqq60 = float(q.iloc[i] / q.iloc[i-60] - 1.0)
        metric_rows = []
        for t in tickers:
            if t not in close.columns:
                continue
            if pd.isna(close[t].iloc[i]):
                continue
            hist = close[t].iloc[:i+1]
            m = calc_metrics(hist, qqq20, qqq60)
            if not m:
                continue
            metric_rows.append({"ticker": t, **m})
        if len(metric_rows) < 30:
            continue
        metric_df = pd.DataFrame(metric_rows).set_index("ticker")
        for h in HORIZONS:
            q_now = q.iloc[i]
            q_future = q.iloc[i+h]
            if pd.isna(q_now) or pd.isna(q_future):
                continue
            bench_ret = float(q_future / q_now - 1.0)
            fwd = {}
            for t in metric_df.index:
                p0 = close[t].iloc[i] if t in close.columns else float("nan")
                p1 = close[t].iloc[i+h] if t in close.columns else float("nan")
                if pd.notna(p0) and pd.notna(p1) and p0 > 0:
                    fwd[t] = float(p1 / p0 - 1.0)
            if len(fwd) < 30:
                continue
            fwd_s = pd.Series(fwd, name="fwd_return")
            raw_eq = float(fwd_s.mean())
            for fid in ["F001", "F002", "F003", "F004", "F005"]:
                x = metric_df[fid].replace([float("inf"), -float("inf")], pd.NA).dropna()
                joined = pd.concat([x.rename("factor"), fwd_s], axis=1).dropna()
                if len(joined) < 30:
                    continue
                joined = joined.sort_values("factor", ascending=False)
                qn = max(1, int(len(joined) * 0.2))
                top = joined.head(qn)["fwd_return"]
                bottom = joined.tail(qn)["fwd_return"]
                ic = spearman_ic(joined["factor"], joined["fwd_return"])
                rows.append({
                    "anchor_date": str(anchor_date.date()),
                    "factor_id": fid,
                    "horizon_days": h,
                    "obs_count": int(len(joined)),
                    "rank_ic": ic,
                    "top_mean_return": float(top.mean()),
                    "bottom_mean_return": float(bottom.mean()),
                    "top_minus_bottom": float(top.mean() - bottom.mean()),
                    "benchmark_return": bench_ret,
                    "top_minus_benchmark": float(top.mean() - bench_ret),
                    "raw_equal_return": raw_eq,
                    "top_minus_raw_equal": float(top.mean() - raw_eq),
                })
    if not rows:
        fail("NO_VALIDATION_ROWS_CREATED")
    return pd.DataFrame(rows)

def summarize(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (fid, h), g in detail.groupby(["factor_id", "horizon_days"]):
        ic = pd.to_numeric(g["rank_ic"], errors="coerce").dropna()
        tmb = pd.to_numeric(g["top_minus_bottom"], errors="coerce").dropna()
        tvb = pd.to_numeric(g["top_minus_benchmark"], errors="coerce").dropna()
        tvr = pd.to_numeric(g["top_minus_raw_equal"], errors="coerce").dropna()
        avg_ic = float(ic.mean()) if len(ic) else float("nan")
        pos_ic = float((ic > 0).mean()) if len(ic) else float("nan")
        avg_tmb = float(tmb.mean()) if len(tmb) else float("nan")
        avg_tvb = float(tvb.mean()) if len(tvb) else float("nan")
        avg_tvr = float(tvr.mean()) if len(tvr) else float("nan")
        if avg_ic > 0.03 and avg_tmb > 0 and avg_tvb > 0:
            status = "PASS_CANDIDATE"
        elif avg_ic > 0 and avg_tmb > 0:
            status = "WATCH_CANDIDATE"
        else:
            status = "REJECT_OR_REWORK"
        rows.append({
            "factor_id": fid,
            "horizon_days": h,
            "validation_dates": int(g["anchor_date"].nunique()),
            "avg_obs_count": float(g["obs_count"].mean()),
            "avg_rank_ic": avg_ic,
            "rank_ic_positive_rate": pos_ic,
            "avg_top_minus_bottom": avg_tmb,
            "avg_top_minus_benchmark": avg_tvb,
            "avg_top_minus_raw_equal": avg_tvr,
            "validation_status": status,
        })
    return pd.DataFrame(rows).sort_values(["factor_id", "horizon_days"])

def write_report(summary: pd.DataFrame, detail: pd.DataFrame, universe_count: int, source: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines += ["# V18.2A Factor Validation Report", "", f"Generated: {now}", ""]
    lines += ["## 1. Status", "", "- V18_2A_STATUS: `OK_FACTOR_VALIDATION_COMPLETED`", "- OFFICIAL_DECISION_IMPACT: `NONE`", f"- UNIVERSE_COUNT: `{universe_count}`", f"- UNIVERSE_SOURCE: `{source}`", "- VALIDATION_METHOD: `rolling historical factor recomputation, forward returns, rank IC, top-bottom spread, top-vs-QQQ`", ""]
    lines += ["## 2. Important Rule", "", "This report is research-only. No factor is promoted by this script. V17.8D official BUY / NO_BUY logic is unchanged.", ""]
    lines += ["## 3. Summary", "", "| factor | horizon | dates | avg_ic | ic_positive | top-bottom | top-QQQ | top-raw_eq | status |", "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for _, r in summary.iterrows():
        lines.append(f"| {r.factor_id} | {int(r.horizon_days)} | {int(r.validation_dates)} | {r.avg_rank_ic:.5f} | {r.rank_ic_positive_rate:.3f} | {r.avg_top_minus_bottom:.5f} | {r.avg_top_minus_benchmark:.5f} | {r.avg_top_minus_raw_equal:.5f} | {r.validation_status} |")
    lines += ["", "## 4. Interpretation", "", "- PASS_CANDIDATE means the factor showed positive average rank IC, positive top-bottom spread, and positive top-vs-QQQ excess return in this first historical check.", "- WATCH_CANDIDATE means the factor has partial evidence but should not be promoted yet.", "- REJECT_OR_REWORK means the factor does not currently show enough standalone evidence.", "", "## 5. Next Step", "", "V18.2B should add factor correlation checks and sector-aware validation before any shadow promotion.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

def write_read_first(summary: pd.DataFrame, detail: pd.DataFrame, universe_count: int, source: str) -> None:
    pass_count = int(summary["validation_status"].eq("PASS_CANDIDATE").sum())
    watch_count = int(summary["validation_status"].eq("WATCH_CANDIDATE").sum())
    reject_count = int(summary["validation_status"].eq("REJECT_OR_REWORK").sum())
    lines = [
        "=== V18.2A FACTOR VALIDATION READ FIRST ===",
        "",
        "STATUS:",
        "V18_2A_STATUS: OK_FACTOR_VALIDATION_COMPLETED",
        "",
        "OFFICIAL_DECISION_IMPACT:",
        "NONE",
        "",
        "UNIVERSE:",
        f"UNIVERSE_COUNT: {universe_count}",
        f"UNIVERSE_SOURCE: {source}",
        "",
        "VALIDATION SUMMARY:",
        f"SUMMARY_ROWS: {len(summary)}",
        f"DETAIL_ROWS: {len(detail)}",
        f"PASS_CANDIDATE_ROWS: {pass_count}",
        f"WATCH_CANDIDATE_ROWS: {watch_count}",
        f"REJECT_OR_REWORK_ROWS: {reject_count}",
        "",
        "OUTPUTS:",
        str(OUT_MD),
        str(OUT_SUMMARY),
        str(OUT_DETAIL),
        str(AUDIT_CSV),
        "",
        "NEXT_STEP:",
        "V18.2B_FACTOR_CORRELATION_AND_SECTOR_AWARE_VALIDATION",
        "",
        "IMPORTANT:",
        "No factor has been promoted. This is validation only.",
    ]
    READ_FIRST.write_text("\n".join(lines), encoding="utf-8")

def write_audit(summary: pd.DataFrame, detail: pd.DataFrame, universe_count: int, source: str) -> None:
    row = {
        "version": VERSION,
        "status": "OK_FACTOR_VALIDATION_COMPLETED",
        "official_decision_impact": "NONE",
        "universe_count": universe_count,
        "universe_source": source,
        "summary_rows": len(summary),
        "detail_rows": len(detail),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    pd.DataFrame([row]).to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")

def write_manifest() -> None:
    rows = []
    for p in [OUT_MD, OUT_SUMMARY, OUT_DETAIL, READ_FIRST, AUDIT_CSV]:
        if p.exists():
            rows.append({"version": VERSION, "path": str(p), "length_bytes": p.stat().st_size, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "purpose": "factor_validation"})
    pd.DataFrame(rows).to_csv(MANIFEST, index=False, encoding="utf-8-sig")

def main() -> None:
    ensure_dirs()
    if not FACTOR_REGISTRY.exists():
        fail("FACTOR_REGISTRY_MISSING. Run V18.1A first.")
    tickers, source = load_universe()
    print("")
    print("=== V18.2A FACTOR VALIDATION START ===")
    print(f"UNIVERSE_COUNT: {len(tickers)}")
    print(f"UNIVERSE_SOURCE: {source}")
    close = download_close(tickers)
    detail = validate(close, tickers)
    summary = summarize(detail)
    detail.to_csv(OUT_DETAIL, index=False, encoding="utf-8-sig")
    summary.to_csv(OUT_SUMMARY, index=False, encoding="utf-8-sig")
    write_report(summary, detail, len(tickers), source)
    write_read_first(summary, detail, len(tickers), source)
    write_audit(summary, detail, len(tickers), source)
    write_manifest()
    print("")
    print("=== V18.2A FACTOR VALIDATION READY ===")
    print("V18_2A_STATUS: OK_FACTOR_VALIDATION_COMPLETED")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"UNIVERSE_COUNT: {len(tickers)}")
    print(f"SUMMARY_ROWS: {len(summary)}")
    print(f"DETAIL_ROWS: {len(detail)}")
    print("")
    print("READ_FIRST:")
    print(str(READ_FIRST))
    print("")
    print("REPORT:")
    print(str(OUT_MD))
    print("")
    print("SUMMARY_CSV:")
    print(str(OUT_SUMMARY))
    print("")
    print("NEXT_VERSION:")
    print("V18.2B_FACTOR_CORRELATION_AND_SECTOR_AWARE_VALIDATION")
    print("")
    print("=== DONE ===")

if __name__ == "__main__":
    main()
