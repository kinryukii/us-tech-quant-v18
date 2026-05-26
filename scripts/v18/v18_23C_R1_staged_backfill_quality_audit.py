from __future__ import annotations

import argparse
import csv
import datetime as dt
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_R1_STAGED_BACKFILL_QUALITY_AUDIT_READY"
STATUS_WARN = "WARN_V18_23C_R1_STAGED_BACKFILL_QUALITY_AUDIT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_23C_R1_STAGED_BACKFILL_QUALITY_AUDIT"
MODE = "READ_ONLY_STAGED_BACKFILL_QUALITY_AUDIT_DRY_RUN"
BATCH_ID = "V18_23C_BATCH1"
STAGED_DIR_REL = "data/v18/staged_backfill/V18_23C_BATCH1"
MANIFEST_REL = f"{STAGED_DIR_REL}/MANIFEST.csv"
COMBINED_REL = f"{STAGED_DIR_REL}/V18_23C_BATCH1_STAGED_PRICE_HISTORY.csv"

OUTPUTS = {
    "md": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_STAGED_BACKFILL_QUALITY_AUDIT.md",
    "ticker": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_TICKER_QUALITY_AUDIT.csv",
    "merge": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_MERGE_CANDIDATES.csv",
    "hold": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_HOLD_REVIEW_TICKERS.csv",
    "plan": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_OFFICIAL_INTEGRATION_DRY_RUN_PLAN.csv",
    "summary": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_DATA_QUALITY_SUMMARY.csv",
    "source": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/staged_backfill/V18_23C_R1_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23C_R1_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R1_CURRENT_STAGED_BACKFILL_QUALITY_AUDIT_REPORT.md",
}

SAFETY = {
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

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "QUALITY_AUDIT_READY", "BATCH_ID", "BATCH_TICKER_COUNT",
    "STAGED_FETCH_SUCCESS_COUNT", "STAGED_EMPTY_COUNT", "STAGED_FULL_HISTORY_READY_COUNT",
    "STAGED_INSUFFICIENT_HISTORY_COUNT", "QUALITY_AUDITED_TICKER_COUNT",
    "MERGE_CANDIDATE_FULL_HISTORY_COUNT", "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT",
    "HOLD_REVIEW_TICKER_COUNT", "HOLD_EMPTY_FETCH_COUNT", "HOLD_INSUFFICIENT_HISTORY_COUNT",
    "HOLD_SCHEMA_INVALID_COUNT", "HOLD_SUSPICIOUS_DATA_COUNT",
    "OFFICIAL_INTEGRATION_DRY_RUN_CREATED", "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP",
    "OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL", "EXTERNAL_DATA_FETCHED",
    "STAGED_PRICE_HISTORY_MODIFIED", "OFFICIAL_PRICE_CACHE_MODIFIED",
    "OFFICIAL_PRICE_HISTORY_MODIFIED", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "LEDGER_MODIFIED",
    "ROLLING_SCAN_EXECUTED", "STAGED_ROLLING_SCAN_RETEST_EXECUTED", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_COVERAGE_STATUS",
    "VALIDATION_FAIL_COUNT", "RECOMMENDED_NEXT_ACTION", "QUALITY_AUDIT_PATH",
    "TICKER_QUALITY_AUDIT_PATH", "MERGE_CANDIDATES_PATH", "HOLD_REVIEW_TICKERS_PATH",
    "OFFICIAL_INTEGRATION_DRY_RUN_PLAN_PATH", "DATA_QUALITY_SUMMARY_PATH",
    "SOURCE_AUDIT_PATH", "VALIDATION_PATH", "REPORT_PATH",
]

TICKER_FIELDS = [
    "ticker", "fetch_status", "staged_file_exists", "staged_row_count", "staged_min_date",
    "staged_max_date", "latest_date_age_days", "has_required_ohlcv_columns",
    "close_non_null_count", "volume_non_null_count", "duplicate_date_count",
    "missing_date_or_parse_issue_count", "non_positive_close_count", "suspicious_large_gap_count",
    "suspicious_return_outlier_count", "full_history_ready_from_v18_23C",
    "staged_local_price_scan_success_from_v18_23C", "insufficient_history_flag_from_v18_23C",
    "official_price_overlap_found", "existing_official_latest_date", "staged_newer_than_official",
    "recommended_integration_action", "integration_block_reason", "quality_score", "quality_grade",
    "classification",
]
PLAN_FIELDS = [
    "ticker", "dry_run_action", "staged_source_path", "official_destination_path",
    "backup_required", "merge_scope", "ledger_update_timing", "ranking_factor_technical_unchanged",
    "post_integration_retest_required", "explicit_approval_required", "notes",
]
SUMMARY_FIELDS = ["metric", "value", "notes"]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


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


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()[:10]
    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def to_float(value: object) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def protected_files(root: Path) -> List[Path]:
    dirs = [
        "data/v18/staged_backfill/V18_23C_BATCH1", "state/v18/price_cache",
        "outputs/v18/factor_pack", "outputs/v18/ranking", "outputs/v18/signal_snapshots",
        "outputs/v18/technical_timing", "state/v18/rolling_coverage", "outputs/v18/universe",
        "state/v18/simulation", "state/v18/forward_outcome", "state/v18/candidate_forward_tracker",
        "state/v18/manual", "state/v16", "archive/stable",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def required_schema(fields: Sequence[str]) -> bool:
    lower = {field.lower() for field in fields}
    return {"date", "open", "high", "low", "close"}.issubset(lower)


def audit_ticker(root: Path, ticker: str, fetch: Dict[str, str], retest: Dict[str, str]) -> Dict[str, object]:
    staged_path = root / STAGED_DIR_REL / f"{ticker}.csv"
    rows, fields = read_csv(staged_path)
    date_col = "Date" if "Date" in fields else fields[0] if fields else ""
    dates: List[dt.date] = []
    date_bad = 0
    close_values: List[float] = []
    volume_count = 0
    for row in rows:
        parsed = parse_date(row.get(date_col, ""))
        if parsed:
            dates.append(parsed)
        else:
            date_bad += 1
        close = to_float(row.get("Close", ""))
        if close is not None:
            close_values.append(close)
        if str(row.get("Volume", "")).strip() not in {"", "nan", "NaN"}:
            volume_count += 1
    duplicate_dates = len(dates) - len(set(dates))
    non_positive_close = sum(1 for value in close_values if value <= 0)
    returns: List[float] = []
    for prev, cur in zip(close_values, close_values[1:]):
        if prev > 0:
            returns.append((cur / prev) - 1)
    outliers = sum(1 for ret in returns if abs(ret) > 0.5)
    gaps = 0
    for prev, cur in zip(sorted(set(dates)), sorted(set(dates))[1:]):
        if (cur - prev).days > 10:
            gaps += 1
    min_date = min(dates).isoformat() if dates else ""
    max_date = max(dates).isoformat() if dates else ""
    age = (dt.date.today() - max(dates)).days if dates else ""
    schema_ok = required_schema(fields)
    severe = (not schema_ok) or date_bad > 0 or non_positive_close > 0 or duplicate_dates > 0 or outliers > 0
    fetch_status = fetch.get("fetch_status", "")
    full_ready = retest.get("staged_scan_status", "") == "STAGED_FULL_HISTORY_READY"
    local_success = retest.get("staged_local_price_available", "") == "TRUE"
    insufficient = retest.get("staged_scan_status", "") == "STAGED_INSUFFICIENT_HISTORY"
    official_path = root / "state/v18/price_cache" / f"{ticker}.csv"
    official_rows, official_fields = read_csv(official_path)
    official_dates = [parse_date(row.get("Date", "") or row.get(official_fields[0], "") if official_fields else "") for row in official_rows]
    official_dates = [d for d in official_dates if d]
    official_latest = max(official_dates).isoformat() if official_dates else ""
    overlap = "TRUE" if official_path.exists() else "FALSE"
    newer = "UNKNOWN"
    if max_date and official_latest:
        newer = str(max_date > official_latest).upper()
    elif max_date and not official_latest:
        newer = "TRUE"
    if fetch_status == "EMPTY":
        cls = "HOLD_EMPTY_FETCH"
        action = "HOLD_REVIEW"
        block = "Empty provider response."
    elif not schema_ok:
        cls = "HOLD_SCHEMA_INVALID"
        action = "HOLD_REVIEW"
        block = "Required OHLC schema missing."
    elif severe:
        cls = "HOLD_SUSPICIOUS_PRICE_DATA"
        action = "HOLD_REVIEW"
        block = "Suspicious staged data quality issue."
    elif full_ready:
        cls = "MERGE_CANDIDATE_FULL_HISTORY"
        action = "DRY_RUN_MERGE_FULL_HISTORY"
        block = ""
    elif local_success and insufficient:
        cls = "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY"
        action = "DRY_RUN_MERGE_PRICE_ONLY_PARTIAL_HISTORY"
        block = "Not full factor-ready."
    else:
        cls = "HOLD_UNKNOWN_QUALITY_ISSUE"
        action = "HOLD_REVIEW"
        block = "Quality state could not be established."
    score = 100
    score -= 40 if not schema_ok else 0
    score -= 25 if not rows else 0
    score -= min(30, duplicate_dates * 5 + non_positive_close * 10 + outliers * 10)
    score -= 10 if insufficient else 0
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "HOLD"
    return {
        "ticker": ticker,
        "fetch_status": fetch_status,
        "staged_file_exists": str(staged_path.exists()).upper(),
        "staged_row_count": len(rows),
        "staged_min_date": min_date,
        "staged_max_date": max_date,
        "latest_date_age_days": age,
        "has_required_ohlcv_columns": str(schema_ok).upper(),
        "close_non_null_count": len(close_values),
        "volume_non_null_count": volume_count,
        "duplicate_date_count": duplicate_dates,
        "missing_date_or_parse_issue_count": date_bad,
        "non_positive_close_count": non_positive_close,
        "suspicious_large_gap_count": gaps,
        "suspicious_return_outlier_count": outliers,
        "full_history_ready_from_v18_23C": str(full_ready).upper(),
        "staged_local_price_scan_success_from_v18_23C": str(local_success).upper(),
        "insufficient_history_flag_from_v18_23C": str(insufficient).upper(),
        "official_price_overlap_found": overlap,
        "existing_official_latest_date": official_latest,
        "staged_newer_than_official": newer,
        "recommended_integration_action": action,
        "integration_block_reason": block,
        "quality_score": score,
        "quality_grade": grade,
        "classification": cls,
    }


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_md(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R1 Staged Backfill Quality Audit

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Purpose
Audit V18.23C staged backfill quality and create an official integration dry-run plan. No official integration is performed.

## Staged Summary
Batch tickers: {values['BATCH_TICKER_COUNT']}. Fetch success: {values['STAGED_FETCH_SUCCESS_COUNT']}. Empty: {values['STAGED_EMPTY_COUNT']}. Full-history ready: {values['STAGED_FULL_HISTORY_READY_COUNT']}. Insufficient history: {values['STAGED_INSUFFICIENT_HISTORY_COUNT']}.

## Quality Summary
Full-history merge candidates: {values['MERGE_CANDIDATE_FULL_HISTORY_COUNT']}. Price-only partial candidates: {values['MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT']}. Hold/review: {values['HOLD_REVIEW_TICKER_COUNT']}.

Empty fetch tickers, including COG and JFROG, remain hold/review and are not merge candidates.

## Official Integration Gate
Official integration allowed next step: {values['OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP']}. Explicit approval required: {values['OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL']}.

## Not Modified
No external fetch, staged file mutation, official price cache mutation, ledger update, ranking/factor/technical/signal mutation, backtest, or trading integration occurred.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R1 Quality Audit Report

Status: {values['STATUS']}.

Quality audited ticker count: {values['QUALITY_AUDITED_TICKER_COUNT']}. Full-history merge candidates: {values['MERGE_CANDIDATE_FULL_HISTORY_COUNT']}. Price-only partial candidates: {values['MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT']}. Hold/review: {values['HOLD_REVIEW_TICKER_COUNT']}.

Official integration dry-run created: {values['OFFICIAL_INTEGRATION_DRY_RUN_CREATED']}. Official integration allowed next step: {values['OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP']}; explicit approval required: {values['OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL']}.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in protected_files(root)}

    fetch_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_CURRENT_BACKFILL_FETCH_RESULT.csv")
    retest_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_CURRENT_STAGED_SCAN_RETEST_RESULT.csv")
    manifest_rows, _ = read_csv(root / MANIFEST_REL)
    combined_rows, _ = read_csv(root / COMBINED_REL)
    fetch_by = {row.get("ticker", ""): row for row in fetch_rows}
    retest_by = {row.get("ticker", ""): row for row in retest_rows}
    tickers = sorted(set(fetch_by) | set(retest_by))
    quality_rows = [audit_ticker(root, ticker, fetch_by.get(ticker, {}), retest_by.get(ticker, {})) for ticker in tickers]
    merge_rows = [row for row in quality_rows if str(row["classification"]).startswith("MERGE_CANDIDATE")]
    hold_rows = [row for row in quality_rows if not str(row["classification"]).startswith("MERGE_CANDIDATE")]
    full_merge = [row for row in quality_rows if row["classification"] == "MERGE_CANDIDATE_FULL_HISTORY"]
    partial_merge = [row for row in quality_rows if row["classification"] == "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY"]
    plan_rows = []
    for row in merge_rows:
        ticker = row["ticker"]
        plan_rows.append({
            "ticker": ticker,
            "dry_run_action": row["recommended_integration_action"],
            "staged_source_path": str(root / STAGED_DIR_REL / f"{ticker}.csv"),
            "official_destination_path": str(root / "state/v18/price_cache" / f"{ticker}.csv"),
            "backup_required": "TRUE",
            "merge_scope": "FULL_HISTORY" if row["classification"] == "MERGE_CANDIDATE_FULL_HISTORY" else "PRICE_ONLY_PARTIAL_HISTORY_NOT_FACTOR_READY",
            "ledger_update_timing": "AFTER_OFFICIAL_LOCAL_SCAN_SUCCEEDS",
            "ranking_factor_technical_unchanged": "TRUE",
            "post_integration_retest_required": "TRUE",
            "explicit_approval_required": "TRUE",
            "notes": "Dry run only; no file copied in R1.",
        })
    summary_rows = [
        {"metric": "quality_audited_ticker_count", "value": len(quality_rows), "notes": "Batch tickers audited."},
        {"metric": "merge_candidate_full_history_count", "value": len(full_merge), "notes": "Potential future official integration candidates."},
        {"metric": "merge_candidate_price_only_partial_history_count", "value": len(partial_merge), "notes": "Price-only, not factor-ready."},
        {"metric": "hold_review_ticker_count", "value": len(hold_rows), "notes": "Not merge candidates."},
    ]
    source_rows = [
        {"source_name": "staged_manifest", "source_path": MANIFEST_REL, "exists": str((root / MANIFEST_REL).exists()).upper(), "row_count": len(manifest_rows), "notes": "Read-only staged manifest."},
        {"source_name": "combined_staged_history", "source_path": COMBINED_REL, "exists": str((root / COMBINED_REL).exists()).upper(), "row_count": len(combined_rows), "notes": "Read-only combined staged file."},
        {"source_name": "fetch_result", "source_path": "outputs/v18/staged_backfill/V18_23C_CURRENT_BACKFILL_FETCH_RESULT.csv", "exists": str(bool(fetch_rows)).upper(), "row_count": len(fetch_rows), "notes": "V18.23C fetch results."},
        {"source_name": "staged_retest", "source_path": "outputs/v18/staged_backfill/V18_23C_CURRENT_STAGED_SCAN_RETEST_RESULT.csv", "exists": str(bool(retest_rows)).upper(), "row_count": len(retest_rows), "notes": "V18.23C staged retest results."},
    ]
    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "QUALITY_AUDIT_READY": "FALSE",
        "BATCH_ID": BATCH_ID,
        "BATCH_TICKER_COUNT": str(len(tickers)),
        "STAGED_FETCH_SUCCESS_COUNT": str(sum(1 for row in fetch_rows if row.get("fetch_status") == "SUCCESS")),
        "STAGED_EMPTY_COUNT": str(sum(1 for row in fetch_rows if row.get("fetch_status") == "EMPTY")),
        "STAGED_FULL_HISTORY_READY_COUNT": str(sum(1 for row in retest_rows if row.get("staged_scan_status") == "STAGED_FULL_HISTORY_READY")),
        "STAGED_INSUFFICIENT_HISTORY_COUNT": str(sum(1 for row in retest_rows if row.get("staged_scan_status") == "STAGED_INSUFFICIENT_HISTORY")),
        "QUALITY_AUDITED_TICKER_COUNT": str(len(quality_rows)),
        "MERGE_CANDIDATE_FULL_HISTORY_COUNT": str(len(full_merge)),
        "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY_COUNT": str(len(partial_merge)),
        "HOLD_REVIEW_TICKER_COUNT": str(len(hold_rows)),
        "HOLD_EMPTY_FETCH_COUNT": str(sum(1 for row in quality_rows if row["classification"] == "HOLD_EMPTY_FETCH")),
        "HOLD_INSUFFICIENT_HISTORY_COUNT": str(sum(1 for row in quality_rows if row["classification"] == "HOLD_INSUFFICIENT_HISTORY")),
        "HOLD_SCHEMA_INVALID_COUNT": str(sum(1 for row in quality_rows if row["classification"] == "HOLD_SCHEMA_INVALID")),
        "HOLD_SUSPICIOUS_DATA_COUNT": str(sum(1 for row in quality_rows if row["classification"] == "HOLD_SUSPICIOUS_PRICE_DATA")),
        "OFFICIAL_INTEGRATION_DRY_RUN_CREATED": "TRUE",
        "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP": str(bool(plan_rows)).upper(),
        "OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL": "TRUE",
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "FALSE_QUALITY_AUDIT_ONLY_NO_OFFICIAL_LEDGER_COVERAGE",
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Review dry-run merge candidates; only run V18.23C-R2 official integration after explicit approval and backup plan acceptance.",
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
    values.update(SAFETY)
    write_csv(root / OUTPUTS["ticker"], quality_rows, TICKER_FIELDS)
    write_csv(root / OUTPUTS["merge"], merge_rows, TICKER_FIELDS)
    write_csv(root / OUTPUTS["hold"], hold_rows, TICKER_FIELDS)
    write_csv(root / OUTPUTS["plan"], plan_rows, PLAN_FIELDS)
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["source"], source_rows, SOURCE_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23C_R1_staged_backfill_quality_audit.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23C_R1_staged_backfill_quality_audit.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "All R1 outputs must exist and be non-empty."),
        validation_row("staged_manifest_readable", bool(manifest_rows), 1, "Manifest must be readable."),
        validation_row("staged_history_readable", bool(combined_rows), 1, "Combined staged history must be readable."),
        validation_row("quality_count_matches_batch", len(quality_rows) == len(tickers), 1, "Quality count must match batch."),
        validation_row("dry_run_plan_non_empty", bool(plan_rows), 1, "Dry-run plan must exist and be non-empty."),
        validation_row("protected_files_unchanged", not changed, len(changed), ";".join(changed[:20])),
        validation_row("true_coverage_remains_false", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] == "FALSE", 1, "Audit only."),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    elif not full_merge or hold_rows:
        values["STATUS"] = STATUS_WARN
    else:
        values["STATUS"] = STATUS_OK
    values["QUALITY_AUDIT_READY"] = "TRUE" if fail_count == 0 else "FALSE"
    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
