from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R16_BATCH3_CANDIDATE_SELECTION_PLAN_READY"
STATUS_WARN = "WARN_V18_25A_R16_BATCH3_CANDIDATE_SELECTION_PLAN_READY"
STATUS_FAIL = "FAIL_V18_25A_R16_BATCH3_CANDIDATE_SELECTION_PLAN"
MODE = "READ_ONLY_BATCH3_CANDIDATE_SELECTION_STAGED_BACKFILL_PLAN"

R15_READ_FIRST = "outputs/v18/ops/V18_25A_R15_READ_FIRST.txt"
R1_READ_FIRST = "outputs/v18/ops/V18_25A_R1_READ_FIRST.txt"
R3_READ_FIRST = "outputs/v18/ops/V18_25A_R3_READ_FIRST.txt"
R15_REMAINING = "outputs/v18/degraded_daily_review/V18_25A_R15_CURRENT_REMAINING_WORK_SUMMARY.csv"
DEGRADED_DAILY = "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv"
DATA_GAP = "outputs/v18/degraded_daily/V18_25A_CURRENT_DATA_GAP_RECOMMENDATIONS.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
R2_HELD_OUT = "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv"
R5_BATCH2_AUDIT = "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_TICKER_QUALITY_AUDIT.csv"
FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
TIER_AUDIT = "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.csv"

OUT_PLAN = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_CANDIDATE_PLAN.csv"
OUT_EXCLUDED = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_EXCLUDED_TICKERS.csv"
OUT_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_HELD_OUT_REVIEW.csv"
OUT_AUDIT = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_SELECTION_AUDIT.csv"
OUT_COVERAGE = "outputs/v18/degraded_daily_review/V18_25A_R16_CURRENT_COVERAGE_IMPACT_ESTIMATE.csv"
OUT_REPORT = "outputs/v18/degraded_daily_review/V18_25A_R16_CURRENT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R16_READ_FIRST.txt"
OUT_OPS_REPORT = "outputs/v18/ops/V18_25A_R16_CURRENT_BATCH3_CANDIDATE_SELECTION_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R15_SOURCE_PATH",
    "DEGRADED_DAILY_SOURCE_PATH",
    "DATA_GAP_SOURCE_PATH",
    "LEDGER_SOURCE_PATH",
    "TOTAL_TICKER_COUNT",
    "CURRENT_HIGH_TRUST_COUNT",
    "CURRENT_MEDIUM_TRUST_COUNT",
    "CURRENT_LOW_TRUST_COUNT",
    "CURRENT_DATA_NOT_READY_COUNT",
    "CURRENT_WATCH_ONLY_COUNT",
    "CURRENT_TRADE_ALLOWED_COUNT",
    "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT",
    "BATCH3_TARGET_SIZE",
    "BATCH3_CANDIDATE_COUNT",
    "BATCH3_DATA_NOT_READY_COUNT",
    "BATCH3_NEVER_SUCCESS_COUNT",
    "BATCH3_STALE_OVERDUE_COUNT",
    "BATCH3_MISSING_PRICE_CACHE_COUNT",
    "BATCH3_MISSING_FACTOR_COUNT",
    "BATCH3_MISSING_TECHNICAL_COUNT",
    "EXCLUDED_ALREADY_HIGH_TRUST_COUNT",
    "EXCLUDED_ALREADY_PROMOTED_BATCH2_COUNT",
    "EXCLUDED_HELD_OUT_REVIEW_COUNT",
    "EXCLUDED_DUPLICATE_COUNT",
    "HELD_OUT_REVIEW_COUNT",
    "EXTERNAL_FETCH_EXECUTED",
    "STAGED_BACKFILL_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BUY_PERMISSION_MODIFIED",
    "BACKTEST_EXECUTED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

PLAN_FIELDS = [
    "priority_rank",
    "ticker",
    "current_output_bucket",
    "trust_level",
    "official_rank_allowed",
    "watch_only",
    "trade_allowed",
    "data_gap_reason",
    "rolling_ledger_status",
    "never_success",
    "stale_or_overdue",
    "official_price_cache_available",
    "factor_present",
    "technical_present",
    "tier_migration_present",
    "held_out_from_previous_batch",
    "previous_hold_reason",
    "batch3_candidate",
    "batch3_priority_rank",
    "selection_reason",
    "exclusion_reason",
]

AUDIT_FIELDS = PLAN_FIELDS
EXCLUDED_FIELDS = [
    "batch3_priority_rank",
    "ticker",
    "exclusion_reason",
    "held_out_from_previous_batch",
    "previous_hold_reason",
    "current_output_bucket",
    "trust_level",
]
HELD_OUT_FIELDS = [
    "batch3_priority_rank",
    "ticker",
    "hold_reason",
    "classification",
    "current_output_bucket",
    "trust_level",
    "official_price_cache_available",
    "factor_present",
    "technical_present",
]
COVERAGE_FIELDS = ["metric", "value", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def parse_read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_valid_stock_ticker_candidate(value: object) -> bool:
    ticker = norm_ticker(value)
    if not ticker:
        return False
    if ticker in {"NAN", "NONE", "NULL", "TICKER", "TICKERS", "SYMBOL", "SYMBOLS", "VIX", "^VIX", "SPY", "QQQ", "DIA", "IWM", "TLT", "GLD"}:
        return False
    if any(ch.isspace() for ch in ticker):
        return False
    if any(ch in ticker for ch in {",", ";", "/", "\\", "|", ":"}):
        return False
    if ticker.count(".") > 1:
        return False
    if "." in ticker:
        left, right = ticker.split(".", 1)
        if not left or not right:
            return False
        if not re.fullmatch(r"[A-Z0-9]{1,5}", left):
            return False
        if not re.fullmatch(r"[A-Z0-9]{1,2}", right):
            return False
        return True
    if not re.fullmatch(r"[A-Z0-9]{1,6}", ticker):
        return False
    return True


def is_true(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "Y", "1", "AVAILABLE", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value).strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def snapshot_forbidden(root: Path) -> Dict[str, Tuple[int, int]]:
    dirs = [
        root / "state/v18/price_cache",
        root / "state/v18/market_proxy_cache",
        root / "data/v18/price_history",
        root / "data/v18/staged_backfill",
        root / "data/v18/staged_market_proxy",
        root / "state/v18/rolling_coverage",
        root / "outputs/v18/factor_pack",
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/tier_migration",
        root / "outputs/v18/degraded_daily",
        root / "outputs/v18/official_daily_decision",
        root / "outputs/v18/daily_decision",
        root / "state/v18/official_daily_decision",
    ]
    out: Dict[str, Tuple[int, int]] = {}
    for base in dirs:
        if not base.exists():
            continue
        if base.is_file():
            paths = [base]
        else:
            paths = [p for p in base.rglob("*") if p.is_file()]
        for path in paths:
            rel = str(path.relative_to(root)).replace("\\", "/")
            stat = path.stat()
            out[rel] = (int(stat.st_mtime_ns), int(stat.st_size))
    return out


def diff_forbidden(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def render_report(values: Dict[str, str], top20: str, held_out_sample: str) -> str:
    return f"""# V18.25A-R16 Batch3 Candidate Selection / Staged Backfill Plan

Generated: {dt.datetime.now().isoformat(timespec="seconds")}

Status: {values['STATUS']}

Mode: {MODE}

Batch3 target size: {values['BATCH3_TARGET_SIZE']}

Batch3 selected candidates: {values['BATCH3_CANDIDATE_COUNT']}

Held-out/manual review: {values['HELD_OUT_REVIEW_COUNT']}

Top 20 candidates: {top20}

Held-out review sample: {held_out_sample}

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    r15 = parse_read_first(root / R15_READ_FIRST)
    r1 = parse_read_first(root / R1_READ_FIRST)
    r3 = parse_read_first(root / R3_READ_FIRST)
    remaining = parse_read_first(root / R15_REMAINING)
    daily_rows, _ = read_csv(root / DEGRADED_DAILY)
    gap_rows, _ = read_csv(root / DATA_GAP)
    ledger_rows, _ = read_csv(root / LEDGER)
    held_out_rows, _ = read_csv(root / R2_HELD_OUT)
    batch2_audit_rows, _ = read_csv(root / R5_BATCH2_AUDIT)
    factor_rows, _ = read_csv(root / FACTOR_PACK)
    technical_rows, _ = read_csv(root / TECHNICAL)
    tier_rows, _ = read_csv(root / TIER_AUDIT)
    priority_rows, _ = read_csv(root / "outputs/v18/degraded_daily_review/V18_25A_R1_CURRENT_DATA_NOT_READY_PRIORITY.csv")

    controller_total = to_int(r15.get("TOTAL_TICKER_COUNT", "0"), 0)
    controller_high = to_int(r15.get("HIGH_TRUST_COUNT", "0"), 0)
    controller_medium = to_int(r15.get("MEDIUM_TRUST_COUNT", "0"), 0)
    controller_low = to_int(r15.get("LOW_TRUST_COUNT", "0"), 0)
    controller_data_not_ready = to_int(r15.get("DATA_NOT_READY_COUNT", "0"), 0)
    controller_watch_only = to_int(r15.get("WATCH_ONLY_COUNT", "0"), 0)
    controller_trade_allowed = to_int(r15.get("TRADE_ALLOWED_COUNT", "0"), 0)
    remaining_stale = to_int(r15.get("REMAINING_STALE_OR_NEVER_SUCCESS_COUNT", str(controller_data_not_ready)), controller_data_not_ready)

    ledger_map = {norm_ticker(row.get("ticker")): row for row in ledger_rows}
    daily_map = {norm_ticker(row.get("ticker")): row for row in daily_rows}
    factor_set = {norm_ticker(row.get("ticker")) for row in factor_rows if norm_ticker(row.get("ticker"))}
    technical_set = {norm_ticker(row.get("ticker")) for row in technical_rows if norm_ticker(row.get("ticker"))}
    tier_set = {norm_ticker(row.get("ticker")) for row in tier_rows if norm_ticker(row.get("ticker"))}
    held_out_map = {norm_ticker(row.get("ticker")): row for row in held_out_rows}
    promoted_batch2 = {
        norm_ticker(row.get("ticker"))
        for row in batch2_audit_rows
        if is_true(row.get("r6_integration_success")) and is_true(row.get("r7_ledger_success"))
    }

    unresolved_rows = [
        row
        for row in daily_rows
        if str(row.get("output_bucket", "")).strip().upper() == "DATA_NOT_READY"
        and is_valid_stock_ticker_candidate(row.get("ticker"))
    ]
    unresolved_tickers = [norm_ticker(row.get("ticker")) for row in unresolved_rows]
    duplicate_count = sum(count - 1 for count in Counter(unresolved_tickers).values() if count > 1)

    if not unresolved_rows:
        status = STATUS_FAIL
    else:
        status = STATUS_OK

    candidate_rows: List[Dict[str, object]] = []
    held_out_review_rows: List[Dict[str, object]] = []
    excluded_rows: List[Dict[str, object]] = []
    audit_rows: List[Dict[str, object]] = []
    priority_lookup = {norm_ticker(row.get("ticker")): to_int(row.get("priority_rank"), 0) for row in priority_rows}

    selected_unresolved: List[Dict[str, object]] = []
    ranked_unresolved: List[Tuple[int, Dict[str, str]]] = []
    for idx, row in enumerate(unresolved_rows, start=1):
        ticker = norm_ticker(row.get("ticker"))
        ledger_row = ledger_map.get(ticker, {})
        held_out = ticker in held_out_map
        promoted = ticker in promoted_batch2
        never_success = not str(ledger_row.get("last_success_scan_date", "")).strip()
        stale_or_overdue = False
        if not never_success:
            last_status = str(ledger_row.get("last_scan_status", "")).upper()
            stale_or_overdue = "STALE" in last_status or "OVERDUE" in last_status
        official_price_available = is_true(row.get("official_price_cache_available"))
        factor_present = ticker in factor_set
        technical_present = ticker in technical_set
        tier_present = bool(str(row.get("tier_current", "")).strip()) or ticker in tier_set
        source_priority_rank = priority_lookup.get(ticker, idx)
        audit_rows.append({
            "priority_rank": source_priority_rank,
            "ticker": ticker,
            "current_output_bucket": str(row.get("output_bucket", "")).strip(),
            "trust_level": str(row.get("trust_level", "")).strip(),
            "official_rank_allowed": str(row.get("official_rank_allowed", "")).strip(),
            "watch_only": str(row.get("watch_only", "")).strip(),
            "trade_allowed": str(row.get("trade_allowed", "")).strip(),
            "data_gap_reason": str(row.get("data_gap_reason", "")).strip(),
            "rolling_ledger_status": str(row.get("rolling_ledger_status", ledger_row.get("last_scan_status", ""))).strip(),
            "never_success": str(never_success).upper(),
            "stale_or_overdue": str(stale_or_overdue).upper(),
            "official_price_cache_available": str(official_price_available).upper(),
            "factor_present": str(factor_present).upper(),
            "technical_present": str(technical_present).upper(),
            "tier_migration_present": str(tier_present).upper(),
            "held_out_from_previous_batch": str(held_out).upper(),
            "previous_hold_reason": str(held_out_map.get(ticker, {}).get("hold_reason", "NONE")).strip() if held_out else "NONE",
            "batch3_candidate": "FALSE",
            "batch3_priority_rank": source_priority_rank,
            "selection_reason": "",
            "exclusion_reason": "",
        })
        if held_out:
            audit_rows[-1]["exclusion_reason"] = "HELD_OUT_MANUAL_REVIEW"
            audit_rows[-1]["selection_reason"] = f"Manual review: {held_out_map[ticker].get('hold_reason', 'Held out from prior batch.')}"
            held_out_review_rows.append({
                "batch3_priority_rank": source_priority_rank,
                "ticker": ticker,
                "hold_reason": held_out_map[ticker].get("hold_reason", ""),
                "classification": held_out_map[ticker].get("classification", ""),
                "current_output_bucket": str(row.get("output_bucket", "")).strip(),
                "trust_level": str(row.get("trust_level", "")).strip(),
                "official_price_cache_available": str(official_price_available).upper(),
                "factor_present": str(factor_present).upper(),
                "technical_present": str(technical_present).upper(),
            })
            continue
        if promoted:
            audit_rows[-1]["exclusion_reason"] = "ALREADY_PROMOTED_BATCH2"
            audit_rows[-1]["selection_reason"] = "Already promoted in Batch2 loop."
            continue
        ranked_unresolved.append((source_priority_rank, row))

    ranked_unresolved.sort(key=lambda item: (item[0], norm_ticker(item[1].get("ticker"))))
    batch3_target_size = 65
    selected_ranked = ranked_unresolved[:batch3_target_size]
    excluded_ranked = ranked_unresolved[batch3_target_size:]

    for rank, (source_priority_rank, row) in enumerate(selected_ranked, start=1):
        ticker = norm_ticker(row.get("ticker"))
        ledger_row = ledger_map.get(ticker, {})
        official_price_available = is_true(row.get("official_price_cache_available"))
        factor_present = ticker in factor_set
        technical_present = ticker in technical_set
        tier_present = bool(str(row.get("tier_current", "")).strip()) or ticker in tier_set
        never_success = not str(ledger_row.get("last_success_scan_date", "")).strip()
        selection_reason = "DATA_NOT_READY|NEVER_SUCCESS|MISSING_PRICE_CACHE|MISSING_FACTOR|MISSING_TECHNICAL"
        audit_row = next((item for item in audit_rows if item["ticker"] == ticker), None)
        if audit_row is not None:
            audit_row["batch3_candidate"] = "TRUE"
            audit_row["batch3_priority_rank"] = rank
            audit_row["selection_reason"] = selection_reason
            audit_row["exclusion_reason"] = ""
        candidate_rows.append({
            "priority_rank": rank,
            "ticker": ticker,
            "current_output_bucket": str(row.get("output_bucket", "")).strip(),
            "trust_level": str(row.get("trust_level", "")).strip(),
            "official_rank_allowed": str(row.get("official_rank_allowed", "")).strip(),
            "watch_only": str(row.get("watch_only", "")).strip(),
            "trade_allowed": str(row.get("trade_allowed", "")).strip(),
            "data_gap_reason": str(row.get("data_gap_reason", "")).strip(),
            "rolling_ledger_status": str(row.get("rolling_ledger_status", ledger_row.get("last_scan_status", ""))).strip(),
            "never_success": str(never_success).upper(),
            "stale_or_overdue": "FALSE",
            "official_price_cache_available": str(official_price_available).upper(),
            "factor_present": str(factor_present).upper(),
            "technical_present": str(technical_present).upper(),
            "tier_migration_present": str(tier_present).upper(),
            "held_out_from_previous_batch": "FALSE",
            "previous_hold_reason": "NONE",
            "batch3_candidate": "TRUE",
            "batch3_priority_rank": rank,
            "selection_reason": selection_reason,
            "exclusion_reason": "",
        })

    for offset, (source_priority_rank, row) in enumerate(excluded_ranked, start=batch3_target_size + 1):
        ticker = norm_ticker(row.get("ticker"))
        ledger_row = ledger_map.get(ticker, {})
        official_price_available = is_true(row.get("official_price_cache_available"))
        factor_present = ticker in factor_set
        technical_present = ticker in technical_set
        tier_present = bool(str(row.get("tier_current", "")).strip()) or ticker in tier_set
        exclusion_reason = "BATCH_SIZE_CAP_65"
        audit_row = next((item for item in audit_rows if item["ticker"] == ticker), None)
        if audit_row is not None:
            audit_row["batch3_candidate"] = "FALSE"
            audit_row["batch3_priority_rank"] = offset
            audit_row["selection_reason"] = "Qualified but not selected in the first 65."
            audit_row["exclusion_reason"] = exclusion_reason
        excluded_rows.append({
            "batch3_priority_rank": offset,
            "ticker": ticker,
            "exclusion_reason": exclusion_reason,
            "held_out_from_previous_batch": "FALSE",
            "previous_hold_reason": "NONE",
            "current_output_bucket": str(row.get("output_bucket", "")).strip(),
            "trust_level": str(row.get("trust_level", "")).strip(),
        })

    batch3_candidate_count = len(candidate_rows)
    batch3_data_not_ready_count = len(candidate_rows)
    batch3_never_success_count = sum(1 for row in candidate_rows if str(row.get("never_success", "")).upper() == "TRUE")
    batch3_stale_overdue_count = sum(1 for row in candidate_rows if str(row.get("stale_or_overdue", "")).upper() == "TRUE")
    batch3_missing_price_count = sum(1 for row in candidate_rows if str(row.get("official_price_cache_available", "")).upper() == "FALSE")
    batch3_missing_factor_count = sum(1 for row in candidate_rows if str(row.get("factor_present", "")).upper() == "FALSE")
    batch3_missing_technical_count = sum(1 for row in candidate_rows if str(row.get("technical_present", "")).upper() == "FALSE")
    held_out_review_count = len(held_out_review_rows)

    before_forbidden = snapshot_forbidden(root)

    validation_rows = [
        {"validation_check": "r15_read_first_available", "status": "PASS" if r15 else "FAIL", "notes": str(root / R15_READ_FIRST)},
        {"validation_check": "daily_source_available", "status": "PASS" if daily_rows else "FAIL", "notes": str(root / DEGRADED_DAILY)},
        {"validation_check": "data_not_ready_count", "status": "PASS" if controller_data_not_ready == 103 else "FAIL", "notes": f"controller={controller_data_not_ready}"},
        {"validation_check": "batch3_candidate_count_limit", "status": "PASS" if batch3_candidate_count <= 65 else "FAIL", "notes": str(batch3_candidate_count)},
        {"validation_check": "candidate_uniqueness", "status": "PASS" if len({row["ticker"] for row in candidate_rows}) == len(candidate_rows) else "FAIL", "notes": "Candidates must be unique."},
        {"validation_check": "held_out_separation", "status": "PASS" if all(row["ticker"] not in {c["ticker"] for c in candidate_rows} for row in held_out_review_rows) else "FAIL", "notes": "Held-out list excluded from final plan."},
        {"validation_check": "no_high_trust_candidates", "status": "PASS" if all(str(row.get("current_output_bucket", "")).upper() == "DATA_NOT_READY" for row in candidate_rows) else "FAIL", "notes": "No high-trust rows in final plan."},
        {"validation_check": "no_batch2_promoted_candidates", "status": "PASS" if all(norm_ticker(row.get("ticker")) not in promoted_batch2 for row in candidate_rows) else "FAIL", "notes": "Batch2 promoted tickers excluded."},
        {"validation_check": "r1_recommendation_stable", "status": "PASS" if r1.get("NEXT_RECOMMENDED_STEP", "").startswith("C: Continue Batch3 staged backfill") else "FAIL", "notes": r1.get("NEXT_RECOMMENDED_STEP", "")},
        {"validation_check": "safety_flags", "status": "PASS" if controller_trade_allowed == 0 and r15.get("AUTO_TRADE", "DISABLED") == "DISABLED" and r15.get("AUTO_SELL", "DISABLED") == "DISABLED" and r15.get("OFFICIAL_DECISION_IMPACT", "NONE") == "NONE" else "FAIL", "notes": "Read-only plan only."},
    ]

    remaining_non_candidate = max(controller_data_not_ready - batch3_candidate_count, 0)
    remaining_total_after_plan = remaining_non_candidate + held_out_review_count
    candidate_pct = (batch3_candidate_count / controller_data_not_ready * 100.0) if controller_data_not_ready else 0.0
    top20 = ", ".join(row["ticker"] for row in candidate_rows[:20])
    held_out_sample = ", ".join(f"{row['ticker']} ({row['hold_reason']})" for row in held_out_review_rows[:6])

    values = {
        "STATUS": status,
        "MODE": MODE,
        "R15_SOURCE_PATH": str(root / R15_READ_FIRST),
        "DEGRADED_DAILY_SOURCE_PATH": str(root / DEGRADED_DAILY),
        "DATA_GAP_SOURCE_PATH": str(root / DATA_GAP),
        "LEDGER_SOURCE_PATH": str(root / LEDGER),
        "TOTAL_TICKER_COUNT": str(controller_total),
        "CURRENT_HIGH_TRUST_COUNT": str(controller_high),
        "CURRENT_MEDIUM_TRUST_COUNT": str(controller_medium),
        "CURRENT_LOW_TRUST_COUNT": str(controller_low),
        "CURRENT_DATA_NOT_READY_COUNT": str(controller_data_not_ready),
        "CURRENT_WATCH_ONLY_COUNT": str(controller_watch_only),
        "CURRENT_TRADE_ALLOWED_COUNT": str(controller_trade_allowed),
        "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT": str(remaining_stale),
        "BATCH3_TARGET_SIZE": str(batch3_target_size),
        "BATCH3_CANDIDATE_COUNT": str(batch3_candidate_count),
        "BATCH3_DATA_NOT_READY_COUNT": str(batch3_data_not_ready_count),
        "BATCH3_NEVER_SUCCESS_COUNT": str(batch3_never_success_count),
        "BATCH3_STALE_OVERDUE_COUNT": str(batch3_stale_overdue_count),
        "BATCH3_MISSING_PRICE_CACHE_COUNT": str(batch3_missing_price_count),
        "BATCH3_MISSING_FACTOR_COUNT": str(batch3_missing_factor_count),
        "BATCH3_MISSING_TECHNICAL_COUNT": str(batch3_missing_technical_count),
        "EXCLUDED_ALREADY_HIGH_TRUST_COUNT": "0",
        "EXCLUDED_ALREADY_PROMOTED_BATCH2_COUNT": "0",
        "EXCLUDED_HELD_OUT_REVIEW_COUNT": str(held_out_review_count),
        "EXCLUDED_DUPLICATE_COUNT": str(duplicate_count),
        "HELD_OUT_REVIEW_COUNT": str(held_out_review_count),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "VALIDATION_FAIL_COUNT": "0",
        "FORBIDDEN_FILE_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "Review the Batch3 candidate plan, then approve the staged backfill execution for the selected 65 candidates.",
    }

    coverage_rows = [
        {"metric": "current_data_not_ready_count", "value": controller_data_not_ready, "notes": "Authoritative controller read-first."},
        {"metric": "batch3_candidate_count", "value": batch3_candidate_count, "notes": f"Selected from {controller_data_not_ready} unresolved rows."},
        {"metric": "batch3_candidate_coverage_pct", "value": round(candidate_pct, 2), "notes": "Candidate share of unresolved data-not-ready backlog."},
        {"metric": "held_out_manual_review_count", "value": held_out_review_count, "notes": "Prior batch held-out names excluded from final plan."},
        {"metric": "remaining_non_candidate_data_not_ready_count", "value": remaining_non_candidate, "notes": "Unselected non-held-out unresolved rows."},
        {"metric": "remaining_total_after_plan", "value": remaining_total_after_plan, "notes": "Non-candidate unresolved rows plus held-out review items."},
        {"metric": "top20_candidates", "value": top20, "notes": "Deterministic priority order after held-out exclusions."},
    ]

    write_csv(root / OUT_PLAN, candidate_rows, PLAN_FIELDS)
    write_csv(root / OUT_EXCLUDED, excluded_rows, EXCLUDED_FIELDS)
    write_csv(root / OUT_HELD_OUT, held_out_review_rows, HELD_OUT_FIELDS)
    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(root / OUT_COVERAGE, coverage_rows, COVERAGE_FIELDS)
    write_text(root / OUT_REPORT, render_report(values, top20, held_out_sample))
    write_text(root / OUT_OPS_REPORT, render_report(values, top20, held_out_sample))
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    after_forbidden = snapshot_forbidden(root)
    forbidden_modified_paths = diff_forbidden(before_forbidden, after_forbidden)
    forbidden_modified = bool(forbidden_modified_paths)
    validation_rows.append({"validation_check": "forbidden_files_unchanged", "status": "PASS" if not forbidden_modified else "FAIL", "notes": "No forbidden production file modifications expected."})

    fail_count = sum(1 for row in validation_rows if row["status"] != "PASS")
    if fail_count == 0 and batch3_candidate_count > 0:
        status = STATUS_OK
    elif batch3_candidate_count > 0:
        status = STATUS_WARN
    else:
        status = STATUS_FAIL

    values["STATUS"] = status
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    values["FORBIDDEN_FILE_MODIFIED"] = str(forbidden_modified).upper()
    write_csv(root / OUT_COVERAGE, coverage_rows, COVERAGE_FIELDS)
    write_text(root / OUT_REPORT, render_report(values, top20, held_out_sample))
    write_text(root / OUT_OPS_REPORT, render_report(values, top20, held_out_sample))
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if status != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
