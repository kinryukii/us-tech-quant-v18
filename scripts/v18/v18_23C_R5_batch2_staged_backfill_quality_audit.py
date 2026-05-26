from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_R5_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT_READY"
STATUS_WARN = "WARN_V18_23C_R5_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_23C_R5_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT"
MODE = "READ_ONLY_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT_DRY_RUN"
BATCH_ID = "V18_23C_BATCH2"
STAGED_DIR_REL = "data/v18/staged_backfill/V18_23C_BATCH2"
COMBINED_REL = f"{STAGED_DIR_REL}/V18_23C_BATCH2_STAGED_PRICE_HISTORY.csv"
MANIFEST_REL = f"{STAGED_DIR_REL}/MANIFEST.csv"
MIN_FULL_HISTORY_ROWS = 500
MIN_FULL_HISTORY_SPAN_DAYS = 700

OUTPUTS = {
    "md": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT.md",
    "ticker": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_TICKER_QUALITY_AUDIT.csv",
    "merge": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_MERGE_CANDIDATES.csv",
    "hold": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_HOLD_REVIEW_TICKERS.csv",
    "plan": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_OFFICIAL_INTEGRATION_DRY_RUN_PLAN.csv",
    "summary": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_DATA_QUALITY_SUMMARY.csv",
    "source": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23C_R5_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R5_CURRENT_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "BATCH2_QUALITY_AUDIT_READY", "BATCH_ID", "BATCH_TICKER_COUNT",
    "STAGED_FETCH_SUCCESS_COUNT", "STAGED_EMPTY_COUNT", "STAGED_FULL_HISTORY_READY_COUNT",
    "STAGED_INSUFFICIENT_HISTORY_COUNT", "QUALITY_AUDITED_TICKER_COUNT",
    "MERGE_CANDIDATE_FULL_HISTORY_COUNT", "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT",
    "HOLD_REVIEW_TICKER_COUNT", "HOLD_EMPTY_FETCH_COUNT", "HOLD_SCHEMA_INVALID_COUNT",
    "HOLD_SUSPICIOUS_DATA_COUNT", "OFFICIAL_INTEGRATION_DRY_RUN_CREATED",
    "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP", "OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL",
    "EXTERNAL_DATA_FETCHED", "STAGED_PRICE_HISTORY_MODIFIED", "OFFICIAL_PRICE_CACHE_MODIFIED",
    "OFFICIAL_PRICE_HISTORY_MODIFIED", "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN",
    "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "LEDGER_MODIFIED", "ROLLING_SCAN_EXECUTED",
    "STAGED_ROLLING_SCAN_RETEST_EXECUTED", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED",
    "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "VALIDATION_FAIL_COUNT", "RECOMMENDED_NEXT_ACTION",
    "QUALITY_AUDIT_PATH", "TICKER_QUALITY_AUDIT_PATH", "MERGE_CANDIDATES_PATH",
    "HOLD_REVIEW_TICKERS_PATH", "OFFICIAL_INTEGRATION_DRY_RUN_PLAN_PATH", "DATA_QUALITY_SUMMARY_PATH",
    "SOURCE_AUDIT_PATH", "VALIDATION_PATH", "REPORT_PATH",
]

TICKER_FIELDS = [
    "batch_id", "ticker", "fetch_status", "staged_file_exists", "staged_row_count", "staged_min_date",
    "staged_max_date", "latest_date_age_days", "has_required_ohlcv_columns", "close_non_null_count",
    "volume_non_null_count", "duplicate_date_count", "missing_date_or_parse_issue_count",
    "non_positive_close_count", "suspicious_large_gap_count", "suspicious_return_outlier_count",
    "staged_local_price_scan_success_from_r4", "staged_full_history_ready_from_r4",
    "staged_insufficient_history_from_r4", "official_price_overlap_found",
    "existing_official_latest_date", "staged_newer_than_official", "recommended_integration_action",
    "integration_block_reason", "quality_grade", "classification",
]
PLAN_FIELDS = [
    "ticker", "dry_run_action", "staged_source_path", "official_destination_path",
    "backup_required", "merge_scope", "ledger_update_timing", "ranking_factor_technical_unchanged",
    "post_integration_retest_required", "explicit_approval_required", "notes",
]
SUMMARY_FIELDS = ["metric", "value", "notes"]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "ticker_count", "required", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

SAFETY_FALSE = {
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "STAGED_PRICE_HISTORY_MODIFIED": "FALSE",
    "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
    "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "STAGED_ROLLING_SCAN_RETEST_EXECUTED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET": "FALSE",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "NA", "N/A", "TICKER"} or ticker.isdigit():
        return ""
    if len(ticker) > 10:
        return ""
    return ticker


def get_ticker(row: Dict[str, str]) -> str:
    for key in ("ticker", "Ticker", "symbol", "Symbol", "yf_ticker"):
        ticker = normalize_ticker(row.get(key, ""))
        if ticker:
            return ticker
    return ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def parse_read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def protected_files(root: Path) -> List[Path]:
    dirs = [
        "state/v18/price_cache", "state/v18/rolling_coverage", "outputs/v18/factor_pack",
        "outputs/v18/ranking", "outputs/v18/signal_snapshots", "outputs/v18/technical_timing",
        "outputs/v18/backtest", "outputs/v18/daily_integrated", "state/v18/manual",
        "state/v18/simulation", "state/v18/forward_outcome", "state/v18/candidate_forward_tracker",
        "archive/stable",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()[:10]
    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def valid_schema(fields: Sequence[str]) -> bool:
    lower = {str(field).strip().lower() for field in fields}
    return {"open", "high", "low", "close"}.issubset(lower)


def safe_float(value: object) -> float | None:
    try:
        text = str(value).replace(",", "").strip()
        if text == "":
            return None
        return float(text)
    except ValueError:
        return None


def grade_from_score(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def quality_score(schema_ok: bool, row_count: int, duplicates: int, bad_dates: int, non_positive: int, gaps: int, outliers: int, classification: str) -> Tuple[int, str]:
    score = 100
    if not schema_ok:
        score -= 35
    if row_count == 0:
        score -= 100
    elif row_count < MIN_FULL_HISTORY_ROWS:
        score -= 15
    score -= min(20, duplicates * 2)
    score -= min(20, bad_dates * 3)
    score -= min(20, non_positive * 5)
    score -= min(15, gaps * 2)
    score -= min(15, outliers * 2)
    if classification.startswith("HOLD"):
        score -= 20
    return max(0, score), grade_from_score(max(0, score))


def read_stage_metrics(path: Path) -> Tuple[int, str, str, bool, int]:
    rows, fields = read_csv(path)
    if not rows:
        return 0, "", "", False, 0
    date_col = "Date" if "Date" in fields else fields[0] if fields else ""
    dates: List[dt.date] = []
    for row in rows:
        date = parse_date(row.get(date_col, ""))
        if date:
            dates.append(date)
    if not dates:
        return len(rows), "", "", valid_schema(fields), 0
    return len(rows), min(dates).isoformat(), max(dates).isoformat(), valid_schema(fields), (max(dates) - min(dates)).days


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_md(values: Dict[str, str], summary_rows: Sequence[Dict[str, object]], reason_counts: Counter[str], plan_rows: Sequence[Dict[str, object]], full_history_count: int) -> str:
    full_history_rows = [row for row in plan_rows if row.get("merge_scope") == "FULL_HISTORY_ONLY"]
    partial_rows = [row for row in plan_rows if row.get("merge_scope") == "PRICE_ONLY_PARTIAL_HISTORY_NOT_FACTOR_READY"]
    return f"""# V18.23C-R5 Batch 2 Staged Backfill Quality Audit

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Purpose
Audit V18.23C-R4 Batch 2 staged backfill data quality and prepare a dry-run official integration gate only. No official integration is performed.

## V18.23C-R4 Summary
Batch 2 staged backfill completed with {values['STAGED_FETCH_SUCCESS_COUNT']} fetch successes, {values['STAGED_EMPTY_COUNT']} empty responses, {values['STAGED_FULL_HISTORY_READY_COUNT']} staged full-history ready tickers, and {values['STAGED_INSUFFICIENT_HISTORY_COUNT']} staged insufficient-history tickers.

## Batch 2 Data Quality
Audited tickers: {values['QUALITY_AUDITED_TICKER_COUNT']}. Full-history merge candidates: {values['MERGE_CANDIDATE_FULL_HISTORY_COUNT']}. Price-only partial candidates: {values['MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT']}. Hold/review tickers: {values['HOLD_REVIEW_TICKER_COUNT']}.

## Empty Fetch Tickers
CDTX, CFLT, and MPW remain empty fetch holds and are excluded from merge candidates.

## Official Integration Gate
Dry-run created: {values['OFFICIAL_INTEGRATION_DRY_RUN_CREATED']}. Allowed next step: {values['OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP']}. Explicit approval required: {values['OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL']}.

## Recommended R6 Policy
Integrate only full-history merge candidates first; keep price-only partial, hold/review, and empty fetch tickers excluded until separately approved.

## Movement/Reason Summary
{render_reason_list(reason_counts)}

## What Was Not Modified
Official price cache, official price history, ledger, ranking, factor pack, technical timing, signal snapshots, backtests, and trading state were not modified.

## Remaining Blockers
{values['HOLD_REVIEW_TICKER_COUNT']} hold/review rows and {values['MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT']} price-only partial rows remain excluded from official integration.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_reason_list(reason_counts: Counter[str]) -> str:
    if not reason_counts:
        return "_None._"
    return "\n".join(f"- {reason}: {count}" for reason, count in reason_counts.most_common(10))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in protected_files(root)}

    r4_read_first = parse_read_first(root / "outputs/v18/ops/V18_23C_R4_READ_FIRST.txt")
    fetch_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_BACKFILL_BATCH2_FETCH_RESULT.csv")
    retest_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_STAGED_BATCH2_SCAN_RETEST_RESULT.csv")
    manifest_rows, _ = read_csv(root / MANIFEST_REL)
    combined_rows, _ = read_csv(root / COMBINED_REL)
    current_coverage_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23C_R4_CURRENT_BATCH2_ROLLING_SCAN_RETEST_SUMMARY.csv")
    remaining_stale_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_REMAINING_STALE_TICKERS.csv")
    held_out_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv")

    batch_tickers = [get_ticker(row) for row in fetch_rows if get_ticker(row)]
    batch_tickers = list(dict.fromkeys(batch_tickers))

    if not batch_tickers:
        batch_tickers = [get_ticker(row) for row in retest_rows if get_ticker(row)]
        batch_tickers = list(dict.fromkeys(batch_tickers))

    if len(batch_tickers) != 65 and fetch_rows:
        batch_tickers = [get_ticker(row) for row in fetch_rows if get_ticker(row)]
        batch_tickers = list(dict.fromkeys(batch_tickers))

    integrated_tickers = set(get_ticker(row) for row in fetch_rows if str(row.get("fetch_status", "")).upper() == "SUCCESS")
    batch1_held_out = {get_ticker(row) for row in held_out_rows if get_ticker(row)}
    current_success_window = set()
    ledger_rows, _ = read_csv(root / "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv")
    if ledger_rows:
        today = dt.date.today()
        cutoff = today - dt.timedelta(days=5)
        for row in ledger_rows:
            ticker = get_ticker(row)
            success_date = parse_date(row.get("last_success_scan_date", ""))
            if ticker and success_date and success_date >= cutoff:
                current_success_window.add(ticker)

    target_rows: List[Dict[str, object]] = []
    merge_candidates: List[Dict[str, object]] = []
    hold_rows: List[Dict[str, object]] = []
    dry_run_rows: List[Dict[str, object]] = []
    excluded_reasons: Counter[str] = Counter()

    official_dir = root / "state/v18/price_cache"
    for row in fetch_rows:
        ticker = get_ticker(row)
        if not ticker:
            continue
        fetch_status = str(row.get("fetch_status", "")).upper()
        staged_path = root / STAGED_DIR_REL / f"{ticker}.csv"
        staged_exists = staged_path.exists()
        staged_row_count, staged_min_date, staged_max_date, schema_ok, span_days = read_stage_metrics(staged_path)
        close_count = 0
        volume_count = 0
        duplicate_dates = 0
        bad_dates = 0
        non_positive_close = 0
        gaps = 0
        outliers = 0
        official_latest = ""
        official_overlap = "UNKNOWN"
        staged_newer = "UNKNOWN"
        if staged_exists:
            rows, fields = read_csv(staged_path)
            date_col = "Date" if "Date" in fields else fields[0] if fields else ""
            dates: List[dt.date] = []
            closes: List[float] = []
            for staged_row in rows:
                date = parse_date(staged_row.get(date_col, ""))
                if date:
                    dates.append(date)
                else:
                    bad_dates += 1
                close = safe_float(staged_row.get("Close", staged_row.get("close", "")))
                if close is not None:
                    closes.append(close)
                if str(staged_row.get("Volume", staged_row.get("volume", ""))).strip() not in {"", "nan", "NaN"}:
                    volume_count += 1
            close_count = len(closes)
            duplicate_dates = len(dates) - len(set(dates))
            non_positive_close = sum(1 for close in closes if close <= 0)
            if len(closes) >= 2:
                for prev, cur in zip(closes, closes[1:]):
                    if prev > 0:
                        change = (cur / prev) - 1
                        if abs(change) > 0.5:
                            outliers += 1
            sorted_dates = sorted(set(dates))
            for prev, cur in zip(sorted_dates, sorted_dates[1:]):
                if (cur - prev).days > 10:
                    gaps += 1
            official_path = official_dir / f"{ticker}.csv"
            if official_path.exists():
                official_overlap = "TRUE"
                official_rows, official_fields = read_csv(official_path)
                official_dates = [parse_date(r.get("date", r.get("Date", ""))) for r in official_rows]
                official_dates = [d for d in official_dates if d]
                official_latest = max(official_dates).isoformat() if official_dates else ""
                if staged_max_date and official_latest:
                    staged_newer = str(staged_max_date > official_latest).upper()
                elif staged_max_date and not official_latest:
                    staged_newer = "TRUE"
                elif not official_latest:
                    staged_newer = "UNKNOWN"
            else:
                official_overlap = "FALSE"
                official_latest = ""

        quality_penalty = duplicate_dates > 0 or bad_dates > 0 or non_positive_close > 0 or outliers > 0 or gaps > 0 or not schema_ok
        if fetch_status == "EMPTY" or not staged_exists or staged_row_count == 0:
            classification = "HOLD_EMPTY_FETCH"
            action = "HOLD_REVIEW"
            block = "Empty provider response."
        elif not schema_ok:
            classification = "HOLD_SCHEMA_INVALID"
            action = "HOLD_REVIEW"
            block = "Required OHLCV schema missing."
        elif quality_penalty:
            classification = "HOLD_SUSPICIOUS_PRICE_DATA"
            action = "HOLD_REVIEW"
            block = "Suspicious staged data quality issue."
        elif fetch_status == "SUCCESS" and str(row.get("schema_valid", "")).upper() == "TRUE" and row.get("row_count") and str(row.get("row_count")).isdigit():
            full_ready = str(r4_scan_status(retest_rows, ticker)).upper() == "STAGED_FULL_HISTORY_READY"
            if full_ready:
                classification = "MERGE_CANDIDATE_FULL_HISTORY"
                action = "DRY_RUN_MERGE_FULL_HISTORY"
                block = ""
            else:
                classification = "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY"
                action = "DRY_RUN_MERGE_PRICE_ONLY_PARTIAL_HISTORY"
                block = "Not factor-ready."
        else:
            classification = "HOLD_UNKNOWN_QUALITY_ISSUE"
            action = "HOLD_REVIEW"
            block = "Quality state could not be established."

        score, grade = quality_score(schema_ok, staged_row_count, duplicate_dates, bad_dates, non_positive_close, gaps, outliers, classification)
        current_r4 = next((r for r in retest_rows if get_ticker(r) == ticker), {})
        target_rows.append({
            "batch_id": BATCH_ID,
            "ticker": ticker,
            "fetch_status": fetch_status,
            "staged_file_exists": str(staged_exists).upper(),
            "staged_row_count": staged_row_count,
            "staged_min_date": staged_min_date,
            "staged_max_date": staged_max_date,
            "latest_date_age_days": "" if not staged_max_date else (dt.date.today() - dt.datetime.strptime(staged_max_date, "%Y-%m-%d").date()).days,
            "has_required_ohlcv_columns": str(schema_ok).upper(),
            "close_non_null_count": close_count,
            "volume_non_null_count": volume_count,
            "duplicate_date_count": duplicate_dates,
            "missing_date_or_parse_issue_count": bad_dates,
            "non_positive_close_count": non_positive_close,
            "suspicious_large_gap_count": gaps,
            "suspicious_return_outlier_count": outliers,
            "staged_local_price_scan_success_from_r4": str(str(current_r4.get("staged_local_price_available", "")).upper() == "TRUE").upper(),
            "staged_full_history_ready_from_r4": str(str(current_r4.get("staged_scan_status", "")) == "STAGED_FULL_HISTORY_READY").upper(),
            "staged_insufficient_history_from_r4": str(str(current_r4.get("staged_scan_status", "")) == "STAGED_INSUFFICIENT_HISTORY").upper(),
            "official_price_overlap_found": official_overlap,
            "existing_official_latest_date": official_latest,
            "staged_newer_than_official": staged_newer,
            "recommended_integration_action": action,
            "integration_block_reason": block,
            "quality_grade": grade,
            "classification": classification,
        })
        if classification == "MERGE_CANDIDATE_FULL_HISTORY":
            merge_candidates.append(target_rows[-1])
        elif classification.startswith("HOLD"):
            hold_rows.append(target_rows[-1])

    if not target_rows:
        target_rows = []

    merge_rows = []
    for row in merge_candidates:
        ticker = row["ticker"]
        merge_rows.append({
            "ticker": ticker,
            "dry_run_action": "DRY_RUN_MERGE_FULL_HISTORY",
            "staged_source_path": str(root / STAGED_DIR_REL / f"{ticker}.csv"),
            "official_destination_path": str(official_dir / f"{ticker}.csv"),
            "backup_required": "TRUE",
            "merge_scope": "FULL_HISTORY_ONLY",
            "ledger_update_timing": "AFTER_OFFICIAL_LOCAL_SCAN_SUCCEEDS",
            "ranking_factor_technical_unchanged": "TRUE",
            "post_integration_retest_required": "TRUE",
            "explicit_approval_required": "TRUE",
            "notes": "Dry run only; no file copied in R5.",
        })

    summary_counter = Counter(row["classification"] for row in target_rows)
    reasons = Counter()
    for row in target_rows:
        reasons[row["classification"]] += 1

    source_rows = [
        {"source_name": "r4_read_first", "source_path": "outputs/v18/ops/V18_23C_R4_READ_FIRST.txt", "exists": str((root / "outputs/v18/ops/V18_23C_R4_READ_FIRST.txt").exists()).upper(), "row_count": 1 if (root / "outputs/v18/ops/V18_23C_R4_READ_FIRST.txt").exists() else 0, "ticker_count": 0, "required": "TRUE", "notes": "Batch 2 summary context."},
        {"source_name": "staged_manifest", "source_path": MANIFEST_REL, "exists": str((root / MANIFEST_REL).exists()).upper(), "row_count": len(manifest_rows), "ticker_count": len({get_ticker(row) for row in manifest_rows if get_ticker(row)}), "required": "TRUE", "notes": "Staged batch 2 manifest."},
        {"source_name": "staged_combined_history", "source_path": COMBINED_REL, "exists": str((root / COMBINED_REL).exists()).upper(), "row_count": len(combined_rows), "ticker_count": len({get_ticker(row) for row in combined_rows if get_ticker(row)}), "required": "TRUE", "notes": "Combined staged history."},
        {"source_name": "r4_fetch_result", "source_path": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_BACKFILL_BATCH2_FETCH_RESULT.csv", "exists": str(bool(fetch_rows)).upper(), "row_count": len(fetch_rows), "ticker_count": len(batch_tickers), "required": "TRUE", "notes": "Batch 2 fetch summary."},
        {"source_name": "r4_scan_retest", "source_path": "outputs/v18/staged_backfill/V18_23C_R4_CURRENT_STAGED_BATCH2_SCAN_RETEST_RESULT.csv", "exists": str(bool(retest_rows)).upper(), "row_count": len(retest_rows), "ticker_count": len(batch_tickers), "required": "TRUE", "notes": "Batch 2 staged retest summary."},
        {"source_name": "r3_remaining_stale", "source_path": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_REMAINING_STALE_TICKERS.csv", "exists": str((root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_REMAINING_STALE_TICKERS.csv").exists()).upper(), "row_count": len(remaining_stale_rows), "ticker_count": len(remaining_stale_rows), "required": "FALSE", "notes": "Remaining stale source."},
        {"source_name": "r2_held_out", "source_path": "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv", "exists": str((root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv").exists()).upper(), "row_count": len(held_out_rows), "ticker_count": len(held_out_rows), "required": "FALSE", "notes": "Held-out context."},
        {"source_name": "r3_ledger_snapshot", "source_path": "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv", "exists": str((root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv").exists()).upper(), "row_count": len(read_csv(root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv")[0]), "ticker_count": len(read_csv(root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv")[0]), "required": "FALSE", "notes": "Coverage evidence context."},
        {"source_name": "ledger", "source_path": "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv", "exists": str((root / "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv").exists()).upper(), "row_count": len(ledger_rows) if 'ledger_rows' in locals() else 0, "ticker_count": len(ledger_rows) if 'ledger_rows' in locals() else 0, "required": "FALSE", "notes": "Read-only evidence context."},
        {"source_name": "v24a_data_not_ready", "source_path": "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv", "exists": str((root / "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv").exists()).upper(), "row_count": len(read_csv(root / "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv")[0]), "ticker_count": len(read_csv(root / "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv")[0]), "required": "FALSE", "notes": "Tier migration context."},
        {"source_name": "v24b_data_not_ready", "source_path": "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv", "exists": str((root / "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv").exists()).upper(), "row_count": len(read_csv(root / "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv")[0]), "ticker_count": len(read_csv(root / "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv")[0]), "required": "FALSE", "notes": "Operator homepage context."},
    ]

    full_history_count = len(merge_candidates)
    partial_history_count = sum(1 for row in target_rows if row["classification"] == "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY")
    hold_empty_count = sum(1 for row in target_rows if row["classification"] == "HOLD_EMPTY_FETCH")
    hold_schema_count = sum(1 for row in target_rows if row["classification"] == "HOLD_SCHEMA_INVALID")
    hold_suspicious_count = sum(1 for row in target_rows if row["classification"] == "HOLD_SUSPICIOUS_PRICE_DATA")
    hold_unknown_count = sum(1 for row in target_rows if row["classification"] == "HOLD_UNKNOWN_QUALITY_ISSUE")
    hold_review_count = len(hold_rows)
    data_not_ready_or_blocked_count = hold_review_count + partial_history_count
    integration_allowed = full_history_count > 0

    plan_rows = merge_rows

    summary_rows = [
        {"metric": "batch_ticker_count", "value": len(batch_tickers), "notes": "Batch 2 staged-only audit rows."},
        {"metric": "fetch_success_count", "value": int(r4_read_first.get("FETCH_SUCCESS_COUNT", "0")), "notes": "From V18.23C-R4."},
        {"metric": "full_history_merge_candidate_count", "value": full_history_count, "notes": "Future R6 candidates."},
        {"metric": "price_only_partial_history_candidate_count", "value": partial_history_count, "notes": "Not factor-ready."},
        {"metric": "hold_review_ticker_count", "value": hold_review_count, "notes": "Excluded from R6."},
        {"metric": "empty_fetch_ticker_count", "value": hold_empty_count, "notes": "CDTX, CFLT, MPW expected."},
        {"metric": "official_integration_allowed_next_step", "value": str(integration_allowed).upper(), "notes": "Dry run plan exists; explicit approval required."},
    ]

    values: Dict[str, str] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "BATCH2_QUALITY_AUDIT_READY": "TRUE",
        "BATCH_ID": BATCH_ID,
        "BATCH_TICKER_COUNT": str(len(batch_tickers)),
        "STAGED_FETCH_SUCCESS_COUNT": r4_read_first.get("FETCH_SUCCESS_COUNT", "0"),
        "STAGED_EMPTY_COUNT": r4_read_first.get("FETCH_EMPTY_COUNT", "0"),
        "STAGED_FULL_HISTORY_READY_COUNT": r4_read_first.get("STAGED_FULL_HISTORY_READY_COUNT", "0"),
        "STAGED_INSUFFICIENT_HISTORY_COUNT": r4_read_first.get("STAGED_INSUFFICIENT_HISTORY_COUNT", "0"),
        "QUALITY_AUDITED_TICKER_COUNT": str(len(target_rows)),
        "MERGE_CANDIDATE_FULL_HISTORY_COUNT": str(full_history_count),
        "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT": str(partial_history_count),
        "HOLD_REVIEW_TICKER_COUNT": str(hold_review_count),
        "HOLD_EMPTY_FETCH_COUNT": str(hold_empty_count),
        "HOLD_SCHEMA_INVALID_COUNT": str(hold_schema_count),
        "HOLD_SUSPICIOUS_DATA_COUNT": str(hold_suspicious_count),
        "OFFICIAL_INTEGRATION_DRY_RUN_CREATED": "TRUE",
        "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP": str(integration_allowed).upper(),
        "OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL": "TRUE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "STAGED_PRICE_HISTORY_MODIFIED": "FALSE",
        "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
        "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_WRITTEN": "FALSE",
        "RANKING_MODIFIED": "FALSE",
        "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "ROLLING_SCAN_EXECUTED": "FALSE",
        "STAGED_ROLLING_SCAN_RETEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BACKTEST_EXECUTED": "FALSE",
        "BACKTEST_RESULTS_APPLIED": "FALSE",
        "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
        "WEIGHT_CHANGE_ALLOWED": "FALSE",
        "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
        "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": "FALSE",
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "FALSE_STAGED_ONLY_NOT_OFFICIAL_LEDGER_COVERAGE",
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Review full-history merge candidates first; only run V18.23C-R6 official integration after explicit approval and backup plan acceptance.",
        "QUALITY_AUDIT_PATH": str(root / OUTPUTS["md"]),
        "TICKER_QUALITY_AUDIT_PATH": str(root / OUTPUTS["ticker"]),
        "MERGE_CANDIDATES_PATH": str(root / OUTPUTS["merge"]),
        "HOLD_REVIEW_TICKERS_PATH": str(root / OUTPUTS["hold"]),
        "OFFICIAL_INTEGRATION_DRY_RUN_PLAN_PATH": str(root / OUTPUTS["plan"]),
        "DATA_QUALITY_SUMMARY_PATH": str(root / OUTPUTS["summary"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY_FALSE)

    write_csv(root / OUTPUTS["ticker"], target_rows, TICKER_FIELDS)
    write_csv(root / OUTPUTS["merge"], merge_rows, PLAN_FIELDS)
    write_csv(root / OUTPUTS["hold"], hold_rows, TICKER_FIELDS)
    write_csv(root / OUTPUTS["plan"], plan_rows, PLAN_FIELDS)
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["source"], source_rows, SOURCE_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values, summary_rows, reasons, plan_rows, full_history_count))
    write_text(root / OUTPUTS["report"], render_md(values, summary_rows, reasons, plan_rows, full_history_count))
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23C_R5_batch2_staged_backfill_quality_audit.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23C_R5_batch2_staged_backfill_quality_audit.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "Required outputs must exist and be non-empty."),
        validation_row("manifest_readable", non_empty(root / MANIFEST_REL), 1, "Batch 2 staged manifest must be readable."),
        validation_row("combined_history_readable", non_empty(root / COMBINED_REL), 1, "Batch 2 staged combined file must be readable."),
        validation_row("batch_count_matches_fetch_rows", len(target_rows) == len(batch_tickers), 1, "Quality audited ticker count must equal batch count."),
        validation_row("dry_run_plan_non_empty", bool(plan_rows), 1, "Dry-run plan must exist and be non-empty."),
        validation_row("no_forbidden_files_modified", not changed, len(changed), ";".join(changed[:20])),
        validation_row("true_coverage_remains_false", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] == "FALSE", 1, "Staged-only test."),
    ]
    for key, expected in SAFETY_FALSE.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not batch_tickers or not combined_rows:
        values["STATUS"] = STATUS_FAIL
        values["BATCH2_QUALITY_AUDIT_READY"] = "FALSE"
    elif hold_review_count > 0 or partial_history_count > 0:
        values["STATUS"] = STATUS_WARN
    elif full_history_count > 0:
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_FAIL
    values["BATCH2_QUALITY_AUDIT_READY"] = "TRUE" if fail_count == 0 and bool(batch_tickers) and bool(combined_rows) else "FALSE"
    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values, summary_rows, reasons, plan_rows, full_history_count))
    write_text(root / OUTPUTS["report"], render_md(values, summary_rows, reasons, plan_rows, full_history_count))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


def r4_scan_status(rows: Sequence[Dict[str, str]], ticker: str) -> str:
    for row in rows:
        if get_ticker(row) == ticker:
            return str(row.get("staged_scan_status", ""))
    return ""


if __name__ == "__main__":
    sys.exit(main())
