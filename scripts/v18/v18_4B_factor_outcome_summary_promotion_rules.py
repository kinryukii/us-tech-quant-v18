from pathlib import Path
from datetime import datetime
import csv
import statistics
import sys

ROOT = Path(r"D:\us-tech-quant")

TRACKER_CSV = ROOT / "state" / "v18" / "forward_outcome" / "V18_4A_FACTOR_FORWARD_TRACKER.csv"
INTEGRATED_READ = ROOT / "outputs" / "v18" / "daily_integrated" / "V18_4A_R1_READ_FIRST.txt"

OUT_DIR = ROOT / "outputs" / "v18" / "outcome_summary"
OUT_DIR.mkdir(parents=True, exist_ok=True)

READ_FIRST = OUT_DIR / "V18_4B_READ_FIRST.txt"
SUMMARY_CSV = OUT_DIR / "V18_4B_CURRENT_FACTOR_OUTCOME_SUMMARY.csv"
RULES_MD = OUT_DIR / "V18_4B_CURRENT_PROMOTION_RULES.md"
GLOBAL_MD = OUT_DIR / "V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md"

RUN_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

HORIZONS = [1, 3, 5, 10, 20]

GROUPS = [
    ("group_factor_top10", "factor_top10", "Factor pack top10"),
    ("group_factor_top30", "factor_top30", "Factor pack top30"),
    ("group_official_review", "official_review", "Official review 10"),
    ("group_factor_pack_overlap", "factor_pack_overlap", "Official review ∩ factor pack top30"),
    ("group_v18_3c_overlap", "v18_3c_overlap", "Official review ∩ V18.3C shadow"),
]

MIN_SAMPLES = {
    "factor_top10": 20,
    "factor_top30": 40,
    "official_review": 20,
    "factor_pack_overlap": 8,
    "v18_3c_overlap": 6,
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
    return path.read_text(errors="ignore")


def read_csv_rows(path: Path):
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def write_csv(path: Path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def to_float(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("%", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def is_true(x) -> bool:
    return str(x).strip().upper() == "TRUE"


def get_key(text: str, key: str, default="UNKNOWN") -> str:
    if not text:
        return default
    import re
    pat = re.compile(r"^\s*" + re.escape(key) + r"\s*:\s*(.+?)\s*$", re.M)
    m = pat.search(text)
    if m:
        return m.group(1).strip()
    return default


def classify(group_key: str, horizon: int, count: int, avg, median, win_rate):
    min_n = MIN_SAMPLES.get(group_key, 20)

    if count == 0:
        return "NO_COMPLETED_OBS_YET"

    if count < min_n:
        return "WATCH_DATA_INSUFFICIENT"

    if avg is None or median is None or win_rate is None:
        return "WATCH_DATA_INCOMPLETE"

    if avg >= 1.0 and median >= 0.5 and win_rate >= 55.0:
        if horizon in (5, 10, 20):
            return "PROMOTE_CANDIDATE_REVIEW_REQUIRED"
        return "POSITIVE_EARLY_SIGNAL_NOT_PROMOTABLE_YET"

    if avg > 0 and median >= 0 and win_rate >= 50.0:
        return "KEEP_WATCHING_POSITIVE"

    if avg <= -1.0 and median < 0 and win_rate <= 45.0:
        return "REJECT_CANDIDATE"

    return "NEUTRAL_KEEP_WATCHING"


def summarize_group(rows, flag_col, group_key, group_label):
    out = []
    selected = [r for r in rows if is_true(r.get(flag_col, ""))]

    for h in HORIZONS:
        vals = []
        tickers = set()

        for r in selected:
            if r.get(f"status_{h}obs", "") == "DONE":
                v = to_float(r.get(f"return_{h}obs_pct", ""))
                if v is not None:
                    vals.append(v)
                    t = str(r.get("ticker", "")).strip().upper()
                    if t:
                        tickers.add(t)

        if vals:
            count = len(vals)
            avg = sum(vals) / count
            median = statistics.median(vals)
            win_rate = sum(1 for v in vals if v > 0) / count * 100.0
            best = max(vals)
            worst = min(vals)
        else:
            count = 0
            avg = None
            median = None
            win_rate = None
            best = None
            worst = None

        eval_status = classify(group_key, h, count, avg, median, win_rate)

        out.append({
            "group_key": group_key,
            "group_label": group_label,
            "horizon_obs": str(h),
            "completed_count": str(count),
            "unique_ticker_count": str(len(tickers)),
            "avg_return_pct": "" if avg is None else f"{avg:.4f}",
            "median_return_pct": "" if median is None else f"{median:.4f}",
            "win_rate_pct": "" if win_rate is None else f"{win_rate:.4f}",
            "best_return_pct": "" if best is None else f"{best:.4f}",
            "worst_return_pct": "" if worst is None else f"{worst:.4f}",
            "min_required_samples": str(MIN_SAMPLES.get(group_key, 20)),
            "promotion_eval": eval_status,
        })

    return out


def main():
    if not TRACKER_CSV.exists():
        raise RuntimeError(f"TRACKER_CSV_NOT_FOUND: {TRACKER_CSV}")

    rows = read_csv_rows(TRACKER_CSV)
    if not rows:
        raise RuntimeError("TRACKER_EMPTY")

    integrated_text = read_text(INTEGRATED_READ)

    summary_rows = []
    for flag_col, group_key, group_label in GROUPS:
        summary_rows.extend(summarize_group(rows, flag_col, group_key, group_label))

    fields = [
        "group_key",
        "group_label",
        "horizon_obs",
        "completed_count",
        "unique_ticker_count",
        "avg_return_pct",
        "median_return_pct",
        "win_rate_pct",
        "best_return_pct",
        "worst_return_pct",
        "min_required_samples",
        "promotion_eval",
    ]

    write_csv(SUMMARY_CSV, summary_rows, fields)

    completed_by_h = {}
    for h in HORIZONS:
        completed_by_h[h] = sum(1 for r in rows if r.get(f"status_{h}obs", "") == "DONE")

    promote_candidates = [
        r for r in summary_rows
        if r["promotion_eval"] == "PROMOTE_CANDIDATE_REVIEW_REQUIRED"
    ]

    reject_candidates = [
        r for r in summary_rows
        if r["promotion_eval"] == "REJECT_CANDIDATE"
    ]

    if sum(completed_by_h.values()) == 0:
        status = "OK_PROMOTION_RULES_READY_NO_COMPLETED_OUTCOMES_YET"
        recommendation = "NO_PROMOTION_DATA_INSUFFICIENT"
    elif promote_candidates:
        status = "OK_PROMOTION_RULES_UPDATED_WITH_CANDIDATES"
        recommendation = "REVIEW_PROMOTION_CANDIDATES_SHADOW_ONLY"
    else:
        status = "OK_PROMOTION_RULES_UPDATED_NO_PROMOTION"
        recommendation = "KEEP_WATCHING"

    snapshot_dates = sorted(set(str(r.get("snapshot_price_date", "")).strip() for r in rows if str(r.get("snapshot_price_date", "")).strip()))
    latest_snapshot_date = snapshot_dates[-1] if snapshot_dates else "UNKNOWN"

    final_action = get_key(integrated_text, "FINAL_ACTION", "UNKNOWN")
    buy_permission = get_key(integrated_text, "BUY_PERMISSION", "UNKNOWN")
    factor_overlap = get_key(integrated_text, "FACTOR_PACK_OVERLAP_NAMES", "UNKNOWN")
    selected_factor = get_key(integrated_text, "SELECTED_FACTOR", "UNKNOWN")

    read_lines = [
        "=== V18.4B FACTOR OUTCOME SUMMARY AND PROMOTION RULES ===",
        "",
        f"V18_4B_STATUS: {status}",
        f"RUN_TIME: {RUN_TIME}",
        "",
        f"TRACKER_CSV: {TRACKER_CSV}",
        f"TRACKER_TOTAL_ROWS: {len(rows)}",
        f"SNAPSHOT_DATE_COUNT: {len(snapshot_dates)}",
        f"LATEST_SNAPSHOT_PRICE_DATE: {latest_snapshot_date}",
        "",
        f"COMPLETED_1OBS_COUNT: {completed_by_h[1]}",
        f"COMPLETED_3OBS_COUNT: {completed_by_h[3]}",
        f"COMPLETED_5OBS_COUNT: {completed_by_h[5]}",
        f"COMPLETED_10OBS_COUNT: {completed_by_h[10]}",
        f"COMPLETED_20OBS_COUNT: {completed_by_h[20]}",
        "",
        f"FINAL_ACTION: {final_action}",
        f"BUY_PERMISSION: {buy_permission}",
        f"SELECTED_FACTOR: {selected_factor}",
        f"FACTOR_PACK_OVERLAP_NAMES: {factor_overlap}",
        "",
        f"PROMOTION_RECOMMENDATION: {recommendation}",
        f"PROMOTION_CANDIDATE_COUNT: {len(promote_candidates)}",
        f"REJECT_CANDIDATE_COUNT: {len(reject_candidates)}",
        "",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "PROMOTION_ACTION: NONE",
        "",
        f"SUMMARY_CSV: {SUMMARY_CSV}",
        f"RULES_MD: {RULES_MD}",
        f"GLOBAL_MD: {GLOBAL_MD}",
        f"READ_FIRST: {READ_FIRST}",
    ]

    READ_FIRST.write_text("\n".join(read_lines) + "\n", encoding="utf-8")

    md = [
        "# V18.4B Factor Outcome Summary and Promotion Rules",
        "",
        f"- V18_4B_STATUS: `{status}`",
        f"- RUN_TIME: `{RUN_TIME}`",
        f"- TRACKER_TOTAL_ROWS: `{len(rows)}`",
        f"- SNAPSHOT_DATE_COUNT: `{len(snapshot_dates)}`",
        f"- LATEST_SNAPSHOT_PRICE_DATE: `{latest_snapshot_date}`",
        "",
        "## Current Decision Context",
        "",
        f"- FINAL_ACTION: `{final_action}`",
        f"- BUY_PERMISSION: `{buy_permission}`",
        f"- SELECTED_FACTOR: `{selected_factor}`",
        f"- FACTOR_PACK_OVERLAP_NAMES: `{factor_overlap}`",
        "",
        "## Completed Forward Observations",
        "",
        "| horizon | completed_count |",
        "|---:|---:|",
    ]

    for h in HORIZONS:
        md.append(f"| {h}obs | {completed_by_h[h]} |")

    md += [
        "",
        "## Group Outcome Summary",
        "",
        "| group | horizon | completed | avg % | median % | win rate % | min n | eval |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for r in summary_rows:
        md.append(
            f"| {r['group_key']} | {r['horizon_obs']}obs | {r['completed_count']} | "
            f"{r['avg_return_pct'] or 'NA'} | {r['median_return_pct'] or 'NA'} | "
            f"{r['win_rate_pct'] or 'NA'} | {r['min_required_samples']} | {r['promotion_eval']} |"
        )

    md += [
        "",
        "## Promotion Rules",
        "",
        "A group can only become a promotion candidate when all of these are true:",
        "",
        "1. Completed sample count reaches the group-specific minimum.",
        "2. Average return is at least +1.0%.",
        "3. Median return is at least +0.5%.",
        "4. Win rate is at least 55%.",
        "5. The confirming horizon is 5obs, 10obs, or 20obs.",
        "",
        "Current promotion recommendation:",
        "",
        f"- PROMOTION_RECOMMENDATION: `{recommendation}`",
        f"- PROMOTION_CANDIDATE_COUNT: `{len(promote_candidates)}`",
        f"- REJECT_CANDIDATE_COUNT: `{len(reject_candidates)}`",
        "",
        "## Safety",
        "",
        "- OFFICIAL_DECISION_IMPACT: `NONE`",
        "- PROMOTION_ACTION: `NONE`",
        "",
        "This module is evaluation-only. It does not change official BUY/NO_BUY decisions.",
    ]

    RULES_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    GLOBAL_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n".join(read_lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("V18_4B_STATUS: FAIL")
        print("ERROR:", str(e))
        sys.exit(1)