#!/usr/bin/env python
"""V18.40A candidate top/full canonical sync.

Preview/apply safety layer for aligning V18_CURRENT_TOP_RANKED_CANDIDATES.csv
to the canonical top 20 derived from V18_CURRENT_FULL_RANKED_CANDIDATES.csv.
Default mode is read-only preview. Apply mode backs up before replacing the
current top alias. No ranking formulas, factor weights, ledgers, or trading
state are modified.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

FULL = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
TOP = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_40A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_SUMMARY.csv"
OUT_PREVIEW = "outputs/v18/candidates/V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_PREVIEW.csv"
OUT_DIFF = "outputs/v18/candidates/V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_DIFF.csv"
OUT_REPORT = "outputs/v18/read_center/V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_CANDIDATE_TOP_FULL_CANONICAL_SYNC.md"

SUMMARY_FIELDS = [
    "status",
    "run_id",
    "apply_candidate_top_full_canonical_sync",
    "full_candidate_count",
    "current_top_candidate_count",
    "canonical_top20_count",
    "overlap_count",
    "mismatch_count",
    "only_current_top_count",
    "only_full_top20_count",
    "order_matches_full_top20",
    "backup_path",
    "warning_count",
    "fail_count",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "ranking_modified",
    "factor_weights_modified",
    "broker_api_used",
    "order_execution_used",
]

DIFF_FIELDS = ["bucket", "position", "ticker", "current_top_position", "full_top20_position", "notes"]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(r) for r in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def norm(value: object) -> str:
    return str(value or "").strip().upper()


def to_float(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def numeric_rank_valid(rows: list[dict[str, str]]) -> bool:
    if not rows or "rank" not in rows[0]:
        return False
    ranks = [to_float(row.get("rank")) for row in rows]
    return all(rank is not None for rank in ranks)


def canonical_top20(full_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in full_rows if norm(row.get("ticker") or row.get("yf_ticker"))]
    if numeric_rank_valid(rows):
        rows.sort(key=lambda row: (to_float(row.get("rank")) or 10**9, norm(row.get("ticker"))))
    else:
        rows.sort(key=lambda row: (to_float(row.get("composite_candidate_score")) is None, -(to_float(row.get("composite_candidate_score")) or -10**9), norm(row.get("ticker"))))
    return rows[:20]


def ticker_list(rows: list[dict[str, str]]) -> list[str]:
    return [norm(row.get("ticker") or row.get("yf_ticker")) for row in rows if norm(row.get("ticker") or row.get("yf_ticker"))]


def compare(top_rows: list[dict[str, str]], full_top20: list[dict[str, str]]) -> tuple[dict[str, object], list[dict[str, object]]]:
    current = ticker_list(top_rows[:20])
    canonical = ticker_list(full_top20)
    current_set = set(current)
    canonical_set = set(canonical)
    only_current = [t for t in current if t not in canonical_set]
    only_full = [t for t in canonical if t not in current_set]
    overlap = len(current_set & canonical_set)
    order_matches = current == canonical
    mismatch_count = max(len(only_current), len(only_full))
    if not order_matches and mismatch_count == 0:
        mismatch_count = sum(1 for a, b in zip(current, canonical) if a != b)

    current_pos = {ticker: idx + 1 for idx, ticker in enumerate(current)}
    full_pos = {ticker: idx + 1 for idx, ticker in enumerate(canonical)}
    diff_rows: list[dict[str, object]] = []
    for ticker in only_current:
        diff_rows.append({
            "bucket": "ONLY_IN_CURRENT_TOP",
            "position": current_pos.get(ticker, ""),
            "ticker": ticker,
            "current_top_position": current_pos.get(ticker, ""),
            "full_top20_position": "",
            "notes": "Present in current top alias but absent from canonical full top20.",
        })
    for ticker in only_full:
        diff_rows.append({
            "bucket": "ONLY_IN_FULL_TOP20",
            "position": full_pos.get(ticker, ""),
            "ticker": ticker,
            "current_top_position": "",
            "full_top20_position": full_pos.get(ticker, ""),
            "notes": "Present in canonical full top20 but absent from current top alias.",
        })
    if not diff_rows and not order_matches:
        for idx, (cur, can) in enumerate(zip(current, canonical), start=1):
            if cur != can:
                diff_rows.append({
                    "bucket": "ORDER_MISMATCH",
                    "position": idx,
                    "ticker": f"{cur}->{can}",
                    "current_top_position": current_pos.get(cur, ""),
                    "full_top20_position": full_pos.get(can, ""),
                    "notes": "Same top20 set but current top alias order differs from canonical full top20.",
                })
    metrics = {
        "overlap_count": overlap,
        "mismatch_count": mismatch_count,
        "only_current_top_count": len(only_current),
        "only_full_top20_count": len(only_full),
        "order_matches_full_top20": str(order_matches).upper(),
        "only_current_top": ",".join(only_current),
        "only_full_top20": ",".join(only_full),
    }
    return metrics, diff_rows


def render_read_first(summary: dict[str, object]) -> str:
    keys = [
        "STATUS",
        "RUN_ID",
        "APPLY_CANDIDATE_TOP_FULL_CANONICAL_SYNC",
        "FULL_CANDIDATE_COUNT",
        "CURRENT_TOP_CANDIDATE_COUNT",
        "CANONICAL_TOP20_COUNT",
        "OVERLAP_COUNT",
        "MISMATCH_COUNT",
        "ONLY_CURRENT_TOP_COUNT",
        "ONLY_FULL_TOP20_COUNT",
        "ORDER_MATCHES_FULL_TOP20",
        "BACKUP_PATH",
        "WARNING_COUNT",
        "FAIL_COUNT",
    ]
    lines = [f"{key}: {summary.get(key.lower(), '')}" for key in keys]
    lines += [
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "RANKING_MODIFIED: FALSE",
        "FACTOR_WEIGHTS_MODIFIED: FALSE",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def render_report(summary: dict[str, object], diff_rows: list[dict[str, object]]) -> str:
    lines = [
        "# V18.40A Candidate Top/Full Canonical Sync",
        "",
        "## Status",
        f"- STATUS: {summary.get('status')}",
        f"- RUN_ID: {summary.get('run_id')}",
        f"- APPLY_CANDIDATE_TOP_FULL_CANONICAL_SYNC: {summary.get('apply_candidate_top_full_canonical_sync')}",
        "",
        "## Comparison",
        f"- Full candidate count: {summary.get('full_candidate_count')}",
        f"- Current top candidate count: {summary.get('current_top_candidate_count')}",
        f"- Canonical top20 count: {summary.get('canonical_top20_count')}",
        f"- Overlap count: {summary.get('overlap_count')}",
        f"- Mismatch count: {summary.get('mismatch_count')}",
        f"- Only current top count: {summary.get('only_current_top_count')}",
        f"- Only full top20 count: {summary.get('only_full_top20_count')}",
        f"- Order matches full top20: {summary.get('order_matches_full_top20')}",
        f"- Backup path: {summary.get('backup_path')}",
        "",
        "## Diff",
        "| bucket | position | ticker | current_top_position | full_top20_position | notes |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    if diff_rows:
        for row in diff_rows:
            lines.append(f"| {row.get('bucket')} | {row.get('position')} | {row.get('ticker')} | {row.get('current_top_position')} | {row.get('full_top20_position')} | {row.get('notes')} |")
    else:
        lines.append("| NONE |  |  |  |  | Current top alias already matches canonical full top20. |")
    lines += [
        "",
        "## Safety",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- RANKING_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def run(root: Path, apply: bool) -> int:
    run_id = f"V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_{stamp()}"
    full_rows, full_fields = read_csv(root / FULL)
    top_rows, top_fields = read_csv(root / TOP)
    canonical = canonical_top20(full_rows)
    metrics, diff_rows = compare(top_rows, canonical)
    backup_path = ""
    fail_count = 0
    warning_count = 0

    if not full_rows:
        status = "FAIL_V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_FAILED"
        fail_count = 1
    elif not apply:
        if int(metrics["mismatch_count"]) == 0 and metrics["order_matches_full_top20"] == "TRUE":
            status = "OK_V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_ALREADY_MATCHED"
        else:
            status = "WARN_V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_PREVIEW_REVIEW_NEEDED"
            warning_count = 1
    else:
        backup_dir = root / "archive/v18/candidate_top_full_sync_backups" / run_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        if (root / TOP).exists():
            shutil.copy2(root / TOP, backup_dir / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv")
        backup_path = backup_dir.as_posix()
        fields = full_fields or list(canonical[0].keys() if canonical else [])
        write_csv(root / TOP, canonical, fields)
        reread_top, _ = read_csv(root / TOP)
        metrics, diff_rows = compare(reread_top, canonical)
        if int(metrics["mismatch_count"]) == 0 and metrics["order_matches_full_top20"] == "TRUE":
            status = "OK_V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_FIXED"
        else:
            status = "FAIL_V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_FAILED"
            fail_count = 1

    preview_fields = full_fields or list(canonical[0].keys() if canonical else [])
    write_csv(root / OUT_PREVIEW, canonical, preview_fields)
    write_csv(root / OUT_DIFF, diff_rows, DIFF_FIELDS)

    summary = {
        "status": status,
        "run_id": run_id,
        "apply_candidate_top_full_canonical_sync": str(bool(apply)).upper(),
        "full_candidate_count": len(full_rows),
        "current_top_candidate_count": len(top_rows),
        "canonical_top20_count": len(canonical),
        "overlap_count": metrics["overlap_count"],
        "mismatch_count": metrics["mismatch_count"],
        "only_current_top_count": metrics["only_current_top_count"],
        "only_full_top20_count": metrics["only_full_top20_count"],
        "order_matches_full_top20": metrics["order_matches_full_top20"],
        "backup_path": backup_path,
        "warning_count": warning_count,
        "fail_count": fail_count,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }
    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(summary))
    report = render_report(summary, diff_rows)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)
    return 1 if status.startswith("FAIL_") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--apply-candidate-top-full-canonical-sync", action="store_true")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), bool(args.apply_candidate_top_full_canonical_sync))


if __name__ == "__main__":
    raise SystemExit(main())
