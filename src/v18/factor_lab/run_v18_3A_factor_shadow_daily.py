from __future__ import annotations
import math
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
VERSION = "V18.3A"
LAB_DIR = ROOT / "outputs" / "v18" / "factor_lab"
VAL_DIR = ROOT / "outputs" / "v18" / "factor_validation"
OUT_DIR = ROOT / "outputs" / "v18" / "factor_shadow"
MANIFEST_DIR = ROOT / "outputs" / "v18" / "manifests"
CURRENT_VALUES = LAB_DIR / "V18_1B_FACTOR_VALUES_CURRENT.csv"
REVIEW_CSV = VAL_DIR / "V18_2B_FACTOR_PROMOTION_REVIEW.csv"
OUT_CSV = OUT_DIR / "V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv"
OUT_MD = OUT_DIR / "V18_3A_FACTOR_SHADOW_DAILY_REPORT.md"
READ_FIRST = OUT_DIR / "V18_3A_READ_FIRST.txt"
AUDIT_CSV = OUT_DIR / "V18_3A_FACTOR_SHADOW_AUDIT.csv"
MANIFEST = MANIFEST_DIR / "V18_3A_FACTOR_SHADOW_DAILY_MANIFEST.csv"

def fail(msg: str) -> None:
    print("")
    print("V18_3A_STATUS: FAIL")
    print(f"REASON: {msg}")
    print("")
    sys.exit(1)

def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def load_inputs():
    if not CURRENT_VALUES.exists():
        fail(f"CURRENT_FACTOR_VALUES_MISSING: {CURRENT_VALUES}. Run V18.1B first.")
    if not REVIEW_CSV.exists():
        fail(f"PROMOTION_REVIEW_MISSING: {REVIEW_CSV}. Run V18.2B first.")
    values = pd.read_csv(CURRENT_VALUES)
    review = pd.read_csv(REVIEW_CSV)
    if "factor_id" not in values.columns or "ticker" not in values.columns:
        fail("CURRENT_FACTOR_VALUES_BAD_SCHEMA")
    if "factor_id" not in review.columns or "recommendation" not in review.columns:
        fail("PROMOTION_REVIEW_BAD_SCHEMA")
    return values, review

def choose_shadow_factors(review: pd.DataFrame):
    r = review.copy()
    r["recommendation"] = r["recommendation"].astype(str)
    shadow = r[r["recommendation"].str.startswith("SHADOW_CANDIDATE")].copy()
    if shadow.empty:
        shadow = r[r["recommendation"].str.startswith("WATCH_CANDIDATE")].copy()
    if shadow.empty:
        fail("NO_SHADOW_OR_WATCH_FACTORS_AVAILABLE")
    shadow = shadow.sort_values(["pass_rows","best_avg_rank_ic"], ascending=[False,False])
    return shadow["factor_id"].astype(str).tolist(), shadow

def build_shadow(values: pd.DataFrame, shadow_ids: list[str]) -> pd.DataFrame:
    v = values.copy()
    v = v[v["factor_id"].astype(str).isin(shadow_ids)].copy()
    v = v[v["status"].astype(str).eq("OK")].copy()
    if v.empty:
        fail("NO_OK_VALUES_FOR_SHADOW_FACTORS")
    if "factor_zscore" not in v.columns:
        metric = "rank_metric" if "rank_metric" in v.columns else "factor_value"
        v[metric] = to_num(v[metric])
        v["factor_zscore"] = v.groupby("factor_id")[metric].transform(lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) and x.std(ddof=0) > 0 else 0)
    v["factor_zscore"] = to_num(v["factor_zscore"])
    v["factor_rank"] = to_num(v["factor_rank"]) if "factor_rank" in v.columns else None
    pivot = v.pivot_table(index="ticker", columns="factor_id", values="factor_zscore", aggfunc="mean")
    pivot["shadow_score"] = pivot.mean(axis=1)
    pivot["shadow_factor_count"] = pivot.drop(columns=["shadow_score"]).notna().sum(axis=1)
    out = pivot.reset_index().sort_values("shadow_score", ascending=False)
    out.insert(0, "shadow_date", datetime.now().strftime("%Y-%m-%d"))
    out.insert(1, "version", VERSION)
    out["official_decision_impact"] = "NONE"
    out["shadow_only"] = "YES"
    out["shadow_factor_ids"] = ",".join(shadow_ids)
    out["shadow_rank"] = range(1, len(out) + 1)
    cols = ["shadow_date","version","shadow_rank","ticker","shadow_score","shadow_factor_count","shadow_factor_ids","official_decision_impact","shadow_only"] + shadow_ids
    cols = [c for c in cols if c in out.columns]
    return out[cols]

def write_md(shadow: pd.DataFrame, selected_review: pd.DataFrame):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines += ["# V18.3A Factor Shadow Daily Report", "", f"Generated: {now}", ""]
    lines += ["## 1. Status", "", "- V18_3A_STATUS: `OK_FACTOR_SHADOW_DAILY_READY`", "- OFFICIAL_DECISION_IMPACT: `NONE`", "- PROMOTION_ACTION: `NONE`", "- SHADOW_ONLY: `YES`", ""]
    lines += ["## 2. Selected Shadow Factors", "", "| factor_id | factor_name | pass_rows | watch_rows | best_horizon_days | best_avg_rank_ic | recommendation |", "|---|---|---:|---:|---:|---:|---|"]
    for _, r in selected_review.iterrows():
        lines.append(f"| {r.get('factor_id','')} | {r.get('factor_name','')} | {r.get('pass_rows','')} | {r.get('watch_rows','')} | {r.get('best_horizon_days','')} | {float(r.get('best_avg_rank_ic',0)):.5f} | {r.get('recommendation','')} |")
    lines += ["", "## 3. Top 30 Shadow Names", "", "| shadow_rank | ticker | shadow_score | factor_count |", "|---:|---|---:|---:|"]
    for _, r in shadow.head(30).iterrows():
        lines.append(f"| {int(r.shadow_rank)} | {r.ticker} | {float(r.shadow_score):.5f} | {int(r.shadow_factor_count)} |")
    lines += ["", "## 4. Important Rule", "", "This is a shadow-only factor report. It does not modify V17.8D official BUY / NO_BUY decisions.", "", "## 5. Next Step", "", "V18.3B should compare this shadow list with V17.8D worth-review/official candidates and track future outcomes.", ""]
    OUT_MD.write_text("\\n".join(lines), encoding="utf-8")

def write_read_first(shadow: pd.DataFrame, selected_review: pd.DataFrame):
    lines = [
        "=== V18.3A FACTOR SHADOW DAILY READ FIRST ===",
        "",
        "STATUS:",
        "V18_3A_STATUS: OK_FACTOR_SHADOW_DAILY_READY",
        "",
        "OFFICIAL_DECISION_IMPACT:",
        "NONE",
        "",
        "PROMOTION_ACTION:",
        "NONE",
        "",
        "SHADOW_ONLY:",
        "YES",
        "",
        "SELECTED_FACTORS:",
        ",".join(selected_review["factor_id"].astype(str).tolist()),
        "",
        "SUMMARY:",
        f"SHADOW_NAME_COUNT: {len(shadow)}",
        f"TOP1: {shadow.iloc[0]['ticker'] if len(shadow) else ''}",
        "",
        "OUTPUTS:",
        str(OUT_MD),
        str(OUT_CSV),
        str(AUDIT_CSV),
        "",
        "NEXT_STEP:",
        "V18.3B_SHADOW_VS_OFFICIAL_CANDIDATE_COMPARE_AND_OUTCOME_TRACKER",
        "",
        "IMPORTANT:",
        "This report is observation only. No official factor promotion has occurred.",
    ]
    READ_FIRST.write_text("\\n".join(lines), encoding="utf-8")

def write_audit(shadow: pd.DataFrame, selected_review: pd.DataFrame):
    row = {
        "version": VERSION,
        "status": "OK_FACTOR_SHADOW_DAILY_READY",
        "official_decision_impact": "NONE",
        "promotion_action": "NONE",
        "shadow_only": "YES",
        "selected_factors": ",".join(selected_review["factor_id"].astype(str).tolist()),
        "shadow_name_count": len(shadow),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    pd.DataFrame([row]).to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")

def write_manifest():
    rows = []
    for p in [READ_FIRST, OUT_MD, OUT_CSV, AUDIT_CSV]:
        if p.exists():
            rows.append({"version": VERSION, "path": str(p), "length_bytes": p.stat().st_size, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "purpose": "factor_shadow_daily"})
    pd.DataFrame(rows).to_csv(MANIFEST, index=False, encoding="utf-8-sig")

def main():
    ensure_dirs()
    print("")
    print("=== V18.3A FACTOR SHADOW DAILY START ===")
    values, review = load_inputs()
    shadow_ids, selected_review = choose_shadow_factors(review)
    shadow = build_shadow(values, shadow_ids)
    shadow.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    write_md(shadow, selected_review)
    write_read_first(shadow, selected_review)
    write_audit(shadow, selected_review)
    write_manifest()
    print("")
    print("=== V18.3A FACTOR SHADOW DAILY READY ===")
    print("V18_3A_STATUS: OK_FACTOR_SHADOW_DAILY_READY")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("PROMOTION_ACTION: NONE")
    print("SHADOW_ONLY: YES")
    print(f"SELECTED_FACTORS: {' ,'.join(shadow_ids)}")
    print(f"SHADOW_NAME_COUNT: {len(shadow)}")
    print("")
    print("READ_FIRST:")
    print(str(READ_FIRST))
    print("")
    print("REPORT:")
    print(str(OUT_MD))
    print("")
    print("SHADOW_CSV:")
    print(str(OUT_CSV))
    print("")
    print("NEXT_VERSION:")
    print("V18.3B_SHADOW_VS_OFFICIAL_CANDIDATE_COMPARE_AND_OUTCOME_TRACKER")
    print("")
    print("=== DONE ===")

if __name__ == "__main__":
    main()
