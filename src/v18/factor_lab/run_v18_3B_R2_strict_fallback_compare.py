from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
VERSION = "V18.3B-R2"
SHADOW_DIR = ROOT / "outputs" / "v18" / "factor_shadow"
STATE_DIR = ROOT / "state" / "v18"
SHADOW_CSV = SHADOW_DIR / "V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv"
OUT_COMPARE = SHADOW_DIR / "V18_3B_R2_SHADOW_OFFICIAL_COMPARE_CURRENT.csv"
OUT_MD = SHADOW_DIR / "V18_3B_R2_SHADOW_OFFICIAL_COMPARE_REPORT.md"
READ_FIRST = SHADOW_DIR / "V18_3B_R2_READ_FIRST.txt"
AUDIT_CSV = SHADOW_DIR / "V18_3B_R2_AUDIT.csv"
TRACKER = STATE_DIR / "factor_shadow_outcome_tracker.csv"
HORIZONS = [1, 3, 5, 10, 20]
STRICT_OFFICIAL_LOCKED = {"ANET","ARM","CRWV","DELL","FLR","NET","QCOM","SNOW","VST","ZS"}

def fail(msg):
    print("")
    print("V18_3B_R2_STATUS: FAIL")
    print("REASON: " + str(msg))
    print("")
    sys.exit(1)

def clean_ticker(x):
    return str(x).strip().upper().replace(".", "-")

def load_shadow():
    if not SHADOW_CSV.exists():
        fail("SHADOW_CSV_MISSING. Run V18.3A first.")
    df = pd.read_csv(SHADOW_CSV)
    need = {"ticker","shadow_rank","shadow_score","shadow_factor_ids"}
    missing = need - set(df.columns)
    if missing:
        fail("SHADOW_COLUMNS_MISSING: " + str(sorted(missing)))
    df = df.copy()
    df["ticker"] = df["ticker"].map(clean_ticker)
    df["shadow_rank"] = pd.to_numeric(df["shadow_rank"], errors="coerce").astype("Int64")
    df["shadow_score"] = pd.to_numeric(df["shadow_score"], errors="coerce")
    df = df.dropna(subset=["ticker","shadow_rank"])
    return df.sort_values("shadow_rank")

def build_compare(shadow):
    df = shadow.copy()
    df["official_source"] = "STRICT_CONFIRMED_V17_LOCKED_10_FALLBACK"
    df["official_actionable_buy"] = False
    df["official_worth_review_locked"] = df["ticker"].isin(STRICT_OFFICIAL_LOCKED)
    df["official_match_flag"] = df["official_worth_review_locked"]
    df["shadow_top30_flag"] = pd.to_numeric(df["shadow_rank"], errors="coerce").le(30)
    def bucket(r):
        if r["shadow_top30_flag"] and r["official_match_flag"]:
            return "SHADOW_TOP30_AND_OFFICIAL_REVIEW"
        if r["shadow_top30_flag"] and not r["official_match_flag"]:
            return "SHADOW_TOP30_ONLY"
        if (not r["shadow_top30_flag"]) and r["official_match_flag"]:
            return "OFFICIAL_REVIEW_NOT_SHADOW_TOP30"
        return "OTHER"
    df["compare_bucket"] = df.apply(bucket, axis=1)
    df["official_status_bucket"] = df["official_worth_review_locked"].map(lambda x: "OFFICIAL_WORTH_REVIEW_LOCKED" if x else "NO_OFFICIAL_CANDIDATE_FLAG")
    return df.sort_values("shadow_rank")

def backup_tracker():
    if not TRACKER.exists():
        return "NONE"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TRACKER.with_name(TRACKER.name + ".before_v18_3B_R2_" + stamp + ".bak")
    backup.write_bytes(TRACKER.read_bytes())
    return str(backup)

def rewrite_tracker_today(compare_df):
    backup = backup_tracker()
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seed = compare_df[(compare_df["shadow_top30_flag"]) | (compare_df["official_match_flag"])].copy()
    rows = []
    for _, r in seed.iterrows():
        for h in HORIZONS:
            rows.append({
                "shadow_date": today,
                "version": VERSION,
                "ticker": r["ticker"],
                "shadow_rank": int(r["shadow_rank"]),
                "shadow_score": float(r["shadow_score"]),
                "shadow_factor_ids": str(r.get("shadow_factor_ids", "")),
                "compare_bucket": r["compare_bucket"],
                "official_status_bucket": r["official_status_bucket"],
                "horizon_days": h,
                "outcome_status": "PENDING",
                "future_return": "",
                "benchmark_return": "",
                "excess_return": "",
                "created_at": now
            })
    new_df = pd.DataFrame(rows)
    if TRACKER.exists():
        old = pd.read_csv(TRACKER)
        if "shadow_date" in old.columns:
            old = old[old["shadow_date"].astype(str) != today]
        combined = pd.concat([old, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(TRACKER, index=False, encoding="utf-8-sig")
    return new_df, backup

def make_table(df, cols):
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, float):
                vals.append(f"{v:.5f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return lines

def write_outputs(compare_df, seed_df, backup):
    overlap = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_AND_OFFICIAL_REVIEW")]
    top_only = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_ONLY")]
    off_not_top = compare_df[compare_df["compare_bucket"].eq("OFFICIAL_REVIEW_NOT_SHADOW_TOP30")]
    names = ",".join(overlap["ticker"].astype(str).tolist()) if len(overlap) else "NONE"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    compare_df.to_csv(OUT_COMPARE, index=False, encoding="utf-8-sig")
    md = []
    md += ["# V18.3B-R2 Strict Shadow vs Official Compare", "", "Generated: " + now, ""]
    md += ["## 1. Status", "", "- V18_3B_R2_STATUS: OK_STRICT_FALLBACK_COMPARE_READY", "- OFFICIAL_DECISION_IMPACT: NONE", "- PROMOTION_ACTION: NONE", "- OFFICIAL_SOURCE: STRICT_CONFIRMED_V17_LOCKED_10_FALLBACK", ""]
    md += ["## 2. Summary", "", "- SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: " + str(len(overlap)), "- SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: " + names, "- SHADOW_TOP30_ONLY_COUNT: " + str(len(top_only)), "- OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: " + str(len(off_not_top)), "- TRACKER_SEED_ROWS_ADDED_OR_UPDATED: " + str(len(seed_df)), "- TRACKER_BACKUP: " + backup, ""]
    md += ["## 3. Overlap", ""]
    md += make_table(overlap, ["shadow_rank","ticker","shadow_score","official_status_bucket","compare_bucket"]) if len(overlap) else ["No overlap."]
    md += ["", "## 4. Official Review Not Shadow Top30", ""]
    md += make_table(off_not_top, ["shadow_rank","ticker","shadow_score","official_status_bucket","compare_bucket"]) if len(off_not_top) else ["None."]
    md += ["", "## 5. Shadow Top30 Only", ""]
    md += make_table(top_only, ["shadow_rank","ticker","shadow_score","official_status_bucket","compare_bucket"])
    OUT_MD.write_text(chr(10).join(md), encoding="utf-8")
    rf = []
    rf += ["=== V18.3B-R2 STRICT SHADOW VS OFFICIAL COMPARE READ FIRST ===", ""]
    rf += ["STATUS:", "V18_3B_R2_STATUS: OK_STRICT_FALLBACK_COMPARE_READY", ""]
    rf += ["OFFICIAL_DECISION_IMPACT:", "NONE", ""]
    rf += ["PROMOTION_ACTION:", "NONE", ""]
    rf += ["SUMMARY:", "OFFICIAL_SOURCE: STRICT_CONFIRMED_V17_LOCKED_10_FALLBACK", "SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: " + str(len(overlap)), "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: " + names, "SHADOW_TOP30_ONLY_COUNT: " + str(len(top_only)), "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: " + str(len(off_not_top)), "TRACKER_SEED_ROWS_ADDED_OR_UPDATED: " + str(len(seed_df)), "TRACKER_BACKUP: " + backup, ""]
    rf += ["OUTPUTS:", str(OUT_MD), str(OUT_COMPARE), str(TRACKER), str(AUDIT_CSV), ""]
    rf += ["NEXT_STEP:", "V18.4A_OUTCOME_TRACKER_UPDATE_AFTER_FORWARD_DAYS", ""]
    rf += ["IMPORTANT:", "No factor has been promoted. This is strict fallback comparison and clean outcome tracking seed only."]
    READ_FIRST.write_text(chr(10).join(rf), encoding="utf-8")
    audit = {"version": VERSION, "status": "OK_STRICT_FALLBACK_COMPARE_READY", "official_decision_impact": "NONE", "promotion_action": "NONE", "official_source": "STRICT_CONFIRMED_V17_LOCKED_10_FALLBACK", "shadow_top30_and_official_review_count": len(overlap), "shadow_top30_only_count": len(top_only), "official_review_not_shadow_top30_count": len(off_not_top), "tracker_seed_rows": len(seed_df), "tracker_backup": backup, "generated_at": now}
    pd.DataFrame([audit]).to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")
    return overlap, top_only, off_not_top

def main():
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    print("")
    print("=== V18.3B-R2 STRICT FALLBACK COMPARE START ===")
    shadow = load_shadow()
    compare_df = build_compare(shadow)
    seed_df, backup = rewrite_tracker_today(compare_df)
    overlap, top_only, off_not_top = write_outputs(compare_df, seed_df, backup)
    print("")
    print("=== V18.3B-R2 STRICT FALLBACK COMPARE READY ===")
    print("V18_3B_R2_STATUS: OK_STRICT_FALLBACK_COMPARE_READY")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("PROMOTION_ACTION: NONE")
    print("OFFICIAL_SOURCE: STRICT_CONFIRMED_V17_LOCKED_10_FALLBACK")
    print("SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: " + str(len(overlap)))
    print("SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: " + (",".join(overlap["ticker"].astype(str).tolist()) if len(overlap) else "NONE"))
    print("SHADOW_TOP30_ONLY_COUNT: " + str(len(top_only)))
    print("OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: " + str(len(off_not_top)))
    print("TRACKER_SEED_ROWS_ADDED_OR_UPDATED: " + str(len(seed_df)))
    print("TRACKER_BACKUP: " + backup)
    print("")
    print("READ_FIRST:")
    print(str(READ_FIRST))
    print("")
    print("COMPARE_CSV:")
    print(str(OUT_COMPARE))
    print("")
    print("OUTCOME_TRACKER:")
    print(str(TRACKER))
    print("")
    print("NEXT_VERSION:")
    print("V18.4A_OUTCOME_TRACKER_UPDATE_AFTER_FORWARD_DAYS")
    print("")
    print("=== DONE ===")

if __name__ == "__main__":
    main()
