#!/usr/bin/env python
"""V18.45A current ranked candidate freshness audit.

Reporting and annotation layer only. It does not change candidate scores,
ranking formulas, factor weights, trading behavior, or execution state.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"

RANKED = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_RECOMPUTED_RANKED_CANDIDATES.csv"
CURRENT_RANKED_ALIAS = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
TOPN = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
READ35D = "outputs/v18/ops/V18_35D_READ_FIRST.txt"
OUT_AUDIT = "outputs/v18/ops/V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_AUDIT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_AUDIT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt"
OUT_STALE_TOPN_EXCLUDED = "outputs/v18/candidates/V18_46A_STALE_TOPN_EXCLUDED_AUDIT.csv"

SUMMARY_FIELDS = [
    "status",
    "run_id",
    "generated_at",
    "refresh_mode",
    "ranked_candidate_count",
    "max_latest_price_date",
    "min_latest_price_date",
    "latest_price_date_distribution",
    "fresh_ranked_candidate_count",
    "stale_ranked_candidate_count",
    "stale_ranked_candidate_sample",
    "topn_count",
    "fresh_topn_count",
    "stale_topn_count",
    "stale_topn_tickers",
    "topn_current_ready",
    "full_universe_price_refresh_complete",
    "top20_price_refresh_complete",
    "full_universe_stale_row_count",
    "top20_stale_row_count",
    "full_price_refresh_complete",
    "full_price_refresh_incomplete_reason",
    "full_ranking_recompute_complete",
    "invalid_pseudo_ticker_count",
    "invalid_pseudo_tickers",
    "yfinance_failed_ticker_count",
    "yfinance_failed_tickers",
    "yfinance_failed_ticker_count_raw",
    "price_unavailable_excluded_count",
    "price_unavailable_excluded_tickers",
    "current_price_refresh_blocking_failed_ticker_count",
    "targeted_stale_retry_attempted_count",
    "targeted_stale_retry_success_count",
    "targeted_stale_retry_still_stale_count",
    "targeted_stale_retry_still_stale_tickers",
    "buy_candidate_report_trust",
    "buy_candidate_report_usable",
    "trading_execution_allowed",
    "auto_trade",
    "auto_sell",
    "broker_api_used",
    "order_execution_used",
    "ranking_logic_changed",
    "factor_weights_changed",
]

ANNOTATION_FIELDS = [
    "freshness_status",
    "stale_price_data_flag",
    "actionable_allowed_by_freshness",
    "original_full_rank",
    "freshness_eligible_rank",
]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip().upper()] = value.strip()
    return out


def to_int(value: object) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else 0
    except Exception:
        return 0


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


def distribution_text(dates: list[str]) -> str:
    counts = Counter(dates)
    return "; ".join(f"{date}={counts[date]}" for date in sorted(counts))


def ticker_set(rows: list[dict[str, str]]) -> set[str]:
    return {clean(row.get("ticker")).upper() for row in rows if clean(row.get("ticker"))}


def full_recompute_complete(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    for row in rows:
        evidence = " ".join(
            clean(row.get(key))
            for key in ("ranking_source_policy", "score_source_status", "primary_score_source_files", "score_source_files")
        ).upper()
        if "FULL_UNIVERSE_RECOMPUTE" not in evidence and "RECOMPUTED_FACTOR_TECHNICAL" not in evidence:
            return False
    return True


def annotate(rows: list[dict[str, str]], fields: list[str], max_date: str) -> tuple[list[dict[str, str]], list[str]]:
    out_fields = list(fields)
    for field in ANNOTATION_FIELDS:
        if field not in out_fields:
            out_fields.append(field)
    annotated: list[dict[str, str]] = []
    eligible_rank = 0
    for idx, row in enumerate(rows, 1):
        copy = dict(row)
        latest = clean(copy.get("latest_price_date"))
        stale = bool(max_date and latest and latest < max_date)
        copy["freshness_status"] = "STALE_PRICE_DATA" if stale else ("FRESH_LATEST_PRICE_DATE" if latest == max_date and max_date else "UNKNOWN_PRICE_DATE")
        copy["stale_price_data_flag"] = "TRUE" if stale else "FALSE"
        copy["actionable_allowed_by_freshness"] = "FALSE" if stale else ("TRUE" if latest == max_date and max_date else "FALSE")
        copy["original_full_rank"] = clean(copy.get("rank")) or str(idx)
        if copy["actionable_allowed_by_freshness"] == "TRUE":
            eligible_rank += 1
            copy["freshness_eligible_rank"] = str(eligible_rank)
        else:
            copy["freshness_eligible_rank"] = ""
        annotated.append(copy)
    return annotated, out_fields


def build(root: Path, refresh_mode: str) -> tuple[dict[str, object], list[dict[str, str]], list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    ranked_rows, ranked_fields = read_csv(root / RANKED)
    top_rows, top_fields = read_csv(root / TOPN)
    read35d = parse_kv(root / READ35D)
    dates = [clean(row.get("latest_price_date")) for row in ranked_rows if clean(row.get("latest_price_date"))]
    max_date = max(dates) if dates else ""
    min_date = min(dates) if dates else ""

    annotated_ranked, ranked_out_fields = annotate(ranked_rows, ranked_fields, max_date)
    annotated_top, top_out_fields = annotate(top_rows, top_fields, max_date)

    fresh_ranked = sum(1 for row in annotated_ranked if row.get("freshness_status") == "FRESH_LATEST_PRICE_DATE")
    stale_ranked = sum(1 for row in annotated_ranked if row.get("stale_price_data_flag") == "TRUE")
    stale_ranked_sample = ", ".join(clean(row.get("ticker")).upper() for row in annotated_ranked if row.get("stale_price_data_flag") == "TRUE" and clean(row.get("ticker")))[:240]
    fresh_top = sum(1 for row in annotated_top if row.get("freshness_status") == "FRESH_LATEST_PRICE_DATE")
    stale_top_rows = [row for row in annotated_top if row.get("stale_price_data_flag") == "TRUE"]
    stale_top_tickers = ", ".join(clean(row.get("ticker")).upper() for row in stale_top_rows if clean(row.get("ticker")))

    recompute_complete = full_recompute_complete(ranked_rows)
    full_universe_stale_count = stale_ranked
    full_universe_price_complete = bool(ranked_rows) and full_universe_stale_count == 0 and bool(max_date)
    price_complete = full_universe_price_complete
    invalid_pseudo_count = to_int(read35d.get("INVALID_PSEUDO_TICKER_COUNT"))
    yfinance_failed_count = to_int(read35d.get("YFINANCE_FAILED_TICKER_COUNT"))
    yfinance_failed_count_raw = to_int(read35d.get("YFINANCE_FAILED_TICKER_COUNT_RAW"))
    price_unavailable_excluded_count = to_int(read35d.get("PRICE_UNAVAILABLE_EXCLUDED_COUNT"))
    current_price_blocking_failed_count = to_int(read35d.get("CURRENT_PRICE_REFRESH_BLOCKING_FAILED_TICKER_COUNT"))
    incomplete_reasons: list[str] = []
    if not ranked_rows or not max_date:
        incomplete_reasons.append("NO_FULL_PRICE_UPDATE_EVIDENCE")
    if min_date and max_date and min_date != max_date:
        incomplete_reasons.append("MIXED_LATEST_PRICE_DATES")
    if invalid_pseudo_count:
        incomplete_reasons.append("INVALID_PSEUDO_TICKERS_REMOVED")
    if yfinance_failed_count:
        incomplete_reasons.append("YFINANCE_FAILED_TICKERS_PRESENT")
    if current_price_blocking_failed_count:
        incomplete_reasons.append("CURRENT_PRICE_REFRESH_BLOCKING_FAILED_TICKERS_PRESENT")
    incomplete_reason = "; ".join(dict.fromkeys(incomplete_reasons)) if not price_complete else "NONE"

    raw_top20 = annotated_ranked[:20]
    stale_excluded = [row for row in raw_top20 if row.get("actionable_allowed_by_freshness") != "TRUE"]
    freshness_top_rows = [dict(row) for row in annotated_ranked if row.get("actionable_allowed_by_freshness") == "TRUE"][:20]
    for idx, row in enumerate(freshness_top_rows, 1):
        row["rank"] = str(idx)
        row["freshness_eligible_rank"] = str(idx)
    annotated_top = freshness_top_rows
    top_out_fields = ranked_out_fields

    fresh_top = sum(1 for row in annotated_top if row.get("freshness_status") == "FRESH_LATEST_PRICE_DATE")
    stale_top_rows = [row for row in annotated_top if row.get("stale_price_data_flag") == "TRUE"]
    stale_top_tickers = ", ".join(clean(row.get("ticker")).upper() for row in stale_top_rows if clean(row.get("ticker")))
    top20_stale_count = len(stale_top_rows)
    top20_price_complete = bool(ranked_rows) and len(annotated_top) == 20 and top20_stale_count == 0 and current_price_blocking_failed_count == 0
    price_complete = full_universe_price_complete and top20_price_complete
    incomplete_reason = "NONE" if price_complete else incomplete_reason
    if stale_top_rows:
        trust = "MEDIUM" if fresh_top > 0 else "LOW"
    elif stale_ranked:
        trust = "MEDIUM"
    elif ranked_rows and annotated_top:
        trust = "HIGH"
    else:
        trust = "LOW"
    usable = "TRUE" if len(annotated_top) == 20 and not stale_top_rows else "FALSE"

    status = "OK_V18_45A_RANKED_CANDIDATE_FRESHNESS_READY"
    if not ranked_rows or not annotated_top:
        status = "FAIL_V18_45A_RANKED_CANDIDATE_FRESHNESS_INPUT_MISSING"
    elif stale_top_rows or (refresh_mode.upper() == "FULL" and not price_complete):
        status = "WARN_V18_45A_RANKED_CANDIDATE_FRESHNESS_REVIEW_NEEDED"

    summary = {
        "status": status,
        "run_id": f"V18_45A_RANKED_CANDIDATE_FRESHNESS_{now_ts()}",
        "generated_at": now_iso(),
        "refresh_mode": refresh_mode,
        "ranked_candidate_count": len(ranked_rows),
        "max_latest_price_date": max_date,
        "min_latest_price_date": min_date,
        "latest_price_date_distribution": distribution_text(dates),
        "fresh_ranked_candidate_count": fresh_ranked,
        "stale_ranked_candidate_count": stale_ranked,
        "stale_ranked_candidate_sample": stale_ranked_sample,
        "topn_count": len(annotated_top),
        "fresh_topn_count": fresh_top,
        "stale_topn_count": len(stale_top_rows),
        "stale_topn_tickers": stale_top_tickers,
        "topn_current_ready": "TRUE" if len(annotated_top) == 20 and not stale_top_rows else "FALSE",
        "full_universe_price_refresh_complete": "TRUE" if full_universe_price_complete else "FALSE",
        "top20_price_refresh_complete": "TRUE" if top20_price_complete else "FALSE",
        "full_universe_stale_row_count": full_universe_stale_count,
        "top20_stale_row_count": top20_stale_count,
        "full_price_refresh_complete": "TRUE" if price_complete else "FALSE",
        "full_price_refresh_incomplete_reason": incomplete_reason,
        "full_ranking_recompute_complete": "TRUE" if recompute_complete else "FALSE",
        "invalid_pseudo_ticker_count": invalid_pseudo_count,
        "invalid_pseudo_tickers": read35d.get("INVALID_PSEUDO_TICKERS", ""),
        "yfinance_failed_ticker_count": yfinance_failed_count,
        "yfinance_failed_tickers": read35d.get("YFINANCE_FAILED_TICKERS", ""),
        "yfinance_failed_ticker_count_raw": yfinance_failed_count_raw,
        "price_unavailable_excluded_count": price_unavailable_excluded_count,
        "price_unavailable_excluded_tickers": read35d.get("PRICE_UNAVAILABLE_EXCLUDED_TICKERS", ""),
        "current_price_refresh_blocking_failed_ticker_count": current_price_blocking_failed_count,
        "targeted_stale_retry_attempted_count": to_int(read35d.get("TARGETED_STALE_RETRY_ATTEMPTED_COUNT")),
        "targeted_stale_retry_success_count": to_int(read35d.get("TARGETED_STALE_RETRY_SUCCESS_COUNT")),
        "targeted_stale_retry_still_stale_count": to_int(read35d.get("TARGETED_STALE_RETRY_STILL_STALE_COUNT")),
        "targeted_stale_retry_still_stale_tickers": read35d.get("TARGETED_STALE_RETRY_STILL_STALE_TICKERS", ""),
        "buy_candidate_report_trust": trust,
        "buy_candidate_report_usable": usable,
        "trading_execution_allowed": "FALSE",
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
        "ranking_logic_changed": "FALSE",
        "factor_weights_changed": "FALSE",
    }
    return summary, annotated_ranked, ranked_out_fields, annotated_top, top_out_fields, stale_excluded


def render_read_first(summary: dict[str, object]) -> str:
    lines = [f"{field.upper()}: {summary.get(field, '')}" for field in SUMMARY_FIELDS]
    lines.append("STALE_TOPN_ACTION_RULE: If TopN contains stale price rows, do not use those stale rows for buy timing.")
    return "\n".join(lines) + "\n"


def render_report(summary: dict[str, object]) -> str:
    lines = [
        "# V18.45A Ranked Candidate Freshness Audit",
        "",
        "## Summary",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field.upper()}: {summary.get(field, '')}")
    lines += [
        "",
        "## Operator Rule",
        "- If TopN contains stale price rows, do not use those stale rows for buy timing.",
        "- Stale rows remain in candidate CSVs for auditability, with freshness_status, stale_price_data_flag, and actionable_allowed_by_freshness fields.",
        "",
        "## Safety",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- TRADING_EXECUTION_ALLOWED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
        "- RANKING_LOGIC_CHANGED: FALSE",
        "- FACTOR_WEIGHTS_CHANGED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def run(root: Path, refresh_mode: str) -> int:
    summary, ranked_rows, ranked_fields, top_rows, top_fields, stale_excluded = build(root, refresh_mode)
    if summary.get("full_ranking_recompute_complete") == "TRUE" and summary.get("topn_current_ready") == "TRUE":
        write_csv(root / CURRENT_RANKED_ALIAS, ranked_rows, ranked_fields)
    write_csv(root / OUT_STALE_TOPN_EXCLUDED, stale_excluded, ranked_fields)
    write_csv(root / OUT_AUDIT, [summary], SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(summary))
    write_text(root / OUT_REPORT, render_report(summary))
    return 1 if str(summary["status"]).startswith("FAIL_") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--refresh-mode", choices=["Rolling", "Full"], default="Rolling")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), args.refresh_mode)


if __name__ == "__main__":
    raise SystemExit(main())
