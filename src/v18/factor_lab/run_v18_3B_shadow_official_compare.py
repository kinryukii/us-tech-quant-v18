from __future__ import annotations
import re
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")
VERSION = "V18.3B"
SHADOW_DIR = ROOT / "outputs" / "v18" / "factor_shadow"
V17_DIR = ROOT / "outputs" / "v17" / "raw105_decision"
STATE_DIR = ROOT / "state" / "v18"
MANIFEST_DIR = ROOT / "outputs" / "v18" / "manifests"
SHADOW_CSV = SHADOW_DIR / "V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv"
V17_FULL_CSV = V17_DIR / "v17_8A_raw105_full_decision_daily.csv"
OUT_COMPARE = SHADOW_DIR / "V18_3B_SHADOW_OFFICIAL_COMPARE_CURRENT.csv"
OUT_MD = SHADOW_DIR / "V18_3B_SHADOW_OFFICIAL_COMPARE_REPORT.md"
READ_FIRST = SHADOW_DIR / "V18_3B_READ_FIRST.txt"
AUDIT_CSV = SHADOW_DIR / "V18_3B_SHADOW_OFFICIAL_COMPARE_AUDIT.csv"
TRACKER = STATE_DIR / "factor_shadow_outcome_tracker.csv"
MANIFEST = MANIFEST_DIR / "V18_3B_SHADOW_OFFICIAL_COMPARE_MANIFEST.csv"
HORIZONS = [1, 3, 5, 10, 20]
FALLBACK_WORTH_REVIEW = {"ANET","ARM","CRWV","DELL","FLR","NET","QCOM","SNOW","VST","ZS"}

def fail(msg: str) -> None:
    print("")
    print("V18_3B_STATUS: FAIL")
    print(f"REASON: {msg}")
    print("")
    sys.exit(1)

def ensure_dirs() -> None:
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

def clean_ticker(x) -> str:
    return str(x).strip().upper().replace(".", "-")

def load_shadow() -> pd.DataFrame:
    if not SHADOW_CSV.exists():
        fail(f"SHADOW_CSV_MISSING: {SHADOW_CSV}. Run V18.3A first.")
    df = pd.read_csv(SHADOW_CSV)
    required = {"ticker","shadow_rank","shadow_score","shadow_factor_ids"}
    missing = required - set(df.columns)
    if missing:
        fail(f"SHADOW_COLUMNS_MISSING: {sorted(missing)}")
    df = df.copy()
    df["ticker"] = df["ticker"].map(clean_ticker)
    df["shadow_rank"] = pd.to_numeric(df["shadow_rank"], errors="coerce").astype("Int64")
    df["shadow_score"] = pd.to_numeric(df["shadow_score"], errors="coerce")
    df = df.dropna(subset=["ticker","shadow_rank"])
    return df.sort_values("shadow_rank")

def row_text(row) -> str:
    vals = []
    for x in row.tolist():
        vals.append(str(x).upper())
    return " ".join(vals)

def detect_official_from_csv(shadow_tickers: set[str]) -> pd.DataFrame:
    rows = []
    if V17_FULL_CSV.exists():
        try:
            df = pd.read_csv(V17_FULL_CSV)
            ticker_col = "ticker" if "ticker" in df.columns else None
            if ticker_col is not None:
                for _, r in df.iterrows():
                    t = clean_ticker(r[ticker_col])
                    if t not in shadow_tickers:
                        continue
                    txt = row_text(r)
                    actionable = ("ACTIONABLE" in txt or "BUY_NOW" in txt or "BUY_TODAY" in txt) and ("NO_BUY" not in txt)
                    worth = ("WORTH_REVIEW" in txt or "WORTH-REVIEW" in txt or "REVIEW" in txt or "CANDIDATE" in txt) and ("LOCK" in txt or "HOLD" in txt or "NO_BUY" in txt or "REVIEW" in txt)
                    blocked = ("BLOCK" in txt or "LOCK" in txt or "FREEZE" in txt or "NO_BUY" in txt or "NO_TRADE" in txt)
                    rows.append({
                        "ticker": t,
                        "v17_source": str(V17_FULL_CSV),
                        "official_actionable_buy": bool(actionable),
                        "official_worth_review_locked": bool(worth),
                        "official_blocked_or_locked": bool(blocked),
                        "official_raw_text_short": txt[:240],
                    })
        except Exception as e:
            print(f"WARN: V17_FULL_CSV_PARSE_FAILED: {e}")
    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame({"ticker": sorted(shadow_tickers)})
        out["v17_source"] = "NO_V17_CSV_PARSED"
        out["official_actionable_buy"] = False
        out["official_worth_review_locked"] = False
        out["official_blocked_or_locked"] = False
        out["official_raw_text_short"] = ""
    found_worth = int(out["official_worth_review_locked"].sum()) if "official_worth_review_locked" in out.columns else 0
    if found_worth == 0:
        out["official_worth_review_locked"] = out["ticker"].isin(FALLBACK_WORTH_REVIEW)
        out["official_blocked_or_locked"] = out["official_blocked_or_locked"] | out["ticker"].isin(FALLBACK_WORTH_REVIEW)
        out.loc[out["ticker"].isin(FALLBACK_WORTH_REVIEW), "v17_source"] = "FALLBACK_LATEST_V17_8B_LOCKED_LIST"
    return out.drop_duplicates(subset=["ticker"], keep="first")

def compare(shadow: pd.DataFrame, official: pd.DataFrame) -> pd.DataFrame:
    df = shadow.merge(official, on="ticker", how="left")
    for c in ["official_actionable_buy","official_worth_review_locked","official_blocked_or_locked"]:
        if c not in df.columns:
            df[c] = False
        df[c] = df[c].fillna(False).astype(bool)
    df["official_match_flag"] = df["official_actionable_buy"] | df["official_worth_review_locked"]
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
    def status(r):
        if r["official_actionable_buy"]:
            return "OFFICIAL_ACTIONABLE_BUY"
        if r["official_worth_review_locked"]:
            return "OFFICIAL_WORTH_REVIEW_LOCKED"
        if r["official_blocked_or_locked"]:
            return "OFFICIAL_BLOCKED_OR_LOCKED"
        return "NO_OFFICIAL_CANDIDATE_FLAG"
    df["official_status_bucket"] = df.apply(status, axis=1)
    return df.sort_values("shadow_rank")

def update_tracker(compare_df: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    shadow_date = datetime.now().strftime("%Y-%m-%d")
    seed = compare_df[(compare_df["shadow_top30_flag"]) | (compare_df["official_match_flag"])].copy()
    rows = []
    for _, r in seed.iterrows():
        for h in HORIZONS:
            rows.append({
                "shadow_date": shadow_date,
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
                "created_at": now,
            })
    new_df = pd.DataFrame(rows)
    if TRACKER.exists():
        old = pd.read_csv(TRACKER)
        combined = pd.concat([old, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["shadow_date","ticker","horizon_days"], keep="last")
    else:
        combined = new_df
    combined.to_csv(TRACKER, index=False, encoding="utf-8-sig")
    return new_df

def table_lines(df: pd.DataFrame, cols: list[str], limit: int | None = None) -> list[str]:
    part = df.copy()
    if limit is not None:
        part = part.head(limit)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in part.iterrows():
        vals = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, float):
                vals.append(f"{v:.5f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return lines

def write_report(compare_df: pd.DataFrame, tracker_seed: pd.DataFrame) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overlap = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_AND_OFFICIAL_REVIEW")]
    top_only = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_ONLY")]
    official_not_top = compare_df[compare_df["compare_bucket"].eq("OFFICIAL_REVIEW_NOT_SHADOW_TOP30")]
    lines = []
    lines += ["# V18.3B Shadow vs Official Candidate Compare", "", f"Generated: {now}", ""]
    lines += ["## 1. Status", "", "- V18_3B_STATUS: `OK_SHADOW_OFFICIAL_COMPARE_READY`", "- OFFICIAL_DECISION_IMPACT: `NONE`", "- PROMOTION_ACTION: `NONE`", "- OUTCOME_TRACKER_STATUS: `SEEDED_PENDING`", ""]
    lines += ["## 2. Summary", "", f"- SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: `{len(overlap)}`", f"- SHADOW_TOP30_ONLY_COUNT: `{len(top_only)}`", f"- OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: `{len(official_not_top)}`", f"- TRACKER_SEED_ROWS_ADDED_OR_UPDATED: `{len(tracker_seed)}`", ""]
    lines += ["## 3. Overlap: Shadow Top30 and Official Review", ""]
    if overlap.empty:
        lines += ["No overlap found.", ""]
    else:
        lines += table_lines(overlap, ["shadow_rank","ticker","shadow_score","official_status_bucket","compare_bucket"], None) + [""]
    lines += ["## 4. Shadow Top30 Only", ""]
    lines += table_lines(top_only, ["shadow_rank","ticker","shadow_score","official_status_bucket","compare_bucket"], 30) + [""]
    lines += ["## 5. Official Review Not In Shadow Top30", ""]
    if official_not_top.empty:
        lines += ["No official review names outside shadow top30.", ""]
    else:
        lines += table_lines(official_not_top.sort_values("shadow_rank"), ["shadow_rank","ticker","shadow_score","official_status_bucket","compare_bucket"], None) + [""]
    lines += ["## 6. Rule", "", "This report is observation-only. It does not change V17.8D official BUY / NO_BUY output.", "", "## 7. Next Step", "", "V18.4A should update the outcome tracker after enough trading days pass and compute realized 1/3/5/10/20 day returns.", ""]
    OUT_MD.write_text(chr(10).join(lines), encoding="utf-8")

def write_read_first(compare_df: pd.DataFrame, tracker_seed: pd.DataFrame) -> None:
    overlap = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_AND_OFFICIAL_REVIEW")]
    top_only = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_ONLY")]
    official_not_top = compare_df[compare_df["compare_bucket"].eq("OFFICIAL_REVIEW_NOT_SHADOW_TOP30")]
    overlap_names = ",".join(overlap["ticker"].astype(str).tolist()) if not overlap.empty else "NONE"
    lines = [
        "=== V18.3B SHADOW VS OFFICIAL COMPARE READ FIRST ===",
        "",
        "STATUS:",
        "V18_3B_STATUS: OK_SHADOW_OFFICIAL_COMPARE_READY",
        "",
        "OFFICIAL_DECISION_IMPACT:",
        "NONE",
        "",
        "PROMOTION_ACTION:",
        "NONE",
        "",
        "SUMMARY:",
        f"SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: {len(overlap)}",
        f"SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: {overlap_names}",
        f"SHADOW_TOP30_ONLY_COUNT: {len(top_only)}",
        f"OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: {len(official_not_top)}",
        f"TRACKER_SEED_ROWS_ADDED_OR_UPDATED: {len(tracker_seed)}",
        "",
        "OUTPUTS:",
        str(OUT_MD),
        str(OUT_COMPARE),
        str(TRACKER),
        str(AUDIT_CSV),
        "",
        "NEXT_STEP:",
        "V18.4A_OUTCOME_TRACKER_UPDATE_AFTER_FORWARD_DAYS",
        "",
        "IMPORTANT:",
        "No factor has been promoted. This is shadow comparison and outcome tracking seed only.",
    ]
    READ_FIRST.write_text(chr(10).join(lines), encoding="utf-8")

def write_audit(compare_df: pd.DataFrame, tracker_seed: pd.DataFrame) -> None:
    overlap = int(compare_df["compare_bucket"].eq("SHADOW_TOP30_AND_OFFICIAL_REVIEW").sum())
    top_only = int(compare_df["compare_bucket"].eq("SHADOW_TOP30_ONLY").sum())
    official_not_top = int(compare_df["compare_bucket"].eq("OFFICIAL_REVIEW_NOT_SHADOW_TOP30").sum())
    row = {
        "version": VERSION,
        "status": "OK_SHADOW_OFFICIAL_COMPARE_READY",
        "official_decision_impact": "NONE",
        "promotion_action": "NONE",
        "shadow_top30_and_official_review_count": overlap,
        "shadow_top30_only_count": top_only,
        "official_review_not_shadow_top30_count": official_not_top,
        "tracker_seed_rows": len(tracker_seed),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    pd.DataFrame([row]).to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")

def write_manifest() -> None:
    rows = []
    for p in [READ_FIRST, OUT_MD, OUT_COMPARE, TRACKER, AUDIT_CSV]:
        if p.exists():
            rows.append({"version": VERSION, "path": str(p), "length_bytes": p.stat().st_size, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "purpose": "shadow_official_compare"})
    pd.DataFrame(rows).to_csv(MANIFEST, index=False, encoding="utf-8-sig")

def main() -> None:
    ensure_dirs()
    print("")
    print("=== V18.3B SHADOW VS OFFICIAL COMPARE START ===")
    shadow = load_shadow()
    official = detect_official_from_csv(set(shadow["ticker"].tolist()))
    compare_df = compare(shadow, official)
    tracker_seed = update_tracker(compare_df)
    compare_df.to_csv(OUT_COMPARE, index=False, encoding="utf-8-sig")
    write_report(compare_df, tracker_seed)
    write_read_first(compare_df, tracker_seed)
    write_audit(compare_df, tracker_seed)
    write_manifest()
    overlap = compare_df[compare_df["compare_bucket"].eq("SHADOW_TOP30_AND_OFFICIAL_REVIEW")]
    print("")
    print("=== V18.3B SHADOW VS OFFICIAL COMPARE READY ===")
    print("V18_3B_STATUS: OK_SHADOW_OFFICIAL_COMPARE_READY")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("PROMOTION_ACTION: NONE")
    print(f"SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: {len(overlap)}")
    print("SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: " + (",".join(overlap["ticker"].astype(str).tolist()) if len(overlap) else "NONE"))
    print(f"TRACKER_SEED_ROWS_ADDED_OR_UPDATED: {len(tracker_seed)}")
    print("")
    print("READ_FIRST:")
    print(str(READ_FIRST))
    print("")
    print("REPORT:")
    print(str(OUT_MD))
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
