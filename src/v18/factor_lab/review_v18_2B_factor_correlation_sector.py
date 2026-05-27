from __future__ import annotations
import itertools
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
VERSION = "V18.2B"
VAL_DIR = ROOT / "outputs" / "v18" / "factor_validation"
LAB_DIR = ROOT / "outputs" / "v18" / "factor_lab"
MANIFEST_DIR = ROOT / "outputs" / "v18" / "manifests"
SUMMARY_CSV = VAL_DIR / "V18_2A_FACTOR_VALIDATION_SUMMARY.csv"
CURRENT_VALUES = LAB_DIR / "V18_1B_FACTOR_VALUES_CURRENT.csv"
OUT_REVIEW = VAL_DIR / "V18_2B_FACTOR_PROMOTION_REVIEW.csv"
OUT_CORR_SPEARMAN = VAL_DIR / "V18_2B_FACTOR_CORRELATION_SPEARMAN.csv"
OUT_CORR_PEARSON = VAL_DIR / "V18_2B_FACTOR_CORRELATION_PEARSON.csv"
OUT_REDUNDANCY = VAL_DIR / "V18_2B_FACTOR_REDUNDANCY_FLAGS.csv"
OUT_SECTOR = VAL_DIR / "V18_2B_FACTOR_TOP20_SECTOR_EXPOSURE.csv"
OUT_MD = VAL_DIR / "V18_2B_FACTOR_CORRELATION_AND_SECTOR_REPORT.md"
READ_FIRST = VAL_DIR / "V18_2B_READ_FIRST.txt"
AUDIT_CSV = VAL_DIR / "V18_2B_AUDIT.csv"
MANIFEST = MANIFEST_DIR / "V18_2B_FACTOR_CORRELATION_SECTOR_MANIFEST.csv"

FACTOR_NAMES = {
    "F001": "REL_STRENGTH_20D",
    "F002": "REL_STRENGTH_60D",
    "F003": "VOL_ADJ_MOMENTUM_20D",
    "F004": "PULLBACK_REPAIR_20D",
    "F005": "DIST_TO_MA20",
}

SECTOR_BUCKETS = {
    "ETF_BENCHMARK": {"QQQ","XLK","SMH","SOXX","SOXL","TQQQ"},
    "SEMICONDUCTOR": {"NVDA","AMD","AVGO","INTC","QCOM","ARM","TSM","ASML","MU","MRVL","AMAT","LRCX","KLAC","ON","MCHP","MPWR","TXN","ADI","NXPI","AEHR","ICHR","WDC","STX","GFS","ENTG","TER","COHR","LSCC","ALAB"},
    "SOFTWARE_CLOUD_SECURITY": {"MSFT","CRM","NOW","SNOW","NET","ZS","DDOG","MDB","CRWD","PANW","PLTR","ADBE","TEAM","SHOP","ORCL","OKTA","ESTC","PATH","AI","APP","S","HUBS","WDAY"},
    "AI_INFRA_NETWORK_HARDWARE": {"ANET","DELL","HPE","SMCI","CSCO","CLS","FLEX","JBL","JNPR","NTAP","PSTG","CIEN","LITE"},
    "MEGACAP_INTERNET_CONSUMER": {"AAPL","GOOG","GOOGL","AMZN","META","TSLA","NFLX","UBER","ABNB","BKNG"},
    "POWER_INDUSTRIAL_ENGINEERING": {"VST","CEG","GE","GEV","ETN","PWR","FLR","EMR","HON","ROK","CAT","DE","ACM"},
    "SPACE_COMMUNICATION": {"RKLB","IRDM","ASTS","LUNR"},
    "ENERGY_MATERIALS": {"XOM","CVX","SHEL","COP","AEM","NEM","FCX","CCJ"},
}

def fail(msg: str) -> None:
    print("")
    print("V18_2B_STATUS: FAIL")
    print(f"REASON: {msg}")
    print("")
    sys.exit(1)

def ensure_dirs() -> None:
    VAL_DIR.mkdir(parents=True, exist_ok=True)
    LAB_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

def sector_for(ticker: str) -> str:
    t = str(ticker).upper().strip()
    for sector, names in SECTOR_BUCKETS.items():
        if t in names:
            return sector
    return "OTHER_UNKNOWN"

def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not SUMMARY_CSV.exists():
        fail(f"V18.2A summary missing: {SUMMARY_CSV}")
    if not CURRENT_VALUES.exists():
        fail(f"V18.1B current factor values missing: {CURRENT_VALUES}")
    summary = pd.read_csv(SUMMARY_CSV)
    current = pd.read_csv(CURRENT_VALUES)
    required_summary = {"factor_id","horizon_days","avg_rank_ic","avg_top_minus_bottom","avg_top_minus_benchmark","validation_status"}
    missing_summary = required_summary - set(summary.columns)
    if missing_summary:
        fail(f"SUMMARY_COLUMNS_MISSING: {sorted(missing_summary)}")
    required_current = {"ticker","factor_id","status"}
    missing_current = required_current - set(current.columns)
    if missing_current:
        fail(f"CURRENT_VALUE_COLUMNS_MISSING: {sorted(missing_current)}")
    return summary, current

def build_current_pivot(current: pd.DataFrame) -> pd.DataFrame:
    metric_col = "rank_metric" if "rank_metric" in current.columns else "factor_value"
    ok = current[current["status"].eq("OK")].copy()
    ok = ok[ok["factor_id"].isin(FACTOR_NAMES.keys())].copy()
    ok[metric_col] = to_num(ok[metric_col])
    ok = ok.dropna(subset=[metric_col])
    if ok.empty:
        fail("NO_OK_CURRENT_FACTOR_VALUES")
    pivot = ok.pivot_table(index="ticker", columns="factor_id", values=metric_col, aggfunc="mean")
    if pivot.shape[0] < 20 or pivot.shape[1] < 2:
        fail(f"CURRENT_FACTOR_PIVOT_TOO_SMALL: {pivot.shape}")
    return pivot

def correlation_outputs(pivot: pd.DataFrame) -> pd.DataFrame:
    spearman = pivot.corr(method="spearman")
    pearson = pivot.corr(method="pearson")
    spearman.to_csv(OUT_CORR_SPEARMAN, encoding="utf-8-sig")
    pearson.to_csv(OUT_CORR_PEARSON, encoding="utf-8-sig")
    rows = []
    for a, b in itertools.combinations(list(spearman.columns), 2):
        v = spearman.loc[a, b]
        if pd.isna(v):
            continue
        flag = "HIGH_REDUNDANCY" if abs(float(v)) >= 0.80 else "OK"
        rows.append({"factor_a": a, "factor_b": b, "spearman_corr": float(v), "abs_corr": abs(float(v)), "redundancy_flag": flag})
    red = pd.DataFrame(rows).sort_values("abs_corr", ascending=False)
    red.to_csv(OUT_REDUNDANCY, index=False, encoding="utf-8-sig")
    return red

def sector_exposure(current: pd.DataFrame) -> pd.DataFrame:
    df = current[current["status"].eq("OK")].copy()
    df = df[df["factor_id"].isin(FACTOR_NAMES.keys())].copy()
    if "factor_rank" in df.columns:
        df["sort_key"] = to_num(df["factor_rank"])
        ascending = True
    else:
        metric_col = "rank_metric" if "rank_metric" in df.columns else "factor_value"
        df["sort_key"] = to_num(df[metric_col])
        ascending = False
    rows = []
    for fid, g in df.groupby("factor_id"):
        top = g.dropna(subset=["sort_key"]).sort_values("sort_key", ascending=ascending).head(20).copy()
        if top.empty:
            continue
        top["sector_bucket"] = top["ticker"].map(sector_for)
        counts = top["sector_bucket"].value_counts()
        top_tickers = ",".join(top["ticker"].astype(str).head(10).tolist())
        for sector, count in counts.items():
            rows.append({
                "factor_id": fid,
                "factor_name": FACTOR_NAMES.get(fid, fid),
                "sector_bucket": sector,
                "top20_count": int(count),
                "top20_pct": float(count / len(top)),
                "top10_tickers": top_tickers,
            })
    out = pd.DataFrame(rows).sort_values(["factor_id","top20_count"], ascending=[True,False])
    out.to_csv(OUT_SECTOR, index=False, encoding="utf-8-sig")
    return out

def build_review(summary: pd.DataFrame, redundancy: pd.DataFrame, sector: pd.DataFrame) -> pd.DataFrame:
    s = summary.copy()
    for col in ["avg_rank_ic","avg_top_minus_bottom","avg_top_minus_benchmark","avg_top_minus_raw_equal"]:
        if col in s.columns:
            s[col] = to_num(s[col])
    rows = []
    for fid, g in s.groupby("factor_id"):
        pass_rows = int(g["validation_status"].eq("PASS_CANDIDATE").sum())
        watch_rows = int(g["validation_status"].eq("WATCH_CANDIDATE").sum())
        reject_rows = int(g["validation_status"].eq("REJECT_OR_REWORK").sum())
        best = g.sort_values("avg_rank_ic", ascending=False).iloc[0]
        high_corr_pairs = []
        if not redundancy.empty:
            rr = redundancy[(redundancy["redundancy_flag"].eq("HIGH_REDUNDANCY")) & ((redundancy["factor_a"].eq(fid)) | (redundancy["factor_b"].eq(fid)))]
            for _, r in rr.iterrows():
                other = r["factor_b"] if r["factor_a"] == fid else r["factor_a"]
                high_corr_pairs.append(f"{other}:{float(r.spearman_corr):.3f}")
        sec = sector[sector["factor_id"].eq(fid)] if not sector.empty else pd.DataFrame()
        if sec.empty:
            max_sector = "UNKNOWN"
            max_sector_pct = float("nan")
            sector_flag = "NO_SECTOR_DATA"
        else:
            top_sec = sec.sort_values("top20_pct", ascending=False).iloc[0]
            max_sector = str(top_sec["sector_bucket"])
            max_sector_pct = float(top_sec["top20_pct"])
            sector_flag = "SECTOR_CONCENTRATED" if max_sector_pct >= 0.60 else "OK"
        if pass_rows >= 2:
            rec = "SHADOW_CANDIDATE"
        elif pass_rows >= 1 or watch_rows >= 3:
            rec = "WATCH_CANDIDATE"
        else:
            rec = "REJECT_OR_REWORK"
        if high_corr_pairs and rec == "SHADOW_CANDIDATE":
            rec = "SHADOW_CANDIDATE_WITH_REDUNDANCY_REVIEW"
        elif high_corr_pairs and rec == "WATCH_CANDIDATE":
            rec = "WATCH_CANDIDATE_WITH_REDUNDANCY_REVIEW"
        if sector_flag == "SECTOR_CONCENTRATED" and rec != "REJECT_OR_REWORK":
            rec = rec + "_AND_SECTOR_REVIEW"
        rows.append({
            "factor_id": fid,
            "factor_name": FACTOR_NAMES.get(fid, fid),
            "pass_rows": pass_rows,
            "watch_rows": watch_rows,
            "reject_rows": reject_rows,
            "best_horizon_days": int(best["horizon_days"]),
            "best_avg_rank_ic": float(best["avg_rank_ic"]),
            "best_avg_top_minus_bottom": float(best["avg_top_minus_bottom"]),
            "best_avg_top_minus_benchmark": float(best["avg_top_minus_benchmark"]),
            "high_corr_pairs": ";".join(high_corr_pairs),
            "sector_top_bucket": max_sector,
            "sector_top_pct": max_sector_pct,
            "sector_flag": sector_flag,
            "recommendation": rec,
        })
    out = pd.DataFrame(rows).sort_values(["recommendation","pass_rows","best_avg_rank_ic"], ascending=[True,False,False])
    out.to_csv(OUT_REVIEW, index=False, encoding="utf-8-sig")
    return out

def md_table(df: pd.DataFrame, cols: List[str]) -> List[str]:
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, float):
                vals.append("" if math.isnan(v) else f"{v:.5f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return lines

def write_report(review: pd.DataFrame, redundancy: pd.DataFrame, sector: pd.DataFrame) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines += ["# V18.2B Factor Correlation and Sector Review", "", f"Generated: {now}", ""]
    lines += ["## 1. Status", "", "- V18_2B_STATUS: `OK_FACTOR_CORRELATION_SECTOR_REVIEW_COMPLETED`", "- OFFICIAL_DECISION_IMPACT: `NONE`", "- PROMOTION_ACTION: `NONE`", ""]
    lines += ["## 2. Factor Promotion Review", ""]
    lines += md_table(review, ["factor_id","factor_name","pass_rows","watch_rows","reject_rows","best_horizon_days","best_avg_rank_ic","high_corr_pairs","sector_top_bucket","sector_top_pct","recommendation"])
    lines += ["", "## 3. Redundancy Flags", ""]
    if redundancy.empty:
        lines += ["No redundancy pairs were computed.", ""]
    else:
        lines += md_table(redundancy.head(20), ["factor_a","factor_b","spearman_corr","redundancy_flag"])
    lines += ["", "## 4. Current Top20 Sector Exposure", ""]
    if sector.empty:
        lines += ["No sector exposure rows were computed.", ""]
    else:
        lines += md_table(sector, ["factor_id","factor_name","sector_bucket","top20_count","top20_pct","top10_tickers"])
    lines += ["", "## 5. Interpretation", "", "- This is still research-only.", "- F002 is expected to be the main shadow candidate if correlation and sector concentration are acceptable.", "- F004 and F005 should not be promoted in their current definitions.", "", "## 6. Next Step", "", "V18.3A should create a shadow daily report using only approved shadow candidates, without changing V17.8D official decisions.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

def write_read_first(review: pd.DataFrame, redundancy: pd.DataFrame, sector: pd.DataFrame) -> None:
    shadow_like = int(review["recommendation"].astype(str).str.startswith("SHADOW_CANDIDATE").sum())
    watch_like = int(review["recommendation"].astype(str).str.startswith("WATCH_CANDIDATE").sum())
    reject_like = int(review["recommendation"].eq("REJECT_OR_REWORK").sum())
    high_corr = int(redundancy["redundancy_flag"].eq("HIGH_REDUNDANCY").sum()) if not redundancy.empty else 0
    concentrated = int(sector["top20_pct"].ge(0.60).sum()) if not sector.empty else 0
    lines = [
        "=== V18.2B FACTOR CORRELATION AND SECTOR REVIEW READ FIRST ===",
        "",
        "STATUS:",
        "V18_2B_STATUS: OK_FACTOR_CORRELATION_SECTOR_REVIEW_COMPLETED",
        "",
        "OFFICIAL_DECISION_IMPACT:",
        "NONE",
        "",
        "PROMOTION_ACTION:",
        "NONE",
        "",
        "REVIEW SUMMARY:",
        f"SHADOW_CANDIDATE_LIKE_COUNT: {shadow_like}",
        f"WATCH_CANDIDATE_LIKE_COUNT: {watch_like}",
        f"REJECT_OR_REWORK_COUNT: {reject_like}",
        f"HIGH_REDUNDANCY_PAIR_COUNT: {high_corr}",
        f"SECTOR_CONCENTRATED_ROW_COUNT: {concentrated}",
        "",
        "OUTPUTS:",
        str(OUT_MD),
        str(OUT_REVIEW),
        str(OUT_CORR_SPEARMAN),
        str(OUT_REDUNDANCY),
        str(OUT_SECTOR),
        "",
        "NEXT_STEP:",
        "V18.3A_FACTOR_SHADOW_DAILY_REPORT",
        "",
        "IMPORTANT:",
        "No factor has been promoted. V17.8D official BUY / NO_BUY remains unchanged.",
    ]
    READ_FIRST.write_text("\n".join(lines), encoding="utf-8")

def write_audit(review: pd.DataFrame, redundancy: pd.DataFrame, sector: pd.DataFrame) -> None:
    row = {
        "version": VERSION,
        "status": "OK_FACTOR_CORRELATION_SECTOR_REVIEW_COMPLETED",
        "official_decision_impact": "NONE",
        "promotion_action": "NONE",
        "review_rows": len(review),
        "redundancy_rows": len(redundancy),
        "sector_rows": len(sector),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    pd.DataFrame([row]).to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")

def write_manifest() -> None:
    rows = []
    for p in [READ_FIRST, OUT_MD, OUT_REVIEW, OUT_CORR_SPEARMAN, OUT_CORR_PEARSON, OUT_REDUNDANCY, OUT_SECTOR, AUDIT_CSV]:
        if p.exists():
            rows.append({"version": VERSION, "path": str(p), "length_bytes": p.stat().st_size, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "purpose": "factor_correlation_sector_review"})
    pd.DataFrame(rows).to_csv(MANIFEST, index=False, encoding="utf-8-sig")

def main() -> None:
    ensure_dirs()
    print("")
    print("=== V18.2B FACTOR CORRELATION AND SECTOR REVIEW START ===")
    summary, current = load_inputs()
    pivot = build_current_pivot(current)
    redundancy = correlation_outputs(pivot)
    sector = sector_exposure(current)
    review = build_review(summary, redundancy, sector)
    write_report(review, redundancy, sector)
    write_read_first(review, redundancy, sector)
    write_audit(review, redundancy, sector)
    write_manifest()
    print("")
    print("=== V18.2B FACTOR CORRELATION AND SECTOR REVIEW READY ===")
    print("V18_2B_STATUS: OK_FACTOR_CORRELATION_SECTOR_REVIEW_COMPLETED")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("PROMOTION_ACTION: NONE")
    print(f"REVIEW_ROWS: {len(review)}")
    print(f"REDUNDANCY_ROWS: {len(redundancy)}")
    print(f"SECTOR_ROWS: {len(sector)}")
    print("")
    print("READ_FIRST:")
    print(str(READ_FIRST))
    print("")
    print("REPORT:")
    print(str(OUT_MD))
    print("")
    print("REVIEW_CSV:")
    print(str(OUT_REVIEW))
    print("")
    print("NEXT_VERSION:")
    print("V18.3A_FACTOR_SHADOW_DAILY_REPORT")
    print("")
    print("=== DONE ===")

if __name__ == "__main__":
    main()
