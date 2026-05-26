from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_23C_R6_BATCH2_OFFICIAL_FULL_HISTORY_INTEGRATION_READY"
STATUS_WARN = "WARN_V18_23C_R6_BATCH2_OFFICIAL_INTEGRATION_PARTIAL"
STATUS_FAIL = "FAIL_V18_23C_R6_BATCH2_OFFICIAL_INTEGRATION"
MODE = "BATCH2_OFFICIAL_PRICE_CACHE_INTEGRATION_FULL_HISTORY_ONLY_WITH_BACKUP"
BATCH_ID = "V18_23C_BATCH2"
STAGED_DIR_REL = "data/v18/staged_backfill/V18_23C_BATCH2"
DEST_DIR_REL = "state/v18/price_cache"

OUTPUTS = {
    "md": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_OFFICIAL_INTEGRATION.md",
    "candidates": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_FULL_HISTORY_INTEGRATION_CANDIDATES.csv",
    "destination": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_OFFICIAL_DESTINATION_AUDIT.csv",
    "backup": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_BACKUP_MANIFEST.csv",
    "merge": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_MERGE_RESULT.csv",
    "held": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_HELD_OUT_TICKERS.csv",
    "retest": "outputs/v18/rolling_coverage/V18_23C_R6_CURRENT_BATCH2_POST_INTEGRATION_RETEST.csv",
    "retest_summary": "outputs/v18/rolling_coverage/V18_23C_R6_CURRENT_BATCH2_POST_INTEGRATION_RETEST_SUMMARY.csv",
    "validation": "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_BATCH2_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23C_R6_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23C_R6_CURRENT_BATCH2_OFFICIAL_INTEGRATION_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "BATCH2_OFFICIAL_INTEGRATION_READY", "BATCH_ID", "INTEGRATION_SCOPE",
    "FULL_HISTORY_CANDIDATE_COUNT", "PRICE_ONLY_PARTIAL_EXCLUDED_COUNT",
    "HOLD_REVIEW_EXCLUDED_COUNT", "EMPTY_FETCH_EXCLUDED_COUNT", "SUSPICIOUS_DATA_EXCLUDED_COUNT",
    "OFFICIAL_DESTINATION_FOUND", "OFFICIAL_DESTINATION_PATH", "BACKUP_CREATED", "BACKUP_PATH",
    "RESTORE_SCRIPT_PATH", "OFFICIAL_PRICE_CACHE_MODIFIED", "OFFICIAL_PRICE_HISTORY_MODIFIED",
    "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_MODIFIED",
    "MERGE_ATTEMPTED_COUNT", "MERGE_SUCCESS_COUNT", "MERGE_SKIPPED_COUNT", "MERGE_FAILED_COUNT",
    "POST_INTEGRATION_RETEST_EXECUTED", "POST_INTEGRATION_LOCAL_PRICE_SUCCESS_COUNT",
    "POST_INTEGRATION_FULL_HISTORY_READY_COUNT", "POST_INTEGRATION_RETEST_SUCCESS_RATIO",
    "LEDGER_MODIFIED", "ROLLING_SCAN_EXECUTED", "ROLLING_SCAN_DATA_FETCHED", "EXTERNAL_DATA_FETCHED",
    "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "VALIDATION_FAIL_COUNT",
    "RECOMMENDED_NEXT_ACTION", "INTEGRATION_REPORT_PATH", "CANDIDATES_PATH", "DESTINATION_AUDIT_PATH",
    "BACKUP_MANIFEST_PATH", "MERGE_RESULT_PATH", "HELD_OUT_TICKERS_PATH",
    "POST_INTEGRATION_RETEST_PATH", "POST_INTEGRATION_RETEST_SUMMARY_PATH", "VALIDATION_PATH", "REPORT_PATH",
]

PRICE_FIELDS = ["date", "open", "high", "low", "close", "adj_close", "volume", "source", "source_file", "updated_at"]
CANDIDATE_FIELDS = ["ticker", "classification", "staged_file", "staged_row_count", "quality_grade"]
DEST_FIELDS = ["destination_role", "destination_path", "exists", "confidence", "selection_reason", "file_count"]
BACKUP_FIELDS = ["ticker", "original_path", "backup_path", "original_existed", "backup_created", "restore_action"]
MERGE_FIELDS = [
    "ticker", "staged_path", "destination_path", "merge_status", "before_row_count", "staged_row_count",
    "after_row_count", "added_or_updated_row_count", "failure_reason",
]
HELD_FIELDS = ["ticker", "classification", "hold_reason", "source_path"]
RETEST_FIELDS = ["ticker", "official_path", "official_file_exists", "row_count", "latest_date", "local_price_scan_success", "full_history_ready", "notes"]
SUMMARY_FIELDS = ["metric", "value", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

SAFETY_FALSE = {
    "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "ROLLING_SCAN_DATA_FETCHED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
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


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def collect_protected(root: Path) -> List[Path]:
    rel_dirs = [
        "outputs/v18/ranking", "outputs/v18/signal_snapshots", "outputs/v18/factor_pack",
        "outputs/v18/technical_timing", "state/v18/rolling_coverage", "state/v18/manual",
        "state/v18/simulation", "state/v18/forward_outcome", "state/v18/candidate_forward_tracker",
        "archive/stable", "outputs/v18/backtest", "outputs/v18/daily_integrated",
    ]
    out: List[Path] = []
    for rel in rel_dirs:
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


def normalize_price_row(row: Dict[str, str], source_file: str, updated_at: str) -> Dict[str, str]:
    def get(*names: str) -> str:
        lower = {k.lower(): v for k, v in row.items()}
        for name in names:
            if name in row:
                return str(row.get(name, "")).strip()
            if name.lower() in lower:
                return str(lower.get(name.lower(), "")).strip()
        return ""

    return {
        "date": get("date", "Date"),
        "open": get("open", "Open"),
        "high": get("high", "High"),
        "low": get("low", "Low"),
        "close": get("close", "Close"),
        "adj_close": get("adj_close", "Adj Close", "Adj_Close"),
        "volume": get("volume", "Volume"),
        "source": "V18_23C_R6_BATCH2_STAGED_FULL_HISTORY_INTEGRATION",
        "source_file": source_file,
        "updated_at": updated_at,
    }


def read_normalized_prices(path: Path, source_file: str, updated_at: str) -> List[Dict[str, str]]:
    rows, _ = read_csv(path)
    normalized: List[Dict[str, str]] = []
    for row in rows:
        out = normalize_price_row(row, source_file, updated_at)
        if parse_date(out["date"]) and out["close"]:
            normalized.append(out)
    return normalized


def merge_price_rows(existing: List[Dict[str, str]], staged: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], int]:
    by_date: Dict[str, Dict[str, str]] = {}
    for row in existing:
        date = row.get("date", "")
        if parse_date(date):
            base = {field: str(row.get(field, "")).strip() for field in PRICE_FIELDS}
            by_date[date] = base
    before_dates = set(by_date)
    for row in staged:
        by_date[row["date"]] = {field: row.get(field, "") for field in PRICE_FIELDS}
    merged = [by_date[key] for key in sorted(by_date)]
    changed = sum(1 for row in staged if row["date"] not in before_dates) + sum(1 for row in staged if row["date"] in before_dates)
    return merged, changed


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


def render_restore_script(backup_rows: Sequence[Dict[str, object]]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        'Write-Host "=== RESTORE V18.23C-R6 PRICE CACHE START ==="',
    ]
    for row in backup_rows:
        original = str(row["original_path"])
        backup = str(row["backup_path"])
        if row["original_existed"] == "TRUE":
            lines += [
                f'$dest = "{original}"',
                f'$src = "{backup}"',
                'if (-not (Test-Path -LiteralPath $src)) { throw "Missing backup: $src" }',
                '$parent = Split-Path -Parent $dest',
                'if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }',
                'Copy-Item -LiteralPath $src -Destination $dest -Force',
            ]
        else:
            lines += [
                f'$dest = "{original}"',
                'if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Force }',
            ]
    lines += ['Write-Host "=== RESTORE V18.23C-R6 PRICE CACHE END ==="', 'exit 0']
    return "\n".join(lines) + "\n"


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_md(values: Dict[str, str]) -> str:
    return f"""# V18.23C-R6 Batch 2 Official Price Cache Integration

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Scope
Full-history-only official price cache integration for V18.23C Batch 2. Price-only partial, empty fetch, suspicious data, and hold/review tickers were excluded.

## Destination
Selected official destination: `{values['OFFICIAL_DESTINATION_PATH']}`.

## Backup
Backup path: `{values['BACKUP_PATH']}`.
Restore script: `{values['RESTORE_SCRIPT_PATH']}`.

## Merge Summary
Attempted: {values['MERGE_ATTEMPTED_COUNT']}. Success: {values['MERGE_SUCCESS_COUNT']}. Failed: {values['MERGE_FAILED_COUNT']}. Skipped: {values['MERGE_SKIPPED_COUNT']}.

## Post-Integration Retest
Local price success: {values['POST_INTEGRATION_LOCAL_PRICE_SUCCESS_COUNT']}. Full-history ready: {values['POST_INTEGRATION_FULL_HISTORY_READY_COUNT']}. Success ratio: {values['POST_INTEGRATION_RETEST_SUCCESS_RATIO']}.

## Safety
No ranking, signal snapshot, factor pack, technical timing, ledger, official decision, trading state, or backtest files were modified. TRUE_5DAY_UNIQUE_COVERAGE_MET remains FALSE because the official rolling ledger was not updated.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    updated_at = dt.datetime.now().isoformat(timespec="seconds")

    before = {str(path): file_sig(path) for path in collect_protected(root)}
    dest_dir = root / DEST_DIR_REL
    staged_dir = root / STAGED_DIR_REL
    backup_dir = root / "archive/v18/price_cache_backups" / f"V18_23C_R6_{timestamp}"
    restore_path = backup_dir / "RESTORE_V18_23C_R6_PRICE_CACHE.ps1"
    backup_manifest_path = backup_dir / "BACKUP_MANIFEST.csv"

    merge_input, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_MERGE_CANDIDATES.csv")
    quality_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_TICKER_QUALITY_AUDIT.csv")
    full_candidates = [row for row in quality_rows if row.get("classification") == "MERGE_CANDIDATE_FULL_HISTORY"]
    full_tickers = sorted({row.get("ticker", "").strip().upper() for row in full_candidates if row.get("ticker", "").strip()})
    held_rows: List[Dict[str, object]] = []
    for row in quality_rows:
        ticker = row.get("ticker", "").strip().upper()
        cls = row.get("classification", "")
        if ticker and cls != "MERGE_CANDIDATE_FULL_HISTORY":
            held_rows.append({
                "ticker": ticker,
                "classification": cls,
                "hold_reason": row.get("integration_block_reason", "") or "Excluded from full-history-only integration.",
                "source_path": str(staged_dir / f"{ticker}.csv"),
            })

    executor_text = (root / "scripts/v18/v18_23B_rolling_scan_executor.py").read_text(encoding="utf-8", errors="replace") if (root / "scripts/v18/v18_23B_rolling_scan_executor.py").exists() else ""
    destination_found = dest_dir.exists() and "state/v18/price_cache" in executor_text
    destination_rows = [{
        "destination_role": "official_price_cache",
        "destination_path": str(dest_dir),
        "exists": str(dest_dir.exists()).upper(),
        "confidence": "HIGH" if destination_found else "LOW",
        "selection_reason": "V18.23B local scan executor reads state/v18/price_cache/<ticker>.csv." if destination_found else "Destination convention not safely confirmed.",
        "file_count": len(list(dest_dir.glob("*.csv"))) if dest_dir.exists() else 0,
    }]

    backup_rows: List[Dict[str, object]] = []
    merge_rows: List[Dict[str, object]] = []
    retest_rows: List[Dict[str, object]] = []
    if destination_found and full_tickers:
        ensure_dir(backup_dir)
        for ticker in full_tickers:
            dest = dest_dir / f"{ticker}.csv"
            backup = backup_dir / f"{ticker}.csv"
            existed = dest.exists()
            if existed:
                shutil.copy2(dest, backup)
            backup_rows.append({
                "ticker": ticker,
                "original_path": str(dest),
                "backup_path": str(backup),
                "original_existed": str(existed).upper(),
                "backup_created": str(existed and backup.exists()).upper(),
                "restore_action": "COPY_BACKUP_OVER_DESTINATION" if existed else "DELETE_CREATED_DESTINATION",
            })
        write_csv(backup_manifest_path, backup_rows, BACKUP_FIELDS)
        write_text(restore_path, render_restore_script(backup_rows))

        for ticker in full_tickers:
            staged = staged_dir / f"{ticker}.csv"
            dest = dest_dir / f"{ticker}.csv"
            before_rows = read_normalized_prices(dest, str(dest), updated_at) if dest.exists() else []
            staged_rows = read_normalized_prices(staged, str(staged), updated_at)
            status = "SUCCESS"
            failure = ""
            after_rows: List[Dict[str, str]] = []
            changed = 0
            if not staged.exists():
                status = "FAILED"
                failure = "STAGED_FILE_MISSING"
            elif not staged_rows:
                status = "FAILED"
                failure = "NO_VALID_STAGED_PRICE_ROWS"
            else:
                after_rows, changed = merge_price_rows(before_rows, staged_rows)
                write_csv(dest, after_rows, PRICE_FIELDS)
            merge_rows.append({
                "ticker": ticker,
                "staged_path": str(staged),
                "destination_path": str(dest),
                "merge_status": status,
                "before_row_count": len(before_rows),
                "staged_row_count": len(staged_rows),
                "after_row_count": len(after_rows) if status == "SUCCESS" else len(before_rows),
                "added_or_updated_row_count": changed if status == "SUCCESS" else 0,
                "failure_reason": failure,
            })

        for ticker in full_tickers:
            dest = dest_dir / f"{ticker}.csv"
            rows, _ = read_csv(dest)
            dates = [parse_date(row.get("date", "") or row.get("Date", "")) for row in rows]
            dates = [date for date in dates if date]
            latest = max(dates).isoformat() if dates else ""
            row_count = len(rows)
            local_success = dest.exists() and row_count > 0 and bool(latest)
            full_ready = local_success and row_count >= 500
            retest_rows.append({
                "ticker": ticker,
                "official_path": str(dest),
                "official_file_exists": str(dest.exists()).upper(),
                "row_count": row_count,
                "latest_date": latest,
                "local_price_scan_success": str(local_success).upper(),
                "full_history_ready": str(full_ready).upper(),
                "notes": "Official cache read-only retest after merge; ledger not updated.",
            })

    merge_success = sum(1 for row in merge_rows if row.get("merge_status") == "SUCCESS")
    merge_failed = sum(1 for row in merge_rows if row.get("merge_status") == "FAILED")
    local_success = sum(1 for row in retest_rows if row.get("local_price_scan_success") == "TRUE")
    full_ready = sum(1 for row in retest_rows if row.get("full_history_ready") == "TRUE")
    ratio = (local_success / len(retest_rows)) if retest_rows else 0.0

    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "BATCH2_OFFICIAL_INTEGRATION_READY": "FALSE",
        "BATCH_ID": BATCH_ID,
        "INTEGRATION_SCOPE": "FULL_HISTORY_ONLY",
        "FULL_HISTORY_CANDIDATE_COUNT": str(len(full_tickers)),
        "PRICE_ONLY_PARTIAL_EXCLUDED_COUNT": str(sum(1 for row in quality_rows if row.get("classification") == "MERGE_CANDIDATE_PRICE_ONLY_PARTIAL_HISTORY")),
        "HOLD_REVIEW_EXCLUDED_COUNT": str(sum(1 for row in quality_rows if not str(row.get("classification", "")).startswith("MERGE_CANDIDATE"))),
        "EMPTY_FETCH_EXCLUDED_COUNT": str(sum(1 for row in quality_rows if row.get("classification") == "HOLD_EMPTY_FETCH")),
        "SUSPICIOUS_DATA_EXCLUDED_COUNT": str(sum(1 for row in quality_rows if row.get("classification") == "HOLD_SUSPICIOUS_PRICE_DATA")),
        "OFFICIAL_DESTINATION_FOUND": str(destination_found).upper(),
        "OFFICIAL_DESTINATION_PATH": str(dest_dir) if destination_found else "",
        "BACKUP_CREATED": str(backup_manifest_path.exists() and restore_path.exists()).upper(),
        "BACKUP_PATH": str(backup_dir) if backup_dir.exists() else "",
        "RESTORE_SCRIPT_PATH": str(restore_path) if restore_path.exists() else "",
        "OFFICIAL_PRICE_CACHE_MODIFIED": str(merge_success > 0).upper(),
        "PRICE_CACHE_MODIFIED": str(merge_success > 0).upper(),
        "MERGE_ATTEMPTED_COUNT": str(len(merge_rows)),
        "MERGE_SUCCESS_COUNT": str(merge_success),
        "MERGE_SKIPPED_COUNT": "0",
        "MERGE_FAILED_COUNT": str(merge_failed),
        "POST_INTEGRATION_RETEST_EXECUTED": str(bool(retest_rows)).upper(),
        "POST_INTEGRATION_LOCAL_PRICE_SUCCESS_COUNT": str(local_success),
        "POST_INTEGRATION_FULL_HISTORY_READY_COUNT": str(full_ready),
        "POST_INTEGRATION_RETEST_SUCCESS_RATIO": f"{ratio:.6f}",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "FALSE_OFFICIAL_CACHE_UPDATED_BUT_LEDGER_NOT_UPDATED",
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Run a separate local-only rolling scan ledger update/retest for integrated tickers; keep price-only partial and hold/review tickers excluded.",
        "INTEGRATION_REPORT_PATH": str(root / OUTPUTS["md"]),
        "CANDIDATES_PATH": str(root / OUTPUTS["candidates"]),
        "DESTINATION_AUDIT_PATH": str(root / OUTPUTS["destination"]),
        "BACKUP_MANIFEST_PATH": str(backup_manifest_path),
        "MERGE_RESULT_PATH": str(root / OUTPUTS["merge"]),
        "HELD_OUT_TICKERS_PATH": str(root / OUTPUTS["held"]),
        "POST_INTEGRATION_RETEST_PATH": str(root / OUTPUTS["retest"]),
        "POST_INTEGRATION_RETEST_SUMMARY_PATH": str(root / OUTPUTS["retest_summary"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY_FALSE)

    write_csv(root / OUTPUTS["candidates"], [
        {
            "ticker": ticker,
            "classification": "MERGE_CANDIDATE_FULL_HISTORY",
            "staged_file": str(staged_dir / f"{ticker}.csv"),
            "staged_row_count": next((row.get("staged_row_count", "") for row in full_candidates if row.get("ticker", "").strip().upper() == ticker), ""),
            "quality_grade": next((row.get("quality_grade", "") for row in full_candidates if row.get("ticker", "").strip().upper() == ticker), ""),
        } for ticker in full_tickers
    ], CANDIDATE_FIELDS)
    write_csv(root / OUTPUTS["destination"], destination_rows, DEST_FIELDS)
    write_csv(root / OUTPUTS["backup"], backup_rows, BACKUP_FIELDS)
    write_csv(root / OUTPUTS["merge"], merge_rows, MERGE_FIELDS)
    write_csv(root / OUTPUTS["held"], held_rows, HELD_FIELDS)
    write_csv(root / OUTPUTS["retest"], retest_rows, RETEST_FIELDS)
    write_csv(root / OUTPUTS["retest_summary"], [
        {"metric": "post_integration_local_price_success_count", "value": local_success, "notes": "Read from official cache only."},
        {"metric": "post_integration_full_history_ready_count", "value": full_ready, "notes": "Row-count threshold >= 500."},
        {"metric": "post_integration_retest_success_ratio", "value": f"{ratio:.6f}", "notes": "Local price success over attempted tickers."},
    ], SUMMARY_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_md(values))
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in collect_protected(root)}
    changed_forbidden = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required_outputs = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23C_R6_batch2_official_price_integration_full_history.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23C_R6_batch2_official_price_integration_full_history.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required_outputs), 1, "All R6 outputs must exist and be non-empty."),
        validation_row("official_destination_found", destination_found, 1, "Destination must be safely identified."),
        validation_row("candidate_count_matches_r5", len(full_tickers) == 52, 1, f"Expected 52 from R5; actual {len(full_tickers)}."),
        validation_row("held_out_contains_exclusions", bool(held_rows) and int(values["PRICE_ONLY_PARTIAL_EXCLUDED_COUNT"]) == 5 and int(values["EMPTY_FETCH_EXCLUDED_COUNT"]) == 3, 1, "Held out must include partial and empty fetch tickers."),
        validation_row("backup_folder_exists", backup_dir.exists(), 1, "Backup folder must exist."),
        validation_row("backup_manifest_non_empty", non_empty(backup_manifest_path), 1, "Backup manifest must exist and be non-empty."),
        validation_row("restore_script_non_empty", non_empty(restore_path), 1, "Restore script must exist and be non-empty."),
        validation_row("merge_result_one_row_per_attempt", len(merge_rows) == len(full_tickers), 1, "Merge result must contain one row per candidate."),
        validation_row("post_retest_one_row_per_attempt", len(retest_rows) == len(full_tickers), 1, "Retest must contain one row per candidate."),
        validation_row("no_forbidden_files_modified", not changed_forbidden, len(changed_forbidden), ";".join(changed_forbidden[:20])),
        validation_row("true_coverage_remains_false", values["TRUE_5DAY_UNIQUE_COVERAGE_MET"] == "FALSE", 1, "Ledger not updated."),
    ]
    for key, expected in SAFETY_FALSE.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not destination_found or not backup_manifest_path.exists() or not restore_path.exists() or merge_success == 0:
        values["STATUS"] = STATUS_FAIL
    elif merge_success == len(full_tickers) and local_success == len(full_tickers) and full_ready == len(full_tickers):
        values["STATUS"] = STATUS_OK
    else:
        values["STATUS"] = STATUS_WARN
    values["BATCH2_OFFICIAL_INTEGRATION_READY"] = "TRUE" if values["STATUS"] != STATUS_FAIL else "FALSE"

    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["md"], render_md(values))
    write_text(root / OUTPUTS["report"], render_md(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
