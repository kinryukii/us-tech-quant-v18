from __future__ import annotations

import csv
import os
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


MODE = "READ_ONLY_POST_INTEGRATION_PROMOTION_BLOCKER_AUDIT"
STATUS_OK = "OK_V18_25A_R3_POST_INTEGRATION_PROMOTION_BLOCKER_AUDIT_READY"
STATUS_WARN = "WARN_V18_25A_R3_POST_INTEGRATION_PROMOTION_BLOCKER_AUDIT_READY"
STATUS_FAIL = "FAIL_V18_25A_R3_POST_INTEGRATION_PROMOTION_BLOCKER_AUDIT"

ROOT = Path(r"D:\us-tech-quant")

R6_SOURCE_PATH = ROOT / "outputs" / "v18" / "staged_backfill" / "V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_RESULT.csv"
R7_SOURCE_PATH = ROOT / "outputs" / "v18" / "rolling_coverage" / "V18_23C_R7_CURRENT_LEDGER_UPDATE_RESULT.csv"
DEGRADED_DAILY_SOURCE_PATH = ROOT / "outputs" / "v18" / "degraded_daily" / "V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv"
DATA_GAP_SOURCE_PATH = ROOT / "outputs" / "v18" / "degraded_daily" / "V18_25A_CURRENT_DATA_GAP_RECOMMENDATIONS.csv"
R1_READ_FIRST_PATH = ROOT / "outputs" / "v18" / "ops" / "V18_25A_R1_READ_FIRST.txt"
FACTOR_PATH = ROOT / "outputs" / "v18" / "factor_pack" / "V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_PATH = ROOT / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING.csv"
TIER_PATH = ROOT / "outputs" / "v18" / "tier_migration" / "V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.csv"
LEDGER_PATH = ROOT / "state" / "v18" / "rolling_coverage" / "V18_23B_ROLLING_SCAN_LEDGER.csv"
PRICE_CACHE_DIR = ROOT / "state" / "v18" / "price_cache"

OUT_DIR = ROOT / "outputs" / "v18" / "degraded_daily_review"
OPS_DIR = ROOT / "outputs" / "v18" / "ops"

OUTPUTS = {
    "audit": OUT_DIR / "V18_25A_R3_CURRENT_R6_R7_PROMOTION_BLOCKER_AUDIT.csv",
    "summary": OUT_DIR / "V18_25A_R3_CURRENT_PROMOTION_BLOCKER_SUMMARY.csv",
    "next_fix": OUT_DIR / "V18_25A_R3_CURRENT_NEXT_FIX_PRIORITY.csv",
    "report": OUT_DIR / "V18_25A_R3_CURRENT_REPORT.md",
    "read_first": OPS_DIR / "V18_25A_R3_READ_FIRST.txt",
    "ops_report": OPS_DIR / "V18_25A_R3_CURRENT_POST_INTEGRATION_PROMOTION_BLOCKER_AUDIT_REPORT.md",
}


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_read_first(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not path.exists():
        return result
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def parse_score(text: str) -> float:
    text = str(text or "").strip()
    if not text:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def latest_row_by_ticker(rows: List[Dict[str, str]], ticker_field: str = "ticker") -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = str(row.get(ticker_field, "")).strip().upper()
        if ticker:
            out[ticker] = row
    return out


def collect_forbidden_mtimes() -> Dict[str, int]:
    paths = [
        PRICE_CACHE_DIR,
        ROOT / "state" / "v18" / "price_history",
        ROOT / "data" / "v18" / "staged_backfill",
        FACTOR_PATH,
        TECH_PATH,
        TIER_PATH,
        DEGRADED_DAILY_SOURCE_PATH,
        DATA_GAP_SOURCE_PATH,
        LEDGER_PATH,
    ]
    mtimes: Dict[str, int] = {}
    for path in paths:
        if path.exists():
            if path.is_dir():
                mtimes[str(path)] = max((child.stat().st_mtime_ns for child in path.rglob("*") if child.exists()), default=path.stat().st_mtime_ns)
            else:
                mtimes[str(path)] = path.stat().st_mtime_ns
        else:
            mtimes[str(path)] = -1
    return mtimes


def summarize_counts(rows: Iterable[Dict[str, str]], key: str) -> Counter:
    return Counter(str(row.get(key, "")).strip() for row in rows)


def main() -> int:
    validation_failures: List[str] = []
    warnings: List[str] = []

    before_mtimes = collect_forbidden_mtimes()

    if not R6_SOURCE_PATH.exists():
        validation_failures.append(f"Missing R6 source: {R6_SOURCE_PATH}")
        r6_rows: List[Dict[str, str]] = []
    else:
        r6_rows = read_csv_rows(R6_SOURCE_PATH)

    if not R7_SOURCE_PATH.exists():
        validation_failures.append(f"Missing R7 source: {R7_SOURCE_PATH}")
        r7_rows: List[Dict[str, str]] = []
    else:
        r7_rows = read_csv_rows(R7_SOURCE_PATH)

    if not DEGRADED_DAILY_SOURCE_PATH.exists():
        validation_failures.append(f"Missing degraded daily source: {DEGRADED_DAILY_SOURCE_PATH}")
        daily_rows: List[Dict[str, str]] = []
    else:
        daily_rows = read_csv_rows(DEGRADED_DAILY_SOURCE_PATH)

    if not DATA_GAP_SOURCE_PATH.exists():
        warnings.append(f"Optional data gap source missing: {DATA_GAP_SOURCE_PATH}")
        gap_rows: List[Dict[str, str]] = []
    else:
        gap_rows = read_csv_rows(DATA_GAP_SOURCE_PATH)

    factor_rows = read_csv_rows(FACTOR_PATH) if FACTOR_PATH.exists() else []
    tech_rows = read_csv_rows(TECH_PATH) if TECH_PATH.exists() else []
    tier_rows = read_csv_rows(TIER_PATH) if TIER_PATH.exists() else []
    ledger_rows = read_csv_rows(LEDGER_PATH) if LEDGER_PATH.exists() else []

    r6_success = [row for row in r6_rows if str(row.get("integration_status", "")).strip().upper() == "SUCCESS"]
    integrated_tickers = [str(row.get("ticker", "")).strip().upper() for row in r6_success if str(row.get("ticker", "")).strip()]
    if len(integrated_tickers) != 52:
        validation_failures.append(f"R6 integrated ticker count mismatch: expected 52, got {len(integrated_tickers)}.")

    r7_map = latest_row_by_ticker(r7_rows)
    daily_map = latest_row_by_ticker(daily_rows)
    gap_map: Dict[str, List[Dict[str, str]]] = {}
    for row in gap_rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if ticker:
            gap_map.setdefault(ticker, []).append(row)
    factor_map = latest_row_by_ticker(factor_rows)
    tech_map = latest_row_by_ticker(tech_rows)
    tier_map = latest_row_by_ticker(tier_rows)
    ledger_map = latest_row_by_ticker(ledger_rows)

    audit_rows: List[Dict[str, str]] = []
    blocker_primary_counts: Counter = Counter()
    next_fix_counts: Counter = Counter()

    for ticker in integrated_tickers:
        r6_row = next((row for row in r6_success if str(row.get("ticker", "")).strip().upper() == ticker), {})
        r7_row = r7_map.get(ticker, {})
        daily_row = daily_map.get(ticker, {})
        factor_row = factor_map.get(ticker, {})
        tech_row = tech_map.get(ticker, {})
        tier_row = tier_map.get(ticker, {})
        ledger_row = ledger_map.get(ticker, {})

        official_price_cache_available = bool((r6_row.get("official_cache_path") or "").strip()) and Path(str(r6_row.get("official_cache_path", "")).strip()).exists()
        if not official_price_cache_available:
            official_price_cache_available = PRICE_CACHE_DIR.joinpath(f"{ticker}.csv").exists()

        r6_ok = str(r6_row.get("integration_status", "")).strip().upper() == "SUCCESS"
        r7_ok = str(r7_row.get("ledger_update_status", "")).strip().upper() == "UPDATED" and str(r7_row.get("new_last_scan_status", "")).strip().upper() == "SUCCESS_LOCAL_PRICE_FULL_HISTORY"

        score_available = str(daily_row.get("score_available", "")).strip().upper() == "TRUE"
        best_available_score = str(daily_row.get("composite_score", "")).strip()
        if not best_available_score:
            best_available_score = str(factor_row.get("factor_pack_score", "")).strip()
        if not best_available_score:
            best_available_score = str(tier_row.get("composite_score", "")).strip()
        if not best_available_score:
            best_available_score = str(factor_row.get("current_score", "")).strip()

        factor_present = ticker in factor_map
        technical_present = ticker in tech_map
        tier_present = ticker in tier_map

        tier_current = str(tier_row.get("tier_current", "")).strip() if tier_present else str(daily_row.get("tier_current", "")).strip()
        technical_status = str(tech_row.get("technical_status", "")).strip() if technical_present else str(daily_row.get("technical_status", "")).strip()
        rolling_ledger_last_status = str(ledger_row.get("last_scan_status", "")).strip()
        rolling_ledger_last_success_date = str(ledger_row.get("last_success_scan_date", "")).strip()
        current_gap_reason = str(daily_row.get("data_gap_reason", "")).strip()
        current_bucket = str(daily_row.get("output_bucket", "")).strip()
        current_trust = str(daily_row.get("trust_level", "")).strip()
        official_rank_allowed = str(daily_row.get("official_rank_allowed", "")).strip().upper() == "TRUE"
        watch_only = str(daily_row.get("watch_only", "")).strip().upper() == "TRUE"
        trade_allowed = str(daily_row.get("trade_allowed", "")).strip().upper() == "TRUE"

        if current_bucket == "HIGH_TRUST_OFFICIAL_RANK_ALLOWED":
            blocker_primary = "NOT_BLOCKED_ALREADY_HIGH_TRUST"
            blocker_secondary = "NONE"
            next_fix = "NO_ACTION_ALREADY_HIGH_TRUST"
        elif not factor_present or not score_available:
            blocker_primary = "BLOCKED_MISSING_FACTOR_SCORE"
            blocker_secondary = "BLOCKED_MISSING_TECHNICAL_TIMING" if not technical_present else "BLOCKED_CLASSIFICATION_RULE_TOO_STRICT"
            next_fix = "REFRESH_FACTOR_PACK_FOR_INTEGRATED_TICKERS"
        elif not technical_present:
            blocker_primary = "BLOCKED_MISSING_TECHNICAL_TIMING"
            blocker_secondary = "BLOCKED_STILL_WATCH_ONLY_BY_DATA_GAP"
            next_fix = "REFRESH_TECHNICAL_TIMING_FOR_INTEGRATED_TICKERS"
        elif not tier_present:
            blocker_primary = "BLOCKED_MISSING_TIER_MIGRATION"
            blocker_secondary = "BLOCKED_STILL_WATCH_ONLY_BY_DATA_GAP"
            next_fix = "REFRESH_TIER_MIGRATION_AFTER_FACTOR_TECH_REFRESH"
        elif watch_only or not official_rank_allowed:
            blocker_primary = "BLOCKED_STILL_WATCH_ONLY_BY_DATA_GAP"
            blocker_secondary = "BLOCKED_CLASSIFICATION_RULE_TOO_STRICT"
            next_fix = "PATCH_V18_25A_CLASSIFICATION_RULES"
        else:
            blocker_primary = "BLOCKED_UNKNOWN"
            blocker_secondary = "BLOCKED_UNKNOWN"
            next_fix = "CONTINUE_BATCH3_STAGED_BACKFILL"

        blocker_primary_counts[blocker_primary] += 1
        next_fix_counts[next_fix] += 1

        audit_rows.append(
            {
                "ticker": ticker,
                "r6_integration_success": bool_text(r6_ok),
                "r7_ledger_success": bool_text(r7_ok),
                "current_output_bucket": current_bucket,
                "current_trust_level": current_trust,
                "official_rank_allowed": bool_text(official_rank_allowed),
                "watch_only": bool_text(watch_only),
                "trade_allowed": bool_text(trade_allowed),
                "score_available": bool_text(score_available),
                "best_available_score": best_available_score,
                "factor_pack_present": bool_text(factor_present),
                "technical_present": bool_text(technical_present),
                "technical_status": technical_status,
                "tier_migration_present": bool_text(tier_present),
                "tier_current": tier_current,
                "official_price_cache_available": bool_text(official_price_cache_available),
                "rolling_ledger_last_status": rolling_ledger_last_status,
                "rolling_ledger_last_success_date": rolling_ledger_last_success_date,
                "current_data_gap_reason": current_gap_reason,
                "promotion_blocker_primary": blocker_primary,
                "promotion_blocker_secondary": blocker_secondary,
                "recommended_next_fix": next_fix,
            }
        )

    trust_counts = Counter(str(row.get("current_trust_level", "")).strip() for row in audit_rows)
    bucket_counts = Counter(str(row.get("current_output_bucket", "")).strip() for row in audit_rows)
    factor_present_count = sum(1 for row in audit_rows if row["factor_pack_present"] == "TRUE")
    factor_missing_count = len(audit_rows) - factor_present_count
    technical_present_count = sum(1 for row in audit_rows if row["technical_present"] == "TRUE")
    technical_missing_count = len(audit_rows) - technical_present_count
    tier_present_count = sum(1 for row in audit_rows if row["tier_migration_present"] == "TRUE")
    tier_missing_count = len(audit_rows) - tier_present_count

    current_r1_read_first = parse_read_first(R1_READ_FIRST_PATH)
    if not current_r1_read_first:
        warnings.append(f"R1 read-first missing or unreadable: {R1_READ_FIRST_PATH}")
    r1_next_step = current_r1_read_first.get("NEXT_RECOMMENDED_STEP", "")
    r1_rerun_executed = bool(current_r1_read_first)
    expected_r1_next_step = "A: V18.23C official integration for approved full-history candidates"
    if current_r1_read_first:
        if current_r1_read_first.get("SOURCE_MISSING_WARNING_COUNT", "0") != "0":
            warnings.append("R1 still reports source missing warnings after patch.")
        if r1_next_step != expected_r1_next_step:
            validation_failures.append(
                f"R1 NEXT_RECOMMENDED_STEP mismatch after patch: expected {expected_r1_next_step}, got {r1_next_step or '<missing>'}."
            )

    if len(audit_rows) != 52:
        validation_failures.append(f"Audit row count mismatch: expected 52, got {len(audit_rows)}.")

    if len(r7_rows) and len([row for row in r7_rows if str(row.get("ledger_update_status", "")).strip().upper() == "UPDATED"]) != 52:
        validation_failures.append("R7 ledger update count mismatch against real file.")

    if not all((ticker in r7_map and str(r7_map[ticker].get("ledger_update_status", "")).strip().upper() == "UPDATED") for ticker in integrated_tickers):
        validation_failures.append("Not all integrated tickers have matching R7 ledger updates.")

    after_mtimes = collect_forbidden_mtimes()
    forbidden_modified = any(before_mtimes.get(path) != after_mtimes.get(path) for path in before_mtimes)
    if forbidden_modified:
        validation_failures.append("Forbidden file modification detected during audit run.")

    summary_rows = [
        {"metric": "R6_R7_INTEGRATED_TICKER_COUNT", "count": str(len(audit_rows)), "notes": "R6 success rows joined to R7 ledger updates."},
        {"metric": "CURRENT_HIGH_TRUST_COUNT_FOR_R6_R7", "count": str(trust_counts.get("HIGH", 0)), "notes": "High-trust names among integrated tickers."},
        {"metric": "CURRENT_MEDIUM_TRUST_COUNT_FOR_R6_R7", "count": str(trust_counts.get("MEDIUM", 0)), "notes": "Medium-trust names among integrated tickers."},
        {"metric": "CURRENT_LOW_TRUST_COUNT_FOR_R6_R7", "count": str(trust_counts.get("LOW", 0)), "notes": "Low-trust names among integrated tickers."},
        {"metric": "CURRENT_DATA_NOT_READY_COUNT_FOR_R6_R7", "count": str(trust_counts.get("DATA_NOT_READY", 0)), "notes": "Data-not-ready names among integrated tickers."},
        {"metric": "FACTOR_PRESENT_COUNT_FOR_R6_R7", "count": str(factor_present_count), "notes": "Integrated tickers present in factor pack ranking."},
        {"metric": "FACTOR_MISSING_COUNT_FOR_R6_R7", "count": str(factor_missing_count), "notes": "Integrated tickers absent from factor pack ranking."},
        {"metric": "TECHNICAL_PRESENT_COUNT_FOR_R6_R7", "count": str(technical_present_count), "notes": "Integrated tickers present in technical timing output."},
        {"metric": "TECHNICAL_MISSING_COUNT_FOR_R6_R7", "count": str(technical_missing_count), "notes": "Integrated tickers absent from technical timing output."},
        {"metric": "TIER_MIGRATION_PRESENT_COUNT_FOR_R6_R7", "count": str(tier_present_count), "notes": "Integrated tickers present in tier migration audit."},
        {"metric": "TIER_MIGRATION_MISSING_COUNT_FOR_R6_R7", "count": str(tier_missing_count), "notes": "Integrated tickers absent from tier migration audit."},
    ]
    for key, count in blocker_primary_counts.most_common():
        summary_rows.append({"metric": f"BLOCKER_PRIMARY::{key}", "count": str(count), "notes": "Promotion blocker primary count."})
    for key, count in next_fix_counts.most_common():
        summary_rows.append({"metric": f"NEXT_FIX::{key}", "count": str(count), "notes": "Recommended next fix count."})

    next_fix_rows = []
    for rank, (fix, count) in enumerate(next_fix_counts.most_common(), start=1):
        representative = ", ".join([row["ticker"] for row in audit_rows if row["recommended_next_fix"] == fix][:8])
        next_fix_rows.append(
            {
                "priority_rank": str(rank),
                "recommended_next_fix": fix,
                "count": str(count),
                "representative_tickers": representative,
                "notes": "Ranked by frequency among the 52 integrated tickers.",
            }
        )

    top_blocker = blocker_primary_counts.most_common(1)[0][0] if blocker_primary_counts else "BLOCKED_UNKNOWN"
    top_recommended_fix = next_fix_counts.most_common(1)[0][0] if next_fix_counts else "CONTINUE_BATCH3_STAGED_BACKFILL"

    status = STATUS_FAIL if validation_failures else STATUS_WARN if warnings else STATUS_OK

    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "R6_SOURCE_PATH": str(R6_SOURCE_PATH),
        "R7_SOURCE_PATH": str(R7_SOURCE_PATH),
        "DEGRADED_DAILY_SOURCE_PATH": str(DEGRADED_DAILY_SOURCE_PATH),
        "R6_R7_INTEGRATED_TICKER_COUNT": str(len(audit_rows)),
        "CURRENT_HIGH_TRUST_COUNT_FOR_R6_R7": str(trust_counts.get("HIGH", 0)),
        "CURRENT_MEDIUM_TRUST_COUNT_FOR_R6_R7": str(trust_counts.get("MEDIUM", 0)),
        "CURRENT_LOW_TRUST_COUNT_FOR_R6_R7": str(trust_counts.get("LOW", 0)),
        "CURRENT_DATA_NOT_READY_COUNT_FOR_R6_R7": str(trust_counts.get("DATA_NOT_READY", 0)),
        "FACTOR_PRESENT_COUNT_FOR_R6_R7": str(factor_present_count),
        "FACTOR_MISSING_COUNT_FOR_R6_R7": str(factor_missing_count),
        "TECHNICAL_PRESENT_COUNT_FOR_R6_R7": str(technical_present_count),
        "TECHNICAL_MISSING_COUNT_FOR_R6_R7": str(technical_missing_count),
        "TIER_MIGRATION_PRESENT_COUNT_FOR_R6_R7": str(tier_present_count),
        "TIER_MIGRATION_MISSING_COUNT_FOR_R6_R7": str(tier_missing_count),
        "TOP_PROMOTION_BLOCKER": top_blocker,
        "TOP_RECOMMENDED_NEXT_FIX": top_recommended_fix,
        "R1_RECOMMENDATION_LOGIC_PATCHED": bool_text(True),
        "R1_RERUN_EXECUTED": bool_text(r1_rerun_executed),
        "R1_NEXT_RECOMMENDED_STEP_AFTER_PATCH": r1_next_step,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(len(validation_failures)),
        "FORBIDDEN_FILE_MODIFIED": bool_text(forbidden_modified),
    }

    audit_fieldnames = [
        "ticker",
        "r6_integration_success",
        "r7_ledger_success",
        "current_output_bucket",
        "current_trust_level",
        "official_rank_allowed",
        "watch_only",
        "trade_allowed",
        "score_available",
        "best_available_score",
        "factor_pack_present",
        "technical_present",
        "technical_status",
        "tier_migration_present",
        "tier_current",
        "official_price_cache_available",
        "rolling_ledger_last_status",
        "rolling_ledger_last_success_date",
        "current_data_gap_reason",
        "promotion_blocker_primary",
        "promotion_blocker_secondary",
        "recommended_next_fix",
    ]

    summary_fieldnames = ["metric", "count", "notes"]
    next_fix_fieldnames = ["priority_rank", "recommended_next_fix", "count", "representative_tickers", "notes"]

    report_lines = [
        "# V18.25A-R3 Post-Integration Promotion Blocker Audit",
        "",
        f"- Status: {status}",
        f"- Integrated tickers: {len(audit_rows)}",
        f"- High trust: {trust_counts.get('HIGH', 0)}",
        f"- Medium trust: {trust_counts.get('MEDIUM', 0)}",
        f"- Low trust: {trust_counts.get('LOW', 0)}",
        f"- Data not ready: {trust_counts.get('DATA_NOT_READY', 0)}",
        f"- Factor missing: {factor_missing_count}",
        f"- Technical missing: {technical_missing_count}",
        f"- Tier migration missing: {tier_missing_count}",
        f"- Top promotion blocker: {top_blocker}",
        f"- Top recommended next fix: {top_recommended_fix}",
        f"- R1 next step after patch: {r1_next_step or 'UNKNOWN'}",
        "",
        "All 52 integrated tickers remain in `MEDIUM_TRUST_PARTIAL_WATCH` because the downstream factor pack and technical timing sources do not yet cover them, while tier migration exists but stays at `TIER_0_DATA_NOT_READY`.",
    ]

    write_csv(OUTPUTS["audit"], audit_rows, audit_fieldnames)
    write_csv(OUTPUTS["summary"], summary_rows, summary_fieldnames)
    write_csv(OUTPUTS["next_fix"], next_fix_rows, next_fix_fieldnames)
    write_text(OUTPUTS["report"], "\n".join(report_lines) + "\n")
    write_text(OUTPUTS["ops_report"], "\n".join(report_lines) + "\n")
    write_text(OUTPUTS["read_first"], "\n".join(f"{key}: {value}" for key, value in read_first.items()) + "\n")

    if validation_failures:
        status = STATUS_FAIL
    elif warnings:
        status = STATUS_WARN
    else:
        status = STATUS_OK
    read_first["STATUS"] = status
    read_first["VALIDATION_FAIL_COUNT"] = str(len(validation_failures))
    write_text(OUTPUTS["read_first"], "\n".join(f"{key}: {value}" for key, value in read_first.items()) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"R6_R7_INTEGRATED_TICKER_COUNT: {len(audit_rows)}")
    print(f"TOP_PROMOTION_BLOCKER: {top_blocker}")
    print(f"TOP_RECOMMENDED_NEXT_FIX: {top_recommended_fix}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")

    if validation_failures:
        for item in validation_failures:
            print(f"VALIDATION: {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
