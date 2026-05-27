from pathlib import Path
from datetime import datetime
import csv
import re
import statistics
import sys

ROOT = Path(r"D:\us-tech-quant")
OUT_DIR = ROOT / "outputs" / "v18" / "forward_outcome"
STATE_DIR = ROOT / "state" / "v18" / "forward_outcome"
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
RUN_DATE = datetime.now().strftime("%Y-%m-%d")

TRACKER_CSV = STATE_DIR / "V18_4A_FACTOR_FORWARD_TRACKER.csv"
CURRENT_SNAPSHOT_CSV = OUT_DIR / "V18_4A_CURRENT_FACTOR_SNAPSHOT.csv"
CURRENT_SUMMARY_MD = OUT_DIR / "V18_4A_CURRENT_FORWARD_OUTCOME_SUMMARY.md"
READ_FIRST = OUT_DIR / "V18_4A_READ_FIRST.txt"
GLOBAL_CURRENT_MD = OUT_DIR / "V18_CURRENT_FORWARD_OUTCOME_SUMMARY.md"

RANKING_PATHS = [
    ROOT / "outputs" / "v18" / "factor_pack" / "V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    ROOT / "outputs" / "v18" / "factor_pack" / "V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    ROOT / "outputs" / "v18" / "factor_pack" / "V18_3D_RAW105_FACTOR_PACK_RANKING.csv",
]

VALUES_PATHS = [
    ROOT / "outputs" / "v18" / "factor_pack" / "V18_CURRENT_RAW105_FACTOR_PACK_VALUES.csv",
    ROOT / "outputs" / "v18" / "factor_pack" / "V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_VALUES.csv",
    ROOT / "outputs" / "v18" / "factor_pack" / "V18_3D_RAW105_FACTOR_PACK_VALUES.csv",
]

COCKPIT_PATHS = [
    ROOT / "outputs" / "v18" / "cockpit" / "V18_CURRENT_DAILY_COCKPIT.md",
    ROOT / "outputs" / "v18" / "cockpit" / "V18_3E_CURRENT_DAILY_COCKPIT.txt",
    ROOT / "outputs" / "v18" / "cockpit" / "V18_3E_R2_READ_FIRST.txt",
]

PRICE_PATHS = [
    ROOT / "outputs" / "v17" / "price" / "v17_6E_screened_universe_latest_prices.csv",
    ROOT / "outputs" / "v17" / "raw105_decision" / "v17_8B_raw105_decision_readable_panel.csv",
    ROOT / "outputs" / "v17" / "raw105_decision" / "V17_8D_CURRENT_RAW105_DECISION_PANEL.csv",
]

HORIZONS = [1, 3, 5, 10, 20]

BASE_FIELDS = [
    "snapshot_run_date",
    "snapshot_price_date",
    "ticker",
    "latest_close",
    "rank_overall",
    "composite_score",
    "group_factor_top10",
    "group_factor_top30",
    "group_official_review",
    "group_factor_pack_overlap",
    "group_v18_3c_overlap",
    "selected_factor",
    "official_final_action",
    "buy_permission",
    "official_decision_impact",
    "promotion_action",
]

RET_FIELDS = []
for h in HORIZONS:
    RET_FIELDS += [
        f"return_{h}obs_pct",
        f"target_price_date_{h}obs",
        f"target_close_{h}obs",
        f"status_{h}obs",
    ]

FIELDS = BASE_FIELDS + RET_FIELDS


def first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None


def read_text(path):
    if not path or not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
    return path.read_text(errors="ignore")


def read_csv_rows(path):
    if not path or not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def norm_ticker(x):
    if x is None:
        return ""
    return str(x).strip().upper().replace(".", "-")


def get_col(row, names):
    lower = {str(k).strip().lower(): k for k in row.keys()}
    for n in names:
        k = lower.get(n.lower())
        if k is not None:
            v = row.get(k, "")
            if v is not None and str(v).strip() != "":
                return str(v).strip()
    return ""


def to_float(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("%", "")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def get_key(text, key, default="UNKNOWN"):
    if not text:
        return default
    pat = re.compile(r"^\s*" + re.escape(key) + r"\s*:\s*(.+?)\s*$", re.M)
    m = pat.search(text)
    if m:
        return m.group(1).strip()
    return default


def parse_names(value):
    if not value or value == "UNKNOWN" or value == "NONE":
        return []
    parts = re.split(r"[,，\s]+", value)
    return [norm_ticker(x) for x in parts if norm_ticker(x)]


def get_cockpit_text():
    buf = []
    for p in COCKPIT_PATHS:
        if p.exists():
            buf.append(f"\n--- FILE: {p} ---\n")
            buf.append(read_text(p))
    return "\n".join(buf)


def get_price_maps(values_rows, price_rows):
    price_by_ticker = {}
    date_by_ticker = {}

    rows = []
    rows.extend(values_rows)
    rows.extend(price_rows)

    for r in rows:
        t = norm_ticker(get_col(r, ["ticker", "symbol", "name"]))
        if not t:
            continue

        close = get_col(r, [
            "latest_close", "latest_price", "close", "Close", "adj_close",
            "last_close", "price", "latest"
        ])
        date = get_col(r, [
            "latest_price_date", "price_date", "date", "Date",
            "latest_date", "asof_date", "snapshot_price_date"
        ])

        f = to_float(close)
        if f is not None:
            price_by_ticker[t] = f
        if date:
            date_by_ticker[t] = date[:10]

    return price_by_ticker, date_by_ticker


def rank_sort_key(row, idx):
    r = to_float(get_col(row, [
        "rank_overall", "overall_rank", "factor_rank", "rank",
        "composite_rank", "F010_XSEC_COMPOSITE_RANK"
    ]))
    if r is None:
        return idx + 1
    return r


def get_score(row):
    return get_col(row, [
        "composite_score", "final_score", "score",
        "F010_XSEC_COMPOSITE_RANK", "factor_pack_score"
    ])


def load_tracker():
    if not TRACKER_CSV.exists():
        return []
    return read_csv_rows(TRACKER_CSV)


def upsert_rows(existing, new_rows):
    by_key = {}
    for r in existing:
        key = (r.get("snapshot_price_date", ""), norm_ticker(r.get("ticker", "")))
        if key[0] and key[1]:
            by_key[key] = r
    for r in new_rows:
        key = (r.get("snapshot_price_date", ""), norm_ticker(r.get("ticker", "")))
        if key[0] and key[1]:
            old = by_key.get(key, {})
            merged = dict(old)
            merged.update(r)
            by_key[key] = merged
    return list(by_key.values())


def recompute_forward_returns(rows):
    price_dates = sorted(set(r.get("snapshot_price_date", "") for r in rows if r.get("snapshot_price_date", "")))
    date_index = {d: i for i, d in enumerate(price_dates)}

    px = {}
    for r in rows:
        d = r.get("snapshot_price_date", "")
        t = norm_ticker(r.get("ticker", ""))
        c = to_float(r.get("latest_close", ""))
        if d and t and c is not None:
            px[(d, t)] = c

    for r in rows:
        d0 = r.get("snapshot_price_date", "")
        t = norm_ticker(r.get("ticker", ""))
        c0 = to_float(r.get("latest_close", ""))

        for h in HORIZONS:
            ret_k = f"return_{h}obs_pct"
            td_k = f"target_price_date_{h}obs"
            tc_k = f"target_close_{h}obs"
            st_k = f"status_{h}obs"

            if not d0 or t == "" or c0 is None or c0 == 0 or d0 not in date_index:
                r[st_k] = "BASE_PRICE_MISSING"
                continue

            target_i = date_index[d0] + h
            if target_i >= len(price_dates):
                r[st_k] = "PENDING"
                continue

            d1 = price_dates[target_i]
            c1 = px.get((d1, t))
            if c1 is None:
                r[st_k] = "TARGET_PRICE_MISSING"
                r[td_k] = d1
                continue

            ret = (c1 / c0 - 1.0) * 100.0
            r[ret_k] = f"{ret:.4f}"
            r[td_k] = d1
            r[tc_k] = f"{c1:.6f}"
            r[st_k] = "DONE"

    return rows


def summarize_group(rows, group_col):
    out = {}
    selected = [r for r in rows if str(r.get(group_col, "")).upper() == "TRUE"]
    for h in HORIZONS:
        vals = []
        for r in selected:
            if r.get(f"status_{h}obs", "") == "DONE":
                v = to_float(r.get(f"return_{h}obs_pct", ""))
                if v is not None:
                    vals.append(v)

        if vals:
            out[h] = {
                "count": len(vals),
                "avg": sum(vals) / len(vals),
                "median": statistics.median(vals),
                "win_rate": sum(1 for v in vals if v > 0) / len(vals) * 100.0,
            }
        else:
            out[h] = {
                "count": 0,
                "avg": None,
                "median": None,
                "win_rate": None,
            }
    return out


def fmt(x):
    if x is None:
        return "NA"
    return f"{x:.4f}"


def main():
    ranking_path = first_existing(RANKING_PATHS)
    values_path = first_existing(VALUES_PATHS)
    cockpit_text = get_cockpit_text()

    if not ranking_path:
        raise RuntimeError("RANKING_SOURCE_NOT_FOUND")

    ranking_rows = read_csv_rows(ranking_path)
    values_rows = read_csv_rows(values_path) if values_path else []

    price_rows = []
    for p in PRICE_PATHS:
        if p.exists():
            price_rows.extend(read_csv_rows(p))

    price_by_ticker, date_by_ticker = get_price_maps(values_rows, price_rows)

    values_by_ticker = {}
    for r in values_rows:
        t = norm_ticker(get_col(r, ["ticker", "symbol", "name"]))
        if t:
            values_by_ticker[t] = r

    official_names = parse_names(get_key(cockpit_text, "OFFICIAL_REVIEW_NAMES", ""))
    pack_overlap_names = parse_names(get_key(cockpit_text, "V18_3D_R2_OVERLAP_NAMES", ""))
    c3_overlap_names = parse_names(get_key(cockpit_text, "V18_3C_OVERLAP_NAMES", ""))

    selected_factor = get_key(cockpit_text, "SELECTED_FACTOR", "UNKNOWN")
    final_action = get_key(cockpit_text, "FINAL_ACTION", "UNKNOWN")
    buy_permission = get_key(cockpit_text, "BUY_PERMISSION", "UNKNOWN")
    decision_impact = get_key(cockpit_text, "OFFICIAL_DECISION_IMPACT", "NONE")
    promotion_action = get_key(cockpit_text, "PROMOTION_ACTION", "NONE")

    decorated = []
    for i, r in enumerate(ranking_rows):
        t = norm_ticker(get_col(r, ["ticker", "symbol", "name"]))
        if not t:
            continue
        decorated.append((rank_sort_key(r, i), i, t, r))

    decorated.sort(key=lambda x: (x[0], x[1]))

    top10 = [x[2] for x in decorated[:10]]
    top30 = [x[2] for x in decorated[:30]]

    current_rows = []
    price_missing = []

    for order_idx, (_, _, t, r) in enumerate(decorated, start=1):
        vrow = values_by_ticker.get(t, {})
        close = None
        date = ""

        for src in (r, vrow):
            close = to_float(get_col(src, [
                "latest_close", "latest_price", "close", "Close", "price", "last_close"
            ]))
            date = get_col(src, [
                "latest_price_date", "price_date", "date", "Date", "latest_date"
            ])
            if close is not None:
                break

        if close is None:
            close = price_by_ticker.get(t)
        if not date:
            date = date_by_ticker.get(t, RUN_DATE)

        if close is None:
            price_missing.append(t)
            continue

        rank_value = get_col(r, [
            "rank_overall", "overall_rank", "factor_rank", "rank",
            "composite_rank"
        ])
        if not rank_value:
            rank_value = str(order_idx)

        row = {
            "snapshot_run_date": RUN_DATE,
            "snapshot_price_date": str(date)[:10],
            "ticker": t,
            "latest_close": f"{close:.6f}",
            "rank_overall": rank_value,
            "composite_score": get_score(r),
            "group_factor_top10": "TRUE" if t in top10 else "FALSE",
            "group_factor_top30": "TRUE" if t in top30 else "FALSE",
            "group_official_review": "TRUE" if t in official_names else "FALSE",
            "group_factor_pack_overlap": "TRUE" if t in pack_overlap_names else "FALSE",
            "group_v18_3c_overlap": "TRUE" if t in c3_overlap_names else "FALSE",
            "selected_factor": selected_factor,
            "official_final_action": final_action,
            "buy_permission": buy_permission,
            "official_decision_impact": decision_impact,
            "promotion_action": promotion_action,
        }

        for f in RET_FIELDS:
            row[f] = ""

        current_rows.append(row)

    existing = load_tracker()
    merged = upsert_rows(existing, current_rows)
    merged = recompute_forward_returns(merged)
    merged.sort(key=lambda r: (r.get("snapshot_price_date", ""), norm_ticker(r.get("ticker", ""))))

    write_csv(TRACKER_CSV, merged, FIELDS)
    write_csv(CURRENT_SNAPSHOT_CSV, current_rows, FIELDS)

    summaries = {
        "factor_top10": summarize_group(merged, "group_factor_top10"),
        "factor_top30": summarize_group(merged, "group_factor_top30"),
        "official_review": summarize_group(merged, "group_official_review"),
        "factor_pack_overlap": summarize_group(merged, "group_factor_pack_overlap"),
        "v18_3c_overlap": summarize_group(merged, "group_v18_3c_overlap"),
    }

    completed_counts = {}
    for h in HORIZONS:
        completed_counts[h] = sum(1 for r in merged if r.get(f"status_{h}obs", "") == "DONE")

    status = "OK_FORWARD_TRACKER_UPDATED"
    if not current_rows:
        status = "FAIL_NO_CURRENT_ROWS"
    elif price_missing:
        status = "WARN_FORWARD_TRACKER_UPDATED_WITH_PRICE_MISSING"

    current_price_dates = sorted(set(r["snapshot_price_date"] for r in current_rows))

    read_lines = [
        "=== V18.4A FACTOR FORWARD OUTCOME TRACKER ===",
        "",
        f"V18_4A_STATUS: {status}",
        f"RUN_TIME: {RUN_TIME}",
        "",
        f"RANKING_SOURCE: {ranking_path}",
        f"VALUES_SOURCE: {values_path if values_path else 'NOT_FOUND'}",
        f"TRACKER_CSV: {TRACKER_CSV}",
        "",
        f"CURRENT_SNAPSHOT_PRICE_DATES: {','.join(current_price_dates) if current_price_dates else 'NONE'}",
        f"CURRENT_SNAPSHOT_COUNT: {len(current_rows)}",
        f"TRACKER_TOTAL_ROWS: {len(merged)}",
        f"PRICE_MISSING_COUNT: {len(price_missing)}",
        f"PRICE_MISSING_NAMES: {','.join(price_missing[:30]) if price_missing else 'NONE'}",
        "",
        f"TOP10_NAMES: {','.join(top10)}",
        f"TOP30_COUNT: {len(top30)}",
        f"OFFICIAL_REVIEW_NAMES: {','.join(official_names) if official_names else 'NONE'}",
        f"FACTOR_PACK_OVERLAP_NAMES: {','.join(pack_overlap_names) if pack_overlap_names else 'NONE'}",
        f"V18_3C_OVERLAP_NAMES: {','.join(c3_overlap_names) if c3_overlap_names else 'NONE'}",
        "",
        f"SELECTED_FACTOR: {selected_factor}",
        f"FINAL_ACTION: {final_action}",
        f"BUY_PERMISSION: {buy_permission}",
        "",
    ]

    for h in HORIZONS:
        read_lines.append(f"COMPLETED_{h}OBS_COUNT: {completed_counts[h]}")

    read_lines += [
        "",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "PROMOTION_ACTION: NONE",
        "",
        f"CURRENT_SNAPSHOT_CSV: {CURRENT_SNAPSHOT_CSV}",
        f"CURRENT_SUMMARY_MD: {CURRENT_SUMMARY_MD}",
        f"GLOBAL_CURRENT_MD: {GLOBAL_CURRENT_MD}",
        f"READ_FIRST: {READ_FIRST}",
    ]

    READ_FIRST.write_text("\n".join(read_lines) + "\n", encoding="utf-8")

    md = [
        "# V18.4A Factor Forward Outcome Tracker",
        "",
        f"- V18_4A_STATUS: `{status}`",
        f"- RUN_TIME: `{RUN_TIME}`",
        f"- CURRENT_SNAPSHOT_COUNT: `{len(current_rows)}`",
        f"- TRACKER_TOTAL_ROWS: `{len(merged)}`",
        f"- CURRENT_SNAPSHOT_PRICE_DATES: `{','.join(current_price_dates) if current_price_dates else 'NONE'}`",
        "",
        "## Current Groups",
        "",
        f"- TOP10_NAMES: `{','.join(top10)}`",
        f"- TOP30_COUNT: `{len(top30)}`",
        f"- OFFICIAL_REVIEW_NAMES: `{','.join(official_names) if official_names else 'NONE'}`",
        f"- FACTOR_PACK_OVERLAP_NAMES: `{','.join(pack_overlap_names) if pack_overlap_names else 'NONE'}`",
        f"- V18_3C_OVERLAP_NAMES: `{','.join(c3_overlap_names) if c3_overlap_names else 'NONE'}`",
        "",
        "## Forward Outcome Summary",
        "",
        "| group | horizon | completed_count | avg_return_pct | median_return_pct | win_rate_pct |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for group, sm in summaries.items():
        for h in HORIZONS:
            item = sm[h]
            md.append(
                f"| {group} | {h}obs | {item['count']} | {fmt(item['avg'])} | {fmt(item['median'])} | {fmt(item['win_rate'])} |"
            )

    md += [
        "",
        "## Safety",
        "",
        "- OFFICIAL_DECISION_IMPACT: `NONE`",
        "- PROMOTION_ACTION: `NONE`",
        "",
        "This module is forward-validation only. It does not change official BUY/NO_BUY decisions.",
    ]

    CURRENT_SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    GLOBAL_CURRENT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n".join(read_lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("V18_4A_STATUS: FAIL")
        print("ERROR:", str(e))
        sys.exit(1)