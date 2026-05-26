import argparse
import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv_rows(path: Path):
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def write_csv_rows(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def extract_field(text: str, label: str, default: str = "UNKNOWN") -> str:
    if not text:
        return default

    prefixes = [
        f"{label}:",
        f"- {label}:",
        f"* {label}:",
        f"{label}：",
        f"- {label}：",
        f"* {label}：",
    ]

    for line in text.splitlines():
        t = line.strip().strip("\r")
        for p in prefixes:
            if t.upper().startswith(p.upper()):
                v = t[len(p):].strip().strip("`").strip()
                if v:
                    return v

    return default


def normalize_num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("$", "").replace("¥", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def pick_col(rows, candidates):
    if not rows:
        return None

    cols = list(rows[0].keys())
    lower = {c.lower(): c for c in cols}

    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]

    for c in cols:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c

    return None


def classify_official_permission(final_action: str, buy_permission: str) -> str:
    blob = f"{final_action} {buy_permission}".upper()

    block_words = [
        "NO_BUY",
        "NO_NEW_BUYS",
        "NO_TRADE",
        "BLOCK",
        "LOCKED",
        "WAIT",
        "EVENT",
        "BUDGET_LOCKED",
    ]

    allow_words = [
        "BUY_NOW",
        "EXECUTE",
        "TRIAL",
        "PROBE",
        "ALLOW",
        "YES",
    ]

    if any(w in blob for w in block_words):
        return "OFFICIAL_BLOCKED"

    if any(w in blob for w in allow_words):
        return "OFFICIAL_ALLOWED"

    return "OFFICIAL_UNKNOWN_CONSERVATIVE_BLOCK"


def detect_tags(row):
    txt = " ".join(str(v) for v in row.values() if v is not None).upper()

    tag_map = [
        ("WATCH_POSITIVE", ["WATCH_POSITIVE"]),
        ("PULLBACK_WATCH", ["PULLBACK_WATCH"]),
        ("BB_SQUEEZE", ["BB_SQUEEZE", "SQUEEZE"]),
        ("BREAKOUT_CONTINUATION", ["BREAKOUT_CONTINUATION", "BREAKOUT"]),
        ("EXHAUSTION_RISK", ["EXHAUSTION_RISK", "EXHAUSTION"]),
        ("OVERHEAT_UNCLASSIFIED", ["OVERHEAT_UNCLASSIFIED"]),
        ("OLD_OVERHEAT", ["OLD_OVERHEAT"]),
        ("STALE", ["STALE"]),
        ("LOW_COVERAGE", ["LOW_COVERAGE"]),
        ("FAIL", ["FAIL"]),
    ]

    tags = []
    for tag, needles in tag_map:
        if any(n in txt for n in needles):
            tags.append(tag)

    # de-duplicate while preserving order
    out = []
    seen = set()
    for t in tags:
        if t not in seen:
            out.append(t)
            seen.add(t)

    return out


def classify_candidate(tags, official_permission):
    tag_set = set(tags)

    positive_tags = {
        "WATCH_POSITIVE",
        "PULLBACK_WATCH",
        "BB_SQUEEZE",
        "BREAKOUT_CONTINUATION",
    }

    tech_risk_tags = {
        "EXHAUSTION_RISK",
        "OVERHEAT_UNCLASSIFIED",
        "OLD_OVERHEAT",
    }

    stale_tags = {
        "STALE",
        "LOW_COVERAGE",
        "FAIL",
    }

    reasons = []

    if official_permission != "OFFICIAL_ALLOWED":
        reasons.append("OFFICIAL_BLOCKED")

    if tag_set & stale_tags:
        reasons.append("TECH_STALE_OR_LOW_COVERAGE")

    if tag_set & tech_risk_tags:
        reasons.append("TECH_OVERHEAT_OR_EXHAUSTION")

    if not (tag_set & positive_tags):
        reasons.append("NO_ACTIONABLE_POSITIVE_TECH_TAG")

    eligible = (
        official_permission == "OFFICIAL_ALLOWED"
        and bool(tag_set & positive_tags)
        and not bool(tag_set & stale_tags)
        and not bool(tag_set & tech_risk_tags)
    )

    if eligible:
        bucket = "SIM_ELIGIBLE_IF_CASH_AVAILABLE"
        reason = "ELIGIBLE_BY_OFFICIAL_AND_TECH"
    elif "OFFICIAL_BLOCKED" in reasons:
        bucket = "OBSERVE_ONLY_OFFICIAL_BLOCKED"
        reason = "+".join(reasons)
    elif "TECH_STALE_OR_LOW_COVERAGE" in reasons:
        bucket = "BLOCKED_BY_TECH_FRESHNESS"
        reason = "+".join(reasons)
    elif "TECH_OVERHEAT_OR_EXHAUSTION" in reasons:
        bucket = "OBSERVE_ONLY_TECH_RISK"
        reason = "+".join(reasons)
    else:
        bucket = "OBSERVE_ONLY_OTHER"
        reason = "+".join(reasons) if reasons else "OBSERVE_ONLY"

    return eligible, bucket, reason


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--max-report-rows", type=int, default=40)
    args = ap.parse_args()

    root = Path(args.root)

    read_center_dir = root / "outputs" / "v18" / "read_center"
    sim_out_dir = root / "outputs" / "v18" / "simulation"
    sim_state_dir = root / "state" / "v18" / "simulation"
    tech_dir = root / "outputs" / "v18" / "technical_timing_read_center"

    sim_out_dir.mkdir(parents=True, exist_ok=True)
    sim_state_dir.mkdir(parents=True, exist_ok=True)

    official_read_first = read_center_dir / "V18_8C_READ_FIRST.txt"
    official_report = read_center_dir / "V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION.md"
    fallback_official_read_first = read_center_dir / "V18_6E_READ_FIRST.txt"
    fallback_official_report = read_center_dir / "V18_6E_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md"

    sim_read_first = sim_out_dir / "V18_8B_READ_FIRST.txt"
    sim_report = sim_out_dir / "V18_CURRENT_SIM_CABIN.md"

    tech_dash = tech_dir / "V18_6D_CURRENT_TECHNICAL_TIMING_DASHBOARD.csv"

    state_tracker = sim_state_dir / "V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"
    output_tracker = sim_out_dir / "V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"
    output_today = sim_out_dir / "V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv"
    report_path = sim_out_dir / "V18_9A_CURRENT_SIM_CANDIDATE_TRACKER.md"
    read_first = sim_out_dir / "V18_9A_READ_FIRST.txt"

    status_text = "\n".join([
        read_text(official_read_first),
        read_text(official_report),
        read_text(fallback_official_read_first),
        read_text(fallback_official_report),
        read_text(sim_read_first),
        read_text(sim_report),
    ])

    final_action = extract_field(status_text, "FINAL_ACTION")
    buy_permission = extract_field(status_text, "BUY_PERMISSION")
    vix_regime = extract_field(status_text, "VIX_REGIME")
    official_impact = extract_field(status_text, "OFFICIAL_DECISION_IMPACT")
    sim_status = extract_field(status_text, "SIM_STATUS")
    if sim_status == "UNKNOWN":
        sim_status = extract_field(status_text, "STATUS")
    official_permission = extract_field(status_text, "OFFICIAL_PERMISSION")
    if official_permission == "UNKNOWN":
        official_permission = classify_official_permission(final_action, buy_permission)

    tech_rows = read_csv_rows(tech_dash)

    sim_date = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fieldnames = [
        "snapshot_date",
        "timestamp",
        "ticker",
        "latest_price_usd",
        "technical_tags",
        "candidate_bucket",
        "eligible_sim_buy",
        "blocked_or_observe_reason",
        "official_permission",
        "final_action",
        "buy_permission",
        "vix_regime",
        "official_decision_impact",
        "sim_status",
        "source_file",
        "source_row_text",
        "fwd_1d_return",
        "fwd_5d_return",
        "fwd_10d_return",
        "fwd_20d_return",
        "forward_status",
    ]

    old_rows = read_csv_rows(state_tracker) if state_tracker.exists() else []
    old_rows = [r for r in old_rows if r.get("snapshot_date") != sim_date]

    today_rows = []

    if tech_rows:
        ticker_col = pick_col(tech_rows, ["ticker", "symbol"])
        price_col = pick_col(tech_rows, ["latest_close", "last_close", "close", "price", "adj_close"])

        seen = set()

        for r in tech_rows:
            if not ticker_col:
                continue

            ticker = str(r.get(ticker_col, "")).strip().upper()
            if not ticker or ticker in seen:
                continue

            tags = detect_tags(r)
            if not tags:
                continue

            price = normalize_num(r.get(price_col)) if price_col else None
            eligible, bucket, reason = classify_candidate(tags, official_permission)

            raw_text = " | ".join(
                f"{k}={v}" for k, v in r.items()
                if v is not None and str(v).strip() != ""
            )

            today_rows.append({
                "snapshot_date": sim_date,
                "timestamp": now,
                "ticker": ticker,
                "latest_price_usd": f"{price:.4f}" if price is not None else "",
                "technical_tags": ";".join(tags),
                "candidate_bucket": bucket,
                "eligible_sim_buy": "YES" if eligible else "NO",
                "blocked_or_observe_reason": reason,
                "official_permission": official_permission,
                "final_action": final_action,
                "buy_permission": buy_permission,
                "vix_regime": vix_regime,
                "official_decision_impact": official_impact,
                "sim_status": sim_status,
                "source_file": str(tech_dash),
                "source_row_text": raw_text[:800],
                "fwd_1d_return": "",
                "fwd_5d_return": "",
                "fwd_10d_return": "",
                "fwd_20d_return": "",
                "forward_status": "PENDING_FORWARD_RETURNS",
            })

            seen.add(ticker)

    all_rows = old_rows + today_rows

    write_csv_rows(state_tracker, all_rows, fieldnames)
    write_csv_rows(output_tracker, all_rows, fieldnames)
    write_csv_rows(output_today, today_rows, fieldnames)

    tag_counter = Counter()
    bucket_counter = Counter()
    reason_counter = Counter()

    for r in today_rows:
        for t in str(r.get("technical_tags", "")).split(";"):
            if t:
                tag_counter[t] += 1
        bucket_counter[r.get("candidate_bucket", "UNKNOWN")] += 1
        reason_counter[r.get("blocked_or_observe_reason", "UNKNOWN")] += 1

    candidate_count = len(today_rows)
    eligible_count = sum(1 for r in today_rows if r.get("eligible_sim_buy") == "YES")
    observe_count = candidate_count - eligible_count

    status = "OK_SIM_CANDIDATE_TRACKER_READY"
    if not tech_dash.exists():
        status = "WARN_TECH_DASHBOARD_MISSING"
    elif candidate_count == 0:
        status = "WARN_NO_TECH_CANDIDATES_FOUND"

    report = []
    report.append("# V18.9A Simulation Candidate Tracker")
    report.append("")
    report.append(f"- STATUS: `{status}`")
    report.append(f"- SNAPSHOT_DATE: `{sim_date}`")
    report.append(f"- GENERATED_AT: `{now}`")
    report.append(f"- MODE: `SHADOW_ONLY`")
    report.append(f"- OFFICIAL_PERMISSION: `{official_permission}`")
    report.append(f"- FINAL_ACTION: `{final_action}`")
    report.append(f"- BUY_PERMISSION: `{buy_permission}`")
    report.append(f"- VIX_REGIME: `{vix_regime}`")
    report.append(f"- OFFICIAL_DECISION_IMPACT: `{official_impact}`")
    report.append(f"- SIM_STATUS: `{sim_status}`")
    report.append("")
    report.append("## Summary")
    report.append("")
    report.append(f"- TODAY_CANDIDATE_COUNT: `{candidate_count}`")
    report.append(f"- ELIGIBLE_SIM_BUY_COUNT: `{eligible_count}`")
    report.append(f"- OBSERVE_OR_BLOCKED_COUNT: `{observe_count}`")
    report.append(f"- TRACKER_TOTAL_ROWS: `{len(all_rows)}`")
    report.append("")
    report.append("## Tag Counts")
    report.append("")
    report.append("| tag | count |")
    report.append("|---|---:|")
    if tag_counter:
        for k, v in tag_counter.most_common():
            report.append(f"| {k} | {v} |")
    else:
        report.append("| NONE | 0 |")

    report.append("")
    report.append("## Bucket Counts")
    report.append("")
    report.append("| bucket | count |")
    report.append("|---|---:|")
    if bucket_counter:
        for k, v in bucket_counter.most_common():
            report.append(f"| {k} | {v} |")
    else:
        report.append("| NONE | 0 |")

    report.append("")
    report.append("## Reason Counts")
    report.append("")
    report.append("| reason | count |")
    report.append("|---|---:|")
    if reason_counter:
        for k, v in reason_counter.most_common():
            report.append(f"| {k} | {v} |")
    else:
        report.append("| NONE | 0 |")

    report.append("")
    report.append("## Today Candidates")
    report.append("")
    report.append("| ticker | price | tags | bucket | eligible | reason |")
    report.append("|---|---:|---|---|---:|---|")
    for r in today_rows[: args.max_report_rows]:
        report.append(
            f"| {r.get('ticker','')} | {r.get('latest_price_usd','')} | "
            f"{r.get('technical_tags','')} | {r.get('candidate_bucket','')} | "
            f"{r.get('eligible_sim_buy','')} | {r.get('blocked_or_observe_reason','')} |"
        )
    if not today_rows:
        report.append("| NONE |  |  |  |  |  |")

    report.append("")
    report.append("## Files")
    report.append("")
    report.append(f"- STATE_TRACKER: `{state_tracker}`")
    report.append(f"- OUTPUT_TRACKER: `{output_tracker}`")
    report.append(f"- OUTPUT_TODAY: `{output_today}`")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first}`")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("- This module is shadow-only.")
    report.append("- It does not modify official buy permission.")
    report.append("- It records which technical candidates were observable today and why they were or were not simulation-eligible.")
    report.append("- Forward-return fields are placeholders for V18.9B.")

    write_text(report_path, "\n".join(report))

    rf = []
    rf.append("V18.9A SIMULATION CANDIDATE TRACKER")
    rf.append("")
    rf.append(f"STATUS: {status}")
    rf.append(f"SNAPSHOT_DATE: {sim_date}")
    rf.append("MODE: SHADOW_ONLY")
    rf.append("")
    rf.append(f"OFFICIAL_PERMISSION: {official_permission}")
    rf.append(f"FINAL_ACTION: {final_action}")
    rf.append(f"BUY_PERMISSION: {buy_permission}")
    rf.append(f"VIX_REGIME: {vix_regime}")
    rf.append(f"OFFICIAL_DECISION_IMPACT: {official_impact}")
    rf.append("")
    rf.append(f"TODAY_CANDIDATE_COUNT: {candidate_count}")
    rf.append(f"ELIGIBLE_SIM_BUY_COUNT: {eligible_count}")
    rf.append(f"OBSERVE_OR_BLOCKED_COUNT: {observe_count}")
    rf.append(f"TRACKER_TOTAL_ROWS: {len(all_rows)}")
    rf.append("")
    rf.append("REPORT:")
    rf.append(str(report_path))
    rf.append("")
    rf.append("STATE_TRACKER:")
    rf.append(str(state_tracker))
    rf.append("")
    rf.append("OUTPUT_TODAY:")
    rf.append(str(output_today))
    rf.append("")
    rf.append("OUTPUT_TRACKER:")
    rf.append(str(output_tracker))

    write_text(read_first, "\n".join(rf))

    print("")
    print("=== V18.9A SIMULATION CANDIDATE TRACKER READY ===")
    print(f"STATUS: {status}")
    print(f"SNAPSHOT_DATE: {sim_date}")
    print(f"OFFICIAL_PERMISSION: {official_permission}")
    print(f"FINAL_ACTION: {final_action}")
    print(f"BUY_PERMISSION: {buy_permission}")
    print(f"VIX_REGIME: {vix_regime}")
    print(f"TODAY_CANDIDATE_COUNT: {candidate_count}")
    print(f"ELIGIBLE_SIM_BUY_COUNT: {eligible_count}")
    print(f"OBSERVE_OR_BLOCKED_COUNT: {observe_count}")
    print(f"TRACKER_TOTAL_ROWS: {len(all_rows)}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first}")
    print("")


if __name__ == "__main__":
    main()
