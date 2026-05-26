import argparse
import importlib.util
import math
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_base_module(root: Path):
    base_path = root / "scripts" / "v18" / "v18_6C_technical_timing_forward_tracker.py"
    if not base_path.exists():
        raise FileNotFoundError(f"Missing base V18.6C script: {base_path}")

    spec = importlib.util.spec_from_file_location("v18_6C_base", base_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def bool_count(df: pd.DataFrame, col: str) -> int:
    if col not in df.columns:
        return 0
    s = df[col]
    if s.dtype == bool:
        return int(s.fillna(False).sum())
    return int(s.astype(str).str.lower().isin(["true", "1", "yes", "y"]).sum())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--min-coverage-ratio", type=float, default=0.80)
    parser.add_argument("--min-date-count", type=int, default=50)
    args = parser.parse_args()

    root = Path(args.root)
    base = load_base_module(root)

    current_path = root / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING.csv"
    tracker_path = root / "state" / "v18" / "V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_TRACKER.csv"

    out_dir = root / "outputs" / "v18" / "technical_timing_forward"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "V18_6C_R1_CURRENT_FRESHNESS_GUARD_REPORT.md"
    global_report_path = out_dir / "V18_CURRENT_TECHNICAL_TIMING_FORWARD_FRESHNESS_GUARD.md"
    read_first_path = out_dir / "V18_6C_R1_READ_FIRST.txt"

    summary_path = out_dir / "V18_6C_R1_CURRENT_TECHNICAL_TIMING_FORWARD_SUMMARY.csv"
    current_stale_audit_path = out_dir / "V18_6C_R1_CURRENT_STALE_PRICE_AUDIT.csv"
    low_coverage_quarantine_path = out_dir / "V18_6C_R1_LOW_COVERAGE_SNAPSHOT_QUARANTINE.csv"
    date_dist_path = out_dir / "V18_6C_R1_SNAPSHOT_DATE_DISTRIBUTION.csv"

    current_raw = base.read_csv_safe(current_path)
    if current_raw.empty:
        raise RuntimeError(f"Missing or empty current V18.6A technical timing file: {current_path}")

    current_all = base.normalize_current_snapshot(current_raw)
    current_all["snapshot_price_date"] = current_all["snapshot_price_date"].astype(str)
    current_all["ticker"] = current_all["ticker"].astype(str)

    current_date_dist = (
        current_all.groupby("snapshot_price_date")
        .size()
        .reset_index(name="current_snapshot_count")
        .sort_values("snapshot_price_date")
    )

    latest_current_date = current_date_dist["snapshot_price_date"].max()

    current_fresh = current_all[current_all["snapshot_price_date"] == latest_current_date].copy()
    current_stale = current_all[current_all["snapshot_price_date"] != latest_current_date].copy()

    write_csv(current_stale, current_stale_audit_path)

    existing = base.read_csv_safe(tracker_path)

    backup_path = ""
    if not existing.empty and tracker_path.exists():
        backup = tracker_path.with_name(f"{tracker_path.stem}.before_V18_6C_R1_{stamp()}.csv")
        shutil.copy2(tracker_path, backup)
        backup_path = str(backup)

    if existing.empty:
        existing_keys = set()
        combined = current_fresh.copy()
    else:
        existing["snapshot_price_date"] = existing["snapshot_price_date"].astype(str)
        existing["ticker"] = existing["ticker"].astype(str)
        existing_keys = set(zip(existing["snapshot_price_date"], existing["ticker"]))
        combined = pd.concat([existing, current_fresh], ignore_index=True, sort=False)

    fresh_keys = set(zip(current_fresh["snapshot_price_date"], current_fresh["ticker"]))
    new_rows = len(fresh_keys - existing_keys)

    combined["snapshot_price_date"] = combined["snapshot_price_date"].astype(str)
    combined["ticker"] = combined["ticker"].astype(str)
    combined = combined.drop_duplicates(subset=["snapshot_price_date", "ticker"], keep="last")
    combined = combined.sort_values(["snapshot_price_date", "ticker"]).reset_index(drop=True)

    combined_date_dist = (
        combined.groupby("snapshot_price_date")
        .size()
        .reset_index(name="tracker_snapshot_count")
        .sort_values("snapshot_price_date")
    )

    max_count = int(combined_date_dist["tracker_snapshot_count"].max()) if not combined_date_dist.empty else 0
    min_valid_count = max(args.min_date_count, int(math.floor(max_count * args.min_coverage_ratio)))

    valid_dates = set(
        combined_date_dist.loc[
            combined_date_dist["tracker_snapshot_count"] >= min_valid_count,
            "snapshot_price_date"
        ].astype(str)
    )

    low_coverage = combined[~combined["snapshot_price_date"].isin(valid_dates)].copy()
    cleaned = combined[combined["snapshot_price_date"].isin(valid_dates)].copy()

    write_csv(low_coverage, low_coverage_quarantine_path)

    date_dist = combined_date_dist.copy()
    date_dist["min_valid_count"] = min_valid_count
    date_dist["date_status"] = date_dist["snapshot_price_date"].astype(str).apply(
        lambda d: "KEEP_VALID_SNAPSHOT_DATE" if d in valid_dates else "QUARANTINE_LOW_COVERAGE_DATE"
    )
    write_csv(date_dist, date_dist_path)

    updated = base.update_forward_outcomes(cleaned)
    summary = base.summarize_tracker(updated)

    base.write_csv(updated, tracker_path)
    stamped_tracker = tracker_path.with_name(f"V18_6C_R1_TECHNICAL_TIMING_FORWARD_TRACKER_{stamp()}.csv")
    base.write_csv(updated, stamped_tracker)
    base.write_csv(summary, summary_path)

    snapshot_dates = sorted(updated["snapshot_price_date"].astype(str).dropna().unique().tolist())
    latest_tracker_date = snapshot_dates[-1] if snapshot_dates else ""

    completed_counts = {h: bool_count(updated, f"completed_{h}") for h in [1, 3, 5, 10, 20]}

    stale_preview_cols = [
        "snapshot_price_date", "ticker", "baseline_close",
        "technical_timing_score", "technical_signal",
        "bb_status", "rsi_status", "kdj_status"
    ]
    stale_preview = current_stale[stale_preview_cols] if not current_stale.empty else pd.DataFrame(columns=stale_preview_cols)

    def table(df):
        if df is None or df.empty:
            return "_EMPTY_"
        return df.to_markdown(index=False)

    report = f"""# V18.6C-R1 Technical Timing Forward Tracker Freshness Guard

## 1. Status

- V18_6C_R1_STATUS: `OK_FRESHNESS_GUARD_READY`
- CURRENT_SNAPSHOT_ROWS: `{len(current_all)}`
- FRESH_CURRENT_ROWS: `{len(current_fresh)}`
- STALE_CURRENT_ROWS: `{len(current_stale)}`
- NEW_TRACKER_ROWS_ADDED: `{new_rows}`
- TRACKER_TOTAL_ROWS_AFTER_CLEAN: `{len(updated)}`
- SNAPSHOT_DATE_COUNT_AFTER_CLEAN: `{len(snapshot_dates)}`
- LATEST_TRACKER_SNAPSHOT_PRICE_DATE: `{latest_tracker_date}`
- LOW_COVERAGE_QUARANTINE_ROWS: `{len(low_coverage)}`
- MIN_VALID_DATE_COUNT: `{min_valid_count}`
- OFFICIAL_DECISION_IMPACT: `NONE`

## 2. Current Snapshot Date Distribution

{table(current_date_dist)}

## 3. Stale Current Rows

{table(stale_preview)}

## 4. Tracker Date Distribution After Guard

{table(date_dist)}

## 5. Completed Forward Outcome Counts

- COMPLETED_1D_COUNT: `{completed_counts.get(1, 0)}`
- COMPLETED_3D_COUNT: `{completed_counts.get(3, 0)}`
- COMPLETED_5D_COUNT: `{completed_counts.get(5, 0)}`
- COMPLETED_10D_COUNT: `{completed_counts.get(10, 0)}`
- COMPLETED_20D_COUNT: `{completed_counts.get(20, 0)}`

## 6. Output Files

- TRACKER: `{tracker_path}`
- SUMMARY: `{summary_path}`
- CURRENT_STALE_AUDIT: `{current_stale_audit_path}`
- LOW_COVERAGE_QUARANTINE: `{low_coverage_quarantine_path}`
- DATE_DISTRIBUTION: `{date_dist_path}`
- BACKUP_BEFORE_PATCH: `{backup_path}`

## 7. Interpretation

This guard excludes stale current technical timing rows from the forward tracker.
It also quarantines low-coverage snapshot dates that were likely created by stale ticker contamination.

Official decision impact remains `NONE`.
"""
    report_path.write_text(report, encoding="utf-8")
    global_report_path.write_text(report, encoding="utf-8")

    read_first = f"""V18.6C-R1 TECHNICAL TIMING FORWARD TRACKER FRESHNESS GUARD READ FIRST

STATUS:
OK_FRESHNESS_GUARD_READY

CURRENT_SNAPSHOT_ROWS:
{len(current_all)}

FRESH_CURRENT_ROWS:
{len(current_fresh)}

STALE_CURRENT_ROWS:
{len(current_stale)}

NEW_TRACKER_ROWS_ADDED:
{new_rows}

TRACKER_TOTAL_ROWS_AFTER_CLEAN:
{len(updated)}

SNAPSHOT_DATE_COUNT_AFTER_CLEAN:
{len(snapshot_dates)}

LATEST_TRACKER_SNAPSHOT_PRICE_DATE:
{latest_tracker_date}

LOW_COVERAGE_QUARANTINE_ROWS:
{len(low_coverage)}

OFFICIAL_DECISION_IMPACT:
NONE

READ:
{report_path}

TRACKER:
{tracker_path}

STALE_AUDIT:
{current_stale_audit_path}
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.6C-R1 TECHNICAL TIMING FRESHNESS GUARD READY ===")
    print(f"CURRENT_SNAPSHOT_ROWS: {len(current_all)}")
    print(f"FRESH_CURRENT_ROWS: {len(current_fresh)}")
    print(f"STALE_CURRENT_ROWS: {len(current_stale)}")
    print(f"NEW_TRACKER_ROWS_ADDED: {new_rows}")
    print(f"TRACKER_TOTAL_ROWS_AFTER_CLEAN: {len(updated)}")
    print(f"SNAPSHOT_DATE_COUNT_AFTER_CLEAN: {len(snapshot_dates)}")
    print(f"LATEST_TRACKER_SNAPSHOT_PRICE_DATE: {latest_tracker_date}")
    print(f"LOW_COVERAGE_QUARANTINE_ROWS: {len(low_coverage)}")
    for h in [1, 3, 5, 10, 20]:
        print(f"COMPLETED_{h}D_COUNT: {completed_counts.get(h, 0)}")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"TRACKER: {tracker_path}")
    print(f"STALE_AUDIT: {current_stale_audit_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")


if __name__ == "__main__":
    main()
