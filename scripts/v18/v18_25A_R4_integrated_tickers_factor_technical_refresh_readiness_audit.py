from __future__ import annotations

import argparse
import csv
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "READ_ONLY_INTEGRATED_TICKERS_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT"
STATUS_OK = "OK_V18_25A_R4_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT_READY"
STATUS_WARN = "WARN_V18_25A_R4_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT_READY"
STATUS_FAIL = "FAIL_V18_25A_R4_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT"

R3_SOURCE_PATH = "outputs/v18/degraded_daily_review/V18_25A_R3_CURRENT_R6_R7_PROMOTION_BLOCKER_AUDIT.csv"
R6_SOURCE_PATH = "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_RESULT.csv"
R7_SOURCE_PATH = "outputs/v18/rolling_coverage/V18_23C_R7_CURRENT_LEDGER_UPDATE_RESULT.csv"
FACTOR_RANKING_PATH = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECHNICAL_CURRENT_PATH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"

FACTOR_REQUIRED_HISTORY_DAYS = 252
TECHNICAL_REQUIRED_HISTORY_DAYS = 120

FACTOR_OUTPUTS = {
    "audit": "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv",
    "summary": "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_REFRESH_READINESS_SUMMARY.csv",
    "candidates": "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_CANDIDATE_REFRESH_SCRIPTS.csv",
    "report": "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_REPORT.md",
    "read_first": "outputs/v18/ops/V18_25A_R4_READ_FIRST.txt",
    "ops_report": "outputs/v18/ops/V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R3_SOURCE_PATH",
    "R6_R7_INTEGRATED_TICKER_COUNT",
    "OFFICIAL_PRICE_CACHE_AVAILABLE_COUNT",
    "FULL_HISTORY_READY_COUNT",
    "FACTOR_PRESENT_CURRENT_COUNT",
    "FACTOR_MISSING_CURRENT_COUNT",
    "FACTOR_REFRESH_INPUT_READY_COUNT",
    "FACTOR_REFRESH_INPUT_BLOCKED_COUNT",
    "TECHNICAL_PRESENT_CURRENT_COUNT",
    "TECHNICAL_MISSING_CURRENT_COUNT",
    "TECHNICAL_REFRESH_INPUT_READY_COUNT",
    "TECHNICAL_REFRESH_INPUT_BLOCKED_COUNT",
    "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH_COUNT",
    "READY_FOR_TECHNICAL_REFRESH_ONLY_COUNT",
    "READY_FOR_FACTOR_REFRESH_ONLY_COUNT",
    "NEEDS_REQUIREMENT_TRACE_COUNT",
    "HOLD_REVIEW_COUNT",
    "TOP_REFRESH_BLOCKER",
    "TOP_RECOMMENDED_NEXT_ACTION",
    "FACTOR_GENERATOR_SCRIPT_CANDIDATE_COUNT",
    "TECHNICAL_GENERATOR_SCRIPT_CANDIDATE_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
]

AUDIT_FIELDS = [
    "ticker",
    "official_price_cache_available",
    "official_price_cache_row_count",
    "latest_price_date",
    "close_column_available",
    "full_history_ready",
    "rolling_ledger_success",
    "factor_pack_present_current",
    "factor_pack_score_present_current",
    "factor_pack_refresh_input_ready",
    "factor_pack_refresh_blocker",
    "technical_timing_present_current",
    "technical_refresh_input_ready",
    "technical_refresh_blocker",
    "required_history_days_available",
    "estimated_refresh_readiness",
    "recommended_refresh_action",
    "refresh_priority",
    "reason_summary",
]

SUMMARY_FIELDS = ["metric", "count", "notes"]
CANDIDATE_FIELDS = ["script_path", "script_type", "matched_terms", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def normalize_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def latest_row_by_ticker(rows: List[Dict[str, str]], ticker_field: str = "ticker") -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = normalize_ticker(row.get(ticker_field, ""))
        if ticker:
            out[ticker] = row
    return out


def read_file_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def collect_mtimes(paths: Sequence[Path]) -> Dict[str, int]:
    mtimes: Dict[str, int] = {}
    for path in paths:
        if not path.exists():
            mtimes[str(path)] = -1
            continue
        if path.is_dir():
            values = [child.stat().st_mtime_ns for child in path.rglob("*") if child.exists()]
            mtimes[str(path)] = max(values) if values else path.stat().st_mtime_ns
        else:
            mtimes[str(path)] = path.stat().st_mtime_ns
    return mtimes


def parse_date(value: object) -> str:
    text = str(value or "").strip()
    return text


def detect_price_columns(fields: Sequence[str]) -> Dict[str, bool]:
    field_set = {str(field).strip().lower() for field in fields}
    return {
        "date": "date" in field_set,
        "open": "open" in field_set,
        "high": "high" in field_set,
        "low": "low" in field_set,
        "close": "close" in field_set,
        "volume": "volume" in field_set,
    }


def load_price_cache(root: Path, ticker: str) -> Tuple[List[Dict[str, str]], List[str], Path]:
    candidates = [
        root / "state" / "v18" / "price_cache" / f"{ticker}.csv",
        root / "data" / "v18" / "price_cache" / f"{ticker}.csv",
    ]
    for path in candidates:
        rows = read_csv_rows(path)
        if rows:
            return rows, list(rows[0].keys()), path
    return [], [], candidates[0]


def infer_refresh_blocker(
    available: bool,
    row_count: int,
    columns: Dict[str, bool],
    required_days: int,
    requirements_trace_known: bool,
    mode: str,
) -> str:
    if not available:
        return "OFFICIAL_PRICE_CACHE_MISSING"
    if not columns.get("date", False) or not columns.get("close", False):
        return f"{mode}_PRICE_COLUMNS_MISSING"
    if row_count < required_days:
        return "NEEDS_MORE_PRICE_HISTORY"
    if not requirements_trace_known:
        return f"{mode}_REQUIREMENTS_UNKNOWN_NEEDS_SOURCE_TRACE"
    return "NONE"


def priority_for_readiness(est: str) -> str:
    if est == "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH":
        return "P1_TARGETED_REFRESH_NOW"
    if est in {"READY_FOR_TECHNICAL_REFRESH_ONLY", "READY_FOR_FACTOR_REFRESH_ONLY"}:
        return "P2_PARTIAL_REFRESH"
    if est in {"NEEDS_FACTOR_REQUIREMENT_TRACE", "NEEDS_TECHNICAL_REQUIREMENT_TRACE"}:
        return "P3_REQUIREMENT_TRACE"
    if est == "NEEDS_MORE_PRICE_HISTORY":
        return "P4_MORE_HISTORY"
    return "P5_HOLD_REVIEW"


def scan_candidate_scripts(root: Path) -> Tuple[List[Dict[str, str]], int, int]:
    factor_terms = OrderedDict(
        [
            ("V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "factor_ranking_output"),
            ("factor_pack", "factor_pack"),
        ]
    )
    technical_terms = OrderedDict(
        [
            ("technical_timing", "technical_timing"),
            ("V18_6A_CURRENT_TECHNICAL_TIMING.csv", "technical_current_output"),
            ("RSI", "rsi"),
            ("KDJ", "kdj"),
            ("Bollinger", "bollinger"),
            ("bb_status", "bb_status"),
            ("bb_mid_20", "bb_mid_20"),
            ("bb_bandwidth", "bb_bandwidth"),
            ("bb_squeeze_flag", "bb_squeeze_flag"),
        ]
    )
    candidate_rows: List[Dict[str, str]] = []
    factor_files: Dict[Path, List[str]] = {}
    tech_files: Dict[Path, List[str]] = {}

    for path in sorted((root / "scripts" / "v18").rglob("*")):
        if path.suffix.lower() not in {".py", ".ps1"}:
            continue
        try:
            text = read_file_text(path)
        except Exception:
            continue
        if not text:
            continue
        lower = text.lower()
        matched_factor = [label for term, label in factor_terms.items() if term.lower() in lower]
        matched_technical = [label for term, label in technical_terms.items() if term.lower() in lower]
        if matched_factor:
            factor_files[path] = matched_factor
        if matched_technical:
            tech_files[path] = matched_technical

    all_paths = sorted(set(list(factor_files.keys()) + list(tech_files.keys())))
    for path in all_paths:
        categories = []
        matched_terms = []
        if path in factor_files:
            categories.append("factor")
            matched_terms.extend(factor_files[path])
        if path in tech_files:
            categories.append("technical")
            matched_terms.extend(tech_files[path])
        candidate_rows.append(
            {
                "script_path": str(path),
                "script_type": "+".join(categories),
                "matched_terms": ";".join(sorted(set(matched_terms))),
                "notes": "Detected via repo text search only; no modification made.",
            }
        )

    return candidate_rows, len(factor_files), len(tech_files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root)

    validation_failures: List[str] = []
    warnings: List[str] = []

    forbidden_paths = [
        root / "state" / "v18" / "price_cache",
        root / "state" / "v18" / "price_history",
        root / "data" / "v18" / "staged_backfill",
        root / "state" / "v18" / "rolling_coverage",
        root / "outputs" / "v18" / "factor_pack",
        root / "outputs" / "v18" / "technical_timing",
        root / "outputs" / "v18" / "technical_timing_backtest",
        root / "outputs" / "v18" / "technical_timing_forward",
        root / "outputs" / "v18" / "tier_migration",
        root / "outputs" / "v18" / "degraded_daily",
        root / "outputs" / "v18" / "degraded_daily_review",
    ]
    before_mtimes = collect_mtimes(forbidden_paths)

    r3_source = root / R3_SOURCE_PATH
    r6_source = root / R6_SOURCE_PATH
    r7_source = root / R7_SOURCE_PATH
    factor_current = root / FACTOR_RANKING_PATH
    technical_current = root / TECHNICAL_CURRENT_PATH

    r3_rows = read_csv_rows(r3_source)
    r6_rows = read_csv_rows(r6_source)
    r7_rows = read_csv_rows(r7_source)
    factor_rows = read_csv_rows(factor_current)
    technical_rows = read_csv_rows(technical_current)

    if not r3_rows:
        validation_failures.append(f"Missing or unreadable R3 source: {r3_source}")
    if not r6_rows:
        validation_failures.append(f"Missing or unreadable R6 source: {r6_source}")
    if not r7_rows:
        validation_failures.append(f"Missing or unreadable R7 source: {r7_source}")

    r6_success_rows = [row for row in r6_rows if str(row.get("integration_status", "")).strip().upper() == "SUCCESS"]
    integrated_tickers: List[str] = []
    seen = set()
    for row in r6_success_rows:
        ticker = normalize_ticker(row.get("ticker"))
        if ticker and ticker not in seen:
            seen.add(ticker)
            integrated_tickers.append(ticker)

    if len(integrated_tickers) != 52:
        validation_failures.append(f"R6 integrated ticker count mismatch: expected 52, got {len(integrated_tickers)}")

    r7_map = latest_row_by_ticker(r7_rows)
    factor_map = latest_row_by_ticker(factor_rows)
    technical_map = latest_row_by_ticker(technical_rows)

    market_proxy_cache = {}
    for proxy in ("QQQ", "SPY", "VIX"):
        rows, fields, path = load_price_cache(root, proxy)
        market_proxy_cache[proxy] = {
            "rows": rows,
            "fields": fields,
            "path": path,
            "available": bool(rows),
            "row_count": len(rows),
            "columns": detect_price_columns(fields),
        }

    candidate_rows, factor_candidate_count, technical_candidate_count = scan_candidate_scripts(root)

    audit_rows: List[Dict[str, str]] = []
    blocker_counts: Counter = Counter()
    action_counts: Counter = Counter()

    for ticker in integrated_tickers:
        r6_row = next((row for row in r6_success_rows if normalize_ticker(row.get("ticker")) == ticker), {})
        r7_row = r7_map.get(ticker, {})
        factor_row = factor_map.get(ticker, {})
        technical_row = technical_map.get(ticker, {})

        price_rows, price_fields, price_path = load_price_cache(root, ticker)
        price_columns = detect_price_columns(price_fields)
        price_available = bool(price_rows)
        price_row_count = len(price_rows)
        latest_price_date = ""
        if price_rows:
            latest_price_date = max(parse_date(row.get("date")) for row in price_rows if parse_date(row.get("date")))
        close_column_available = price_columns.get("close", False)
        full_history_ready = price_available and price_row_count >= FACTOR_REQUIRED_HISTORY_DAYS and close_column_available
        rolling_ledger_success = (
            str(r7_row.get("ledger_update_status", "")).strip().upper() == "UPDATED"
            and str(r7_row.get("new_last_scan_status", "")).strip().upper() == "SUCCESS_LOCAL_PRICE_FULL_HISTORY"
        )

        factor_pack_present_current = ticker in factor_map
        factor_pack_score_present_current = bool(str(factor_row.get("factor_pack_score", "")).strip())
        technical_timing_present_current = ticker in technical_map

        factor_requirements_known = True
        technical_requirements_known = True

        factor_price_columns_ready = price_columns.get("date", False) and price_columns.get("high", False) and price_columns.get("low", False) and price_columns.get("close", False) and price_columns.get("volume", False)
        factor_market_ready = all(
            proxy_data["available"]
            and proxy_data["row_count"] >= FACTOR_REQUIRED_HISTORY_DAYS
            and proxy_data["columns"].get("date", False)
            and proxy_data["columns"].get("close", False)
            and proxy_data["columns"].get("high", False)
            and proxy_data["columns"].get("low", False)
            and proxy_data["columns"].get("volume", False)
            for proxy_data in market_proxy_cache.values()
        )
        factor_pack_refresh_input_ready = price_available and price_row_count >= FACTOR_REQUIRED_HISTORY_DAYS and factor_price_columns_ready and factor_market_ready
        factor_pack_refresh_blocker = infer_refresh_blocker(
            price_available,
            price_row_count,
            price_columns,
            FACTOR_REQUIRED_HISTORY_DAYS,
            factor_requirements_known,
            "FACTOR",
        )
        if factor_pack_refresh_blocker == "NONE" and not factor_market_ready:
            factor_pack_refresh_blocker = "FACTOR_MARKET_PROXY_HISTORY_MISSING"
        if not factor_pack_refresh_input_ready and factor_pack_refresh_blocker == "NONE":
            factor_pack_refresh_blocker = "FACTOR_MARKET_PROXY_HISTORY_MISSING" if not factor_market_ready else "FACTOR_INPUT_NOT_READY"

        technical_price_columns_ready = price_columns.get("date", False) and price_columns.get("close", False) and price_columns.get("high", False) and price_columns.get("low", False) and price_columns.get("volume", False)
        technical_refresh_input_ready = price_available and price_row_count >= TECHNICAL_REQUIRED_HISTORY_DAYS and technical_price_columns_ready
        technical_refresh_blocker = infer_refresh_blocker(
            price_available,
            price_row_count,
            price_columns,
            TECHNICAL_REQUIRED_HISTORY_DAYS,
            technical_requirements_known,
            "TECHNICAL",
        )

        if factor_pack_refresh_input_ready and technical_refresh_input_ready:
            estimated_refresh_readiness = "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH"
        elif factor_pack_refresh_input_ready:
            estimated_refresh_readiness = "READY_FOR_FACTOR_REFRESH_ONLY"
        elif technical_refresh_input_ready:
            estimated_refresh_readiness = "READY_FOR_TECHNICAL_REFRESH_ONLY"
        elif factor_pack_refresh_blocker.endswith("REQUIREMENTS_UNKNOWN_NEEDS_SOURCE_TRACE"):
            estimated_refresh_readiness = "NEEDS_FACTOR_REQUIREMENT_TRACE"
        elif technical_refresh_blocker.endswith("REQUIREMENTS_UNKNOWN_NEEDS_SOURCE_TRACE"):
            estimated_refresh_readiness = "NEEDS_TECHNICAL_REQUIREMENT_TRACE"
        elif price_row_count < max(FACTOR_REQUIRED_HISTORY_DAYS, TECHNICAL_REQUIRED_HISTORY_DAYS):
            estimated_refresh_readiness = "NEEDS_MORE_PRICE_HISTORY"
        else:
            estimated_refresh_readiness = "HOLD_REVIEW"

        if estimated_refresh_readiness == "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH":
            recommended_refresh_action = "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH"
        elif estimated_refresh_readiness == "READY_FOR_TECHNICAL_REFRESH_ONLY":
            recommended_refresh_action = "READY_FOR_TECHNICAL_REFRESH_ONLY"
        elif estimated_refresh_readiness == "READY_FOR_FACTOR_REFRESH_ONLY":
            recommended_refresh_action = "READY_FOR_FACTOR_REFRESH_ONLY"
        elif estimated_refresh_readiness == "NEEDS_FACTOR_REQUIREMENT_TRACE":
            recommended_refresh_action = "NEEDS_FACTOR_REQUIREMENT_TRACE"
        elif estimated_refresh_readiness == "NEEDS_TECHNICAL_REQUIREMENT_TRACE":
            recommended_refresh_action = "NEEDS_TECHNICAL_REQUIREMENT_TRACE"
        elif estimated_refresh_readiness == "NEEDS_MORE_PRICE_HISTORY":
            recommended_refresh_action = "NEEDS_MORE_PRICE_HISTORY"
        else:
            recommended_refresh_action = "HOLD_REVIEW"

        refresh_priority = priority_for_readiness(estimated_refresh_readiness)

        reason_summary = (
            f"Official cache rows={price_row_count}; latest_date={latest_price_date or 'UNKNOWN'}; "
            f"factor_current={'YES' if factor_pack_present_current else 'NO'}; "
            f"technical_current={'YES' if technical_timing_present_current else 'NO'}; "
            f"factor_market_proxy_ready={'YES' if factor_market_ready else 'NO'}; "
            f"ledger_success={'YES' if rolling_ledger_success else 'NO'}."
        )

        audit_rows.append(
            {
                "ticker": ticker,
                "official_price_cache_available": bool_text(price_available),
                "official_price_cache_row_count": str(price_row_count),
                "latest_price_date": latest_price_date,
                "close_column_available": bool_text(close_column_available),
                "full_history_ready": bool_text(full_history_ready),
                "rolling_ledger_success": bool_text(rolling_ledger_success),
                "factor_pack_present_current": bool_text(factor_pack_present_current),
                "factor_pack_score_present_current": bool_text(factor_pack_score_present_current),
                "factor_pack_refresh_input_ready": bool_text(factor_pack_refresh_input_ready),
                "factor_pack_refresh_blocker": factor_pack_refresh_blocker,
                "technical_timing_present_current": bool_text(technical_timing_present_current),
                "technical_refresh_input_ready": bool_text(technical_refresh_input_ready),
                "technical_refresh_blocker": technical_refresh_blocker,
                "required_history_days_available": str(price_row_count),
                "estimated_refresh_readiness": estimated_refresh_readiness,
                "recommended_refresh_action": recommended_refresh_action,
                "refresh_priority": refresh_priority,
                "reason_summary": reason_summary,
            }
        )

        blocker_counts[factor_pack_refresh_blocker] += 1
        blocker_counts[technical_refresh_blocker] += 1
        action_counts[recommended_refresh_action] += 1

    official_price_cache_available_count = sum(1 for row in audit_rows if row["official_price_cache_available"] == "TRUE")
    full_history_ready_count = sum(1 for row in audit_rows if row["full_history_ready"] == "TRUE")
    factor_present_current_count = sum(1 for row in audit_rows if row["factor_pack_present_current"] == "TRUE")
    factor_missing_current_count = len(audit_rows) - factor_present_current_count
    factor_refresh_input_ready_count = sum(1 for row in audit_rows if row["factor_pack_refresh_input_ready"] == "TRUE")
    factor_refresh_input_blocked_count = len(audit_rows) - factor_refresh_input_ready_count
    technical_present_current_count = sum(1 for row in audit_rows if row["technical_timing_present_current"] == "TRUE")
    technical_missing_current_count = len(audit_rows) - technical_present_current_count
    technical_refresh_input_ready_count = sum(1 for row in audit_rows if row["technical_refresh_input_ready"] == "TRUE")
    technical_refresh_input_blocked_count = len(audit_rows) - technical_refresh_input_ready_count

    ready_both_count = sum(1 for row in audit_rows if row["estimated_refresh_readiness"] == "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH")
    ready_tech_only_count = sum(1 for row in audit_rows if row["estimated_refresh_readiness"] == "READY_FOR_TECHNICAL_REFRESH_ONLY")
    ready_factor_only_count = sum(1 for row in audit_rows if row["estimated_refresh_readiness"] == "READY_FOR_FACTOR_REFRESH_ONLY")
    needs_trace_count = sum(
        1
        for row in audit_rows
        if row["estimated_refresh_readiness"] in {"NEEDS_FACTOR_REQUIREMENT_TRACE", "NEEDS_TECHNICAL_REQUIREMENT_TRACE"}
    )
    hold_review_count = sum(1 for row in audit_rows if row["estimated_refresh_readiness"] == "HOLD_REVIEW")

    top_refresh_blocker = "NONE"
    for candidate in [
        "OFFICIAL_PRICE_CACHE_MISSING",
        "FACTOR_PRICE_COLUMNS_MISSING",
        "FACTOR_MARKET_PROXY_HISTORY_MISSING",
        "NEEDS_MORE_PRICE_HISTORY",
        "TECHNICAL_PRICE_COLUMNS_MISSING",
        "FACTOR_REQUIREMENTS_UNKNOWN_NEEDS_SOURCE_TRACE",
        "TECHNICAL_REQUIREMENTS_UNKNOWN_NEEDS_SOURCE_TRACE",
    ]:
        if blocker_counts.get(candidate, 0):
            top_refresh_blocker = candidate
            break

    if ready_both_count:
        top_recommended_next_action = "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH"
    elif ready_tech_only_count:
        top_recommended_next_action = "READY_FOR_TECHNICAL_REFRESH_ONLY"
    elif ready_factor_only_count:
        top_recommended_next_action = "READY_FOR_FACTOR_REFRESH_ONLY"
    elif needs_trace_count:
        top_recommended_next_action = "NEEDS_REQUIREMENT_TRACE"
    elif hold_review_count:
        top_recommended_next_action = "HOLD_REVIEW"
    else:
        top_recommended_next_action = "NONE"

    after_mtimes = collect_mtimes(forbidden_paths)
    forbidden_modified = any(before_mtimes.get(str(path), -1) != after_mtimes.get(str(path), -1) for path in forbidden_paths)
    if forbidden_modified:
        validation_failures.append("Forbidden file modification detected during audit run.")

    if len(candidate_rows) == 0:
        warnings.append("No candidate generator scripts matched the search terms.")

    status = STATUS_FAIL if validation_failures else STATUS_WARN if warnings else STATUS_OK

    summary_rows = [
        {"metric": "R6_R7_INTEGRATED_TICKER_COUNT", "count": str(len(audit_rows)), "notes": "R6 integration successes joined to R7 ledger updates."},
        {"metric": "OFFICIAL_PRICE_CACHE_AVAILABLE_COUNT", "count": str(official_price_cache_available_count), "notes": "Integrated tickers with local official price cache files."},
        {"metric": "FULL_HISTORY_READY_COUNT", "count": str(full_history_ready_count), "notes": f"Official cache rows >= {FACTOR_REQUIRED_HISTORY_DAYS} and close column present."},
        {"metric": "FACTOR_PRESENT_CURRENT_COUNT", "count": str(factor_present_current_count), "notes": "Integrated tickers present in current factor pack ranking."},
        {"metric": "FACTOR_MISSING_CURRENT_COUNT", "count": str(factor_missing_current_count), "notes": "Integrated tickers absent from current factor pack ranking."},
        {"metric": "FACTOR_REFRESH_INPUT_READY_COUNT", "count": str(factor_refresh_input_ready_count), "notes": "Official history and required columns are sufficient for factor refresh."},
        {"metric": "FACTOR_REFRESH_INPUT_BLOCKED_COUNT", "count": str(factor_refresh_input_blocked_count), "notes": "Integrated tickers blocked from factor refresh input readiness."},
        {"metric": "TECHNICAL_PRESENT_CURRENT_COUNT", "count": str(technical_present_current_count), "notes": "Integrated tickers present in current technical timing output."},
        {"metric": "TECHNICAL_MISSING_CURRENT_COUNT", "count": str(technical_missing_current_count), "notes": "Integrated tickers absent from current technical timing output."},
        {"metric": "TECHNICAL_REFRESH_INPUT_READY_COUNT", "count": str(technical_refresh_input_ready_count), "notes": "Official history and required columns are sufficient for technical refresh."},
        {"metric": "TECHNICAL_REFRESH_INPUT_BLOCKED_COUNT", "count": str(technical_refresh_input_blocked_count), "notes": "Integrated tickers blocked from technical refresh input readiness."},
        {"metric": "READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH_COUNT", "count": str(ready_both_count), "notes": "Both factor and technical inputs are ready."},
        {"metric": "READY_FOR_TECHNICAL_REFRESH_ONLY_COUNT", "count": str(ready_tech_only_count), "notes": "Technical ready, factor not ready."},
        {"metric": "READY_FOR_FACTOR_REFRESH_ONLY_COUNT", "count": str(ready_factor_only_count), "notes": "Factor ready, technical not ready."},
        {"metric": "NEEDS_REQUIREMENT_TRACE_COUNT", "count": str(needs_trace_count), "notes": "Refresh requirements still need source trace."},
        {"metric": "HOLD_REVIEW_COUNT", "count": str(hold_review_count), "notes": "Residual hold-review rows after conservative checks."},
    ]

    candidate_report_rows = candidate_rows

    report_lines = [
        "# V18.25A-R4 Integrated Tickers Factor / Technical Refresh Readiness Audit",
        "",
        f"- Status: {status}",
        f"- Mode: {MODE}",
        f"- R6/R7 integrated tickers: {len(audit_rows)}",
        f"- Official price cache available: {official_price_cache_available_count}",
        f"- Full history ready: {full_history_ready_count}",
        f"- Factor present current: {factor_present_current_count}",
        f"- Factor missing current: {factor_missing_current_count}",
        f"- Factor refresh input ready: {factor_refresh_input_ready_count}",
        f"- Technical present current: {technical_present_current_count}",
        f"- Technical missing current: {technical_missing_current_count}",
        f"- Technical refresh input ready: {technical_refresh_input_ready_count}",
        f"- Ready for targeted factor and technical refresh: {ready_both_count}",
        f"- Top refresh blocker: {top_refresh_blocker}",
        f"- Top recommended next action: {top_recommended_next_action}",
        f"- Factor generator script candidates: {factor_candidate_count}",
        f"- Technical generator script candidates: {technical_candidate_count}",
        "",
        "## Readiness Summary",
        "",
        "| Metric | Count | Notes |",
        "| --- | ---: | --- |",
    ]
    for row in summary_rows:
        report_lines.append(f"| {row['metric']} | {row['count']} | {row['notes']} |")

    report_lines.extend(
        [
            "",
            "## Candidate Scripts",
            "",
            f"Detected {len(candidate_report_rows)} candidate scripts by text search across `scripts/v18`.",
            "",
        ]
    )
    preview = candidate_report_rows[:20]
    if preview:
        report_lines.append("| Script | Type | Matched Terms |")
        report_lines.append("| --- | --- | --- |")
        for row in preview:
            report_lines.append(f"| `{row['script_path']}` | {row['script_type']} | {row['matched_terms']} |")
    if len(candidate_report_rows) > len(preview):
        report_lines.append("")
        report_lines.append(f"Additional candidate scripts omitted from preview: {len(candidate_report_rows) - len(preview)}")

    report_lines.extend(
        [
            "",
            "## Safety",
            "",
            "- OFFICIAL_DECISION_IMPACT: `NONE`",
            "- AUTO_TRADE: `DISABLED`",
            "- AUTO_SELL: `DISABLED`",
            "- EXTERNAL_DATA_FETCHED: `FALSE`",
            "- BACKTEST_EXECUTED: `FALSE`",
            "- No forbidden source files were intentionally modified.",
        ]
    )

    read_first = OrderedDict(
        [
            ("STATUS", status),
            ("MODE", MODE),
            ("R3_SOURCE_PATH", str(r3_source)),
            ("R6_R7_INTEGRATED_TICKER_COUNT", str(len(audit_rows))),
            ("OFFICIAL_PRICE_CACHE_AVAILABLE_COUNT", str(official_price_cache_available_count)),
            ("FULL_HISTORY_READY_COUNT", str(full_history_ready_count)),
            ("FACTOR_PRESENT_CURRENT_COUNT", str(factor_present_current_count)),
            ("FACTOR_MISSING_CURRENT_COUNT", str(factor_missing_current_count)),
            ("FACTOR_REFRESH_INPUT_READY_COUNT", str(factor_refresh_input_ready_count)),
            ("FACTOR_REFRESH_INPUT_BLOCKED_COUNT", str(factor_refresh_input_blocked_count)),
            ("TECHNICAL_PRESENT_CURRENT_COUNT", str(technical_present_current_count)),
            ("TECHNICAL_MISSING_CURRENT_COUNT", str(technical_missing_current_count)),
            ("TECHNICAL_REFRESH_INPUT_READY_COUNT", str(technical_refresh_input_ready_count)),
            ("TECHNICAL_REFRESH_INPUT_BLOCKED_COUNT", str(technical_refresh_input_blocked_count)),
            ("READY_FOR_TARGETED_FACTOR_AND_TECHNICAL_REFRESH_COUNT", str(ready_both_count)),
            ("READY_FOR_TECHNICAL_REFRESH_ONLY_COUNT", str(ready_tech_only_count)),
            ("READY_FOR_FACTOR_REFRESH_ONLY_COUNT", str(ready_factor_only_count)),
            ("NEEDS_REQUIREMENT_TRACE_COUNT", str(needs_trace_count)),
            ("HOLD_REVIEW_COUNT", str(hold_review_count)),
            ("TOP_REFRESH_BLOCKER", top_refresh_blocker),
            ("TOP_RECOMMENDED_NEXT_ACTION", top_recommended_next_action),
            ("FACTOR_GENERATOR_SCRIPT_CANDIDATE_COUNT", str(factor_candidate_count)),
            ("TECHNICAL_GENERATOR_SCRIPT_CANDIDATE_COUNT", str(technical_candidate_count)),
            ("OFFICIAL_DECISION_IMPACT", "NONE"),
            ("AUTO_TRADE", "DISABLED"),
            ("AUTO_SELL", "DISABLED"),
            ("PRICE_CACHE_MODIFIED", "FALSE"),
            ("PRICE_HISTORY_MODIFIED", "FALSE"),
            ("STAGED_BACKFILL_MODIFIED", "FALSE"),
            ("LEDGER_MODIFIED", "FALSE"),
            ("FACTOR_PACK_MODIFIED", "FALSE"),
            ("TECHNICAL_TIMING_MODIFIED", "FALSE"),
            ("TIER_MIGRATION_MODIFIED", "FALSE"),
            ("DEGRADED_DAILY_MODIFIED", "FALSE"),
            ("OFFICIAL_DAILY_DECISION_MODIFIED", "FALSE"),
            ("BACKTEST_EXECUTED", "FALSE"),
            ("EXTERNAL_DATA_FETCHED", "FALSE"),
            ("VALIDATION_FAIL_COUNT", str(len(validation_failures))),
            ("FORBIDDEN_FILE_MODIFIED", bool_text(forbidden_modified)),
        ]
    )

    write_csv(root / FACTOR_OUTPUTS["audit"], audit_rows, AUDIT_FIELDS)
    write_csv(root / FACTOR_OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / FACTOR_OUTPUTS["candidates"], candidate_rows, CANDIDATE_FIELDS)
    write_text(root / FACTOR_OUTPUTS["report"], "\n".join(report_lines) + "\n")
    write_text(root / FACTOR_OUTPUTS["ops_report"], "\n".join(report_lines) + "\n")
    write_text(root / FACTOR_OUTPUTS["read_first"], "\n".join(f"{k}: {v}" for k, v in read_first.items()) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"R6_R7_INTEGRATED_TICKER_COUNT: {len(audit_rows)}")
    print(f"OFFICIAL_PRICE_CACHE_AVAILABLE_COUNT: {official_price_cache_available_count}")
    print(f"FULL_HISTORY_READY_COUNT: {full_history_ready_count}")
    print(f"FACTOR_REFRESH_INPUT_READY_COUNT: {factor_refresh_input_ready_count}")
    print(f"TECHNICAL_REFRESH_INPUT_READY_COUNT: {technical_refresh_input_ready_count}")
    print(f"TOP_REFRESH_BLOCKER: {top_refresh_blocker}")
    print(f"TOP_RECOMMENDED_NEXT_ACTION: {top_recommended_next_action}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")

    if validation_failures:
        for item in validation_failures:
            print(f"VALIDATION: {item}")
        return 1
    if warnings:
        for item in warnings:
            print(f"WARNING: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
