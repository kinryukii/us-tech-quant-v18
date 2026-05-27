import re
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

ROOT = Path(r"D:\us-tech-quant")

OUT_DIR = ROOT / "outputs" / "v17" / "raw105_decision"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_FULL_UNIVERSE_RAW.csv"
FULL_SECOND_STAGE_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_FULL_UNIVERSE_SECOND_STAGE.csv"
TOP_CANDIDATES_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_SECOND_STAGE_TOP_CANDIDATES.csv"
WATCHLIST_PATH = ROOT / "outputs" / "v16" / "universe" / "V16_SECOND_STAGE_WATCHLIST.csv"

SEMANTIC_PATH = ROOT / "outputs" / "v17" / "raw_universe_audit" / "v17_7B_universe_semantic_audit.csv"
RAW105_PRICE_PATH = ROOT / "outputs" / "v17" / "raw_universe_audit" / "v17_7F_raw105_latest_price_refresh.csv"
FRESHNESS_ACCEPT_PATH = ROOT / "outputs" / "v17" / "raw_universe_audit" / "v17_7F_B_price_freshness_acceptance.csv"

SECOND_STAGE_CURRENT_PATH = ROOT / "outputs" / "v17" / "price" / "v17_6E_second_stage_tickers.csv"
MAIN_COMPUTE_CURRENT_PATH = ROOT / "outputs" / "v17" / "price" / "v17_6E_screened_universe_tickers.csv"

MANUAL_DAILY_DIR = ROOT / "outputs" / "v17" / "manual_daily"

OUT_CSV = OUT_DIR / "v17_8A_raw105_full_decision_daily.csv"
BUY_CANDIDATES_CSV = OUT_DIR / "v17_8A_today_buy_candidates.csv"
WATCH_CSV = OUT_DIR / "v17_8A_today_watch_candidates.csv"
SUMMARY_MD = OUT_DIR / "V17_8A_RAW105_FULL_DECISION_DAILY.md"
READ_FIRST = OUT_DIR / "V17_8A_READ_FIRST.txt"

def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()

def find_ticker_col(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    candidates = ["ticker", "Ticker", "symbol", "Symbol", "code", "Code"]
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        lc = str(c).lower()
        if "ticker" in lc or "symbol" in lc:
            return c
    return df.columns[0] if len(df.columns) else None

def normalize_ticker_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    col = find_ticker_col(df)
    if col is None:
        return pd.DataFrame()
    out = df.copy()
    if col != "ticker":
        out = out.rename(columns={col: "ticker"})
    out["ticker"] = out["ticker"].astype(str).str.strip().str.upper()
    out = out[(out["ticker"] != "") & (out["ticker"] != "NAN")]
    return out

def ticker_set(path: Path):
    df = normalize_ticker_df(read_csv_safe(path))
    if df.empty:
        return set()
    return set(df["ticker"].dropna().astype(str).str.upper().tolist())

def latest_manual_daily_txt():
    if not MANUAL_DAILY_DIR.exists():
        return None
    files = sorted(
        MANUAL_DAILY_DIR.glob("V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if files:
        return files[0]
    files = sorted(
        MANUAL_DAILY_DIR.glob("V17_6F_E_MANUAL_DAILY_STABLE_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None

def read_kv_txt(path: Path):
    d = {}
    if path is None or not path.exists():
        return d
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        m = re.match(r"^([^:]+):\s*(.*)$", line.strip())
        if m:
            d[m.group(1).strip()] = m.group(2).strip()
    return d

def pick_first_existing_col(df: pd.DataFrame, names):
    for n in names:
        if n in df.columns:
            return n
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None

def maybe_num(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    raw = normalize_ticker_df(read_csv_safe(RAW_PATH))
    if raw.empty:
        print("ERROR: RAW universe missing or empty")
        print(str(RAW_PATH))
        sys.exit(2)

    semantic = normalize_ticker_df(read_csv_safe(SEMANTIC_PATH))
    raw_price = normalize_ticker_df(read_csv_safe(RAW105_PRICE_PATH))
    freshness = normalize_ticker_df(read_csv_safe(FRESHNESS_ACCEPT_PATH))

    full_second = normalize_ticker_df(read_csv_safe(FULL_SECOND_STAGE_PATH))
    top_candidates = normalize_ticker_df(read_csv_safe(TOP_CANDIDATES_PATH))
    watchlist = normalize_ticker_df(read_csv_safe(WATCHLIST_PATH))

    main_set = ticker_set(MAIN_COMPUTE_CURRENT_PATH)
    second_set = ticker_set(SECOND_STAGE_CURRENT_PATH)
    top_set = set(top_candidates["ticker"].tolist()) if not top_candidates.empty else set()
    watch_set = set(watchlist["ticker"].tolist()) if not watchlist.empty else set()

    latest_daily = latest_manual_daily_txt()
    daily_kv = read_kv_txt(latest_daily)

    today_safe = daily_kv.get("TODAY_SAFE", "")
    official_action = daily_kv.get("OFFICIAL_ACTION", "")
    budget_action = daily_kv.get("BUDGET_ACTION", "")
    buy_permission = daily_kv.get("BUY_PERMISSION", "")
    global_mode = daily_kv.get("GLOBAL_MODE", "")
    manual_daily_status = daily_kv.get("MANUAL_DAILY_STATUS", "")
    price_audit_status = daily_kv.get("PRICE_AUDIT_STATUS", "")

    event_or_budget_locked = (
        today_safe == "NO_TRADE_NO_NEW_BUYS"
        or "NO_TRADE" in official_action
        or "LOCKED" in budget_action
        or "NO_NEW_BUYS" in buy_permission
        or "LOCKED" in global_mode
    )

    # Build base rows
    base = raw[["ticker"]].drop_duplicates().copy()
    base["run_time"] = now

    # Merge semantic layer
    if not semantic.empty:
        keep = [c for c in [
            "ticker",
            "semantic_layer",
            "in_raw_universe",
            "in_classified_universe",
            "in_main_compute_universe",
            "in_second_stage_candidate",
            "raw_price_ok",
            "price_status",
            "latest_price_date",
            "latest_close",
            "special_tag",
            "inferred_exclusion_reason"
        ] if c in semantic.columns]
        base = base.merge(semantic[keep], on="ticker", how="left")

    # Merge raw105 latest price
    if not raw_price.empty:
        keep = [c for c in [
            "ticker",
            "refresh_status",
            "latest_price_date",
            "latest_close",
            "latest_volume",
            "freshness_status"
        ] if c in raw_price.columns]
        rp = raw_price[keep].copy()
        rename = {}
        for c in rp.columns:
            if c != "ticker":
                rename[c] = "raw105_" + c
        rp = rp.rename(columns=rename)
        base = base.merge(rp, on="ticker", how="left")

    # Merge freshness acceptance
    if not freshness.empty:
        keep = [c for c in [
            "ticker",
            "acceptance_status",
            "max_latest_price_date"
        ] if c in freshness.columns]
        fa = freshness[keep].copy()
        rename = {}
        for c in fa.columns:
            if c != "ticker":
                rename[c] = "freshness_" + c
        fa = fa.rename(columns=rename)
        base = base.merge(fa, on="ticker", how="left")

    # Merge any full second-stage scoring columns, if present.
    score_cols = []
    if not full_second.empty:
        candidate_names = [
            "rank", "score", "final_score", "final_signal_score",
            "composite_score", "total_score", "bucket", "stage",
            "decision", "reason", "review_decision", "candidate_review_decision",
            "momentum_score", "trend_score", "relative_strength_score",
            "pullback_score", "overheat_penalty", "volatility_penalty",
            "event_risk_penalty", "execution_penalty"
        ]
        lower_map = {str(c).lower(): c for c in full_second.columns}
        keep = ["ticker"]
        for name in candidate_names:
            if name.lower() in lower_map and lower_map[name.lower()] not in keep:
                keep.append(lower_map[name.lower()])
        # Also keep compact useful columns containing these words
        for c in full_second.columns:
            lc = str(c).lower()
            if c == "ticker":
                continue
            if any(k in lc for k in ["score", "rank", "bucket", "decision", "reason", "status", "penalty", "return", "momentum", "trend", "pullback"]):
                if c not in keep:
                    keep.append(c)
        fs = full_second[keep].copy()
        rename = {}
        for c in fs.columns:
            if c != "ticker":
                rename[c] = "model_" + str(c)
                score_cols.append("model_" + str(c))
        fs = fs.rename(columns=rename)
        base = base.merge(fs, on="ticker", how="left")

    base["is_current_main_compute"] = base["ticker"].isin(main_set)
    base["is_current_second_stage"] = base["ticker"].isin(second_set)
    base["is_top_candidate_file"] = base["ticker"].isin(top_set)
    base["is_watchlist_file"] = base["ticker"].isin(watch_set)

    # Decide candidate tier for every ticker
    def candidate_tier(row):
        if row["is_current_second_stage"]:
            return "A_SECOND_STAGE_TOP10"
        if row["is_current_main_compute"]:
            return "B_MAIN_COMPUTE_NOT_TOP10"
        layer = str(row.get("semantic_layer", ""))
        if "CLASSIFIED" in layer:
            return "C_CLASSIFIED_NOT_MAIN_COMPUTE"
        return "D_RAW_ONLY_OR_UNCLASSIFIED"

    base["candidate_tier"] = base.apply(candidate_tier, axis=1)

    def full_decision(row):
        price_ok = str(row.get("raw105_refresh_status", "")).startswith("OK") or str(row.get("price_status", "")).startswith("OK")
        freshness_accept = str(row.get("freshness_acceptance_status", ""))
        in_second = bool(row["is_current_second_stage"])
        in_main = bool(row["is_current_main_compute"])

        if not price_ok:
            return "REJECT_PRICE_NOT_OK"
        if freshness_accept.startswith("REVIEW") or freshness_accept.startswith("REJECT"):
            return "REJECT_OR_REVIEW_PRICE_FRESHNESS"

        if event_or_budget_locked:
            if in_second:
                return "WORTH_REVIEW_BUT_NO_BUY_TODAY_EVENT_OR_BUDGET_LOCKED"
            if in_main:
                return "WATCH_MAIN_COMPUTE_NO_BUY_TODAY"
            return "NO_BUY_NOT_MAIN_COMPUTE"

        # If gates are open, still do not auto-buy everything.
        if in_second:
            return "BUY_CANDIDATE_REQUIRES_MANUAL_CONFIRMATION"
        if in_main:
            return "WATCH_MAIN_COMPUTE_NOT_BUY_CANDIDATE"
        return "NO_BUY_NOT_MAIN_COMPUTE"

    base["full_buy_decision"] = base.apply(full_decision, axis=1)

    def decision_reason(row):
        if row["full_buy_decision"] == "WORTH_REVIEW_BUT_NO_BUY_TODAY_EVENT_OR_BUDGET_LOCKED":
            return f"进入 second stage，但今日被事件/预算门控锁住：{official_action} / {budget_action} / {buy_permission}"
        if row["full_buy_decision"] == "BUY_CANDIDATE_REQUIRES_MANUAL_CONFIRMATION":
            return "进入 second stage，且门控未锁；需要人工复核触发价、仓位、事件风险后才可买"
        if row["full_buy_decision"] == "WATCH_MAIN_COMPUTE_NO_BUY_TODAY":
            return "进入 main compute，但未进入 second stage；且今日门控锁住，不买"
        if row["full_buy_decision"] == "WATCH_MAIN_COMPUTE_NOT_BUY_CANDIDATE":
            return "进入 main compute，但未进入 second stage；观察，不是今日买入候选"
        if row["full_buy_decision"] == "NO_BUY_NOT_MAIN_COMPUTE":
            return "未进入当前 main compute；只保留在 RAW/classified 层，不作为今日买入候选"
        if row["full_buy_decision"] == "REJECT_PRICE_NOT_OK":
            return "价格刷新或价格审计未通过"
        if row["full_buy_decision"] == "REJECT_OR_REVIEW_PRICE_FRESHNESS":
            return "价格 freshness 需要复核或拒绝"
        return "规则外状态，需要人工检查"

    base["decision_reason_cn"] = base.apply(decision_reason, axis=1)

    # Ranking: second stage first, then main compute, then classified
    tier_order = {
        "A_SECOND_STAGE_TOP10": 1,
        "B_MAIN_COMPUTE_NOT_TOP10": 2,
        "C_CLASSIFIED_NOT_MAIN_COMPUTE": 3,
        "D_RAW_ONLY_OR_UNCLASSIFIED": 4,
    }
    base["tier_order"] = base["candidate_tier"].map(tier_order).fillna(9)

    # Try to sort by model rank/score if available
    rank_col = None
    score_col = None
    for c in base.columns:
        lc = str(c).lower()
        if rank_col is None and "rank" in lc:
            rank_col = c
        if score_col is None and ("final" in lc and "score" in lc):
            score_col = c
    if score_col is None:
        for c in base.columns:
            if "score" in str(c).lower():
                score_col = c
                break

    if rank_col:
        base["_sort_rank"] = pd.to_numeric(base[rank_col], errors="coerce").fillna(999999)
    else:
        base["_sort_rank"] = 999999

    if score_col:
        base["_sort_score"] = pd.to_numeric(base[score_col], errors="coerce").fillna(-999999)
    else:
        base["_sort_score"] = -999999

    base = base.sort_values(["tier_order", "_sort_rank", "_sort_score", "ticker"], ascending=[True, True, False, True])

    raw_count = len(base)
    main_count = int(base["is_current_main_compute"].sum())
    second_count = int(base["is_current_second_stage"].sum())
    price_ok_count = int(base["raw105_refresh_status"].astype(str).str.startswith("OK").sum()) if "raw105_refresh_status" in base.columns else 0
    price_fail_count = raw_count - price_ok_count if price_ok_count else 0

    actionable_buy = base[base["full_buy_decision"] == "BUY_CANDIDATE_REQUIRES_MANUAL_CONFIRMATION"].copy()
    worth_review_locked = base[base["full_buy_decision"] == "WORTH_REVIEW_BUT_NO_BUY_TODAY_EVENT_OR_BUDGET_LOCKED"].copy()
    main_watch = base[base["candidate_tier"] == "B_MAIN_COMPUTE_NOT_TOP10"].copy()

    actionable_buy_count = len(actionable_buy)
    worth_review_count = len(worth_review_locked)
    watch_count = len(main_watch)

    if event_or_budget_locked:
        final_action = "NO_BUY_TODAY_EVENT_OR_BUDGET_LOCKED"
    elif actionable_buy_count > 0:
        final_action = "BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION"
    else:
        final_action = "NO_BUY_TODAY_NO_ACTIONABLE_CANDIDATE"

    base.drop(columns=[c for c in ["_sort_rank", "_sort_score"] if c in base.columns], inplace=True)
    base.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    actionable_buy.to_csv(BUY_CANDIDATES_CSV, index=False, encoding="utf-8-sig")
    worth_review_locked.to_csv(WATCH_CSV, index=False, encoding="utf-8-sig")

    md = []
    md.append("# V17.8A RAW105 Full Decision Daily")
    md.append("")
    md.append(f"Generated: {now}")
    md.append("")
    md.append("## 1. Main Conclusion")
    md.append("")
    md.append(f"RAW105_FULL_DECISION_STATUS: OK")
    md.append(f"FINAL_ACTION: {final_action}")
    md.append("")
    if final_action == "NO_BUY_TODAY_EVENT_OR_BUDGET_LOCKED":
        md.append("**今天没有可执行买入。原因不是没有候选，而是事件风险/预算门控仍然锁住。**")
    elif final_action == "BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION":
        md.append("**今天存在买入候选，但仍需要人工确认触发价、仓位和事件风险。**")
    else:
        md.append("**今天没有可执行买入候选。**")
    md.append("")
    md.append("## 2. Gate Status")
    md.append("")
    md.append("| item | value |")
    md.append("|---|---|")
    md.append(f"| MANUAL_DAILY_STATUS | {manual_daily_status} |")
    md.append(f"| TODAY_SAFE | {today_safe} |")
    md.append(f"| OFFICIAL_ACTION | {official_action} |")
    md.append(f"| BUDGET_ACTION | {budget_action} |")
    md.append(f"| BUY_PERMISSION | {buy_permission} |")
    md.append(f"| GLOBAL_MODE | {global_mode} |")
    md.append(f"| PRICE_AUDIT_STATUS | {price_audit_status} |")
    md.append("")
    md.append("## 3. RAW105 Full Decision Counts")
    md.append("")
    md.append("| item | count |")
    md.append("|---|---:|")
    md.append(f"| RAW_UNIVERSE_DECISION_COUNT | {raw_count} |")
    md.append(f"| MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC | {main_count} |")
    md.append(f"| SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC | {second_count} |")
    md.append(f"| RAW105_PRICE_OK_COUNT | {price_ok_count} |")
    md.append(f"| RAW105_PRICE_FAIL_COUNT | {price_fail_count} |")
    md.append(f"| ACTIONABLE_BUY_COUNT_TODAY | {actionable_buy_count} |")
    md.append(f"| WORTH_REVIEW_BUT_LOCKED_COUNT | {worth_review_count} |")
    md.append(f"| MAIN_COMPUTE_WATCH_COUNT | {watch_count} |")
    md.append("")
    md.append("## 4. 今日值得复核但不能买的候选")
    md.append("")
    md.append("| ticker | latest_price_date | latest_close | decision | reason |")
    md.append("|---|---:|---:|---|---|")
    for _, r in worth_review_locked.iterrows():
        md.append(f"| {r.get('ticker','')} | {r.get('raw105_latest_price_date','')} | {r.get('raw105_latest_close','')} | {r.get('full_buy_decision','')} | {r.get('decision_reason_cn','')} |")
    md.append("")
    md.append("## 5. 如果今天门控打开，优先复核层")
    md.append("")
    md.append("优先级不是直接买入顺序，而是人工复核顺序：")
    md.append("")
    md.append("1. second stage candidate")
    md.append("2. main compute but not second stage")
    md.append("3. classified only")
    md.append("")
    md.append("## 6. Output Files")
    md.append("")
    md.append(f"- Full RAW105 decision CSV: {OUT_CSV}")
    md.append(f"- Actionable buy candidates CSV: {BUY_CANDIDATES_CSV}")
    md.append(f"- Worth-review watch CSV: {WATCH_CSV}")
    md.append(f"- Summary: {SUMMARY_MD}")
    md.append(f"- Read first: {READ_FIRST}")
    if latest_daily:
        md.append(f"- Latest manual daily source: {latest_daily}")
    md.append("")

    SUMMARY_MD.write_text("\n".join(md), encoding="utf-8")

    rf = []
    rf.append("=== V17.8A RAW105 FULL DECISION DAILY READY ===")
    rf.append("RAW105_FULL_DECISION_STATUS: OK")
    rf.append(f"FINAL_ACTION: {final_action}")
    rf.append(f"RAW_UNIVERSE_DECISION_COUNT: {raw_count}")
    rf.append(f"MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: {main_count}")
    rf.append(f"SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: {second_count}")
    rf.append(f"RAW105_PRICE_OK_COUNT: {price_ok_count}")
    rf.append(f"RAW105_PRICE_FAIL_COUNT: {price_fail_count}")
    rf.append(f"ACTIONABLE_BUY_COUNT_TODAY: {actionable_buy_count}")
    rf.append(f"WORTH_REVIEW_BUT_LOCKED_COUNT: {worth_review_count}")
    rf.append(f"TODAY_SAFE: {today_safe}")
    rf.append(f"OFFICIAL_ACTION: {official_action}")
    rf.append(f"BUDGET_ACTION: {budget_action}")
    rf.append(f"BUY_PERMISSION: {buy_permission}")
    rf.append("")
    rf.append("START HERE:")
    rf.append(str(SUMMARY_MD))
    rf.append("")
    rf.append("FULL RAW105 DECISION CSV:")
    rf.append(str(OUT_CSV))
    rf.append("")
    rf.append("WORTH REVIEW WATCH CSV:")
    rf.append(str(WATCH_CSV))
    rf.append("")
    rf.append("ACTIONABLE BUY CSV:")
    rf.append(str(BUY_CANDIDATES_CSV))
    READ_FIRST.write_text("\n".join(rf), encoding="utf-8")

    print("")
    print("=== V17.8A RAW105 FULL DECISION DAILY READY ===")
    print("RAW105_FULL_DECISION_STATUS: OK")
    print(f"FINAL_ACTION: {final_action}")
    print(f"RAW_UNIVERSE_DECISION_COUNT: {raw_count}")
    print(f"MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: {main_count}")
    print(f"SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: {second_count}")
    print(f"RAW105_PRICE_OK_COUNT: {price_ok_count}")
    print(f"RAW105_PRICE_FAIL_COUNT: {price_fail_count}")
    print(f"ACTIONABLE_BUY_COUNT_TODAY: {actionable_buy_count}")
    print(f"WORTH_REVIEW_BUT_LOCKED_COUNT: {worth_review_count}")
    print(f"TODAY_SAFE: {today_safe}")
    print(f"OFFICIAL_ACTION: {official_action}")
    print(f"BUDGET_ACTION: {budget_action}")
    print(f"BUY_PERMISSION: {buy_permission}")
    print("")
    print("START HERE:")
    print(str(SUMMARY_MD))
    print("")
    print("FULL RAW105 DECISION CSV:")
    print(str(OUT_CSV))
    print("")
    print("READ FIRST:")
    print(str(READ_FIRST))

if __name__ == "__main__":
    main()
