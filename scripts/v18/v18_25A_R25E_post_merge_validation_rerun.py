from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R25E_POST_MERGE_VALIDATION_READY"
STATUS_DOWNSTREAM_SKIPPED = "WARN_V18_25A_R25E_DOWNSTREAM_REVIEW_SKIPPED"
STATUS_STILL_BLOCKED = "WARN_V18_25A_R25E_TARGETS_STILL_BLOCKED"
STATUS_CLASS_MISSING = "WARN_V18_25A_R25E_CLASSIFICATION_OUTPUT_MISSING"
STATUS_RANKED_MISSING = "WARN_V18_25A_R25E_RANKED_CANDIDATE_OUTPUT_MISSING"
STATUS_PARTIAL_GAP = "WARN_V18_25A_R25E_PARTIAL_VALIDATION_GAP"

MODE = "READ_ONLY_POST_MERGE_VALIDATION"
EXPECTED_TARGET_COUNT = 93

R25D_POST = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_POST_MERGE_VALIDATION.csv"
R25D_FACTOR_RESULT = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_FACTOR_MERGE_RESULT.csv"
R25D_TECH_RESULT = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_TECHNICAL_MERGE_RESULT.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
R24_TARGETS = "outputs/v18/readiness/V18_25A_R24_CURRENT_TARGETS.csv"
R24_SUMMARY = "outputs/v18/readiness/V18_25A_R24_CURRENT_REFRESH_READINESS_SUMMARY.csv"
HIGH_TRUST = "outputs/v18/degraded_daily_review/V18_25A_R1_CURRENT_HIGH_TRUST_TOP30.csv"
DATA_NOT_READY = "outputs/v18/degraded_daily_review/V18_25A_R1_CURRENT_DATA_NOT_READY_PRIORITY.csv"
WATCH_ONLY = "outputs/v18/degraded_daily_review/V18_25A_R1_CURRENT_WATCH_ONLY_PRIORITY.csv"

OUT_TARGETS = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_TARGETS.csv"
OUT_PRESENCE = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_FACTOR_TECHNICAL_PRESENCE_AUDIT.csv"
OUT_CLEARANCE = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_BLOCKER_CLEARANCE_AUDIT.csv"
OUT_TRUST = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_TRUST_CLASSIFICATION_AUDIT.csv"
OUT_RANKED = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_RANKED_CANDIDATE_IMPACT.csv"
OUT_BLOCKERS = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_REMAINING_BLOCKERS.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25E_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25E_CURRENT_POST_MERGE_VALIDATION_REPORT.md"

TARGET_FIELDS = ["priority_rank", "ticker", "source", "factor_merge_success", "technical_merge_success"]
PRESENCE_FIELDS = [
    "ticker", "factor_present", "factor_score_present", "factor_score_numeric", "technical_present",
    "technical_score_present", "technical_score_numeric", "price_cache_present", "price_cache_readable",
    "rolling_ledger_present", "factor_duplicate_count", "technical_duplicate_count", "fully_factor_technical_ready", "reason",
]
CLEARANCE_FIELDS = [
    "ticker", "blocked_missing_factor_score_cleared", "blocked_missing_technical_timing_cleared",
    "blocked_missing_price_cache", "blocked_not_in_rolling_ledger", "all_core_blockers_cleared", "reason",
]
TRUST_FIELDS = ["ticker", "classification_source", "trust_level", "output_bucket", "official_rank_allowed", "reason"]
RANKED_FIELDS = ["ticker", "ranked_candidate_present", "rank", "final_action", "score_source_status", "reason"]
BLOCKER_FIELDS = ["ticker", "blocker_type", "reason", "next_action"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "MAX_TICKERS", "TARGET_SOURCE_PATH", "TARGET_TICKER_COUNT", "FACTOR_PACK_PATH",
    "TECHNICAL_TIMING_PATH", "FACTOR_TARGET_PRESENT_COUNT", "FACTOR_TARGET_MISSING_COUNT", "FACTOR_SCORE_PRESENT_COUNT",
    "FACTOR_SCORE_MISSING_COUNT", "TECHNICAL_TARGET_PRESENT_COUNT", "TECHNICAL_TARGET_MISSING_COUNT",
    "TECHNICAL_SCORE_PRESENT_COUNT", "TECHNICAL_SCORE_MISSING_COUNT", "PRICE_CACHE_PRESENT_COUNT", "PRICE_CACHE_MISSING_COUNT",
    "ROLLING_LEDGER_PRESENT_COUNT", "ROLLING_LEDGER_MISSING_COUNT", "FACTOR_DUPLICATE_TARGET_COUNT",
    "TECHNICAL_DUPLICATE_TARGET_COUNT", "MISSING_FACTOR_BLOCKER_CLEARED_COUNT", "MISSING_TECHNICAL_BLOCKER_CLEARED_COUNT",
    "MISSING_PRICE_BLOCKER_COUNT", "MISSING_LEDGER_BLOCKER_COUNT", "TARGETS_FULLY_FACTOR_TECHNICAL_READY_COUNT",
    "TARGETS_STILL_BLOCKED_COUNT", "RANKED_CANDIDATE_TARGET_PRESENT_COUNT", "DOWNSTREAM_REVIEW_RAN",
    "DOWNSTREAM_REVIEW_STATUS", "HIGH_TRUST_COUNT_AFTER", "MEDIUM_COUNT_AFTER", "LOW_COUNT_AFTER", "DATA_NOT_READY_COUNT_AFTER",
    "WATCH_ONLY_COUNT_AFTER", "OFFICIAL_RANK_ALLOWED_COUNT_AFTER", "BLOCKER_CLEARANCE_AUDIT_PATH",
    "TRUST_CLASSIFICATION_AUDIT_PATH", "RANKED_CANDIDATE_IMPACT_PATH", "REMAINING_BLOCKERS_PATH",
    "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED",
    "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED", "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]


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
        except Exception:
            continue
    return [], []


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): file_sig(p) for p in root.rglob("*") if p.is_file()}


def by_ticker(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get("ticker")): row for row in rows if norm_ticker(row.get("ticker"))}


def count_by_ticker(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            counts[ticker] = counts.get(ticker, 0) + 1
    return counts


def score_col(fields: Sequence[str], candidates: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return ""


def price_cache_readable(path: Path) -> bool:
    rows, fields = read_csv(path)
    return bool(rows) and {"date", "close"}.issubset({field.lower() for field in fields})


def first_existing_classification(root: Path, ticker: str) -> Tuple[str, str, str, str]:
    for source, path in [("HIGH_TRUST", HIGH_TRUST), ("DATA_NOT_READY", DATA_NOT_READY), ("WATCH_ONLY", WATCH_ONLY)]:
        rows, _ = read_csv(root / path)
        for row in rows:
            if norm_ticker(row.get("ticker")) == ticker:
                return source, str(row.get("trust_level") or ("HIGH" if source == "HIGH_TRUST" else "")), str(row.get("output_bucket") or source), str(row.get("reason_summary") or row.get("data_gap_reason") or row.get("priority_reason") or "")
    return "NOT_FOUND", "", "", ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=93)
    parser.add_argument("--run-downstream-review", action="store_true")
    parser.add_argument("--no-rerun", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25E_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": file_sig(root / FACTOR_CURRENT),
        "technical": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }

    factor_result, _ = read_csv(root / R25D_FACTOR_RESULT)
    tech_result, _ = read_csv(root / R25D_TECH_RESULT)
    factor_rows, factor_fields = read_csv(root / FACTOR_CURRENT)
    tech_rows, tech_fields = read_csv(root / TECH_CURRENT)
    ledger_rows, _ = read_csv(root / LEDGER)
    ranked_rows, _ = read_csv(root / RANKED)

    tech_success = {norm_ticker(row.get("ticker")): is_true(row.get("success")) for row in tech_result}
    targets = [
        {
            "priority_rank": idx,
            "ticker": norm_ticker(row.get("ticker")),
            "source": R25D_FACTOR_RESULT,
            "factor_merge_success": str(is_true(row.get("success"))).upper(),
            "technical_merge_success": str(tech_success.get(norm_ticker(row.get("ticker")), False)).upper(),
        }
        for idx, row in enumerate(factor_result, 1)
        if norm_ticker(row.get("ticker")) and is_true(row.get("success"))
    ][: max(args.max_tickers, 0)]
    target_tickers = [str(row["ticker"]) for row in targets]
    target_set = set(target_tickers)

    factor_by = by_ticker(factor_rows)
    tech_by = by_ticker(tech_rows)
    ledger_set = set(by_ticker(ledger_rows))
    ranked_by = by_ticker(ranked_rows)
    factor_counts = count_by_ticker(factor_rows)
    tech_counts = count_by_ticker(tech_rows)
    factor_score = score_col(factor_fields, ["factor_score", "factor_pack_score", "F010_XSEC_COMPOSITE_RANK"])
    tech_score = score_col(tech_fields, ["technical_timing_score", "technical_score"])

    presence_rows: List[Dict[str, object]] = []
    clearance_rows: List[Dict[str, object]] = []
    trust_rows: List[Dict[str, object]] = []
    ranked_impact_rows: List[Dict[str, object]] = []
    blockers: List[Dict[str, object]] = []
    for ticker in target_tickers:
        factor_present = ticker in factor_by
        factor_score_numeric = factor_present and to_float(factor_by[ticker].get(factor_score)) is not None
        tech_present = ticker in tech_by
        tech_score_numeric = tech_present and to_float(tech_by[ticker].get(tech_score)) is not None
        price_path = root / PRICE_CACHE / f"{ticker}.csv"
        price_present = price_path.exists()
        price_readable = price_cache_readable(price_path)
        ledger_present = ticker in ledger_set
        reasons: List[str] = []
        if not factor_score_numeric:
            reasons.append("BLOCKED_MISSING_FACTOR_SCORE")
            blockers.append({"ticker": ticker, "blocker_type": "BLOCKED_MISSING_FACTOR_SCORE", "reason": "Factor row or numeric score missing.", "next_action": "Review official factor pack row."})
        if not tech_score_numeric:
            reasons.append("BLOCKED_MISSING_TECHNICAL_TIMING")
            blockers.append({"ticker": ticker, "blocker_type": "BLOCKED_MISSING_TECHNICAL_TIMING", "reason": "Technical row or numeric score missing.", "next_action": "Review official technical timing row."})
        if not price_readable:
            reasons.append("BLOCKED_MISSING_PRICE_CACHE")
            blockers.append({"ticker": ticker, "blocker_type": "BLOCKED_MISSING_PRICE_CACHE", "reason": "Price cache missing or unreadable.", "next_action": "Review local price cache."})
        if not ledger_present:
            reasons.append("BLOCKED_NOT_IN_ROLLING_LEDGER")
            blockers.append({"ticker": ticker, "blocker_type": "BLOCKED_NOT_IN_ROLLING_LEDGER", "reason": "Ticker missing from rolling ledger.", "next_action": "Review rolling ledger."})
        if factor_counts.get(ticker, 0) > 1:
            reasons.append("BLOCKED_DUPLICATE_FACTOR_ROW")
            blockers.append({"ticker": ticker, "blocker_type": "BLOCKED_DUPLICATE_FACTOR_ROW", "reason": "Duplicate target rows in factor pack.", "next_action": "Deduplicate official factor pack."})
        if tech_counts.get(ticker, 0) > 1:
            reasons.append("BLOCKED_DUPLICATE_TECHNICAL_ROW")
            blockers.append({"ticker": ticker, "blocker_type": "BLOCKED_DUPLICATE_TECHNICAL_ROW", "reason": "Duplicate target rows in technical timing.", "next_action": "Deduplicate official technical timing."})
        ready = not reasons
        presence_rows.append({
            "ticker": ticker,
            "factor_present": str(factor_present).upper(),
            "factor_score_present": str(bool(factor_present and str(factor_by[ticker].get(factor_score, "")).strip())).upper(),
            "factor_score_numeric": str(factor_score_numeric).upper(),
            "technical_present": str(tech_present).upper(),
            "technical_score_present": str(bool(tech_present and str(tech_by[ticker].get(tech_score, "")).strip())).upper(),
            "technical_score_numeric": str(tech_score_numeric).upper(),
            "price_cache_present": str(price_present).upper(),
            "price_cache_readable": str(price_readable).upper(),
            "rolling_ledger_present": str(ledger_present).upper(),
            "factor_duplicate_count": factor_counts.get(ticker, 0),
            "technical_duplicate_count": tech_counts.get(ticker, 0),
            "fully_factor_technical_ready": str(ready).upper(),
            "reason": "; ".join(reasons),
        })
        clearance_rows.append({
            "ticker": ticker,
            "blocked_missing_factor_score_cleared": str(factor_score_numeric).upper(),
            "blocked_missing_technical_timing_cleared": str(tech_score_numeric).upper(),
            "blocked_missing_price_cache": str(not price_readable).upper(),
            "blocked_not_in_rolling_ledger": str(not ledger_present).upper(),
            "all_core_blockers_cleared": str(ready).upper(),
            "reason": "cleared" if ready else "; ".join(reasons),
        })
        class_source, trust, bucket, class_reason = first_existing_classification(root, ticker)
        official_allowed = class_source == "HIGH_TRUST" or ticker in ranked_by
        trust_rows.append({
            "ticker": ticker,
            "classification_source": class_source,
            "trust_level": trust,
            "output_bucket": bucket,
            "official_rank_allowed": str(official_allowed).upper(),
            "reason": class_reason,
        })
        ranked = ranked_by.get(ticker, {})
        ranked_impact_rows.append({
            "ticker": ticker,
            "ranked_candidate_present": str(bool(ranked)).upper(),
            "rank": ranked.get("rank", ""),
            "final_action": ranked.get("final_action", ""),
            "score_source_status": ranked.get("score_source_status", ""),
            "reason": ranked.get("reason", "") if ranked else "not present in current ranked candidates",
        })

    write_csv(root / OUT_TARGETS, targets, TARGET_FIELDS)
    write_csv(root / OUT_PRESENCE, presence_rows, PRESENCE_FIELDS)
    write_csv(root / OUT_CLEARANCE, clearance_rows, CLEARANCE_FIELDS)
    write_csv(root / OUT_TRUST, trust_rows, TRUST_FIELDS)
    write_csv(root / OUT_RANKED, ranked_impact_rows, RANKED_FIELDS)
    write_csv(root / OUT_BLOCKERS, blockers, BLOCKER_FIELDS)

    downstream_ran = False
    downstream_status = "SKIPPED_NO_RERUN_REQUESTED"
    if args.no_rerun:
        downstream_status = "SKIPPED_BY_NO_RERUN"
    elif args.run_downstream_review:
        downstream_status = "SKIPPED_NO_SAFE_READ_ONLY_WRAPPER_CONFIRMED"

    factor_present_count = sum(1 for row in presence_rows if row["factor_present"] == "TRUE")
    tech_present_count = sum(1 for row in presence_rows if row["technical_present"] == "TRUE")
    factor_score_present_count = sum(1 for row in presence_rows if row["factor_score_numeric"] == "TRUE")
    tech_score_present_count = sum(1 for row in presence_rows if row["technical_score_numeric"] == "TRUE")
    price_present_count = sum(1 for row in presence_rows if row["price_cache_readable"] == "TRUE")
    ledger_present_count = sum(1 for row in presence_rows if row["rolling_ledger_present"] == "TRUE")
    factor_dupe_count = sum(1 for row in presence_rows if int(row["factor_duplicate_count"]) > 1)
    tech_dupe_count = sum(1 for row in presence_rows if int(row["technical_duplicate_count"]) > 1)
    ready_count = sum(1 for row in presence_rows if row["fully_factor_technical_ready"] == "TRUE")
    blocked_count = len(targets) - ready_count
    ranked_present_count = sum(1 for row in ranked_impact_rows if row["ranked_candidate_present"] == "TRUE")

    high_after = sum(1 for row in trust_rows if row["classification_source"] == "HIGH_TRUST")
    data_not_ready_after = sum(1 for row in trust_rows if row["classification_source"] == "DATA_NOT_READY")
    watch_after = sum(1 for row in trust_rows if row["classification_source"] == "WATCH_ONLY")
    medium_after = sum(1 for row in trust_rows if str(row["trust_level"]).upper() == "MEDIUM")
    low_after = sum(1 for row in trust_rows if str(row["trust_level"]).upper() == "LOW")
    official_allowed_after = sum(1 for row in trust_rows if row["official_rank_allowed"] == "TRUE")
    classification_available = any((root / p).exists() for p in [HIGH_TRUST, DATA_NOT_READY, WATCH_ONLY])
    ranked_available = (root / RANKED).exists()

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": file_sig(root / FACTOR_CURRENT),
        "technical": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }
    mods = {key: before[key] != after[key] for key in before}
    forbidden = any(mods.values())

    status = STATUS_OK
    if len(targets) != EXPECTED_TARGET_COUNT or factor_dupe_count or tech_dupe_count:
        status = STATUS_PARTIAL_GAP
    elif blocked_count:
        status = STATUS_STILL_BLOCKED
    elif not classification_available:
        status = STATUS_CLASS_MISSING
    elif not ranked_available:
        status = STATUS_RANKED_MISSING
    elif args.run_downstream_review and not downstream_ran:
        status = STATUS_DOWNSTREAM_SKIPPED

    validation_fail_count = int(status in {STATUS_PARTIAL_GAP, STATUS_STILL_BLOCKED} or forbidden)
    next_step = (
        "R26: Factor effectiveness validation / forward-test integration readiness."
        if blocked_count == 0 and len(targets) == EXPECTED_TARGET_COUNT
        else "Resolve remaining blockers before factor effectiveness validation."
    )
    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "MAX_TICKERS": args.max_tickers,
        "TARGET_SOURCE_PATH": R25D_FACTOR_RESULT,
        "TARGET_TICKER_COUNT": len(targets),
        "FACTOR_PACK_PATH": FACTOR_CURRENT,
        "TECHNICAL_TIMING_PATH": TECH_CURRENT,
        "FACTOR_TARGET_PRESENT_COUNT": factor_present_count,
        "FACTOR_TARGET_MISSING_COUNT": len(targets) - factor_present_count,
        "FACTOR_SCORE_PRESENT_COUNT": factor_score_present_count,
        "FACTOR_SCORE_MISSING_COUNT": len(targets) - factor_score_present_count,
        "TECHNICAL_TARGET_PRESENT_COUNT": tech_present_count,
        "TECHNICAL_TARGET_MISSING_COUNT": len(targets) - tech_present_count,
        "TECHNICAL_SCORE_PRESENT_COUNT": tech_score_present_count,
        "TECHNICAL_SCORE_MISSING_COUNT": len(targets) - tech_score_present_count,
        "PRICE_CACHE_PRESENT_COUNT": price_present_count,
        "PRICE_CACHE_MISSING_COUNT": len(targets) - price_present_count,
        "ROLLING_LEDGER_PRESENT_COUNT": ledger_present_count,
        "ROLLING_LEDGER_MISSING_COUNT": len(targets) - ledger_present_count,
        "FACTOR_DUPLICATE_TARGET_COUNT": factor_dupe_count,
        "TECHNICAL_DUPLICATE_TARGET_COUNT": tech_dupe_count,
        "MISSING_FACTOR_BLOCKER_CLEARED_COUNT": factor_score_present_count,
        "MISSING_TECHNICAL_BLOCKER_CLEARED_COUNT": tech_score_present_count,
        "MISSING_PRICE_BLOCKER_COUNT": len(targets) - price_present_count,
        "MISSING_LEDGER_BLOCKER_COUNT": len(targets) - ledger_present_count,
        "TARGETS_FULLY_FACTOR_TECHNICAL_READY_COUNT": ready_count,
        "TARGETS_STILL_BLOCKED_COUNT": blocked_count,
        "RANKED_CANDIDATE_TARGET_PRESENT_COUNT": ranked_present_count,
        "DOWNSTREAM_REVIEW_RAN": str(downstream_ran).upper(),
        "DOWNSTREAM_REVIEW_STATUS": downstream_status,
        "HIGH_TRUST_COUNT_AFTER": high_after,
        "MEDIUM_COUNT_AFTER": medium_after,
        "LOW_COUNT_AFTER": low_after,
        "DATA_NOT_READY_COUNT_AFTER": data_not_ready_after,
        "WATCH_ONLY_COUNT_AFTER": watch_after,
        "OFFICIAL_RANK_ALLOWED_COUNT_AFTER": official_allowed_after,
        "BLOCKER_CLEARANCE_AUDIT_PATH": OUT_CLEARANCE,
        "TRUST_CLASSIFICATION_AUDIT_PATH": OUT_TRUST,
        "RANKED_CANDIDATE_IMPACT_PATH": OUT_RANKED,
        "REMAINING_BLOCKERS_PATH": OUT_BLOCKERS,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25E Post-Merge Validation Report",
        "",
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"RUN_ID: {run_id}",
        "",
        f"- target_ticker_count: {len(targets)}",
        f"- factor_present/score: {factor_present_count}/{factor_score_present_count}",
        f"- technical_present/score: {tech_present_count}/{tech_score_present_count}",
        f"- price_cache_readable: {price_present_count}",
        f"- rolling_ledger_present: {ledger_present_count}",
        f"- targets_still_blocked: {blocked_count}",
        f"- ranked_candidate_target_present: {ranked_present_count}",
        f"- downstream_review_status: {downstream_status}",
        "",
        "R25E is validation/report only and did not modify official factor, technical, price, ledger, tier, or decision files.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
